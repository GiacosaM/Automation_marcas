"""
Página de gestión de marcas
"""
import streamlit as st
import pandas as pd
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import (
    crear_conexion, obtener_marcas, insertar_marca, actualizar_marca,
    actualizar_marca_cliente, eliminar_marca, obtener_clientes,
    verificar_cuit_duplicado_marca,
)
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
    
    # Verificar si venimos de agregar una marca exitosamente
    if st.session_state.get("marca_agregada_exitosamente", False):
        # Limpiar la bandera para evitar entrar en este bloque de nuevo
        del st.session_state["marca_agregada_exitosamente"]

    # Mostrar aviso de discrepancia de titular si fue detectado en el ciclo anterior
    if st.session_state.get("aviso_titular_discrepancia"):
        msg = st.session_state.pop("aviso_titular_discrepancia")
        st.warning(msg)
    
    # Cargar datos de marcas
    conn = crear_conexion()
    if conn:
        try:
            # Obtener datos actualizados
            marcas_data, marcas_columns = obtener_marcas(conn)
            
            # Construir DataFrame siempre (vacío si no hay datos).
            # Las pestañas se renderizan en ambos casos para no bloquear al usuario.
            df_marcas = (
                pd.DataFrame(marcas_data, columns=marcas_columns)
                if marcas_data
                else pd.DataFrame()
            )
            if not df_marcas.empty:
                st.session_state.marcas_data = df_marcas

            # Estilos personalizados para pestañas (siempre activos)
            st.markdown("""
            <style>
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
            .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
            }
            .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
            }
            .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {
                background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
            }
            button[key="refresh_marcas"] {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 0.75rem 1.5rem !important;
                font-weight: 700 !important;
                font-size: 0.9rem !important;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase !important;
                letter-spacing: 0.8px !important;
            }
            button[key="refresh_marcas"]:hover {
                background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
                transform: translateY(-3px) !important;
            }
            button[key="refresh_marcas"]:active {
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # Cambio de pestaña programático via session_state.
            # Streamlit siempre activa la primera pestaña al renderizar.
            # Al establecer _marcas_ir_a_agregar=True y hacer rerun,
            # invertimos el orden de las pestañas para que "Agregar Marca"
            # quede en posición 1 (activa por defecto), sin ningún hack de JS.
            ir_a_agregar = st.session_state.pop("_marcas_ir_a_agregar", False)

            if ir_a_agregar:
                tab2, tab1 = st.tabs(["➕ Agregar Marca", "📋 Lista de Marcas"])
            else:
                tab1, tab2 = st.tabs(["📋 Lista de Marcas", "➕ Agregar Marca"])

            if True:
                
                with tab1:
                    st.subheader("📋 Lista Completa de Marcas")

                    if df_marcas.empty:
                        # Estado vacío — guía al usuario sin bloquear la navegación.
                        # También verificamos si hay clientes para anticipar el siguiente paso.
                        clientes_rows_empty, clientes_cols_empty = obtener_clientes(conn)
                        hay_clientes = bool(clientes_rows_empty)

                        st.markdown("---")
                        col_ico, col_msg = st.columns([1, 6])
                        with col_ico:
                            st.markdown("## 📭")
                        with col_msg:
                            st.markdown(
                                "### No hay marcas registradas todavía\n"
                                "Las marcas deben estar vinculadas a clientes para participar "
                                "en el flujo de envío de reportes por email."
                            )

                        if not hay_clientes:
                            st.warning(
                                "⚠️ **Tampoco hay clientes registrados.** "
                                "Antes de crear una marca debés crear al menos un cliente. "
                                "Dirigite a la sección **Clientes** del menú lateral."
                            )
                        else:
                            st.success(
                                f"✅ Hay **{len(clientes_rows_empty)}** cliente(s) disponible(s). "
                                "Podés crear la primera marca ahora."
                            )
                            if st.button(
                                "➕ Crear primera marca",
                                type="primary",
                                use_container_width=False,
                                key="btn_ir_a_agregar_marca",
                            ):
                                # Activar flag para que en el próximo render las pestañas
                                # se creen con "Agregar Marca" en posición 1 (activa).
                                st.session_state["_marcas_ir_a_agregar"] = True
                                st.rerun()

                        st.markdown("---")

                    # Grid + filtros: solo cuando hay datos.
                    # El bloque anterior (empty state) ya manejó el caso df_marcas.empty.
                    if not df_marcas.empty:

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
                                    mensaje_container = st.empty()
                                    with mensaje_container.container():
                                        st.info("⏳ Actualizando datos de marcas desde la base de datos...")
                                    if 'marcas_data' in st.session_state:
                                        del st.session_state.marcas_data
                                    for key in list(st.session_state.keys()):
                                        if key.startswith('grid_marcas_'):
                                            del st.session_state[key]
                                    st.rerun()

                            # P6 — Filtro de marcas sin cliente vinculado.
                            solo_sin_cliente = st.checkbox(
                                "⚠️ Solo marcas sin cliente vinculado",
                                value=False,
                                key="filtro_sin_cliente",
                                help=(
                                    "Muestra únicamente las marcas que no tienen cliente asociado. "
                                    "Estas marcas NO pueden participar en el flujo de envío de emails."
                                )
                            )

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
                        if solo_sin_cliente:
                            filtered_marcas = filtered_marcas[
                                filtered_marcas['cliente_id'].isna() |
                                (filtered_marcas['cliente_id'].astype(str).str.strip() == '')
                            ]

                        # Grilla de solo lectura con selección por checkbox
                        if not filtered_marcas.empty:
                            st.markdown(f"📊 **{len(filtered_marcas)}** marcas de **{len(df_marcas)}** totales")
                            st.caption("Selecciona una marca con el checkbox para ver las acciones disponibles.")

                            # Invalidar la selección cacheada si la marca ya no aparece en los
                            # resultados filtrados actuales (evita mostrar acciones sobre filas
                            # que el usuario no puede ver). Robusto ante DataFrame vacío.
                            _sel_cacheada = st.session_state.get('_marcas_selected_data')
                            if _sel_cacheada is not None:
                                _ids_visibles = set(filtered_marcas['id'].values)
                                if _sel_cacheada.get('id') not in _ids_visibles:
                                    _marca_id_oculta = _sel_cacheada.get('id')
                                    st.session_state.pop('_marcas_selected_data', None)
                                    st.session_state.pop(f"confirmar_eliminar_{_marca_id_oculta}", None)
                                    st.session_state.pop(f"cambiar_cliente_activo_{_marca_id_oculta}", None)

                            grid_response = GridService.show_marca_grid(filtered_marcas, 'grid_marcas_editable')

                            # Persistir la fila seleccionada en session_state para que el panel
                            # sobreviva a cualquier rerun provocado por los botones de acción.
                            selected_rows = grid_response.get('selected_rows', [])
                            if selected_rows:
                                st.session_state['_marcas_selected_data'] = dict(selected_rows[0])

                            selected_marca = st.session_state.get('_marcas_selected_data')

                            if not selected_marca:
                                st.info("☝️ Selecciona una marca con el checkbox para ver las acciones.")
                            else:
                                st.markdown("---")
                                col_titulo, col_cerrar = st.columns([5, 1])
                                with col_titulo:
                                    st.markdown(f"### 🎯 Marca: **{selected_marca.get('marca', '')}**")
                                with col_cerrar:
                                    if st.button("✖ Cerrar", key="btn_cerrar_panel_marca"):
                                        _mid = selected_marca.get('id')
                                        if _mid is not None:
                                            st.session_state.pop(f"confirmar_eliminar_{_mid}", None)
                                            st.session_state.pop(f"cambiar_cliente_activo_{_mid}", None)
                                            st.session_state.pop(f"editar_marca_activo_{_mid}", None)
                                            st.session_state.pop(f"_edit_form_ver_{_mid}", None)
                                        st.session_state.pop('_marcas_selected_data', None)
                                        st.rerun()

                                col_editar, col_eliminar = st.columns(2)
                                with col_editar:
                                    editar_key = f"editar_marca_activo_{selected_marca['id']}"
                                    label_editar = (
                                        "✖ Cerrar edición"
                                        if st.session_state.get(editar_key, False)
                                        else "✏️ Editar"
                                    )
                                    if st.button(label_editar, type="secondary",
                                                 key=f"btn_toggle_editar_{selected_marca['id']}",
                                                 use_container_width=True):
                                        st.session_state[editar_key] = not st.session_state.get(
                                            editar_key, False
                                        )
                                        st.rerun()
                                with col_eliminar:
                                    eliminar_key = f"confirmar_eliminar_{selected_marca['id']}"
                                    if not st.session_state.get(eliminar_key, False):
                                        if st.button("🗑️ Eliminar", type="secondary",
                                                     use_container_width=True):
                                            st.session_state[eliminar_key] = True
                                            st.rerun()
                                    else:
                                        st.warning("¿Confirmar eliminación?")
                                        col_si, col_no = st.columns(2)
                                        with col_si:
                                            if st.button("✅ Sí", type="primary",
                                                         key=f"btn_si_eliminar_{selected_marca['id']}",
                                                         use_container_width=True):
                                                try:
                                                    resultado = eliminar_marca(conn, selected_marca['id'])
                                                    if resultado:
                                                        st.success(f"✅ Marca '{selected_marca['marca']}' eliminada")
                                                        st.session_state.pop('_marcas_selected_data', None)
                                                        st.session_state.pop(eliminar_key, None)
                                                        if 'marcas_data' in st.session_state:
                                                            del st.session_state['marcas_data']
                                                        for k in list(st.session_state.keys()):
                                                            if k.startswith('grid_marcas_'):
                                                                del st.session_state[k]
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ No se pudo eliminar la marca")
                                                except Exception as e:
                                                    st.error(f"❌ Error al eliminar: {e}")
                                        with col_no:
                                            if st.button("✖ No", key=f"btn_no_eliminar_{selected_marca['id']}",
                                                         use_container_width=True):
                                                st.session_state.pop(eliminar_key, None)
                                                st.rerun()

                                # Sección de vinculación de cliente
                                st.markdown("---")
                                cliente_actual_nombre = selected_marca.get('cliente_nombre') or None
                                cliente_actual_id_str = str(selected_marca.get('cliente_id') or "")
                                cambiar_key = f"cambiar_cliente_activo_{selected_marca['id']}"

                                col_cli_estado, col_cli_accion = st.columns([3, 1])
                                with col_cli_estado:
                                    if cliente_actual_nombre:
                                        st.markdown(f"🔗 **Cliente vinculado:** {cliente_actual_nombre}")
                                    else:
                                        st.warning("⚠️ Esta marca no tiene cliente vinculado.")
                                with col_cli_accion:
                                    label_cambiar = "🔄 Cambiar" if cliente_actual_nombre else "➕ Vincular"
                                    if st.button(label_cambiar,
                                                 key=f"btn_toggle_cli_{selected_marca['id']}",
                                                 use_container_width=True):
                                        st.session_state[cambiar_key] = not st.session_state.get(
                                            cambiar_key, False
                                        )
                                        st.rerun()

                                if st.session_state.get(cambiar_key, False):
                                    clientes_rows_r, clientes_cols_r = obtener_clientes(conn)
                                    clientes_df_r = pd.DataFrame(clientes_rows_r, columns=clientes_cols_r)

                                    if not clientes_df_r.empty:
                                        opciones_r = [("", "— Sin cliente (desvincular)")] + [
                                            (str(row['id']), row['titular'])
                                            for _, row in clientes_df_r.iterrows()
                                        ]
                                        labels_r = [
                                            f"{cid} — {nombre}" if cid else nombre
                                            for cid, nombre in opciones_r
                                        ]
                                        idx_actual_r = next(
                                            (i for i, (cid, _) in enumerate(opciones_r)
                                             if cid == cliente_actual_id_str),
                                            0
                                        )

                                        col_sel_r, col_ok_r, col_cancel_r = st.columns([4, 1, 1])
                                        with col_sel_r:
                                            nuevo_idx_r = st.selectbox(
                                                "Nuevo cliente",
                                                range(len(opciones_r)),
                                                index=idx_actual_r,
                                                format_func=lambda i: labels_r[i],
                                                key=f"reasignar_sel_{selected_marca['id']}"
                                            )
                                        nuevo_cliente_id_r = opciones_r[nuevo_idx_r][0]

                                        with col_ok_r:
                                            st.markdown("<br>", unsafe_allow_html=True)
                                            confirmar_r = st.button(
                                                "✅", key=f"btn_ok_reasignar_{selected_marca['id']}",
                                                help="Confirmar reasignación", use_container_width=True
                                            )
                                        with col_cancel_r:
                                            st.markdown("<br>", unsafe_allow_html=True)
                                            if st.button(
                                                "✖", key=f"btn_cancel_reasignar_{selected_marca['id']}",
                                                help="Cancelar", use_container_width=True
                                            ):
                                                st.session_state[cambiar_key] = False
                                                st.rerun()

                                        if confirmar_r:
                                            try:
                                                nuevo_cid = int(nuevo_cliente_id_r) if nuevo_cliente_id_r else None
                                                resultado_r = actualizar_marca_cliente(
                                                    conn,
                                                    selected_marca['id'],
                                                    nuevo_cid
                                                )
                                                if resultado_r:
                                                    st.success("✅ Cliente actualizado correctamente")
                                                    st.session_state[cambiar_key] = False
                                                    st.session_state.pop('_marcas_selected_data', None)
                                                    if 'marcas_data' in st.session_state:
                                                        del st.session_state['marcas_data']
                                                    for k in list(st.session_state.keys()):
                                                        if k.startswith('grid_marcas_'):
                                                            del st.session_state[k]
                                                    st.rerun()
                                                else:
                                                    st.error("❌ No se pudo actualizar el cliente")
                                            except Exception as e_r:
                                                st.error(f"❌ Error al reasignar: {e_r}")
                                    else:
                                        st.warning("❌ No hay clientes disponibles.")

                                # ── Panel de edición de datos de la marca ─────────────
                                editar_key = f"editar_marca_activo_{selected_marca['id']}"
                                if st.session_state.get(editar_key, False):
                                    st.markdown("---")
                                    st.markdown("### ✏️ Editar datos de la marca")

                                    _mid = selected_marca['id']
                                    # Key dinámica para limpiar el form tras guardar
                                    if f"_edit_form_ver_{_mid}" not in st.session_state:
                                        st.session_state[f"_edit_form_ver_{_mid}"] = 0
                                    edit_form_key = f"form_editar_marca_{_mid}_{st.session_state[f'_edit_form_ver_{_mid}']}"

                                    # Mensaje de éxito entre reruns
                                    if st.session_state.pop(f"_edit_ok_{_mid}", False):
                                        st.success("✅ Marca actualizada correctamente")

                                    with st.form(key=edit_form_key):
                                        ec1, ec2 = st.columns(2)
                                        with ec1:
                                            e_marca = st.text_input(
                                                "Nombre de Marca 🏷️",
                                                value=str(selected_marca.get('marca') or ''),
                                            )
                                            e_codigo = st.text_input(
                                                "Código de Marca",
                                                value=str(selected_marca.get('codigo_marca') or ''),
                                            )
                                            e_clase = st.number_input(
                                                "Clase",
                                                min_value=1, max_value=45,
                                                value=int(selected_marca.get('clase') or 35),
                                            )
                                            e_acta = st.text_input(
                                                "Acta 📄",
                                                value=str(selected_marca.get('acta') or ''),
                                            )
                                            e_nrocon = st.text_input(
                                                "Nro. Concesión",
                                                value=str(selected_marca.get('nrocon') or ''),
                                            )
                                        with ec2:
                                            e_custodia = st.text_input(
                                                "Custodia",
                                                value=str(selected_marca.get('custodia') or ''),
                                            )
                                            e_titular = st.text_input(
                                                "Titular 👤",
                                                value=str(selected_marca.get('titular') or ''),
                                                help="Modifica el nombre del titular de esta marca. "
                                                     "No cambia el titular del cliente vinculado.",
                                            )
                                            e_cuit_raw = str(selected_marca.get('cuit') or '')
                                            e_cuit_display = "".join(
                                                ch for ch in e_cuit_raw if ch.isdigit()
                                            )
                                            e_cuit = st.text_input(
                                                "CUIT 🆔",
                                                value=e_cuit_display,
                                                placeholder="Solo dígitos, 11 caracteres",
                                                help="Si cambias el CUIT, el sistema intentará "
                                                     "re-vincular la marca con el cliente correspondiente.",
                                            )
                                            e_email = st.text_input(
                                                "Email 📧",
                                                value=str(selected_marca.get('email') or ''),
                                            )

                                        st.markdown("---")
                                        ebtn1, ebtn2 = st.columns([1, 3])
                                        with ebtn1:
                                            e_cancelar = st.form_submit_button(
                                                "❌ Cancelar", use_container_width=True
                                            )
                                        with ebtn2:
                                            e_guardar = st.form_submit_button(
                                                "💾 Guardar cambios", type="primary",
                                                use_container_width=True,
                                            )

                                        if e_cancelar:
                                            st.session_state[editar_key] = False
                                            st.rerun()

                                        if e_guardar:
                                            # Validaciones básicas
                                            if not e_marca.strip():
                                                st.error("❌ El nombre de la marca es obligatorio.")
                                                st.stop()

                                            # Normalizar y validar CUIT
                                            e_cuit_limpio = "".join(
                                                ch for ch in e_cuit if ch.isdigit()
                                            )
                                            if e_cuit_limpio and len(e_cuit_limpio) != 11:
                                                st.error(
                                                    "⚠️ El CUIT debe tener exactamente 11 dígitos "
                                                    "(sin puntos ni guiones)."
                                                )
                                                st.stop()

                                            # Verificar CUIT duplicado en otras marcas
                                            if e_cuit_limpio:
                                                dup_edit = verificar_cuit_duplicado_marca(
                                                    conn, e_cuit_limpio, excluir_id=_mid
                                                )
                                                if dup_edit:
                                                    st.error(
                                                        f"❌ El CUIT **{e_cuit_limpio}** ya está "
                                                        f"registrado en la marca **{dup_edit['marca']}** "
                                                        f"(titular: {dup_edit['titular']}, "
                                                        f"ID: {dup_edit['id']}). "
                                                        "Cada marca debe tener un CUIT único."
                                                    )
                                                    st.stop()

                                            try:
                                                ok = actualizar_marca(
                                                    conn,
                                                    _mid,
                                                    e_marca.strip(),
                                                    e_codigo.strip() or None,
                                                    e_clase,
                                                    e_acta.strip() or None,
                                                    e_custodia.strip() or None,
                                                    e_cuit_limpio or None,
                                                    e_titular.strip() or None,
                                                    e_nrocon.strip() or None,
                                                    e_email.strip() or None,
                                                    # Preservar cliente_id actual;
                                                    # el cambio de cliente se hace en su panel propio.
                                                    selected_marca.get('cliente_id'),
                                                )
                                                if ok:
                                                    # Limpiar caches y refrescar
                                                    st.session_state.pop('marcas_data', None)
                                                    st.session_state.pop('_marcas_selected_data', None)
                                                    st.session_state[editar_key] = False
                                                    for k in list(st.session_state.keys()):
                                                        if k.startswith('grid_marcas_'):
                                                            del st.session_state[k]
                                                    # Incrementar versión del form (limpieza)
                                                    st.session_state[f"_edit_form_ver_{_mid}"] = (
                                                        st.session_state.get(f"_edit_form_ver_{_mid}", 0) + 1
                                                    )
                                                    st.session_state[f"_edit_ok_{_mid}"] = True
                                                    st.rerun()
                                                else:
                                                    st.error("❌ No se pudo guardar los cambios.")
                                            except Exception as e_edit:
                                                st.error(f"❌ Error al guardar: {e_edit}")

                        else:
                            st.warning("🔍 No se encontraron marcas con los filtros aplicados.")
                
                with tab2:
                    st.subheader("➕ Agregar Nueva Marca")

                    # ── Mensaje de éxito persistente entre reruns ─────────────────────
                    # Se guarda en session_state antes del rerun y se consume aquí
                    # para que sea visible con el formulario ya limpio.
                    if st.session_state.pop("_marca_guardada_ok", False):
                        st.success("✅ Marca agregada correctamente")

                    # ── Versión dinámica del formulario ───────────────────────────────
                    # Al incrementar este contador el formulario recibe una nueva key,
                    # Streamlit lo trata como un widget nuevo y todos los campos
                    # vuelven a su valor por defecto — sin JS ni hacks.
                    if "_marca_form_ver" not in st.session_state:
                        st.session_state["_marca_form_ver"] = 0

                    form_key = f"form_nueva_marca_{st.session_state['_marca_form_ver']}"
                    # El selectbox de cliente también necesita key dinámica para
                    # volver al primer ítem ("Sin vincular") tras el guardado.
                    selector_key = f"nueva_marca_cliente_selector_{st.session_state['_marca_form_ver']}"

                    # El selector de cliente está FUERA del st.form para que al
                    # cambiar la selección se dispare un rerun y se pre-llenen
                    # los campos Titular y CUIT antes de que el usuario confirme.
                    clientes_rows_add, clientes_cols_add = obtener_clientes(conn)
                    clientes_df_add = pd.DataFrame(clientes_rows_add, columns=clientes_cols_add)

                    titular_prefill = ""
                    cuit_prefill = ""
                    cliente_id_prefill = ""

                    if clientes_df_add.empty:
                        st.error(
                            "❌ No hay clientes disponibles. "
                            "Debe crear al menos un cliente antes de agregar marcas."
                        )
                    else:
                        opciones_add = [("", "— Sin vincular (opcional)")] + [
                            (str(row['id']), row['titular'])
                            for _, row in clientes_df_add.iterrows()
                        ]
                        labels_add = [
                            f"{cid} — {nombre}" if cid else nombre
                            for cid, nombre in opciones_add
                        ]

                        st.markdown("**🔗 Vincular a Cliente**")
                        idx_add = st.selectbox(
                            "Seleccione un cliente (pre-llena Titular y CUIT)",
                            range(len(opciones_add)),
                            format_func=lambda i: labels_add[i],
                            key=selector_key,
                        )
                        cliente_id_prefill = opciones_add[idx_add][0]

                        if cliente_id_prefill:
                            fila_add = clientes_df_add[
                                clientes_df_add['id'] == int(cliente_id_prefill)
                            ]
                            if not fila_add.empty:
                                titular_prefill = str(
                                    fila_add.iloc[0].get('titular', '') or ''
                                ).strip()
                                cuit_raw_add = str(
                                    fila_add.iloc[0].get('cuit', '') or ''
                                ).strip()
                                cuit_prefill = "".join(
                                    ch for ch in cuit_raw_add if ch.isdigit()
                                )
                            st.info(
                                f"📋 **{titular_prefill}** · "
                                f"CUIT del cliente: `{cuit_prefill or 'no registrado'}`"
                            )

                    # ── Checkbox "Usar CUIT del cliente" ─────────────────────────────
                    # Debe estar FUERA del st.form para que al activarlo/desactivarlo
                    # se dispare un rerun inmediato que cambie el estado del campo CUIT.
                    usar_cuit_cliente = False
                    if cliente_id_prefill:
                        usar_cuit_cliente = st.checkbox(
                            "☑ Usar CUIT del cliente seleccionado",
                            value=True,
                            key=f"usar_cuit_cliente_{st.session_state['_marca_form_ver']}",
                            help=(
                                "Activado: el campo CUIT se completa automáticamente con el "
                                "CUIT del cliente y queda bloqueado. "
                                "Desactivado: podés ingresar un CUIT distinto para esta marca."
                            ),
                        )
                        if usar_cuit_cliente and cuit_prefill:
                            st.caption(
                                f"CUIT que se asignará a la marca: `{cuit_prefill}` "
                                "(del cliente seleccionado)"
                            )
                        elif not usar_cuit_cliente:
                            st.caption(
                                "Ingresá el CUIT propio de esta marca. "
                                "Puede ser distinto al del cliente."
                            )

                    # Formulario con los campos de la marca.
                    # La key dinámica garantiza que los campos se vacíen tras un
                    # guardado exitoso.
                    with st.form(key=form_key):
                        col1, col2 = st.columns(2)

                        with col1:
                            marca_nueva = st.text_input(
                                "Nombre de Marca 🏷️",
                                placeholder="Ingrese nombre de marca"
                            )
                            codigo_marca_nueva = st.text_input(
                                "Código de Marca",
                                placeholder="Código de marca (opcional)"
                            )
                            clase_nueva = st.number_input(
                                "Clase", min_value=1, max_value=45, value=35
                            )
                            acta_nueva = st.text_input(
                                "Acta 📄", placeholder="Número de acta (opcional)"
                            )
                            nrocon_nueva = st.text_input(
                                "Nro. Concesión",
                                placeholder="Número de concesión (opcional)"
                            )

                        with col2:
                            custodia_nueva = st.text_input(
                                "Custodia",
                                placeholder="Estado de custodia (opcional)"
                            )

                            if cliente_id_prefill:
                                # Titular → siempre del cliente (solo lectura)
                                st.text_input(
                                    "Titular 👤 (del cliente)",
                                    value=titular_prefill,
                                    disabled=True,
                                    help="Deriva del cliente seleccionado. "
                                         "Para modificarlo, edita el cliente desde Clientes.",
                                )
                                titular_nueva = titular_prefill

                                # CUIT → independiente; controlado por el checkbox externo.
                                # Cuando el checkbox está ON:  disabled=True, value=cuit del cliente.
                                # Cuando el checkbox está OFF: disabled=False, value=cuit del cliente
                                #   como punto de partida editable.
                                # La key estable dentro de la versión actual del form garantiza
                                # que el valor ingresado manualmente sobrevive reruns intermedios.
                                cuit_nueva = st.text_input(
                                    "CUIT 🆔 de la marca",
                                    value=cuit_prefill,
                                    disabled=usar_cuit_cliente,
                                    key=f"cuit_nueva_input_{st.session_state['_marca_form_ver']}",
                                    placeholder="Solo dígitos, 11 caracteres",
                                    help=(
                                        "CUIT específico de esta marca. "
                                        "Puede diferir del CUIT del cliente."
                                        if not usar_cuit_cliente
                                        else "Bloqueado: se usa el CUIT del cliente. "
                                             "Desactivá el checkbox para cambiarlo."
                                    ),
                                )
                                # Cuando el checkbox está ON, forzar el valor del cliente
                                # (el widget disabled puede devolver el valor anterior si la
                                # key no cambió; sobreescribimos explícitamente para seguridad)
                                if usar_cuit_cliente:
                                    cuit_nueva = cuit_prefill
                            else:
                                # Sin cliente → ingreso manual obligatorio
                                titular_nueva = st.text_input(
                                    "Titular 👤 *",
                                    placeholder="Nombre del titular (obligatorio)",
                                )
                                cuit_nueva = st.text_input(
                                    "CUIT 🆔 *",
                                    placeholder="Solo números, 11 dígitos",
                                    key=f"cuit_nueva_input_{st.session_state['_marca_form_ver']}",
                                )

                            email_nueva = st.text_input(
                                "Email 📧", placeholder="Email de contacto"
                            )

                        st.markdown("---")
                        col_btn1, col_btn2 = st.columns([1, 3])

                        with col_btn1:
                            cancelar = st.form_submit_button(
                                "❌ Cancelar", use_container_width=True
                            )
                        with col_btn2:
                            submit_button = st.form_submit_button(
                                "💾 Guardar Marca", use_container_width=True
                            )

                        # Cancelar: limpiar el formulario con la misma técnica
                        if cancelar:
                            st.session_state["_marca_form_ver"] = (
                                st.session_state.get("_marca_form_ver", 0) + 1
                            )
                            st.rerun()

                        # Procesar formulario
                        if submit_button:
                            if not marca_nueva:
                                st.error("❌ El nombre de la marca es obligatorio")
                            elif not cliente_id_prefill and not titular_nueva.strip():
                                st.error("❌ El titular es obligatorio cuando no se selecciona un cliente")
                            elif not cliente_id_prefill and not cuit_nueva.strip():
                                st.error("❌ El CUIT es obligatorio cuando no se selecciona un cliente")
                            else:
                                # Advertencia no bloqueante: sin cliente y sin CUIT válido
                                cuit_para_advertencia = "".join(
                                    ch for ch in (cuit_nueva or "") if ch.isdigit()
                                )
                                if not cliente_id_prefill and len(cuit_para_advertencia) != 11:
                                    st.warning(
                                        "⚠️ **Marca sin cliente vinculado.** "
                                        "Esta marca no quedará asociada a ningún cliente y "
                                        "no podrá participar en el flujo de envío de reportes por email. "
                                        "Podés vincularla desde la Lista de Marcas una vez guardada."
                                    )

                                try:
                                    # Normalizar CUIT: dejar solo dígitos
                                    cuit_limpio = "".join(
                                        ch for ch in cuit_nueva if ch.isdigit()
                                    )

                                    # Validar longitud de CUIT (11 dígitos).
                                    if len(cuit_limpio) != 11:
                                        st.error(
                                            "⚠️ El CUIT debe contener exactamente 11 dígitos "
                                            "(sin puntos ni guiones)."
                                        )
                                        st.stop()

                                    # Verificar que el CUIT no esté registrado en otra marca
                                    dup = verificar_cuit_duplicado_marca(conn, cuit_limpio)
                                    if dup:
                                        st.error(
                                            f"❌ El CUIT **{cuit_limpio}** ya está registrado "
                                            f"en la marca **{dup['marca']}** "
                                            f"(titular: {dup['titular']}, ID: {dup['id']}). "
                                            "Cada marca debe tener un CUIT único."
                                        )
                                        st.stop()

                                    # Insertar marca con cliente_id explícito
                                    resultado = insertar_marca(
                                        conn,
                                        marca_nueva,
                                        codigo_marca_nueva,
                                        clase_nueva,
                                        acta_nueva,
                                        custodia_nueva,
                                        cuit_limpio,
                                        titular_nueva.strip(),
                                        nrocon_nueva,
                                        email_nueva,
                                        int(cliente_id_prefill) if cliente_id_prefill else None
                                    )

                                    # Verificar discrepancia titular marca vs cliente
                                    if resultado and cliente_id_prefill and titular_prefill:
                                        if titular_prefill.lower() != titular_nueva.strip().lower():
                                            st.session_state["aviso_titular_discrepancia"] = (
                                                f"⚠️ El titular ingresado en la marca "
                                                f"(**{titular_nueva.strip()}**) difiere del registrado "
                                                f"en el cliente (**{titular_prefill}**). "
                                                "El cliente no fue modificado. Si el nombre debe "
                                                "actualizarse, hacerlo desde la sección **Clientes**."
                                            )

                                    if resultado:
                                        # Limpiar datos cacheados de marcas
                                        st.session_state.pop("marcas_data", None)

                                        # Incrementar la versión del formulario → clave nueva
                                        # en el siguiente render → todos los campos se vacían.
                                        st.session_state["_marca_form_ver"] = (
                                            st.session_state.get("_marca_form_ver", 0) + 1
                                        )

                                        # Guardar mensaje de éxito para mostrarlo DESPUÉS
                                        # del rerun, cuando el formulario ya esté limpio.
                                        st.session_state["_marca_guardada_ok"] = True
                                        st.session_state["marca_agregada_exitosamente"] = True
                                        st.session_state["active_tab"] = "Lista de Marcas"

                                        st.rerun()
                                    else:
                                        st.error("❌ No se pudo agregar la marca")
                                except Exception as e:
                                    st.error(f"❌ Error al agregar la marca: {e}")

                    
        except Exception as e:
            st.error(f"❌ Error al cargar datos de marcas: {e}")
        finally:
            if conn:
                conn.close()
    else:
        st.error("❌ No se pudo conectar a la base de datos")
