    def _get_dashboard_data(self, conn):
        """Obtiene datos para el dashboard."""
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total_boletines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1")
        reportes_generados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
        reportes_enviados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        # Datos por fecha (últimos 30 días)
        cursor.execute("""
            SELECT DATE(fecha_alta) as fecha, COUNT(*) as cantidad
            FROM boletines 
            WHERE fecha_alta >= date('now', '-30 days')
            GROUP BY DATE(fecha_alta)
            ORDER BY fecha
        """)
        datos_timeline = cursor.fetchall()
        
        # Top titulares
        cursor.execute("""
            SELECT titular, COUNT(*) as cantidad
            FROM boletines
            GROUP BY titular
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        top_titulares = cursor.fetchall()
        
        # Reportes próximos a vencer (últimos 7 días de plazo legal)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
        """)
        proximos_vencer = cursor.fetchone()[0]
        
        # Reportes ya vencidos (más de 30 días)
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') < date('now')
        """)
        reportes_vencidos = cursor.fetchone()[0]
        
        # Detalles de reportes próximos a vencer
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) - 
                        julianday(date('now')) AS INTEGER) as dias_restantes
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
            ORDER BY dias_restantes ASC
            LIMIT 10
        """)
        detalles_proximos_vencer = cursor.fetchall()
        
        # Detalles de reportes vencidos
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date('now')) - 
                        julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) AS INTEGER) as dias_vencido
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') < date('now')
            ORDER BY dias_vencido DESC
            LIMIT 10
        """)
        detalles_vencidos = cursor.fetchall()
        
        # Detalles de reportes en curso (entre 0 y 30 días desde la fecha del boletín)
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date('now')) - 
                        julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2))) AS INTEGER) as dias_transcurridos
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                               substr(fecha_boletin, 4, 2) || '-' || 
                                               substr(fecha_boletin, 1, 2))) <= 30
            AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                               substr(fecha_boletin, 4, 2) || '-' || 
                                               substr(fecha_boletin, 1, 2))) >= 0
            ORDER BY dias_transcurridos ASC
            LIMIT 30
        """)
        detalles_en_curso = cursor.fetchall()
        
        # Contar total de reportes en curso
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                               substr(fecha_boletin, 4, 2) || '-' || 
                                               substr(fecha_boletin, 1, 2))) <= 30
            AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                               substr(fecha_boletin, 4, 2) || '-' || 
                                               substr(fecha_boletin, 1, 2))) >= 0
        """)
        reportes_en_curso = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'total_boletines': total_boletines,
            'reportes_generados': reportes_generados,
            'reportes_enviados': reportes_enviados,
            'total_clientes': total_clientes,
            'datos_timeline': datos_timeline,
            'top_titulares': top_titulares,
            'proximos_vencer': proximos_vencer,
            'reportes_vencidos': reportes_vencidos,
            'reportes_en_curso': reportes_en_curso,
            'detalles_proximos_vencer': detalles_proximos_vencer,
            'detalles_vencidos': detalles_vencidos,
            'detalles_en_curso': detalles_en_curso
        }
