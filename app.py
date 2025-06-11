import streamlit as st
import pandas as pd
from database import crear_conexion, crear_tabla, insertar_datos, obtener_datos, actualizar_registro, eliminar_registro, insertar_cliente, obtener_clientes, actualizar_cliente, eliminar_cliente
from extractor import extraer_datos_agrupados
from report_generator import generar_informe_pdf
from email_sender import procesar_envio_emails, generar_reporte_envios

import math


# Custom CSS para barra de navegación fija
st.markdown(
    """
    <style>
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #f8f9fa;
        padding: 10px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        display: flex;
        align-items: center;
    }
    .navbar button {
        margin-right: 10px;
    }
    .main-content {
        margin-top: 60px;
    }
    </style>
    """,
    unsafe_allow_html=True
)



# Inicializar estado de la sesión
if 'show_db_section' not in st.session_state:
    st.session_state.show_db_section = False
if 'show_clientes_section' not in st.session_state:
    st.session_state.show_clientes_section = False
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

if 'show_email_section' not in st.session_state:
    st.session_state.show_email_section = False

st.markdown('<div class="navbar">', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 1])

# Add consistent styling to all buttons
button_style = """
    <style>
    .stButton>button {
        width: 150px;  /* Uniform width */
        height: 40px;  /* Uniform height */
        font-size: 16px;  /* Uniform font size */
        text-align: center;
        margin: 0 auto;  /* Center alignment */
    }
    </style>
"""
st.markdown(button_style, unsafe_allow_html=True)

with col_nav1:
    if st.button("Historial"):
        st.session_state.show_db_section = not st.session_state.show_db_section
        if st.session_state.show_db_section:
            st.session_state.show_clientes_section = False
            st.session_state.show_email_section = False
with col_nav2:
    if st.button("Clientes"):
        st.session_state.show_clientes_section = not st.session_state.show_clientes_section
        if st.session_state.show_clientes_section:
            st.session_state.show_db_section = False
            st.session_state.show_email_section = False
with col_nav3:
    if st.button("Generar Informes"):
        conn = crear_conexion()
        if conn:
            try:
                crear_tabla(conn)
                generar_informe_pdf(conn)
                st.success("Informe PDF generado exitosamente.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()
with col_nav4:
    if st.button("Enviar Emails"):
        st.session_state.show_email_section = not st.session_state.show_email_section
        if st.session_state.show_email_section:
            st.session_state.show_db_section = False
            st.session_state.show_clientes_section = False

st.markdown('</div>', unsafe_allow_html=True)

# Contenido principal
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Interfaz Streamlit
st.title("Boletines por Titular")

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
            #st.write("Tablas 'boletines' y 'clientes' verificadas/creadas.")
            # Insertar datos en la base de datos
            if st.button("Ingresa los datos a la base de datos"):
                insertar_datos(conn, datos_agrupados)
                st.success("Datos insertados en la base de datos correctamente.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

    # Mostrar datos agrupados en formato de planilla
    if datos_agrupados:
        for titular, registros in datos_agrupados.items():
            st.subheader(f"Titular: {titular}")
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
        st.warning("No se encontraron titulares.")

    # Botón para generar el informe PDF
    if st.button("Generar Informe PDF"):
        conn = crear_conexion()
        if conn:
            try:
                crear_tabla(conn)
                
                generar_informe_pdf(conn)
                st.success("Informe PDF generado exitosamente.")
                
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()

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
            # st.write("Tablas 'boletines' y 'clientes' verificadas/creadas.")
            
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

                # Paginación
                rows_per_page = 10
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