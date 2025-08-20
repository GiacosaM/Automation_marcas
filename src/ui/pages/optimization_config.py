"""
Página de configuración de optimización para la aplicación
"""
import streamlit as st
import os
import json
import time

def show_optimization_config():
    """Mostrar opciones de configuración para las optimizaciones"""
    st.title("⚙️ Configuración de Optimización")
    
    # Cargar configuración actual
    config = load_optimization_config()
    
    # Configuración general
    st.subheader("🔧 Configuración General")
    
    use_optimized = st.checkbox(
        "Usar versiones optimizadas de páginas",
        value=config.get("use_optimized_pages", False),
        help="Activar para usar versiones optimizadas de las páginas de la aplicación"
    )
    
    # Configuración de caché
    st.subheader("🧠 Configuración de Caché")
    
    cache_ttl = st.slider(
        "Tiempo de vida de caché (segundos)",
        min_value=10,
        max_value=600,
        value=config.get("cache", {}).get("ttl", 60),
        step=10,
        help="Tiempo que los datos permanecen en caché antes de actualizarse"
    )
    
    cache_dashboard = st.checkbox(
        "Habilitar caché para dashboard",
        value=config.get("cache", {}).get("dashboard_enabled", True),
        help="Mantener en caché las estadísticas del dashboard"
    )
    
    cache_lists = st.checkbox(
        "Habilitar caché para listados",
        value=config.get("cache", {}).get("lists_enabled", True),
        help="Mantener en caché las listas de datos (clientes, boletines, etc.)"
    )
    
    # Configuración de pool de conexiones
    st.subheader("🔄 Pool de Conexiones")
    
    min_connections = st.number_input(
        "Conexiones mínimas",
        min_value=1,
        max_value=5,
        value=config.get("database", {}).get("pool_min_connections", 2),
        help="Número mínimo de conexiones mantenidas en el pool"
    )
    
    max_connections = st.number_input(
        "Conexiones máximas",
        min_value=5,
        max_value=20,
        value=config.get("database", {}).get("pool_max_connections", 10),
        help="Número máximo de conexiones permitidas en el pool"
    )
    
    # Guardar configuración
    if st.button("💾 Guardar Configuración", type="primary"):
        # Actualizar configuración
        config["use_optimized_pages"] = use_optimized
        config["cache"] = config.get("cache", {})
        config["cache"]["ttl"] = cache_ttl
        config["cache"]["dashboard_enabled"] = cache_dashboard
        config["cache"]["lists_enabled"] = cache_lists
        config["database"] = config.get("database", {})
        config["database"]["pool_min_connections"] = min_connections
        config["database"]["pool_max_connections"] = max_connections
        
        # Guardar en archivo
        save_optimization_config(config)
        
        st.success("✅ Configuración guardada correctamente")
        st.info("💡 Reinicia la aplicación para aplicar los cambios")

def load_optimization_config():
    """Cargar configuración de optimización"""
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
        else:
            config = {}
    except Exception as e:
        st.error(f"Error al cargar configuración: {e}")
        config = {}
    
    return config

def save_optimization_config(config):
    """Guardar configuración de optimización"""
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración: {e}")
        return False

if __name__ == "__main__":
    show_optimization_config()
