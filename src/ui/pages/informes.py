"""
Página de generación de informes
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, crear_tabla
from report_generator import generar_informe_pdf
from src.ui.components import UIComponents
from src.utils.session_manager import SessionManager


class InformesPage:
    """Página de generación de informes"""
    
    def __init__(self):
        self.conn = None
    
    def _get_reports_status(self, conn):
        """Obtener estado de reportes"""
        cursor = conn.cursor()
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 0")
        reportes_pendientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 0 AND importancia = 'Pendiente'")
        pendientes_importancia = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
        reportes_generados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total_boletines = cursor.fetchone()[0]
        
        # Reportes por importancia
        cursor.execute("""
            SELECT importancia, COUNT(*) 
            FROM boletines 
            WHERE reporte_generado = 0 
            GROUP BY importancia
        """)
        por_importancia = cursor.fetchall()
        
        # Últimos reportes generados
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_alta
            FROM boletines 
            WHERE reporte_generado = 1
            ORDER BY fecha_alta DESC
            LIMIT 10
        """)
        ultimos_generados = cursor.fetchall()
        
        cursor.close()
        
        return {
            'reportes_pendientes': reportes_pendientes,
            'pendientes_importancia': pendientes_importancia,
            'reportes_generados': reportes_generados,
            'total_boletines': total_boletines,
            'por_importancia': por_importancia,
            'ultimos_generados': ultimos_generados
        }
    
    def _show_status_metrics(self, status):
        """Mostrar métricas de estado"""
        procesables = status['reportes_pendientes'] - status['pendientes_importancia']
        
        metrics = [
            {
                'value': status['total_boletines'],
                'label': '📄 Total Boletines',
                'color': '#667eea'
            },
            {
                'value': status['reportes_generados'],
                'label': '✅ Reportes Generados',
                'color': '#28a745'
            },
            {
                'value': status['reportes_pendientes'],
                'label': '⏳ Pendientes de Generar',
                'color': '#ffc107' if status['reportes_pendientes'] > 0 else '#28a745'
            },
            {
                'value': procesables,
                'label': '🚀 Listos para Procesar',
                'color': '#17a2b8' if procesables > 0 else '#6c757d'
            },
            {
                'value': status['pendientes_importancia'],
                'label': '⚠️ En Estado Pendiente',
                'color': '#dc3545' if status['pendientes_importancia'] > 0 else '#28a745'
            }
        ]
        
        UIComponents.create_metric_grid(metrics, columns=5)
    
    def _show_importance_breakdown(self, status):
        """Mostrar desglose por importancia con texto visible para titular en cards rojas"""
        if status['por_importancia']:
            with st.expander("� Desglose por Importancia", expanded=True):
                cols = st.columns(len(status['por_importancia']))
                for i, (importancia, cantidad) in enumerate(status['por_importancia']):
                    with cols[i]:
                        color_map = {
                            'Alta': '#dc3545',
                            'Media': '#ffc107', 
                            'Baja': '#28a745',
                            'Pendiente': '#6c757d'
                        }
                        color = color_map.get(importancia, '#667eea')
                        # Si es importancia Alta, mostrar texto destacado
                        if importancia == 'Alta':
                            st.markdown(f"""
                            <div style='background:{color};padding:1rem;border-radius:8px;text-align:center;'>
                                <span style='font-size:2rem;font-weight:bold;color:#fff;'>{cantidad}</span><br>
                                <span style='font-size:1rem;color:#fff;font-weight:bold;'>IMPORTANCIA ALTA</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background:{color};padding:1rem;border-radius:8px;text-align:center;'>
                                <span style='font-size:2rem;font-weight:bold;color:#222222;'>{cantidad}</span><br>
                                <span style='font-size:1rem;color:#222222;'>{importancia}</span>
                            </div>
                            """, unsafe_allow_html=True)
    
    def _show_generation_options(self, status):
        """Mostrar opciones de generación"""
        procesables = status['reportes_pendientes'] - status['pendientes_importancia']
        
        if status['reportes_pendientes'] > 0:
            # Mensajes informativos
            if status['pendientes_importancia'] > 0 and status['pendientes_importancia'] == status['reportes_pendientes']:
                st.warning(f"⚠️ {status['reportes_pendientes']} registros están marcados como 'Pendiente'. Cambia la importancia para poder generar informes.")
                st.info("💡 **Sugerencia**: Ve a la sección 'Historial' para cambiar la importancia de los registros.")
                return
            elif status['pendientes_importancia'] > 0:
                st.info(f"💡 {status['pendientes_importancia']} registros marcados como 'Pendiente' no se procesarán. Se generarán {procesables} informes.")
            
            # Opciones de generación
            st.markdown("### 🚀 Opciones de Generación")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(
                    f"📄 Generar Todos los Informes ({procesables})",
                    type="primary",
                    use_container_width=True,
                    disabled=procesables == 0
                ):
                    self._generate_all_reports()
            
            
        else:
            st.success("✅ Todos los informes están actualizados")
    
    def _generate_all_reports(self):
        """Generar todos los reportes pendientes usando report_generator y mostrar links de descarga"""
        import os
        with st.spinner("🔄 Generando informes..."):
            try:
                conn = crear_conexion()
                if conn:
                    resultado = generar_informe_pdf(conn)
                    download_links = []
                    # Si la función retorna nombres/rutas de archivos, mostrar links
                    if resultado['success']:
                        if resultado['message'] == 'no_pending':
                            st.success("✅ No hay informes pendientes de generación")
                        elif resultado['message'] == 'completed':
                            if resultado['reportes_generados'] > 0:
                                st.success(f"✅ Se generaron {resultado['reportes_generados']} informes correctamente")
                                if resultado.get('pendientes', 0) > 0:
                                    st.info(f"ℹ️ {resultado['pendientes']} registros permanecen como 'Pendiente' y no fueron procesados")
                                if resultado.get('errores', 0) > 0:
                                    st.warning(f"⚠️ {resultado['errores']} informes tuvieron errores durante la generación")
                                # Mostrar links de descarga si existen
                                # Buscar los archivos generados en la carpeta de informes
                                informes_dir = "informes"
                                if os.path.exists(informes_dir):
                                    archivos = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
                                    if archivos:
                                        st.markdown("### 📥 Descargar Informes Generados")
                                        for archivo in archivos:
                                            ruta = os.path.join(informes_dir, archivo)
                                            with open(ruta, "rb") as f:
                                                st.download_button(
                                                    label=f"Descargar {archivo}",
                                                    data=f.read(),
                                                    file_name=archivo,
                                                    mime="application/pdf"
                                                )
                            else:
                                st.warning("⚠️ No se pudo generar ningún informe")
                    else:
                        if resultado['message'] == 'pending_only':
                            st.warning(f"⚠️ No se generaron informes. Los {resultado['pendientes']} registros están marcados como 'Pendiente'")
                            st.info("💡 Cambia la importancia de los registros en la sección 'Historial' para poder procesarlos")
                        elif resultado['message'] == 'error':
                            st.error(f"❌ Error al generar informes: {resultado.get('error', 'Error desconocido')}")
                        else:
                            st.error("❌ No se pudieron generar los informes")
                    # Botón para ir al historial
                    if st.button("📋 Ver Reportes Generados"):
                        SessionManager.set_current_page('historial')
                        SessionManager.set('show_db_section', True)
                        st.rerun()
                else:
                    st.error("❌ No se pudo conectar a la base de datos")
            except Exception as e:
                st.error(f"❌ Error durante la generación: {e}")
    
    
    
    
    
    def _show_recent_reports(self, status):
        """Mostrar reportes generados recientemente con botón de descarga y nombre del titular"""
        if status['ultimos_generados']:
            with st.expander("📋 Últimos Reportes Generados", expanded=False):
                st.markdown("### Reportes generados recientemente:")
                informes_dir = "informes"
                archivos_disponibles = []
                if os.path.exists(informes_dir):
                    archivos_disponibles = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
                for reporte in status['ultimos_generados']:
                    numero, titular, fecha = reporte
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 0.8rem; margin: 0.3rem 0; border-radius: 6px; border-left: 3px solid #28a745; color: #222222;">
                        <strong style='color:#222222;'>Boletín {numero}</strong> - <span style='color:#222222;'>{titular[:40]}...</span><br>
                        <small style="color: #555555;">Generado: {fecha}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    # Buscar archivo PDF correspondiente (por titular y boletín)
                    archivo_pdf = None
                    for f in archivos_disponibles:
                        if str(numero) in f and titular[:10].replace(' ', '') in f.replace(' ', ''):
                            archivo_pdf = f
                            break
                    if archivo_pdf:
                        ruta = os.path.join(informes_dir, archivo_pdf)
                        with open(ruta, "rb") as f:
                            st.download_button(
                                label=f"Descargar informe de {titular}",
                                data=f.read(),
                                file_name=archivo_pdf,
                                mime="application/pdf",
                                key=f"download_{archivo_pdf}_{numero}_{titular}"
                            )
                    # Si no se encuentra el PDF exacto, no mostrar ningún botón extra
    
    def show(self):
        """Mostrar la página de informes"""
        UIComponents.create_section_header(
            "📄 Generación de Informes",
            "Crear y gestionar reportes PDF de boletines",
            "green-70"
        )
        
        # Obtener estado de reportes
        conn = crear_conexion()
        if conn:
            try:
                crear_tabla(conn)
                status = self._get_reports_status(conn)
                
                # Mostrar métricas de estado
                self._show_status_metrics(status)
                
                # Mostrar desglose por importancia
                self._show_importance_breakdown(status)
                
                # Mostrar opciones de generación
                self._show_generation_options(status)
                
               

                # (Eliminado) Mostrar reportes recientes
                # Mostrar cuadrícula de últimos informes generados
                self._show_boletines_grid()
                
                # Añadir sección de verificación de reportes
                self._show_verificacion_reportes_section()
                
            except Exception as e:
                st.error(f"Error: {e}")

    def _show_boletines_grid(self):
        """Mostrar los últimos 10 informes generados en tarjetas con pandas y Streamlit"""
        import pandas as pd
        import sqlite3
        import streamlit as st
        from paths import get_db_path
        db_path = get_db_path()
        query = '''
            SELECT id, titular, nombre_reporte, ruta_reporte
            FROM boletines
            WHERE reporte_generado = 1 AND ruta_reporte IS NOT NULL AND nombre_reporte IS NOT NULL
            ORDER BY id DESC
            LIMIT 10
        '''
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
        except Exception as e:
            st.error(f"Error al leer los informes: {e}")
            return

        if df.empty:
            st.info("No hay informes generados recientemente.")
            return

        st.markdown("<h3 style='margin-top:2rem;'>🗂️ Últimos informes generados</h3>", unsafe_allow_html=True)
        # Mostrar en cuadrícula (2 o 3 por fila)
        num_cols = 3 if len(df) >= 6 else 2
        cols = st.columns(num_cols)
        for idx, row in df.iterrows():
            col = cols[idx % num_cols]
            with col:
                st.container()
                st.markdown(f"""
                <div style='background:#f4f6fa;padding:1.2rem;margin-bottom:1rem;border-radius:12px;box-shadow:0 2px 8px #0001;'>
                    <span style='font-size:1.3rem;font-weight:bold;color:#222;'>{row['titular']}</span><br>
                    <span style='font-size:1rem;color:#555;'>{row['nombre_reporte']}</span><br>
                </div>
                """, unsafe_allow_html=True)
                try:
                    with open(row['ruta_reporte'], "rb") as f:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=f.read(),
                            file_name=row['nombre_reporte'],
                            mime="application/pdf",
                            key=f"download_{row['id']}"
                        )
                except Exception as e:
                    st.caption(f"No se pudo acceder al PDF: {e}")
    
    def _show_verificacion_reportes_section(self):
        """Muestra la sección para verificar titulares sin reportes"""
        with st.expander("🔍 Verificación de Titulares sin Reportes", expanded=False):
            st.markdown("""
            ### 🔔 Verificación de Titulares sin Reportes
            
            Esta herramienta verifica qué titulares no tienen reportes generados durante el mes actual 
            y les envía un correo electrónico de notificación.
            """)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Mostrar resultado de verificación automática si existe
                from src.utils.session_manager import SessionManager
                resultado_verificacion = SessionManager.get('resultado_verificacion_reportes', None)
                
                if resultado_verificacion:
                    estado = resultado_verificacion.get('estado', '')
                    
                    if estado == 'completado':
                        st.success("✅ Verificación automática realizada")
                        
                        metrics = [
                            {"value": resultado_verificacion.get('titulares_con_marcas_sin_reportes', 0), 
                             "label": "Titulares con marcas sin reportes", 
                             "color": "#ffc107"},
                            {"value": resultado_verificacion.get('emails_enviados', 0), 
                             "label": "Emails enviados", 
                             "color": "#28a745"},
                            {"value": resultado_verificacion.get('errores', 0), 
                             "label": "Errores", 
                             "color": "#dc3545"},
                        ]
                        
                        for metric in metrics:
                            st.markdown(f"""
                            <div style='background:{metric["color"]};padding:1rem;border-radius:8px;text-align:center;margin-bottom:10px;'>
                                <span style='font-size:1.5rem;font-weight:bold;color:#fff;'>{metric["value"]}</span><br>
                                <span style='font-size:0.9rem;color:#fff;'>{metric["label"]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.caption(f"Última verificación: {resultado_verificacion.get('fecha_verificacion', 'N/A')}")
                    else:
                        st.error(f"❌ Error en la última verificación: {resultado_verificacion.get('mensaje', 'Error desconocido')}")
            
            with col2:
                st.markdown("### Verificación Manual")
                st.info("Puedes ejecutar la verificación manualmente en cualquier momento.")
                
                if st.button("🚨 Verificar Titulares sin Reportes", use_container_width=True):
                    with st.spinner("Verificando titulares sin reportes..."):
                        try:
                            from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes
                            from database import crear_conexion
                            
                            conn = crear_conexion()
                            if conn:
                                resultado = verificar_titulares_sin_reportes(conn)
                                conn.close()
                                
                                # Guardar resultado en la sesión
                                SessionManager.set('resultado_verificacion_reportes', resultado)
                                
                                if resultado['estado'] == 'completado':
                                    st.success("✅ Verificación completada con éxito")
                                    st.info(f"Se encontraron {resultado['titulares_con_marcas_sin_reportes']} titulares con marcas sin reportes")
                                    st.success(f"Se enviaron {resultado['emails_enviados']} correos de notificación")
                                    
                                    if resultado['errores'] > 0:
                                        st.warning(f"Hubo {resultado['errores']} errores durante el envío")
                                else:
                                    st.error(f"❌ Error: {resultado['mensaje']}")
                                
                                # Forzar recarga para mostrar los resultados actualizados
                                st.rerun()
                            else:
                                st.error("❌ No se pudo conectar a la base de datos")
                        except Exception as e:
                            st.error(f"❌ Error durante la verificación: {e}")

def show_informes_page():
    """Función de compatibilidad para mostrar la página de informes"""
    informes_page = InformesPage()
    informes_page.show()
