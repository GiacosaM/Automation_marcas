"""
Página de optimización de rendimiento para PostgreSQL/Supabase
"""
import streamlit as st
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Importar utilidades de optimización
from src.utils.db_indexer import show_optimization_page
from src.utils.db_optimizations import obtener_estadisticas

def show_optimization_page():
    """Mostrar página de optimización de rendimiento"""
    st.title("⚡ Optimización de Rendimiento")
    st.markdown("Herramientas para mejorar el rendimiento de la aplicación con PostgreSQL/Supabase")
    
    # Tabs para diferentes secciones de optimización
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Índices y Estructura", 
        "🔄 Conexiones y Caché", 
        "📊 Monitoreo",
        "⚙️ Configuración"
    ])
    
    with tab1:
        # Utilizar la función de db_indexer.py
        show_optimization_page()
    
    with tab2:
        show_connection_optimization()
    
    with tab3:
        show_performance_monitoring()
        
    with tab4:
        # Importar y usar la página de configuración
        from src.ui.pages.optimization_config import show_optimization_config
        show_optimization_config()

def show_connection_optimization():
    """Mostrar opciones de optimización de conexiones"""
    st.subheader("🔄 Optimización de Conexiones y Caché")
    
    # Información sobre pool de conexiones
    st.markdown("""
    ### Pool de Conexiones
    
    El pool de conexiones permite reutilizar conexiones a la base de datos en lugar de crear/cerrar conexiones para cada operación,
    lo que reduce significativamente la latencia y mejora el rendimiento.
    
    La implementación del pool está en `src/utils/connection_pool.py` y ya está integrada con las funciones optimizadas.
    """)
    
    # Configuración del pool
    st.markdown("#### Configuración del Pool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_conn = st.number_input(
            "Conexiones mínimas", 
            min_value=1, 
            max_value=5, 
            value=2,
            help="Número mínimo de conexiones que se mantienen en el pool"
        )
    
    with col2:
        max_conn = st.number_input(
            "Conexiones máximas", 
            min_value=5, 
            max_value=20, 
            value=10,
            help="Número máximo de conexiones permitidas en el pool"
        )
    
    if st.button("Guardar configuración del pool"):
        # Guardar en un archivo de configuración (implementación ejemplo)
        try:
            import json
            config = {}
            
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
            
            config["database"] = config.get("database", {})
            config["database"]["pool_min_connections"] = min_conn
            config["database"]["pool_max_connections"] = max_conn
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            st.success("✅ Configuración del pool guardada correctamente")
        except Exception as e:
            st.error(f"❌ Error al guardar la configuración: {e}")
    
    # Información sobre caché
    st.markdown("""
    ### Caché en Streamlit
    
    El uso adecuado de la caché de Streamlit puede mejorar drásticamente el rendimiento, evitando la ejecución repetida 
    de consultas a la base de datos cuando los datos no han cambiado.
    
    Las funciones optimizadas ya incluyen caché con el decorador `@st.cache_data`.
    """)
    
    # Configuración de caché
    st.markdown("#### Configuración de Caché")
    
    ttl = st.slider(
        "Tiempo de vida de la caché (segundos)", 
        min_value=10, 
        max_value=600, 
        value=60,
        step=10,
        help="Tiempo que los datos permanecen en caché antes de ser refrescados"
    )
    
    if st.button("Guardar configuración de caché"):
        try:
            import json
            config = {}
            
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
            
            config["cache"] = config.get("cache", {})
            config["cache"]["ttl"] = ttl
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            st.success("✅ Configuración de caché guardada correctamente")
        except Exception as e:
            st.error(f"❌ Error al guardar la configuración: {e}")
    
    st.info("💡 Reinicia la aplicación para aplicar los cambios de configuración")

def show_performance_monitoring():
    """Mostrar monitoreo de rendimiento"""
    st.subheader("📊 Monitoreo de Rendimiento")
    
    # Verificar si existe el archivo de log
    log_path = "performance.log"
    if not os.path.exists(log_path):
        st.warning("⚠️ No se encontró el archivo de monitoreo de rendimiento. Se creará cuando se ejecuten consultas optimizadas.")
    else:
        # Mostrar contenido del log
        st.markdown("### Registro de Rendimiento")
        
        with open(log_path, "r") as f:
            logs = f.readlines()
        
        if logs:
            # Mostrar las últimas 20 entradas
            st.code("".join(logs[-20:]), language="text")
            
            # Opción para limpiar logs
            if st.button("Limpiar logs de rendimiento"):
                try:
                    with open(log_path, "w") as f:
                        f.write("")
                    st.success("✅ Logs limpiados correctamente")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Error al limpiar logs: {e}")
        else:
            st.info("No hay registros de rendimiento disponibles")

if __name__ == "__main__":
    show_optimization_page()
