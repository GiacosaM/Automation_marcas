import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_status_donut_chart(data):
    """Crea un gráfico de dona profesional para el estado de reportes"""
    
    # Datos para el gráfico
    labels = ['Generados', 'Enviados', 'Pendientes']
    values = [
        data['reportes_generados'] - data['reportes_enviados'],
        data['reportes_enviados'], 
        data['total_boletines'] - data['reportes_generados']
    ]
    colors = ['#ffc107', '#28a745', '#dc3545']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.6,
        marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, color='white', family='Inter'),
        hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )])
    
    # Agregar texto central
    total = sum(values)
    fig.add_annotation(
        text=f"<b>{total}</b><br>Total<br>Boletines",
        x=0.5, y=0.5,
        font_size=16,
        font_color="#495057",
        showarrow=False
    )
    
    fig.update_layout(
        title={
            'text': "📊 Estado de Reportes",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#495057', 'family': 'Inter'}
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=50, b=50, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300
    )
    
    return fig

def create_urgency_gauge_chart(data):
    """Crea un gauge chart para mostrar la urgencia del sistema"""
    
    total_problemas = data['reportes_vencidos'] + data['proximos_vencer']
    max_gauge = max(total_problemas + 5, 20)  # Escala dinámica
    
    # Determinar color y texto basado en la urgencia
    if data['reportes_vencidos'] > 0:
        color = "red"
        status = "CRÍTICO"
    elif data['proximos_vencer'] > 5:
        color = "orange"
        status = "URGENTE"
    elif data['proximos_vencer'] > 0:
        color = "yellow"
        status = "ATENCIÓN"
    else:
        color = "green"
        status = "CONTROLADO"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = total_problemas,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"🚨 Estado del Sistema<br><span style='font-size:14px'>{status}</span>"},
        delta = {'reference': 0, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, max_gauge], 'tickwidth': 1, 'tickcolor': "#495057"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#dee2e6",
            'steps': [
                {'range': [0, max_gauge * 0.3], 'color': "#d4edda"},
                {'range': [max_gauge * 0.3, max_gauge * 0.6], 'color': "#fff3cd"},
                {'range': [max_gauge * 0.6, max_gauge], 'color': "#f8d7da"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_gauge * 0.8
            }
        }
    ))
    
    fig.update_layout(
        margin=dict(t=50, b=50, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        font=dict(family='Inter', color='#495057')
    )
    
    return fig

def create_timeline_chart(data):
    """Crea un gráfico de línea temporal para mostrar tendencias"""
    
    # Datos simulados para demostración (en una implementación real vendría de la BD)
    dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
    reportes_mes = [45, 52, 38, 61, 47, 55, 42, 58, 63, 49, 56, data['total_boletines']]
    enviados_mes = [43, 50, 36, 59, 45, 53, 40, 56, 61, 47, 54, data['reportes_enviados']]
    
    fig = go.Figure()
    
    # Línea de reportes generados
    fig.add_trace(go.Scatter(
        x=dates,
        y=reportes_mes,
        mode='lines+markers',
        name='Reportes Generados',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#667eea'),
        hovertemplate='<b>Reportes Generados</b><br>Fecha: %{x}<br>Cantidad: %{y}<extra></extra>'
    ))
    
    # Línea de reportes enviados
    fig.add_trace(go.Scatter(
        x=dates,
        y=enviados_mes,
        mode='lines+markers',
        name='Reportes Enviados',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8, color='#28a745'),
        hovertemplate='<b>Reportes Enviados</b><br>Fecha: %{x}<br>Cantidad: %{y}<extra></extra>'
    ))
    
    # Área de diferencia
    fig.add_trace(go.Scatter(
        x=dates,
        y=[g-e for g, e in zip(reportes_mes, enviados_mes)],
        mode='lines',
        name='Pendientes de Envío',
        fill='tozeroy',
        fillcolor='rgba(255, 193, 7, 0.3)',
        line=dict(color='rgba(255, 193, 7, 0.6)', width=2),
        hovertemplate='<b>Pendientes</b><br>Fecha: %{x}<br>Cantidad: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': "📈 Tendencia Mensual de Reportes",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#495057', 'family': 'Inter'}
        },
        xaxis_title="Período",
        yaxis_title="Cantidad de Reportes",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=50, b=80, l=50, r=50),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        font=dict(family='Inter', color='#495057')
    )
    
    # Estilo de grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig

def create_compliance_bar_chart(data):
    """Crea un gráfico de barras para el cumplimiento por categoría"""
    
    # Calcular datos de cumplimiento
    total_en_plazo = data['total_boletines'] - data['reportes_vencidos']
    cumplimiento_general = (total_en_plazo / max(data['total_boletines'], 1) * 100) if data['total_boletines'] > 0 else 100
    eficiencia_envios = (data['reportes_enviados'] / max(data['total_boletines'], 1) * 100) if data['total_boletines'] > 0 else 0
    eficiencia_generacion = (data['reportes_generados'] / max(data['total_boletines'], 1) * 100) if data['total_boletines'] > 0 else 0
    
    categorias = ['Cumplimiento<br>Legal', 'Eficiencia<br>Generación', 'Eficiencia<br>Envíos']
    valores = [cumplimiento_general, eficiencia_generacion, eficiencia_envios]
    colores = ['#28a745' if v >= 95 else '#ffc107' if v >= 80 else '#dc3545' for v in valores]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categorias,
            y=valores,
            marker_color=colores,
            text=[f'{v:.1f}%' for v in valores],
            textposition='auto',
            textfont=dict(size=14, color='white', family='Inter'),
            hovertemplate='<b>%{x}</b><br>Porcentaje: %{y:.1f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title={
            'text': "📊 Indicadores de Rendimiento",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#495057', 'family': 'Inter'}
        },
        yaxis_title="Porcentaje (%)",
        yaxis=dict(range=[0, 100]),
        margin=dict(t=50, b=50, l=50, r=50),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        font=dict(family='Inter', color='#495057')
    )
    
    # Líneas de referencia
    fig.add_hline(y=95, line_dash="dash", line_color="green", opacity=0.7,
                  annotation_text="Objetivo: 95%", annotation_position="bottom right")
    fig.add_hline(y=80, line_dash="dash", line_color="orange", opacity=0.7,
                  annotation_text="Mínimo: 80%", annotation_position="top right")
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig
