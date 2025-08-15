# app.py - Versión integrada con dashboard y configuración con autenticación

import streamlit as st

# MOVER st.set_page_config AL INICIO - ANTES DE CUALQUIER OTRO COMANDO DE STREAMLIT
st.set_page_config(
    page_title="Sistema de Gestión de Marcas - Estudio Contable",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
from datetime import datetime, timedelta
import math
import time
import base64
import json
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from streamlit_option_menu import option_menu

# Importar componentes profesionales
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.stateful_button import button
from streamlit_extras.grid import grid
import streamlit_shadcn_ui as ui
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import extra_streamlit_components as stx

# Importar el tema profesional
from professional_theme import apply_professional_theme, create_professional_card, create_metric_card, create_status_badge
from dashboard_charts import create_status_donut_chart, create_urgency_gauge_chart, create_timeline_chart, create_compliance_bar_chart

# Aplicar tema profesional
apply_professional_theme()

# Importar configuración
from config import get_config, set_config, show_settings_page, load_email_credentials, save_email_credentials, validate_email_format

# Importar módulos existentes
from database import crear_conexion, crear_tabla, insertar_datos, obtener_datos, actualizar_registro, eliminar_registro, insertar_cliente, obtener_clientes, actualizar_cliente, eliminar_cliente, obtener_logs_envios, obtener_estadisticas_logs, limpiar_logs_antiguos, obtener_emails_enviados, obtener_ruta_reporte_pdf, optimizar_archivo_log, limpieza_automatica_logs, configurar_limpieza_logs
from extractor import extraer_datos_agrupados
from report_generator import generar_informe_pdf
from email_sender import procesar_envio_emails, generar_reporte_envios, obtener_info_reportes_pendientes, obtener_estadisticas_envios, validar_email, validar_clientes_para_envio

# Importar sistema de autenticación simplificado
from auth_manager_simple import handle_authentication, check_authentication, AuthManager

try:
    from streamlit_on_Hover_tabs import on_hover_tabs
    HOVER_TABS_AVAILABLE = True
except ImportError:
    HOVER_TABS_AVAILABLE = False
    # Comentar esta línea por ahora para evitar el warning:
    # st.warning("⚠️ streamlit-on-Hover-tabs no está instalado. Instalalo con: pip install streamlit-on-Hover-tabs")

# ================================
# FUNCIONES PARA GESTIÓN DE CREDENCIALES DE EMAIL
# ================================

def cargar_credenciales_email():
    """
    Carga las credenciales de email desde credenciales.json
    """
    return load_email_credentials()

def guardar_credenciales_email(email, password):
    """
    Guarda las credenciales de email en credenciales.json
    """
    return save_email_credentials(email, password)

def obtener_credenciales_email():
    """
    Obtiene las credenciales de email desde session_state o las carga desde archivo
    """
    # Si no están en session_state, cargarlas desde archivo
    if 'email_credentials' not in st.session_state:
        st.session_state.email_credentials = cargar_credenciales_email()
    
    return st.session_state.email_credentials

def verificar_integridad_datos(df_original, df_grid):
    """
    Función para verificar la integridad entre los datos originales y del grid
    """
    try:
        if len(df_original) != len(df_grid):
            return False, f"Diferencia en número de filas: original={len(df_original)}, grid={len(df_grid)}"
        
        # Verificar que todos los IDs coincidan
        ids_original = set(df_original['id'].astype(str))
        ids_grid = set(df_grid['id'].astype(str))
        
        if ids_original != ids_grid:
            return False, f"IDs no coinciden. Faltantes: {ids_original - ids_grid}, Extras: {ids_grid - ids_original}"
        
        return True, "Datos íntegros"
    except Exception as e:
        return False, f"Error en verificación: {e}"

def show_grid_data(df, key, selection_mode='single'):
    """
    Función helper para mostrar datos usando ag-Grid
    
    Args:
        df: DataFrame de pandas a mostrar
        key: Identificador único para el grid
        selection_mode: Modo de selección ('single' o 'multiple')
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurar opciones del grid
    gb.configure_pagination(
        enabled=True,
        paginationAutoPageSize=False,
        paginationPageSize=10
    )
    gb.configure_selection(selection_mode=selection_mode, use_checkbox=True)
    
    # Configurar todas las columnas como no editables por defecto
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        editable=False,
        sorteable=True,
        filterable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
        minWidth=100  # Ancho mínimo para todas las columnas
    )
    
    # Configurar anchos específicos para cada columna
    gb.configure_column('numero_boletin', width=120, header_name="N° Boletín")
    gb.configure_column('fecha_boletin', width=120, header_name="Fecha")
    gb.configure_column('numero_orden', width=120, header_name="N° Orden")
    gb.configure_column('solicitante', width=200)
    gb.configure_column('agente', width=200)
    gb.configure_column('numero_expediente', width=150, header_name="N° Expediente")
    gb.configure_column('clase', width=100)
    gb.configure_column('marca_custodia', width=200, header_name="Marca Custodia")
    gb.configure_column('marca_publicada', width=200, header_name="Marca Publicada")
    gb.configure_column('clases_acta', width=120, header_name="Clases")
    gb.configure_column('titular', width=300, wrapText=True, autoHeight=True)
    gb.configure_column('reporte_enviado', width=120, header_name="Enviado")
    gb.configure_column('reporte_generado', width=120, header_name="Generado")
    
    # Configurar específicamente la columna 'importancia'
    gb.configure_column(
        'importancia',
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={
            'values': ['Baja', 'Media', 'Alta', 'Pendiente']
        },
        width=120,
        cellStyle={'cursor': 'pointer'},
        header_name="Importancia"
    )
    
    grid_options = gb.build()
    
    # Mostrar el grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
        theme='streamlit',
        key=key,
        allow_unsafe_jscode=True,
        height=400
    )

    # Manejar cambios en la importancia - VERSIÓN MEJORADA
    if grid_response['data'] is not None and len(grid_response['data']) > 0:
        df_new = pd.DataFrame(grid_response['data'])
        
        # Verificar si hay cambios reales comparando con el DataFrame original
        for index, row in df_new.iterrows():
            try:
                # Buscar la fila original por ID
                original_row = df[df['id'] == row['id']]
                
                if not original_row.empty:
                    original_row = original_row.iloc[0]
                    
                    # Verificar si la importancia cambió
                    if str(row['importancia']) != str(original_row['importancia']):
                        # Crear identificador único basado en timestamp para evitar duplicados
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        cambio_id = f"cambio_{row['id']}_{current_time}"
                        
                        # Usar session_state para evitar procesamiento múltiple solo por un breve periodo
                        if 'cambios_recientes' not in st.session_state:
                            st.session_state.cambios_recientes = {}
                        
                        # Limpiar cambios antiguos (más de 5 segundos)
                        now = datetime.now()
                        st.session_state.cambios_recientes = {
                            k: v for k, v in st.session_state.cambios_recientes.items() 
                            if (now - v).total_seconds() < 5
                        }
                        
                        # Verificar si este registro fue modificado recientemente
                        registro_modificado_recientemente = any(
                            k.startswith(f"cambio_{row['id']}_") 
                            for k in st.session_state.cambios_recientes.keys()
                        )
                        
                        if not registro_modificado_recientemente:
                            # Marcar como procesado
                            st.session_state.cambios_recientes[cambio_id] = now
                            
                            # Actualizar base de datos
                            conn = crear_conexion()
                            if conn:
                                try:
                                    actualizar_registro(
                                        conn,
                                        int(row['id']),
                                        row['numero_boletin'],
                                        row['fecha_boletin'],
                                        row['numero_orden'],
                                        row['solicitante'],
                                        row['agente'],
                                        row['numero_expediente'],
                                        row['clase'],
                                        row['marca_custodia'],
                                        row['marca_publicada'],
                                        row['clases_acta'],
                                        bool(row['reporte_enviado']),
                                        row['titular'],
                                        bool(row['reporte_generado']),
                                        row['importancia']
                                    )
                                    
                                    # Verificar que el cambio se guardó correctamente
                                    cursor = conn.cursor()
                                    cursor.execute("SELECT importancia FROM boletines WHERE id = ?", (int(row['id']),))
                                    result = cursor.fetchone()
                                    cursor.close()
                                    
                                    if result and result[0] == row['importancia']:
                                        # Mostrar mensaje de éxito
                                        st.success(f"✅ Importancia actualizada a '{row['importancia']}' para registro ID {row['id']}")
                                        
                                        # Actualizar los datos en session_state para reflejar el cambio
                                        if 'db_data' in st.session_state:
                                            mask = st.session_state.db_data['id'] == row['id']
                                            if mask.any():
                                                st.session_state.db_data.loc[mask, 'importancia'] = row['importancia']
                                        
                                        # Recargar página después de un breve delay
                                        time.sleep(1.5)
                                        st.rerun()
                                    else:
                                        importancia_guardada = result[0] if result else "No encontrado"
                                        st.error(f"❌ Error: El cambio no se guardó correctamente. Esperado: '{row['importancia']}', Guardado: '{importancia_guardada}'")
                                        # Limpiar cache del cambio fallido
                                        if cambio_id in st.session_state.cambios_recientes:
                                            del st.session_state.cambios_recientes[cambio_id]
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar registro ID {row['id']}: {e}")
                                    # Remover de procesados si hubo error
                                    if cambio_id in st.session_state.cambios_recientes:
                                        del st.session_state.cambios_recientes[cambio_id]
                                finally:
                                    conn.close()
                            
                            # Solo procesar un cambio a la vez
                            break
                            
            except Exception as e:
                st.error(f"❌ Error al procesar cambio en registro: {e}")
                continue

    return grid_response

# Corregir la función show_grid_data_clientes para que sea más responsive

def show_grid_data_clientes(df, key, selection_mode='single'):
    """
    Función helper para mostrar datos de clientes usando ag-Grid - Versión EDITABLE
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurar opciones del grid
    gb.configure_pagination(
        enabled=True,
        paginationAutoPageSize=False,
        paginationPageSize=20
    )
    gb.configure_selection(selection_mode=selection_mode, use_checkbox=True)
    
    # Configurar todas las columnas como EDITABLES por defecto
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        editable=True,  # CAMBIAR A TRUE para edición
        sorteable=True,
        filterable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
        minWidth=100,
        flex=1,
        singleClickEdit=True  # Edición con un solo clic
    )
    
    # Configurar anchos específicos y editabilidad por columna
    gb.configure_column('id', hide=True)  # Ocultar ID - NO EDITABLE
    gb.configure_column('titular', width=200, header_name="👤 Titular", pinned='left', flex=2, editable=True)
    gb.configure_column('email', width=180, header_name="📧 Email", flex=2, editable=True)
    gb.configure_column('telefono', width=130, header_name="📞 Teléfono", flex=1, editable=True)
    gb.configure_column('direccion', width=250, header_name="📍 Dirección", wrapText=True, flex=3, editable=True)
    gb.configure_column('ciudad', width=120, header_name="🏙️ Ciudad", flex=1, editable=True)
    gb.configure_column('cuit', width=130, header_name="🆔 CUIT", flex=1, editable=True)
    
    # Configurar opciones adicionales para edición
    gb.configure_grid_options(
        enableRangeSelection=True,
        stopEditingWhenCellsLoseFocus=True,
        suppressClickEdit=False
    )
    
    grid_options = gb.build()
    
    # Mostrar el grid con modo de actualización para capturar cambios
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,  # CAMBIAR PARA CAPTURAR EDICIONES
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        key=key,
        allow_unsafe_jscode=True,
        height=600,
        width='100%',
        reload_data=False  # Importante para mantener ediciones
    )

    return grid_response

