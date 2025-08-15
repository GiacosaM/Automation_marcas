"""
Página del Dashboard - Panel de Control
"""
import streamlit as st
import pandas as pd
import sys
import os
from streamlit_extras.grid import grid
from streamlit_extras.colored_header import colored_header
from streamlit_extras.metric_cards import style_metric_cards

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, crear_tabla
from dashboard_charts import create_status_donut_chart, create_urgency_gauge_chart
from professional_theme import create_metric_card
from src.ui.components import UIComponents
from src.utils.helpers import ReportUtils, DateUtils


class DashboardPage:
    """Página del Dashboard con análisis y métricas"""
    
    def __init__(self):
        self.conn = None
    
    def _get_dashboard_data(self, conn):
        """Obtiene datos para el dashboard."""
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total_boletines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
        reportes_generados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
        reportes_enviados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        # Datos por fecha (últimos 30 días)
        cursor.execute("""
            SELECT DATE(fecha_alta) as fecha, COUNT(*) as cantidad
            FROM boletines 
            WHERE fecha_alta >= date('now', '-30 days')
            GROUP BY DATE(fecha_alta)
            ORDER BY fecha
        """)
        datos_timeline = cursor.fetchall()
        
        # Top titulares
        cursor.execute("""
            SELECT titular, COUNT(*) as cantidad
            FROM boletines
            GROUP BY titular
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        top_titulares = cursor.fetchall()
        
        # Reportes próximos a vencer (últimos 7 días de plazo legal)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
        """)
        proximos_vencer = cursor.fetchone()[0]
        
        # Reportes ya vencidos (más de 30 días)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') < date('now')
        """)
        reportes_vencidos = cursor.fetchone()[0]
        
        # Detalles de reportes próximos a vencer
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) - 
                        julianday(date('now')) AS INTEGER) as dias_restantes
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
            ORDER BY dias_restantes ASC
            LIMIT 10
        """)
        detalles_proximos_vencer = cursor.fetchall()
        
        # Detalles de reportes vencidos
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date('now')) - 
                        julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) AS INTEGER) as dias_vencido
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') < date('now')
            ORDER BY dias_vencido DESC
            LIMIT 10
        """)
        detalles_vencidos = cursor.fetchall()
        
        cursor.close()
        
        return {
            'total_boletines': total_boletines,
            'reportes_generados': reportes_generados,
            'reportes_enviados': reportes_enviados,
            'total_clientes': total_clientes,
            'datos_timeline': datos_timeline,
            'top_titulares': top_titulares,
            'proximos_vencer': proximos_vencer,
            'reportes_vencidos': reportes_vencidos,
            'detalles_proximos_vencer': detalles_proximos_vencer,
            'detalles_vencidos': detalles_vencidos
        }
    
    def _show_main_header(self):
        """Mostrar header principal del dashboard"""
        st.markdown("""
        <div class="main-header">
            <h1>Panel de Control - Mi Marca</h1>
            
        </div>
        """, unsafe_allow_html=True)
    
    def _show_metrics(self, data):
        """Mostrar métricas principales"""
        # Calcular porcentajes
        gen_percentage = (data['reportes_generados']/max(data['total_boletines'], 1)*100) if data['total_boletines'] > 0 else 0
        env_percentage = (data['reportes_enviados']/max(data['reportes_generados'], 1)*100) if data['reportes_generados'] > 0 else 0
        
        # Definir métricas
        metrics = [
            {
                'value': data['total_boletines'],
                'label': '📋 Total Boletines',
                'color': '#667eea'
            },
            {
                'value': f"{data['reportes_generados']}",
                'label': f"📄 Reportes Generados ({gen_percentage:.1f}%)",
                'color': '#28a745'
            },
            {
                'value': f"{data['reportes_enviados']}",
                'label': f"📧 Reportes Enviados ({env_percentage:.1f}%)",
                'color': '#17a2b8'
            },
            {
                'value': data['proximos_vencer'],
                'label': '⏰ Próximos a Vencer',
                'color': '#dc3545' if data['proximos_vencer'] > 0 else '#28a745'
            },
            {
                'value': data['reportes_vencidos'],
                'label': '🚨 Vencidos',
                'color': '#dc3545' if data['reportes_vencidos'] > 0 else '#28a745'
            }
        ]
        
        UIComponents.create_metric_grid(metrics, columns=5)
    
    def _show_alerts(self, data):
        """Mostrar alertas del sistema"""
        UIComponents.create_section_header(
            "🔔 Alertas del Sistema",
            "Estado actual de reportes y notificaciones críticas",
            "blue-70"
        )
        
        # Preparar alertas
        alerts = []
        
        # Alertas críticas
        if data['reportes_vencidos'] > 0:
            alerts.append({
                'type': 'error',
                'message': f"🚨 **CRÍTICO**: {data['reportes_vencidos']} reportes han superado el plazo legal",
                'details': UIComponents.create_info_card(

                    "<h4 class='error-card'>⚠️ Acción requerida</h4>",
                    "<div class='error-card'>Revisar reportes vencidos inmediatamente</div>",
                    "error"
                )
            })
        else:
            alerts.append({
                'type': 'success',
                'message': "✅ **Cumplimiento Legal**: Todos los reportes están dentro del plazo",
                'details': UIComponents.create_info_card(
                    "📊 Estado",
                    "Excelente cumplimiento normativo",
                    "success"
                )
            })
        
        # Alertas de urgencia
        if data['proximos_vencer'] > 0:
            alerts.append({
                'type': 'warning',
                'message': f"⏰ **URGENTE**: {data['proximos_vencer']} reportes vencen en los próximos 7 días",
                'details': UIComponents.create_info_card(
                    "<h4 class='warning-card'>💡 Recomendación</h4>",
                    "<div class='warning-card'>Priorizar estos reportes</div>",
                    "warning"
                )
            })
        else:
            alerts.append({
                'type': 'info',
                'message': "📅 **Plazos Controlados**: Sin vencimientos próximos",
                'details': UIComponents.create_info_card(
                    "📈 Estado",
                    "Planificación temporal adecuada",
                    "info"
                )
            })
        
        UIComponents.create_alert_grid(alerts, columns=2)
    
    def _show_expired_details(self, data):
        """Mostrar detalles de reportes vencidos"""
        if data['reportes_vencidos'] > 0:
            with st.expander("🔍 Detalles de Reportes Vencidos", expanded=True):
                if data['detalles_vencidos']:
                    st.markdown("### Reportes que requieren atención inmediata:")
                    for detalle in data['detalles_vencidos']:
                        dias_vencido = int(detalle[3])
                        
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #dc3545; color: #000000;">
                            <strong style='color: #000000;'>Boletín {detalle[0]}</strong> - <span class='expirado-titular'>{detalle[1][:50]}...</span><br>
                            <small style="color: #555555;">Fecha: {detalle[2]} | <span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">🚨 Vencido hace {dias_vencido} días</span></small>
                        </div>
                        """, unsafe_allow_html=True)
    
    def _show_upcoming_details(self, data):
        """Mostrar detalles de reportes próximos a vencer"""
        if data['proximos_vencer'] > 0:
            with st.expander("📋 Reportes Próximos a Vencer", expanded=True):
                if data['detalles_proximos_vencer']:
                    st.markdown("### Reportes que requieren atención prioritaria:")
                    for detalle in data['detalles_proximos_vencer']:
                        dias_restantes = int(detalle[3])
                        
                        if dias_restantes <= 2:
                            color = '#dc3545'
                            icon = '🚨'
                            texto = f'Crítico - {dias_restantes} días restantes'
                        elif dias_restantes <= 5:
                            color = '#ffc107'
                            icon = '⏰'
                            texto = f'Urgente - {dias_restantes} días restantes'
                        else:
                            color = '#28a745'
                            icon = '📅'
                            texto = f'{dias_restantes} días restantes'
                        
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid {color}; color: #000000;">
                            <strong style='color: #000000;'>Boletín {detalle[0]}</strong> - <span class='expirado-titular'>{detalle[1][:50]}...</span><br>
                            <small style="color: #555555;">Fecha: {detalle[2]} | <span class="vencimiento-chip" style="background: {color}; color: #000000; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">{icon} {texto}</span></small>
                        </div>
                        """, unsafe_allow_html=True)
    
    def _show_charts(self, data):
        """Mostrar gráficos del dashboard"""
        if data['total_boletines'] > 0:
            UIComponents.create_section_header(
                "📊 Análisis Visual",
                "Gráficos y estadísticas avanzadas del sistema",
                "violet-70"
            )
            
            # Grid de gráficos
            chart_grid = grid(2, vertical_align="top")
            
            # Gráfico de dona - Estado de reportes
            with chart_grid.container():
                st.markdown("### 📊 Estado de Reportes")
                try:
                    fig_donut = create_status_donut_chart(data)
                    st.plotly_chart(fig_donut, use_container_width=True)
                except Exception as e:
                    st.warning(f"Error al cargar gráfico de dona: {e}")
            
            # Gauge de urgencia
            with chart_grid.container():
                st.markdown("### 🚨 Monitor de Urgencia")
                try:
                    fig_gauge = create_urgency_gauge_chart(data)
                    st.plotly_chart(fig_gauge, use_container_width=True)
                except Exception as e:
                    st.warning(f"Error al cargar gauge de urgencia: {e}")
    
    def _show_positive_messages(self, data):
        """Mostrar mensajes de estado positivo"""
        if data['reportes_vencidos'] == 0 and data['proximos_vencer'] == 0:
            if data['total_boletines'] > 0:
                st.success("✅ ¡Excelente! Todos los reportes están dentro del plazo legal y bajo control")
        
        if data['total_boletines'] == 0:
            st.info("📂 No hay boletines cargados en el sistema. Use la sección 'Cargar Datos' para comenzar.")
    
    def show(self):
        """Mostrar la página del dashboard"""
        try:
            # Header principal
            self._show_main_header()
            
            # Obtener datos
            conn = crear_conexion()
            if not conn:
                st.error("No se pudo conectar a la base de datos")
                return
            
            try:
                crear_tabla(conn)
                data = self._get_dashboard_data(conn)
                
                # Mostrar métricas principales
                self._show_metrics(data)
                
                # Mostrar alertas
                self._show_alerts(data)
                
                # Mostrar detalles expandibles
                self._show_expired_details(data)
                self._show_upcoming_details(data)
                
                # Mostrar mensajes positivos
                self._show_positive_messages(data)
                
                # Mostrar gráficos
                self._show_charts(data)
                
                # Estilizar las métricas
                style_metric_cards(
                    background_color="#ffffff",
                    border_left_color="#667eea",
                    border_color="#e9ecef",
                    box_shadow="#f0f0f0"
                )
                
            except Exception as e:
                st.error(f"Error al cargar el dashboard: {e}")
            finally:
                conn.close()
                
        except Exception as e:
            st.error(f"Error crítico en el dashboard: {e}")


def show_dashboard():
    """Función de compatibilidad para mostrar el dashboard"""
    dashboard = DashboardPage()
    dashboard.show()
