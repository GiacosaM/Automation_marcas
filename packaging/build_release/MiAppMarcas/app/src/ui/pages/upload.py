"""
Página de carga de datos
"""
import streamlit as st
import pandas as pd
import sys
import os
from streamlit_extras.grid import grid

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from database import crear_conexion, insertar_datos
from extractor import extraer_datos_agrupados
from src.ui.components import UIComponents
from src.utils.session_manager import SessionManager


class UploadPage:
    """Página de carga de boletines"""
    
    def __init__(self):
        self.max_file_size_kb = 10240  # 10MB
    
    def _validate_file(self, archivo) -> bool:
        """Validar el archivo cargado"""
        if not archivo:
            return False
        
        # Validar tamaño
        size_kb = archivo.size / 1024
        if size_kb > self.max_file_size_kb:
            st.error(f"❌ El archivo es demasiado grande ({size_kb:.1f} KB). Máximo permitido: {self.max_file_size_kb} KB")
            return False
        
        # Validar tipo
        if not archivo.name.endswith('.xlsx'):
            st.error("❌ Solo se permiten archivos .xlsx")
            return False
        
        return True
    
    def _process_file(self, archivo) -> tuple:
        """
        Procesar el archivo Excel
        
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            # Extraer datos agrupados
            datos_agrupados = extraer_datos_agrupados(df)
            
            if not datos_agrupados:
                return False, None, "No se pudieron extraer datos válidos del archivo"
            
            return True, datos_agrupados, None
            
        except Exception as e:
            return False, None, f"Error al procesar el archivo: {str(e)}"
    
    def _show_file_info(self, archivo) -> None:
        """Mostrar información del archivo cargado"""
        size_kb = round(archivo.size / 1024, 1)
        
        info_html = UIComponents.create_file_info_card(
            archivo.name,
            size_kb,
            archivo.type
        )
        
        st.markdown(info_html, unsafe_allow_html=True)
    
    def _show_data_preview(self, datos_agrupados: dict) -> None:
        """Mostrar vista previa de los datos"""
        total_registros = sum(len(registros) for registros in datos_agrupados.values())
        total_titulares = len(datos_agrupados)
        
        # Métricas del archivo
        metrics = [
            {
                'value': total_registros,
                'label': '📄 Total Registros',
                'color': '#667eea'
            },
            {
                'value': total_titulares,
                'label': '👥 Titulares Únicos',
                'color': '#28a745'
            },
            {
                'value': f"{total_registros/total_titulares:.1f}" if total_titulares > 0 else "0",
                'label': '📊 Promedio por Titular',
                'color': '#17a2b8'
            }
        ]
        
        UIComponents.create_metric_grid(metrics, columns=3)
        
        # Vista previa de datos con mejor estilo
        with st.expander("🔍 Vista Previa de Datos", expanded=True):
            st.markdown("""
            <div style="color: #e5e5e5; margin-bottom: 1.5rem;">
                <h3 style="color: #e5e5e5 !important; margin-bottom: 0.5rem;">Primeros registros por titular:</h3>
                <p style="color: #888; margin: 0; font-size: 0.9em;">Se muestran hasta 5 titulares como ejemplo</p>
            </div>
            """, unsafe_allow_html=True)
            
            count = 0
            for titular, registros in list(datos_agrupados.items())[:5]:  # Mostrar solo 5 titulares
                if registros:
                    primer_registro = registros[0]
                    
                    # Extraer datos del registro
                    boletin = primer_registro.get('Número de Boletín', 'N/A')
                    marca = primer_registro.get('Marca en Custodia', 'N/A')
                    clase = primer_registro.get('Clase', 'N/A')
                    expediente = primer_registro.get('Expediente', 'N/A')
                    solicitante = primer_registro.get('Solicitante', 'N/A')
                    fecha_boletin = primer_registro.get('Fecha de Boletín', 'N/A')
                    
                    # Crear card usando componentes nativos de Streamlit
                    with st.container():
                        # Header del titular
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%); padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #667eea; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                            <h4 style="color: #e5e5e5; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
                                <span style="margin-right: 0.5rem;">👤</span> {titular}
                            </h4>
                            <span style="background: #667eea; color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 600;">
                                {len(registros)} registros
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Información detallada del registro
                        st.markdown("**📄 Ejemplo de registro:**")
                        
                        # Primera fila - Información principal
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("**📋 Boletín**")
                            st.info(f"Nº {boletin}")
                            st.markdown("**� Fecha**")
                            st.write(fecha_boletin)
                        
                        with col2:
                            st.markdown("**🏷️ Marca**")
                            st.success(marca)
                            st.markdown("**🔢 Clase**")
                            st.write(clase)
                        
                        with col3:
                            st.markdown("**📁 Expediente**")
                            st.write(expediente)
                            st.markdown("**� Solicitante**")
                            # Truncar solicitante si es muy largo
                            solicitante_display = solicitante[:40] + "..." if len(str(solicitante)) > 40 else solicitante
                            st.write(solicitante_display)
                        
                        st.markdown("---")  # Separador elegante
                
                count += 1
                if count >= 5:
                    break
            
            if len(datos_agrupados) > 5:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 1.5rem;
                    color: #888;
                    font-style: italic;
                    border-top: 2px solid #333;
                    margin-top: 1.5rem;
                    background: #1a1a1a;
                    border-radius: 8px;
                ">
                    <span style="font-size: 1.1em;">📊</span> 
                    <strong>y {len(datos_agrupados) - 5} titulares más</strong> están listos para importar
                </div>
                """, unsafe_allow_html=True)
    
    def _handle_import(self, datos_agrupados: dict) -> None:
        """Manejar la importación de datos"""
        if st.button("🚀 Importar Datos a la Base", type="primary", use_container_width=True):
            with st.spinner("⏳ Importando datos..."):
                conn = crear_conexion()
                if conn:
                    try:
                        # Insertar datos
                        resultado = insertar_datos(conn, datos_agrupados)
                        
                        # Verificar que resultado no sea None
                        if resultado is None:
                            st.error("❌ Error: La función de inserción no devolvió resultado")
                            return
                        
                        # Manejar resultado
                        if resultado.get('success', False):
                            st.success(f"✅ {resultado.get('mensaje', 'Datos importados exitosamente')}")
                            
                            # Limpiar estado
                            SessionManager.set('datos_insertados', True)
                            
                            # Mostrar estadísticas si están disponibles
                            if 'estadisticas' in resultado:
                                stats = resultado['estadisticas']
                                with st.container():
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("📊 Total Procesados", stats.get('total_procesados', 'N/A'))
                                    with col2:
                                        st.metric("✅ Insertados", stats.get('insertados', 'N/A'))
                                    with col3:
                                        st.metric("⚠️ Omitidos", stats.get('omitidos', 'N/A'))
                            
                            
                        else:
                            st.error(f"❌ {resultado.get('mensaje', 'Error al importar datos')}")
                            
                    except Exception as e:
                        st.error(f"❌ Error durante la importación: {e}")
                        # Log adicional para debug
                        st.error(f"Tipo de error: {type(e).__name__}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ No se pudo conectar a la base de datos")
    
    def show(self) -> None:
        """Mostrar la página de carga"""
        # Header de sección
        UIComponents.create_section_header(
            "📤 Carga de Boletines",
            "Importar y procesar archivos XLSX de boletines oficiales",
            "blue-70"
        )
        
        # Instrucciones
        instructions_html = UIComponents.create_info_card(
            "",
            """
            <div class="instructions-card">
                <h4>Pasos para cargar boletines:</h4>
                <ol>
                    <li><strong>Seleccionar archivo:</strong> Elija un archivo XLSX con los datos del boletín</li>
                    <li><strong>Vista previa:</strong> Revise los datos extraídos antes de importar</li>
                    <li><strong>Importar:</strong> Confirme la carga a la base de datos</li>
                </ol>
                <div class="instructions-tip">
                    <strong>Tip:</strong> Asegúrese de que el archivo tenga el formato correcto antes de cargar.
                </div>
            </div>
            """,
            "info"
        )
        st.markdown(instructions_html, unsafe_allow_html=True)
        
        # Área de carga de archivos
        upload_grid = grid(1, vertical_align="center")
        
        with upload_grid.container():
            st.markdown(UIComponents.create_file_upload_area(), unsafe_allow_html=True)
            
            archivo = st.file_uploader(
                "Seleccionar archivo XLSX",
                type=["xlsx"],
                help="Seleccione un archivo Excel (.xlsx) con los datos del boletín"
            )
        
        # Procesar archivo si se cargó uno
        if archivo and self._validate_file(archivo):
            # Mostrar información del archivo
            self._show_file_info(archivo)
            
            # Procesar archivo
            with st.spinner("🔄 Procesando archivo..."):
                success, datos_agrupados, error = self._process_file(archivo)
            
            if success and datos_agrupados:
                # Mostrar vista previa
                self._show_data_preview(datos_agrupados)
                
                # Botón de importación
                st.markdown("<br>", unsafe_allow_html=True)
                self._handle_import(datos_agrupados)
                
            else:
                st.error(f"❌ {error}")


def show_upload_page():
    """Función de compatibilidad para mostrar la página de carga"""
    upload_page = UploadPage()
    upload_page.show()
