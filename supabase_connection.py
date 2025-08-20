"""
Módulo para conectar con Supabase (PostgreSQL)
Migración desde SQLite a Supabase
"""
import os
import sys
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

# Cargar variables de entorno
load_dotenv()

class SupabaseManager:
    """Gestor de conexiones a Supabase"""
    
    def __init__(self):
        # Configuración de Supabase desde variables de entorno
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # Configuración directa de PostgreSQL (opcional)
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', 5432),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        self._supabase_client = None
        self._pg_connection = None
    
    @property
    def supabase(self) -> Optional[Client]:
        """Cliente de Supabase usando el SDK oficial"""
        if not self._supabase_client and self.url and self.key:
            try:
                self._supabase_client = create_client(self.url, self.key)
            except Exception as e:
                st.error(f"Error conectando con Supabase: {e}")
                return None
        return self._supabase_client
    
    def get_postgres_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Conexión directa a PostgreSQL usando psycopg2"""
        try:
            if not self._pg_connection or self._pg_connection.closed:
                self._pg_connection = psycopg2.connect(**self.db_config)
            return self._pg_connection
        except Exception as e:
            st.error(f"Error conectando con PostgreSQL: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Ejecutar consulta SQL usando psycopg2
        Para queries complejas o migraciones
        """
        conn = self.get_postgres_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return []
        except Exception as e:
            conn.rollback()
            st.error(f"Error ejecutando query: {e}")
            return []
    
    def close_connections(self):
        """Cerrar todas las conexiones"""
        if self._pg_connection and not self._pg_connection.closed:
            self._pg_connection.close()


# Instancia global del gestor
supabase_manager = SupabaseManager()


def usar_supabase():
    """Determinar si usar Supabase basado en configuración"""
    try:
        from config import ConfigManager
        config_manager = ConfigManager()
        return config_manager.get('database.type', 'supabase') == 'supabase'  # Default a supabase
    except Exception as e:
        print(f"Error al cargar configuración: {e}, usando fallback")
        # Fallback: usar variables de entorno
        return bool(os.getenv('SUPABASE_URL'))


def crear_conexion_supabase():
    """Crear cliente de Supabase"""
    try:
        manager = SupabaseManager()
        return manager.supabase
    except Exception as e:
        print(f"Error creando cliente Supabase: {e}")
        return None

def crear_conexion_postgres() -> Optional[psycopg2.extensions.connection]:
    """
    Crear conexión directa a PostgreSQL
    Para casos que requieren SQL nativo
    """
    return supabase_manager.get_postgres_connection()


def migrar_tabla_boletines():
    """
    Crear tabla de boletines en Supabase
    Migración desde SQLite
    """
    query = """
    CREATE TABLE IF NOT EXISTS boletines (
        id SERIAL PRIMARY KEY,
        titular VARCHAR(255) NOT NULL,
        numero_boletin VARCHAR(100),
        importancia VARCHAR(50) DEFAULT 'Pendiente',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_envio_reporte TIMESTAMP,
        reporte_enviado BOOLEAN DEFAULT FALSE,
        nombre_archivo_reporte VARCHAR(255),
        ruta_reporte VARCHAR(500),
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Crear índices para mejorar rendimiento
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_boletines_titular ON boletines(titular);",
        "CREATE INDEX IF NOT EXISTS idx_boletines_numero ON boletines(numero_boletin);",
        "CREATE INDEX IF NOT EXISTS idx_boletines_importancia ON boletines(importancia);",
        "CREATE INDEX IF NOT EXISTS idx_boletines_fecha_creacion ON boletines(fecha_creacion);",
    ]
    
    try:
        # Ejecutar creación de tabla
        supabase_manager.execute_query(query)
        st.success("✅ Tabla 'boletines' creada en Supabase")
        
        # Crear índices
        for indice in indices:
            supabase_manager.execute_query(indice)
        
        st.success("✅ Índices creados correctamente")
        
    except Exception as e:
        st.error(f"❌ Error creando tabla boletines: {e}")


def migrar_tabla_clientes():
    """
    Crear tabla de clientes en Supabase
    """
    query = """
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        titular VARCHAR(255) NOT NULL UNIQUE,
        email VARCHAR(255),
        activo BOOLEAN DEFAULT TRUE,
        fecha_ultimo_reporte TIMESTAMP,
        total_reportes INTEGER DEFAULT 0,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_clientes_titular ON clientes(titular);",
        "CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);",
        "CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo);",
    ]
    
    try:
        supabase_manager.execute_query(query)
        st.success("✅ Tabla 'clientes' creada en Supabase")
        
        for indice in indices:
            supabase_manager.execute_query(indice)
            
    except Exception as e:
        st.error(f"❌ Error creando tabla clientes: {e}")


