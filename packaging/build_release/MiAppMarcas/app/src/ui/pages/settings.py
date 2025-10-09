"""
Página de gestión de usuarios
"""
import streamlit as st
import pandas as pd
import time
import re
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, obtener_usuarios, insertar_usuario, actualizar_usuario, eliminar_usuario
from src.services.grid_service import GridService
from src.ui.components import UIComponents

def validate_email_format(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def show_settings_page():
    """Mostrar la página de usuarios"""
    st.title("👥 Gestión de Usuarios")

    # Cargar datos de usuarios
    conn = crear_conexion()
    if conn:
        try:
            rows, columns = obtener_usuarios(conn)

            if rows:
                df_usuarios = pd.DataFrame(rows, columns=columns)
                st.session_state.usuarios_data = df_usuarios

                # Solo dos pestañas: Lista Editable y Agregar Usuario
                tab1, tab2 = st.tabs(["📋 Lista de Usuarios (Editable)", "➕ Agregar Usuario"])

                with tab1:
                    st.subheader("📋 Lista Completa de Usuarios")
                    st.info("💡 **Instrucciones:** Haz clic en cualquier celda para editarla directamente. Los cambios se guardan automáticamente.")

                    # Mostrar resultados - TABLA EDITABLE
                    if not df_usuarios.empty:
                        st.markdown(f"📊 **{len(df_usuarios)}** usuarios registrados")

                        # GRILLA EDITABLE
                        grid_response = GridService.show_user_grid(df_usuarios, 'grid_usuarios_editable')

                        # PROCESAR CAMBIOS EN TIEMPO REAL
                        if grid_response['data'] is not None and len(grid_response['data']) > 0:
                            df_modificado = pd.DataFrame(grid_response['data'])

                            # Comparar con datos originales para encontrar cambios
                            for index, row in df_modificado.iterrows():
                                original_row = df_usuarios[df_usuarios['id'] == row['id']]
                                if not original_row.empty:
                                    original_row = original_row.iloc[0]

                                    # Verificar si hay cambios en cada campo
                                    cambios = False
                                    campos_cambiados = []

                                    for column in ['username', 'email', 'role', 'is_active']:
                                        # Normalizar valores para comparación (manejar NaN y None)
                                        valor_nuevo = str(row[column]) if pd.notna(row[column]) else ""
                                        valor_original = str(original_row[column]) if pd.notna(original_row[column]) else ""

                                        if valor_nuevo != valor_original:
                                            cambios = True
                                            campos_cambiados.append(column)

                                    if cambios:
                                        # Actualizar en la base de datos
                                        try:
                                            actualizar_usuario(
                                                conn,
                                                row['id'],
                                                row['username'] if pd.notna(row['username']) else "",
                                                row['email'] if pd.notna(row['email']) else "",
                                                row['role'] if pd.notna(row['role']) else "",
                                                row['is_active'] if pd.notna(row['is_active']) else 1
                                            )
                                            st.success(f"✅ Usuario '{row['username']}' actualizado: {', '.join(campos_cambiados)}")
                                            time.sleep(0.5)
                                            st.rerun()  # Recargar para mostrar cambios
                                        except Exception as e:
                                            st.error(f"❌ Error al actualizar '{row['username']}': {e}")

                        # Panel de acciones para usuario seleccionado
                        if grid_response['selected_rows']:
                            selected_user = grid_response['selected_rows'][0]

                            with st.container():
                                st.markdown("---")
                                st.markdown(f"### 🎯 Usuario Seleccionado: **{selected_user['username']}**")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("🔑 Resetear Contraseña", type="secondary", use_container_width=True):
                                        st.info("🔑 Funcionalidad próximamente")
                                with col2:
                                    if st.button("🗑️ Eliminar Usuario", type="secondary", use_container_width=True):
                                        # Confirmar eliminación
                                        if st.button("⚠️ Confirmar Eliminación", type="primary"):
                                            try:
                                                eliminar_usuario(conn, selected_user['id'])
                                                st.success(f"✅ Usuario '{selected_user['username']}' eliminado")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error al eliminar: {e}")
                    else:
                        st.warning("🔍 No se encontraron usuarios registrados.")

                with tab2:
                    st.subheader("➕ Agregar Nuevo Usuario")
                    st.markdown("Complete la información del nuevo usuario. Los campos marcados con **\*** son obligatorios.")

                    with st.form("form_nuevo_usuario", clear_on_submit=False):
                        # Información básica
                        st.markdown("##### 📝 Información Básica")
                        col1, col2 = st.columns(2)
                        with col1:
                            nuevo_username = st.text_input("👤 Nombre de Usuario *", placeholder="Ingrese un nombre de usuario")
                            nuevo_email = st.text_input("📧 Email *", placeholder="usuario@ejemplo.com")
                        with col2:
                            nuevo_role = st.selectbox("🔑 Rol", options=["admin", "user"], index=1)
                            nuevo_is_active = st.checkbox("🟢 Activo", value=True)

                        # Botón de envío con diseño profesional
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            submitted = st.form_submit_button(
                                "💾 GUARDAR USUARIO",
                                type="primary",
                                use_container_width=True,
                                help="Haz clic para agregar este usuario a la base de datos"
                            )

                        if submitted:
                            if nuevo_username and nuevo_email:
                                # Validar formato de email
                                if validate_email_format(nuevo_email):
                                    try:
                                        insertar_usuario(conn, nuevo_username, nuevo_email, nuevo_role, nuevo_is_active)
                                        st.success("✅ Usuario agregado correctamente")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error al agregar el usuario: {e}")
                                else:
                                    st.error("⚠️ El formato del email no es válido. Por favor, ingrese un email correcto.")
                            else:
                                if not nuevo_username:
                                    st.error("⚠️ El campo Nombre de Usuario es obligatorio")
                                if not nuevo_email:
                                    st.error("⚠️ El campo Email es obligatorio")
            else:
                st.info("📂 No hay usuarios registrados en el sistema")

        except Exception as e:
            st.error(f"❌ Error al consultar usuarios: {e}")
            st.exception(e)
        finally:
            conn.close()
    else:
        st.error("❌ No se pudo conectar a la base de datos")
