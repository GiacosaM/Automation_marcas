#!/usr/bin/env python3
"""
Script de migración de SQLite a Supabase
Ejecutar después de configurar las variables de entorno
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Agregar directorio del proyecto al path
sys.path.append(os.path.dirname(__file__))

from supabase_connection import (
    crear_todas_las_tablas,
    exportar_datos_sqlite,
    importar_datos_a_supabase,
    supabase_manager
)


def verificar_configuracion():
    """Verificar que las variables de entorno están configuradas"""
    variables_requeridas = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'DB_HOST',
        'DB_PASSWORD'
    ]
    
    faltantes = []
    for var in variables_requeridas:
        if not os.getenv(var):
            faltantes.append(var)
    
    if faltantes:
        st.error(f"❌ Faltan variables de entorno: {', '.join(faltantes)}")
        st.info("📋 Configura el archivo .env con tus credenciales de Supabase")
        return False
    
    st.success("✅ Configuración verificada")
    return True


def ejecutar_migracion():
    """Ejecutar el proceso completo de migración"""
    st.title("🚀 Migración de SQLite a Supabase")
    st.markdown("---")
    
    # Verificar configuración
    st.subheader("1. Verificación de Configuración")
    if not verificar_configuracion():
        return
    
    # Crear tablas en Supabase
    st.subheader("2. Creación de Tablas en Supabase")
    with st.spinner("Creando estructura de base de datos..."):
        crear_todas_las_tablas()
    
    # Opción para migrar datos existentes
    st.subheader("3. Migración de Datos")
    
    if os.path.exists('boletines.db'):
        st.info("📁 Base de datos SQLite encontrada: boletines.db")
        
        if st.button("🔄 Migrar Datos desde SQLite", type="primary"):
            with st.spinner("Exportando datos desde SQLite..."):
                datos = exportar_datos_sqlite()
            
            if datos:
                with st.spinner("Importando datos a Supabase..."):
                    importar_datos_a_supabase(datos)
                
                st.success("🎉 Migración completada exitosamente")
                
                # Crear backup de SQLite
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"boletines_backup_{timestamp}.db"
                
                try:
                    import shutil
                    shutil.copy2('boletines.db', backup_name)
                    st.info(f"📦 Backup creado: {backup_name}")
                except Exception as e:
                    st.warning(f"⚠️ No se pudo crear backup: {e}")
            else:
                st.warning("⚠️ No se encontraron datos para migrar")
    else:
        st.info("📝 No se encontró base de datos SQLite existente")
        st.success("✅ Las tablas están listas para usar con Supabase")
    
    # Información adicional
    st.subheader("4. Próximos Pasos")
    st.markdown("""
    ### 📋 Tareas pendientes después de la migración:
    
    1. **Actualizar imports en el código:**
       ```python
       # Cambiar:
       from database import crear_conexion, crear_tabla
       
       # Por:
       from supabase_connection import crear_conexion_supabase, crear_todas_las_tablas
       ```
    
    2. **Configurar autenticación (opcional):**
       - Habilitar Row Level Security (RLS) en Supabase
       - Configurar políticas de acceso
    
    3. **Optimizar queries:**
       - Aprovechar las funciones de Supabase SDK
       - Implementar subscripciones en tiempo real si es necesario
    
    4. **Configurar backups automáticos:**
       - Los backups están habilitados por defecto en Supabase
       - Configurar retención según tus necesidades
    
    ### 🔧 Variables de entorno necesarias:
    - `SUPABASE_URL`: URL de tu proyecto Supabase
    - `SUPABASE_KEY`: Clave anónima de Supabase
    - `DB_HOST`: Host de la base de datos PostgreSQL
    - `DB_PASSWORD`: Contraseña de la base de datos
    """)


if __name__ == "__main__":
    ejecutar_migracion()
