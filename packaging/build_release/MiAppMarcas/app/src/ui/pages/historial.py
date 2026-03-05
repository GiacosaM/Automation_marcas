import streamlit as st
import pandas as pd
import time
import sys
import os
from datetime import date, timedelta

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from database import (
    crear_conexion, obtener_datos, obtener_clientes, insertar_cliente,
    diagnosticar_vinculacion, _normalizar_titular,
)
from src.services.grid_service import GridService


def _normalizar_cuit(cuit_raw: str) -> str:
    """Devuelve solo dígitos del CUIT ingresado."""
    return "".join(ch for ch in str(cuit_raw) if ch.isdigit())


def _asistente_crear_cliente(conn, titular: str, cuit_sugerido: str = "") -> bool:
    """
    Muestra un formulario embebido para crear un cliente a partir del titular
    de un boletín. Reutiliza insertar_cliente() sin duplicar lógica.

    NOTA: esta función NO usa st.expander internamente porque se llama desde
    dentro de un expander existente; Streamlit no permite anidar expanders.

    Args:
        conn: Conexión activa a la base de datos.
        titular: Nombre del titular pre-llenado desde el boletín.
        cuit_sugerido: CUIT inferido desde la tabla Marcas (puede estar vacío).

    Returns:
        True si el cliente fue creado exitosamente, False en caso contrario.
    """
    form_key = f"asistente_cliente_{titular.replace(' ', '_')[:40]}"

    st.markdown(
        f"**Datos de contacto para:** `{titular}`"
    )
    st.info(
        "Completa los datos de contacto para este titular. "
        "El cliente quedará disponible de inmediato para enviar su reporte."
    )

    # Intentar inferir CUIT desde Marcas si no se recibió uno
    cuit_inicial = cuit_sugerido
    if not cuit_inicial:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cuit FROM Marcas WHERE normalizar_titular(titular) = normalizar_titular(?) "
                "AND cuit IS NOT NULL AND cuit != '' ORDER BY id DESC LIMIT 1",
                (titular,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                cuit_inicial = str(row[0])
            cursor.close()
        except Exception:
            pass

    with st.form(key=form_key):
        col1, col2 = st.columns(2)

        with col1:
            campo_titular = st.text_input(
                "Nombre / Razón Social *",
                value=titular,
                disabled=True,
                help="Debe coincidir exactamente con el nombre del titular en el boletín."
            )
            campo_email = st.text_input(
                "Email *",
                placeholder="titular@ejemplo.com",
                help="Email de contacto para el envío del reporte."
            )
            campo_cuit = st.text_input(
                "CUIT / CUIL *",
                value=cuit_inicial,
                placeholder="30712353569",
                help="Solo dígitos, 11 caracteres. Se normalizará automáticamente."
            )

        with col2:
            campo_telefono = st.text_input("Teléfono", placeholder="+54 9 11 1234-5678")
            campo_ciudad = st.text_input("Ciudad", placeholder="Buenos Aires")
            campo_provincia = st.text_input("Provincia", placeholder="Buenos Aires")

        campo_direccion = st.text_area(
            "Dirección", placeholder="Calle, número, piso, código postal", height=68
        )

        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            cancelar = st.form_submit_button("✖ Cancelar")
        with col_btn2:
            guardar = st.form_submit_button("💾 Crear cliente", type="primary")

    if cancelar:
        # Limpiar la bandera del asistente para este titular y salir
        flag = f"asistente_activo_{titular}"
        if flag in st.session_state:
            del st.session_state[flag]
        st.rerun()

    if guardar:
        # Validaciones de campos obligatorios
        errores = []
        if not campo_titular.strip():
            errores.append("El nombre del titular es obligatorio.")
        if not campo_email.strip():
            errores.append("El email es obligatorio para poder enviar reportes.")
        else:
            import re as _re
            if not _re.match(r'^[^@]+@[^@]+\.[^@]+$', campo_email.strip()):
                errores.append("El formato del email no es válido.")
        if not campo_cuit.strip():
            errores.append("El CUIT es obligatorio.")

        cuit_normalizado = _normalizar_cuit(campo_cuit)
        if not errores and len(cuit_normalizado) != 11:
            errores.append(
                f"El CUIT debe tener exactamente 11 dígitos (se recibieron {len(cuit_normalizado)})."
            )

        if errores:
            for e in errores:
                st.error(f"⚠️ {e}")
            return False

        # Verificar si ya existe cliente con ese CUIT
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT titular FROM clientes WHERE REPLACE(REPLACE(cuit,'-',''),' ','') = ? LIMIT 1",
                (cuit_normalizado,)
            )
            dup = cursor.fetchone()
            cursor.close()
            if dup:
                st.warning(
                    f"⚠️ Ya existe un cliente con ese CUIT: **{dup[0]}**. "
                    "Puedes actualizar su email en la sección Clientes."
                )
                return False
        except Exception as ex:
            st.error(f"❌ Error al verificar duplicado de CUIT: {ex}")
            return False

        # Verificar si ya existe cliente con ese titular
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM clientes WHERE normalizar_titular(titular) = normalizar_titular(?) LIMIT 1",
                (campo_titular.strip(),)
            )
            dup_titular = cursor.fetchone()
            cursor.close()
            if dup_titular:
                st.warning(
                    f"⚠️ Ya existe un cliente con el titular **{campo_titular.strip()}** (ID: {dup_titular[0]}). "
                    "Puedes editar su email en la sección Clientes."
                )
                return False
        except Exception as ex:
            st.error(f"❌ Error al verificar duplicado de titular: {ex}")
            return False

        # Crear el cliente usando la función existente (no se duplica lógica)
        try:
            nuevo_id = insertar_cliente(
                conn,
                campo_titular.strip(),
                campo_email.strip(),
                campo_telefono.strip(),
                campo_direccion.strip(),
                campo_ciudad.strip(),
                campo_provincia.strip(),
                cuit_normalizado,
            )
            if nuevo_id:
                st.success(
                    f"✅ Cliente **{campo_titular.strip()}** creado correctamente (ID: {nuevo_id}). "
                    "El historial se actualizará al recargar."
                )
                # Limpiar bandera y marcar para recargar indicadores
                flag = f"asistente_activo_{titular}"
                if flag in st.session_state:
                    del st.session_state[flag]
                if 'clientes_data' in st.session_state:
                    del st.session_state['clientes_data']
                return True
            else:
                st.error("❌ No se pudo crear el cliente. Intente nuevamente.")
                return False
        except Exception as ex:
            st.error(f"❌ Error al crear el cliente: {ex}")
            return False

    return False


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
                # DataFrame completo para historial y búsquedas
                df_all = pd.DataFrame(rows, columns=columns)

                # Indicadores de vinculación Cliente/Email/Marcas (solo para visibilidad en la UI).
                # Se usan comparaciones normalizadas (misma lógica que el JOIN SQL) para que
                # "ROSSI, NATALIA" y "ROSSI NATALIA" se reconozcan como el mismo titular.
                if 'titular' in df_all.columns:
                    try:
                        clientes_rows, clientes_cols = obtener_clientes(conn, force_refresh=False)
                        df_clientes = pd.DataFrame(clientes_rows, columns=clientes_cols) if clientes_rows else pd.DataFrame()

                        if not df_clientes.empty and 'titular' in df_clientes.columns:
                            df_clientes['titular'] = df_clientes['titular'].astype(str)
                            df_all['titular'] = df_all['titular'].astype(str)

                            # Columna normalizada en clientes (Python-side, misma función que la UDF SQL)
                            df_clientes['_titular_norm'] = df_clientes['titular'].map(_normalizar_titular)
                            # Columna normalizada en boletines
                            df_all['_titular_norm'] = df_all['titular'].map(_normalizar_titular)

                            # tiene_cliente: hay algún cliente cuyo nombre normalizado coincide
                            norm_con_cliente = set(df_clientes['_titular_norm'].dropna().unique())
                            df_all['tiene_cliente'] = df_all['_titular_norm'].isin(norm_con_cliente)

                            # tiene_email: el cliente con ese nombre tiene email no vacío
                            df_clientes['email_str'] = df_clientes['email'].fillna('').astype(str).str.strip()
                            norm_con_email = set(
                                df_clientes[df_clientes['email_str'] != '']['_titular_norm'].dropna().unique()
                            )
                            df_all['tiene_email'] = df_all['_titular_norm'].isin(norm_con_email)

                            # tiene_marcas_vinculadas
                            if 'tiene_marcas' in df_clientes.columns:
                                norm_con_marcas = set(
                                    df_clientes[df_clientes['tiene_marcas'] == 1]['_titular_norm'].dropna().unique()
                                )
                                df_all['tiene_marcas_vinculadas'] = df_all['_titular_norm'].isin(norm_con_marcas)

                            # Limpiar columna auxiliar (no debe aparecer en la UI)
                            df_all.drop(columns=['_titular_norm'], inplace=True, errors='ignore')
                    except Exception as e:
                        # Si algo falla, no interrumpir la carga del historial
                        st.debug(f"Error calculando indicadores de vinculación: {e}") if hasattr(st, "debug") else None

                # Por defecto, trabajamos con un subconjunto visible
                df_visible = df_all.copy()

                # Filtrado principal: últimos 30 días o importancia "Pendiente"
                if 'fecha_boletin' in df_all.columns:
                    # Convertir la columna de fecha a datetime de forma segura
                    df_all['fecha_boletin'] = pd.to_datetime(df_all['fecha_boletin'],dayfirst=True,errors='coerce')

                    # Calcular rango de últimos 30 días
                    hoy = date.today()
                    desde = hoy - timedelta(days=30)

                    # Registros dentro del rango [desde, hoy]
                    mask_rango = df_all['fecha_boletin'].dt.date.between(desde, hoy)

                    # Registros pendientes por importancia, independientemente de la fecha
                    if 'importancia' in df_all.columns:
                        mask_pendientes = df_all['importancia'] == "Pendiente"
                    else:
                        mask_pendientes = pd.Series(False, index=df_all.index)

                    mask_visible = mask_rango | mask_pendientes
                    df_visible = df_all[mask_visible].copy()

                    if df_visible.empty:
                        st.info("📅 No hay boletines recientes ni pendientes. Usa el buscador inferior para ver el historial completo.")
                else:
                    st.warning("⚠️ No se encontró la columna 'fecha_boletin'. Se muestra el historial completo sin filtrar por fecha.")
                    df_visible = df_all.copy()

                # Panel de asistente: titulares sin cliente o sin email en todo el historial (df_all)
                if 'tiene_cliente' in df_all.columns or 'tiene_email' in df_all.columns:
                    titulares_sin_cliente = set()
                    titulares_sin_email = set()

                    if 'tiene_cliente' in df_all.columns:
                        titulares_sin_cliente = set(
                            df_all[~df_all['tiene_cliente']]['titular'].dropna().unique()
                        )
                    if 'tiene_email' in df_all.columns:
                        titulares_sin_email = set(
                            df_all[~df_all['tiene_email']]['titular'].dropna().unique()
                        )

                    titulares_necesitan_cliente = titulares_sin_cliente | titulares_sin_email

                    if titulares_necesitan_cliente:
                        titulares_ordenados = sorted(titulares_necesitan_cliente)

                        # Diagnóstico técnico solo visible para rol admin (RBAC)
                        if (st.session_state.get("user_info") or {}).get("role") == "admin":
                            with st.expander("🔍 Diagnóstico de vinculación (técnico)", expanded=False):
                                st.caption(
                                    "Ejecuta un diagnóstico para verificar si la normalización de nombres "
                                    "funciona correctamente y por qué ciertos titulares no se vinculan."
                                )
                                if st.button("▶ Ejecutar diagnóstico ahora", key="_btn_diagnostico_vinculacion"):
                                    with st.spinner("Analizando..."):
                                        try:
                                            conn_diag = crear_conexion()
                                            diag = diagnosticar_vinculacion(conn_diag, max_filas=30)
                                            conn_diag.close()

                                            st.write(f"**Python:** {diag.get('python_version', '?')}")
                                            st.write(f"**Base de datos:** `{diag.get('db_path', '?')}`")

                                            if diag.get("udf_ok"):
                                                st.success(
                                                    f"✅ UDF `normalizar_titular` activa — "
                                                    f"`'ROSSI, NATALIA'` → `'{diag['udf_resultado']}'`"
                                                )
                                            else:
                                                st.error(
                                                    f"❌ UDF `normalizar_titular` NO funciona: "
                                                    f"{diag.get('udf_resultado', 'sin resultado')}. "
                                                    "El JOIN usará coincidencia exacta y fallará para formatos distintos."
                                                )

                                            sin_cliente = diag.get("sin_cliente", [])
                                            if sin_cliente:
                                                st.warning(
                                                    f"⚠️ {len(sin_cliente)} titular(es) sin cliente después de normalizar:"
                                                )
                                                for item in diag.get("muestra_norm", []):
                                                    with st.expander(
                                                        f"📋 `{item['boletin_original']}` → norm: `{item['boletin_normalizado']}`",
                                                        expanded=True
                                                    ):
                                                        st.write("**Clientes en BD (normalizados):**")
                                                        for c in item.get("clientes_normalizados", []):
                                                            match = "✅" if c["normalizado"] == item["boletin_normalizado"] else "❌"
                                                            st.write(
                                                                f"{match} `{c['original']}` → `{c['normalizado']}`"
                                                            )
                                            else:
                                                st.success("✅ Todos los titulares visibles tienen cliente vinculado vía normalización.")

                                            if "error" in diag:
                                                st.error(f"Error en diagnóstico: {diag['error']}")
                                        except Exception as e:
                                            st.error(f"Error ejecutando diagnóstico: {e}")

                        alguno_activo = any(
                            st.session_state.get(f"asistente_activo_{t}", False)
                            for t in titulares_ordenados
                        )

                        with st.expander(
                            f"👤 {len(titulares_necesitan_cliente)} titular(es) sin cliente/email — "
                            "Asistente de creación rápida",
                            expanded=alguno_activo
                        ):
                            st.caption(
                                "Estos titulares tienen reportes pero no tienen un cliente con email asociado. "
                                "Crea el cliente directamente desde aquí sin salir de la pantalla."
                            )

                            for titular_pendiente in titulares_ordenados:
                                motivo = []
                                if titular_pendiente in titulares_sin_cliente:
                                    motivo.append("sin cliente")
                                elif titular_pendiente in titulares_sin_email:
                                    motivo.append("sin email")
                                motivo_str = " · ".join(motivo)

                                flag_key = f"asistente_activo_{titular_pendiente}"
                                ya_activo = st.session_state.get(flag_key, False)

                                col_t, col_btn = st.columns([4, 1])
                                with col_t:
                                    st.markdown(
                                        f"**{titular_pendiente}** "
                                        f"<span style='color:#f59e0b;font-size:0.85rem;'>({motivo_str})</span>",
                                        unsafe_allow_html=True
                                    )
                                with col_btn:
                                    if not ya_activo:
                                        if st.button(
                                            "➕ Crear cliente",
                                            key=f"btn_asistente_{titular_pendiente[:30]}",
                                            use_container_width=True
                                        ):
                                            st.session_state[flag_key] = True
                                            st.rerun()
                                    else:
                                        st.caption("✏️ Formulario abierto ↓")

                                form_slot = st.container()
                                if ya_activo:
                                    with form_slot:
                                        creado = _asistente_crear_cliente(
                                            conn,
                                            titular=titular_pendiente,
                                        )
                                        if creado:
                                            st.rerun()

                # Sección de métricas y grid solo si hay datos visibles
                if not df_visible.empty:
                    # Mostrar métricas usando solo los datos visibles
                    total_boletines = len(df_visible)
                    st.subheader(f"📈 Métricas Generales")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Boletines", total_boletines)
                    
                    with col2:
                        alta_importancia = len(
                            [r for _, r in df_visible.iterrows()
                             if 'importancia' in r and r['importancia'] == "Alta"]
                        )
                        st.metric("🔴 Alta Importancia", alta_importancia)
                    
                    with col3:
                        baja_importancia = len(
                            [r for _, r in df_visible.iterrows()
                             if 'importancia' in r and r['importancia'] == "Baja"]
                        )
                        st.metric("🟡 Baja Importancia", baja_importancia)
                    
                    with col4:
                        pendientes = len(
                            [r for _, r in df_visible.iterrows()
                             if 'importancia' in r and r['importancia'] == "Pendiente"]
                        )
                        st.metric("⚠️ Pendientes", pendientes)
                    
                    # Mostrar advertencia si hay registros pendientes
                    if pendientes > 0:
                        st.warning(
                            "⚠️ Hay registros marcados como 'Pendiente'. "
                            "Puedes cambiar la importancia haciendo clic en la celda correspondiente del grid."
                        )
                    
                    st.markdown("---")

                    # Convertir tipos de datos correctamente en el subconjunto visible
                    if 'reporte_enviado' in df_visible.columns:
                        df_visible['reporte_enviado'] = df_visible['reporte_enviado'].astype(bool)
                    if 'reporte_generado' in df_visible.columns:
                        df_visible['reporte_generado'] = df_visible['reporte_generado'].astype(bool)
                    
                    # Aplicar filtros avanzados sobre el subconjunto visible
                    df_filtered = _apply_filters(df_visible)
                    
                    # Aplicar la conversión visual también al DataFrame filtrado
                    df_filtered_display = df_filtered.copy()
                    if 'reporte_enviado' in df_filtered_display.columns:
                        df_filtered_display['reporte_enviado'] = df_filtered_display['reporte_enviado'].map(
                            {True: '●', False: '○'}
                        )
                    if 'reporte_generado' in df_filtered_display.columns:
                        df_filtered_display['reporte_generado'] = df_filtered_display['reporte_generado'].map(
                            {True: '●', False: '○'}
                        )
                    # Indicadores visuales para vinculación Cliente/Email/Marcas (solo UI)
                    for col in ['tiene_cliente', 'tiene_email', 'tiene_marcas_vinculadas']:
                        if col in df_filtered_display.columns:
                            df_filtered_display[col] = df_filtered_display[col].map(
                                {True: '✅', False: '❌'}
                            )
                    
                    # Actualizar métricas con datos filtrados
                    total_filtrados = len(df_filtered)
                    if total_filtrados != total_boletines:
                        st.info(f"📊 Mostrando {total_filtrados} de {total_boletines} registros")
                    
                    # Mostrar datos en grid usando el servicio de boletines
                    st.subheader("📋 Datos del Historial")
                    #st.caption(
                        #"Las columnas 'tiene_cliente', 'tiene_email' y 'tiene_marcas_vinculadas' "
                        #"muestran el estado actual de vinculación necesario para el envío de emails. "
                        #"Solo son indicadores visuales: no modifican la lógica de negocio."
                    #)
                    
                    # Usar el grid específico para boletines que incluye edición de importancia
                    GridService.show_bulletin_grid(
                        df=df_filtered_display,
                        key="historial_grid"
                    )

                # Sección de búsqueda en el historial completo (incluye registros antiguos procesados)
                st.markdown("---")
                st.markdown("### 🔎 Buscar en historial completo")
                
                search_term = st.text_input(
                    "Buscar en todo el historial (titular, número de boletín, expediente, etc.)",
                    placeholder="Escribe para buscar también en registros antiguos procesados..."
                )

                if search_term:
                    df_search = df_all.copy()
                    # Máscara de búsqueda sobre varias columnas relevantes
                    mask_search = pd.Series(False, index=df_search.index)
                    columnas_busqueda = [
                        "titular",
                        "numero_boletin",
                        "numero_orden",
                        "numero_expediente",
                        "marca_custodia",
                        "marca_publicada",
                    ]
                    for col in columnas_busqueda:
                        if col in df_search.columns:
                            mask_search |= df_search[col].astype(str).str.contains(
                                search_term, case=False, na=False
                            )

                    df_search = df_search[mask_search].copy()

                    if df_search.empty:
                        st.info("🔍 No se encontraron registros en el historial completo para ese término.")
                    else:
                        st.markdown("#### Resultados en historial completo")

                        # Tipos y visualización coherentes con el grid principal
                        if 'reporte_enviado' in df_search.columns:
                            df_search['reporte_enviado'] = df_search['reporte_enviado'].astype(bool)
                        if 'reporte_generado' in df_search.columns:
                            df_search['reporte_generado'] = df_search['reporte_generado'].astype(bool)

                        df_search_display = df_search.copy()
                        if 'reporte_enviado' in df_search_display.columns:
                            df_search_display['reporte_enviado'] = df_search_display['reporte_enviado'].map(
                                {True: '●', False: '○'}
                            )
                        if 'reporte_generado' in df_search_display.columns:
                            df_search_display['reporte_generado'] = df_search_display['reporte_generado'].map(
                                {True: '●', False: '○'}
                            )

                        # Indicadores visuales también en resultados del historial completo
                        for col in ['tiene_cliente', 'tiene_email', 'tiene_marcas_vinculadas']:
                            if col in df_search_display.columns:
                                df_search_display[col] = df_search_display[col].map(
                                    {True: '✅', False: '❌'}
                                )

                        GridService.show_bulletin_grid(
                            df=df_search_display,
                            key="historial_search_grid"
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
