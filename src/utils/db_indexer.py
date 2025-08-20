"""
Script para crear índices y optimizar el esquema en PostgreSQL (Supabase)
"""
import os
import streamlit as st
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Cargar variables de entorno
load_dotenv()

def get_postgres_connection():
    """Obtener conexión directa a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        st.error(f"Error conectando con PostgreSQL: {e}")
        return None

def crear_indices_optimizacion():
    """Crear índices para optimizar el rendimiento de las consultas"""
    conn = get_postgres_connection()
    if not conn:
        return False, "No se pudo conectar a la base de datos"
    
    cursor = None
    indices_creados = []
    try:
        cursor = conn.cursor()
        
        # Definir índices a crear
        indices = [
            # Tabla boletines - índices para las consultas más frecuentes
            {
                "nombre": "idx_boletines_titular",
                "tabla": "boletines",
                "columnas": "titular",
                "descripcion": "Índice para búsquedas por titular"
            },
            {
                "nombre": "idx_boletines_cuit",
                "tabla": "boletines",
                "columnas": "cuit",
                "descripcion": "Índice para búsquedas por CUIT"
            },
            {
                "nombre": "idx_boletines_fecha",
                "tabla": "boletines",
                "columnas": "fecha_boletin",
                "descripcion": "Índice para filtrar por fecha"
            },
            {
                "nombre": "idx_boletines_reportes",
                "tabla": "boletines",
                "columnas": "(reporte_generado, reporte_enviado)",
                "descripcion": "Índice para filtrar por estado de reportes"
            },
            {
                "nombre": "idx_boletines_importancia",
                "tabla": "boletines",
                "columnas": "importancia",
                "descripcion": "Índice para filtrar por importancia"
            },
            {
                "nombre": "idx_boletines_marca",
                "tabla": "boletines",
                "columnas": "marca_publicada",
                "descripcion": "Índice para búsquedas por marca"
            },
            
            # Tabla clientes - índices para búsquedas
            {
                "nombre": "idx_clientes_titular",
                "tabla": "clientes",
                "columnas": "titular",
                "descripcion": "Índice para búsquedas por titular"
            },
            {
                "nombre": "idx_clientes_cuit",
                "tabla": "clientes",
                "columnas": "cuit",
                "descripcion": "Índice para búsquedas por CUIT"
            },
            {
                "nombre": "idx_clientes_email",
                "tabla": "clientes",
                "columnas": "email",
                "descripcion": "Índice para búsquedas por email"
            },
            
            # Tabla emails_enviados - índices para filtrado
            {
                "nombre": "idx_emails_fecha",
                "tabla": "emails_enviados",
                "columnas": "fecha_envio",
                "descripcion": "Índice para filtrar por fecha de envío"
            },
            {
                "nombre": "idx_emails_status",
                "tabla": "emails_enviados",
                "columnas": "status",
                "descripcion": "Índice para filtrar por estado de envío"
            }
        ]
        
        # Crear cada índice si no existe
        for indice in indices:
            try:
                # Verificar si el índice ya existe
                cursor.execute(
                    """
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = %s
                    """, 
                    (indice["nombre"],)
                )
                
                if cursor.fetchone() is None:
                    # Crear el índice
                    query = f"""
                    CREATE INDEX {indice["nombre"]} 
                    ON {indice["tabla"]} ({indice["columnas"]})
                    """
                    cursor.execute(query)
                    indices_creados.append(indice["nombre"])
                    st.success(f"✅ Índice {indice['nombre']} creado: {indice['descripcion']}")
                else:
                    st.info(f"ℹ️ Índice {indice['nombre']} ya existe")
            
            except Exception as e:
                st.error(f"❌ Error al crear índice {indice['nombre']}: {e}")
        
        # Analizar tablas para actualizar estadísticas
        tablas = ["boletines", "clientes", "emails_enviados"]
        for tabla in tablas:
            cursor.execute(f"ANALYZE {tabla}")
            st.info(f"📊 Estadísticas actualizadas para tabla: {tabla}")
        
        conn.commit()
        return True, f"Se crearon {len(indices_creados)} índices nuevos"
    
    except Exception as e:
        conn.rollback()
        logging.error(f"Error al crear índices: {e}")
        return False, f"Error al crear índices: {e}"
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def show_optimization_page():
    """Mostrar página de optimización de base de datos"""
    st.title("🚀 Optimización de PostgreSQL")
    st.markdown("Esta herramienta crea índices para optimizar el rendimiento de las consultas")
    st.warning("⚠️ Esta operación debe ejecutarse una sola vez o después de cambios en el esquema")
    
    with st.expander("ℹ️ Información sobre índices", expanded=True):
        st.markdown("""
        ### ¿Qué son los índices y por qué son importantes?
        Los índices aceleran las consultas SQL al crear estructuras de datos ordenadas para las columnas más consultadas.
        Esto permite a PostgreSQL encontrar rápidamente los registros que coinciden con tus criterios de búsqueda.
        
        ### Beneficios de los índices:
        - **Búsquedas más rápidas**: Reducen drásticamente el tiempo de consultas con filtros (`WHERE`)
        - **Joins eficientes**: Aceleran las operaciones de unión entre tablas
        - **Ordenamiento rápido**: Mejoran el rendimiento de `ORDER BY`
        
        ### Columnas indexadas en este proyecto:
        - **Boletines**: titular, cuit, fecha_boletin, importancia, marca_publicada
        - **Clientes**: titular, cuit, email
        - **Emails**: fecha_envio, status
        """)
    
    if st.button("🚀 Ejecutar Optimización", type="primary"):
        with st.spinner("Creando índices..."):
            success, message = crear_indices_optimizacion()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with st.expander("📊 Columnas más consultadas", expanded=False):
        st.markdown("""
        ### Columnas frecuentemente utilizadas en consultas:
        
        **Tabla `boletines`**:
        - `titular`: Usado en JOINs y filtros
        - `fecha_boletin`: Filtrado por fechas
        - `importancia`: Categorización de boletines
        - `reporte_generado`, `reporte_enviado`: Estados de reportes
        - `marca_publicada`: Búsquedas por marca
        
        **Tabla `clientes`**:
        - `titular`: Usado en JOINs
        - `cuit`: Identificador único
        - `email`: Para envío de notificaciones
        
        **Tabla `emails_enviados`**:
        - `fecha_envio`: Filtrado por fecha
        - `status`: Estado del envío
        """)

if __name__ == "__main__":
    show_optimization_page()
