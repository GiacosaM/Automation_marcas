"""
Página de generación de informes
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta

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
    
    def _get_pending_detail(self, conn):
        """Devuelve un DataFrame con los grupos de registros pendientes (procesables).

        Columnas: titular, importancia, cantidad, fecha_min, fecha_max.
        Excluye registros con importancia = 'Pendiente' (sin clasificar).
        """
        import pandas as pd
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT titular, importancia,
                       COUNT(*)          AS cantidad,
                       MIN(fecha_boletin) AS fecha_min,
                       MAX(fecha_boletin) AS fecha_max
                FROM boletines
                WHERE reporte_generado = 0
                  AND importancia != 'Pendiente'
                GROUP BY titular, importancia
                ORDER BY
                    CASE importancia
                        WHEN 'Alta'  THEN 1
                        WHEN 'Media' THEN 2
                        WHEN 'Baja'  THEN 3
                        ELSE 4
                    END,
                    titular
            """)
            rows = cursor.fetchall()
        finally:
            cursor.close()
        if not rows:
            return pd.DataFrame(
                columns=['titular', 'importancia', 'cantidad', 'fecha_min', 'fecha_max']
            )
        return pd.DataFrame(
            rows, columns=['titular', 'importancia', 'cantidad', 'fecha_min', 'fecha_max']
        )

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
                'value': procesables,
                'label': '🚀 Listos para Generar',
                'color': '#17a2b8' if procesables > 0 else '#6c757d'
            },
        ]

        UIComponents.create_metric_grid(metrics, columns=3)
    
    def _show_importance_breakdown(self, status):
        """Mostrar desglose por importancia con texto visible para titular en cards rojas"""
        if status['por_importancia']:
            with st.expander("📊 Desglose por Importancia", expanded=False):
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
                        # Texto blanco sobre fondos oscuros, oscuro sobre amarillo
                        text_color = '#333' if importancia == 'Media' else '#fff'
                        st.markdown(f"""
                        <div style='background:{color};padding:1rem;border-radius:8px;text-align:center;'>
                            <span style='font-size:2rem;font-weight:bold;color:{text_color};'>{cantidad}</span><br>
                            <span style='font-size:1rem;color:{text_color};font-weight:600;'>{importancia}</span>
                        </div>
                        """, unsafe_allow_html=True)
    
    def _show_generation_options(self, status):
        """Opciones de generación con resumen previo, filtros selectivos y confirmación."""
        procesables = status['reportes_pendientes'] - status['pendientes_importancia']

        # ── Caso: todo sin clasificar, nada procesable ────────────────────────
        if procesables == 0 and status['pendientes_importancia'] > 0:
            st.warning(
                f"⚠️ {status['reportes_pendientes']} registro(s) están marcados como "
                "'Pendiente'. Cambia la importancia para poder generar informes."
            )
            st.info("💡 Ve a la sección **Historial** para cambiar la importancia.")
            return

        # ── Caso: nada pendiente ──────────────────────────────────────────────
        if procesables == 0:
            st.success("✅ Todos los informes están actualizados")
            return

        if status['pendientes_importancia'] > 0:
            st.info(
                f"💡 {status['pendientes_importancia']} registro(s) marcados como "
                f"'Pendiente' no se procesarán. Listos para generar: {procesables}."
            )

        st.markdown("### 🚀 Generación de Informes")

        # ── Cargar detalle de pendientes ──────────────────────────────────────
        conn_detail = crear_conexion()
        if not conn_detail:
            st.error("❌ No se pudo conectar a la base de datos")
            return
        try:
            df_pending = self._get_pending_detail(conn_detail)
        except Exception as e:
            st.error(f"Error al leer los registros pendientes: {e}")
            return
        finally:
            conn_detail.close()

        if df_pending.empty:
            st.success("✅ No hay registros listos para generar")
            return

        # ── Filtros ───────────────────────────────────────────────────────────
        with st.expander("⚙️ Opciones de filtrado", expanded=False):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sel_titulares = st.multiselect(
                    "Titular(es)",
                    options=sorted(df_pending['titular'].unique().tolist()),
                    default=[],
                    key="_inf_sel_titulares",
                    placeholder="Todos los titulares",
                )
            with col_f2:
                sel_importancias = st.multiselect(
                    "Importancia",
                    options=sorted(df_pending['importancia'].unique().tolist()),
                    default=[],
                    key="_inf_sel_importancias",
                    placeholder="Todas las importancias",
                )

        # ── Aplicar filtros ───────────────────────────────────────────────────
        df_filtered = df_pending.copy()
        if sel_titulares:
            df_filtered = df_filtered[df_filtered['titular'].isin(sel_titulares)]
        if sel_importancias:
            df_filtered = df_filtered[df_filtered['importancia'].isin(sel_importancias)]

        # ── Preview / Resumen ─────────────────────────────────────────────────
        if df_filtered.empty:
            st.warning("⚠️ Ningún registro coincide con los filtros seleccionados.")
            return

        total_grupos    = len(df_filtered)
        total_registros = int(df_filtered['cantidad'].sum())

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("📄 Informes a generar",   total_grupos)
        col_m2.metric("📝 Registros incluidos", total_registros)

        # Distribución por importancia
        COLOR_EMOJI = {'Alta': '🔴', 'Media': '🟡', 'Baja': '🟢'}
        imp_summary = (
            df_filtered.groupby('importancia')
            .agg(registros=('cantidad', 'sum'), informes=('cantidad', 'count'))
            .reset_index()
        )
        for _, row in imp_summary.iterrows():
            emoji = COLOR_EMOJI.get(row['importancia'], '⚪')
            st.write(
                f"{emoji} **{row['importancia']}**: "
                f"{int(row['registros'])} registro(s) en "
                f"{int(row['informes'])} informe(s)"
            )

        # Detalle completo expandible
        with st.expander("Ver detalle completo de registros", expanded=False):
            st.dataframe(
                df_filtered.rename(columns={
                    'titular': 'Titular', 'importancia': 'Importancia',
                    'cantidad': 'Registros',
                    'fecha_min': 'Fecha mín.', 'fecha_max': 'Fecha máx.',
                }),
                use_container_width=True,
                hide_index=True,
            )

        # ── Confirmación explícita ────────────────────────────────────────────
        st.markdown("---")
        confirmado = st.checkbox(
            f"✅ Confirmo la generación de {total_grupos} informe(s) "
            f"({total_registros} registro(s) incluidos)",
            key="_inf_confirmado",
            value=False,
        )

        # ── Botón de generación ───────────────────────────────────────────────
        filtros = {}
        if sel_titulares:
            filtros['titulares'] = sel_titulares
        if sel_importancias:
            filtros['importancias'] = sel_importancias

        btn_label = (
            f"📄 Generar {total_grupos} informe(s) seleccionados"
            if filtros else
            f"📄 Generar todos los informes ({total_grupos})"
        )

        if st.button(
            btn_label,
            type="primary",
            use_container_width=True,
            disabled=(not confirmado),
        ):
            self._generate_all_reports(
                filtros=filtros if filtros else None,
                total_grupos=total_grupos,
            )

        if st.button("📋 Ver historial de reportes", use_container_width=True):
            SessionManager.set_current_page('historial')
            SessionManager.set('show_db_section', True)
            st.rerun()
    
    def _generate_all_reports(self, filtros=None, total_grupos=None):
        """Generar reportes usando report_generator con feedback de progreso en tiempo real.

        Args:
            filtros:      Dict opcional {'titulares': [...], 'importancias': [...]}.
                          None = generar todos los registros procesables.
            total_grupos: Número de informes esperados (para la barra de progreso).
        """
        import time
        import traceback
        import logging
        from paths import get_informes_dir, get_assets_dir, get_image_path, inicializar_assets, get_logo_path

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        report_logger = logging.getLogger('report_generation')

        try:
            st.info("🔄 Iniciando generación de informes…")

            progress_placeholder = st.empty()
            progress_bar         = st.progress(0)
            status_text          = st.empty()

            progress_placeholder.text("Verificando directorios y assets…")

            informes_dir = get_informes_dir()
            assets_dir   = get_assets_dir()
            imagenes_dir = get_image_path()

            for dir_path in [informes_dir, assets_dir, imagenes_dir]:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists("informes"):
                os.makedirs("informes", exist_ok=True)

            progress_placeholder.text("Inicializando recursos (logos)…")
            inicializar_assets()

            logo_path = get_logo_path()
            if not (logo_path and os.path.exists(logo_path)):
                report_logger.warning(
                    "Logo no encontrado. Los informes se generarán sin logo. "
                    "Coloca 'logo.jpg' o 'Logo.png' en 'assets' o 'imagenes'."
                )

            with st.spinner("🔄 Generando informes…"):
                progress_placeholder.text("Conectando a la base de datos…")
                conn = crear_conexion()
                if not conn:
                    st.error("❌ No se pudo conectar a la base de datos")
                    return

                start_time = time.time()
                progress_placeholder.text("Procesando registros y generando informes…")

                # ── Callback de progreso (actualiza barra en tiempo real) ─────
                _total = total_grupos or 1

                def _on_progress(current, total, titular_actual):
                    t = max(total, 1)
                    progress_bar.progress(min(current / t, 1.0))
                    msg = (
                        f"Generando {current}/{total}: {titular_actual}"
                        if titular_actual else
                        f"Completado: {current}/{total} informes"
                    )
                    status_text.text(msg)

                try:
                    resultado = generar_informe_pdf(
                        conn, filtros=filtros, on_progress=_on_progress
                    )
                finally:
                    conn.close()

                progress_bar.progress(1.0)
                elapsed_time = time.time() - start_time
                progress_placeholder.text(
                    f"Proceso completado en {elapsed_time:.1f} segundos"
                )
                status_text.empty()
                report_logger.info(f"Resultado de generación: {resultado}")

                # ── Mostrar resultado ─────────────────────────────────────────
                if resultado['success']:
                    if resultado['message'] == 'no_pending':
                        st.success("✅ No hay informes pendientes de generación")
                    elif resultado['message'] == 'completed':
                        generados = resultado.get('reportes_generados', 0)
                        errores   = resultado.get('errores', 0)
                        pendientes_exc = resultado.get('pendientes', 0)

                        if generados > 0:
                            st.success(
                                f"✅ {generados} informe(s) generados correctamente "
                                f"en {elapsed_time:.1f}s"
                            )
                        if pendientes_exc > 0:
                            st.info(
                                f"ℹ️ {pendientes_exc} registro(s) permanecen como "
                                "'Pendiente' y no fueron procesados"
                            )
                        if errores > 0:
                            st.warning(
                                f"⚠️ {errores} informe(s) tuvieron errores durante "
                                "la generación — revisa los logs para más detalle"
                            )
                        if generados == 0:
                            st.warning("⚠️ No se pudo generar ningún informe")
                        elif generados > 0:
                            st.info("ℹ️ Los informes generados aparecen en la sección de abajo.")
                else:
                    if resultado.get('message') == 'pending_only':
                        st.warning(
                            f"⚠️ Los {resultado.get('pendientes', 0)} registros están "
                            "marcados como 'Pendiente'. Cambia la importancia en 'Historial'."
                        )
                    elif resultado.get('message') == 'error':
                        st.error(
                            f"❌ Error al generar informes: "
                            f"{resultado.get('error', 'Error desconocido')}"
                        )
                    else:
                        st.error("❌ No se pudieron generar los informes")

            progress_placeholder.empty()

        except Exception as e:
            st.error(f"❌ Error durante la generación de informes: {e}")
            st.error(traceback.format_exc())
            report_logger.error(f"Error crítico en _generate_all_reports: {e}")
    
    
    
    
    
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

                st.divider()

                # Buscador de informes anteriores
                self._show_search_section()

                # Añadir sección de verificación de reportes
                self._show_verificacion_reportes_section()
                
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()

    # ── Configuración visual por nivel de importancia ─────────────────────────
    _IMP_STYLE = {
        'Alta':  {'border': '#dc3545', 'bg': '#fff5f5',
                  'badge_bg': '#dc3545', 'badge_fg': '#fff', 'label': '🔴 Alta'},
        'Media': {'border': '#e0a800', 'bg': '#fffef0',
                  'badge_bg': '#ffc107', 'badge_fg': '#333', 'label': '🟡 Media'},
        'Baja':  {'border': '#28a745', 'bg': '#f0fff4',
                  'badge_bg': '#28a745', 'badge_fg': '#fff', 'label': '🟢 Baja'},
    }
    _IMP_DEFAULT = {'border': '#adb5bd', 'bg': '#f8f9fa',
                    'badge_bg': '#6c757d', 'badge_fg': '#fff', 'label': '⚪ —'}

    def _parse_report_date(self, nombre_reporte: str, fecha_db) -> str:
        """Devuelve una fecha legible para mostrar en la tarjeta.

        Prioriza fecha_creacion_reporte de la BD.  Si no existe, intenta
        extraer la fecha del patrón YYYYMMDD_HHMMSS del nombre de archivo.
        """
        import re
        from datetime import datetime

        # 1. Desde la BD (formato: 'YYYY-MM-DD HH:MM:SS')
        if fecha_db:
            try:
                dt = datetime.strptime(str(fecha_db)[:19], "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d/%m/%Y  %H:%M")
            except ValueError:
                pass

        # 2. Desde el nombre del archivo (formato: ..._YYYYMMDD_HHMMSS.pdf)
        m = re.search(r'(\d{8})_(\d{6})', nombre_reporte or '')
        if m:
            try:
                dt = datetime.strptime(f"{m.group(1)}{m.group(2)}", "%Y%m%d%H%M%S")
                return dt.strftime("%d/%m/%Y  %H:%M")
            except ValueError:
                pass

        return "—"

    def _show_boletines_grid(self):
        """Últimos 10 informes generados: tarjetas con badge de importancia y fecha."""
        import pandas as pd
        import sqlite3
        from paths import get_db_path

        db_path = get_db_path()
        query = """
            SELECT id, titular, importancia, nombre_reporte,
                   ruta_reporte, fecha_creacion_reporte
            FROM boletines
            WHERE reporte_generado = 1
              AND ruta_reporte   IS NOT NULL
              AND nombre_reporte IS NOT NULL
            ORDER BY COALESCE(fecha_creacion_reporte, '') DESC, id DESC
            LIMIT 10
        """
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
        except Exception as e:
            st.error(f"Error al leer los informes: {e}")
            return
        finally:
            if conn:
                conn.close()

        if df.empty:
            st.info("No hay informes generados aún.")
            return

        st.markdown(
            "<h3 style='margin-top:2.5rem;margin-bottom:1rem;'>"
            "🗂️ Últimos informes generados</h3>",
            unsafe_allow_html=True,
        )

        # Distribuir en 2 columnas
        col_left, col_right = st.columns(2)
        columns = [col_left, col_right]

        for idx, row in df.iterrows():
            imp    = row.get('importancia') or ''
            style  = self._IMP_STYLE.get(imp, self._IMP_DEFAULT)
            fecha  = self._parse_report_date(
                row.get('nombre_reporte', ''),
                row.get('fecha_creacion_reporte'),
            )
            titular = str(row.get('titular') or '—')
            nombre  = str(row.get('nombre_reporte') or '—')

            with columns[idx % 2]:
                # ── Tarjeta HTML ──────────────────────────────────────────────
                st.markdown(f"""
                <div style="
                    background:{style['bg']};
                    border-left:4px solid {style['border']};
                    border-radius:8px;
                    padding:1rem 1.1rem 0.6rem 1.1rem;
                    margin-bottom:0.3rem;
                    box-shadow:0 1px 4px rgba(0,0,0,0.07);
                ">
                  <div style="display:flex;justify-content:space-between;
                              align-items:center;margin-bottom:0.4rem;">
                    <span style="
                        background:{style['badge_bg']};
                        color:{style['badge_fg']};
                        font-size:0.72rem;font-weight:700;
                        padding:2px 10px;border-radius:20px;
                        letter-spacing:0.04em;
                    ">{style['label']}</span>
                    <span style="font-size:0.78rem;color:#666;">{fecha}</span>
                  </div>
                  <div style="font-size:1.05rem;font-weight:700;
                              color:#1a1a2e;margin-bottom:0.15rem;
                              white-space:nowrap;overflow:hidden;
                              text-overflow:ellipsis;" title="{titular}">
                    {titular}
                  </div>
                  <div style="font-size:0.75rem;color:#888;
                              white-space:nowrap;overflow:hidden;
                              text-overflow:ellipsis;" title="{nombre}">
                    {nombre}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Botón de descarga bajo la tarjeta ─────────────────────────
                ruta = row.get('ruta_reporte', '')
                try:
                    with open(ruta, "rb") as f:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=f.read(),
                            file_name=nombre,
                            mime="application/pdf",
                            key=f"dl_grid_{row['id']}",
                            use_container_width=True,
                        )
                except Exception:
                    st.caption("⚠️ Archivo no disponible en disco")
    
    @staticmethod
    def _status_badge(reporte_generado: int, reporte_enviado: int) -> str:
        """Devuelve HTML de un badge de estado coloreado.

        🟢 Enviado     → reporte_enviado  = 1
        🟡 Generado    → reporte_generado = 1, reporte_enviado = 0
        🔴 No generado → reporte_generado = 0
        """
        if reporte_enviado:
            bg, fg, label = '#28a745', '#fff', '🟢 Enviado'
        elif reporte_generado:
            bg, fg, label = '#e0a800', '#333', '🟡 Generado'
        else:
            bg, fg, label = '#dc3545', '#fff', '🔴 No generado'

        return (
            f"<span style='"
            f"background:{bg};color:{fg};"
            f"font-size:0.72rem;font-weight:700;"
            f"padding:2px 10px;border-radius:20px;"
            f"letter-spacing:0.04em;white-space:nowrap;"
            f"'>{label}</span>"
        )

    def _show_search_section(self):
        """Buscador de informes anteriores dentro de un expander colapsado."""
        import sqlite3
        from paths import get_db_path

        with st.expander("🔎 Buscar informes anteriores", expanded=False):

            # ── Filtros ───────────────────────────────────────────────────────
            col_f1, col_f2, col_f3 = st.columns([3, 1.5, 1.5])

            with col_f1:
                txt_titular = st.text_input(
                    "Titular",
                    placeholder="Buscar por nombre del titular…",
                    key="_srch_titular",
                    label_visibility="visible",
                )
            with col_f2:
                sel_importancia = st.selectbox(
                    "Importancia",
                    options=["Todas", "Alta", "Media", "Baja", "Pendiente"],
                    key="_srch_importancia",
                    label_visibility="visible",
                )
            with col_f3:
                sel_envio = st.selectbox(
                    "Estado de envío",
                    options=["Todos", "Enviado", "No enviado"],
                    key="_srch_envio",
                    label_visibility="visible",
                )

            # ── Query dinámica ────────────────────────────────────────────────
            where = [
                "reporte_generado = 1",
                "ruta_reporte IS NOT NULL",
            ]
            params: list = []

            if txt_titular.strip():
                where.append("LOWER(titular) LIKE LOWER(?)")
                params.append(f"%{txt_titular.strip()}%")

            if sel_importancia != "Todas":
                where.append("importancia = ?")
                params.append(sel_importancia)

            if sel_envio == "Enviado":
                where.append("reporte_enviado = 1")
            elif sel_envio == "No enviado":
                where.append("reporte_enviado = 0")

            sql = f"""
                SELECT id, titular, importancia,
                       fecha_boletin, nombre_reporte, ruta_reporte,
                       reporte_generado, reporte_enviado
                FROM   boletines
                WHERE  {' AND '.join(where)}
                ORDER  BY fecha_boletin DESC
                LIMIT  50
            """

            # ── Ejecutar consulta ─────────────────────────────────────────────
            conn = None
            rows = []
            try:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                cursor.close()
            except Exception as e:
                st.error(f"Error al buscar informes: {e}")
                return
            finally:
                if conn:
                    conn.close()

            # ── Resultados ────────────────────────────────────────────────────
            if not rows:
                st.info("No se encontraron informes con los filtros seleccionados.")
                return

            st.markdown(
                f"<p style='color:#555;font-size:0.85rem;margin:0.4rem 0 0.8rem;'>"
                f"{len(rows)} resultado(s) encontrado(s)"
                f"{'  —  mostrando los primeros 50' if len(rows) == 50 else ''}"
                f"</p>",
                unsafe_allow_html=True,
            )

            imp_style = self._IMP_STYLE

            for row in rows:
                (rid, titular, importancia, fecha_boletin,
                 nombre_reporte, ruta_reporte,
                 reporte_generado, reporte_enviado) = row

                titular     = titular      or "—"
                importancia = importancia  or "—"
                fecha_str   = str(fecha_boletin or "—")
                nombre      = nombre_reporte or "—"

                imp_cfg  = imp_style.get(importancia, self._IMP_DEFAULT)
                badge_html = self._status_badge(reporte_generado, reporte_enviado)

                archivo_ok = bool(ruta_reporte and __import__('os').path.exists(ruta_reporte))

                col_info, col_btn = st.columns([5, 1])

                with col_info:
                    st.markdown(f"""
                    <div style="
                        background:{imp_cfg['bg']};
                        border-left:4px solid {imp_cfg['border']};
                        border-radius:6px;
                        padding:0.65rem 1rem;
                        margin-bottom:0.25rem;
                    ">
                      <div style="display:flex;align-items:center;
                                  gap:0.5rem;margin-bottom:0.25rem;flex-wrap:wrap;">
                        <span style="
                            background:{imp_cfg['badge_bg']};
                            color:{imp_cfg['badge_fg']};
                            font-size:0.7rem;font-weight:700;
                            padding:1px 9px;border-radius:20px;
                        ">{imp_cfg['label']}</span>
                        {badge_html}
                        <span style="font-size:0.78rem;color:#666;">
                            📅 {fecha_str}
                        </span>
                      </div>
                      <div style="font-weight:700;color:#000000;font-size:1rem;
                                  white-space:nowrap;overflow:hidden;
                                  text-overflow:ellipsis;" title="{titular}">
                        {titular}
                      </div>
                      <div style="font-size:0.73rem;color:#333333;
                                  white-space:nowrap;overflow:hidden;
                                  text-overflow:ellipsis;" title="{nombre}">
                        {nombre}
                      </div>
                      {'<div style="font-size:0.72rem;color:#dc3545;margin-top:0.2rem;">'
                       '⚠️ Archivo no encontrado en disco</div>'
                       if not archivo_ok else ''}
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    if archivo_ok:
                        try:
                            with open(ruta_reporte, "rb") as f:
                                st.download_button(
                                    label="📥",
                                    data=f.read(),
                                    file_name=nombre,
                                    mime="application/pdf",
                                    key=f"srch_dl_{rid}",
                                    use_container_width=True,
                                    help="Descargar PDF",
                                )
                        except Exception:
                            st.caption("⚠️ Error")
                    else:
                        st.button(
                            "📥",
                            disabled=True,
                            key=f"srch_dl_dis_{rid}",
                            use_container_width=True,
                            help="Archivo no disponible",
                        )

    def _show_verificacion_reportes_section(self):
        """Muestra la sección para verificar titulares sin reportes"""
        with st.expander("🔍 Verificación de Titulares sin Reportes", expanded=False):
            st.markdown("""
            ### 🔔 Verificación de Titulares sin Reportes
            
            Esta herramienta verifica qué titulares no tienen reportes generados durante el mes actual 
            y les envía un correo electrónico de notificación.
            """)

            # ── [UX] Período analizado ────────────────────────────────────────
            _fa = datetime.now()
            _primer_dia_mp = (_fa.replace(day=1) - timedelta(days=1)).replace(day=1)
            _ultimo_dia_mp = _fa.replace(day=1) - timedelta(days=1)
            _MESES = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
            }
            _nombre_mes_ui = _MESES.get(_primer_dia_mp.month, str(_primer_dia_mp.month))
            st.info(
                f"🔎 **Analizando período:** {_nombre_mes_ui} {_primer_dia_mp.year}  \n"
                f"Desde: {_primer_dia_mp.strftime('%d/%m/%Y')}  "
                f"— Hasta: {_ultimo_dia_mp.strftime('%d/%m/%Y')}"
            )
            # ── [/UX] ─────────────────────────────────────────────────────────

            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Mostrar resultado de verificación automática si existe
                from src.utils.session_manager import SessionManager
                resultado_verificacion = SessionManager.get('resultado_verificacion_reportes', None)
                
                if resultado_verificacion:
                    estado = resultado_verificacion.get('estado', '')
                    
                    if estado == 'completado':
                        st.success("✅ Verificación automática realizada")

                        # Mostrar mensaje específico para la UI si la verificación lo generó
                        mensaje_ui = resultado_verificacion.get('mensaje_ui')
                        if mensaje_ui:
                            # Mensaje informativo persistente para que el usuario lo vea después del rerun
                            st.info(mensaje_ui)

                        metrics = [
                            {"value": resultado_verificacion.get('titulares_con_marcas_sin_reportes', 0), 
                             "label": "Titulares con marcas sin reportes", 
                             "color": "#ffc107"},
                            {"value": resultado_verificacion.get('emails_enviados', 0), 
                             "label": "Emails enviados", 
                             "color": "#28a745"},
                            {"value": resultado_verificacion.get('ya_notificados', 0), 
                             "label": "Ya notificados", 
                             "color": "#17a2b8"},
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
                            # Importar el módulo correctamente usando sys.path para asegurarnos de que encuentre el archivo
                            import sys
                            import os
                            
                            # Añadir el directorio raíz de la aplicación al path
                            app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                            if app_root not in sys.path:
                                sys.path.insert(0, app_root)
                            
                            from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes
                            from database import crear_conexion
                            
                            conn = crear_conexion()
                            if conn:
                                try:
                                    resultado = verificar_titulares_sin_reportes(conn)
                                finally:
                                    conn.close()
                                
                                # Guardar resultado en la sesión
                                SessionManager.set('resultado_verificacion_reportes', resultado)
                                
                                if resultado['estado'] == 'completado':
                                    st.success("✅ Verificación completada con éxito")
                                    # Mostrar mensaje UI si existe (por ejemplo: "No hay reportes para enviar")
                                    if resultado.get('mensaje_ui'):
                                        st.info(resultado.get('mensaje_ui'))
                                    else:
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
