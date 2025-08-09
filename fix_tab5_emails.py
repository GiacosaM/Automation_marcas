#!/usr/bin/env python3
"""
Corrección para la sección de emails - tab5 (Emails Enviados) siempre visible
"""

def crear_contenido_emails_tab5(conn):
    """Función que genera el contenido de la pestaña tab5 - Emails Enviados"""
    import streamlit as st
    import pandas as pd
    import os
    from datetime import datetime
    from database import obtener_emails_enviados, obtener_ruta_reporte_pdf
    
    st.markdown("### 📁 Historial de Emails Enviados")
    st.info("💡 Esta sección muestra todos los emails enviados exitosamente con acceso directo a los reportes PDF")
    
    # Obtener emails enviados
    try:
        # Filtros para la nueva pestaña
        st.markdown("#### 🔍 Filtros de Búsqueda")
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            filtro_titular_emails = st.text_input(
                "🏢 Titular",
                placeholder="Buscar por titular...",
                key="filtro_titular_emails"
            )
        
        with col_filter2:
            # Filtro por rango de fechas
            col_fecha1, col_fecha2 = st.columns(2)
            with col_fecha1:
                fecha_desde = st.date_input(
                    "📅 Desde",
                    value=None,
                    help="Fecha de inicio"
                )
            with col_fecha2:
                fecha_hasta = st.date_input(
                    "📅 Hasta", 
                    value=None,
                    help="Fecha de fin"
                )
        
        with col_filter3:
            limite_emails = st.selectbox(
                "📄 Mostrar últimos",
                [25, 50, 100, 200],
                index=1,
                key="limite_emails"
            )
        
        with col_filter4:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        # Preparar filtros
        filtro_fechas = None
        if fecha_desde and fecha_hasta:
            filtro_fechas = (fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
        elif fecha_desde:
            filtro_fechas = (fecha_desde.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))
        
        titular_filtro = filtro_titular_emails if filtro_titular_emails else None
        
        # Obtener datos
        emails_enviados = obtener_emails_enviados(
            conn, 
            filtro_fechas=filtro_fechas,
            filtro_titular=titular_filtro,
            limite=limite_emails
        )
        
        if emails_enviados:
            # Estadísticas rápidas
            st.markdown("---")
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            
            total_emails = len(emails_enviados)
            total_boletines = sum(email['total_boletines'] for email in emails_enviados)
            titulares_unicos = len(set(email['titular'] for email in emails_enviados))
            
            with col_stats1:
                st.metric("📧 Emails Enviados", total_emails)
            with col_stats2:
                st.metric("📄 Total Boletines", total_boletines)
            with col_stats3:
                st.metric("👥 Titulares", titulares_unicos)
            with col_stats4:
                promedio = total_boletines / total_emails if total_emails > 0 else 0
                st.metric("📊 Promedio/Email", f"{promedio:.1f}")
            
            # Mostrar tabla de emails enviados
            st.markdown("---")
            st.markdown(f"#### 📋 Últimos {len(emails_enviados)} Emails Enviados")
            
            for email in emails_enviados:
                with st.expander(
                    f"📧 {email['titular']} - {email['fecha_envio']} ({email['total_boletines']} boletines)",
                    expanded=False
                ):
                    # Información del email
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.markdown(f"**📧 Destinatario:** {email['email']}")
                        st.markdown(f"**📅 Fecha de Envío:** {email['fecha_envio']}")
                        st.markdown(f"**📄 Total Boletines:** {email['total_boletines']}")
                        
                        if email['importancias_boletines']:
                            importancias = list(set(email['importancias_boletines']))
                            st.markdown(f"**⚡ Importancias:** {', '.join(importancias)}")
                    
                    with col_info2:
                        if email['fecha_primer_boletin'] and email['fecha_ultimo_boletin']:
                            st.markdown(f"**📅 Rango de Boletines:**")
                            st.markdown(f"- Desde: {email['fecha_primer_boletin']}")
                            st.markdown(f"- Hasta: {email['fecha_ultimo_boletin']}")
                        
                        # Buscar archivo PDF
                        ruta_pdf = obtener_ruta_reporte_pdf(email['titular'], email['fecha_envio'])
                        
                        if ruta_pdf and os.path.exists(ruta_pdf):
                            st.markdown(f"**📄 Archivo:** {os.path.basename(ruta_pdf)}")
                            
                            # Botón para descargar PDF
                            try:
                                with open(ruta_pdf, "rb") as pdf_file:
                                    pdf_data = pdf_file.read()
                                    
                                st.download_button(
                                    label="📥 Descargar PDF",
                                    data=pdf_data,
                                    file_name=os.path.basename(ruta_pdf),
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key=f"download_pdf_{email['id']}"
                                )
                            except Exception as e:
                                st.error(f"Error al cargar PDF: {e}")
                        else:
                            st.warning("📄 Archivo PDF no encontrado")
                    
                    # Mostrar números de boletines si hay muchos
                    if email['numeros_boletines'] and len(email['numeros_boletines']) > 0:
                        with st.expander(f"📋 Ver Boletines Incluidos ({len(email['numeros_boletines'])})", expanded=False):
                            # Organizar en columnas
                            boletines = email['numeros_boletines']
                            cols_per_row = 4
                            
                            for i in range(0, len(boletines), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, boletin in enumerate(boletines[i:i+cols_per_row]):
                                    with cols[j]:
                                        st.markdown(f"• {boletin}")
            
            # Paginación o información adicional
            if len(emails_enviados) == limite_emails:
                st.info(f"📄 Mostrando los últimos {limite_emails} emails. Ajusta el filtro 'Mostrar últimos' para ver más.")
        
        else:
            st.info("📭 No se encontraron emails enviados con los filtros aplicados")
            st.markdown("💡 **Sugerencias:**")
            st.markdown("- Verifica que se hayan enviado emails exitosamente")
            st.markdown("- Ajusta los filtros de fecha")
            st.markdown("- Revisa la sección 'Logs Detallados' para más información")
    
    except Exception as e:
        st.error(f"❌ Error al cargar emails enviados: {e}")
        st.markdown("🔧 **Posibles soluciones:**")
        st.markdown("- Verifica la conexión a la base de datos")
        st.markdown("- Revisa que la tabla 'envios_log' esté correctamente configurada")
        st.markdown("- Consulta los logs del sistema para más detalles")


if __name__ == "__main__":
    # Demo de la función
    import streamlit as st
    from database import crear_conexion
    
    st.set_page_config(
        page_title="Demo Tab5 - Emails Enviados",
        page_icon="📁",
        layout="wide"
    )
    
    st.title("📁 Demo: Pestaña Emails Enviados")
    
    conn = crear_conexion()
    if conn:
        try:
            crear_contenido_emails_tab5(conn)
        finally:
            conn.close()
    else:
        st.error("No se pudo conectar a la base de datos")
