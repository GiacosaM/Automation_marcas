#!/usr/bin/env python3
"""
Test directo de la funcionalidad de la sección de emails
"""

import streamlit as st
import sys
import os
sys.path.append('/Users/martingiacosa/Desktop/Proyectos/Python/Automation')

from database import crear_conexion, obtener_estadisticas_envios

def test_email_section():
    st.title("🧪 Test: Sección de Emails")
    
    # Verificar conexión a BD
    conn = crear_conexion()
    if not conn:
        st.error("❌ No se puede conectar a la base de datos")
        return
    
    try:
        # Obtener estadísticas
        stats = obtener_estadisticas_envios(conn)
        
        if stats:
            st.success("✅ Estadísticas obtenidas correctamente")
            
            # Mostrar estadísticas
            st.subheader("📊 Estadísticas Actuales")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Total Reportes", stats['total_reportes'])
                st.metric("📄 Generados", stats['reportes_generados'])
            with col2:
                st.metric("📧 Enviados", stats['reportes_enviados'])
                st.metric("⚠️ Pendientes Revisión", stats['pendientes_revision'])
            with col3:
                st.metric("🚀 Listos para Envío", stats['listos_envio'])
            
            # Mostrar condiciones
            st.subheader("🔍 Análisis de Condiciones")
            
            st.write("**Condición 1:** `stats['pendientes_revision'] == 0`")
            condicion1 = stats['pendientes_revision'] == 0
            st.write(f"  Resultado: {condicion1} (pendientes_revision = {stats['pendientes_revision']})")
            
            st.write("**Condición 2:** `stats['listos_envio'] > 0`")
            condicion2 = stats['listos_envio'] > 0
            st.write(f"  Resultado: {condicion2} (listos_envio = {stats['listos_envio']})")
            
            st.write("**Condición Combinada:** `pendientes_revision == 0 AND listos_envio > 0`")
            condicion_combinada = condicion1 and condicion2
            st.write(f"  Resultado: {condicion_combinada}")
            
            if condicion_combinada:
                st.success("✅ Las pestañas DEBERÍAN estar visibles")
            else:
                st.warning("⚠️ Las pestañas podrían estar ocultas por la condición")
                
            # Probar las pestañas independientemente
            st.subheader("🧪 Test de Pestañas")
            st.info("Las siguientes pestañas deberían aparecer independientemente de las condiciones:")
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🚀 Enviar Emails", 
                "⚙️ Configuración", 
                "📊 Historial de Envíos", 
                "📋 Logs Detallados", 
                "📁 Emails Enviados"
            ])
            
            with tab1:
                if condicion_combinada:
                    st.success("✅ Tab1: Contenido de envío disponible")
                    st.write("Aquí aparecería el contenido de envío de emails")
                else:
                    st.warning("⚠️ Tab1: Contenido restringido por condiciones")
                    st.write("**Motivos:**")
                    if not condicion1:
                        st.write(f"- Hay {stats['pendientes_revision']} reportes pendientes de revisión")
                    if not condicion2:
                        st.write(f"- No hay reportes listos para envío ({stats['listos_envio']})")
            
            with tab2:
                st.info("✅ Tab2: Configuración - siempre disponible")
            
            with tab3:
                st.info("✅ Tab3: Historial - siempre disponible")
            
            with tab4:
                st.info("✅ Tab4: Logs - siempre disponible")
            
            with tab5:
                st.success("✅ Tab5: Emails Enviados - SIEMPRE DEBERÍA ESTAR DISPONIBLE")
                st.write("Esta pestaña debería funcionar independientemente de las condiciones")
                
                # Test de la función de emails enviados
                from database import obtener_emails_enviados
                try:
                    emails = obtener_emails_enviados(conn, limite=5)
                    if emails:
                        st.success(f"🎉 Funcionando! Se encontraron {len(emails)} emails enviados")
                        for email in emails[:2]:  # Mostrar solo los primeros 2
                            st.write(f"- {email['titular']}: {email['fecha_envio']} ({email['total_boletines']} boletines)")
                    else:
                        st.info("📭 No hay emails enviados registrados")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.error("❌ No se pudieron obtener las estadísticas")
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
        st.exception(e)
    
    finally:
        conn.close()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Test Email Section",
        page_icon="🧪",
        layout="wide"
    )
    
    test_email_section()
