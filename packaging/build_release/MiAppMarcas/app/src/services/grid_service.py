"""
Servicio para manejo de grids y tablas
"""
import streamlit as st
import pandas as pd
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from typing import Dict, Any, Optional, Tuple
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import crear_conexion, actualizar_registro
from src.config.constants import BULLETIN_COLUMNS, CLIENT_COLUMNS, GRID_CONFIG
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
            sorteable=True,
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
            sorteable=True,
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
            sorteable=True,
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
            sorteable=True,
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
            sorteable=True,
            filterable=True,
            resizable=True,
            wrapText=True,
            autoHeight=True
        )
        
        # Aplicar configuraciones personalizadas de columnas si existen
        if custom_column_defs:
            for col_def in custom_column_defs:
                field_name = col_def.pop("field")
                header_name = col_def.pop("headerName", field_name)
                gb.configure_column(field_name, headerName=header_name, **col_def)
        
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
