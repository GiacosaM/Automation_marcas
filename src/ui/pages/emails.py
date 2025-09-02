"""
Página de gestión de emails
"""
import streamlit as st
import sys
import os
import pandas as pd
import time
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, crear_tabla
from database_extensions import obtener_logs_envios, obtener_estadisticas_logs, limpiar_logs_antiguos, obtener_emails_enviados
from email_sender import procesar_envio_emails, generar_reporte_envios, obtener_info_reportes_pendientes, obtener_estadisticas_envios, validar_clientes_para_envio, validar_credenciales_email
from config import load_email_credentials, save_email_credentials, validate_email_format
from src.ui.components import UIComponents
from src.utils.session_manager import SessionManager


class EmailsPage:
    """Página de gestión de emails"""
    
    def __init__(self):
        self.email_types = {
            'marketing': {
                'name': '📧 Marketing',
                'description': 'Campañas promocionales y boletines',
                'color': '#667eea'
            },
            'operativo': {
                'name': '⚙️ Operativo',
                'description': 'Comunicaciones administrativas',
                'color': '#17a2b8'
            },
            'alerta': {
                'name': '🚨 Alertas',
                'description': 'Notificaciones críticas',
                'color': '#dc3545'
            },
            'informes': {
                'name': '📊 Informes',
                'description': 'Reportes automáticos',
                'color': '#28a745'
            },
            'notificacion': {
                'name': '🔔 Notificación',
                'description': 'Notificaciones sin reportes',
                'color': '#ffc107'
            }
        }
        
        self.importancia_types = {
            'Alta': {'color': '#dc3545', 'emoji': '🔴'},
            'Media': {'color': '#ffc107', 'emoji': '🟡'},
            'Baja': {'color': '#28a745', 'emoji': '🟢'},
            'Pendiente': {'color': '#6c757d', 'emoji': '⚪'},
            'Sin Reportes': {'color': '#17a2b8', 'emoji': '🔵'}
        }
        
        # Inicializar estado de confirmación de envío
        if 'confirmar_envio_emails' not in st.session_state:
            st.session_state.confirmar_envio_emails = False
    
    def _cargar_credenciales_email(self):
        """Carga las credenciales de email desde credenciales.json"""
        return load_email_credentials()
    
    def _guardar_credenciales_email(self, email, password):
        """Guarda las credenciales de email en credenciales.json"""
        return save_email_credentials(email, password)
    
    def _obtener_credenciales_email(self):
        """Obtiene las credenciales de email desde session_state o las carga desde archivo"""
        if 'email_credentials' not in st.session_state:
            st.session_state.email_credentials = self._cargar_credenciales_email()
        return st.session_state.email_credentials
    
    def _get_email_stats(self, conn):
        """Obtener estadísticas de emails"""
        cursor = conn.cursor()
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM emails_enviados")
        total_enviados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM emails_enviados WHERE status = 'enviado'")
        exitosos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM emails_enviados WHERE status = 'error'")
        con_error = cursor.fetchone()[0]
        
        # Emails por tipo en los últimos 30 días
        cursor.execute("""
            SELECT tipo_email, COUNT(*) 
            FROM emails_enviados 
            WHERE fecha_envio >= datetime('now', '-30 days')
            GROUP BY tipo_email
        """
        )
        por_tipo = cursor.fetchall()
        
        # Últimos emails enviados
        cursor.execute("""
            SELECT destinatario, asunto, fecha_envio, status, tipo_email
            FROM emails_enviados 
            ORDER BY fecha_envio DESC 
            LIMIT 10
        """
        )
        ultimos_emails = cursor.fetchall()
        
        # Estadísticas semanales
        cursor.execute("""
            SELECT DATE(fecha_envio) as dia, COUNT(*) as cantidad
            FROM emails_enviados 
            WHERE fecha_envio >= datetime('now', '-7 days')
            GROUP BY DATE(fecha_envio)
            ORDER BY dia DESC
        """
        )
        por_dia = cursor.fetchall()
        
        cursor.close()
        
        return {
            'total_enviados': total_enviados,
            'exitosos': exitosos,
            'con_error': con_error,
            'por_tipo': por_tipo,
            'ultimos_emails': ultimos_emails,
            'por_dia': por_dia
        }
    

    # def _show_email_types_breakdown(self, stats):
    #     """Mostrar desglose por tipos de email"""
    #     if stats['por_tipo']:
    #         with st.expander("📊 Emails por Tipo (Últimos 30 días)", expanded=True):
    #             cols = st.columns(len(stats['por_tipo']))
                
    #             for i, (tipo, cantidad) in enumerate(stats['por_tipo']):
    #                 with cols[i]:
    #                     tipo_info = self.email_types.get(tipo, {
    #                         'name': tipo.title(),
    #                         'description': 'Tipo personalizado',
    #                         'color': '#6c757d'
    #                     })
                        
    #                     st.markdown(UIComponents.create_metric_card(
    #                         cantidad,
    #                         tipo_info['name'],
    #                         tipo_info['color']
    #                     ), unsafe_allow_html=True)
                        
    #                     st.caption(tipo_info['description'])
    
    
    def _send_email(self, destinatario, asunto, mensaje, tipo_email, prioridad):
        """Enviar email"""
        with st.spinner("📤 Enviando email..."):
            try:
                # Aquí iría la lógica real de envío
                # resultado = enviar_email(destinatario, asunto, mensaje)
                
                # Simulación por ahora
                import time
                time.sleep(1.5)
                
                # Registrar en base de datos
                conn = crear_conexion()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO emails_enviados 
                        (destinatario, asunto, mensaje, tipo_email, status, fecha_envio)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (destinatario, asunto, mensaje, tipo_email, 'enviado', datetime.now()))
                    conn.commit()
                    conn.close()
                
                st.success("✅ Email enviado exitosamente")
                st.balloons()
                
                # Actualizar página
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al enviar email: {e}")
    
    
            
            selected_template = st.selectbox(
                "Seleccionar plantilla:",
                options=list(templates.keys()),
                format_func=lambda x: templates[x]['name']
            )
            
            if selected_template:
                template = templates[selected_template]
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text_area(
                        "Vista previa:",
                        value=f"Asunto: {template['subject']}\n\n{template['body']}",
                        height=150,
                        disabled=True
                    )
                
                with col2:
                    if st.button("📝 Usar Plantilla", use_container_width=True):
                        # Establecer valores en el formulario
                        SessionManager.set('template_subject', template['subject'])
                        SessionManager.set('template_body', template['body'])
                        st.success("✅ Plantilla cargada")
    
    # def _show_recent_emails(self, stats):
    #     """Mostrar emails recientes"""
    #     if stats['ultimos_emails']:
    #         with st.expander("📮 Emails Recientes", expanded=True):
    #             for email in stats['ultimos_emails']:
    #                 destinatario, asunto, fecha, status, tipo = email
                    
    #                 # Color según status
    #                 status_color = {
    #                     'enviado': '#28a745',
    #                     'error': '#dc3545',
    #                     'pendiente': '#ffc107'
    #                 }.get(status, '#6c757d')
                    
    #                 # Icono según tipo
    #                 tipo_info = self.email_types.get(tipo, {'name': tipo.title()})
                    
    #                 st.markdown(f"""
    #                 <div style="background: #f8f9fa; padding: 0.8rem; margin: 0.3rem 0; border-radius: 6px; border-left: 3px solid {status_color}; color: #000000;">
    #                     <div style="display: flex; justify-content: space-between; align-items: center;">
    #                         <div>
    #                             <strong>{asunto[:50]}{'...' if len(asunto) > 50 else ''}</strong><br>
    #                             <small style="color: #555555;">Para: {destinatario} | {tipo_info['name']}</small>
    #                         </div>
    #                         <div style="text-align: right;">
    #                             <span style="color: {status_color}; font-weight: bold;">{status.upper()}</span><br>
    #                             <small style="color: #555555;">{fecha}</small>
    #                         </div>
    #                     </div>
    #                 </div>
    #                 """, unsafe_allow_html=True)
    
    def _show_email_analytics(self, stats):
        """Mostrar analíticas de emails"""
        # Removed as requested
        pass
    
    def _show_email_management_system(self, conn, stats):
        """Mostrar sistema completo de gestión de emails"""
        # Verificar si hay reportes con importancia pendiente
        if stats['pendientes_revision'] > 0:
            st.warning(f"⚠️ Hay {stats['pendientes_revision']} reportes con importancia 'Pendiente' que requieren revisión antes del envío.")
            
            # Mostrar información detallada de los pendientes
            with st.expander("🔍 Ver Reportes Pendientes de Revisión", expanded=False):
                try:
                    info_pendientes = obtener_info_reportes_pendientes(conn)
                    if info_pendientes:
                        for detalle in info_pendientes['detalles']:
                            st.markdown(f"""
                            **{detalle['titular']}**: {detalle['cantidad']} reportes
                            - Boletines: {', '.join(detalle['boletines'][:3])}{'...' if len(detalle['boletines']) > 3 else ''}
                            """)
                        st.info("💡 Ve a la sección 'Historial' para asignar importancia a estos reportes.")
                    else:
                        st.error("Error al obtener información de reportes pendientes")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.divider()
        
        # Sistema de pestañas
        tab1, tab2 = st.tabs([
            "🚀 Enviar Emails", "📊 Historial de Envíos"
        ])
        
        with tab1:
            self._show_envio_masivo_tab(conn, stats)
        
        with tab2:
            self._show_historial_envios_tab(conn)
    
    def _show_envio_masivo_tab(self, conn, stats):
        """Mostrar tab de envío masivo de reportes"""
        if stats['pendientes_revision'] == 0 and stats['listos_envio'] > 0:
            st.markdown("### 📧 Envío Masivo de Reportes")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"📬 Hay **{stats['listos_envio']}** reportes listos para enviar")
                
                # Previsualización de lo que se va a enviar
                with st.expander("👀 Previsualizar Envíos", expanded=False):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT b.titular, c.email, COUNT(*) as cantidad_reportes,
                                   GROUP_CONCAT(DISTINCT b.importancia) as importancias
                            FROM boletines b
                            LEFT JOIN clientes c ON b.titular = c.titular
                            WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0 
                            AND b.importancia IN ('Baja', 'Media', 'Alta')
                            GROUP BY b.titular, c.email
                            ORDER BY b.titular
                        """)
                        preview_data = cursor.fetchall()
                        cursor.close()
                        
                        if preview_data:
                            preview_df = pd.DataFrame(preview_data, 
                                columns=['Titular', 'Email', 'Cantidad Reportes', 'Importancias'])
                            
                            # Marcar clientes sin email
                            preview_df['Estado'] = preview_df['Email'].apply(
                                lambda x: "✅ Listo" if x and x.strip() else "❌ Sin Email"
                            )
                            
                            st.dataframe(preview_df, use_container_width=True)
                            
                            # Estadísticas del preview
                            con_email = len(preview_df[preview_df['Email'].notna() & (preview_df['Email'] != '')])
                            sin_email = len(preview_df) - con_email
                            
                            if sin_email > 0:
                                st.warning(f"⚠️ {sin_email} clientes no tienen email registrado y no recibirán reportes")
                        else:
                            st.info("No hay datos para previsualizar")
                    except Exception as e:
                        st.error(f"Error en previsualización: {e}")
            
            with col2:
                self._show_credentials_panel()
        else:
            st.success("✅ No hay reportes pendientes de envío")
            st.info("🎉 Todos los reportes generados han sido enviados exitosamente")
    
    def _show_credentials_panel(self):
        """Mostrar panel de credenciales y botón de envío"""
        #st.markdown("##### 📧 Credenciales de Email")
        
        # Obtener credenciales actuales
        credenciales = self._obtener_credenciales_email()
        
        # # Mostrar credenciales cargadas (email visible, password oculta)
        # if credenciales['email']:
        #     st.success(f"✅ Email configurado: {credenciales['email']}")
        #     st.info("🔑 Contraseña cargada desde archivo")
            
        #     # Mostrar estado de validación
        #     if validate_email_format(credenciales['email']):
        #         st.success("📧 Formato de email válido")
        #     else:
        #         st.error("❌ Formato de email inválido")
                
        #     # Enlace a configuración
        #     st.markdown("---")
        #     if st.button("⚙️ Cambiar Credenciales", use_container_width=True):
        #         st.info("💡 Ve a la pestaña 'Configuración' para cambiar las credenciales")
        
        # else:
        #     st.warning("⚠️ No hay credenciales configuradas")
        #     st.info("💡 Ve a la pestaña 'Configuración' para configurar las credenciales")
        
        #st.markdown("---")
        
        # Botón principal de envío - solo si hay credenciales
        if credenciales['email'] and credenciales['password']:
            self._show_send_confirmation_system(credenciales)
        else:
            st.warning("⚠️ Configura las credenciales de email para continuar")
    
    def _show_send_confirmation_system(self, credenciales):
        """Sistema de confirmación para envío de emails"""
        conn = crear_conexion()
        if not conn:
            st.error("❌ Error de conexión a la base de datos")
            return
        
        try:
            # Botón de confirmación si está en estado de confirmación
            if st.session_state.get('confirmar_envio_emails', False):
                self._show_final_confirmation(conn, credenciales)
            else:
                self._show_initial_send_button(conn)
        finally:
            conn.close()
    
    def _show_initial_send_button(self, conn):
        """Mostrar botón inicial para comenzar el proceso de envío"""
        # Validación previa antes de mostrar el botón
        validacion = validar_clientes_para_envio(conn)
        
        # Mostrar información de validación
        if validacion['sin_email'] or validacion['sin_reporte']:
            st.markdown("#### ⚠️ Avisos de Validación")
            
            if validacion['sin_email']:
                with st.expander(f"📧 {len(validacion['sin_email'])} Grupos sin Email", expanded=True):
                    st.warning("Los siguientes grupos no tienen email registrado y no recibirán reportes:")
                    for grupo in validacion['sin_email']:
                        st.write(f"• {grupo}")
                    st.info("💡 Puedes agregar emails en la sección 'Clientes'")
            
            if validacion['sin_reporte']:
                with st.expander(f"📄 {len(validacion['sin_reporte'])} Grupos sin Reporte", expanded=True):
                    st.warning("Los siguientes grupos no tienen archivo de reporte:")
                    for grupo in validacion['sin_reporte']:
                        st.write(f"• {grupo}")
                    st.info("💡 Genera los reportes en la sección 'Informes'")
        
        # Mostrar resumen de la validación
        if validacion['listos_para_envio'] > 0:
            st.success(f"✅ {validacion['listos_para_envio']} grupos listos para recibir emails")
            # st.info("📨 Cada grupo representa una combinación de titular + importancia, enviándose emails separados por importancia")
            
            # Botón inicial para comenzar el proceso
            if st.button("🚀 Enviar Todos los Emails", 
                        type="primary", 
                        use_container_width=True,
                        disabled=not validacion['puede_continuar']):
                
                # Activar confirmación solo si la validación es exitosa
                if validacion['puede_continuar']:
                    st.session_state.confirmar_envio_emails = True
                    st.rerun()
                else:
                    st.error("❌ No se puede continuar debido a los problemas de validación")
        else:
            st.error("❌ No hay grupos listos para recibir emails")
            st.info("Revisa que los clientes tengan email registrado y reportes generados")
            
            # Botón deshabilitado para mostrar el estado
            st.button("🚀 Enviar Todos los Emails", 
                    type="primary", 
                    use_container_width=True,
                    disabled=True)
    
    def _show_final_confirmation(self, conn, credenciales):
        """Mostrar confirmación final antes del envío"""
        # Realizar validación final antes de confirmar
        validacion_final = validar_clientes_para_envio(conn)
        
        st.warning("⚠️ ¿Estás seguro de enviar todos los emails?")
        
        # Mostrar información detallada de lo que se enviará
        if validacion_final['listos_para_envio'] > 0:
            st.success(f"📧 Se enviarán reportes a {validacion_final['listos_para_envio']} clientes")
            
            # Mostrar advertencias si las hay
            if validacion_final['sin_email']:
                st.warning(f"⚠️ {len(validacion_final['sin_email'])} clientes serán omitidos por no tener email")
            
            if validacion_final['sin_reporte']:
                st.warning(f"⚠️ {len(validacion_final['sin_reporte'])} clientes serán omitidos por no tener reportes")
        else:
            st.error("❌ No hay clientes listos para recibir emails")
            st.session_state.confirmar_envio_emails = False
            st.rerun()
        
        col_conf1, col_conf2 = st.columns(2)
        with col_conf1:
            if st.button("✅ Sí, Enviar", type="primary", use_container_width=True):
                self._process_email_sending(conn, credenciales)
        
        with col_conf2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.confirmar_envio_emails = False
                st.rerun()
        
        # Mostrar resultados de envío si están disponibles
        self._show_sending_results()
    
    def _process_email_sending(self, conn, credenciales):
        """Procesar el envío real de emails"""
        # EJECUTAR EL ENVÍO AQUÍ
        with st.spinner("📤 Enviando emails..."):
            try:
                st.info("🔄 Procesando envíos...")
                resultados = procesar_envio_emails(
                    conn, 
                    credenciales['email'], 
                    credenciales['password']
                )
                
                # Resetear confirmación
                st.session_state.confirmar_envio_emails = False
                
                # Guardar resultados en session_state para mostrarlos
                st.session_state.resultados_envio = resultados
                
                # Mostrar resultados básicos
                if resultados.get('bloqueado_por_pendientes', False):
                    st.error("❌ Envío bloqueado por reportes pendientes")
                    info_pendientes = resultados.get('info_pendientes')
                    if info_pendientes:
                        st.markdown(f"**{info_pendientes['total_reportes']}** reportes requieren revisión de **{info_pendientes['total_titulares']}** titulares")
                else:
                    st.success("🎉 Proceso de envío completado!")
                    # Forzar actualización para mostrar resultados
                    st.rerun()
                        
            except Exception as e:
                st.session_state.confirmar_envio_emails = False
                st.error(f"❌ Error durante el envío: {str(e)}")
                
                # Mostrar detalles del error si es por reportes pendientes
                if "Pendiente" in str(e):
                    st.info("💡 Ve a la sección 'Historial' para cambiar la importancia de los reportes pendientes.")
    
    def _show_sending_results(self):
        """Mostrar resultados detallados del envío"""
        if 'resultados_envio' in st.session_state and st.session_state.resultados_envio:
            resultados = st.session_state.resultados_envio
            st.session_state.resultados_envio = None  # Limpiar después de mostrar
            
            st.success("🎉 Proceso de envío completado!")
            
            # Métricas de resultados
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("✅ Exitosos", len(resultados['exitosos']))
            with col_r2:
                st.metric("❌ Fallidos", len(resultados['fallidos']))
            with col_r3:
                st.metric("📧 Sin Email", len(resultados['sin_email']))
            with col_r4:
                st.metric("📄 Sin Archivo", len(resultados['sin_archivo']))
            
            # Detalles de envíos exitosos
            if len(resultados['exitosos']) > 0:
                st.success(f"🎉 ¡{len(resultados['exitosos'])} emails enviados exitosamente!")
                with st.expander(f"📧 Ver detalles de envíos exitosos ({len(resultados['exitosos'])})", expanded=False):
                    for envio in resultados['exitosos']:
                        titular = envio.get('titular', 'N/A')
                        importancia = envio.get('importancia', 'N/A')
                        email = envio.get('email', 'N/A')
                        cantidad = envio.get('cantidad_boletines', 0)
                        st.write(f"✅ **{titular}** ({importancia}) → {email} ({cantidad} boletines)")
            
            # Detalles de fallos
            if len(resultados['fallidos']) > 0:
                st.error(f"❌ {len(resultados['fallidos'])} envíos fallaron")
                with st.expander(f"Ver detalles de fallos ({len(resultados['fallidos'])})", expanded=True):
                    for fallo in resultados['fallidos']:
                        titular = fallo.get('titular', 'N/A')
                        importancia = fallo.get('importancia', 'N/A')
                        email = fallo.get('email', 'N/A')
                        error = fallo.get('error', 'N/A')
                        st.write(f"❌ **{titular}** ({importancia}) → {email}")
                        st.write(f"   Error: {error}")
            
            # Grupos sin email
            if len(resultados['sin_email']) > 0:
                st.warning(f"📧 {len(resultados['sin_email'])} grupos no recibieron emails por falta de dirección de email")
                with st.expander(f"Ver grupos sin email ({len(resultados['sin_email'])})", expanded=False):
                    for grupo in resultados['sin_email']:
                        st.write(f"• {grupo}")
                    st.info("💡 Puedes agregar emails en la sección 'Clientes'")
            
            # Grupos sin archivo
            if len(resultados['sin_archivo']) > 0:
                st.warning(f"📄 {len(resultados['sin_archivo'])} grupos no recibieron emails por falta de archivo de reporte")
                with st.expander(f"Ver grupos sin reporte ({len(resultados['sin_archivo'])})", expanded=False):
                    for grupo in resultados['sin_archivo']:
                        st.write(f"• {grupo}")
                    st.info("💡 Genera los reportes en la sección 'Informes'")
            
            # Mostrar reporte detallado
            with st.expander("📋 Reporte Detallado", expanded=len(resultados['exitosos']) == 0):
                reporte = generar_reporte_envios(resultados)
                st.text(reporte)
            
            # Auto-actualizar estadísticas
            st.success("🔄 Actualizando estadísticas...")
            time.sleep(2)
            st.rerun()
    
    def _show_configuracion_tab(self):
        """Mostrar tab de configuración de email"""
        st.markdown("### ⚙️ Configuración de Email")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📧 Configuración SMTP")
            st.info("🔧 **Servidor**: smtp.gmail.com:587")
            st.info("🔐 **Seguridad**: TLS habilitado")
            
            st.markdown("##### 💡 Consejos")
            st.markdown("""
            - Usa una **contraseña de aplicación** para Gmail
            - Habilita la **verificación en 2 pasos**
            - Verifica que los clientes tengan **emails válidos**
            """)
        
        with col2:
            st.markdown("##### 🔑 Gestión de Credenciales")
            
            # Obtener credenciales actuales
            credenciales_actuales = self._obtener_credenciales_email()
            
            # Formulario para cambiar credenciales
            with st.form("form_credenciales_email"):
                st.markdown("**Credenciales de Email**")
                
                nuevo_email = st.text_input(
                    "📧 Email", 
                    value=credenciales_actuales.get('email', ''),
                    placeholder="tu_email@gmail.com"
                )
                
                nueva_password = st.text_input(
                    "🔑 Contraseña de Aplicación", 
                    type="password",
                    placeholder="Contraseña de aplicación de Gmail",
                    help="Genera una contraseña de aplicación en tu cuenta de Google"
                )
                
                col_form1, col_form2 = st.columns(2)
                with col_form1:
                    if st.form_submit_button("💾 Guardar Credenciales", type="primary", use_container_width=True):
                        if nuevo_email and nueva_password:
                            if validate_email_format(nuevo_email):
                                # Validar credenciales antes de guardar
                                with st.spinner("Validando credenciales..."):
                                    try:
                                        if validar_credenciales_email(nuevo_email, nueva_password):
                                            # Guardar en archivo y session_state
                                            if self._guardar_credenciales_email(nuevo_email, nueva_password):
                                                st.session_state.email_credentials = {
                                                    'email': nuevo_email,
                                                    'password': nueva_password
                                                }
                                                st.success("✅ Credenciales guardadas exitosamente")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("❌ Error al guardar credenciales")
                                        else:
                                            st.error("❌ Credenciales inválidas. Verifica email y contraseña")
                                    except Exception as e:
                                        st.error(f"❌ Error al validar credenciales: {e}")
                            else:
                                st.error("❌ Formato de email inválido")
                        else:
                            st.error("⚠️ Complete todos los campos")
                
                with col_form2:
                    if st.form_submit_button("🧪 Solo Validar", use_container_width=True):
                        if nuevo_email and nueva_password:
                            if validate_email_format(nuevo_email):
                                with st.spinner("Validando..."):
                                    try:
                                        if validar_credenciales_email(nuevo_email, nueva_password):
                                            st.success("✅ Credenciales válidas")
                                        else:
                                            st.error("❌ Credenciales inválidas")
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")
                            else:
                                st.error("❌ Formato de email inválido")
                        else:
                            st.error("⚠️ Complete todos los campos")
            
            # Mostrar estado actual
            st.markdown("---")
            st.markdown("**Estado Actual:**")
            if credenciales_actuales['email']:
                st.success(f"📧 Email: {credenciales_actuales['email']}")
                st.success("🔑 Contraseña: Configurada")
            else:
                st.warning("⚠️ No hay credenciales configuradas")
    
    def _show_historial_envios_tab(self, conn):
        """Mostrar tab de historial de envíos"""
        st.markdown("### 📊 Historial de Envíos")
        
        # Consultar historial de envíos
        try:
            # Primero intentar obtener datos de la función específica
            historial_df = None
            try:
                # Intentar usar la función dedicada si existe
                from database_extensions import obtener_emails_enviados
                emails_enviados = obtener_emails_enviados(conn, limite=200)
                if emails_enviados and len(emails_enviados) > 0:
                    # Convertir a DataFrame si la función devuelve resultados
                    columnas = ['ID', 'Destinatario', 'Asunto', 'Fecha Envío', 'Estado', 'Error', 'Titular', 'Tipo']
                    historial_df = pd.DataFrame(emails_enviados, columns=columnas)
                    st.success(f"✅ Cargados {len(emails_enviados)} registros de envíos desde la extensión de base de datos")
            except Exception as e:
                st.warning(f"Usando consulta de respaldo: {str(e)}")
            
            # Si la función específica falló, usar la consulta directa
            if historial_df is None:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT b.titular, b.numero_boletin, b.fecha_envio_reporte, 
                           b.importancia, c.email, 'informes' as tipo_envio
                    FROM boletines b
                    LEFT JOIN clientes c ON b.titular = c.titular
                    WHERE b.reporte_enviado = 1 
                    
                    UNION ALL
                    
                    -- Incluir notificaciones de clientes sin reportes
                    SELECT e.titular, 
                           'Sin reportes', e.fecha_envio, 
                           'Sin Reportes' as importancia, e.destinatario as email, 'notificacion' as tipo_envio
                    FROM emails_enviados e
                    WHERE e.tipo_email = 'notificacion' AND e.status = 'enviado'
                    
                    ORDER BY fecha_envio_reporte DESC
                    LIMIT 150
                """)
                historial_envios = cursor.fetchall()
                cursor.close()
                
                if historial_envios:
                    historial_df = pd.DataFrame(historial_envios, 
                        columns=['Titular', 'Boletín', 'Fecha Envío', 'Importancia', 'Email', 'Tipo'])
            
            if historial_df is not None and not historial_df.empty:
                # Formatear fecha permitiendo formatos mixtos
                if 'Fecha Envío' in historial_df.columns:
                    historial_df['Fecha Envío'] = pd.to_datetime(
                        historial_df['Fecha Envío'], errors='coerce'
                    ).dt.strftime('%d/%m/%Y %H:%M')
                
                # Crear filtros para el historial
                col_filter1, col_filter2 = st.columns([2, 2])
                with col_filter1:
                    # Si existe columna Titular, permitir filtrado
                    if 'Titular' in historial_df.columns:
                        titular_filter = st.text_input("🔍 Filtrar por Titular:", key="titular_filter")
                        if titular_filter:
                            historial_df = historial_df[historial_df['Titular'].str.contains(titular_filter, case=False, na=False)]
                
                with col_filter2:
                    # Si existe columna Importancia, permitir filtrado
                    if 'Importancia' in historial_df.columns and 'Importancia' in historial_df:
                        importancias = ['Todas'] + sorted(historial_df['Importancia'].dropna().unique().tolist())
                        imp_filter = st.selectbox("🏷️ Filtrar por Importancia:", importancias, key="imp_filter")
                        if imp_filter != 'Todas':
                            historial_df = historial_df[historial_df['Importancia'] == imp_filter]
                
                # Mostrar el grid con los datos de historial usando el GridService
                from src.services.grid_service import GridService
                grid_result = GridService.create_grid(
                    historial_df, 
                    key='grid_historial_envios',
                    height=400,
                    selection_mode='single',
                    fit_columns=True
                )

                # Estadísticas del historial
                st.markdown("#### 📈 Estadísticas del Historial")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_enviados = len(historial_df)
                    st.metric("📧 Total Enviados", total_enviados)
                with col2:
                    hoy = datetime.now().date()
                    if 'Fecha Envío' in historial_df.columns:
                        try:
                            enviados_hoy = len(historial_df[pd.to_datetime(
                                historial_df['Fecha Envío'], errors='coerce'
                            ).dt.date == hoy])
                            st.metric("📅 Enviados Hoy", enviados_hoy)
                        except:
                            st.metric("📅 Enviados Hoy", "N/A")
                    else:
                        st.metric("📅 Enviados Hoy", "N/A")
                with col3:
                    if 'Importancia' in historial_df.columns:
                        try:
                            importancia_alta = len(historial_df[historial_df['Importancia'] == 'Alta'])
                            st.metric("🔴 Importancia Alta", importancia_alta)
                        except:
                            st.metric("🔴 Importancia Alta", "N/A")
                    else:
                        st.metric("🔴 Importancia Alta", "N/A")
                with col4:
                    if 'Importancia' in historial_df.columns:
                        try:
                            sin_reportes = len(historial_df[historial_df['Importancia'] == 'Sin Reportes'])
                            st.metric("🔵 Sin Reportes", sin_reportes)
                        except:
                            st.metric("🔵 Sin Reportes", "N/A")
                    else:
                        st.metric("🔵 Sin Reportes", "N/A")
                
                # Añadir exportación CSV
                st.markdown("---")
                if st.button("📊 Exportar Historial", use_container_width=True):
                    # Preparar CSV para descarga
                    csv = historial_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Descargar CSV",
                        data=csv,
                        file_name=f"historial_envios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("📭 No hay envíos registrados")
        
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")
    
    def _show_logs_detallados_tab(self, conn):
        """Mostrar tab de logs detallados - REMOVED as requested"""
        pass
    
    def _show_emails_enviados_tab(self, conn):
        """Mostrar tab de emails enviados - REMOVED as requested"""
        pass
    
    def _get_email_sending_stats(self, conn):
        """Obtener estadísticas específicas para el sistema de envío"""
        try:
            stats = obtener_estadisticas_envios(conn)
            return stats if stats else {
                'total_reportes': 0,
                'reportes_generados': 0,
                'reportes_enviados': 0,
                'pendientes_revision': 0,
                'listos_envio': 0
            }
        except Exception:
            return {
                'total_reportes': 0,
                'reportes_generados': 0,
                'reportes_enviados': 0,
                'pendientes_revision': 0,
                'listos_envio': 0
            }
    
    def show(self):
        """Mostrar la página de emails"""
        UIComponents.create_section_header(
            "📧 Gestión de Envío de Emails",
            "Sistema completo de envío masivo de reportes",
            "blue-70"
        )
        
        # Obtener estadísticas de envío de reportes
        conn = crear_conexion()
        if conn:
            try:
                crear_tabla(conn)
                
                # Obtener estadísticas específicas del sistema de envío
                stats = self._get_email_sending_stats(conn)
                
                if stats:
                    # Dashboard de estadísticas de reportes
                    st.subheader("📊 Estado de Envíos de Reportes")
                    
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
                    
                    # Mostrar sistema completo de gestión de emails
                    self._show_email_management_system(conn, stats)
                
                # Crear tabla de emails si no existe (para compatibilidad)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emails_enviados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        destinatario TEXT NOT NULL,
                        asunto TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        tipo_email TEXT DEFAULT 'general',
                        status TEXT DEFAULT 'pendiente',
                        fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                        titular TEXT DEFAULT NULL
                    )
                """)
                conn.commit()
                
                # Verificamos si la columna titular ya existe en la tabla emails_enviados
                cursor.execute("PRAGMA table_info(emails_enviados)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'titular' not in columns:
                    try:
                        cursor.execute("ALTER TABLE emails_enviados ADD COLUMN titular TEXT DEFAULT NULL")
                        conn.commit()
                    except Exception as e:
                        st.warning(f"No se pudo añadir la columna titular: {e}")
                
                cursor.close()
                
                # Mostrar estadísticas adicionales del sistema de emails simple
                stats_simple = self._get_email_stats(conn)
                
                # Mostrar desglose por tipos
                # self._show_email_types_breakdown(stats_simple)
                
                # Emails recientes
                # self._show_recent_emails(stats_simple)
                
            except Exception as e:
                st.error(f"Error: {e}")
                
            finally:
                conn.close()
        else:
            st.error("No se pudo conectar a la base de datos")


def show_emails_page():
    """Función de compatibilidad para mostrar la página de emails"""
    emails_page = EmailsPage()
    emails_page.show()
