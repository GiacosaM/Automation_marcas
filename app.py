# app.py - Versión integrada con dashboard y configuración

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# Importar configuración
from config import get_config, set_config, show_settings_page

# Importar módulos existentes
from database import crear_conexion, crear_tabla, insertar_datos, obtener_datos, actualizar_registro, eliminar_registro, insertar_cliente, obtener_clientes, actualizar_cliente, eliminar_cliente
from extractor import extraer_datos_agrupados
from report_generator import generar_informe_pdf
from email_sender import procesar_envio_emails, generar_reporte_envios

# Configuración de página usando config
st.set_page_config(
    page_title=get_config("app.title", "Sistema de Gestión de Marcas"),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown(f"""
<style>
    /* Tema profesional */
    .main {{
        padding-top: 2rem;
    }}
    
    /* Header principal */
    .main-header {{
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* Cards de estadísticas */
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }}
    
    /* Botones mejorados */
    .stButton > button {{
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }}
    
    /* Navbar fija mejorada */
    .navbar {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        padding: 1rem 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    /* Tablas mejoradas */
    .dataframe {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    /* Progress bars */
    .stProgress > div > div {{
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    }}
</style>
""", unsafe_allow_html=True)
# ================================
# FUNCIONES DEL DASHBOARD
# ================================

def get_dashboard_data(conn):
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
    
    cursor.close()
    
    return {
        'total_boletines': total_boletines,
        'reportes_generados': reportes_generados,
        'reportes_enviados': reportes_enviados,
        'total_clientes': total_clientes,
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
    company_name = get_config("app.company_name", "Mi Estudio Contable")
    st.markdown(f'<div class="main-header"><h1>📊 {get_config("app.title", "Sistema de Gestión de Marcas")}</h1><p>Panel de Control Ejecutivo - {company_name}</p></div>', unsafe_allow_html=True)
    
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
                delta=f"{data['total_boletines'] - data['reportes_generados']} pendientes" if data['total_boletines'] - data['reportes_generados'] > 0 else "Todo procesado"
            )
        
        with col2:
            percentage = (data['reportes_generados']/max(data['total_boletines'], 1)*100) if data['total_boletines'] > 0 else 0
            st.metric(
                label="📄 Reportes Generados",
                value=data['reportes_generados'],
                delta=f"{percentage:.1f}%"
            )
        
        with col3:
            percentage = (data['reportes_enviados']/max(data['reportes_generados'], 1)*100) if data['reportes_generados'] > 0 else 0
            st.metric(
                label="📧 Reportes Enviados",
                value=data['reportes_enviados'],
                delta=f"{percentage:.1f}%"
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
                st.info("📈 No hay datos suficientes para mostrar la línea temporal")
        
        with col_right:
            # Estado de reportes
            donut_fig = create_status_donut(
                data['reportes_generados'], 
                data['reportes_enviados'], 
                data['total_boletines']
            )
            st.plotly_chart(donut_fig, use_container_width=True)
        
        # Top clientes (solo si está habilitado en configuración)
        if get_config("reports.include_charts", True):
            st.subheader("📈 Análisis de Clientes")
            top_clients_fig = create_top_clients_chart(data['top_titulares'])
            if top_clients_fig:
                st.plotly_chart(top_clients_fig, use_container_width=True)
            else:
                st.info("📊 No hay datos de titulares para mostrar")
        
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
        
        if data['total_boletines'] == 0:
            st.info("📂 No hay boletines cargados en el sistema")
    
    except Exception as e:
        st.error(f"Error al cargar el dashboard: {e}")
    finally:
        conn.close()

# ================================
# INICIALIZACIÓN DE ESTADO
# ================================


# Inicializar estado de la sesión
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'show_db_section' not in st.session_state:
    st.session_state.show_db_section = False
if 'show_clientes_section' not in st.session_state:
    st.session_state.show_clientes_section = False
if 'show_email_section' not in st.session_state:
    st.session_state.show_email_section = False
if 'selected_record_id' not in st.session_state:
    st.session_state.selected_record_id = None
if 'selected_cliente_id' not in st.session_state:
    st.session_state.selected_cliente_id = None
if 'db_data' not in st.session_state:
    st.session_state.db_data = None
if 'clientes_data' not in st.session_state:
    st.session_state.clientes_data = None
if 'pending_action' not in st.session_state:
    st.session_state.pending_action = None
if 'pending_data' not in st.session_state:
    st.session_state.pending_data = None
if 'datos_insertados' not in st.session_state:
    st.session_state.datos_insertados = False
if 'email_credentials' not in st.session_state:
    st.session_state.email_credentials = {'email': '', 'password': ''}
if 'confirmar_generar_informes' not in st.session_state:
    st.session_state.confirmar_generar_informes = False

# ================================
# BARRA DE NAVEGACIÓN
# ================================

st.markdown('<div class="navbar">', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6, col_nav7 = st.columns(7)

with col_nav1:
    if st.button("🏠 Dashboard"):
        st.session_state.current_page = 'dashboard'
        # Reset other sections
        st.session_state.show_db_section = False
        st.session_state.show_clientes_section = False
        st.session_state.show_email_section = False
        st.rerun()

with col_nav2:
    if st.button("📤 Cargar Datos"):
        st.session_state.current_page = 'upload'
        st.session_state.show_db_section = False
        st.session_state.show_clientes_section = False
        st.session_state.show_email_section = False
        st.rerun()

with col_nav3:
    if st.button("📊 Historial"):
        st.session_state.show_db_section = not st.session_state.show_db_section
        st.session_state.current_page = 'historial'
        if st.session_state.show_db_section:
            st.session_state.show_clientes_section = False
            st.session_state.show_email_section = False

with col_nav4:
    if st.button("👥 Clientes"):
        st.session_state.show_clientes_section = not st.session_state.show_clientes_section
        st.session_state.current_page = 'clientes'
        if st.session_state.show_clientes_section:
            st.session_state.show_db_section = False
            st.session_state.show_email_section = False

with col_nav5:
    if 'confirmar_generar_informes' not in st.session_state:
        st.session_state.confirmar_generar_informes = False
    
    if not st.session_state.confirmar_generar_informes:
        # Botón inicial para generar informes
        if st.button("📄 Generar Informes"):
            # Verificar si hay reportes pendientes de generar
            conn = crear_conexion()
            if conn:
                try:
                    crear_tabla(conn)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 0")
                    reportes_pendientes = cursor.fetchone()[0]
                    cursor.close()
                    
                    if reportes_pendientes > 0:
                        st.session_state.confirmar_generar_informes = True
                        st.rerun()
                    else:
                        st.info("ℹ️ No hay reportes pendientes de generar.")
                        
                except Exception as e:
                    st.error(f"❌ Error al verificar reportes pendientes: {e}")
                finally:
                    conn.close()
    else:
        # Mostrar confirmación
        st.markdown("⚠️ **¿Confirmar generación?**")
        col_confirm1, col_confirm2 = st.columns(2)
        
        with col_confirm1:
            if st.button("✅ Sí, generar", type="primary", key="confirm_generate"):
                conn = crear_conexion()
                if conn:
                    try:
                        crear_tabla(conn)
                        
                        # Obtener número de reportes pendientes para mostrar progreso
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 0")
                        total_pendientes = cursor.fetchone()[0]
                        cursor.close()
                        
                        if total_pendientes > 0:
                            with st.spinner(f"Generando {total_pendientes} informes PDF..."):
                                watermark_path = get_config("reports.watermark_path", "imagenes/marca_agua.jpg")
                                generar_informe_pdf(conn, watermark_path)
                            
                            st.success(f"✅ {total_pendientes} informes PDF generados exitosamente.")
                            st.balloons()  # Efecto visual de celebración
                        else:
                            st.info("ℹ️ No había reportes pendientes de generar.")
                            
                    except Exception as e:
                        st.error(f"❌ Error durante la generación: {e}")
                    finally:
                        conn.close()
                
                # Reset del estado de confirmación
                st.session_state.confirmar_generar_informes = False
                st.rerun()
        
        with col_confirm2:
            if st.button("❌ Cancelar", key="cancel_generate"):
                st.session_state.confirmar_generar_informes = False
                st.info("Operación cancelada.")
                st.rerun()

with col_nav6:
    if st.button("📧 Enviar Emails"):
        st.session_state.show_email_section = not st.session_state.show_email_section
        st.session_state.current_page = 'emails'
        if st.session_state.show_email_section:
            st.session_state.show_db_section = False
            st.session_state.show_clientes_section = False

with col_nav7:
    if st.button("⚙️ Configuración"):
        st.session_state.current_page = 'settings'
        st.session_state.show_db_section = False
        st.session_state.show_clientes_section = False
        st.session_state.show_email_section = False
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ================================
# CONTENIDO PRINCIPAL
# ================================

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Mostrar página según selección
if st.session_state.current_page == 'dashboard':
    show_dashboard()

elif st.session_state.current_page == 'settings':
    show_settings_page()

elif st.session_state.current_page == 'upload':
    st.title("📤 Carga de Boletines")
    
    # Sección para subir archivo
    archivo = st.file_uploader("Subí un archivo XLSX", type=["xlsx"])

    if archivo:
        # Leer el archivo Excel
        df = pd.read_excel(archivo)
        
        # Extraer datos agrupados
        datos_agrupados = extraer_datos_agrupados(df)

        # Crear conexión y tabla
        conn = crear_conexion()
        if conn:
            try:
                crear_tabla(conn)
                
                # Insertar datos en la base de datos
                if st.button("📥 Ingresar datos a la base de datos", type="primary"):
                    with st.spinner("Insertando datos..."):
                        insertar_datos(conn, datos_agrupados)
                    st.success("✅ Datos insertados en la base de datos correctamente.")
                    st.balloons()
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                conn.close()

        # Mostrar datos agrupados en formato de planilla
        if datos_agrupados:
            st.subheader("📋 Vista previa de datos")
            for titular, registros in datos_agrupados.items():
                with st.expander(f"📁 Titular: {titular} ({len(registros)} registros)"):
                    # Convertir registros a DataFrame
                    df_registros = pd.DataFrame(registros)
                    # Añadir columna 'Titular' con el valor del titular
                    df_registros['Titular'] = titular
                    # Reordenar columnas para que 'Titular' esté al principio
                    cols = ['Titular'] + [col for col in df_registros.columns if col != 'Titular']
                    df_registros = df_registros[cols]
                    # Mostrar el DataFrame como tabla interactiva
                    st.dataframe(df_registros, use_container_width=True)
        else:
            st.warning("⚠️ No se encontraron titulares en el archivo.")

# Sección para mostrar y filtrar datos de la base de datos (boletines)
if st.session_state.show_db_section:
    st.markdown("---")
    st.header("Datos en la Base de Datos")

    # Cargar datos de la base de datos
    conn = crear_conexion()
    if conn:
        try:
            # Asegurar que las tablas existan antes de consultar
            crear_tabla(conn)
            
            # Obtener datos y actualizar estado
            rows, columns = obtener_datos(conn)
            st.session_state.db_data = pd.DataFrame(rows, columns=columns)
            
            if not st.session_state.db_data.empty:
                # Filtros
                st.subheader("Filtros")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtro_titular = st.text_input("Titular", "", key="filtro_titular_boletines").strip()
                    filtro_boletin = st.text_input("Número de Boletín", "").strip()
                    filtro_orden = st.text_input("Número de Orden", "").strip()
                with col2:
                    filtro_solicitante = st.text_input("Solicitante", "").strip()
                    filtro_agente = st.text_input("Agente", "").strip()
                    filtro_expediente = st.text_input("Número de Expediente", "").strip()
                with col3:
                    filtro_fecha = st.text_input("Fecha de Boletín (YYYY-MM-DD)", "").strip()
                    filtro_clase = st.text_input("Clase", "").strip()
                    filtro_reporte_enviado = st.checkbox("Reportes pendientes de ser Enviados")
                    filtro_reporte_generado = st.checkbox("Reportes Pendientes de Generacion")
                
                # Filtros de clientes
                col4, col5, col6 = st.columns(3)
                with col4:
                    filtro_email = st.text_input("Email", "").strip()
                with col5:
                    filtro_telefono = st.text_input("Teléfono", "").strip()
                with col6:
                    filtro_ciudad = st.text_input("Ciudad", "").strip()

                # Aplicar filtros
                filtered_df = st.session_state.db_data.copy()
                if filtro_titular:
                    filtered_df = filtered_df[filtered_df['titular'].str.contains(filtro_titular, case=False, na=False)]
                if filtro_boletin:
                    filtered_df = filtered_df[filtered_df['numero_boletin'].str.contains(filtro_boletin, case=False, na=False)]
                if filtro_orden:
                    filtered_df = filtered_df[filtered_df['numero_orden'].str.contains(filtro_orden, case=False, na=False)]
                if filtro_solicitante:
                    filtered_df = filtered_df[filtered_df['solicitante'].str.contains(filtro_solicitante, case=False, na=False)]
                if filtro_agente:
                    filtered_df = filtered_df[filtered_df['agente'].str.contains(filtro_agente, case=False, na=False)]
                if filtro_expediente:
                    filtered_df = filtered_df[filtered_df['numero_expediente'].str.contains(filtro_expediente, case=False, na=False)]
                if filtro_fecha:
                    filtered_df = filtered_df[filtered_df['fecha_boletin'].str.contains(filtro_fecha, case=False, na=False)]
                if filtro_clase:
                    filtered_df = filtered_df[filtered_df['clase'].str.contains(filtro_clase, case=False, na=False)]
                if filtro_reporte_enviado:
                    filtered_df = filtered_df[filtered_df['reporte_enviado'] == False]
                if filtro_reporte_generado:
                    filtered_df = filtered_df[filtered_df['reporte_generado'] == False]
                if filtro_email:
                    filtered_df = filtered_df[filtered_df['email'].str.contains(filtro_email, case=False, na=False)]
                if filtro_telefono:
                    filtered_df = filtered_df[filtered_df['telefono'].str.contains(filtro_telefono, case=False, na=False)]
                if filtro_ciudad:
                    filtered_df = filtered_df[filtered_df['ciudad'].str.contains(filtro_ciudad, case=False, na=False)]

                # Paginación - usar configuración
                rows_per_page = get_config("ui.items_per_page", 10)
                total_rows = len(filtered_df)
                total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
                page_options = [f"Página {i+1} de {total_pages}" for i in range(total_pages)]
                selected_page = st.selectbox("Seleccionar página", page_options, index=0, key="page_boletines")
                current_page = int(selected_page.split(" ")[1]) - 1  # Extraer número de página

                # Calcular índices para la página actual
                start_idx = current_page * rows_per_page
                end_idx = min(start_idx + rows_per_page, total_rows)
                paginated_df = filtered_df.iloc[start_idx:end_idx]

                # Mostrar resultados con selección de registros
                if not paginated_df.empty:
                    st.dataframe(paginated_df, use_container_width=True)
                    st.write(f"Mostrando registros {start_idx + 1} a {end_idx} de {total_rows}")

                    # Selección de registro
                    record_ids = paginated_df['id'].tolist()
                    selected_id = st.selectbox("Seleccionar registro para editar o eliminar", ["Ninguno"] + record_ids, index=0, key="select_boletines")
                    
                    if selected_id != "Ninguno":
                        st.session_state.selected_record_id = selected_id
                        selected_record = paginated_df[paginated_df['id'] == selected_id].iloc[0]

                        # Formulario para editar registro
                        st.subheader("Editar Registro")
                        st.write(f"Datos del Cliente: Email: {selected_record['email'] or 'N/A'}, Teléfono: {selected_record['telefono'] or 'N/A'}, Dirección: {selected_record['direccion'] or 'N/A'}, Ciudad: {selected_record['ciudad'] or 'N/A'}")
                        with st.form(key="edit_form_boletines"):
                            edit_numero_boletin = st.text_input("Número de Boletín", value=selected_record['numero_boletin'])
                            edit_fecha_boletin = st.text_input("Fecha de Boletín (YYYY-MM-DD)", value=selected_record['fecha_boletin'])
                            edit_numero_orden = st.text_input("Número de Orden", value=selected_record['numero_orden'])
                            edit_solicitante = st.text_input("Solicitante", value=selected_record['solicitante'])
                            edit_agente = st.text_input("Agente", value=selected_record['agente'])
                            edit_numero_expediente = st.text_input("Número de Expediente", value=selected_record['numero_expediente'])
                            edit_clase = st.text_input("Clase", value=selected_record['clase'])
                            edit_marca_custodia = st.text_input("Marca Custodia", value=selected_record['marca_custodia'])
                            edit_marca_publicada = st.text_input("Marca Publicada", value=selected_record['marca_publicada'])
                            edit_clases_acta = st.text_input("Clases Acta", value=selected_record['clases_acta'])
                            edit_reporte_enviado = st.checkbox("Reporte Enviado", value=selected_record['reporte_enviado'])
                            edit_reporte_generado = st.checkbox("Reporte Generado", value=selected_record['reporte_generado'])
                            edit_titular = st.text_input("Titular", value=selected_record['titular'])

                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                submit_button = st.form_submit_button("Actualizar Registro")
                            with col_btn2:
                                delete_button = st.form_submit_button("Eliminar Registro")

                            if submit_button:
                                # Almacenar acción pendiente
                                st.session_state.pending_action = "update_boletines"
                                st.session_state.pending_data = {
                                    "id": selected_id,
                                    "numero_boletin": edit_numero_boletin,
                                    "fecha_boletin": edit_fecha_boletin,
                                    "numero_orden": edit_numero_orden,
                                    "solicitante": edit_solicitante,
                                    "agente": edit_agente,
                                    "numero_expediente": edit_numero_expediente,
                                    "clase": edit_clase,
                                    "marca_custodia": edit_marca_custodia,
                                    "marca_publicada": edit_marca_publicada,
                                    "clases_acta": edit_clases_acta,
                                    "reporte_enviado": edit_reporte_enviado,
                                    "reporte_generado": edit_reporte_generado,
                                    "titular": edit_titular
                                }

                            if delete_button:
                                # Almacenar acción pendiente
                                st.session_state.pending_action = "delete_boletines"
                                st.session_state.pending_data = {"id": selected_id}

                else:
                    st.warning("No se encontraron registros que coincidan con los filtros.")
            else:
                    st.warning("La base de datos está vacía.")
                

            # Manejar acción pendiente para boletines
            if st.session_state.pending_action:
                if st.session_state.pending_action == "update_boletines":
                    st.warning("¿Estás seguro de que deseas actualizar este registro?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("Confirmar Actualización", key="confirm_update_boletines"):
                            try:
                                data = st.session_state.pending_data
                                actualizar_registro(
                                    conn, data["id"], data["numero_boletin"], data["fecha_boletin"],
                                    data["numero_orden"], data["solicitante"], data["agente"],
                                    data["numero_expediente"], data["clase"], data["marca_custodia"],
                                    data["marca_publicada"], data["clases_acta"], data["reporte_enviado"],
                                    data["titular"],data["reporte_generado"]
                                )
                                # Refrescar datos
                                rows, columns = obtener_datos(conn)
                                st.session_state.db_data = pd.DataFrame(rows, columns=columns)
                                st.success("Registro actualizado correctamente.")
                                st.session_state.selected_record_id = None
                                st.session_state.pending_action = None
                                st.session_state.pending_data = None
                                st.rerun()  # Forzar re-renderizado
                            except Exception as e:
                                st.error(f"Error al actualizar: {e}")

                    with col_confirm2:
                        if st.button("Cancelar Actualización", key="cancel_update_boletines"):
                            st.session_state.pending_action = None
                            st.session_state.pending_data = None
                            st.rerun()

                elif st.session_state.pending_action == "delete_boletines":
                    st.warning("¿Estás seguro de que deseas eliminar este registro?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("Confirmar Eliminación", key="confirm_delete_boletines"):
                            try:
                                eliminar_registro(conn, st.session_state.pending_data["id"])
                                # Refrescar datos
                                rows, columns = obtener_datos(conn)
                                st.session_state.db_data = pd.DataFrame(rows, columns=columns)
                                st.success("Registro eliminado correctamente.")
                                st.session_state.selected_record_id = None
                                st.session_state.pending_action = None
                                st.session_state.pending_data = None
                                st.rerun()  # Forzar re-renderizado
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")

                    with col_confirm2:
                        if st.button("Cancelar Eliminación", key="cancel_delete_boletines"):
                            st.session_state.pending_action = None
                            st.session_state.pending_data = None
                            st.rerun()

        except Exception as e:
            st.error(f"Error al consultar la base de datos: {e}")
        finally:
            conn.close()

# Sección para gestionar clientes
if st.session_state.show_clientes_section:
    st.markdown("---")
    st.header("Gestión de Clientes")

    # Cargar datos de clientes
    conn = crear_conexion()
    if conn:
        try:
            # Asegurar que las tablas existan
            crear_tabla(conn)
            # st.write("Tablas 'boletines' y 'clientes' verificadas/creadas.")
            # Obtener datos de clientes
            rows, columns = obtener_clientes(conn)
            st.session_state.clientes_data = pd.DataFrame(rows, columns=columns)
            
            if not st.session_state.clientes_data.empty:
                # Filtros
                st.subheader("Filtros")
                col1, col2, col3 = st.columns(3)
                with col1:
                    filtro_titular = st.text_input("Titular", "", key="filtro_titular_clientes").strip()
                with col2:
                    filtro_email = st.text_input("Email", "").strip()
                with col3:
                    filtro_ciudad = st.text_input("Ciudad", "").strip()

                # Aplicar filtros
                filtered_df = st.session_state.clientes_data.copy()
                if filtro_titular:
                    filtered_df = filtered_df[filtered_df['titular'].str.contains(filtro_titular, case=False, na=False)]
                if filtro_email:
                    filtered_df = filtered_df[filtered_df['email'].str.contains(filtro_email, case=False, na=False)]
                if filtro_ciudad:
                    filtered_df = filtered_df[filtered_df['ciudad'].str.contains(filtro_ciudad, case=False, na=False)]

                # Paginación
                rows_per_page = 10
                total_rows = len(filtered_df)
                total_pages = math.ceil(total_rows / rows_per_page) if total_rows > 0 else 1
                page_options = [f"Página {i+1} de {total_pages}" for i in range(total_pages)]
                selected_page = st.selectbox("Seleccionar página", page_options, index=0, key="page_clientes")
                current_page = int(selected_page.split(" ")[1]) - 1

                # Calcular índices para la página actual
                start_idx = current_page * rows_per_page
                end_idx = min(start_idx + rows_per_page, total_rows)
                paginated_df = filtered_df.iloc[start_idx:end_idx]

                # Mostrar resultados
                if not paginated_df.empty:
                    st.dataframe(paginated_df, use_container_width=True)
                    st.write(f"Mostrando registros {start_idx + 1} a {end_idx} de {total_rows}")

                    # Selección de registro
                    cliente_ids = paginated_df['id'].tolist()
                    selected_id = st.selectbox("Seleccionar cliente para editar o eliminar", ["Ninguno"] + cliente_ids, index=0, key="select_clientes")
                    
                    if selected_id != "Ninguno":
                        st.session_state.selected_cliente_id = selected_id
                        selected_cliente = paginated_df[paginated_df['id'] == selected_id].iloc[0]

                        # Formulario para editar cliente
                        st.subheader("Editar Cliente")
                        with st.form(key="edit_form_clientes"):
                            edit_titular = st.text_input("Titular", value=selected_cliente['titular'])
                            edit_email = st.text_input("Email", value=selected_cliente['email'] or '')
                            edit_telefono = st.text_input("Teléfono", value=selected_cliente['telefono'] or '')
                            edit_direccion = st.text_input("Dirección", value=selected_cliente['direccion'] or '')
                            edit_ciudad = st.text_input("Ciudad", value=selected_cliente['ciudad'] or '')

                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                submit_button = st.form_submit_button("Actualizar Cliente")
                            with col_btn2:
                                delete_button = st.form_submit_button("Eliminar Cliente")

                            if submit_button:
                                st.session_state.pending_action = "update_clientes"
                                st.session_state.pending_data = {
                                    "id": selected_id,
                                    "titular": edit_titular,
                                    "email": edit_email,
                                    "telefono": edit_telefono,
                                    "direccion": edit_direccion,
                                    "ciudad": edit_ciudad
                                }

                            if delete_button:
                                st.session_state.pending_action = "delete_clientes"
                                st.session_state.pending_data = {"id": selected_id}

                else:
                    st.warning("No se encontraron clientes que coincidan con los filtros.")
            else:
                st.warning("No hay clientes registrados.")

            # Formulario para agregar nuevo cliente
            st.subheader("Agregar Nuevo Cliente")
            with st.form(key="add_form_clientes"):
                new_titular = st.text_input("Titular", key="new_titular")
                new_email = st.text_input("Email", key="new_email")
                new_telefono = st.text_input("Teléfono", key="new_telefono")
                new_direccion = st.text_input("Dirección", key="new_direccion")
                new_ciudad = st.text_input("Ciudad", key="new_ciudad")
                add_button = st.form_submit_button("Agregar Cliente")

                if add_button:
                    if new_titular:
                        try:
                            insertar_cliente(conn, new_titular, new_email, new_telefono, new_direccion, new_ciudad)
                            # Refrescar datos
                            rows, columns = obtener_clientes(conn)
                            st.session_state.clientes_data = pd.DataFrame(rows, columns=columns)
                            st.success(f"Cliente '{new_titular}' agregado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al agregar cliente: {e}")
                    else:
                        st.error("El campo 'Titular' es obligatorio.")

            # Manejar acción pendiente para clientes
            if st.session_state.pending_action:
                if st.session_state.pending_action == "update_clientes":
                    st.warning("¿Estás seguro de que deseas actualizar este cliente?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("Confirmar Actualización", key="confirm_update_clientes"):
                            try:
                                data = st.session_state.pending_data
                                actualizar_cliente(
                                    conn, data["id"], data["titular"], data["email"],
                                    data["telefono"], data["direccion"], data["ciudad"]
                                )
                                # Refrescar datos
                                rows, columns = obtener_clientes(conn)
                                st.session_state.clientes_data = pd.DataFrame(rows, columns=columns)
                                st.success("Cliente actualizado correctamente.")
                                st.session_state.selected_cliente_id = None
                                st.session_state.pending_action = None
                                st.session_state.pending_data = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar cliente: {e}")

                    with col_confirm2:
                        if st.button("Cancelar Actualización", key="cancel_update_clientes"):
                            st.session_state.pending_action = None
                            st.session_state.pending_data = None
                            st.rerun()

                elif st.session_state.pending_action == "delete_clientes":
                    st.warning("¿Estás seguro de que deseas eliminar este cliente?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("Confirmar Eliminación", key="confirm_delete_clientes"):
                            try:
                                eliminar_cliente(conn, st.session_state.pending_data["id"])
                                # Refrescar datos
                                rows, columns = obtener_clientes(conn)
                                st.session_state.clientes_data = pd.DataFrame(rows, columns=columns)
                                st.success("Cliente eliminado correctamente.")
                                st.session_state.selected_cliente_id = None
                                st.session_state.pending_action = None
                                st.session_state.pending_data = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar cliente: {e}")

                    with col_confirm2:
                        if st.button("Cancelar Eliminación", key="cancel_delete_clientes"):
                            st.session_state.pending_action = None
                            st.session_state.pending_data = None
                            st.rerun()

        except Exception as e:
            st.error(f"Error al consultar clientes: {e}")
        finally:
            conn.close()


# Sección para envío de emails
if st.session_state.show_email_section:
    st.markdown("---")
    st.header("Envío de Reportes por Email")

    # Usar configuración para email
    smtp_server = get_config("email.smtp_server", "smtp.gmail.com")
    smtp_port = get_config("email.smtp_port", 587)
    batch_size = get_config("email.batch_size", 10)
    
    st.info(f"Configuración de email: {smtp_server}:{smtp_port} (Lote: {batch_size})")
    # Configurar credenciales de email
    st.subheader("Configuración de Email")
    
    col1, col2 = st.columns(2)
    with col1:
        email_usuario = st.text_input(
            "Email de Gmail:", 
            value=st.session_state.email_credentials['email'],
            placeholder="martingiacosa@gmail.com"
        )
    with col2:
        password_usuario = st.text_input(
            "App Password de Gmail:", 
            value=st.session_state.email_credentials['password'],
            type="password",
            placeholder="djry dhjb dcmi oeue"
        )
    
    # Guardar credenciales en sesión
    st.session_state.email_credentials['email'] = "martingiacosa@gmail.com"
    st.session_state.email_credentials['password'] = "djry dhjb dcmi oeue"
    
   
    
    # Verificar que las credenciales estén completas
    if email_usuario and password_usuario:
        # Mostrar resumen de reportes pendientes
        conn = crear_conexion()
        if conn:
            try:
                from email_sender import obtener_registros_pendientes_envio
                
                registros_pendientes = obtener_registros_pendientes_envio(conn)
                
                if registros_pendientes:
                    st.subheader("Reportes Pendientes de Envío")
                    
                    # Crear tabla resumen
                    resumen_data = []
                    for titular, datos in registros_pendientes.items():
                        resumen_data.append({
                            'Titular': titular,
                            'Email': datos['email'] or 'SIN EMAIL',
                            'Cantidad Boletines': len(datos['boletines']),
                            'Estado Email': '✅ Listo' if datos['email'] else '❌ Sin email'
                        })
                    
                    df_resumen = pd.DataFrame(resumen_data)
                    st.dataframe(df_resumen, use_container_width=True)
                    
                    # Estadísticas
                    total_clientes = len(registros_pendientes)
                    clientes_con_email = sum(1 for datos in registros_pendientes.values() if datos['email'])
                    clientes_sin_email = total_clientes - clientes_con_email
                    total_boletines = sum(len(datos['boletines']) for datos in registros_pendientes.values())
                    
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    with col_stat1:
                        st.metric("Total Clientes", total_clientes)
                    with col_stat2:
                        st.metric("Con Email", clientes_con_email)
                    with col_stat3:
                        st.metric("Sin Email", clientes_sin_email)
                    with col_stat4:
                        st.metric("Total Boletines", total_boletines)
                    
                    # Botón para enviar emails con confirmación
                    st.markdown("---")
                    
                    if clientes_con_email > 0:
                        if 'confirmar_envio' not in st.session_state:
                            st.session_state.confirmar_envio = False
                        
                        if not st.session_state.confirmar_envio:
                            st.warning(f"⚠️ Se enviarán emails a {clientes_con_email} clientes con {sum(len(datos['boletines']) for titular, datos in registros_pendientes.items() if datos['email'])} boletines en total.")
                            
                            col_confirm1, col_confirm2 = st.columns(2)
                            with col_confirm1:
                                if st.button("✅ Sí, enviar emails", type="primary"):
                                    st.session_state.confirmar_envio = True
                                    st.rerun()
                            with col_confirm2:
                                if st.button("❌ Cancelar"):
                                    st.info("Operación cancelada.")
                        
                        else:
                            # Confirmar nuevamente
                            st.error("🚨 **CONFIRMACIÓN FINAL**: ¿Está seguro que desea enviar los emails? Esta acción no se puede deshacer.")
                            
                            col_final1, col_final2 = st.columns(2)
                            with col_final1:
                                if st.button("🚀 ENVIAR AHORA", type="primary"):
                                    # Procesar envío
                                    with st.spinner("Enviando emails..."):
                                        try:
                                            resultados = procesar_envio_emails(
                                                conn, 
                                                email_usuario, 
                                                password_usuario
                                            )
                                            
                                            # Mostrar resultados
                                            if resultados['exitosos']:
                                                st.success(f"✅ Se enviaron {len(resultados['exitosos'])} emails exitosamente.")
                                                
                                                # Mostrar detalles de envíos exitosos
                                                with st.expander("Ver detalles de envíos exitosos"):
                                                    for envio in resultados['exitosos']:
                                                        st.write(f"• {envio['titular']} ({envio['email']}) - {envio['cantidad_boletines']} boletines")
                                            
                                            if resultados['fallidos']:
                                                st.error(f"❌ {len(resultados['fallidos'])} envíos fallaron.")
                                                with st.expander("Ver errores"):
                                                    for fallo in resultados['fallidos']:
                                                        st.write(f"• {fallo['titular']} ({fallo['email']}): {fallo['error']}")
                                            
                                            if resultados['sin_email']:
                                                st.warning(f"⚠️ {len(resultados['sin_email'])} clientes sin email.")
                                                with st.expander("Ver clientes sin email"):
                                                    for cliente in resultados['sin_email']:
                                                        st.write(f"• {cliente}")
                                            
                                            if resultados['sin_archivo']:
                                                st.warning(f"⚠️ {len(resultados['sin_archivo'])} clientes sin archivo de reporte.")
                                                with st.expander("Ver clientes sin archivo"):
                                                    for cliente in resultados['sin_archivo']:
                                                        st.write(f"• {cliente}")
                                            
                                            # Generar reporte completo
                                            reporte_completo = generar_reporte_envios(resultados)
                                            with st.expander("📋 Ver reporte completo"):
                                                st.text(reporte_completo)
                                            
                                            # Reset confirmación
                                            st.session_state.confirmar_envio = False
                                            
                                        except Exception as e:
                                            st.error(f"Error durante el envío: {e}")
                                            st.session_state.confirmar_envio = False
                            
                            with col_final2:
                                if st.button("❌ Cancelar"):
                                    st.session_state.confirmar_envio = False
                                    st.info("Operación cancelada.")
                                    st.rerun()
                    else:
                        st.warning("No hay clientes con email válido para enviar reportes.")
                        
                else:
                    st.info("No hay reportes pendientes de envío.")
                    st.write("Los reportes deben tener:")
                    st.write("- `reporte_generado = True`")
                    st.write("- `reporte_enviado = False`")
                
            except Exception as e:
                st.error(f"Error al consultar reportes pendientes: {e}")
            finally:
                conn.close()
    else:
        st.warning("⚠️ Por favor, ingresa las credenciales de Gmail para continuar.")
        st.info("Necesitas un email de Gmail y un App Password para enviar los reportes.")


st.markdown('</div>', unsafe_allow_html=True)