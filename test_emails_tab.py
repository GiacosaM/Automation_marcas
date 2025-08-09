#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de la pestaña de emails enviados
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Importar módulos locales
from database import crear_conexion, obtener_emails_enviados, obtener_ruta_reporte_pdf

def test_emails_tab():
    """Prueba específica de la pestaña de emails enviados"""
    
    st.title("🧪 Prueba: Pestaña Emails Enviados")
    
    # Conectar a la base de datos
    conn = crear_conexion()
    if not conn:
        st.error("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        st.subheader("1. 🔍 Prueba de función obtener_emails_enviados")
        
        # Obtener emails enviados
        emails_enviados = obtener_emails_enviados(conn, limite=10)
        
        if emails_enviados:
            st.success(f"✅ Se encontraron {len(emails_enviados)} emails enviados")
            
            # Mostrar información detallada
            st.subheader("2. 📧 Información de Emails")
            
            for i, email in enumerate(emails_enviados):
                with st.expander(f"Email {i+1}: {email['titular']}", expanded=i==0):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Información básica:**")
                        st.write(f"- ID: {email['id']}")
                        st.write(f"- Titular: {email['titular']}")
                        st.write(f"- Email: {email['email']}")
                        st.write(f"- Fecha envío: {email['fecha_envio']}")
                        st.write(f"- Total boletines: {email['total_boletines']}")
                    
                    with col2:
                        st.write("**Detalles adicionales:**")
                        if email.get('importancias_boletines'):
                            st.write(f"- Importancias: {email['importancias_boletines']}")
                        if email.get('fecha_primer_boletin'):
                            st.write(f"- Primer boletín: {email['fecha_primer_boletin']}")
                        if email.get('fecha_ultimo_boletin'):
                            st.write(f"- Último boletín: {email['fecha_ultimo_boletin']}")
                        if email.get('numeros_boletines'):
                            st.write(f"- Boletines: {len(email['numeros_boletines'])} números")
                    
                    # Probar función de obtener PDF
                    st.write("**3. 📄 Prueba de obtención de PDF:**")
                    ruta_pdf = obtener_ruta_reporte_pdf(email['titular'], email['fecha_envio'])
                    
                    if ruta_pdf:
                        st.write(f"- Ruta PDF: {ruta_pdf}")
                        if os.path.exists(ruta_pdf):
                            st.success("✅ Archivo PDF encontrado")
                            # Mostrar información del archivo
                            size = os.path.getsize(ruta_pdf)
                            st.write(f"- Tamaño: {size:,} bytes")
                            st.write(f"- Modificado: {datetime.fromtimestamp(os.path.getmtime(ruta_pdf))}")
                        else:
                            st.warning("⚠️ Archivo PDF no existe en la ruta")
                    else:
                        st.error("❌ No se pudo determinar la ruta del PDF")
        
        else:
            st.warning("⚠️ No se encontraron emails enviados")
            
            # Verificar si hay datos en las tablas relacionadas
            st.subheader("3. 🔍 Diagnóstico de Datos")
            
            cursor = conn.cursor()
            
            # Verificar tabla envios_log
            cursor.execute("SELECT COUNT(*) FROM envios_log")
            count_envios = cursor.fetchone()[0]
            st.write(f"- Registros en envios_log: {count_envios}")
            
            # Verificar tabla boletines
            cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
            count_boletines_enviados = cursor.fetchone()[0]
            st.write(f"- Boletines marcados como enviados: {count_boletines_enviados}")
            
            # Verificar tabla clientes
            cursor.execute("SELECT COUNT(*) FROM clientes")
            count_clientes = cursor.fetchone()[0]
            st.write(f"- Total clientes: {count_clientes}")
            
            cursor.close()
    
    except Exception as e:
        st.error(f"❌ Error durante la prueba: {e}")
        st.exception(e)
    
    finally:
        conn.close()

def test_tab_structure():
    """Prueba la estructura de pestañas"""
    st.title("🧪 Prueba: Estructura de Pestañas")
    
    # Crear pestañas de prueba
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 Enviar Emails", 
        "⚙️ Configuración", 
        "📊 Historial de Envíos", 
        "📋 Logs Detallados", 
        "📁 Emails Enviados"
    ])
    
    with tab1:
        st.write("✅ Tab 1 funciona correctamente")
    
    with tab2:
        st.write("✅ Tab 2 funciona correctamente")
    
    with tab3:
        st.write("✅ Tab 3 funciona correctamente")
    
    with tab4:
        st.write("✅ Tab 4 funciona correctamente")
    
    with tab5:
        st.write("✅ Tab 5 (Emails Enviados) funciona correctamente")
        test_emails_tab()

if __name__ == "__main__":
    # Configurar página
    st.set_page_config(
        page_title="Test Emails Tab",
        page_icon="🧪",
        layout="wide"
    )
    
    # Menú principal
    option = st.selectbox(
        "🔧 Selecciona qué probar:",
        ["Estructura de Pestañas", "Función Emails Enviados"]
    )
    
    if option == "Estructura de Pestañas":
        test_tab_structure()
    else:
        test_emails_tab()
