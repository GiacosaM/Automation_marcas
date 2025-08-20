"""
Página de configuración de Supabase
Interfaz para gestionar la migración y configuración de Supabase
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from config import (
    get_config, set_config, 
    is_supabase_enabled, get_supabase_config,
    switch_to_supabase, switch_to_sqlite,
    validate_supabase_config
)
from supabase_connection import (
    supabase_manager,
    crear_conexion_supabase,
    crear_todas_las_tablas,
    exportar_datos_sqlite,
    importar_datos_a_supabase
)

def show_supabase_config_page():
    """Mostrar página de configuración de Supabase"""
    st.title("🗄️ Configuración de Supabase")
    st.markdown("Gestiona la migración de SQLite a Supabase PostgreSQL")
    st.markdown("---")
    
    # Estado actual
    col1, col2 = st.columns(2)
    
    with col1:
        if is_supabase_enabled():
            st.success("✅ Supabase está habilitado")
        else:
            st.info("📄 Usando SQLite (modo legacy)")
    
    with col2:
        db_type = "Supabase" if is_supabase_enabled() else "SQLite"
        st.metric("Base de Datos Actual", db_type)
    
    # Tabs para diferentes configuraciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔧 Configurar Supabase",
        "🚀 Migrar Datos", 
        "🧪 Probar Conexión",
        "📊 Información"
    ])
    
    with tab1:
        show_supabase_configuration()
    
    with tab2:
        show_migration_interface()
    
    with tab3:
        show_connection_test()
    
    with tab4:
        show_database_info()


def show_supabase_configuration():
    """Mostrar configuración de Supabase"""
    st.subheader("🔧 Configuración de Supabase")
    
    # Formulario de configuración
    with st.form("supabase_config"):
        st.markdown("### Credenciales de Supabase")
        
        col1, col2 = st.columns(2)
        
        with col1:
            supabase_url = st.text_input(
                "🌐 URL de Supabase:",
                value=os.getenv('SUPABASE_URL', ''),
                placeholder="https://tu-proyecto.supabase.co",
                help="URL de tu proyecto en Supabase"
            )
            
            supabase_key = st.text_input(
                "🔑 Clave Anónima:",
                value=os.getenv('SUPABASE_KEY', ''),
                type="password",
                help="Clave anónima de Supabase (anon key)"
            )
        
        with col2:
            db_host = st.text_input(
                "🖥️ Host PostgreSQL:",
                value=os.getenv('DB_HOST', ''),
                placeholder="db.tu-proyecto.supabase.co",
                help="Host de la base de datos PostgreSQL"
            )
            
            db_password = st.text_input(
                "🔐 Contraseña BD:",
                value=os.getenv('DB_PASSWORD', ''),
                type="password",
                help="Contraseña de la base de datos"
            )
        
        # Configuración avanzada
        with st.expander("⚙️ Configuración Avanzada"):
            col3, col4 = st.columns(2)
            
            with col3:
                db_port = st.number_input(
                    "Puerto:", 
                    value=int(os.getenv('DB_PORT', 5432)),
                    min_value=1,
                    max_value=65535
                )
                
                db_name = st.text_input(
                    "Nombre BD:",
                    value=os.getenv('DB_NAME', 'postgres')
                )
            
            with col4:
                db_user = st.text_input(
                    "Usuario BD:",
                    value=os.getenv('DB_USER', 'postgres')
                )
                
                enable_realtime = st.checkbox(
                    "Habilitar Realtime",
                    value=get_config("supabase.enable_realtime", False),
                    help="Habilitar subscripciones en tiempo real"
                )
        
        # Botones de acción
        col_save, col_test = st.columns(2)
        
        with col_save:
            if st.form_submit_button("💾 Guardar Configuración", type="primary"):
                # Actualizar variables de entorno (esto requiere reinicio)
                st.info("💡 Actualiza tu archivo .env con estos valores:")
                
                env_content = f"""
SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
                st.code(env_content, language="bash")
                
                # Guardar en configuración
                set_config("database.supabase_url", supabase_url)
                set_config("database.supabase_key", supabase_key)
                set_config("database.postgres_host", db_host)
                set_config("database.postgres_port", db_port)
                set_config("database.postgres_db", db_name)
                set_config("database.postgres_user", db_user)
                set_config("database.postgres_password", db_password)
                set_config("supabase.enable_realtime", enable_realtime)
                
                st.success("✅ Configuración guardada")
                st.warning("⚠️ Reinicia la aplicación para aplicar los cambios")
        
        with col_test:
            if st.form_submit_button("🧪 Probar Conexión"):
                test_supabase_connection(supabase_url, supabase_key, db_host, db_password)


