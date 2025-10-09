import streamlit as st
import pandas as pd
import time
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from database import crear_conexion, obtener_datos
from src.services.grid_service import GridService


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros avanzados al DataFrame"""
    st.markdown("""
        <style>
        .filter-container {
            background-color: rgba(28, 131, 225, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #1c83e1;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown('#### 🔍 Filtros Avanzados')
    
    # Pestañas para organizar filtros
    tab1, tab2, tab3 = st.tabs(["📋 Información General", "📊 Estados", "🏷️ Clasificación"])
    
    # Variables para filtros
    mask = pd.Series(True, index=df.index)
    
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
        
        # Slider Minimalista de Importancia
        st.markdown("##### 🎯 Nivel de Importancia")
        
        # CSS para el slider minimalista
        st.markdown("""
        <style>
        .importance-slider-container {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .importance-badge {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            margin-left: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .badge-baja { 
            background: linear-gradient(135deg, #10b981, #059669); 
            color: white; 
        }
        .badge-media { 
            background: linear-gradient(135deg, #f59e0b, #d97706); 
            color: white; 
        }
        .badge-alta { 
            background: linear-gradient(135deg, #ef4444, #dc2626); 
            color: white; 
        }
        .badge-pendiente { 
            background: linear-gradient(135deg, #6b7280, #4b5563); 
            color: white; 
        }
        .badge-todas { 
            background: linear-gradient(135deg, #8b5cf6, #7c3aed); 
            color: white; 
        }
        
        .stSelectSlider {
            margin-bottom: 0;
        }
        
        .stSelectSlider > div > div {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="importance-slider-container">', unsafe_allow_html=True)
        
        # Crear el select_slider
        filtro_importancia_slider = st.select_slider(
            "Nivel de Importancia",
            #options=["Todas", "Baja", "Media", "Alta", "Pendiente"],
            options=["Todas", "Baja", "Alta", "Pendiente"],
            value="Todas",
            key="importance_slider",
            help="Desliza para seleccionar el nivel de importancia",
            label_visibility="collapsed"
        )
        
        # Mostrar badge con color según la selección
        color_map = {
            "Todas": "todas",
            "Baja": "baja", 
            "Media": "media",
            "Alta": "alta",
            "Pendiente": "pendiente"
        }
        
        badge_class = f"badge-{color_map[filtro_importancia_slider]}"
        
        st.markdown(f"""
        <div style="text-align: center; margin-top: 0.5rem;">
            <span style="color: #9ca3af; font-size: 0.9rem;">Filtrando por:</span>
            <span class="importance-badge {badge_class}">{filtro_importancia_slider}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🏷️ Clasificación")
            filtro_clase = st.text_input("🔢 Clase", placeholder="Ej: 35, 9, 42...")
            filtro_marca_custodia = st.text_input("🏷️ Marca Custodia", placeholder="Buscar marca...")
        
        with col2:
            st.markdown("##### 📋 Información Adicional")
            filtro_marca_publicada = st.text_input("📢 Marca Publicada", placeholder="Buscar marca publicada...")
            filtro_clases_acta = st.text_input("📄 Clases Acta", placeholder="Buscar en clases...")

    # Aplicar filtros
    if filtro_titular:
        mask &= df['titular'].str.contains(filtro_titular, case=False, na=False)
    if filtro_boletin:
        mask &= df['numero_boletin'].str.contains(filtro_boletin, case=False, na=False)
    if filtro_orden:
        mask &= df['numero_orden'].astype(str).str.contains(filtro_orden, na=False)
    if filtro_solicitante:
        mask &= df['solicitante'].str.contains(filtro_solicitante, case=False, na=False)
    if filtro_agente:
        mask &= df['agente'].str.contains(filtro_agente, case=False, na=False)
    if filtro_expediente:
        mask &= df['numero_expediente'].str.contains(filtro_expediente, na=False)
    
    if filtro_reporte_enviado:
        mask &= (df['reporte_enviado'] == False)
    if filtro_reporte_generado:
        mask &= (df['reporte_generado'] == False)
    
    if filtro_fecha:
        mask &= (pd.to_datetime(df['fecha_boletin']).dt.date == filtro_fecha)
    
    # Aplicar filtro del slider de importancia
    if filtro_importancia_slider != "Todas":
        mask &= (df['importancia'] == filtro_importancia_slider)
    
    # Aplicar filtros adicionales de clasificación
    if 'filtro_clase' in locals() and filtro_clase:
        mask &= df['clase'].str.contains(filtro_clase, case=False, na=False)
    if 'filtro_marca_custodia' in locals() and filtro_marca_custodia:
        mask &= df['marca_custodia'].str.contains(filtro_marca_custodia, case=False, na=False)
    if 'filtro_marca_publicada' in locals() and filtro_marca_publicada:
        mask &= df['marca_publicada'].str.contains(filtro_marca_publicada, case=False, na=False)
    if 'filtro_clases_acta' in locals() and filtro_clases_acta:
        mask &= df['clases_acta'].str.contains(filtro_clases_acta, case=False, na=False)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return df[mask]


def show_historial_page():
    """Muestra la página de historial de boletines."""
    st.title("📊 Historial de Boletines")
    
    # Obtener datos de la base de datos
    try:
        conn = crear_conexion()
        if conn:
            rows, columns = obtener_datos(conn)
            
            if rows:
                # Mostrar métricas
                total_boletines = len(rows)
                st.subheader(f"📈 Métricas Generales")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Boletines", total_boletines)
                
                with col2:
                    # Contar por importancia (índice 15 en la consulta obtener_datos)
                    alta_importancia = len([r for r in rows if len(r) > 15 and r[15] == "Alta"])
                    st.metric("🔴 Alta Importancia", alta_importancia)
                
                with col3:
                    media_importancia = len([r for r in rows if len(r) > 15 and r[15] == "Baja"])
                    st.metric("🟡 Baja Importancia", media_importancia)
                
                with col4:
                    pendientes = len([r for r in rows if len(r) > 15 and r[15] == "Pendiente"])
                    st.metric("⚠️ Pendientes", pendientes)
                
                # Mostrar advertencia si hay registros pendientes
                if pendientes > 0:
                    st.warning(f"⚠️ Hay {pendientes} registros marcados como 'Pendiente'. Puedes cambiar la importancia haciendo clic en la celda correspondiente del grid.")
                
                st.markdown("---")
                
                # Convertir datos a DataFrame
                df = pd.DataFrame(rows, columns=columns)
                
                # Convertir tipos de datos correctamente
                df['reporte_enviado'] = df['reporte_enviado'].astype(bool)
                df['reporte_generado'] = df['reporte_generado'].astype(bool)
                
                # Convertir booleanos a símbolos discretos para mejor presentación
                df_display = df.copy()
                df_display['reporte_enviado'] = df['reporte_enviado'].map({True: '●', False: '○'})
                df_display['reporte_generado'] = df['reporte_generado'].map({True: '●', False: '○'})
                
                # Aplicar filtros
                df_filtered = _apply_filters(df)
                
                # Aplicar la conversión visual también al DataFrame filtrado
                df_filtered_display = df_filtered.copy()
                df_filtered_display['reporte_enviado'] = df_filtered['reporte_enviado'].map({True: '●', False: '○'})
                df_filtered_display['reporte_generado'] = df_filtered['reporte_generado'].map({True: '●', False: '○'})
                
                # Actualizar métricas con datos filtrados
                total_filtrados = len(df_filtered)
                if total_filtrados != total_boletines:
                    st.info(f"📊 Mostrando {total_filtrados} de {total_boletines} registros")
                
                # Mostrar datos en grid usando el servicio de boletines
                st.subheader("📋 Datos del Historial")
                
                # Usar el grid específico para boletines que incluye edición de importancia
                GridService.show_bulletin_grid(
                    df=df_filtered_display,
                    key="historial_grid"
                )
                
            else:
                st.info("📂 No hay datos en la base de datos. Use la sección 'Cargar Datos' para importar boletines.")
                
        else:
            st.error("❌ No se pudo conectar a la base de datos")
            
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
