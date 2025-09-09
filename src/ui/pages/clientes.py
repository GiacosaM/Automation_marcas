"""
Página de gestión de clientes
"""
import streamlit as st
import pandas as pd
import time
import re
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, obtener_clientes, insertar_cliente, actualizar_cliente, eliminar_cliente
from src.services.grid_service import GridService
from src.ui.components import UIComponents


def validate_email_format(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_cuit_format(cuit):
    """Validar formato de CUIT/CUIL (11 dígitos sin guiones)"""
    # Eliminar espacios y guiones para la validación
    cuit_clean = cuit.replace('-', '').replace(' ', '')
    # Verificar que tenga exactamente 11 dígitos y sean todos números
    return cuit_clean.isdigit() and len(cuit_clean) == 11

def format_cuit_for_display(cuit):
    """Formatea el CUIT para mostrar"""
    if not cuit:
        return ""
    # Eliminar cualquier guión o espacio existente
    cuit_clean = cuit.replace('-', '').replace(' ', '')
    if len(cuit_clean) == 11:
        return cuit_clean
    return cuit


def show_clientes_page():
    """Mostrar la página de clientes"""
    st.title("👥 Gestión de Clientes")
    
    # Cargar datos de clientes - forzar datos frescos
    conn = crear_conexion()
    if conn:
        try:
            # Siempre obtener datos actualizados (force_refresh=True)
            rows, columns = obtener_clientes(conn, force_refresh=True)
            
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
                
                /* Botón Actualizar Datos Profesional */
                button[key="refresh_clientes"] {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 12px !important;
                    padding: 0.75rem 1.5rem !important;
                    font-weight: 700 !important;
                    font-size: 0.9rem !important;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
                    transition: all 0.3s ease !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.8px !important;
                }
                
                button[key="refresh_clientes"]:hover {
                    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
                    transform: translateY(-3px) !important;
                }
                
                button[key="refresh_clientes"]:active {
                    transform: translateY(-1px) !important;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Inicializar el índice de la pestaña activa si no existe
                if 'active_tab_index' not in st.session_state:
                    st.session_state.active_tab_index = 0  # Por defecto, la primera pestaña (lista)
                
                # Verificar si hay una solicitud para cambiar de pestaña
                if 'switch_to_list' in st.session_state and st.session_state.switch_to_list:
                    st.session_state.active_tab_index = 0  # Cambiar a la pestaña de lista
                    st.session_state.switch_to_list = False  # Limpiar el flag
                    
                    # Forzar limpieza de caché de datos para mostrar información actualizada
                    if 'clientes_data' in st.session_state:
                        del st.session_state['clientes_data']
                
                # Si viene de agregar un cliente y pidió agregar otro
                if 'switch_to_add' in st.session_state and st.session_state.switch_to_add:
                    st.session_state.active_tab_index = 1  # Cambiar a la pestaña de agregar
                    st.session_state.switch_to_add = False  # Limpiar el flag
                
                # Solo dos pestañas: Lista Editable y Agregar Cliente (usando el índice guardado)
                tab_names = ["📋 Lista de Clientes (Editable)", "➕ Agregar Cliente"]
                tab1, tab2 = st.tabs(tab_names)
                
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
                            filtro_provincia_cliente = st.text_input("🗺️ Provincia", placeholder="Provincia...")
                            filtro_cuit_cliente = st.text_input("🆔 CUIT", placeholder="CUIT...")
                            # Filtro para clientes con/sin marcas
                            filtro_marcas = st.selectbox(
                                "🏷️ Marcas",
                                options=["Todos", "Con marcas", "Sin marcas"],
                                index=0,
                                help="Filtrar clientes con o sin marcas vinculadas"
                            )
                        with col4:
                            st.markdown("##### 🎯 Acciones")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            if st.button("🔄 Actualizar Datos", 
                                       key="refresh_clientes",
                                       use_container_width=True,
                                       help="Recargar la lista de clientes desde la base de datos"):
                                # Crear un contenedor para el mensaje
                                mensaje_container = st.empty()
                                
                                with mensaje_container.container():
                                    st.info("⏳ Actualizando datos de clientes desde la base de datos...")
                                
                                # Limpiar cache y recargar - más intensivo
                                if 'clientes_data' in st.session_state:
                                    del st.session_state['clientes_data']
                                    
                                # Limpiar cualquier otro cache relacionado
                                for key in list(st.session_state.keys()):
                                    if key.startswith('grid_clientes_'):
                                        del st.session_state[key]
                                
                                # Pequeña pausa para asegurar la limpieza del caché
                                time.sleep(0.8)
                                
                                # Recargar la página para mostrar datos frescos
                                st.rerun()
                    
                    # Aplicar filtros
                    filtered_clientes = df_clientes.copy()
                    
                    if filtro_titular_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['titular'].str.contains(filtro_titular_cliente, case=False, na=False)]
                    if filtro_email_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['email'].str.contains(filtro_email_cliente, case=False, na=False)]
                    if filtro_telefono_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['telefono'].astype(str).str.contains(filtro_telefono_cliente, case=False, na=False)]
                    if filtro_ciudad_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['ciudad'].str.contains(filtro_ciudad_cliente, case=False, na=False)]
                    if filtro_provincia_cliente:
                        # Manejar valores None en provincia
                        mask_provincia = filtered_clientes['provincia'].fillna('').str.contains(filtro_provincia_cliente, case=False, na=False)
                        filtered_clientes = filtered_clientes[mask_provincia]
                    if filtro_cuit_cliente:
                        filtered_clientes = filtered_clientes[filtered_clientes['cuit'].astype(str).str.contains(filtro_cuit_cliente, case=False, na=False)]
                    
                    # Aplicar filtro de marcas
                    if filtro_marcas != "Todos":
                        if filtro_marcas == "Con marcas":
                            filtered_clientes = filtered_clientes[filtered_clientes['tiene_marcas'] == 1]
                        else:  # "Sin marcas"
                            filtered_clientes = filtered_clientes[filtered_clientes['tiene_marcas'] == 0]
                    
                    # Mostrar resultados - TABLA EDITABLE
                    if not filtered_clientes.empty:
                        st.markdown(f"📊 **{len(filtered_clientes)}** clientes de **{len(df_clientes)}** totales")
                        
                        # GRILLA EDITABLE
                        grid_response = GridService.show_client_grid(filtered_clientes, 'grid_clientes_editable')
                        
                        # PROCESAR CAMBIOS EN TIEMPO REAL
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
                                    
                                    for column in ['titular', 'email', 'telefono', 'direccion', 'ciudad', 'provincia', 'cuit']:
                                        # Normalizar valores para comparación (manejar NaN y None)
                                        valor_nuevo = str(row[column]) if pd.notna(row[column]) else ""
                                        valor_original = str(original_row[column]) if pd.notna(original_row[column]) else ""
                                        
                                        if valor_nuevo != valor_original:
                                            cambios = True
                                            campos_cambiados.append(column)
                                    
                                    if cambios:
                                        # Actualizar en la base de datos
                                        try:
                                            # Verificar si se está modificando el CUIT (posible vinculación de marcas)
                                            cuit_modificado = 'cuit' in campos_cambiados
                                            
                                            # Crear un contenedor para los mensajes
                                            mensaje_container = st.empty()
                                            
                                            # Si se modificó el CUIT, mostrar un mensaje especial
                                            if cuit_modificado:
                                                with mensaje_container.container():
                                                    st.info("⏳ Actualizando CUIT y vinculaciones de marcas...")
                                            else:
                                                with mensaje_container.container():
                                                    st.info(f"⏳ Actualizando cliente '{row['titular']}'...")
                                            
                                            # Aplicar la actualización en la base de datos
                                            resultado = actualizar_cliente(
                                                conn, 
                                                row['id'], 
                                                row['titular'] if pd.notna(row['titular']) else "", 
                                                row['email'] if pd.notna(row['email']) else "", 
                                                row['telefono'] if pd.notna(row['telefono']) else "", 
                                                row['direccion'] if pd.notna(row['direccion']) else "", 
                                                row['ciudad'] if pd.notna(row['ciudad']) else "", 
                                                row['provincia'] if pd.notna(row['provincia']) else "", 
                                                row['cuit'] if pd.notna(row['cuit']) else ""
                                            )
                                            
                                            mensaje = f"✅ Cliente '{row['titular']}' actualizado: {', '.join(campos_cambiados)}"
                                            
                                            # Mensaje especial si se modificó el CUIT (posible vinculación)
                                            if cuit_modificado:
                                                mensaje += "\n\n⚠️ Se actualizaron las vinculaciones de marcas"
                                                # Forzar limpieza del caché de datos
                                                if 'clientes_data' in st.session_state:
                                                    del st.session_state['clientes_data']
                                            
                                            # Mostrar mensaje de éxito y dar tiempo para que el usuario lo vea
                                            with mensaje_container.container():
                                                st.success(mensaje)
                                                # Limpiar otros cachés relacionados
                                                for key in list(st.session_state.keys()):
                                                    if key.startswith('grid_clientes_'):
                                                        del st.session_state[key]
                                                # Dar tiempo para que el usuario vea el mensaje
                                                time.sleep(1.5)
                                                
                                            # Forzar recarga completa para mostrar cambios
                                            st.rerun()
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
                                    if st.button("� Ver Boletines", type="secondary", use_container_width=True):
                                        st.info("📋 Funcionalidad próximamente")
                                with col3:
                                    if st.button("📄 Generar Reporte", type="secondary", use_container_width=True):
                                        st.info("📄 Funcionalidad próximamente")
                                with col4:
                                    if st.button("🗑️ Eliminar Cliente", type="secondary", use_container_width=True):
                                        # Confirmar eliminación
                                        if st.button("⚠️ Confirmar Eliminación", type="primary"):
                                            # Crear un contenedor para los mensajes
                                            mensaje_container = st.empty()
                                            
                                            with mensaje_container.container():
                                                st.info(f"⏳ Eliminando cliente '{selected_client['titular']}' y desvinculando marcas asociadas...")
                                            
                                            try:
                                                resultado = eliminar_cliente(conn, selected_client['id'])
                                                
                                                if resultado["success"]:
                                                    cliente = resultado["cliente"]
                                                    marcas = resultado["marcas_desvinculadas"]
                                                    
                                                    mensaje = f"✅ Cliente '{cliente}' eliminado correctamente"
                                                    if marcas > 0:
                                                        mensaje += f"\n\n🏷️ {marcas} marcas han sido desvinculadas"
                                                    
                                                    # Mostrar el mensaje de éxito
                                                    with mensaje_container.container():
                                                        st.success(mensaje)
                                                    
                                                    # Forzar limpieza completa del caché
                                                    if 'clientes_data' in st.session_state:
                                                        del st.session_state['clientes_data']
                                                    
                                                    # Limpiar cualquier otro cache relacionado
                                                    for key in list(st.session_state.keys()):
                                                        if key.startswith('grid_clientes_'):
                                                            del st.session_state[key]
                                                    
                                                    # Dar tiempo para que el usuario vea el mensaje
                                                    time.sleep(1.5)
                                                    
                                                    # Recargar la página para mostrar los cambios
                                                    st.rerun()
                                                else:
                                                    with mensaje_container.container():
                                                        st.error(f"❌ Error: {resultado.get('error', 'Error desconocido')}")
                                            except Exception as e:
                                                with mensaje_container.container():
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
                    if 'form_provincia' not in st.session_state:
                        st.session_state.form_provincia = ""
                    if 'form_direccion' not in st.session_state:
                        st.session_state.form_direccion = ""
                    
                    with st.form("form_nuevo_cliente", clear_on_submit=True):
                        # Información básica
                        st.markdown("##### 📄 Información Básica")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nuevo_titular = st.text_input("🏢 Titular *", 
                                                        key="input_titular",
                                                        value=st.session_state.form_titular,
                                                        placeholder="Nombre o razón social")
                            nuevo_email = st.text_input("📧 Email *", 
                                                       key="input_email",
                                                       value=st.session_state.form_email,
                                                       placeholder="cliente@ejemplo.com")
                        with col2:
                            nuevo_telefono = st.text_input("📞 Teléfono", 
                                                          key="input_telefono",
                                                          value=st.session_state.form_telefono,
                                                          placeholder="+54 9 11 1234-5678")
                            nuevo_cuit = st.text_input("🆔 CUIT/CUIL *", 
                                                      key="input_cuit",
                                                      value=st.session_state.form_cuit,
                                                      placeholder="30712353569")
                        with col3:
                            nueva_ciudad = st.text_input("🏙️ Ciudad", 
                                                        value=st.session_state.form_ciudad,
                                                        placeholder="Buenos Aires")
                            nueva_provincia = st.text_input("🗺️ Provincia", 
                                                           value=st.session_state.form_provincia,
                                                           placeholder="Buenos Aires")
                            
                        # Dirección completa
                        st.markdown("##### 📍 Dirección")
                        nueva_direccion = st.text_area("🏠 Dirección Completa", 
                                                      value=st.session_state.form_direccion,
                                                      placeholder="Calle, número, piso, departamento, código postal", 
                                                      height=80)
                        
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
                                "💾 GUARDAR CLIENTE",
                                type="primary", 
                                use_container_width=True,
                                help="Haz clic para agregar este cliente a la base de datos"
                            )
                        
                        if submitted:
                            # Crear contenedor para los mensajes de estado
                            status_container = st.empty()
                            
                            # Guardar los valores actuales para referencias
                            current_values = {
                                'titular': nuevo_titular,
                                'email': nuevo_email,
                                'telefono': nuevo_telefono,
                                'cuit': nuevo_cuit,
                                'ciudad': nueva_ciudad,
                                'provincia': nueva_provincia,
                                'direccion': nueva_direccion
                            }
                            
                            # Actualizar session_state con los valores actuales
                            st.session_state.form_titular = nuevo_titular
                            st.session_state.form_email = nuevo_email
                            st.session_state.form_telefono = nuevo_telefono
                            st.session_state.form_cuit = nuevo_cuit
                            st.session_state.form_ciudad = nueva_ciudad
                            st.session_state.form_provincia = nueva_provincia
                            st.session_state.form_direccion = nueva_direccion
                            
                            if nuevo_titular and nuevo_email and nuevo_cuit:
                                # Validar formato de email y CUIT
                                email_valido = validate_email_format(nuevo_email)
                                cuit_valido = validate_cuit_format(nuevo_cuit)
                                
                                if not email_valido:
                                    with status_container.container():
                                        st.error("⚠️ El formato del email no es válido. Por favor, ingrese un email correcto.")
                                elif not cuit_valido:
                                    with status_container.container():
                                        st.error("⚠️ El formato del CUIT no es válido. Debe contener 11 dígitos sin guiones (ej: 30712353569).")
                                else:
                                    try:
                                        # Mostrar mensaje de procesamiento
                                        with status_container.container():
                                            st.info("⏳ Procesando el nuevo cliente...")
                                        
                                        # Formatear el CUIT (eliminar guiones y espacios)
                                        cuit_formateado = format_cuit_for_display(nuevo_cuit)
                                        
                                        # Verificar si ya existe un cliente con ese titular
                                        cursor = conn.cursor()
                                        cursor.execute("SELECT COUNT(*) FROM clientes WHERE titular = ?", (nuevo_titular,))
                                        existe = cursor.fetchone()[0] > 0
                                        cursor.close()
                                        
                                        if existe:
                                            with status_container.container():
                                                st.error("⚠️ Ya existe un cliente con ese titular. Use un nombre diferente.")
                                        else:
                                            # Insertar el nuevo cliente con el CUIT formateado
                                            nuevo_cliente_id = insertar_cliente(
                                                conn, nuevo_titular, nuevo_email, nuevo_telefono, 
                                                nueva_direccion, nueva_ciudad, nueva_provincia, cuit_formateado
                                            )
                                            
                                            # Mostrar mensaje de éxito con detalles
                                            with status_container.container():
                                                st.success(f"""
                                                ✅ **¡Cliente agregado correctamente!**
                                                
                                                **Titular:** {nuevo_titular}  
                                                **Email:** {nuevo_email}  
                                                **CUIT:** {nuevo_cuit if nuevo_cuit else "No especificado"}
                                                
                                                *Se ha añadido a la lista de clientes con ID #{nuevo_cliente_id}*
                                                """)
                                            
                                            # Limpiar todos los campos del formulario
                                            st.session_state.form_titular = ""
                                            st.session_state.form_email = ""
                                            st.session_state.form_telefono = ""
                                            st.session_state.form_cuit = ""
                                            st.session_state.form_ciudad = ""
                                            st.session_state.form_provincia = ""
                                            st.session_state.form_direccion = ""
                                            
                                            # Configurar los flags y limpiar cache para la siguiente acción
                                            # Limpiar caché de datos para actualizarlos
                                            if 'clientes_data' in st.session_state:
                                                del st.session_state['clientes_data']
                                                
                                            # Mostrar mensaje informativo sobre los botones de acción fuera del formulario
                                            st.info("✅ **Cliente agregado con éxito.** Puedes agregar otro cliente o ver la lista de todos los clientes usando los botones abajo.")
                                            
                                            # Guardar un flag para indicar que debemos cambiar de pestaña en la próxima ejecución
                                            st.session_state.cliente_recien_agregado = True
                                            
                                            # Limpiar caché de datos para actualizarlos en segundo plano
                                            if 'clientes_data' in st.session_state:
                                                del st.session_state['clientes_data']
                                    
                                    except Exception as e:
                                        with status_container.container():
                                            st.error(f"❌ Error al agregar el cliente: {e}")
                                            st.exception(e)
                                    else:
                                        with status_container.container():
                                            st.error("⚠️ El formato del email no es válido. Por favor, ingrese un email correcto.")
                            else:
                                errors = []
                                if not nuevo_titular:
                                    errors.append("⚠️ El campo **Titular** es obligatorio")
                                if not nuevo_email:
                                    errors.append("⚠️ El campo **Email** es obligatorio")
                                if not nuevo_cuit:
                                    errors.append("⚠️ El campo **CUIT/CUIL** es obligatorio")
                                
                                with status_container.container():
                                    for error in errors:
                                        st.error(error)
                    
                    # Mostrar botones de acción fuera del formulario cuando se haya agregado un cliente
                    if 'cliente_recien_agregado' in st.session_state and st.session_state.cliente_recien_agregado:
                        st.session_state.cliente_recien_agregado = False  # Resetear flag
                        
                        st.markdown("---")
                        st.markdown("### ¿Qué deseas hacer ahora?")
                        
                        col1, col2 = st.columns(2)
                        
                        # Botón para ver lista de clientes con estilo mejorado
                        with col1:
                            if st.button("📋 Ver lista de clientes", key="btn_ver_lista", use_container_width=True, type="primary"):
                                # Este es el punto clave: configuramos el flag y forzamos rerun
                                st.session_state.switch_to_list = True
                                
                                # Limpiar cualquier caché para asegurar datos frescos
                                if 'clientes_data' in st.session_state:
                                    del st.session_state['clientes_data']
                                
                                # Pequeña pausa para asegurar que los cambios se apliquen
                                time.sleep(0.1)
                                st.rerun()
                                
                        # Botón para agregar otro cliente
                        with col2:
                            if st.button("➕ Agregar otro cliente", key="btn_otro_cliente", use_container_width=True):
                                # Limpiar los campos del formulario para un nuevo cliente
                                st.session_state.form_titular = ""
                                st.session_state.form_email = ""
                                st.session_state.form_telefono = ""
                                st.session_state.form_cuit = ""
                                st.session_state.form_ciudad = ""
                                st.session_state.form_provincia = ""
                                st.session_state.form_direccion = ""
                                
                                # Recargar la página para mostrar el formulario limpio
                                st.rerun()
            
            else:
                st.info("No hay clientes registrados en el sistema")
                
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
    else:
        st.error("❌ No se pudo conectar a la base de datos")
