    def _get_dashboard_data(self, conn):
        """Obtiene datos para el dashboard con compatibilidad PostgreSQL nativa."""
        from database import usar_supabase, crear_conexion
        
        try:
            # Crear una nueva conexión para evitar conflictos de cursor
            dashboard_conn = crear_conexion()
            if not dashboard_conn:
                st.error("No se pudo establecer conexión con la base de datos")
                return self._get_default_data()
                
            cursor = dashboard_conn.cursor()
            
            if usar_supabase():
                # PostgreSQL queries
                cursor.execute("SELECT COUNT(*) FROM boletines")
                total_boletines = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = TRUE")
                reportes_generados = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = TRUE")
                reportes_enviados = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
                total_clientes = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT fecha_alta::date as fecha, COUNT(*) as cantidad
                    FROM boletines 
                    WHERE fecha_alta >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY fecha_alta::date
                    ORDER BY fecha
                """)
                datos_timeline = cursor.fetchall()
                
                cursor.execute("""
                    SELECT titular, COUNT(*) as cantidad
                    FROM boletines
                    GROUP BY titular
                    ORDER BY cantidad DESC
                    LIMIT 10
                """)
                top_titulares = cursor.fetchall()
                
                # Para simplicidad, valores básicos para vencimientos
                proximos_vencer = 0
                reportes_vencidos = 0
                detalles_proximos_vencer = []
                detalles_vencidos = []
                
            else:
                # SQLite queries simplificadas
                cursor.execute("SELECT COUNT(*) FROM boletines")
                total_boletines = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
                reportes_generados = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
                reportes_enviados = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
                total_clientes = cursor.fetchone()[0]
                
                datos_timeline = []
                top_titulares = []
                proximos_vencer = 0
                reportes_vencidos = 0
                detalles_proximos_vencer = []
                detalles_vencidos = []
                
            # Cerrar conexiones
            cursor.close()
            dashboard_conn.close()
                
            return {
                'total_boletines': total_boletines,
                'reportes_generados': reportes_generados,
                'reportes_enviados': reportes_enviados,
                'total_clientes': total_clientes,
                'datos_timeline': datos_timeline,
                'top_titulares': top_titulares,
                'proximos_vencer': proximos_vencer,
                'reportes_vencidos': reportes_vencidos,
                'detalles_proximos_vencer': detalles_proximos_vencer,
                'detalles_vencidos': detalles_vencidos
            }
                
        except Exception as e:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
                if 'dashboard_conn' in locals() and dashboard_conn:
                    dashboard_conn.close()
            except:
                pass
            st.error(f"Error al obtener datos del dashboard: {e}")
            return self._get_default_data()