def migrar_tabla_emails_enviados():
    """
    Crear tabla de emails enviados en Supabase
    """
    query = """
    CREATE TABLE IF NOT EXISTS emails_enviados (
        id SERIAL PRIMARY KEY,
        titular VARCHAR(255),
        destinatario VARCHAR(255) NOT NULL,
        asunto VARCHAR(500) NOT NULL,
        mensaje TEXT NOT NULL,
        tipo_email VARCHAR(100) DEFAULT 'general',
        status VARCHAR(50) DEFAULT 'pendiente',
        fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        error_mensaje TEXT,
        numero_boletin VARCHAR(100),
        ruta_archivo VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_emails_titular ON emails_enviados(titular);",
        "CREATE INDEX IF NOT EXISTS idx_emails_destinatario ON emails_enviados(destinatario);",
        "CREATE INDEX IF NOT EXISTS idx_emails_status ON emails_enviados(status);",
        "CREATE INDEX IF NOT EXISTS idx_emails_fecha ON emails_enviados(fecha_envio);",
    ]
    
    try:
        supabase_manager.execute_query(query)
        st.success("✅ Tabla 'emails_enviados' creada en Supabase")
        
        for indice in indices:
            supabase_manager.execute_query(indice)
            
    except Exception as e:
        st.error(f"❌ Error creando tabla emails_enviados: {e}")


def crear_todas_las_tablas():
    """
    Crear todas las tablas necesarias en Supabase
    Función equivalente a crear_tabla() de SQLite
    """
    try:
        migrar_tabla_boletines()
        migrar_tabla_clientes()
        migrar_tabla_emails_enviados()
        st.success("🎉 Todas las tablas han sido creadas en Supabase")
        
    except Exception as e:
        st.error(f"❌ Error en migración completa: {e}")


# Funciones de compatibilidad con el código existente
def crear_conexion():
    """
    Función de compatibilidad - devuelve conexión PostgreSQL
    Mantiene la interfaz del código SQLite existente
    """
    return crear_conexion_postgres()


def crear_tabla(conn=None):
    """
    Función de compatibilidad - crea todas las tablas
    Mantiene la interfaz del código SQLite existente
    """
    crear_todas_las_tablas()


# Funciones auxiliares para migración de datos
def exportar_datos_sqlite():
    """
    Exportar datos desde SQLite para migración
    """
    import sqlite3
    import pandas as pd
    
    try:
        # Conectar a SQLite existente
        sqlite_conn = sqlite3.connect('boletines.db')
        
        # Exportar cada tabla
        tablas = ['boletines', 'clientes', 'emails_enviados']
        datos_exportados = {}
        
        for tabla in tablas:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {tabla}", sqlite_conn)
                datos_exportados[tabla] = df
                st.info(f"📊 {tabla}: {len(df)} registros exportados")
            except Exception as e:
                st.warning(f"⚠️ No se pudo exportar {tabla}: {e}")
        
        sqlite_conn.close()
        return datos_exportados
        
    except Exception as e:
        st.error(f"❌ Error exportando datos de SQLite: {e}")
        return {}


def importar_datos_a_supabase(datos_exportados: Dict[str, Any]):
    """
    Importar datos exportados a Supabase
    """
    supabase = crear_conexion_supabase()
    if not supabase:
        st.error("❌ No se pudo conectar con Supabase")
        return
    
    for tabla, df in datos_exportados.items():
        try:
            # Convertir DataFrame a lista de diccionarios
            registros = df.to_dict('records')
            
            # Insertar datos usando el SDK de Supabase
            for registro in registros:
                # Limpiar valores None y ajustar tipos
                registro_limpio = {k: v for k, v in registro.items() if v is not None}
                
                result = supabase.table(tabla).insert(registro_limpio).execute()
                
            st.success(f"✅ {tabla}: {len(registros)} registros migrados")
            
        except Exception as e:
            st.error(f"❌ Error migrando {tabla}: {e}")
