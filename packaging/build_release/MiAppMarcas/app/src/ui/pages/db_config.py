"""
Página de configuración de la base de datos
"""

import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import db_utils

def show_db_config_page():
    """
    Mostrar la página de configuración de la base de datos
    """
    import sys
    import os
    # Asegurarse de que el directorio principal esté en el path
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
        
    # Importar el módulo db_utils
    import db_utils
    
    st.title("⚙️ Configuración de la Base de Datos")
    
    # Contenedor principal con estilo consistente
    with st.container():
        st.markdown("""
        <div class="section-header">
            <h3>Gestión de la Base de Datos</h3>
        </div>
        """, unsafe_allow_html=True)

        # Información de la ubicación actual de la base de datos
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Ubicación Actual")
                db_path = db_utils.get_db_path()
                st.info(f"📁 {db_path}")
                
                # Información del archivo
                if os.path.exists(db_path):
                    file_size = os.path.getsize(db_path) / (1024 * 1024)  # Convertir a MB
                    modified_time = datetime.fromtimestamp(os.path.getmtime(db_path))
                    
                    st.markdown(f"""
                    - **Tamaño:** {file_size:.2f} MB
                    - **Última modificación:** {modified_time.strftime('%d/%m/%Y %H:%M:%S')}
                    """)
                
                # Verificar integridad
                if st.button("✅ Verificar Integridad", key="verify_integrity"):
                    with st.spinner("Verificando integridad de la base de datos..."):
                        is_valid = db_utils.verify_db_integrity()
                        if is_valid:
                            st.success("La base de datos está íntegra y no presenta problemas")
                        else:
                            st.error("Se encontraron problemas en la base de datos. Se recomienda restaurar desde un backup")
            
            with col2:
                # Mostrar estadísticas de la BD en un gráfico simple
                if os.path.exists(db_path):
                    try:
                        conn = db_utils.connect_db()
                        cursor = conn.cursor()
                        
                        # Obtener conteos de tablas
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        
                        table_counts = []
                        for table in tables:
                            table_name = table[0]
                            if not table_name.startswith('sqlite_'):
                                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                count = cursor.fetchone()[0]
                                table_counts.append({"tabla": table_name, "registros": count})
                        
                        conn.close()
                        
                        if table_counts:
                            df = pd.DataFrame(table_counts)
                            
                            # Crear un gráfico simple
                            fig, ax = plt.subplots(figsize=(4, 3))
                            bars = ax.bar(df['tabla'], df['registros'], color='steelblue')
                            ax.set_ylabel('Registros')
                            ax.set_title('Estadísticas de la BD')
                            plt.xticks(rotation=45, ha="right")
                            plt.tight_layout()
                            
                            # Añadir valores sobre las barras
                            for bar in bars:
                                height = bar.get_height()
                                ax.annotate(f'{height}',
                                            xy=(bar.get_x() + bar.get_width() / 2, height),
                                            xytext=(0, 3),  # 3 puntos de desplazamiento vertical
                                            textcoords="offset points",
                                            ha='center', va='bottom')
                            
                            st.pyplot(fig)
                    except Exception as e:
                        st.warning(f"No se pudieron cargar estadísticas: {e}")

        # Separador visual
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Sección de backup
        st.subheader("Copias de Seguridad")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Crear Backup")
            backup_name = st.text_input("Nombre para el backup (opcional)", key="backup_name")
            
            if st.button("💾 Crear Copia de Seguridad", key="create_backup"):
                with st.spinner("Creando copia de seguridad..."):
                    backup_path = db_utils.create_backup(backup_name=backup_name if backup_name else None)
                    if backup_path:
                        st.success(f"Backup creado exitosamente en: {os.path.basename(backup_path)}")
                    else:
                        st.error("Error al crear el backup")
        
        with col2:
            st.markdown("#### Backups Disponibles")
            backups = db_utils.list_backups()
            
            if not backups:
                st.info("No hay copias de seguridad disponibles")
            else:
                # Mostrar backups como opciones seleccionables
                backup_options = []
                for backup in backups:
                    filename = os.path.basename(backup)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(backup))
                    file_size = os.path.getsize(backup) / (1024 * 1024)  # Convertir a MB
                    
                    backup_options.append({
                        "filename": filename,
                        "path": backup,
                        "modified": modified_time,
                        "size": file_size
                    })
                
                selected_backup = st.selectbox(
                    "Selecciona un backup",
                    options=range(len(backup_options)),
                    format_func=lambda x: f"{backup_options[x]['filename']} - {backup_options[x]['modified'].strftime('%d/%m/%Y %H:%M')} ({backup_options[x]['size']:.2f} MB)"
                )
                
                if st.button("🔄 Restaurar Backup", key="restore_backup"):
                    backup_to_restore = backup_options[selected_backup]["path"]
                    
                    # Confirmación
                    st.warning("⚠️ Esta acción reemplazará la base de datos actual. ¿Estás seguro?")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if st.button("✅ Confirmar Restauración"):
                            with st.spinner("Restaurando desde backup..."):
                                result = db_utils.restore_backup(backup_to_restore)
                                if result:
                                    st.success("Base de datos restaurada exitosamente")
                                    st.info("Recarga la aplicación para ver los cambios")
                                else:
                                    st.error("Error al restaurar la base de datos")

        # Separador visual
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Sección de configuración avanzada
        st.subheader("Configuración Avanzada")
        
        # Migrar DB existente
        with st.expander("Migrar Base de Datos Existente"):
            st.info("Esta opción permite migrar una base de datos existente a la ubicación estándar.")
            source_path = st.text_input("Ruta completa a la base de datos de origen:", placeholder="/ruta/completa/a/boletines.db")
            
            if st.button("🔄 Migrar Base de Datos", key="migrate_db"):
                if not source_path:
                    st.warning("Ingresa la ruta a la base de datos de origen")
                elif not os.path.exists(source_path):
                    st.error(f"El archivo no existe: {source_path}")
                else:
                    with st.spinner("Migrando base de datos..."):
                        result = db_utils.migrate_existing_db(source_path)
                        if result:
                            st.success(f"Base de datos migrada exitosamente a: {db_utils.get_db_path()}")
                        else:
                            st.error("Error al migrar la base de datos")