"""
Página de clientes optimizada con paginación y caching
"""
import streamlit as st
import sys
import os
import time
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Importar componentes del sistema original
from database import crear_conexion, crear_tabla, insertar_cliente, actualizar_cliente, eliminar_cliente

# Importar nuevas utilidades optimizadas
from src.utils.db_optimizations import obtener_clientes_optimizado, time_query
from src.utils.connection_pool import optimized_db_client
from src.ui.components import UIComponents

class ClientesPageOptimized:
    """Página de clientes optimizada"""
    
    def __init__(self):
        # Inicializar estado de sesión si no existe
        if 'page' not in st.session_state:
            st.session_state['page'] = 1
        if 'page_size' not in st.session_state:
            st.session_state['page_size'] = 25
        if 'search_query' not in st.session_state:
            st.session_state['search_query'] = ""
    
    @time_query
    def show(self):
        """Mostrar página de clientes"""
        st.title("👥 Gestión de Clientes (Optimizado)")
        
        # Barra de búsqueda y controles
        self._show_search_controls()
        
        # Tabla de clientes con paginación
        self._show_clients_table()
        
        # Controles para agregar clientes
        self._show_add_client_form()
    
    def _show_search_controls(self):
        """Mostrar controles de búsqueda"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Búsqueda con debounce
            search_query = st.text_input(
                "🔍 Buscar cliente por nombre, CUIT o email",
                value=st.session_state.get('search_query', "")
            )
            
            # Actualizar búsqueda en session_state
            if search_query != st.session_state.get('search_query', ""):
                st.session_state['search_query'] = search_query
                st.session_state['page'] = 1  # Volver a primera página
        
        with col2:
            # Selector de tamaño de página
            page_size = st.selectbox(
                "Registros por página",
                options=[10, 25, 50, 100],
                index=1  # Default: 25
            )
            
            if page_size != st.session_state.get('page_size'):
                st.session_state['page_size'] = page_size
                st.session_state['page'] = 1  # Volver a primera página
        
        with col3:
            # Botón para refrescar
            if st.button("🔄 Refrescar", use_container_width=True):
                # Limpiar caché de la función
                obtener_clientes_optimizado.clear()
                st.experimental_rerun()
    
    def _show_clients_table(self):
        """Mostrar tabla de clientes con paginación"""
        start_time = time.time()
        
        # Obtener conexión
        conn = crear_conexion()
        
        # Preparar filtros basados en la búsqueda
        filtros = {}
        if st.session_state.get('search_query'):
            search = st.session_state['search_query']
            # Aquí podemos elegir en qué campo buscar basado en el formato
            if '@' in search:  # Parece un email
                filtros['email'] = search
            elif search.isdigit() or '-' in search:  # Parece un CUIT
                filtros['cuit'] = search
            else:  # Asumimos que es un nombre
                filtros['titular'] = search
        
        try:
            # Usar la versión optimizada con paginación
            rows, columns, pagination = obtener_clientes_optimizado(
                conn,
                page=st.session_state['page'],
                page_size=st.session_state['page_size'],
                filtro=filtros
            )
            
            # Mostrar estadísticas y tiempo
            end_time = time.time()
            query_time = end_time - start_time
            
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; padding: 0.5rem 0;'>
                <span>📊 {pagination['total_records']} clientes | Página {pagination['current_page']} de {pagination['total_pages']}</span>
                <span style='color:gray;'>⏱️ {query_time:.3f}s</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar tabla de clientes
            if rows:
                # Convertir a dataframe para la tabla
                import pandas as pd
                df = pd.DataFrame(rows, columns=columns)
                
                # Tabla interactiva
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "id": st.column_config.Column("ID", width="small"),
                        "titular": st.column_config.Column("Titular", width="large"),
                        "email": st.column_config.Column("Email", width="medium"),
                        "telefono": st.column_config.Column("Teléfono", width="medium"),
                        "cuit": st.column_config.Column("CUIT", width="medium")
                    }
                )
                
                # Controles de paginación
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("◀️ Anterior", disabled=pagination['current_page'] <= 1):
                        st.session_state['page'] -= 1
                        st.experimental_rerun()
                
                with col2:
                    # Mini navegador de páginas
                    pages_to_show = min(5, pagination['total_pages'])
                    page_cols = st.columns(pages_to_show)
                    
                    start_page = max(1, min(
                        pagination['current_page'] - pages_to_show // 2,
                        pagination['total_pages'] - pages_to_show + 1
                    ))
                    
                    for i, col in enumerate(page_cols):
                        page_num = start_page + i
                        if page_num <= pagination['total_pages']:
                            with col:
                                if st.button(
                                    f"{page_num}",
                                    use_container_width=True,
                                    type="primary" if page_num == pagination['current_page'] else "secondary"
                                ):
                                    st.session_state['page'] = page_num
                                    st.experimental_rerun()
                
                with col3:
                    if st.button("▶️ Siguiente", disabled=pagination['current_page'] >= pagination['total_pages']):
                        st.session_state['page'] += 1
                        st.experimental_rerun()
            else:
                st.info("No se encontraron clientes")
        
        except Exception as e:
            st.error(f"Error al cargar clientes: {e}")
        
        finally:
            if conn:
                conn.close()
    
    def _show_add_client_form(self):
        """Mostrar formulario para agregar clientes"""
        with st.expander("➕ Agregar Nuevo Cliente"):
            with st.form("nuevo_cliente_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    titular = st.text_input("Titular/Razón Social *", key="new_titular")
                    email = st.text_input("Email *", key="new_email")
                    telefono = st.text_input("Teléfono", key="new_telefono")
                
                with col2:
                    cuit = st.text_input("CUIT *", key="new_cuit")
                    direccion = st.text_input("Dirección", key="new_direccion")
                    ciudad = st.text_input("Ciudad", key="new_ciudad")
                    provincia = st.text_input("Provincia", key="new_provincia")
                
                submit = st.form_submit_button("Guardar Cliente")
                
                if submit:
                    if not titular or not email or not cuit:
                        st.error("❌ Titular, Email y CUIT son campos obligatorios")
                    else:
                        try:
                            conn = crear_conexion()
                            if conn:
                                resultado = insertar_cliente(
                                    conn, titular, email, telefono, direccion,
                                    ciudad, provincia, cuit
                                )
                                if resultado:
                                    st.success(f"✅ Cliente {titular} agregado correctamente")
                                    # Limpiar caché para actualizar lista
                                    obtener_clientes_optimizado.clear()
                                else:
                                    st.error("❌ Error al insertar cliente")
                                conn.close()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

def show_clientes_optimized_page():
    """Función para mostrar la página de clientes optimizada"""
    clientes_page = ClientesPageOptimized()
    clientes_page.show()

if __name__ == "__main__":
    show_clientes_optimized_page()