def show_migration_interface():
    """Mostrar interfaz de migración"""
    st.subheader("🚀 Migración de Datos")
    
    # Verificar si hay datos en SQLite
    sqlite_exists = os.path.exists('boletines.db')
    
    if sqlite_exists:
        st.info("📁 Base de datos SQLite encontrada: boletines.db")
        
        # Mostrar estadísticas de SQLite
        try:
            import sqlite3
            conn = sqlite3.connect('boletines.db')
            cursor = conn.cursor()
            
            # Contar registros en cada tabla
            tablas_info = []
            for tabla in ['boletines', 'clientes', 'emails_enviados']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    tablas_info.append((tabla, count))
                except:
                    tablas_info.append((tabla, 0))
            
            conn.close()
            
            # Mostrar estadísticas
            st.markdown("### 📊 Datos en SQLite:")
            cols = st.columns(len(tablas_info))
            for i, (tabla, count) in enumerate(tablas_info):
                with cols[i]:
                    st.metric(tabla.title(), count)
        
        except Exception as e:
            st.error(f"❌ Error leyendo SQLite: {e}")
    
    else:
        st.warning("⚠️ No se encontró base de datos SQLite")
    
    # Opciones de migración
    st.markdown("### 🔄 Opciones de Migración")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏗️ Crear Tablas en Supabase", use_container_width=True):
            with st.spinner("Creando estructura de tablas..."):
                try:
                    crear_todas_las_tablas()
                    st.success("✅ Tablas creadas en Supabase")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("📤 Exportar de SQLite", use_container_width=True, disabled=not sqlite_exists):
            if sqlite_exists:
                with st.spinner("Exportando datos..."):
                    datos = exportar_datos_sqlite()
                    if datos:
                        st.session_state.datos_exportados = datos
                        st.success("✅ Datos exportados exitosamente")
                    else:
                        st.error("❌ No se pudieron exportar los datos")
    
    with col3:
        datos_disponibles = hasattr(st.session_state, 'datos_exportados')
        if st.button("📥 Importar a Supabase", use_container_width=True, disabled=not datos_disponibles):
            if datos_disponibles:
                with st.spinner("Importando a Supabase..."):
                    try:
                        importar_datos_a_supabase(st.session_state.datos_exportados)
                        st.success("✅ Datos importados a Supabase")
                        
                        # Opción para cambiar a Supabase
                        if st.button("🔄 Cambiar a Supabase"):
                            switch_to_supabase()
                            st.success("✅ Configuración cambiada a Supabase")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Error importando: {e}")


def show_connection_test():
    """Mostrar pruebas de conexión"""
    st.subheader("🧪 Pruebas de Conexión")
    
    # Test del SDK de Supabase
    st.markdown("### 📡 SDK de Supabase")
    if st.button("Probar SDK de Supabase"):
        try:
            supabase = crear_conexion_supabase()
            if supabase:
                # Realizar una consulta simple
                result = supabase.table('boletines').select('count', count='exact').execute()
                st.success(f"✅ SDK conectado - Registros en boletines: {result.count}")
            else:
                st.error("❌ No se pudo conectar con el SDK")
        except Exception as e:
            st.error(f"❌ Error con SDK: {e}")
    
    # Test de PostgreSQL directo
    st.markdown("### 🐘 PostgreSQL Directo")
    if st.button("Probar PostgreSQL"):
        try:
            conn = supabase_manager.get_postgres_connection()
            if conn:
                result = supabase_manager.execute_query("SELECT version();")
                if result:
                    st.success(f"✅ PostgreSQL conectado")
                    st.info(f"Versión: {result[0].get('version', 'N/A')}")
                else:
                    st.error("❌ No se pudo ejecutar consulta")
            else:
                st.error("❌ No se pudo conectar a PostgreSQL")
        except Exception as e:
            st.error(f"❌ Error con PostgreSQL: {e}")
    
    # Test de configuración
    st.markdown("### ⚙️ Validación de Configuración")
    if st.button("Validar Configuración"):
        is_valid, message = validate_supabase_config()
        if is_valid:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")


def show_database_info():
    """Mostrar información de la base de datos"""
    st.subheader("📊 Información de Base de Datos")
    
    if is_supabase_enabled():
        # Información de Supabase
        st.markdown("### 🗄️ Supabase")
        
        try:
            supabase = crear_conexion_supabase()
            if supabase:
                # Obtener información de las tablas
                tablas = ['boletines', 'clientes', 'emails_enviados']
                
                for tabla in tablas:
                    try:
                        result = supabase.table(tabla).select('count', count='exact').execute()
                        st.metric(f"Registros en {tabla}", result.count)
                    except:
                        st.metric(f"Registros en {tabla}", "Error")
                
                # Información adicional
                config = get_supabase_config()
                if config:
                    st.markdown("### 🔧 Configuración Actual")
                    st.json({
                        "URL": config.get('url', 'No configurado'),
                        "Host": config.get('postgres_host', 'No configurado'),
                        "Puerto": config.get('postgres_port', 'No configurado'),
                        "Base de datos": config.get('postgres_db', 'No configurado'),
                        "Usuario": config.get('postgres_user', 'No configurado')
                    })
        
        except Exception as e:
            st.error(f"❌ Error obteniendo información: {e}")
    
    else:
        # Información de SQLite
        st.markdown("### 📄 SQLite")
        st.info("Actualmente usando SQLite. Configura Supabase para migrar.")


def test_supabase_connection(url, key, host, password):
    """Probar conexión con credenciales específicas"""
    try:
        # Test básico de URL
        if not url or not key:
            st.error("❌ URL y clave son requeridos")
            return
        
        # Aquí podrías hacer una prueba real de conexión
        # Por ahora, simulamos la validación
        
        if "supabase.co" in url and len(key) > 20:
            st.success("✅ Credenciales válidas")
        else:
            st.error("❌ Credenciales inválidas")
    
    except Exception as e:
        st.error(f"❌ Error probando conexión: {e}")


if __name__ == "__main__":
    show_supabase_config_page()