# CSS personalizado mejorado - TEMA OSCURO
st.markdown(f"""
<style>
    /* Tema oscuro profesional */
    .stApp {{
        background-color: #0f0f0f;
        color: #e5e5e5;
    }}
    
    .main {{
        padding-top: 2rem;
        background-color: #0f0f0f;
    }}
    
    /* Background para toda la aplicación */
    .stApp > div {{
        background-color: #0f0f0f;
    }}
    
    /* Header principal */
    .main-header {{
        background: linear-gradient(90deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: #e5e5e5;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #333;
    }}
    
    /* Cards de estadísticas - tema oscuro */
    .metric-card {{
        background: #1a1a1a;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border-left: 4px solid #667eea;
        border: 1px solid #333;
        margin: 1rem 0;
        color: #e5e5e5;
    }}
    
    /* Botones mejorados */
    .stButton > button {{
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
    }}
    
    /* Sidebar oscuro */
    .css-1d391kg {{
        background-color: #1a1a1a;
    }}
    
    /* Elementos de texto */
    .stMarkdown {{
        color: #e5e5e5;
    }}
    
    /* Inputs y selectbox */
    .stSelectbox > div > div {{
        background-color: #2d2d2d;
        color: #e5e5e5;
        border: 1px solid #444;
    }}
    
    .stTextInput > div > div > input {{
        background-color: #2d2d2d;
        color: #e5e5e5;
        border: 1px solid #444;
    }}
    
    .stFileUploader > div {{
        background-color: #2d2d2d;
        border: 2px dashed #667eea;
        border-radius: 10px;
    }}
    
    /* Estilos para ag-Grid - tema oscuro */
    .ag-theme-streamlit {{
        --ag-background-color: #1a1a1a;
        --ag-foreground-color: #e5e5e5;
        --ag-header-background-color: #2d2d2d;
        --ag-header-foreground-color: #e5e5e5;
        --ag-header-cell-hover-background-color: #3d3d3d;
        --ag-row-hover-color: #2d2d2d;
        --ag-selected-row-background-color: rgba(102, 126, 234, 0.2);
        --ag-border-color: #444;
        --ag-font-family: inherit;
        --ag-font-size: 14px;
    }}
    
    .ag-theme-streamlit .ag-header-cell {{
        font-weight: 600;
        border-bottom: 1px solid #444;
    }}
    
    .ag-theme-streamlit .ag-cell {{
        padding: 8px;
        border-bottom: 1px solid #333;
    }}
    
    .ag-theme-streamlit .ag-row {{
        background-color: #1a1a1a;
    }}
    
    .ag-theme-streamlit .ag-row:hover {{
        background-color: #2d2d2d;
    }}
    
    /* Estilos para la sección de emails - tema oscuro */
    .email-section {{
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #444;
    }}
    
    .email-config-card {{
        background: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin: 10px 0;
        border: 1px solid #444;
        color: #e5e5e5;
    }}
    
    /* Estilos para botones de gestión de emails */
    .email-management-container {{
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border: 1px solid #4a4a5a;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    
    .email-management-title {{
        color: #e5e5e5;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 20px;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Botones primarios de email con estilo avanzado */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        text-transform: none;
        font-size: 0.95rem;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }}
    
    .stButton > button[kind="primary"]:active {{
        transform: translateY(0px);
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }}
    
    /* Botones secundarios de email */
    .stButton > button:not([kind="primary"]) {{
        background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%);
        color: #e5e5e5;
        border: 1px solid #5a5a6a;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }}
    
    .stButton > button:not([kind="primary"]):hover {{
        background: linear-gradient(135deg, #3d3d4d 0%, #4d4d5d 100%);
        border-color: #667eea;
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }}
    
    /* Botones de confirmación específicos */
    .email-confirm-button {{
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }}
    
    .email-cancel-button {{
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
    }}
    
    /* Pestañas de email con colores específicos - Mayor especificidad */
    .email-management-container .stTabs [data-baseweb="tab-list"] {{
        background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid #4a4a5a !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"] {{
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
        color: #b5b5c3 !important;
        border: 1px solid #3a3a4a !important;
        border-radius: 8px !important;
        margin: 0 3px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        font-size: 0.9rem !important;
        text-transform: none !important;
        min-height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"]:hover {{
        background: linear-gradient(135deg, #3d3d4d 0%, #4d4d5d 100%) !important;
        color: #667eea !important;
        border-color: #667eea !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #5a6fd8 !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-2px) !important;
        font-weight: 700 !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"][aria-selected="true"]:hover {{
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
    }}
    
    /* Estilos adicionales para pestañas específicas por emoji */
    .email-management-container .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {{
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        box-shadow: 0 4px 20px rgba(40, 167, 69, 0.4) !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {{
        background: linear-gradient(135deg, #fd7e14 0%, #e83e8c 100%) !important;
        box-shadow: 0 4px 20px rgba(253, 126, 20, 0.4) !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"]:nth-child(4)[aria-selected="true"] {{
        background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%) !important;
        box-shadow: 0 4px 20px rgba(111, 66, 193, 0.4) !important;
    }}
    
    .email-management-container .stTabs [data-baseweb="tab"]:nth-child(5)[aria-selected="true"] {{
        background: linear-gradient(135deg, #20c997 0%, #fd7e14 100%) !important;
        box-shadow: 0 4px 20px rgba(32, 201, 151, 0.4) !important;
    }}
    
    /* Métricas de Streamlit */
    .metric-container {{
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: #2d2d2d;
        color: #e5e5e5;
        border: 1px solid #444;
    }}
    
    .streamlit-expanderContent {{
        background-color: #1a1a1a;
        border: 1px solid #444;
        border-top: none;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: #2d2d2d;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #444;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #667eea;
        color: white;
    }}
    
    /* Alertas personalizadas */
    .stAlert {{
        background-color: #2d2d2d;
        border: 1px solid #444;
        color: #e5e5e5;
    }}
    
    /* Status indicators */
    .status-indicator {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }}
    
    .status-ready {{
        background-color: #10b981;
    }}
    
    .status-warning {{
        background-color: #f59e0b;
    }}
    
    .status-error {{
        background-color: #ef4444;
    }}
    
    /* Plotly charts - fondo oscuro */
    .js-plotly-plot {{
        background-color: #1a1a1a !important;
    }}
    
    /* Headers y títulos */
    h1, h2, h3, h4, h5, h6 {{
        color: #e5e5e5 !important;
    }}
    
    /* Option menu styling para tema oscuro */
    .nav-link {{
        background-color: #2d2d2d !important;
        color: #e5e5e5 !important;
        border: 1px solid #444 !important;
    }}
    
    .nav-link-selected {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
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
    
    # NUEVO: Reportes próximos a vencer (últimos 7 días de plazo legal)
    # Los reportes vencen a los 30 días desde fecha_boletin
    # Alertar cuando quedan 7 días o menos (a partir del día 23)
    # Manejar formato de fecha DD/MM/YYYY
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
    
    # Detalles de reportes próximos a vencer para mostrar información adicional
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

def show_dashboard():
    """Dashboard profesional mejorado para estudio contable"""
    
    # Header principal profesional
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Panel de Control </h1>
        <p></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos
    conn = crear_conexion()
    if not conn:
        st.error("No se pudo conectar a la base de datos")
        return
    
    try:
        crear_tabla(conn)
        data = get_dashboard_data(conn)
        
        # Grid de métricas principales con cards profesionales
        metric_grid = grid(5, vertical_align="center")
        
        # Métricas con cards estilizadas
        with metric_grid.container():
            st.markdown(create_metric_card(
                data['total_boletines'], 
                "📋 Total Boletines", 
                "#667eea"
            ), unsafe_allow_html=True)
        
        with metric_grid.container():
            percentage = (data['reportes_generados']/max(data['total_boletines'], 1)*100) if data['total_boletines'] > 0 else 0
            st.markdown(create_metric_card(
                f"{data['reportes_generados']}", 
                f"📄 Reportes Generados ({percentage:.1f}%)", 
                "#28a745"
            ), unsafe_allow_html=True)
        
        with metric_grid.container():
            percentage = (data['reportes_enviados']/max(data['reportes_generados'], 1)*100) if data['reportes_generados'] > 0 else 0
            st.markdown(create_metric_card(
                f"{data['reportes_enviados']}", 
                f"📧 Reportes Enviados ({percentage:.1f}%)", 
                "#17a2b8"
            ), unsafe_allow_html=True)
        
        with metric_grid.container():
            color = "#dc3545" if data['proximos_vencer'] > 0 else "#28a745"
            st.markdown(create_metric_card(
                data['proximos_vencer'], 
                "⏰ Próximos a Vencer", 
                color
            ), unsafe_allow_html=True)
        
        with metric_grid.container():
            color = "#dc3545" if data['reportes_vencidos'] > 0 else "#28a745"
            st.markdown(create_metric_card(
                data['reportes_vencidos'], 
                "🚨 Vencidos", 
                color
            ), unsafe_allow_html=True)
        
        # Alertas profesionales con cards
        colored_header(
            label="🔔 Alertas del Sistema",
            description="Estado actual de reportes y notificaciones críticas",
            color_name="blue-70"
        )
        
        # Grid para alertas
        alert_grid = grid(2, vertical_align="top")
        
        # Alertas críticas
        with alert_grid.container():
            if data['reportes_vencidos'] > 0:
                st.error(f"🚨 **CRÍTICO**: {data['reportes_vencidos']} reportes han superado el plazo legal")
                st.markdown("""
                <div style="background: #f8d7da; padding: 1rem; border-radius: 8px; border-left: 4px solid #dc3545; margin-top: 0.5rem; color: #000000;">
                    <strong>⚠️ Acción requerida:</strong> Revisar reportes vencidos inmediatamente
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success("✅ **Cumplimiento Legal**: Todos los reportes están dentro del plazo")
                st.markdown("""
                <div style="background: #d4edda; padding: 1rem; border-radius: 8px; border-left: 4px solid #28a745; margin-top: 0.5rem; color: #000000;">
                    <strong>📊 Estado:</strong> Excelente cumplimiento normativo
                </div>
                """, unsafe_allow_html=True)
        
        # Alertas de urgencia
        with alert_grid.container():
            if data['proximos_vencer'] > 0:
                st.warning(f"⏰ **URGENTE**: {data['proximos_vencer']} reportes vencen en los próximos 7 días")
                st.markdown("""
                <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107; margin-top: 0.5rem; color: #000000;">
                    <strong>💡 Recomendación:</strong> Priorizar estos reportes
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("📅 **Plazos Controlados**: Sin vencimientos próximos")
                st.markdown("""
                <div style="background: #d1ecf1; padding: 1rem; border-radius: 8px; border-left: 4px solid #17a2b8; margin-top: 0.5rem; color: #000000;">
                    <strong>📈 Estado:</strong> Planificación temporal adecuada
                </div>
                """, unsafe_allow_html=True)
        
        # Detalles expandibles con diseño profesional
        if data['reportes_vencidos'] > 0:
            with st.expander("🔍 Detalles de Reportes Vencidos", expanded=True):
                if data['detalles_vencidos']:
                    # Crear DataFrame para mejor visualización
                    df_vencidos = pd.DataFrame(data['detalles_vencidos'][:10], 
                                             columns=['Boletín', 'Titular', 'Fecha', 'Días Vencido'])
                    df_vencidos['Estado'] = df_vencidos['Días Vencido'].apply(
                        lambda x: f'<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">🚨 {int(x)} días</span>'
                    )
                    
                    st.markdown("### Reportes que requieren atención inmediata:")
                    for _, row in df_vencidos.iterrows():
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #dc3545; color: #000000;">
                            <strong>Boletín {row['Boletín']}</strong> - {row['Titular'][:50]}...<br>
                            <small style="color: #555555;">Fecha: {row['Fecha']} | <span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">🚨 {int(row["Días Vencido"])} días vencido</span></small>
                        </div>
                        """, unsafe_allow_html=True)
        
        if data['proximos_vencer'] > 0:
            with st.expander("📋 Reportes Próximos a Vencer", expanded=True):
                if data['detalles_proximos_vencer']:
                    st.markdown("### Reportes que requieren atención prioritaria:")
                    for detalle in data['detalles_proximos_vencer']:
                        dias_restantes = int(detalle[3])
                        status = 'vencido' if dias_restantes <= 2 else 'proximo' if dias_restantes <= 5 else 'activo'
                        # Create static badge based on status
                        if status == 'vencido':
                            badge_html = f'<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">🚨 {dias_restantes} días restantes</span>'
                        elif status == 'proximo':
                            badge_html = f'<span style="background: #ffc107; color: #000; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">⚠️ {dias_restantes} días restantes</span>'
                        else:
                            badge_html = f'<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">✅ {dias_restantes} días restantes</span>'
                        
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid {'#dc3545' if status == 'vencido' else '#ffc107' if status == 'proximo' else '#28a745'}; color: #000000;">
                            <strong>Boletín {detalle[0]}</strong> - {detalle[1][:50]}...<br>
                            <small style="color: #555555;">Fecha: {detalle[2]} | {badge_html}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Mensajes de estado positivo
        if data['reportes_vencidos'] == 0 and data['proximos_vencer'] == 0:
            if data['total_boletines'] > 0:
                st.success("✅ ¡Excelente! Todos los reportes están dentro del plazo legal y bajo control")
        
        if data['total_boletines'] == 0:
            st.info("📂 No hay boletines cargados en el sistema. Use la sección 'Cargar Datos' para comenzar.")
        
        # Sección de gráficos profesionales
        if data['total_boletines'] > 0:
            colored_header(
                label="📊 Análisis Visual",
                description="Gráficos y estadísticas avanzadas del sistema",
                color_name="violet-70"
            )
            
            # Grid de gráficos (solo 2 gráficos)
            chart_grid = grid(2, vertical_align="top")
            
            # Gráfico de dona - Estado de reportes
            with chart_grid.container():
                st.markdown("### 📊 Estado de Reportes")
                fig_donut = create_status_donut_chart(data)
                st.plotly_chart(fig_donut, use_container_width=True)
            
            # Gauge de urgencia
            with chart_grid.container():
                st.markdown("### 🚨 Monitor de Urgencia")
                fig_gauge = create_urgency_gauge_chart(data)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
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
    st.session_state.email_credentials = cargar_credenciales_email()
if 'confirmar_generar_informes' not in st.session_state:
    st.session_state.confirmar_generar_informes = False
if 'email_config' not in st.session_state:
    st.session_state.email_config = cargar_credenciales_email()
if 'confirmar_envio_emails' not in st.session_state:
    st.session_state.confirmar_envio_emails = False
if 'resultados_envio' not in st.session_state:
    st.session_state.resultados_envio = None

# ================================
# SISTEMA DE AUTENTICACIÓN SIMPLIFICADO
# ================================

# Manejar autenticación completa
if not handle_authentication():
    st.stop()

# Usuario autenticado - mostrar aplicación principal
# ================================
# NAVEGACIÓN PROFESIONAL MEJORADA
# ================================

# Modal para cambiar contraseña (si se implementa en el futuro)
# if st.session_state.get('show_change_password', False):
#     show_change_password_modal()

# Gestión de usuarios avanzada (si se implementa en el futuro)
# if st.session_state.get('show_user_management', False):
#     show_user_management()

# Mostrar aplicación principal
# Menú de navegación profesional con efectos hover
tabs = option_menu(
    menu_title=None,
    options=["Dashboard", "Cargar Datos", "Historial", "Clientes", "📋 Reportes", "Configuración"],
    icons=["house-fill", "cloud-upload-fill", "list-task", "people-fill", "gear-fill", "gear-fill"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0!important",
            "background": "rgba(255, 255, 255, 0.95)",
            "border": "1px solid rgba(255, 255, 255, 0.2)",
            "border-radius": "16px",
            "margin-bottom": "2rem",
            "box-shadow": "0 8px 32px rgba(0, 0, 0, 0.1)",
            "backdrop-filter": "blur(10px)"
        },
        "icon": {
            "color": "#667eea", 
            "font-size": "20px",
            "margin-right": "8px"
        },
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "8px 4px",
            "padding": "12px 20px",
            "background-color": "transparent",
            "color": "#495057",
            "border-radius": "12px",
            "font-weight": "600",
            "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            "white-space": "nowrap",
            "position": "relative",
            "overflow": "hidden"
        },
        "nav-link-selected": {
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "color": "white",
            "font-weight": "700",
            "box-shadow": "0 8px 25px rgba(102, 126, 234, 0.4)",
            "transform": "translateY(-2px)"
        },
        "nav-link:hover": {
            "background": "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)",
            "color": "#667eea",
            "transform": "translateY(-3px)",
            "box-shadow": "0 6px 20px rgba(102, 126, 234, 0.2)"
        }
    }
)

