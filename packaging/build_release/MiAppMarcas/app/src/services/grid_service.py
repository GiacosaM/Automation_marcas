"""
Servicio para manejo de grids y tablas
"""
import streamlit as st
import pandas as pd
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from typing import Dict, Any, Optional, Tuple
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import crear_conexion, actualizar_registro
from src.config.constants import BULLETIN_COLUMNS, CLIENT_COLUMNS, MARCA_COLUMNS, GRID_CONFIG
from src.utils.session_manager import SessionManager


class GridService:
    """Servicio para manejo de grids con ag-Grid"""
    
    @staticmethod
    def _configure_bulletin_grid(gb: GridOptionsBuilder) -> None:
        """Configurar grid para boletines"""
        # Configuración base
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=GRID_CONFIG["pagination_page_size"]
        )
        gb.configure_selection(selection_mode='single', use_checkbox=True)
        
        # Configuración por defecto de columnas
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            editable=False,
            sortable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True,
            minWidth=GRID_CONFIG["min_column_width"]
        )
        
        # Configurar columnas específicas
        for column, config in BULLETIN_COLUMNS.items():
            gb.configure_column(column, **config)
    
    @staticmethod
    def _configure_client_grid(gb: GridOptionsBuilder) -> None:
        """Configurar grid para clientes"""
        # Configuración base
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=GRID_CONFIG["clients_pagination_page_size"]
        )
        gb.configure_selection(selection_mode='single', use_checkbox=True)
        
        # Configuración por defecto - EDITABLE
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            editable=True,
            sortable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True,
            minWidth=GRID_CONFIG["min_column_width"],
            flex=1,
            singleClickEdit=True
        )
        
        # Configurar columnas específicas
        for column, config in CLIENT_COLUMNS.items():
            gb.configure_column(column, **config)
        
        # Configurar opciones adicionales para edición
        gb.configure_grid_options(
            enableRangeSelection=True,
            stopEditingWhenCellsLoseFocus=True,
            suppressClickEdit=False
        )
    
    @staticmethod
    def _handle_importance_changes(grid_response):
        """Procesa cambios de importancia en el grid"""
        # Limpiar el tracking de cambios para permitir procesar todos los cambios en cada edición
        import streamlit as st
        if 'cambios_procesados' in st.session_state:
            st.session_state.cambios_procesados.clear()
        if not grid_response or not hasattr(grid_response, 'data'):
            return False
        from database import crear_conexion as get_db_connection, obtener_datos, actualizar_registro
        import pandas as pd
        try:
            current_data = pd.DataFrame(grid_response.data)
            conn = get_db_connection()
            original_rows, original_columns = obtener_datos(conn)
            original_df = pd.DataFrame(original_rows, columns=original_columns)
            conn.close()
            cambios_realizados = False
            for index, row in current_data.iterrows():
                # Usar un change_id único por registro
                change_id = f"importance_{row['id']}"
                if SessionManager.track_change(change_id):
                    continue
                original_row = original_df[original_df['id'] == int(row['id'])].iloc[0]
                # Solo actualizar si la importancia realmente cambió
                if str(row['importancia']) != str(original_row['importancia']):
                    conn = None
                    try:
                        conn = get_db_connection()
                        if conn:
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
                                bool(original_row['reporte_enviado']),
                                row['titular'],
                                bool(original_row['reporte_generado']),
                                row['importancia']
                            )
                            st.success(f"✅ Importancia actualizada a '{row['importancia']}'")
                            cambios_realizados = True
                            time.sleep(0.2)
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")
                        SessionManager.untrack_change(change_id)
                    finally:
                        if conn:
                            conn.close()
            if cambios_realizados:
                st.rerun()
                return True
        except Exception as e:
            st.error(f"Error procesando cambios: {e}")
            return False
        return False
    
    @staticmethod
    def show_bulletin_grid(df: pd.DataFrame, key: str) -> Dict[str, Any]:
        """
        Mostrar grid de boletines con funcionalidad de edición de importancia
        
        Args:
            df: DataFrame con los datos de boletines
            key: Clave única para el grid
            
        Returns:
            Respuesta del grid
        """
        # Orden visual: titular (pinned), id, clase, clases_acta, numero_orden, importancia, resto
        priority_cols = ['titular', 'id', 'clase', 'clases_acta', 'numero_orden', 'importancia']
        ordered = [c for c in priority_cols if c in df.columns]
        ordered += [c for c in df.columns if c not in ordered]
        df = df[ordered]

        gb = GridOptionsBuilder.from_dataframe(df)
        GridService._configure_bulletin_grid(gb)
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
            height=GRID_CONFIG["grid_height"]
        )
        
        # Manejar cambios en la importancia
        GridService._handle_importance_changes(grid_response)
        
        return grid_response
    
    @staticmethod
    def show_client_grid(df: pd.DataFrame, key: str) -> Dict[str, Any]:
        """
        Mostrar grid de clientes con funcionalidad de edición
        
        Args:
            df: DataFrame con los datos de clientes
            key: Clave única para el grid
            
        Returns:
            Respuesta del grid
        """
        gb = GridOptionsBuilder.from_dataframe(df)
        GridService._configure_client_grid(gb)
        grid_options = gb.build()
        
        # Mostrar el grid
        # Asegurar que tiene_marcas sea un entero
        if 'tiene_marcas' in df.columns:
            df['tiene_marcas'] = df['tiene_marcas'].apply(lambda x: '✅' if x == 1 else '❌')
        
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key=key,
            allow_unsafe_jscode=True,
            height=GRID_CONFIG["clients_grid_height"],
            width='100%'
        )
        
        return grid_response
    
    @staticmethod
    def _configure_marca_grid(gb: GridOptionsBuilder) -> None:
        """
        Configura el grid de marcas en modo SOLO LECTURA con selección por checkbox.

        La columna técnica '_select' (ya insertada en el DataFrame por show_marca_grid)
        actúa como soporte exclusivo del checkbox — desacopla el widget de selección
        de cualquier columna de negocio y garantiza que siempre aparezca como
        primera columna fija a la izquierda.
        """
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=GRID_CONFIG.get("marcas_pagination_page_size", 15)
        )

        gb.configure_selection(
            selection_mode='single',
            use_checkbox=True
        )

        # Columnas de negocio: solo lectura
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            editable=False,
            sortable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True,
            minWidth=GRID_CONFIG["min_column_width"],
            flex=1,
            singleClickEdit=False,
            suppressClickEdit=True
        )

        # Columnas específicas de marca (forzar editable=False)
        for column, config in MARCA_COLUMNS.items():
            gb.configure_column(column, **{**config, 'editable': False})

        # Estilos condicionales por fila: ámbar para marcas sin cliente vinculado.
        # DEBE ser JsCode — AgGrid espera una función JS, no un string.
        # El guard "!params.data" previene el error cuando la fila es undefined
        # (cabecera flotante, filas de grupo, etc.).
        row_style_sin_cliente = JsCode("""
function(params) {
    if (!params.data) return null;
    var cid = params.data.cliente_id;
    if (cid === null || cid === undefined || cid === '') {
        return { 'background-color': '#fff3cd', 'color': '#856404' };
    }
    return null;
}
""")

        # Opciones base del grid.
        # allow_unsafe_jscode=True ya está activo en la llamada a AgGrid.
        gb.configure_grid_options(
            rowSelection='single',
            suppressRowClickSelection=True,
            suppressCellFocus=True,
            enableRangeSelection=False,
            undoRedoCellEditing=False,
            getRowStyle=row_style_sin_cliente,
        )

        # Columna técnica exclusiva para el checkbox.
        # checkboxSelection=True en esta columna es lo que hace que AgGrid
        # renderice la celda del checkbox; sin esto el widget no aparece.
        # pinned="left" la ancla como primera columna visible.
        gb.configure_column(
            '_select',
            header_name='',
            width=50,
            checkboxSelection=True,
            headerCheckboxSelection=False,
            pinned='left',
            editable=False,
            sortable=False,
            filter=False,
            resizable=False,
            suppressMenu=True
        )

    @staticmethod
    def show_marca_grid(df: pd.DataFrame, key: str) -> Dict[str, Any]:
        """
        Muestra el grid de marcas en modo solo lectura con selección por checkbox.

        Inserta una columna técnica '_select' como primera columna del DataFrame
        de trabajo para anclar el checkbox de selección de forma garantizada,
        independientemente del esquema real de la tabla Marcas.
        La columna '_select' se elimina de selected_rows antes de devolverla.

        Args:
            df: DataFrame con los datos de marcas.
            key: Clave única para el grid.

        Returns:
            dict con 'data' (DataFrame original) y
            'selected_rows' (lista de dicts sin '_select', siempre inicializada).
        """
        # DataFrame de trabajo con la columna técnica de selección
        df_grid = df.copy()
        df_grid.insert(0, '_select', '')

        gb = GridOptionsBuilder.from_dataframe(df_grid)
        GridService._configure_marca_grid(gb)
        grid_options = gb.build()

        aggrid_response = AgGrid(
            df_grid,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key=key,
            allow_unsafe_jscode=True,
            height=GRID_CONFIG.get("marcas_grid_height", 500),
            width='100%'
        )

        # AgGridReturn es de solo lectura — construimos un dict propio.
        # Normalizamos el tipo (DataFrame vs lista según versión de st-aggrid)
        # y eliminamos la columna técnica '_select' para que el resto del código
        # reciba exactamente la misma estructura que tenía el DataFrame original.
        raw_selection = aggrid_response.get('selected_rows', [])
        if isinstance(raw_selection, pd.DataFrame):
            selected_rows = raw_selection.to_dict('records')
        elif raw_selection is None:
            selected_rows = []
        else:
            selected_rows = list(raw_selection)

        # Quitar '_select' de cada fila seleccionada
        selected_rows = [
            {k: v for k, v in row.items() if k != '_select'}
            for row in selected_rows
        ]

        return {
            'data': aggrid_response.get('data'),
            'selected_rows': selected_rows,
        }
    
    @staticmethod
    def create_simple_grid(df: pd.DataFrame, key: str, 
                          selection_mode: str = 'single',
                          height: int = 400) -> Dict[str, Any]:
        """
        Crear un grid simple sin configuraciones especiales
        
        Args:
            df: DataFrame a mostrar
            key: Clave única para el grid
            selection_mode: Modo de selección ('single' o 'multiple')
            height: Altura del grid
            
        Returns:
            Respuesta del grid
        """
        gb = GridOptionsBuilder.from_dataframe(df)
        
        gb.configure_pagination(enabled=True, paginationPageSize=10)
        gb.configure_selection(selection_mode=selection_mode, use_checkbox=True)
        gb.configure_default_column(
            editable=False,
            sortable=True,
            filterable=True,
            resizable=True
        )
        
        grid_options = gb.build()
        
        return AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key=key,
            height=height
        )
    
    @staticmethod
    def show_user_grid(df: pd.DataFrame, key: str) -> Dict[str, Any]:
        """
        Mostrar grid de usuarios con funcionalidad de edición

        Args:
            df: DataFrame con los datos de usuarios
            key: Clave única para el grid

        Returns:
            Respuesta del grid
        """
        gb = GridOptionsBuilder.from_dataframe(df)
        GridService._configure_user_grid(gb)
        grid_options = gb.build()

        # Mostrar el grid
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key=key,
            allow_unsafe_jscode=True,
            height=GRID_CONFIG.get("users_grid_height", 400),
            width='100%',
            reload_data=False
        )

        return grid_response

    @staticmethod
    def _configure_user_grid(gb: GridOptionsBuilder) -> None:
        """Configurar grid para usuarios"""
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=GRID_CONFIG.get("users_pagination_page_size", 10)
        )
        gb.configure_selection(selection_mode='single', use_checkbox=True)

        # Configuración por defecto de columnas
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            editable=True,
            sortable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True,
            minWidth=GRID_CONFIG["min_column_width"]
        )
        
    @staticmethod
    def create_grid(df: pd.DataFrame, key: str, 
                   height: int = 400, 
                   selection_mode: str = 'single',
                   fit_columns: bool = False,
                   editable: bool = False,
                   custom_column_defs: list = None) -> Dict[str, Any]:
        """
        Crear un grid configurable para datos generales
        
        Args:
            df: DataFrame a mostrar
            key: Clave única para el grid
            height: Altura del grid
            selection_mode: Modo de selección ('single' o 'multiple')
            fit_columns: Ajustar columnas automáticamente
            editable: Permitir edición de celdas
            custom_column_defs: Lista de definiciones personalizadas para columnas
            
        Returns:
            Respuesta del grid
        """
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configuración básica
        gb.configure_pagination(
            enabled=True, 
            paginationAutoPageSize=False,
            paginationPageSize=10
        )
        gb.configure_selection(selection_mode=selection_mode, use_checkbox=True)
        
        # Configuración de columnas
        gb.configure_default_column(
            editable=editable,
            sortable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True
        )
        
        # Aplicar configuraciones personalizadas de columnas si existen
        if custom_column_defs:
            for col_def in custom_column_defs:
                # Hacer una copia para no modificar el original
                col_def_copy = col_def.copy()
                field_name = col_def_copy.pop("field", None)
                if field_name is None:
                    continue  # Saltar esta columna si no tiene el campo field
                header_name = col_def_copy.pop("headerName", field_name)
                gb.configure_column(field_name, headerName=header_name, **col_def_copy)
        
        grid_options = gb.build()
        
        return AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED if editable else GridUpdateMode.NO_UPDATE,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=fit_columns,
            theme='streamlit',
            key=key,
            height=height
        )
