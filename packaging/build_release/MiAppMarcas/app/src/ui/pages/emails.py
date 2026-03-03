"""
Página de gestión de emails
"""
import streamlit as st
import sys
import os
import pandas as pd
import time
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, crear_tabla
from database_extensions import obtener_logs_envios, obtener_estadisticas_logs, limpiar_logs_antiguos, obtener_emails_enviados
from email_sender import (
    procesar_envio_emails, generar_reporte_envios, obtener_info_reportes_pendientes,
    obtener_estadisticas_envios, validar_clientes_para_envio, validar_credenciales_email,
    obtener_registros_pendientes_envio, obtener_mensajes_predefinidos,
)
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
        # Siempre recargar las credenciales para asegurar que estén actualizadas
        credentials = self._cargar_credenciales_email()
        
        # Actualizar session_state
        st.session_state.email_credentials = credentials
        
        # Verificar que las credenciales sean válidas
        if not credentials.get('email') or not credentials.get('password'):
            logging.warning("Credenciales de email no válidas o incompletas")
            return {'email': '', 'password': ''}
            
        return credentials
    
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
                            SELECT b.titular,
                                   COALESCE(c.email, c2.email) AS email,
                                   COUNT(*) as cantidad_reportes,
                                   GROUP_CONCAT(DISTINCT b.importancia) as importancias
                            FROM boletines b
                            LEFT JOIN clientes c
                                   ON normalizar_titular(b.titular) = normalizar_titular(c.titular)
                            LEFT JOIN Marcas m
                                   ON c.id IS NULL
                                  AND normalizar_titular(b.titular) = normalizar_titular(m.titular)
                                  AND m.cliente_id IS NOT NULL
                            LEFT JOIN clientes c2
                                   ON c.id IS NULL
                                  AND m.cliente_id = c2.id
                            WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0
                            AND b.importancia IN ('Baja', 'Media', 'Alta')
                            GROUP BY b.titular, COALESCE(c.email, c2.email)
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
            #st.info("🎉 Todos los reportes generados han sido enviados exitosamente")
    
    def _show_credentials_panel(self):
        """Mostrar panel de credenciales y botón de envío"""
        st.markdown("##### 📧 Credenciales de Email")
        
        # Obtener credenciales actuales (esto forzará una recarga desde keyring)
        credenciales = self._obtener_credenciales_email()
        
        # Verificar si hay credenciales configuradas
        if credenciales.get('email') and credenciales.get('password'):
            st.success(f"✅ Email configurado: {credenciales['email']}")
            #st.info("🔑 Contraseña cargada de forma segura")
            
            # Mostrar estado de validación
           

            # Enlace a configuración
            #if st.button("⚙️ Cambiar Credenciales", use_container_width=True):
                #st.session_state.main_tab = "Configuración"
               # st.session_state.config_tab = "Email"
                #st.rerun()
            
            st.markdown("---")
            
            # Mostrar sistema de confirmación de envío
            self._show_send_confirmation_system(credenciales)
        else:
            st.warning("⚠️ No hay credenciales configuradas")
            st.info("💡 Ve a la pestaña 'Configuración > Email' para configurar las credenciales")
            
            #if st.button("⚙️ Ir a Configuración de Email", use_container_width=True):
                #st.session_state.main_tab = "Configuración"
                #st.session_state.config_tab = "Email"
                #st.rerun()
    
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
        
        # Mostrar información de validación y motivos detallados
        if validacion['sin_email'] or validacion['sin_reporte'] or validacion.get('sin_marcas'):
            st.markdown("#### ⚠️ Avisos de Validación")
            
            if validacion['sin_email']:
                with st.expander(f"📧 {len(validacion['sin_email'])} Grupos sin Email", expanded=True):
                    st.warning("Los siguientes grupos no tienen un email disponible y no recibirán reportes:")
                    for grupo in validacion['sin_email']:
                        st.write(f"• {grupo}")
                    st.info("💡 Revisa la sección 'Clientes' para crear o completar los datos de contacto.")
            
            if validacion['sin_reporte']:
                with st.expander(f"📄 {len(validacion['sin_reporte'])} Grupos sin Reporte", expanded=True):
                    st.warning("Los siguientes grupos no tienen archivo de reporte PDF generado:")
                    for grupo in validacion['sin_reporte']:
                        st.write(f"• {grupo}")
                    st.info("💡 Genera los reportes en la sección 'Informes'.")
            
            # Información adicional: clientes sin marcas vinculadas (no bloquea el envío)
            if validacion.get('sin_marcas'):
                with st.expander(f"🏷️ {len(validacion['sin_marcas'])} Grupos sin marcas vinculadas", expanded=False):
                    st.warning(
                        "Estos grupos pertenecen a clientes que no tienen marcas vinculadas por CUIT. "
                        "El envío de emails no se bloquea por este motivo, pero puede indicar una carga incompleta."
                    )
                    for grupo in validacion['sin_marcas']:
                        st.write(f"• {grupo}")
                    st.info("💡 Verifica la vinculación Cliente ↔ Marca en las secciones 'Clientes' y 'Marcas'.")
            
            # Mostrar mensajes detallados de validación para mayor claridad
            if validacion.get('mensajes'):
                with st.expander("📝 Detalle de validación", expanded=False):
                    for msg in validacion['mensajes']:
                        st.write(msg)
        
        # Mostrar resumen de la validación
        if validacion['listos_para_envio'] > 0:
            st.success(f"✅ {validacion['listos_para_envio']} grupos listos para recibir emails")
        else:
            st.info("Revisa que los clientes tengan email registrado y reportes generados")

        # Botón único: habilitado/deshabilitado según validación
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
    
    def _show_final_confirmation(self, conn, credenciales):
        """Mostrar confirmación final antes del envío"""
        # Realizar validación final antes de confirmar (sin cambio de lógica)
        validacion_final = validar_clientes_para_envio(conn)

        # Guardia original intacta: sin grupos listos → abortar
        if validacion_final['listos_para_envio'] == 0:
            st.error("❌ No hay clientes listos para recibir emails")
            st.session_state.confirmar_envio_emails = False
            st.rerun()

        # ── [UX] Tabla resumen ────────────────────────────────────────────────
        # Calcular asunto usando la misma lógica que email_sender.py (sin DB)
        now = datetime.now()
        _meses_es = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        _mes_anterior = (
            f"{_meses_es[now.month - 2].capitalize()} {now.year}"
            if now.month > 1 else f"Diciembre {now.year - 1}"
        )

        # Obtener grupos (misma query que ya ejecutó validar_clientes_para_envio)
        try:
            _grupos = obtener_registros_pendientes_envio(conn)
        except Exception:
            _grupos = {}

        if _grupos:
            _filas = []
            for _datos in _grupos.values():
                _imp = _datos['importancia']
                _asunto = (
                    f"Custodia de Marcas con deteccion de similares - {_mes_anterior}"
                    if _imp.lower() == 'baja'
                    else f"Custodia de Marcas con deteccion de similitudes relevantes - {_mes_anterior}"
                )
                _filas.append({
                    'Titular':    _datos['titular'],
                    'Email':      _datos.get('email') or '—',
                    'Importancia': _imp,
                    'Asunto':     _asunto,
                })

            _df = pd.DataFrame(_filas)
            _df_listos = _df[_df['Email'] != '—'].reset_index(drop=True)

            st.markdown("#### 📋 Resumen de envíos a confirmar")
            st.dataframe(_df_listos, use_container_width=True, hide_index=True)

            if validacion_final['sin_email']:
                st.caption(
                    f"ℹ️ {len(validacion_final['sin_email'])} grupo(s) omitidos por falta de email."
                )
            if validacion_final['sin_reporte']:
                st.caption(
                    f"ℹ️ {len(validacion_final['sin_reporte'])} grupo(s) omitidos por falta de reporte PDF."
                )

            # ── [UX] Vista previa del asunto ─────────────────────────────────
            if not _df_listos.empty:
                st.markdown("---")
                st.markdown("##### 📨 Asunto del email")
                for _asunto_u in _df_listos['Asunto'].unique():
                    _imps = ', '.join(_df_listos[_df_listos['Asunto'] == _asunto_u]['Importancia'].unique())
                    st.info(f"**{_asunto_u}** *(Importancia: {_imps})*")

                # ── [UX] Vista previa del cuerpo ─────────────────────────────
                _mensajes = obtener_mensajes_predefinidos()
                _imps_presentes = _df_listos['Importancia'].unique().tolist()
                with st.expander("👁 Vista previa del contenido del email", expanded=False):
                    for _i, _imp in enumerate(_imps_presentes):
                        _texto = _mensajes.get(_imp, _mensajes['default']).strip()
                        st.markdown(f"**Nivel {_imp}:**")
                        st.text(_texto)
                        if _i < len(_imps_presentes) - 1:
                            st.divider()
        # ── [/UX] ─────────────────────────────────────────────────────────────

        # ── [UX] Confirmación final profesional ───────────────────────────────
        st.markdown("---")
        _n = validacion_final['listos_para_envio']
        st.warning(
            f"⚠️ Se enviarán **{_n} email{'s' if _n != 1 else ''}** a clientes reales.  \n"
            f"Esta acción **no se puede deshacer**."
        )

        col_conf1, col_conf2 = st.columns(2)
        with col_conf1:
            if st.button("📤 Confirmar Envío Definitivo", type="primary", use_container_width=True):
                self._process_email_sending(conn, credenciales)

        with col_conf2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.confirmar_envio_emails = False
                st.rerun()
        # ── [/UX] ─────────────────────────────────────────────────────────────

        # Mostrar resultados de envío si están disponibles (sin cambio)
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
                           b.importancia, COALESCE(c.email, c2.email) AS email, 'informes' as tipo_envio
                    FROM boletines b
                    LEFT JOIN clientes c
                           ON normalizar_titular(b.titular) = normalizar_titular(c.titular)
                    LEFT JOIN Marcas m
                           ON c.id IS NULL
                          AND normalizar_titular(b.titular) = normalizar_titular(m.titular)
                          AND m.cliente_id IS NOT NULL
                    LEFT JOIN clientes c2
                           ON c.id IS NULL
                          AND m.cliente_id = c2.id
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
            # Intentar obtener stats con reintentos
            max_retries = 2
            for attempt in range(max_retries):
                stats = obtener_estadisticas_envios(conn)
                if stats and stats.get('total_reportes', 0) > 0:
                    return stats
                # Si falló el primer intento, esperar un poco
                if attempt < max_retries - 1:
                    time.sleep(0.1)
            
            # Si llegamos aquí, retornar lo que obtuvimos o valores por defecto
            return stats if stats else {
                'total_reportes': 0,
                'reportes_generados': 0,
                'reportes_enviados': 0,
                'pendientes_revision': 0,
                'listos_envio': 0
            }
        except Exception as e:
            logging.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total_reportes': 0,
                'reportes_generados': 0,
                'reportes_enviados': 0,
                'pendientes_revision': 0,
                'listos_envio': 0
            }
    
    def show(self):
        """Mostrar la página de emails"""
        logging.info("=== EMAILS PAGE: Iniciando show() ===")
        # Inicializar flag de primera carga si no existe
        if 'emails_page_loaded' not in st.session_state:
            st.session_state.emails_page_loaded = False
            logging.info("Primera carga de página emails detectada")
        
        UIComponents.create_section_header(
            "📧 Gestión de Envío de Emails",
            "Sistema completo de envío masivo de reportes",
            "blue-70"
        )
        
        logging.info("Intentando crear conexión DB...")
        # Obtener estadísticas de envío de reportes
        conn = crear_conexion()
        if conn:
            logging.info("Conexión DB creada exitosamente")
            try:
                logging.info("Llamando a crear_tabla()...")
                crear_tabla(conn)
                logging.info("crear_tabla() completada")
                
                # Obtener estadísticas específicas del sistema de envío
                logging.info("Obteniendo estadísticas de envío...")
                stats = self._get_email_sending_stats(conn)
                logging.info(f"Estadísticas obtenidas: {stats}")
                
                # Si es la primera carga y no hay stats válidas, forzar recarga
                if not st.session_state.emails_page_loaded and stats:
                    logging.info(f"Verificando si necesita rerun... total_reportes={stats.get('total_reportes', 0)}")
                    if stats.get('total_reportes', 0) == 0:
                        # Marcar como cargado y hacer rerun
                        st.session_state.emails_page_loaded = True
                        conn.close()
                        logging.info("Forzando rerun por stats vacías")
                        st.rerun()
                    else:
                        st.session_state.emails_page_loaded = True
                        logging.info("Primera carga marcada como completada")
                
                if stats:
                    # Dashboard de estadísticas de reportes
                    col_header1, col_header2 = st.columns([4, 1])
                    with col_header1:
                        st.subheader("📊 Estado de Envíos de Reportes")
                    with col_header2:
                        if st.button("🔄 Actualizar", key="refresh_stats", help="Actualizar estadísticas"):
                            st.rerun()
                    
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