# Manejo de navegación basado en la selección del option-menu
if tabs == 'Dashboard':
    st.session_state.current_page = 'dashboard'
    st.session_state.show_db_section = False
    st.session_state.show_clientes_section = False
    st.session_state.show_email_section = False

elif tabs == 'Cargar Datos':
    st.session_state.current_page = 'upload'
    st.session_state.show_db_section = False
    st.session_state.show_clientes_section = False
    st.session_state.show_email_section = False

elif tabs == 'Historial':
    st.session_state.current_page = 'historial'
    st.session_state.show_db_section = True
    st.session_state.show_clientes_section = False
    st.session_state.show_email_section = False

elif tabs == 'Clientes':
    st.session_state.current_page = 'clientes'
    st.session_state.show_clientes_section = True
    st.session_state.show_db_section = False
    st.session_state.show_email_section = False

elif tabs == '📋 Reportes':
    st.session_state.current_page = 'reportes_unificados'
    st.session_state.show_db_section = False
    st.session_state.show_clientes_section = False
    st.session_state.show_email_section = False
    
    # Importar y mostrar la gestión unificada
    from unified_report_manager import show_unified_report_management
    show_unified_report_management()

elif tabs == 'Configuración':
    st.session_state.current_page = 'settings'
    st.session_state.show_db_section = False
    st.session_state.show_clientes_section = False
    st.session_state.show_email_section = False

    # Estadísticas rápidas con mejor diseño
    st.markdown("---")
    st.markdown("### 📊 Resumen Ejecutivo")
    
    # Obtener estadísticas rápidas
    conn_stats = crear_conexion()
    if conn_stats:
        try:
            data = get_dashboard_data(conn_stats)
            
            # Mostrar métricas de dashboard
            st.success(f"📊 Total de boletines: {data['total_boletines']}")            
            # Métricas compactas en dos columnas
            col1, col2 = st.columns(2)
            with col1:
                percentage_gen = (data['reportes_generados']/max(data['total_boletines'], 1)*100) if data['total_boletines'] > 0 else 0
                st.metric("📊 Reportes Generados", data['reportes_generados'], f"{percentage_gen:.0f}%")
            
            with col2:
                percentage_env = (data['reportes_enviados']/max(data['reportes_generados'], 1)*100) if data['reportes_generados'] > 0 else 0
                st.metric("📧 Reportes Enviados", data['reportes_enviados'], f"{percentage_env:.0f}%")
                
        except Exception as e:
            st.error("Error al cargar estadísticas")
        finally:
            conn_stats.close()
    
    # Footer mejorado
    st.markdown("---")
    st.markdown("**v2.1.0** - 2024")

# ================================
# CONTENIDO PRINCIPAL
# ================================

# Inicialización automática del sistema (solo una vez por sesión)
if 'sistema_inicializado' not in st.session_state:
    st.session_state.sistema_inicializado = False

if not st.session_state.sistema_inicializado:
    try:
        # Ejecutar limpieza automática de logs al iniciar
        conn = crear_conexion()
        if conn:
            try:
                resultado_limpieza = limpieza_automatica_logs(conn)
                st.session_state.resultado_limpieza_automatica = resultado_limpieza
                st.session_state.sistema_inicializado = True
            except Exception as e:
                # Si hay error, no bloquear la aplicación
                st.session_state.resultado_limpieza_automatica = {'mensaje': f'Error en limpieza: {e}'}
                st.session_state.sistema_inicializado = True
            finally:
                conn.close()
    except:
        # Si no se puede conectar, marcar como inicializado para no bloquear
        st.session_state.sistema_inicializado = True

# Mostrar contenido basado en la página actual
if st.session_state.current_page == 'dashboard':
    show_dashboard()


