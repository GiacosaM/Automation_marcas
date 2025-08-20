#!/usr/bin/env python3
"""
Test simple de Streamlit con conexión a base de datos
"""

import streamlit as st
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.title("🔧 Test de Conexión a Base de Datos")

def test_connection():
    """Test básico de conexión"""
    try:
        # Importar módulos
        from database import crear_conexion, usar_supabase, convertir_query_boolean
        
        st.success("✅ Módulos importados correctamente")
        
        # Verificar configuración
        using_supabase = usar_supabase()
        st.info(f"🔗 Usando Supabase: {using_supabase}")
        
        # Crear conexión
        with st.spinner("Conectando a la base de datos..."):
            conn = crear_conexion()
            st.success(f"✅ Conexión establecida: {type(conn)}")
            
            # Test de query simple
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM boletines")
            total_boletines = cursor.fetchone()[0]
            st.metric("📊 Total Boletines", total_boletines)
            
            # Test de query con conversión
            query_convertida = convertir_query_boolean("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
            cursor.execute(query_convertida)
            reportes_generados = cursor.fetchone()[0]
            st.metric("📋 Reportes Generados", reportes_generados)
            
            cursor.close()
            conn.close()
            st.success("✅ Conexión cerrada correctamente")
            
            return True
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)
        return False

# Ejecutar test
if st.button("🚀 Probar Conexión") or True:  # Ejecutar automáticamente
    success = test_connection()
    
    if success:
        st.balloons()
        st.success("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        st.error("💥 Algunas pruebas fallaron")

# Mostrar información del entorno
with st.expander("ℹ️ Información del Sistema"):
    import os
    st.write("**Variables de entorno relevantes:**")
    env_vars = ['SUPABASE_URL', 'DB_HOST', 'DB_USER', 'DB_NAME']
    for var in env_vars:
        value = os.getenv(var, 'No definida')
        if var == 'DB_PASSWORD':
            value = value[:5] + "..." if value != 'No definida' else 'No definida'
        st.write(f"- {var}: `{value}`")
