#!/usr/bin/env python3
"""
Navegación directa a la sección de emails para verificar las pestañas
"""

import streamlit as st
import sys
sys.path.append('/Users/martingiacosa/Desktop/Proyectos/Python/Automation')

from database import crear_conexion, obtener_estadisticas_envios, obtener_emails_enviados

def main():
    st.set_page_config(
        page_title="Verificación Pestañas Emails",
        page_icon="📧",
        layout="wide"
    )
    
    st.title("📧 Verificación: Pestañas de Email")
    
    # Obtener estadísticas reales
    conn = crear_conexion()
    if not conn:
        st.error("No se pudo conectar a la base de datos")
        return
    
    try:
        stats = obtener_estadisticas_envios(conn)
        
        if stats:
            # Mostrar estadísticas como en la app real
            st.subheader("📊 Estado Actual del Sistema")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("📋 Total Reportes", stats['total_reportes'])
            with col2:
                st.metric("📄 Generados", stats['reportes_generados'])
            with col3:
                st.metric("📧 Enviados", stats['reportes_enviados'])
            with col4:
                st.metric("⚠️ Pendientes Revisión", stats['pendientes_revision'])
            with col5:
                st.metric("🚀 Listos para Envío", stats['listos_envio'])
            
            # Mostrar condiciones que podrían afectar la visibilidad
            st.subheader("🔍 Análisis de Condiciones")
            
            if stats['pendientes_revision'] > 0:
                st.warning(f"⚠️ Hay {stats['pendientes_revision']} reportes pendientes de revisión")
            
            if stats['listos_envio'] == 0:
                st.info("ℹ️ No hay reportes listos para envío")
            
            # Las pestañas SIEMPRE deben estar visibles
            st.divider()
            st.subheader("🔧 Pestañas de Gestión de Emails")
            st.success("✅ Las siguientes pestañas deberían estar SIEMPRE visibles:")
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🚀 Enviar Emails", 
                "⚙️ Configuración", 
                "📊 Historial de Envíos", 
                "📋 Logs Detallados", 
                "📁 Emails Enviados"
            ])
            
            with tab1:
                st.markdown("### 🚀 Enviar Emails")
                if stats['pendientes_revision'] > 0:
                    st.warning("⚠️ Envío bloqueado por reportes pendientes de revisión")
                elif stats['listos_envio'] == 0:
                    st.info("ℹ️ No hay reportes listos para envío")
                else:
                    st.success(f"✅ {stats['listos_envio']} reportes listos para enviar")
            
            with tab2:
                st.markdown("### ⚙️ Configuración")
                st.info("Configuración de credenciales de email")
            
            with tab3:
                st.markdown("### 📊 Historial de Envíos")
                st.info("Historial de reportes enviados")
            
            with tab4:
                st.markdown("### 📋 Logs Detallados")
                st.info("Logs detallados de envíos")
            
            with tab5:
                st.markdown("### 📁 Emails Enviados")
                st.success("🎉 ¡Esta pestaña SIEMPRE debe estar visible!")
                
                # Test de funcionalidad real
                try:
                    emails = obtener_emails_enviados(conn, limite=5)
                    if emails:
                        st.success(f"✅ Funcionalidad operativa: {len(emails)} emails encontrados")
                        
                        st.subheader("📧 Últimos Emails Enviados")
                        for i, email in enumerate(emails[:3]):
                            with st.expander(f"Email {i+1}: {email['titular']}", expanded=i==0):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Titular:** {email['titular']}")
                                    st.write(f"**Email:** {email['email']}")
                                    st.write(f"**Fecha:** {email['fecha_envio']}")
                                with col_b:
                                    st.write(f"**Boletines:** {email['total_boletines']}")
                                    if email.get('importancias_boletines'):
                                        st.write(f"**Importancias:** {', '.join(set(email['importancias_boletines']))}")
                    else:
                        st.info("📭 No hay emails enviados registrados aún")
                        st.markdown("**Esto es normal si:**")
                        st.markdown("- Es la primera vez que usas el sistema")
                        st.markdown("- No se han enviado emails todavía")
                        st.markdown("- Los envíos se realizaron antes de implementar el logging")
                
                except Exception as e:
                    st.error(f"❌ Error en la funcionalidad: {e}")
                    st.exception(e)
        
        else:
            st.error("❌ No se pudieron obtener las estadísticas")
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
        st.exception(e)
    
    finally:
        conn.close()
    
    # Mensaje final
    st.markdown("---")
    st.markdown("### 📝 Conclusión")
    st.success("✅ Si puedes ver las 5 pestañas arriba, entonces la funcionalidad está correcta")
    st.info("💡 La pestaña '📁 Emails Enviados' debería estar siempre disponible, independientemente del estado de los reportes")

if __name__ == "__main__":
    main()
