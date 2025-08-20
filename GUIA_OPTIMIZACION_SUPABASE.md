# Optimización de Rendimiento para Aplicación Streamlit con Supabase/PostgreSQL

Este documento presenta una guía completa para implementar las optimizaciones de rendimiento en la aplicación, resolviendo los problemas de consultas lentas en Supabase (PostgreSQL).

## Índice

1. [Diagnóstico de Problemas](#diagnóstico-de-problemas)
2. [Optimización de Consultas SQL](#optimización-de-consultas-sql)
3. [Implementación de Índices](#implementación-de-índices)
4. [Paginación de Resultados](#paginación-de-resultados)
5. [Implementación de Caché en Streamlit](#implementación-de-caché-en-streamlit)
6. [Pool de Conexiones](#pool-de-conexiones)
7. [Integración de Cambios](#integración-de-cambios)

## Diagnóstico de Problemas

Los principales problemas identificados en la aplicación son:

1. **Consultas sin optimizar**: Se utilizan `SELECT *` y no se filtran columnas necesarias
2. **Falta de índices**: No hay índices en columnas de filtrado frecuente como CUIT, Titular, Fecha
3. **Carga completa de datos**: No se implementa paginación al cargar tablas
4. **Sin caché**: No se aprovecha el sistema de caché de Streamlit
5. **Conexiones ineficientes**: Se abren/cierran conexiones en cada operación

## Optimización de Consultas SQL

### Reemplazar SELECT * por columnas específicas

```python
# Antes
cursor.execute("SELECT * FROM boletines")

# Después
cursor.execute("""
    SELECT id, numero_boletin, titular, fecha_boletin, 
           numero_orden, marca_publicada, importancia
    FROM boletines
""")
```

### Añadir LIMIT y filtros apropiados

```python
# Antes
cursor.execute("SELECT * FROM clientes")

# Después
cursor.execute("""
    SELECT id, titular, email, telefono, cuit
    FROM clientes
    ORDER BY titular
    LIMIT %s OFFSET %s
""", (page_size, offset))
```

## Implementación de Índices

Se han creado índices para mejorar el rendimiento de las consultas frecuentes:

```sql
-- Índices para la tabla boletines
CREATE INDEX IF NOT EXISTS idx_boletines_titular ON boletines (titular);
CREATE INDEX IF NOT EXISTS idx_boletines_fecha ON boletines (fecha_boletin);
CREATE INDEX IF NOT EXISTS idx_boletines_importancia ON boletines (importancia);
CREATE INDEX IF NOT EXISTS idx_boletines_reportes ON boletines (reporte_generado, reporte_enviado);
CREATE INDEX IF NOT EXISTS idx_boletines_marca ON boletines (marca_publicada);

-- Índices para la tabla clientes
CREATE INDEX IF NOT EXISTS idx_clientes_titular ON clientes (titular);
CREATE INDEX IF NOT EXISTS idx_clientes_cuit ON clientes (cuit);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes (email);

-- Índices para la tabla emails_enviados
CREATE INDEX IF NOT EXISTS idx_emails_fecha ON emails_enviados (fecha_envio);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails_enviados (status);
```

El script `src/utils/db_indexer.py` implementa la creación de estos índices.

## Paginación de Resultados

Se ha implementado paginación en todas las consultas de listado:

```python
def obtener_clientes_optimizado(conn, page=1, page_size=50, filtro=None):
    """Versión optimizada con paginación"""
    # Calcular offset para paginación
    offset = (page - 1) * page_size
    
    # Consulta base
    query = """
        SELECT id, titular, email, telefono, cuit
        FROM clientes
    """
    
    # Añadir filtros si existen
    params = []
    where_clauses = []
    
    if filtro:
        # Implementación de filtros
        # ...
        
    # Añadir paginación
    query += " ORDER BY titular LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    
    # Ejecutar consulta
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Obtener total de registros para meta-información de paginación
    # ...
    
    return rows, columns, pagination_info
```

## Implementación de Caché en Streamlit

Se ha implementado el decorador `@st.cache_data` para funciones que obtienen datos:

```python
@st.cache_data(ttl=300)  # Caché durante 5 minutos
def obtener_estadisticas(conn):
    """Obtiene estadísticas del sistema de manera optimizada"""
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
```

## Pool de Conexiones

Se ha implementado un pool de conexiones para optimizar la gestión de conexiones:

```python
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
        # Configuración...
        
    def get_connection(self):
        """Obtiene una conexión del pool"""
        # Implementación...
        
    def return_connection(self, connection):
        """Devuelve una conexión al pool"""
        # Implementación...
```

Para usar el pool, se reemplaza el patrón de creación/cierre de conexiones:

```python
# Antes
def function_requiring_db():
    conn = crear_conexion()
    try:
        # código que usa conn
    finally:
        conn.close()

# Después
def function_requiring_db():
    pool = ConnectionPool.get_instance()
    conn = pool.get_connection()
    try:
        # código que usa conn
    finally:
        pool.return_connection(conn)
```

## Integración de Cambios

Para integrar estas optimizaciones, sigue estos pasos:

1. **Copia los nuevos archivos** a tu proyecto:
   - `src/utils/db_optimizations.py`
   - `src/utils/connection_pool.py` 
   - `src/utils/db_indexer.py`

2. **Actualiza tu página de Supabase** con las opciones de optimización

3. **Ejecuta la creación de índices** desde la interfaz de usuario

4. **Reemplaza tus funciones de obtención de datos** con las versiones optimizadas

5. **Implementa el caché** en funciones que obtienen datos que no cambian frecuentemente

## Ejemplo de Uso

Así es como se verían las llamadas a las nuevas funciones optimizadas:

```python
# Importar utilidades optimizadas
from src.utils.db_optimizations import obtener_clientes_optimizado
from src.utils.connection_pool import optimized_db_client

# En una función de UI de Streamlit
def show_clientes_page():
    # Controles de paginación
    page = st.session_state.get('page', 1)
    page_size = st.session_state.get('page_size', 25)
    
    # Filtros (opcional)
    filtro = {}
    if st.session_state.get('search_query'):
        filtro['titular'] = st.session_state['search_query']
    
    # Obtener datos paginados
    rows, columns, pagination = obtener_clientes_optimizado(
        conn,
        page=page,
        page_size=page_size,
        filtro=filtro
    )
    
    # Mostrar datos en una tabla
    df = pd.DataFrame(rows, columns=columns)
    st.dataframe(df)
    
    # Controles de paginación
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Anterior", disabled=page <= 1):
            st.session_state['page'] -= 1
            st.experimental_rerun()
    
    with col2:
        if st.button("Siguiente", disabled=page >= pagination['total_pages']):
            st.session_state['page'] += 1
            st.experimental_rerun()
```

Para cualquier pregunta o aclaración adicional sobre estas optimizaciones, consulta la documentación incluida en los archivos de código.
