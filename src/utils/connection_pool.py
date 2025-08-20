"""
Gestor de pool de conexiones para Supabase/PostgreSQL
Optimiza la reutilización de conexiones y reduce la latencia de conexión
"""
import os
from typing import Optional, Dict, Any
from functools import wraps
import time
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ConnectionPool:
    """Implementa un pool de conexiones para PostgreSQL/Supabase"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern para acceder al pool"""
        if cls._instance is None:
            cls._instance = ConnectionPool()
        return cls._instance
    
    def __init__(self):
        """Inicializa el pool de conexiones"""
        self.connection_pool = None
        self.min_connections = 2
        self.max_connections = 10
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializar el pool de conexiones"""
        try:
            if all(self.db_config.values()):  # Verificar que todas las credenciales estén configuradas
                self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    **self.db_config
                )
                logging.info("Pool de conexiones inicializado correctamente")
            else:
                logging.warning("Configuración de base de datos incompleta, el pool no se ha inicializado")
        except Exception as e:
            logging.error(f"Error al inicializar el pool de conexiones: {e}")
            self.connection_pool = None
    
    def get_connection(self):
        """Obtiene una conexión del pool"""
        if self.connection_pool is None:
            self._initialize_pool()
            
        if self.connection_pool is None:
            logging.error("No se pudo obtener una conexión del pool (pool no inicializado)")
            return None
        
        try:
            connection = self.connection_pool.getconn()
            return connection
        except Exception as e:
            logging.error(f"Error al obtener conexión del pool: {e}")
            return None
    
    def return_connection(self, connection):
        """Devuelve una conexión al pool"""
        if self.connection_pool and connection:
            try:
                self.connection_pool.putconn(connection)
            except Exception as e:
                logging.error(f"Error al devolver conexión al pool: {e}")
    
    def close_all(self):
        """Cierra todas las conexiones del pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logging.info("Todas las conexiones del pool han sido cerradas")
            self.connection_pool = None


# Decorator para medir y loguear el tiempo de ejecución de consultas
def measure_query_time(func):
    """Decorator para medir tiempo de ejecución de consultas"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log solo si la consulta es lenta (> 100ms)
        if execution_time > 0.1:
            func_name = func.__name__
            logging.warning(f"Consulta lenta: {func_name} - {execution_time:.4f}s")
        
        return result
    return wrapper


class OptimizedDbClient:
    """Cliente de base de datos optimizado con pool de conexiones"""
    
    def __init__(self):
        self.pool = ConnectionPool.get_instance()
    
    @measure_query_time
    def execute_query(self, query: str, params=None, fetch=True):
        """
        Ejecuta una consulta SQL utilizando el pool de conexiones
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            fetch: Si es True, devuelve los resultados, si no, solo ejecuta
            
        Returns:
            List o None: Resultados de la consulta o None si es una operación
        """
        connection = None
        cursor = None
        
        try:
            connection = self.pool.get_connection()
            if not connection:
                raise Exception("No se pudo obtener una conexión de la base de datos")
                
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            
            if fetch and query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                connection.commit()
                return cursor.rowcount if not fetch else []
                
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Error en consulta SQL: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.pool.return_connection(connection)
    
    @st.cache_data(ttl=60)  # Cache por 1 minuto
    def fetch_with_pagination(self, query: str, params=None, page=1, page_size=50):
        """
        Ejecuta una consulta con paginación
        
        Args:
            query: Consulta SQL (sin LIMIT/OFFSET)
            params: Parámetros para la consulta
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Dict: Resultados paginados y metadatos
        """
        offset = (page - 1) * page_size
        
        # Query de conteo para metadatos de paginación
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        
        # Query principal con paginación
        paginated_query = f"{query} LIMIT %s OFFSET %s"
        
        # Lista de parámetros para la consulta paginada
        paginated_params = list(params) if params else []
        paginated_params.extend([page_size, offset])
        
        # Ejecutar query de conteo
        count_result = self.execute_query(count_query, params)
        total_records = count_result[0]['total'] if count_result else 0
        total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
        
        # Ejecutar query principal
        results = self.execute_query(paginated_query, paginated_params)
        
        return {
            'data': results,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'total_records': total_records
            }
        }


# Instancia global del cliente
optimized_db_client = OptimizedDbClient()
