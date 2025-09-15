"""
Página de gestión de marcas
"""
import streamlit as st
import pandas as pd
import sys
import os
import time

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, obtener_marcas, insertar_marca, actualizar_marca, eliminar_marca, obtener_clientes
from src.services.grid_service import GridService
from src.ui.components import UIComponents


def validate_integer(value, allow_empty=False):
    """Validar que un valor sea un entero"""
    if allow_empty and (value is None or value == ""):
        return True
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def show_marcas_page():
    """Mostrar la página de gestión de marcas"""
    st.title("🏷️ Gestión de Marcas")
    
    # Cargar datos de marcas
    conn = crear_conexion()
    if conn:
        try:
            # Obtener datos actualizados
            marcas_data, marcas_columns = obtener_marcas(conn)
            
            if marcas_data:
                df_marcas = pd.DataFrame(marcas_data, columns=marcas_columns)
                st.session_state.marcas_data = df_marcas
                
                # Estilos personalizados para pestañas
                st.markdown("""
                <style>
                /* Estilos personalizados para pestañas de marcas */
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
                
                /* Lista de Marcas - Verde */
                .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                }
                
                /* Agregar Marca - Azul */
                .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
                }
                
                /* Estadísticas - Morado */
                .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {
                    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                    color: white;
                    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
                }
                """
                , unsafe_allow_html=True)
                
                # Crear pestañas
                tab1, tab2 = st.tabs(["📋 Lista de Marcas", "➕ Agregar Marca"])
                
                with tab1:
                    st.subheader("📋 Lista Completa de Marcas")
                    st.info("💡 **Instrucciones:** Selecciona una marca para editarla o eliminarla. Utiliza los filtros para buscar marcas específicas.")
                    
                    # Filtros para marcas
                    with st.expander("🔍 Filtros de Búsqueda", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            filtro_marca = st.text_input("🏷️ Marca", placeholder="Buscar marca...")
                            filtro_codigo = st.text_input("📝 Código", placeholder="Código de marca...")
                        with col2:
                            filtro_clase = st.text_input("🔢 Clase", placeholder="Clase...")
                            filtro_custodia = st.text_input("🔐 Custodia", placeholder="Custodia...")
                        with col3:
                            filtro_titular = st.text_input("👤 Titular", placeholder="Titular...")
                            filtro_cuit = st.text_input("🆔 CUIT", placeholder="CUIT...")
                        with col4:
                            st.markdown("##### 🎯 Acciones")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            if st.button("🔄 Actualizar Datos", 
                                       key="refresh_marcas",
                                       use_container_width=True,
                                       help="Recargar la lista de marcas desde la base de datos"):
                                # Crear un contenedor para el mensaje
                                mensaje_container = st.empty()
                                
                                with mensaje_container.container():
                                    st.info("⏳ Actualizando datos de marcas desde la base de datos...")
                                
                                # Limpiar cache y recargar
                                if 'marcas_data' in st.session_state:
                                    del st.session_state.marcas_data
                                    
                                # Limpiar cualquier otro cache relacionado
                                for key in list(st.session_state.keys()):
                                    if key.startswith('grid_marcas_'):
                                        del st.session_state[key]
                                
                                time.sleep(0.8)
                                st.rerun()
                    
                    # Aplicar filtros
                    filtered_marcas = df_marcas.copy()
                    
                    if filtro_marca:
                        filtered_marcas = filtered_marcas[filtered_marcas['marca'].str.contains(filtro_marca, case=False, na=False)]
                    if filtro_codigo:
                        filtered_marcas = filtered_marcas[filtered_marcas['codigo_marca'].str.contains(filtro_codigo, case=False, na=False)]
                    if filtro_clase:
                        filtered_marcas = filtered_marcas[filtered_marcas['clase'].astype(str).str.contains(filtro_clase, case=False, na=False)]
                    if filtro_custodia:
                        filtered_marcas = filtered_marcas[filtered_marcas['custodia'].str.contains(filtro_custodia, case=False, na=False)]
                    if filtro_titular:
                        filtered_marcas = filtered_marcas[filtered_marcas['titular'].str.contains(filtro_titular, case=False, na=False)]
                    if filtro_cuit:
                        filtered_marcas = filtered_marcas[filtered_marcas['cuit'].astype(str).str.contains(filtro_cuit, case=False, na=False)]
                    
                    # Mostrar resultados
                    if not filtered_marcas.empty:
                        st.markdown(f"📊 **{len(filtered_marcas)}** marcas de **{len(df_marcas)}** totales")
                        
                        # Crear grid para marcas con columnas personalizadas
                        column_defs = [
                            {"headerName": "ID", "field": "id", "hide": True},
                            {"headerName": "Marca", "field": "marca", "width": 180},
                            {"headerName": "Código", "field": "codigo_marca", "width": 120},
                            {"headerName": "Clase", "field": "clase", "width": 100},
                            {"headerName": "Acta", "field": "acta", "width": 120},
                            {"headerName": "Nro. Concesión", "field": "nrocon", "width": 150},
                            {"headerName": "Custodia", "field": "custodia", "width": 120},
                            {"headerName": "Titular", "field": "titular", "width": 180},
                            {"headerName": "CUIT", "field": "cuit", "width": 140},
                            {"headerName": "Email", "field": "email", "width": 250},  # Columna de email más ancha
                            {"headerName": "Cliente ID", "field": "cliente_id", "width": 120}
                        ]
                        
                        grid_response = GridService.create_grid(
                            filtered_marcas, 
                            'grid_marcas', 
                            height=500,
                            selection_mode='single',
                            fit_columns=False,
                            editable=False,
                            custom_column_defs=column_defs
                        )
                        
                                # Panel de acciones para marca seleccionada
                        if grid_response['selected_rows']:
                            selected_marca = grid_response['selected_rows'][0]
                            
                            with st.container():
                                st.markdown("---")
                                st.markdown(f"### 🎯 Marca Seleccionada: **{selected_marca['marca']}**")
                                
                                # Agregar un botón explícito para eliminar marca
                                delete_col1, delete_col2 = st.columns([3, 1])
                                with delete_col2:
                                    if st.button("🗑️ Eliminar Marca", type="primary", use_container_width=True):
                                        st.session_state['show_delete_dialog'] = True
                                        st.session_state['marca_to_delete'] = selected_marca
                                
                                # Mostrar diálogo de confirmación si se presiona el botón
                                if st.session_state.get('show_delete_dialog', False) and 'marca_to_delete' in st.session_state:
                                    with st.container():
                                        st.warning(f"⚠️ ¿Está seguro que desea eliminar la marca **{st.session_state['marca_to_delete']['marca']}**?")
                                        confirm_col1, confirm_col2 = st.columns(2)
                                        with confirm_col1:
                                            if st.button("❌ Cancelar", use_container_width=True):
                                                st.session_state['show_delete_dialog'] = False
                                                del st.session_state['marca_to_delete']
                                                st.rerun()
                                        with confirm_col2:
                                            if st.button("✅ Confirmar Eliminación", type="primary", use_container_width=True):
                                                try:
                                                    resultado = eliminar_marca(conn, st.session_state['marca_to_delete']['id'])
                                                    if resultado:
                                                        st.success("✅ Marca eliminada correctamente")
                                                        # Limpiar cache y recargar
                                                        if 'marcas_data' in st.session_state:
                                                            del st.session_state['marcas_data']
                                                        st.session_state['show_delete_dialog'] = False
                                                        del st.session_state['marca_to_delete']
                                                        time.sleep(0.8)
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ No se pudo eliminar la marca")
                                                except Exception as e:
                                                    st.error(f"❌ Error al eliminar la marca: {e}")
                                
                                col1, col2, col3 = st.columns(3)                                # Panel Editar Marca
                                with col1:
                                    with st.expander("✏️ Editar Marca", expanded=True):
                                        with st.form(key=f"edit_form_{selected_marca['id']}"):
                                            st.subheader("✏️ Editar Marca")
                                            
                                            # Formulario con los campos actuales
                                            marca_edit = st.text_input("Marca", value=selected_marca['marca'])
                                            codigo_marca_edit = st.text_input("Código de Marca", value=selected_marca['codigo_marca'] if pd.notna(selected_marca['codigo_marca']) else "")
                                            clase_edit = st.number_input("Clase", value=int(selected_marca['clase']) if pd.notna(selected_marca['clase']) else 0, min_value=0, max_value=45)
                                            acta_edit = st.text_input("Acta", value=selected_marca['acta'] if pd.notna(selected_marca['acta']) else "")
                                            nrocon_edit = st.text_input("Nro. Concesión", value=selected_marca['nrocon'] if pd.notna(selected_marca['nrocon']) else "")
                                            custodia_edit = st.text_input("Custodia", value=selected_marca['custodia'] if pd.notna(selected_marca['custodia']) else "")
                                            titular_edit = st.text_input("Titular", value=selected_marca['titular'] if pd.notna(selected_marca['titular']) else "")
                                            cuit_edit = st.text_input("CUIT", value=selected_marca['cuit'] if pd.notna(selected_marca['cuit']) else "")
                                            email_edit = st.text_input("Email", value=selected_marca['email'] if pd.notna(selected_marca['email']) else "")
                                            
                                            # Obtener lista de clientes para vincular
                                            clientes_rows, clientes_cols = obtener_clientes(conn)
                                            if clientes_rows:
                                                clientes_df = pd.DataFrame(clientes_rows, columns=clientes_cols)
                                                clientes_options = [{"label": f"{row['titular']} (CUIT: {row['cuit']})", "value": row['id']} for _, row in clientes_df.iterrows()]
                                                clientes_options.insert(0, {"label": "Sin cliente asignado", "value": None})
                                                
                                                # Encontrar el índice del cliente actual
                                                current_cliente_id = selected_marca['cliente_id'] if pd.notna(selected_marca['cliente_id']) else None
                                                current_index = 0
                                                for i, option in enumerate(clientes_options):
                                                    if option['value'] == current_cliente_id:
                                                        current_index = i
                                                        break
                                                
                                                cliente_id_edit = st.selectbox(
                                                    "Cliente asociado",
                                                    options=[o['value'] for o in clientes_options],
                                                    format_func=lambda x: next((o['label'] for o in clientes_options if o['value'] == x), "Sin cliente asignado"),
                                                    index=current_index
                                                )
                                            else:
                                                cliente_id_edit = None
                                                st.warning("No se encontraron clientes para vincular")
                                            
                                            submit_edit = st.form_submit_button("💾 Guardar Cambios")
                                            
                                            if submit_edit:
                                                try:
                                                    resultado = actualizar_marca(
                                                        conn,
                                                        selected_marca['id'],
                                                        marca_edit,
                                                        codigo_marca_edit,
                                                        clase_edit,
                                                        acta_edit,
                                                        custodia_edit,
                                                        cuit_edit,
                                                        titular_edit,
                                                        nrocon_edit,
                                                        email_edit,
                                                        cliente_id_edit
                                                    )
                                                    
                                                    if resultado:
                                                        st.success(f"✅ Marca '{marca_edit}' actualizada correctamente")
                                                        time.sleep(1)
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ No se pudo actualizar la marca. Verifique los datos ingresados.")
                                                except Exception as e:
                                                    st.error(f"❌ Error al actualizar la marca: {e}")
                                
                                # Panel Ver Detalles
                                with col2:
                                    with st.expander("🔍 Detalles de la Marca", expanded=True):
                                        st.markdown("### 📝 Información de la Marca")
                                        
                                        # Crear tarjetas con datos de la marca
                                        st.markdown("""
                                        <style>
                                        .info-card {
                                            background-color: #2d2d2d;
                                            border-radius: 10px;
                                            padding: 15px;
                                            margin-bottom: 10px;
                                            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                                        }
                                        .info-card h4 {
                                            margin: 0;
                                            color: #10b981;
                                            font-size: 14px;
                                        }
                                        .info-card p {
                                            margin: 5px 0 0 0;
                                            font-size: 16px;
                                            color: #e5e5e5;
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                        
                                        col_a, col_b = st.columns(2)
                                        
                                        with col_a:
                                            st.markdown(f"""
                                            <div class="info-card">
                                                <h4>MARCA</h4>
                                                <p>{selected_marca['marca'] if pd.notna(selected_marca['marca']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>CÓDIGO</h4>
                                                <p>{selected_marca['codigo_marca'] if pd.notna(selected_marca['codigo_marca']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>CLASE</h4>
                                                <p>{selected_marca['clase'] if pd.notna(selected_marca['clase']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>ACTA</h4>
                                                <p>{selected_marca['acta'] if pd.notna(selected_marca['acta']) else 'N/A'}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                        with col_b:
                                            st.markdown(f"""
                                            <div class="info-card">
                                                <h4>TITULAR</h4>
                                                <p>{selected_marca['titular'] if pd.notna(selected_marca['titular']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>CUIT</h4>
                                                <p>{selected_marca['cuit'] if pd.notna(selected_marca['cuit']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>CUSTODIA</h4>
                                                <p>{selected_marca['custodia'] if pd.notna(selected_marca['custodia']) else 'N/A'}</p>
                                            </div>
                                            
                                            <div class="info-card">
                                                <h4>CONCESIÓN</h4>
                                                <p>{selected_marca['nrocon'] if pd.notna(selected_marca['nrocon']) else 'N/A'}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                        # Cliente vinculado
                                        cliente_info = "Sin cliente asignado"
                                        if pd.notna(selected_marca['cliente_id']):
                                            # Buscar nombre del cliente
                                            clientes_rows, _ = obtener_clientes(conn)
                                            clientes_df = pd.DataFrame(clientes_rows, columns=clientes_cols)
                                            cliente = clientes_df[clientes_df['id'] == selected_marca['cliente_id']]
                                            if not cliente.empty:
                                                cliente_info = f"{cliente.iloc[0]['titular']} (ID: {cliente.iloc[0]['id']})"
                                        
                                        st.markdown(f"""
                                        <div class="info-card" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border-left: 5px solid #10b981;">
                                            <h4>CLIENTE ASOCIADO</h4>
                                            <p>{cliente_info}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                # Panel de información adicional (en lugar del panel eliminar)
                                with col3:
                                    with st.expander("ℹ️ Información Adicional", expanded=True):
                                        st.markdown("### ℹ️ Detalles de la Marca")
                                        
                                        # Mostrar información de la marca
                                        st.markdown(f"""
                                        - **ID:** {selected_marca['id']}
                                        - **Marca:** {selected_marca['marca']}
                                        - **Código:** {selected_marca['codigo_marca'] if pd.notna(selected_marca['codigo_marca']) else "N/A"}
                                        - **Clase:** {selected_marca['clase']}
                                        - **Acta:** {selected_marca['acta'] if pd.notna(selected_marca['acta']) else "N/A"}
                                        - **Nro. Concesión:** {selected_marca['nrocon'] if pd.notna(selected_marca['nrocon']) else "N/A"}
                                        - **Titular:** {selected_marca['titular']}
                                        - **CUIT:** {selected_marca['cuit']}
                                        - **Email:** {selected_marca['email'] if pd.notna(selected_marca['email']) else "N/A"}
                                        - **Cliente ID:** {selected_marca['cliente_id'] if pd.notna(selected_marca['cliente_id']) else "No vinculado"}
                                        """)
                    else:
                        st.warning("🔍 No se encontraron marcas con los filtros aplicados.")
                
                with tab2:
                    st.subheader("➕ Agregar Nueva Marca")
                    
                
                    
                    # Formulario para agregar nueva marca
                    with st.form(key="form_nueva_marca"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            marca_nueva = st.text_input("Nombre de Marca 🏷️", placeholder="Ingrese nombre de marca")
                            codigo_marca_nueva = st.text_input("Código de Marca �", placeholder="Ingrese código de marca (opcional)")
                            clase_nueva = st.number_input("Clase �", min_value=1, max_value=45, value=35)
                            acta_nueva = st.text_input("Acta 📄", placeholder="Número de acta (opcional)")
                            nrocon_nueva = st.text_input("Nro. Concesión �", placeholder="Número de concesión (opcional)")
                        
                        with col2:
                            custodia_nueva = st.text_input("Custodia �", placeholder="Estado de custodia (opcional)")
                            titular_nueva = st.text_input("Titular 👤", placeholder="Nombre del titular")
                            cuit_nueva = st.text_input("CUIT 🆔", placeholder="CUIT del titular")
                            email_nueva = st.text_input("Email 📧", placeholder="Email de contacto")
                            
                            # Obtener lista de clientes para vincular
                            clientes_rows, clientes_cols = obtener_clientes(conn)
                            clientes_df = pd.DataFrame(clientes_rows, columns=clientes_cols)
                            
                            if not clientes_df.empty:
                                # Crear opciones para el selectbox con ID y nombre
                                opciones_clientes = [("", "Sin vincular")] + [(str(row['id']), row['titular']) for _, row in clientes_df.iterrows()]
                                cliente_labels = [f"{id} - {nombre}" if id else nombre for id, nombre in opciones_clientes]
                                
                                # Mostrar selector
                                cliente_seleccionado_idx = st.selectbox(
                                    "Vincular a Cliente �", 
                                    range(len(opciones_clientes)),
                                    format_func=lambda i: cliente_labels[i]
                                )
                                cliente_id_nueva = opciones_clientes[cliente_seleccionado_idx][0]
                            else:
                                st.warning("No hay clientes disponibles para vincular.")
                                cliente_id_nueva = ""
                        
                        st.markdown("---")
                        col_btn1, col_btn2 = st.columns([1, 3])
                        
                        with col_btn1:
                            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                        with col_btn2:
                            submit_button = st.form_submit_button("💾 Guardar Marca", use_container_width=True)
                        
                        # Procesar formulario
                        if submit_button:
                            if not marca_nueva:
                                st.error("❌ El nombre de la marca es obligatorio")
                            elif not titular_nueva:
                                st.error("❌ El titular es obligatorio")
                            elif not cuit_nueva:
                                st.error("❌ El CUIT es obligatorio")
                            else:
                                try:
                                    # Insertar marca en la base de datos
                                    resultado = insertar_marca(
                                        conn,
                                        marca_nueva,
                                        codigo_marca_nueva,
                                        clase_nueva,
                                        acta_nueva,
                                        custodia_nueva,
                                        titular_nueva,
                                        cuit_nueva,
                                        nrocon_nueva,
                                        email_nueva,
                                        cliente_id_nueva if cliente_id_nueva else None
                                    )
                                    
                                    if resultado:
                                        st.success("✅ Marca agregada correctamente")
                                        
                                        # Limpiar cache para recargar datos
                                        if 'marcas_data' in st.session_state:
                                            del st.session_state.marcas_data
                                        
                                        # Limpiar campos del formulario
                                        st.session_state["form_nueva_marca"] = {}
                                        
                                        # Cambiar a la pestaña de lista
                                        st.session_state["active_tab"] = "Lista de Marcas"
                                        
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error("❌ No se pudo agregar la marca")
                                except Exception as e:
                                    st.error(f"❌ Error al agregar la marca: {e}")

                
            else:
                # No hay datos de marcas
                st.warning("🔍 No se encontraron registros de marcas en la base de datos.")
                
                with st.expander("➕ Agregar primera marca"):
                    with st.form(key="first_marca_form"):
                        st.info("💡 Complete los datos para agregar la primera marca al sistema")
                        
                        marca_nueva = st.text_input("Marca 🏷️", placeholder="Nombre de la marca")
                        titular_nueva = st.text_input("Titular 👤", placeholder="Nombre del titular")
                        clase_nueva = st.number_input("Clase 🔢", min_value=0, max_value=45)
                        cuit_nueva = st.text_input("CUIT 🆔", placeholder="CUIT del titular")
                        
                        submit_button = st.form_submit_button("✅ Agregar Primera Marca")
                        
                        if submit_button:
                            if not marca_nueva:
                                st.error("❌ El nombre de la marca es obligatorio")
                            else:
                                try:
                                    resultado = insertar_marca(
                                        conn,
                                        marca_nueva,
                                        "",  # código_marca
                                        clase_nueva,
                                        "",  # acta
                                        "",  # custodia
                                        cuit_nueva,
                                        titular_nueva
                                    )
                                    
                                    if resultado:
                                        st.success(f"✅ Marca '{marca_nueva}' agregada correctamente")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ No se pudo agregar la marca. Verifique los datos ingresados.")
                                except Exception as e:
                                    st.error(f"❌ Error al agregar la marca: {e}")
                    
        except Exception as e:
            st.error(f"❌ Error al cargar datos de marcas: {e}")
        finally:
            if conn:
                conn.close()
    else:
        st.error("❌ No se pudo conectar a la base de datos")
