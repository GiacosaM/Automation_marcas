"""
Página de gestión de emails - Versión limpia y optimizada
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
from db_utils import convertir_query_boolean, usar_supabase_simple
from email_sender import (procesar_envio_emails, obtener_estadisticas_envios, 
                         validar_clientes_para_envio, validar_credenciales_email,
                         obtener_info_reportes_pendientes, generar_reporte_envios)
from config import load_email_credentials, save_email_credentials, validate_email_format
from src.ui.components import UIComponents


class EmailsPage:
    """Página de gestión de emails - versión optimizada"""
    
    def __init__(self):
        # Inicializar estado de confirmación
        if 'confirmar_envio_emails' not in st.session_state:
            st.session_state.confirmar_envio_emails = False

    def _create_connection(self):
        """Crear nueva conexión a la base de datos"""
        conn = crear_conexion()
        if conn:
            # Crear tablas necesarias
            crear_tabla(conn)
            self._create_emails_table(conn)
        return conn

    def _create_emails_table(self, conn):
        """Crear tabla de emails con sintaxis correcta según el motor"""
        cursor = conn.cursor()
        try:
            if usar_supabase_simple():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emails_enviados (
                        id SERIAL PRIMARY KEY,
                        destinatario TEXT NOT NULL,
                        asunto TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        tipo_email TEXT DEFAULT 'general',
                        status TEXT DEFAULT 'pendiente',
                        fecha_envio TIMESTAMPTZ DEFAULT NOW(),
                        titular TEXT DEFAULT NULL
                    )
                """)
            else:
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
        except Exception as e:
            st.error(f"Error creando tabla emails: {e}")
        finally:
            cursor.close()

    def _get_email_stats(self):
        """Obtener estadísticas de envío"""
        conn = self._create_connection()
        if not conn:
            return None
        
        try:
            stats = obtener_estadisticas_envios(conn)
            return stats if stats else {
                'total_reportes': 0,
                'reportes_generados': 0,
                'reportes_enviados': 0,
                'pendientes_revision': 0,
                'listos_envio': 0
            }
        except Exception as e:
            st.error(f"Error obteniendo estadísticas: {e}")
            return None
        finally:
            conn.close()

    def _show_stats_dashboard(self, stats):
        """Mostrar dashboard de estadísticas"""
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

    def _show_pending_reports_warning(self, stats):
        """Mostrar advertencia de reportes pendientes"""
        if stats['pendientes_revision'] > 0:
            st.warning(f"⚠️ Hay {stats['pendientes_revision']} reportes con importancia 'Pendiente' que requieren revisión antes del envío.")
            
            with st.expander("🔍 Ver Reportes Pendientes de Revisión", expanded=False):
                conn = self._create_connection()
                if conn:
                    try:
                        info_pendientes = obtener_info_reportes_pendientes(conn)
                        if info_pendientes:
                            for detalle in info_pendientes['detalles']:
                                st.markdown(f"""
                                **{detalle['titular']}**: {detalle['cantidad']} reportes
                                - Boletines: {', '.join(detalle['boletines'][:3])}{'...' if len(detalle['boletines']) > 3 else ''}
                                """)
                            st.info("💡 Ve a la sección 'Historial' para asignar importancia a estos reportes.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()

    def _show_send_tab(self, stats):
        """Tab de envío de emails"""
        if stats['pendientes_revision'] == 0 and stats['listos_envio'] > 0:
            st.markdown("### 📧 Envío Masivo de Reportes")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"📬 Hay **{stats['listos_envio']}** reportes listos para enviar")
                self._show_preview()
            
            with col2:
                self._show_send_controls()
        else:
            st.success("✅ No hay reportes pendientes de envío")
            st.info("🎉 Todos los reportes generados han sido enviados exitosamente")

    def _show_preview(self):
        """Mostrar previsualización de envíos"""
        with st.expander("👀 Previsualizar Envíos", expanded=False):
            conn = self._create_connection()
            if not conn:
                st.error("Error de conexión")
                return
            
            try:
                cursor = conn.cursor()
                if usar_supabase_simple():
                    cursor.execute("""
                        SELECT b.titular, c.email, COUNT(*) AS cantidad_reportes,
                               STRING_AGG(DISTINCT b.importancia, ', ') AS importancias
                        FROM boletines b
                        LEFT JOIN clientes c ON b.titular = c.titular
                        WHERE b.reporte_generado = TRUE AND b.reporte_enviado = FALSE
                          AND b.importancia IN ('Baja', 'Media', 'Alta')
                        GROUP BY b.titular, c.email
                        ORDER BY b.titular
                    """)
                else:
                    query = convertir_query_boolean("""
                        SELECT b.titular, c.email, COUNT(*) AS cantidad_reportes,
                               GROUP_CONCAT(DISTINCT b.importancia) AS importancias
                        FROM boletines b
                        LEFT JOIN clientes c ON b.titular = c.titular
                        WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0
                          AND b.importancia IN ('Baja', 'Media', 'Alta')
                        GROUP BY b.titular, c.email
                        ORDER BY b.titular
                    """)
                    cursor.execute(query)
                
                preview_data = cursor.fetchall()
                
                if preview_data:
                    df = pd.DataFrame(preview_data, columns=['Titular', 'Email', 'Cantidad Reportes', 'Importancias'])
                    df['Estado'] = df['Email'].apply(lambda x: "✅ Listo" if x and x.strip() else "❌ Sin Email")
                    st.dataframe(df, use_container_width=True)
                    
                    sin_email = len(df[df['Email'].isna() | (df['Email'] == '')])
                    if sin_email > 0:
                        st.warning(f"⚠️ {sin_email} clientes no tienen email registrado")
                else:
                    st.info("No hay datos para previsualizar")
                    
            except Exception as e:
                st.error(f"Error en previsualización: {e}")
            finally:
                cursor.close()
                conn.close()

    def _show_send_controls(self):
        """Controles de envío"""
        credenciales = load_email_credentials()
        
        if credenciales['email'] and credenciales['password']:
            if st.session_state.get('confirmar_envio_emails', False):
                self._show_confirmation()
            else:
                self._show_send_button()
        else:
            st.warning("⚠️ Configura las credenciales de email en la pestaña 'Configuración'")

    def _show_send_button(self):
        """Botón inicial de envío"""
        conn = self._create_connection()
        if not conn:
            st.error("Error de conexión")
            return
        
        try:
            validacion = validar_clientes_para_envio(conn)
            
            if validacion['sin_email']:
                with st.expander(f"📧 {len(validacion['sin_email'])} Grupos sin Email"):
                    for grupo in validacion['sin_email']:
                        st.write(f"• {grupo}")
            
            if validacion['sin_reporte']:
                with st.expander(f"📄 {len(validacion['sin_reporte'])} Grupos sin Reporte"):
                    for grupo in validacion['sin_reporte']:
                        st.write(f"• {grupo}")
            
            if validacion['listos_para_envio'] > 0:
                st.success(f"✅ {validacion['listos_para_envio']} grupos listos para envío")
                
                if st.button("🚀 Enviar Todos los Emails", 
                            type="primary", 
                            use_container_width=True,
                            disabled=not validacion['puede_continuar']):
                    
                    if validacion['puede_continuar']:
                        st.session_state.confirmar_envio_emails = True
                        st.rerun()
                    else:
                        st.error("❌ No se puede continuar debido a problemas de validación")
            else:
                st.error("❌ No hay grupos listos para envío")
                st.button("🚀 Enviar Todos los Emails", disabled=True, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error en validación: {e}")
        finally:
            conn.close()

    def _show_confirmation(self):
        """Confirmación final de envío"""
        st.warning("⚠️ ¿Estás seguro de enviar todos los emails?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, Enviar", type="primary", use_container_width=True):
                self._process_sending()
        
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.confirmar_envio_emails = False
                st.rerun()

    def _process_sending(self):
        """Procesar envío de emails"""
        credenciales = load_email_credentials()
        conn = self._create_connection()
        
        if not conn:
            st.error("Error de conexión")
            return
        
        try:
            with st.spinner("📤 Enviando emails..."):
                resultados = procesar_envio_emails(
                    conn, 
                    credenciales['email'], 
                    credenciales['password']
                )
                
                st.session_state.confirmar_envio_emails = False
                
                if resultados.get('bloqueado_por_pendientes', False):
                    st.error("❌ Envío bloqueado por reportes pendientes")
                else:
                    st.success("🎉 Proceso completado!")
                    self._show_results(resultados)
                    
        except Exception as e:
            st.error(f"❌ Error durante el envío: {str(e)}")
            st.session_state.confirmar_envio_emails = False
        finally:
            conn.close()

    def _show_results(self, resultados):
        """Mostrar resultados del envío"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Exitosos", len(resultados['exitosos']))
        with col2:
            st.metric("❌ Fallidos", len(resultados['fallidos']))
        with col3:
            st.metric("📧 Sin Email", len(resultados['sin_email']))
        with col4:
            st.metric("📄 Sin Archivo", len(resultados['sin_archivo']))
        
        if resultados['exitosos']:
            with st.expander(f"📧 Envíos exitosos ({len(resultados['exitosos'])})"):
                for envio in resultados['exitosos']:
                    st.write(f"✅ {envio['titular']} ({envio['importancia']}) → {envio['email']}")
        
        if resultados['fallidos']:
            with st.expander(f"❌ Envíos fallidos ({len(resultados['fallidos'])})"):
                for fallo in resultados['fallidos']:
                    st.write(f"❌ {fallo['titular']} → {fallo['error']}")

    def _show_history_tab(self):
        """Tab de historial"""
        st.markdown("### 📊 Historial de Envíos")
        
        conn = self._create_connection()
        if not conn:
            st.error("Error de conexión")
            return
        
        try:
            cursor = conn.cursor()
            query = convertir_query_boolean("""
                SELECT b.titular, b.numero_boletin, b.fecha_envio_reporte, 
                       b.importancia, c.email
                FROM boletines b
                LEFT JOIN clientes c ON b.titular = c.titular
                WHERE b.reporte_enviado = 1 
                ORDER BY b.fecha_envio_reporte DESC
                LIMIT 100
            """)
            cursor.execute(query)
            historial = cursor.fetchall()
            
            if historial:
                df = pd.DataFrame(historial, columns=['Titular', 'Boletín', 'Fecha Envío', 'Importancia', 'Email'])
                st.dataframe(df, use_container_width=True)
                
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📧 Total Enviados", len(df))
                with col2:
                    hoy = datetime.now().date()
                    enviados_hoy = len(df[pd.to_datetime(df['Fecha Envío']).dt.date == hoy])
                    st.metric("📅 Enviados Hoy", enviados_hoy)
                with col3:
                    alta = len(df[df['Importancia'] == 'Alta'])
                    st.metric("🔴 Importancia Alta", alta)
            else:
                st.info("📭 No hay envíos registrados")
                
        except Exception as e:
            st.error(f"Error cargando historial: {e}")
        finally:
            cursor.close()
            conn.close()

    def _show_config_tab(self):
        """Tab de configuración"""
        st.markdown("### ⚙️ Configuración de Email")
        
        credenciales = load_email_credentials()
        
        with st.form("credenciales_form"):
            email = st.text_input("📧 Email", value=credenciales.get('email', ''))
            password = st.text_input("🔑 Contraseña de Aplicación", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar", type="primary", use_container_width=True):
                    if email and password and validate_email_format(email):
                        if validar_credenciales_email(email, password):
                            if save_email_credentials(email, password):
                                st.success("✅ Credenciales guardadas")
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar")
                        else:
                            st.error("❌ Credenciales inválidas")
                    else:
                        st.error("⚠️ Complete todos los campos correctamente")
            
            with col2:
                if st.form_submit_button("🧪 Validar", use_container_width=True):
                    if email and password:
                        if validar_credenciales_email(email, password):
                            st.success("✅ Credenciales válidas")
                        else:
                            st.error("❌ Credenciales inválidas")

    def show(self):
        """Mostrar página principal"""
        UIComponents.create_section_header(
            "📧 Gestión de Envío de Emails",
            "Sistema completo de envío masivo de reportes",
            "blue-70"
        )
        
        # Obtener estadísticas
        stats = self._get_email_stats()
        if not stats:
            st.error("No se pudo conectar a la base de datos")
            return
        
        # Dashboard de estadísticas
        self._show_stats_dashboard(stats)
        
        # Advertencia de reportes pendientes
        self._show_pending_reports_warning(stats)
        
        st.divider()
        
        # Pestañas principales
        tab1, tab2, tab3 = st.tabs([
            "🚀 Enviar Emails", 
            "📊 Historial de Envíos",
            "⚙️ Configuración"
        ])
        
        with tab1:
            self._show_send_tab(stats)
        
        with tab2:
            self._show_history_tab()
        
        with tab3:
            self._show_config_tab()


def show_emails_page():
    """Función de compatibilidad"""
    emails_page = EmailsPage()
    emails_page.show()
