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
