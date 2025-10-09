    def _show_historial_envios_tab(self, conn):
        """Mostrar tab de historial de envíos"""
        st.markdown("### 📊 Historial de Envíos")
        
        # Consultar historial de envíos
        try:
            # Primero intentar obtener datos de la función específica
            historial_df = None
            try:
                # Intentar usar la función dedicada si existe
                from database_extensions import obtener_emails_enviados
                emails_enviados = obtener_emails_enviados(conn, limite=200)
                if emails_enviados and len(emails_enviados) > 0:
                    # Convertir a DataFrame si la función devuelve resultados
                    columnas = ['ID', 'Destinatario', 'Asunto', 'Fecha Envío', 'Estado', 'Error', 'Titular', 'Tipo']
                    historial_df = pd.DataFrame(emails_enviados, columns=columnas)
                    st.success(f"✅ Cargados {len(emails_enviados)} registros de envíos desde la extensión de base de datos")
            except Exception as e:
                st.warning(f"Usando consulta de respaldo: {str(e)}")
            
            # Si la función específica falló, usar la consulta directa
            if historial_df is None:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT b.titular, b.numero_boletin, b.fecha_envio_reporte, 
                           b.importancia, c.email, 'informes' as tipo_envio
                    FROM boletines b
                    LEFT JOIN clientes c ON b.titular = c.titular
                    WHERE b.reporte_enviado = 1 
                    
                    UNION ALL
                    
                    -- Incluir notificaciones de clientes sin reportes
                    SELECT e.titular, 
                           'Sin reportes', e.fecha_envio, 
                           'Sin Reportes' as importancia, e.destinatario as email, 'notificacion' as tipo_envio
                    FROM emails_enviados e
                    WHERE e.tipo_email = 'notificacion' AND e.status = 'enviado'
                    
                    ORDER BY fecha_envio_reporte DESC
                    LIMIT 150
                """)
                historial_envios = cursor.fetchall()
                cursor.close()
                
                if historial_envios:
                    historial_df = pd.DataFrame(historial_envios, 
                        columns=['Titular', 'Boletín', 'Fecha Envío', 'Importancia', 'Email', 'Tipo'])
            
            if historial_df is not None and not historial_df.empty:
                # Formatear fecha permitiendo formatos mixtos
                if 'Fecha Envío' in historial_df.columns:
                    historial_df['Fecha Envío'] = pd.to_datetime(
                        historial_df['Fecha Envío'], errors='coerce'
                    ).dt.strftime('%d/%m/%Y %H:%M')
                
                # Crear filtros para el historial
                col_filter1, col_filter2 = st.columns([2, 2])
                with col_filter1:
                    # Si existe columna Titular, permitir filtrado
                    if 'Titular' in historial_df.columns:
                        titular_filter = st.text_input("🔍 Filtrar por Titular:", key="titular_filter")
                        if titular_filter:
                            historial_df = historial_df[historial_df['Titular'].str.contains(titular_filter, case=False, na=False)]
                
                with col_filter2:
                    # Si existe columna Importancia, permitir filtrado
                    if 'Importancia' in historial_df.columns and 'Importancia' in historial_df:
                        importancias = ['Todas'] + sorted(historial_df['Importancia'].dropna().unique().tolist())
                        imp_filter = st.selectbox("🏷️ Filtrar por Importancia:", importancias, key="imp_filter")
                        if imp_filter != 'Todas':
                            historial_df = historial_df[historial_df['Importancia'] == imp_filter]
                
                # Mostrar el grid con los datos de historial usando el GridService
                from src.services.grid_service import GridService
                grid_result = GridService.create_grid(
                    historial_df, 
                    key='grid_historial_envios',
                    height=400,
                    selection_mode='single',
                    fit_columns=True
                )

                # Estadísticas del historial
                st.markdown("#### 📈 Estadísticas del Historial")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_enviados = len(historial_df)
                    st.metric("📧 Total Enviados", total_enviados)
                with col2:
                    hoy = datetime.now().date()
                    if 'Fecha Envío' in historial_df.columns:
                        try:
                            enviados_hoy = len(historial_df[pd.to_datetime(
                                historial_df['Fecha Envío'], errors='coerce'
                            ).dt.date == hoy])
                            st.metric("📅 Enviados Hoy", enviados_hoy)
                        except:
                            st.metric("📅 Enviados Hoy", "N/A")
                    else:
                        st.metric("📅 Enviados Hoy", "N/A")
                with col3:
                    if 'Importancia' in historial_df.columns:
                        try:
                            importancia_alta = len(historial_df[historial_df['Importancia'] == 'Alta'])
                            st.metric("🔴 Importancia Alta", importancia_alta)
                        except:
                            st.metric("🔴 Importancia Alta", "N/A")
                    else:
                        st.metric("🔴 Importancia Alta", "N/A")
                with col4:
                    if 'Importancia' in historial_df.columns:
                        try:
                            sin_reportes = len(historial_df[historial_df['Importancia'] == 'Sin Reportes'])
                            st.metric("🔵 Sin Reportes", sin_reportes)
                        except:
                            st.metric("🔵 Sin Reportes", "N/A")
                    else:
                        st.metric("🔵 Sin Reportes", "N/A")
                
                # Añadir exportación CSV
                st.markdown("---")
                if st.button("📊 Exportar Historial", use_container_width=True):
                    # Preparar CSV para descarga
                    csv = historial_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Descargar CSV",
                        data=csv,
                        file_name=f"historial_envios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("📭 No hay envíos registrados")
        
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")
