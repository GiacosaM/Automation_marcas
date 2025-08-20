"""
Utilidades para optimizar consultas y conexiones a la base de datos
Enfocado en mejorar el rendimiento de PostgreSQL en Supabase
"""
import time
from functools import wraps
import streamlit as st
from typing import List, Dict, Tuple, Any, Optional, Callable
import logging

# Configuración de logging para medición de rendimiento
perf_logger = logging.getLogger('performance')
perf_logger.setLevel(logging.DEBUG)
if not perf_logger.handlers:
    perf_handler = logging.FileHandler('performance.log')
    perf_handler.setFormatter(logging.Formatter('%(asctime)s - PERF - %(message)s'))
    perf_logger.addHandler(perf_handler)
perf_logger.propagate = False

def time_query(func):
    """Decorador para medir el tiempo de ejecución de una consulta"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Registrar tiempo de ejecución
        func_name = func.__name__
        perf_logger.debug(f"{func_name} - Tiempo: {execution_time:.4f}s")
        
        if execution_time > 1.0:  # Advertir si una consulta toma más de 1 segundo
            perf_logger.warning(f"CONSULTA LENTA: {func_name} - {execution_time:.4f}s")
            
        return result
    return wrapper

# Funciones optimizadas para reemplazar consultas existentes

@st.cache_data(ttl=300)  # Cache durante 5 minutos
def obtener_clientes_optimizado(_conn, page=1, page_size=50, filtro=None):
    """
    Versión optimizada de obtener_clientes con paginación y filtrado
    
    Args:
        _conn: Conexión a la base de datos
        page: Número de página (comienza en 1)
        page_size: Tamaño de página
        filtro: Diccionario con filtros {campo: valor}
    
    Returns:
        Tuple[List, List]: Filas y columnas
    """
    cursor = None
    try:
        cursor = _conn.cursor()
        
        # Construcción de consulta base
        query_base = """
            SELECT id, titular, email, telefono, cuit
            FROM clientes
        """
        
        # Agregar filtros si existen
        params = []
        where_clauses = []
        
        if filtro:
            for campo, valor in filtro.items():
                if campo in ['titular', 'email', 'cuit']:
                    where_clauses.append(f"{campo} ILIKE %s")
                    params.append(f"%{valor}%")
        
        # Construir WHERE si hay filtros
        if where_clauses:
            query_base += " WHERE " + " AND ".join(where_clauses)
        
        # Agregar ordenamiento y paginación
        query_base += " ORDER BY titular"
        query_base += " LIMIT %s OFFSET %s"
        
        # Calcular offset
        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        
        # Ejecutar consulta
        cursor.execute(query_base, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Obtener total de registros para paginación
        count_query = "SELECT COUNT(*) FROM clientes"
        if where_clauses:
            count_query += " WHERE " + " AND ".join(where_clauses)
            cursor.execute(count_query, params[:-2])  # Excluir LIMIT y OFFSET
        else:
            cursor.execute(count_query)
            
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + page_size - 1) // page_size  # Redondeo hacia arriba
        
        return rows, columns, {"current_page": page, "total_pages": total_pages, "total_records": total_records}
    
    except Exception as e:
        logging.error(f"Error al consultar clientes: {e}")
        raise Exception(f"Error al consultar clientes: {e}")
    finally:
        if cursor:
            cursor.close()

@st.cache_data(ttl=60)  # Cache durante 1 minuto
def obtener_boletines_optimizado(conn, page=1, page_size=50, filtros=None, columnas=None):
    """
    Versión optimizada de obtener boletines con paginación
    
    Args:
        conn: Conexión a la base de datos
        page: Número de página (comienza en 1)
        page_size: Tamaño de página
        filtros: Diccionario con filtros {campo: valor}
        columnas: Lista de columnas a seleccionar
    
    Returns:
        Tuple[List, List]: Filas y columnas
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Columnas predeterminadas si no se especifican
        if not columnas:
            columnas = [
                'id', 'numero_boletin', 'titular', 'fecha_boletin', 
                'numero_orden', 'marca_publicada', 'importancia'
            ]
        
        # Construcción de consulta base
        query_base = f"""
            SELECT {', '.join(columnas)}
            FROM boletines
        """
        
        # Agregar filtros si existen
        params = []
        where_clauses = []
        
        if filtros:
            for campo, valor in filtros.items():
                if campo == 'fecha_boletin':
                    where_clauses.append(f"{campo} = %s")
                    params.append(valor)
                elif campo in ['reporte_generado', 'reporte_enviado']:
                    where_clauses.append(f"{campo} = %s")
                    params.append(valor)
                elif campo in ['titular', 'marca_publicada', 'marca_custodia']:
                    where_clauses.append(f"{campo} ILIKE %s")
                    params.append(f"%{valor}%")
                elif campo == 'importancia':
                    where_clauses.append(f"{campo} = %s")
                    params.append(valor)
        
        # Construir WHERE si hay filtros
        if where_clauses:
            query_base += " WHERE " + " AND ".join(where_clauses)
        
        # Agregar ordenamiento y paginación
        query_base += " ORDER BY fecha_boletin DESC, numero_boletin, numero_orden"
        query_base += " LIMIT %s OFFSET %s"
        
        # Calcular offset
        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        
        # Ejecutar consulta
        cursor.execute(query_base, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Obtener total de registros para paginación
        count_query = "SELECT COUNT(*) FROM boletines"
        if where_clauses:
            count_query += " WHERE " + " AND ".join(where_clauses)
            cursor.execute(count_query, params[:-2])  # Excluir LIMIT y OFFSET
        else:
            cursor.execute(count_query)
            
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + page_size - 1) // page_size  # Redondeo hacia arriba
        
        return rows, columns, {"current_page": page, "total_pages": total_pages, "total_records": total_records}
    
    except Exception as e:
        logging.error(f"Error al consultar boletines: {e}")
        raise Exception(f"Error al consultar boletines: {e}")
    finally:
        if cursor:
            cursor.close()

# Función para generar consultas COUNT optimizadas
@st.cache_data(ttl=300)  # Cache durante 5 minutos
def obtener_estadisticas(conn):
    """Obtiene estadísticas del sistema de manera optimizada"""
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Utilizamos un solo viaje a la BD con UNION ALL
        query = """
            SELECT 'total_boletines' as tipo, COUNT(*) as cantidad FROM boletines
            UNION ALL
            SELECT 'reportes_generados', COUNT(*) FROM boletines WHERE reporte_generado = TRUE
            UNION ALL
            SELECT 'reportes_enviados', COUNT(*) FROM boletines WHERE reporte_enviado = TRUE
            UNION ALL
            SELECT 'clientes_total', COUNT(DISTINCT titular) FROM clientes
        """
        
        cursor.execute(query)
        resultados = {row[0]: row[1] for row in cursor.fetchall()}
        
        return resultados
    except Exception as e:
        logging.error(f"Error al obtener estadísticas: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()

# Fin de la función o clase correspondiente