elif st.session_state.current_page == 'upload':
    # Header de sección profesional
    colored_header(
        label="📤 Carga de Boletines",
        description="Importar y procesar archivos XLSX de boletines oficiales",
        color_name="blue-70"
    )
    
    # Instrucciones en card profesional
    st.markdown("""
<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #667eea;">
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <i class="fas fa-info-circle" style="color: #667eea; font-size: 1.2rem; margin-right: 0.5rem;"></i>
        <h3 style="color: #000000 !important; margin: 0;">Instrucciones de Carga</h3>
    </div>
    <div style="margin: 1rem 0; color: #000000;">
        <h4 style="color: #000000 !important; margin-bottom: 1rem;">Pasos para cargar boletines:</h4>
        <ol style="margin: 0; padding-left: 1.5rem; line-height: 1.8; color: #000000;">
            <li><strong style="color: #000000;">Seleccionar archivo:</strong> Elija un archivo XLSX con los datos del boletín</li>
            <li><strong style="color: #000000;">Vista previa:</strong> Revise los datos extraídos antes de importar</li>
            <li><strong style="color: #000000;">Importar:</strong> Confirme la carga a la base de datos</li>
        </ol>
        <div style="background: #e7f3ff; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #667eea; color: #000000;">
            <strong style="color: #000000;">Tip:</strong> Asegúrese de que el archivo tenga el formato correcto antes de cargar.
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)
    
    # Área de carga de archivos mejorada
    upload_grid = grid(1, vertical_align="center")
    
    with upload_grid.container():
        st.markdown("""
<div style="border: 2px dashed #667eea; border-radius: 16px; padding: 2rem; text-align: center; background: rgba(102, 126, 234, 0.05); margin: 1rem 0;">
    <div style="font-size: 3rem; color: #667eea; margin-bottom: 1rem;">FILE</div>
    <h3 style="color: #495057; margin-bottom: 0.5rem;">Cargar Archivo XLSX</h3>
    <p style="color: #6c757d; margin-bottom: 1rem;">Arrastra tu archivo aqui o haz clic para seleccionar</p>
</div>
        """, unsafe_allow_html=True)
        
        archivo = st.file_uploader(
            "Seleccionar archivo XLSX",
            type=["xlsx"],
            help="Seleccione un archivo Excel (.xlsx) con los datos del boletín"
        )

    if archivo:
        # Calcular tamaño en KB
        tamano_kb = round(archivo.size / 1024, 1)
        
        # Mostrar información del archivo
        st.markdown(f"""
<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #28a745;">
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <i class="fas fa-file-excel" style="color: #28a745; font-size: 1.2rem; margin-right: 0.5rem;"></i>
        <h3 style="color: #000000 !important; margin: 0;">Archivo Cargado Exitosamente</h3>
    </div>
    <div style="margin: 1rem 0; color: #000000;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div style="color: #000000;">
                <strong style="color: #000000;">Nombre:</strong> {archivo.name}<br>
                <strong style="color: #000000;">Tamaño:</strong> {tamano_kb} KB
            </div>
            <div style="color: #000000;">
                <strong style="color: #000000;">Tipo:</strong> {archivo.type}<br>
                <strong style="color: #000000;">Estado:</strong> <span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">Listo para procesar</span>
            </div>
        </div>
    </div>
</div>
        """, unsafe_allow_html=True)
        
        # Procesar archivo
        try:
            with st.spinner("🔄 Procesando archivo..."):
                # Leer el archivo Excel
                df = pd.read_excel(archivo)
                
                # Extraer datos agrupados
                datos_agrupados = extraer_datos_agrupados(df)
            
            if datos_agrupados:
                # Estadísticas del archivo
                total_registros = sum(len(registros) for registros in datos_agrupados.values())
                total_titulares = len(datos_agrupados)
                
                # Métricas del archivo
                metrics_grid = grid(3, vertical_align="center")
                
                with metrics_grid.container():
                    st.markdown(create_metric_card(
                        total_titulares, 
                        "👥 Titulares Encontrados", 
                        "#17a2b8"
                    ), unsafe_allow_html=True)
                
                with metrics_grid.container():
                    st.markdown(create_metric_card(
                        total_registros, 
                        "📋 Registros Totales", 
                        "#28a745"
                    ), unsafe_allow_html=True)
                
                with metrics_grid.container():
                    promedio = total_registros / total_titulares if total_titulares > 0 else 0
                    st.markdown(create_metric_card(
                        f"{promedio:.1f}", 
                        "📊 Promedio por Titular", 
                        "#ffc107"
                    ), unsafe_allow_html=True)
                
                # Botón de importación profesional
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    # Crear conexión para verificar estado
                    conn = crear_conexion()
                    if conn:
                        try:
                            crear_tabla(conn)
                            
                            # Botón estilizado para importar
                            import_button = button(
                                "📥 Importar a Base de Datos", 
                                key="import_data_btn",
                                type="primary"
                            )
                            
                            if import_button:
                                with st.spinner("🔄 Importando datos a la base de datos..."):
                                    time.sleep(1)  # Simular procesamiento
                                    insertar_datos(conn, datos_agrupados)
                                
                                st.success("✅ ¡Datos importados exitosamente!")
                                
                                # Mostrar resumen de importación
                                st.markdown(f"""
                                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #28a745;">
                                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                                        <i class="fas fa-check-circle" style="color: #28a745; font-size: 1.2rem; margin-right: 0.5rem;"></i>
                                        <h3 style="color: #000000 !important; margin: 0;">Resumen de Importación</h3>
                                    </div>
                                    <div style="text-align: center; margin: 1rem 0; color: #000000;">
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                                            <div style="color: #000000;">
                                                <div style="font-size: 2rem; color: #28a745; margin-bottom: 0.5rem;">&check;</div>
                                                <strong style="color: #000000;">{total_registros}</strong><br>
                                                <small style="color: #000000;">Registros Importados</small>
                                            </div>
                                            <div style="color: #000000;">
                                                <div style="font-size: 2rem; color: #17a2b8; margin-bottom: 0.5rem;">&hearts;</div>
                                                <strong style="color: #000000;">{total_titulares}</strong><br>
                                                <small style="color: #000000;">Titulares Procesados</small>
                                            </div>
                                        </div>
                                        <div style="margin-top: 1rem; padding: 1rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745; color: #000000;">
                                            <strong style="color: #000000;">Estado:</strong> Importación completada exitosamente
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.error(f"❌ Error durante la importación: {e}")
                        finally:
                            conn.close()
                    else:
                        st.error("❌ No se pudo conectar a la base de datos")
                
                # Vista previa de datos con diseño profesional
                colored_header(
                    label="� Vista Previa de Datos",
                    description="Revise los datos extraídos antes de la importación",
                    color_name="green-70"
                )
                
                for titular, registros in datos_agrupados.items():
                    with st.expander(f"📁 {titular} ({len(registros)} registros)", expanded=False):
                        # Convertir registros a DataFrame
                        df_registros = pd.DataFrame(registros)
                        # Añadir columna 'Titular' con el valor del titular
                        df_registros['Titular'] = titular
                        # Reordenar columnas para que 'Titular' esté al principio
                        cols = ['Titular'] + [col for col in df_registros.columns if col != 'Titular']
                        df_registros = df_registros[cols]
                        
                        # Mostrar estadísticas del titular
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                            <strong>📊 Estadísticas:</strong> {len(registros)} registros | 
                            <strong>📅 Período:</strong> Datos del boletín cargado |
                            <span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600;">✅ Válido</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Mostrar el DataFrame como tabla interactiva
                        st.dataframe(df_registros, use_container_width=True)
            else:
                st.warning("⚠️ No se encontraron titulares válidos en el archivo.")
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")
            st.markdown(create_professional_card(
                "🔧 Sugerencias para Resolver Problemas",
                """
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>Verifique que el archivo sea un XLSX válido</li>
                    <li>Asegúrese de que tenga el formato de columnas esperado</li>
                    <li>Revise que no haya celdas combinadas problemáticas</li>
                    <li>Intente guardar el archivo nuevamente desde Excel</li>
                </ul>
                """,
                "fas fa-tools"
            ), unsafe_allow_html=True)

elif st.session_state.current_page == 'historial' and st.session_state.show_db_section:
    st.title("📋 Historial de Boletines")
    
    # Cargar datos de la base de datos
    conn = crear_conexion()
    if conn:
        try:
            crear_tabla(conn)
            rows, columns = obtener_datos(conn)
            
            if rows:
                # Convertir a DataFrame
                df = pd.DataFrame(rows, columns=columns)
                st.session_state.db_data = df
                
                # Implementar aquí tu código de filtros profesionales que mencionaste antes
                # Convertir columnas booleanas
                filtered_df = st.session_state.db_data.copy()
                filtered_df['reporte_enviado'] = filtered_df['reporte_enviado'].astype(bool)
                filtered_df['reporte_generado'] = filtered_df['reporte_generado'].astype(bool)
                
                # Filtros con pestañas
                with st.container():
                    st.markdown("""
                    <style>
                    .filter-container {
                        background-color: #f8fafc;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-bottom: 20px;
                    }
                    
                    /* Estilos personalizados para pestañas del historial */
                    .stTabs [data-baseweb="tab-list"] {
                        background: linear-gradient(90deg, #2d2d2d 0%, #3a3a3a 100%);
                        border-radius: 12px;
                        padding: 6px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    }
                    
                    .stTabs [data-baseweb="tab"] {
                        background: transparent;
                        color: #e5e5e5;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 20px;
                        margin: 0 4px;
                        font-weight: 600;
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .stTabs [data-baseweb="tab"]:hover {
                        background: rgba(102, 126, 234, 0.2);
                        color: #ffffff;
                        transform: translateY(-2px);
                    }
                    
                    /* Información General - Azul */
                    .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
                        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                        color: white;
                        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
                    }
                    
                    /* Estados - Verde */
                    .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: white;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                    }
                    
                    /* Clasificación - Púrpura */
                    .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {
                        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                        color: white;
                        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                    st.markdown('#### 🔍 Filtros Avanzados', unsafe_allow_html=True)
                    
                    # Pestañas para organizar filtros
                    tab1, tab2, tab3 = st.tabs(["📋 Información General", "📊 Estados", "🏷️ Clasificación"])
                    
                    with tab1:
                        col1, col2 = st.columns(2)
                        with col1:
                            filtro_titular = st.text_input("🏢 Titular", placeholder="Buscar por titular...")
                            filtro_boletin = st.text_input("📝 Número de Boletín", placeholder="Ej: BOL-2023-001")
                            filtro_orden = st.text_input("🔢 Número de Orden", placeholder="Ej: 12345")
                        
                        with col2:
                            filtro_solicitante = st.text_input("👤 Solicitante", placeholder="Nombre del solicitante...")
                            filtro_agente = st.text_input("👥 Agente", placeholder="Nombre del agente...")
                            filtro_expediente = st.text_input("📂 Número de Expediente", placeholder="Ej: EXP-2023-001")

                    with tab2:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("##### Estado de Reportes")
                            filtro_reporte_enviado = st.toggle("📤 Pendientes de Envío", help="Mostrar solo los que no han sido enviados")
                            filtro_reporte_generado = st.toggle("📄 Pendientes de Generación", help="Mostrar solo los que no han sido generados")
                        
                        with col2:
                            st.markdown("##### Fechas")
                            filtro_fecha = st.date_input(
                                "📅 Fecha de Boletín",
                                value=None,
                                help="Filtrar por fecha específica"
                            )

                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            filtro_importancia = st.select_slider(
                                "⚡ Importancia",
                                options=["Todos", "Baja", "Media", "Alta", "Pendiente"],
                                value="Todos"
                            )
                        
                        with col2:
                            st.markdown("##### Opciones Adicionales")
                            filtro_importancia_pendiente = st.checkbox(
                                "⚠️ Solo Pendientes",
                                help="Mostrar solo registros con importancia pendiente"
                            )

                    # Aplicar filtros
                    mask = pd.Series(True, index=filtered_df.index)
                    
                    if filtro_titular:
                        mask &= filtered_df['titular'].str.contains(filtro_titular, case=False, na=False)
                    if filtro_boletin:
                        mask &= filtered_df['numero_boletin'].str.contains(filtro_boletin, case=False, na=False)
                    if filtro_orden:
                        mask &= filtered_df['numero_orden'].astype(str).str.contains(filtro_orden, na=False)
                    if filtro_solicitante:
                        mask &= filtered_df['solicitante'].str.contains(filtro_solicitante, case=False, na=False)
                    if filtro_agente:
                        mask &= filtered_df['agente'].str.contains(filtro_agente, case=False, na=False)
                    if filtro_expediente:
                        mask &= filtered_df['numero_expediente'].str.contains(filtro_expediente, na=False)
                    
                    if filtro_reporte_enviado:
                        mask &= (filtered_df['reporte_enviado'] == False)
                    if filtro_reporte_generado:
                        mask &= (filtered_df['reporte_generado'] == False)
                    
                    if filtro_fecha:
                        mask &= (pd.to_datetime(filtered_df['fecha_boletin']).dt.date == filtro_fecha)
                    
                    if filtro_importancia != "Todos":
                        mask &= (filtered_df['importancia'] == filtro_importancia)
                    
                    if filtro_importancia_pendiente:
                        mask &= (filtered_df['importancia'] == "Pendiente")
                    
                    filtered_df = filtered_df[mask]
                    st.markdown('</div>', unsafe_allow_html=True)

                # Mostrar tabla con grid
                if not filtered_df.empty:
                    st.markdown(f"📊 Mostrando {len(filtered_df)} registros de {len(st.session_state.db_data)} totales")
                    
                    # Mensaje informativo sobre edición
                    st.info("💡 **Tip**: Haz clic en la columna 'Importancia' para editarla. Los cambios se guardan automáticamente.")
                    
                    grid_response = show_grid_data(filtered_df, 'grid_boletines')
                else:
                    st.warning("No se encontraron registros que coincidan con los filtros.")
            else:
                st.info("No hay datos en la base de datos")
        except Exception as e:
            st.error(f"Error al consultar la base de datos: {e}")
        finally:
            conn.close()

elif st.session_state.current_page == 'clientes' and st.session_state.show_clientes_section:
    st.title("👥 Gestión de Clientes")
    
    # Cargar datos de clientes
    conn = crear_conexion()
    if conn:
        try:
            crear_tabla(conn)
            rows, columns = obtener_clientes(conn)
            
            if rows:
                df_clientes = pd.DataFrame(rows, columns=columns)
                st.session_state.clientes_data = df_clientes
                
                # Estilos personalizados para pestañas de clientes
                st.markdown("""
                <style>
                /* Estilos personalizados para pestañas de clientes */
                .stTabs [data-baseweb="tab-list"] {
                    background: linear-gradient(90deg, #2d2d2d 0%, #3a3a3a 100%);
                    border-radius: 12px;
                    padding: 6px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                
                .stTabs [data-baseweb="tab"] {
                    background: transparent;
                    color: #e5e5e5;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    margin: 0 4px;
                    font-weight: 600;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                }
                
                .stTabs [data-baseweb="tab"]:hover {
                    background: rgba(102, 126, 234, 0.2);
                    color: #ffffff;
                    transform: translateY(-2px);
                }
                
                /* Lista de Clientes - Naranja */
                .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
                    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(249, 115, 22, 0.4);
                }
                
                /* Agregar Cliente - Cyan */
                .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
                    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Solo dos pestañas: Lista Editable y Agregar Cliente
                tab1, tab2 = st.tabs(["📋 Lista de Clientes (Editable)", "➕ Agregar Cliente"])
                
                with tab1:
                    st.subheader("📋 Lista Completa de Clientes")
                    st.info("💡 **Instrucciones:** Haz clic en cualquier celda para editarla directamente. Los cambios se guardan automáticamente.")
                    
                    # Filtros para clientes - COMPACTOS
                    with st.expander("🔍 Filtros de Búsqueda", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            filtro_titular_cliente = st.text_input("🏢 Titular", placeholder="Buscar titular...")
                            filtro_email_cliente = st.text_input("📧 Email", placeholder="email@ejemplo.com")
                        with col2:
                            filtro_telefono_cliente = st.text_input("📞 Teléfono", placeholder="Teléfono...")
                            filtro_ciudad_cliente = st.text_input("🏙️ Ciudad", placeholder="Ciudad...")
                        with col3:
                            filtro_cuit_cliente = st.text_input("🆔 CUIT", placeholder="CUIT...")
                            mostrar_solo_incompletos = st.checkbox("⚠️ Solo incompletos")
                        with col4:
                            st.markdown("##### Acciones")
                            if st.button("🔄 Actualizar Datos", use_container_width=True):
                                st.rerun()
                    
                    # Aplicar filtros
                    filtered_clientes = df_clientes.copy()
                    
                    if filtro_titular_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['titular'].str.contains(filtro_titular_cliente, case=False, na=False)]
                    if filtro_email_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['email'].str.contains(filtro_email_cliente, case=False, na=False)]
                    if filtro_telefono_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['telefono'].str.contains(filtro_telefono_cliente, case=False, na=False)]
                    if filtro_ciudad_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['ciudad'].str.contains(filtro_ciudad_cliente, case=False, na=False)]
                    if filtro_cuit_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['cuit'].str.contains(filtro_cuit_cliente, case=False, na=False)]
                    if mostrar_solo_incompletos:
                        mask_incompletos = (
                            (filtered_clientes['email'].isna() | (filtered_clientes['email'] == '')) |
                            (filtered_clientes['telefono'].isna() | (filtered_clientes['telefono'] == '')) |
                            (filtered_clientes['direccion'].isna() | (filtered_clientes['direccion'] == ''))
                        )
                        filtered_clientes = filtered_clientes[mask_incompletos]
                    
                    # Mostrar resultados - TABLA EDITABLE
                    if not filtered_clientes.empty:
                        st.markdown(f"📊 **{len(filtered_clientes)}** clientes de **{len(df_clientes)}** totales")
                        
                        # GRILLA EDITABLE
                        grid_response = show_grid_data_clientes(filtered_clientes, 'grid_clientes_editable')
                        
                        # PROCESAR CAMBIOS EN TIEMPO REAL
                        # Reemplazar la sección de procesamiento de cambios en la pestaña tab1:

                        # PROCESAR CAMBIOS EN TIEMPO REAL - VERSIÓN CORREGIDA
                        if grid_response['data'] is not None and len(grid_response['data']) > 0:
                            df_modificado = pd.DataFrame(grid_response['data'])
                            
                            # Comparar con datos originales para encontrar cambios
                            for index, row in df_modificado.iterrows():
                                original_row = filtered_clientes[filtered_clientes['id'] == row['id']]
                                if not original_row.empty:
                                    original_row = original_row.iloc[0]
                                    
                                    # Verificar si hay cambios en cada campo
                                    cambios = False
                                    campos_cambiados = []
                                    
                                    for column in ['titular', 'email', 'telefono', 'direccion', 'ciudad', 'cuit']:
                                        # Normalizar valores para comparación (manejar NaN y None)
                                        valor_nuevo = str(row[column]) if pd.notna(row[column]) else ""
                                        valor_original = str(original_row[column]) if pd.notna(original_row[column]) else ""
                                        
                                        if valor_nuevo != valor_original:
                                            cambios = True
                                            campos_cambiados.append(column)
                                    
                                    if cambios:
                                        # Actualizar en la base de datos
                                        try:
                                            actualizar_cliente(
                                                conn, 
                                                row['id'], 
                                                row['titular'] if pd.notna(row['titular']) else "", 
                                                row['email'] if pd.notna(row['email']) else "", 
                                                row['telefono'] if pd.notna(row['telefono']) else "", 
                                                row['direccion'] if pd.notna(row['direccion']) else "", 
                                                row['ciudad'] if pd.notna(row['ciudad']) else "", 
                                                row['cuit'] if pd.notna(row['cuit']) else ""
                                            )
                                            st.success(f"✅ Cliente '{row['titular']}' actualizado: {', '.join(campos_cambiados)}")
                                            time.sleep(0.5)
                                            st.rerun()  # Recargar para mostrar cambios
                                        except Exception as e:
                                            st.error(f"❌ Error al actualizar '{row['titular']}': {e}")
                        
                        # Panel de acciones para cliente seleccionado
                        if grid_response['selected_rows']:
                            selected_client = grid_response['selected_rows'][0]
                            
                            with st.container():
                                st.markdown("---")
                                st.markdown(f"### 🎯 Cliente Seleccionado: **{selected_client['titular']}**")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    if st.button("📧 Enviar Email", type="secondary", use_container_width=True):
                                        st.info("📧 Funcionalidad próximamente")
                                with col2:
                                    if st.button("📋 Ver Boletines", type="secondary", use_container_width=True):
                                        st.info("📋 Funcionalidad próximamente")
                                with col3:
                                    if st.button("📄 Generar Reporte", type="secondary", use_container_width=True):
                                        st.info("📄 Funcionalidad próximamente")
                                with col4:
                                    if st.button("🗑️ Eliminar Cliente", type="secondary", use_container_width=True):
                                        # Confirmar eliminación
                                        if st.button("⚠️ Confirmar Eliminación", type="primary"):
                                            try:
                                                eliminar_cliente(conn, selected_client['id'])
                                                st.success(f"✅ Cliente '{selected_client['titular']}' eliminado")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error al eliminar: {e}")
                    else:
                        st.warning("🔍 No se encontraron clientes que coincidan con los filtros aplicados.")
                
                with tab2:
                    st.subheader("➕ Agregar Nuevo Cliente")
                    st.markdown("Complete la información del nuevo cliente. Los campos marcados con **\\*** son obligatorios.")
                    
                    # Inicializar valores en session_state si no existen
                    if 'form_titular' not in st.session_state:
                        st.session_state.form_titular = ""
                    if 'form_email' not in st.session_state:
                        st.session_state.form_email = ""
                    if 'form_telefono' not in st.session_state:
                        st.session_state.form_telefono = ""
                    if 'form_cuit' not in st.session_state:
                        st.session_state.form_cuit = ""
                    if 'form_ciudad' not in st.session_state:
                        st.session_state.form_ciudad = ""
                    if 'form_direccion' not in st.session_state:
                        st.session_state.form_direccion = ""
                    
                    with st.form("form_nuevo_cliente", clear_on_submit=False):
                        # Información básica
                        st.markdown("##### 📋 Información Básica")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nuevo_titular = st.text_input("🏢 Titular *", 
                                                        value=st.session_state.form_titular,
                                                        placeholder="Nombre o razón social")
                            nuevo_email = st.text_input("📧 Email *", 
                                                       value=st.session_state.form_email,
                                                       placeholder="cliente@ejemplo.com")
                        with col2:
                            nuevo_telefono = st.text_input("📞 Teléfono", 
                                                          value=st.session_state.form_telefono,
                                                          placeholder="+54 9 11 1234-5678")
                            nuevo_cuit = st.text_input("🆔 CUIT/CUIL", 
                                                      value=st.session_state.form_cuit,
                                                      placeholder="20-12345678-9")
                        with col3:
                            nueva_ciudad = st.text_input("🏙️ Ciudad", 
                                                        value=st.session_state.form_ciudad,
                                                        placeholder="Buenos Aires")
                            
                        # Dirección completa
                        st.markdown("##### 📍 Dirección")
                        nueva_direccion = st.text_area("🏠 Dirección Completa", 
                                                      value=st.session_state.form_direccion,
                                                      placeholder="Calle, número, piso, departamento, código postal", 
                                                      height=80)
                        
                        # Estilos CSS para el botón personalizado
                        st.markdown("""
                        <style>
                        .custom-submit-btn {
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                            color: white !important;
                            border: none !important;
                            border-radius: 12px !important;
                            padding: 0.75rem 2rem !important;
                            font-weight: 700 !important;
                            font-size: 1.1rem !important;
                            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
                            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                            text-transform: uppercase !important;
                            letter-spacing: 1px !important;
                            position: relative !important;
                            overflow: hidden !important;
                        }
                        
                        .custom-submit-btn:hover {
                            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
                            transform: translateY(-3px) !important;
                            box-shadow: 0 12px 35px rgba(16, 185, 129, 0.6) !important;
                        }
                        
                        .custom-submit-btn:active {
                            transform: translateY(-1px) !important;
                            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
                        }
                        
                        .custom-submit-btn::before {
                            content: '';
                            position: absolute;
                            top: 0;
                            left: -100%;
                            width: 100%;
                            height: 100%;
                            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                            transition: left 0.5s ease;
                        }
                        
                        .custom-submit-btn:hover::before {
                            left: 100%;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Botón de envío con diseño profesional
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            # Contenedor centrado para el botón
                            st.markdown("""
                            <div style="text-align: center; margin: 2rem 0;">
                                <div style="background: rgba(16, 185, 129, 0.1); padding: 1.5rem; border-radius: 16px; border: 2px dashed rgba(16, 185, 129, 0.3);">
                                    <div style="font-size: 1.1rem; color: #059669; margin-bottom: 1rem; font-weight: 600;">
                                        💾 ¿Listo para guardar el nuevo cliente?
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            submitted = st.form_submit_button(
                                "� GUARDAR CLIENTE",
                                type="primary", 
                                use_container_width=True,
                                help="Haz clic para agregar este cliente a la base de datos"
                            )
                        
                        if submitted:
                            # Actualizar session_state con los valores actuales
                            st.session_state.form_titular = nuevo_titular
                            st.session_state.form_email = nuevo_email
                            st.session_state.form_telefono = nuevo_telefono
                            st.session_state.form_cuit = nuevo_cuit
                            st.session_state.form_ciudad = nueva_ciudad
                            st.session_state.form_direccion = nueva_direccion
                            
                            if nuevo_titular and nuevo_email:
                                # Validar formato de email
                                if validate_email_format(nuevo_email):
                                    try:
                                        # Verificar si ya existe un cliente con ese titular
                                        cursor = conn.cursor()
                                        cursor.execute("SELECT COUNT(*) FROM clientes WHERE titular = ?", (nuevo_titular,))
                                        existe = cursor.fetchone()[0] > 0
                                        cursor.close()
                                        
                                        if existe:
                                            st.error("⚠️ Ya existe un cliente con ese titular. Use un nombre diferente.")
                                        else:
                                            insertar_cliente(conn, nuevo_titular, nuevo_email, nuevo_telefono, 
                                                           nueva_direccion, nueva_ciudad, nuevo_cuit)
                                            st.success("✅ Cliente agregado correctamente")
                                            
                                            # Limpiar formulario solo después del éxito
                                            st.session_state.form_titular = ""
                                            st.session_state.form_email = ""
                                            st.session_state.form_telefono = ""
                                            st.session_state.form_cuit = ""
                                            st.session_state.form_ciudad = ""
                                            st.session_state.form_direccion = ""
                                            
                                            time.sleep(1)
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error al agregar el cliente: {e}")
                                else:
                                    st.error("⚠️ El formato del email no es válido. Por favor, ingrese un email correcto.")
                            else:
                                if not nuevo_titular:
                                    st.error("⚠️ El campo Titular es obligatorio")
                                if not nuevo_email:
                                    st.error("⚠️ El campo Email es obligatorio")
            
            else:
                st.info("📂 No hay clientes registrados en el sistema")
                
                # Botón para agregar el primer cliente
                st.markdown("---")
                st.markdown("### 🚀 ¡Comienza agregando tu primer cliente!")
                
                if st.button("➕ Agregar Primer Cliente", type="primary", use_container_width=True):
                    pass
                    
        except Exception as e:
            st.error(f"❌ Error al consultar clientes: {e}")
            st.exception(e)
        finally:
            conn.close()

elif st.session_state.current_page == 'settings':
    show_settings_page()
    
    # Cargar estadísticas
    conn = crear_conexion()
    if conn:
        try:
            crear_tabla(conn)
            
            # Obtener estadísticas de envíos
            stats = obtener_estadisticas_envios(conn)
            
            if stats:
                # Dashboard de estadísticas
                st.subheader("📊 Estado de Envíos")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("📋 Total Reportes", stats['total_reportes'])
                with col2:
                    st.metric("📄 Generados", stats['reportes_generados'])
                with col3:
                    st.metric("📧 Enviados", stats['reportes_enviados'])
                with col4:
                    pendientes_color = "normal" if stats['pendientes_revision'] == 0 else "inverse"
                    st.metric("⚠️ Pendientes Revisión", stats['pendientes_revision'])
                with col5:
                    st.metric("🚀 Listos para Envío", stats['listos_envio'])
                
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
                
                # Aplicar estilos CSS para gestión de emails
                st.markdown('<div class="email-management-container">', unsafe_allow_html=True)
                
                # Estilos CSS globales y muy específicos para las pestañas de gestión de emails
                st.markdown("""
                    <style>
                    /* ESTILOS FORZADOS PARA PESTAÑAS DE EMAIL */
                    
                    /* Contenedor de pestañas con mayor especificidad */
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
                        background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%) !important;
                        border-radius: 12px !important;
                        padding: 8px !important;
                        margin-bottom: 20px !important;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
                        border: 1px solid #4a4a5a !important;
                    }
                    
                    /* Pestañas individuales */
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
                        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
                        color: #b5b5c3 !important;
                        border: 1px solid #3a3a4a !important;
                        border-radius: 8px !important;
                        margin: 0 3px !important;
                        font-weight: 600 !important;
                        padding: 12px 16px !important;
                        font-size: 0.9rem !important;
                        transition: all 0.3s ease !important;
                        min-height: 45px !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                    
                    /* Hover state */
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:hover {
                        background: rgba(102, 126, 234, 0.2) !important;
                        color: #ffffff !important;
                        transform: translateY(-2px) !important;
                    }
                    
                    /* Pestaña activa - Estados específicos por posición */
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                        color: white !important;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
                    }
                    
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
                        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
                        color: white !important;
                        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
                    }
                    
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {
                        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
                        color: white !important;
                        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
                    }
                    
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-child(4)[aria-selected="true"] {
                        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
                        color: white !important;
                        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
                    }
                    
                    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-child(5)[aria-selected="true"] {
                        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%) !important;
                        color: white !important;
                        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4) !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                
                # JavaScript más agresivo para aplicar estilos
                import streamlit.components.v1 as components
                components.html("""
                <script>
                function applyEmailTabStyles() {
                    // Buscar todas las pestañas
                    const tabList = document.querySelector('div[data-testid="stTabs"] > div[data-baseweb="tab-list"]');
                    if (!tabList) return;
                    
                    // Estilizar contenedor de pestañas
                    tabList.style.cssText = `
                        background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%) !important;
                        border-radius: 12px !important;
                        padding: 8px !important;
                        margin-bottom: 20px !important;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
                        border: 1px solid #4a4a5a !important;
                    `;
                    
                    // Buscar y estilizar pestañas individuales
                    const tabs = tabList.querySelectorAll('button[data-baseweb="tab"]');
                    const gradients = [
                        'linear-gradient(135deg, #10b981 0%, #059669 100%)', // Verde - Enviar
                        'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', // Azul - Configuración
                        'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', // Naranja - Historial
                        'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)', // Púrpura - Logs
                        'linear-gradient(135deg, #ec4899 0%, #be185d 100%)'  // Rosa - Enviados
                    ];
                    
                    tabs.forEach((tab, index) => {
                        // Estilos base para todas las pestañas
                        tab.style.cssText = `
                            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
                            color: #b5b5c3 !important;
                            border: 1px solid #3a3a4a !important;
                            border-radius: 8px !important;
                            margin: 0 3px !important;
                            font-weight: 600 !important;
                            padding: 12px 16px !important;
                            font-size: 0.9rem !important;
                            transition: all 0.3s ease !important;
                            min-height: 45px !important;
                        `;
                        
                        // Si la pestaña está activa, aplicar gradiente específico
                        if (tab.getAttribute('aria-selected') === 'true') {
                            tab.style.background = gradients[index] + ' !important';
                            tab.style.color = 'white !important';
                            tab.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4) !important';
                        }
                        
                        // Agregar listener para mantener estilos al hacer clic
                        tab.addEventListener('click', function() {
                            setTimeout(() => {
                                tabs.forEach((t, i) => {
                                    t.style.cssText = `
                                        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
                                        color: #b5b5c3 !important;
                                        border: 1px solid #3a3a4a !important;
                                        border-radius: 8px !important;
                                        margin: 0 3px !important;
                                        font-weight: 600 !important;
                                        padding: 12px 16px !important;
                                        font-size: 0.9rem !important;
                                        transition: all 0.3s ease !important;
                                        min-height: 45px !important;
                                    `;
                                    
                                    if (t.getAttribute('aria-selected') === 'true') {
                                        t.style.background = gradients[i] + ' !important';
                                        t.style.color = 'white !important';
                                        t.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4) !important';
                                    }
                                });
                            }, 50);
                        });
                    });
                }
                
                // Aplicar estilos inmediatamente y después de un delay
                setTimeout(applyEmailTabStyles, 100);
                setTimeout(applyEmailTabStyles, 500);
                setTimeout(applyEmailTabStyles, 1000);
                
                // Observar cambios en el DOM para reaplicar estilos
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList' || mutation.type === 'attributes') {
                            setTimeout(applyEmailTabStyles, 100);
                        }
                    });
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['aria-selected']
                });
                </script>
                """, height=0)
                
                # Pestañas para organizar la funcionalidad - SIEMPRE VISIBLES
                st.markdown('<h3 class="email-management-title">🔧 Gestión de Emails</h3>', unsafe_allow_html=True)
                
                # CSS más agresivo usando st.write
                st.write("""
                <style>
                /* FORZAR ESTILOS PARA PESTAÑAS DE EMAIL - MÁXIMA PRIORIDAD */
                [data-testid="stTabs"] [data-baseweb="tab-list"] {
                    background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%) !important;
                    border-radius: 12px !important;
                    padding: 8px !important;
                    margin-bottom: 20px !important;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
                    border: 1px solid #4a4a5a !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"] {
                    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
                    color: #b5b5c3 !important;
                    border: 1px solid #3a3a4a !important;
                    border-radius: 8px !important;
                    margin: 0 3px !important;
                    font-weight: 600 !important;
                    padding: 12px 16px !important;
                    font-size: 0.9rem !important;
                    transition: all 0.3s ease !important;
                    min-height: 45px !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"]:hover {
                    background: rgba(102, 126, 234, 0.2) !important;
                    color: #ffffff !important;
                    transform: translateY(-2px) !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]:nth-of-type(1) {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]:nth-of-type(2) {
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]:nth-of-type(3) {
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]:nth-of-type(4) {
                    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
                }
                
                [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]:nth-of-type(5) {
                    background: linear-gradient(135deg, #ec4899 0%, #be185d 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Forzar actualización con timestamp único
                import time
                unique_key = f"email_tabs_{int(time.time())}"
                
                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    ["🚀 Enviar Emails", "⚙️ Configuración", "📊 Historial de Envíos", "📋 Logs Detallados", "📁 Emails Enviados"]
                )
                
                # Solo mostrar contenido de envío si no hay reportes pendientes
                with tab1:
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
                                st.markdown("##### 📧 Credenciales de Email")
                                
                                # Obtener credenciales actuales
                                credenciales = obtener_credenciales_email()
                                
                                # Mostrar credenciales cargadas (email visible, password oculta)
                                if credenciales['email']:
                                    st.success(f"✅ Email configurado: {credenciales['email']}")
                                    st.info("🔑 Contraseña cargada desde archivo")
                                    
                                    # Mostrar estado de validación
                                    if validate_email_format(credenciales['email']):
                                        st.success("📧 Formato de email válido")
                                    else:
                                        st.error("❌ Formato de email inválido")
                                        
                                    # Enlace a configuración
                                    st.markdown("---")
                                    if st.button("⚙️ Cambiar Credenciales", use_container_width=True):
                                        st.info("💡 Ve a la pestaña 'Configuración' para cambiar las credenciales")
                                
                                else:
                                    st.warning("⚠️ No hay credenciales configuradas")
                                    st.info("💡 Ve a la pestaña 'Configuración' para configurar las credenciales")
                                
                                st.markdown("---")
                                
                                # Botón principal de envío - solo si hay credenciales
                                if credenciales['email'] and credenciales['password']:
                                    # Botón de confirmación si está en estado de confirmación
                                    if st.session_state.get('confirmar_envio_emails', False):
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
                                                # EJECUTAR EL ENVÍO AQUÍ
                                                with st.spinner(f"Enviando {stats['listos_envio']} emails..."):
                                                    try:
                                                        st.info("🔄 Procesando envíos...")
                                                        resultados = procesar_envio_emails(
                                                            conn, 
                                                            credenciales['email'], 
                                                            credenciales['password']
                                                        )
                                                        
                                                        # Resetear confirmación
                                                        st.session_state.confirmar_envio_emails = False
                                                        
                                                        # Guardar resultados en session_state para mostrarlos fuera del contexto de columnas
                                                        st.session_state.resultados_envio = resultados
                                                        
                                                        # Mostrar resultados sin columnas anidadas
                                                        if resultados.get('bloqueado_por_pendientes', False):
                                                            st.error("❌ Envío bloqueado por reportes pendientes")
                                                            info_pendientes = resultados.get('info_pendientes')
                                                            if info_pendientes:
                                                                st.markdown(f"**{info_pendientes['total_reportes']}** reportes requieren revisión de **{info_pendientes['total_titulares']}** titulares")
                                                        else:
                                                            # Forzar actualización para mostrar resultados
                                                            st.rerun()
                                                    
                                                    except Exception as e:
                                                        st.session_state.confirmar_envio_emails = False
                                                        st.error(f"❌ Error durante el envío: {str(e)}")
                                                        
                                                        # Mostrar detalles del error si es por reportes pendientes
                                                        if "Pendiente" in str(e):
                                                            st.info("� Ve a la sección 'Historial' para cambiar la importancia de los reportes pendientes.")
                                        with col_conf2:
                                            if st.button("❌ Cancelar", use_container_width=True):
                                                st.session_state.confirmar_envio_emails = False
                                                st.rerun()
                                        
                                        # Mostrar resultados de envío fuera del contexto de columnas
                                        if 'resultados_envio' in st.session_state and st.session_state.resultados_envio:
                                            resultados = st.session_state.resultados_envio
                                            st.session_state.resultados_envio = None  # Limpiar después de mostrar
                                            
                                            st.success("🎉 Proceso de envío completado!")
                                            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                                            with col_r1:
                                                st.metric("✅ Exitosos", len(resultados['exitosos']))
                                            with col_r2:
                                                st.metric("❌ Fallidos", len(resultados['fallidos']))
                                            with col_r3:
                                                st.metric("📧 Sin Email", len(resultados['sin_email']))
                                            with col_r4:
                                                st.metric("� Sin Archivo", len(resultados['sin_archivo']))
                                            
                                            if len(resultados['exitosos']) > 0:
                                                st.success(f"🎉 ¡{len(resultados['exitosos'])} emails enviados exitosamente!")
                                                # Mostrar detalles de los envíos exitosos
                                                with st.expander(f"📧 Ver detalles de envíos exitosos ({len(resultados['exitosos'])})", expanded=False):
                                                    for envio in resultados['exitosos']:
                                                        titular = envio.get('titular', 'N/A')
                                                        importancia = envio.get('importancia', 'N/A')
                                                        email = envio.get('email', 'N/A')
                                                        cantidad = envio.get('cantidad_boletines', 0)
                                                        st.write(f"✅ **{titular}** ({importancia}) → {email} ({cantidad} boletines)")
                                            
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
                                            
                                            if len(resultados['sin_email']) > 0:
                                                st.warning(f"📧 {len(resultados['sin_email'])} grupos no recibieron emails por falta de dirección de email")
                                                with st.expander(f"Ver grupos sin email ({len(resultados['sin_email'])})", expanded=False):
                                                    for grupo in resultados['sin_email']:
                                                        st.write(f"• {grupo}")
                                                    st.info("💡 Puedes agregar emails en la sección 'Clientes'")
                                            
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
                                    else:
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
                                            st.info("📨 Cada grupo representa una combinación de titular + importancia, enviándose emails separados por importancia")
                                            
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
                                
                                else:
                                    st.warning("⚠️ Configura las credenciales de email para continuar")
                                    if st.button("⚙️ Ir a Configuración", use_container_width=True):
                                        st.session_state.current_page = 'settings'
                                        st.rerun()
                    
                    else:
                        st.success("✅ No hay reportes pendientes de envío")
                        st.info("🎉 Todos los reportes generados han sido enviados exitosamente")
                
                with tab2:
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
                                st.markdown("##### � Gestión de Credenciales")
                                
                                # Obtener credenciales actuales
                                credenciales_actuales = obtener_credenciales_email()
                                
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
                                                            from email_sender import validar_credenciales_email
                                                            if validar_credenciales_email(nuevo_email, nueva_password):
                                                                # Guardar en archivo y session_state
                                                                if save_email_credentials(nuevo_email, nueva_password):
                                                                    st.session_state.email_credentials = {
                                                                        'email': nuevo_email,
                                                                        'password': nueva_password
                                                                    }
                                                                    st.session_state.email_config = {
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
                                                            from email_sender import validar_credenciales_email
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
                                
                                st.markdown("##### �📝 Plantillas de Mensaje")
                                st.markdown("Los mensajes se personalizan automáticamente según la importancia:")
                                st.markdown("🔴 **Alta**: Mensaje urgente")
                                st.markdown("🟡 **Media**: Mensaje informativo")
                                st.markdown("🟢 **Baja**: Mensaje estándar")
                                
                                st.markdown("##### 📊 Estado del Sistema")
                                if stats['pendientes_revision'] == 0:
                                    st.success("✅ Sistema listo para envíos")
                                else:
                                    st.warning(f"⚠️ {stats['pendientes_revision']} reportes necesitan revisión")
                
                with tab3:
                            st.markdown("### 📊 Historial de Envíos")
                            
                            # Consultar historial de envíos
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT b.titular, b.numero_boletin, b.fecha_envio_reporte, 
                                           b.importancia, c.email
                                    FROM boletines b
                                    LEFT JOIN clientes c ON b.titular = c.titular
                                    WHERE b.reporte_enviado = 1 
                                    ORDER BY b.fecha_envio_reporte DESC
                                    LIMIT 100
                                """)
                                historial_envios = cursor.fetchall()
                                cursor.close()
                                
                                if historial_envios:
                                    historial_df = pd.DataFrame(historial_envios, 
                                        columns=['Titular', 'Boletín', 'Fecha Envío', 'Importancia', 'Email'])
                                    
                                    # Formatear fecha
                                    historial_df['Fecha Envío'] = pd.to_datetime(historial_df['Fecha Envío']).dt.strftime('%d/%m/%Y %H:%M')
                                    
                                    st.dataframe(historial_df, use_container_width=True)
                                    
                                    # Estadísticas del historial
                                    st.markdown("##### 📈 Estadísticas de Envíos")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        total_enviados = len(historial_df)
                                        st.metric("📧 Total Enviados", total_enviados)
                                    with col2:
                                        hoy = datetime.now().date()
                                        enviados_hoy = len(historial_df[pd.to_datetime(historial_df['Fecha Envío']).dt.date == hoy])
                                        st.metric("📅 Enviados Hoy", enviados_hoy)
                                    with col3:
                                        importancia_alta = len(historial_df[historial_df['Importancia'] == 'Alta'])
                                        st.metric("🔴 Importancia Alta", importancia_alta)
                                else:
                                    st.info("📭 No hay envíos registrados")
                            
                            except Exception as e:
                                st.error(f"Error al cargar historial: {e}")
                
                with tab4:
                            st.markdown("### 📋 Logs Detallados de Envíos")
                            
                            # Estadísticas de logs
                            try:
                                stats_logs = obtener_estadisticas_logs(conn)
                                
                                # Dashboard de estadísticas de logs
                                st.subheader("📊 Estadísticas de Logs")
                                col1, col2, col3, col4, col5 = st.columns(5)
                                with col1:
                                    st.metric("📧 Total Envíos", stats_logs['total_envios'])
                                with col2:
                                    st.metric("✅ Exitosos", stats_logs['exitosos'])
                                with col3:
                                    st.metric("❌ Fallidos", stats_logs['fallidos'])
                                with col4:
                                    st.metric("📤 Hoy", stats_logs['envios_hoy'])
                                with col5:
                                    tasa_exito = stats_logs['tasa_exito']
                                    color = "normal" if tasa_exito >= 80 else "inverse"
                                    st.metric("📈 Tasa Éxito", f"{tasa_exito:.1f}%")
                                
                                # Filtros para logs
                                st.markdown("---")
                                col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                                with col_filtro1:
                                    filtro_estado_log = st.selectbox(
                                        "🔍 Filtrar por Estado",
                                        ["Todos", "exitoso", "fallido", "sin_email", "sin_archivo"],
                                        index=0
                                    )
                                with col_filtro2:
                                    filtro_titular_log = st.text_input(
                                        "🏢 Filtrar por Titular",
                                        placeholder="Nombre del titular..."
                                    )
                                with col_filtro3:
                                    limite_logs = st.selectbox(
                                        "📄 Mostrar últimos",
                                        [50, 100, 200, 500],
                                        index=1
                                    )
                                
                                # Obtener logs con filtros
                                estado_filtro = None if filtro_estado_log == "Todos" else filtro_estado_log
                                titular_filtro = filtro_titular_log if filtro_titular_log else None
                                
                                logs_rows, logs_columns = obtener_logs_envios(
                                    conn, 
                                    limite=limite_logs,
                                    filtro_estado=estado_filtro,
                                    filtro_titular=titular_filtro
                                )
                                
                                if logs_rows:
                                    logs_df = pd.DataFrame(logs_rows, columns=logs_columns)
                                    
                                    # Formatear fecha
                                    logs_df['fecha_envio'] = pd.to_datetime(logs_df['fecha_envio']).dt.strftime('%d/%m/%Y %H:%M:%S')
                                    
                                    # Personalizar colores por estado
                                    def colorear_estado(val):
                                        if val == 'exitoso':
                                            return 'background-color: #d4edda; color: #155724'
                                        elif val == 'fallido':
                                            return 'background-color: #f8d7da; color: #721c24'
                                        elif val == 'sin_email':
                                            return 'background-color: #fff3cd; color: #856404'
                                        elif val == 'sin_archivo':
                                            return 'background-color: #e2e3e5; color: #383d41'
                                        return ''
                                    
                                    # Aplicar estilos
                                    styled_df = logs_df.style.applymap(colorear_estado, subset=['estado'])
                                    
                                    # Mostrar tabla
                                    st.dataframe(styled_df, use_container_width=True, height=400)
                                    
                                    # Información de la tabla
                                    st.info(f"📊 Mostrando {len(logs_df)} registros de logs")
                                    
                                    # Análisis por importancia
                                    if stats_logs['por_importancia']:
                                        st.markdown("##### 📊 Envíos Exitosos por Importancia")
                                        col_imp1, col_imp2, col_imp3 = st.columns(3)
                                        
                                        por_importancia = stats_logs['por_importancia']
                                        with col_imp1:
                                            alta = por_importancia.get('Alta', 0)
                                            st.metric("🔴 Alta", alta)
                                        with col_imp2:
                                            media = por_importancia.get('Media', 0)
                                            st.metric("🟡 Media", media)
                                        with col_imp3:
                                            baja = por_importancia.get('Baja', 0)
                                            st.metric("🟢 Baja", baja)
                                    
                                    # Herramientas de administración
                                    st.markdown("---")
                                    st.markdown("##### 🔧 Herramientas de Administración")
                                    col_admin1, col_admin2, col_admin3 = st.columns(3)
                                    
                                    with col_admin1:
                                        if st.button("🗑️ Limpiar Logs Antiguos (30+ días)", use_container_width=True):
                                            try:
                                                eliminados = limpiar_logs_antiguos(conn, 30)
                                                if eliminados > 0:
                                                    st.success(f"✅ {eliminados} logs antiguos eliminados")
                                                else:
                                                    st.info("ℹ️ No hay logs antiguos para eliminar")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error al limpiar logs: {e}")
                                    
                                    with col_admin2:
                                        if st.button("🔧 Optimizar Archivo Log", use_container_width=True):
                                            try:
                                                resultado = optimizar_archivo_log()
                                                if "optimizado" in resultado.lower():
                                                    st.success(f"✅ {resultado}")
                                                else:
                                                    st.info(f"ℹ️ {resultado}")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error al optimizar: {e}")
                                    
                                    with col_admin3:
                                        if st.button("📊 Exportar Logs", use_container_width=True):
                                            # Preparar CSV para descarga
                                            csv = logs_df.to_csv(index=False)
                                            st.download_button(
                                                label="💾 Descargar CSV",
                                                data=csv,
                                                file_name=f"logs_envios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                                mime="text/csv",
                                                use_container_width=True
                                            )
                                
                                # Información del Sistema de Limpieza Automática
                                st.markdown("---")
                                st.markdown("##### 🤖 Sistema de Limpieza Automática")
                                
                                try:
                                    config_logs = configurar_limpieza_logs()
                                    
                                    # Mostrar configuración actual
                                    col_config1, col_config2, col_config3 = st.columns(3)
                                    
                                    with col_config1:
                                        st.markdown("**📋 Configuración Actual:**")
                                        st.info(f"🗑️ Logs exitosos: {config_logs['dias_conservar_exitosos']} días")
                                        st.info(f"❌ Logs de errores: {config_logs['dias_conservar_errores']} días")
                                        st.info(f"🔄 Frecuencia limpieza: {config_logs['frecuencia_limpieza_dias']} días")
                                    
                                    with col_config2:
                                        st.markdown("**📊 Estado del Sistema:**")
                                        st.metric("📁 Tamaño del Log", f"{config_logs['tamaño_actual_mb']} MB")
                                        st.info(f"🔧 Auto-optimización: {config_logs['tamaño_auto_optimizacion_mb']} MB")
                                        
                                        # Color del estado según el tamaño
                                        if config_logs['tamaño_actual_mb'] > config_logs['tamaño_auto_optimizacion_mb']:
                                            st.error("⚠️ Log necesita optimización")
                                        elif config_logs['tamaño_actual_mb'] > config_logs['tamaño_maximo_mb']:
                                            st.warning("📈 Log creciendo")
                                        else:
                                            st.success("✅ Log en buen estado")
                                    
                                    with col_config3:
                                        st.markdown("**🕐 Última Actividad:**")
                                        st.info(f"🧹 Última limpieza: {config_logs['ultima_limpieza']}")
                                        
                                        # Mostrar resultado de la limpieza automática si está disponible
                                        if 'resultado_limpieza_automatica' in st.session_state:
                                            resultado = st.session_state.resultado_limpieza_automatica
                                            if resultado['logs_eliminados'] > 0:
                                                st.success(f"🤖 Último ciclo: {resultado['logs_eliminados']} logs eliminados")
                                            else:
                                                st.info("🤖 Sistema funcionando normalmente")
                                
                                except Exception as e:
                                    st.error(f"Error al cargar configuración: {e}")
                                
                                # Información educativa sobre el sistema automático
                                with st.expander("ℹ️ Información del Sistema Automático", expanded=False):
                                    st.markdown("""
                                    **🤖 Funcionamiento Automático:**
                                    
                                    - **Cada 7 días**: Se ejecuta limpieza automática de logs antiguos
                                    - **Al superar 100MB**: El archivo se optimiza automáticamente creando respaldos
                                    - **Cada 90 días**: Los respaldos muy antiguos se eliminan automáticamente
                                    
                                    **🔧 Qué se conserva:**
                                    - ✅ **Errores**: Se conservan por 1 año (importantes para debugging)
                                    - ✅ **Logs recientes**: Últimos 30 días de actividad
                                    - ✅ **Respaldos**: Últimos 90 días de archivos optimizados
                                    
                                    **🗑️ Qué se elimina:**
                                    - ❌ **Logs exitosos antiguos**: Mayores a 30 días
                                    - ❌ **Respaldos antiguos**: Mayores a 90 días
                                    - ❌ **Archivos de log grandes**: Se comprimen manteniendo información crítica
                                    
                                    **⚡ Beneficios:**
                                    - Mejor rendimiento de la aplicación
                                    - Menor uso de espacio en disco
                                    - Logs más fáciles de revisar
                                    - Mantenimiento automático sin intervención manual
                                    """)
                                
                            except Exception as e:
                                st.error(f"Error al cargar logs: {e}")
                
                with tab5:
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
                                                st.markdown(f"**⚡ Importancia:** {email['importancia']}")
                                            
                                            with col_info2:
                                                # Mostrar boletines incluidos
                                                if email['numeros_boletines']:
                                                    st.markdown(f"**📋 Boletines:**")
                                                    boletines_str = ', '.join(email['numeros_boletines'])
                                                    if len(boletines_str) > 50:
                                                        st.markdown(f"- {boletines_str[:50]}...")
                                                    else:
                                                        st.markdown(f"- {boletines_str}")
                                                
                                                # Buscar archivo PDF
                                                ruta_pdf = obtener_ruta_reporte_pdf(email['titular'], email['fecha_envio'])
                                                
                                                if ruta_pdf and os.path.exists(ruta_pdf):
                                                    st.markdown(f"**📄 Archivo:** {os.path.basename(ruta_pdf)}")
                                                    
                                                    # Botón para descargar PDF
                                                    try:
                                                        with open(ruta_pdf, "rb") as pdf_file:
                                                            pdf_data = pdf_file.read()
                                                        
                                                        # Crear clave única usando titular + importancia + fecha
                                                        unique_key = f"download_pdf_{email['titular']}_{email['importancia']}_{email['fecha_envio'].replace(':', '').replace('-', '').replace(' ', '')}"
                                                        
                                                        st.download_button(
                                                            label="📥 Descargar PDF",
                                                            data=pdf_data,
                                                            file_name=os.path.basename(ruta_pdf),
                                                            mime="application/pdf",
                                                            use_container_width=True,
                                                            key=unique_key
                                                        )
                                                    except Exception as e:
                                                        st.error(f"Error al cargar PDF: {e}")
                                                else:
                                                    st.warning("📄 Archivo PDF no encontrado")
                                            
                                            # Mostrar números de boletines si hay muchos
                                            if email['numeros_boletines'] and len(email['numeros_boletines']) > 5:
                                                st.markdown("---")
                                                st.markdown(f"**📋 Boletines Incluidos ({len(email['numeros_boletines'])}):**")
                                                
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
                
                # Cerrar el contenedor de gestión de emails
                st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                st.error("Error al obtener estadísticas de envíos")
        
        except Exception as e:
            st.error(f"Error al cargar la sección de emails: {e}")
        finally:
            conn.close()
    
    else:
        st.error("No se pudo conectar a la base de datos")

elif st.session_state.current_page == 'settings':
    show_settings_page()

else:
    # Si se están mostrando modales, no mostrar el contenido principal
    pass