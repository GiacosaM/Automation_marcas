# dashboard.py - Nuevo módulo para el dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import crear_conexion, crear_tabla, convertir_query_boolean

def get_dashboard_data(conn):
    """Obtiene datos para el dashboard con compatibilidad PostgreSQL nativa."""
    from database import usar_supabase
    
    cursor = conn.cursor()
    
    if usar_supabase():
        # Usar queries nativas de PostgreSQL para compatibilidad total
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total_boletines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = TRUE")
        reportes_generados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = TRUE")
        reportes_enviados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        # Datos por fecha (últimos 30 días) - PostgreSQL nativo
        cursor.execute("""
            SELECT fecha_alta::date as fecha, COUNT(*) as cantidad
            FROM boletines 
            WHERE fecha_alta >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY fecha_alta::date
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
        
        # Reportes próximos a vencer (entre 23 y 30 días desde fecha del boletín)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = FALSE 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND LENGTH(fecha_boletin) = 10
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '23 days' <= CURRENT_DATE
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' >= CURRENT_DATE
        """)
        proximos_vencer = cursor.fetchone()[0]
        
        # Reportes vencidos (más de 30 días)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = FALSE 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND LENGTH(fecha_boletin) = 10
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' < CURRENT_DATE
        """)
        reportes_vencidos = cursor.fetchone()[0]
        
        # Detalles de reportes próximos a vencer
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   EXTRACT(EPOCH FROM (TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' - CURRENT_DATE))/86400 as dias_restantes
            FROM boletines 
            WHERE reporte_enviado = FALSE 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND LENGTH(fecha_boletin) = 10
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '23 days' <= CURRENT_DATE
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' >= CURRENT_DATE
            ORDER BY dias_restantes ASC
            LIMIT 10
        """)
        detalles_proximos_vencer = cursor.fetchall()
        
        # Detalles de reportes vencidos
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   EXTRACT(EPOCH FROM (CURRENT_DATE - (TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days')))/86400 as dias_vencido
            FROM boletines 
            WHERE reporte_enviado = FALSE 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND LENGTH(fecha_boletin) = 10
            AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' < CURRENT_DATE
            ORDER BY dias_vencido DESC
            LIMIT 10
        """)
        detalles_vencidos = cursor.fetchall()
        
    else:
        # Usar queries de SQLite (mantener código original)
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total_boletines = cursor.fetchone()[0]
        
        query_generados = convertir_query_boolean("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
        cursor.execute(query_generados)
        reportes_generados = cursor.fetchone()[0]
        
        query_enviados = convertir_query_boolean("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
        cursor.execute(query_enviados)
        reportes_enviados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        # Datos por fecha (últimos 30 días)
        query_timeline = convertir_query_boolean("""
            SELECT DATE(fecha_alta) as fecha, COUNT(*) as cantidad
            FROM boletines 
            WHERE fecha_alta >= date('now', '-30 days')
            GROUP BY DATE(fecha_alta)
            ORDER BY fecha
        """)
        cursor.execute(query_timeline)
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
        
        # Para SQLite, usar cálculos aproximados para vencimientos
        proximos_vencer = 0
        reportes_vencidos = 0
        detalles_proximos_vencer = []
        detalles_vencidos = []
    
    cursor.close()
    
    return {
        'total_boletines': total_boletines,
        'reportes_generados': reportes_generados,
        'reportes_enviados': reportes_enviados,
        'total_clientes': total_clientes,
        'proximos_vencer': proximos_vencer,
        'reportes_vencidos': reportes_vencidos,
        'detalles_proximos_vencer': detalles_proximos_vencer,
        'detalles_vencidos': detalles_vencidos,
        'datos_timeline': datos_timeline,
        'top_titulares': top_titulares
    }

def create_timeline_chart(datos_timeline):
    """Crea gráfico de línea temporal."""
    if not datos_timeline:
        return None
    
    df = pd.DataFrame(datos_timeline, columns=['fecha', 'cantidad'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    fig = px.line(
        df, x='fecha', y='cantidad',
        title='Boletines Procesados (Últimos 30 días)',
        labels={'fecha': 'Fecha', 'cantidad': 'Cantidad de Boletines'}
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#1e293b',
        title_font_size=16,
        showlegend=False
    )
    
    fig.update_traces(
        line=dict(color='#3b82f6', width=3),
        fill='tonexty',
        fillcolor='rgba(59, 130, 246, 0.1)'
    )
    
    return fig

def create_top_clients_chart(top_titulares):
    """Crea gráfico de barras de top clientes."""
    if not top_titulares:
        return None
    
    df = pd.DataFrame(top_titulares, columns=['titular', 'cantidad'])
    
    fig = px.bar(
        df, x='cantidad', y='titular',
        orientation='h',
        title='Top 10 Titulares por Cantidad de Boletines',
        labels={'cantidad': 'Cantidad', 'titular': 'Titular'}
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#1e293b',
        title_font_size=16,
        height=400
    )
    
    fig.update_traces(marker_color='#3b82f6')
    
    return fig

def create_status_donut(reportes_generados, reportes_enviados, total_boletines):
    """Crea gráfico de dona para estados de reportes."""
    pendientes_generacion = total_boletines - reportes_generados
    pendientes_envio = reportes_generados - reportes_enviados
    
    labels = ['Enviados', 'Pendiente Envío', 'Pendiente Generación']
    values = [reportes_enviados, pendientes_envio, pendientes_generacion]
    colors = ['#10b981', '#f59e0b', '#ef4444']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=.3,
        marker_colors=colors
    )])
    
    fig.update_layout(
        title="Estado de Reportes",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#1e293b',
        title_font_size=16
    )
    
    return fig

def show_dashboard():
    """Muestra el dashboard principal."""
    st.markdown('<div class="main-header"><h1>📊 Sistema de Gestión de Marcas</h1><p>Panel de Control Ejecutivo</p></div>', unsafe_allow_html=True)
    
    # Obtener datos
    conn = crear_conexion()
    if not conn:
        st.error("No se pudo conectar a la base de datos")
        return
    
    try:
        crear_tabla(conn)
        data = get_dashboard_data(conn)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📋 Total Boletines",
                value=data['total_boletines'],
                delta=f"+{data['total_boletines'] - data['reportes_generados']} pendientes"
            )
        
        with col2:
            st.metric(
                label="📄 Reportes Generados",
                value=data['reportes_generados'],
                delta=f"{(data['reportes_generados']/max(data['total_boletines'], 1)*100):.1f}%" if data['total_boletines'] > 0 else "0%"
            )
        
        with col3:
            st.metric(
                label="📧 Reportes Enviados",
                value=data['reportes_enviados'],
                delta=f"{(data['reportes_enviados']/max(data['reportes_generados'], 1)*100):.1f}%" if data['reportes_generados'] > 0 else "0%"
            )
        
        with col4:
            st.metric(
                label="👥 Clientes Registrados",
                value=data['total_clientes']
            )
        
        st.divider()
        
        # Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Timeline de boletines
            timeline_fig = create_timeline_chart(data['datos_timeline'])
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar la línea temporal")
        
        with col_right:
            # Estado de reportes
            donut_fig = create_status_donut(
                data['reportes_generados'], 
                data['reportes_enviados'], 
                data['total_boletines']
            )
            st.plotly_chart(donut_fig, use_container_width=True)
        
        # Top clientes
        st.subheader("📈 Análisis de Clientes")
        top_clients_fig = create_top_clients_chart(data['top_titulares'])
        if top_clients_fig:
            st.plotly_chart(top_clients_fig, use_container_width=True)
        else:
            st.info("No hay datos de titulares para mostrar")
        
        # Alertas y notificaciones
        st.subheader("🔔 Alertas del Sistema")
        
        pendientes_generacion = data['total_boletines'] - data['reportes_generados']
        pendientes_envio = data['reportes_generados'] - data['reportes_enviados']
        
        if pendientes_generacion > 0:
            st.warning(f"⚠️ Hay {pendientes_generacion} boletines pendientes de generar reportes")
        
        if pendientes_envio > 0:
            st.info(f"📧 Hay {pendientes_envio} reportes listos para enviar")
        
        if pendientes_generacion == 0 and pendientes_envio == 0 and data['total_boletines'] > 0:
            st.success("✅ Todos los reportes han sido procesados y enviados")
    
    except Exception as e:
        st.error(f"Error al cargar el dashboard: {e}")
    finally:
        conn.close()