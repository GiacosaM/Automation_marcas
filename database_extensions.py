"""
Extensiones para la base de datos de la aplicación
Este archivo contiene funciones adicionales para trabajar con la base de datos
"""
import logging
import sqlite3
from datetime import datetime, timedelta

# Importar funciones de compatibilidad
try:
    from database import usar_supabase, obtener_columnas_tabla
except ImportError:
    # Definir fallbacks si no se pueden importar
    def usar_supabase():
        return False
    def obtener_columnas_tabla(conn, tabla):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({tabla})")
        return [column[1] for column in cursor.fetchall()]

def obtener_emails_enviados(conn, filtro_fechas=None, filtro_titular=None, filtro_tipo_email=None, limite=None):
    """
    Obtiene lista de emails enviados con información de la tabla emails_enviados.
    
    Args:
        conn: Conexión a la base de datos
        filtro_fechas: Tupla (fecha_desde, fecha_hasta) para filtrar por rango de fechas
        filtro_titular: Texto para filtrar por titular
        filtro_tipo_email: Lista de tipos de email para filtrar
        limite: Número máximo de registros a retornar
    
    Returns:
        list: Lista de emails enviados
    """
    try:
        cursor = conn.cursor()
        
        # Verificar estructura de tabla de forma compatible
        columns = obtener_columnas_tabla(conn, 'emails_enviados')
        
        # Si la tabla no existe o no tiene las columnas esperadas, retornamos vacío
        if not columns:
            logging.error("La tabla emails_enviados no existe")
            return []
            
        # Verificar columna titular
        tiene_titular = 'titular' in columns
            
        # Construir consulta
        query = """
            SELECT id, destinatario, asunto, fecha_envio, status, 
                   mensaje_error, 
        """
        
        if tiene_titular:
            query += "titular, "
        else:
            query += "NULL as titular, "
            
        query += """
                   tipo_email
            FROM emails_enviados
            WHERE 1=1
        """
        params = []
        
        # Aplicar filtros
        if filtro_fechas:
            fecha_desde, fecha_hasta = filtro_fechas
            query += " AND fecha_envio BETWEEN ? AND ?"
            params.append(fecha_desde)
            params.append(fecha_hasta)
        
        if filtro_titular and tiene_titular:
            query += " AND (titular LIKE ? OR destinatario LIKE ?)"
            params.append(f"%{filtro_titular}%")
            params.append(f"%{filtro_titular}%")
        elif filtro_titular:
            query += " AND destinatario LIKE ?"
            params.append(f"%{filtro_titular}%")
            
        if filtro_tipo_email and len(filtro_tipo_email) > 0:
            placeholders = ', '.join(['?' for _ in filtro_tipo_email])
            query += f" AND tipo_email IN ({placeholders})"
            params.extend(filtro_tipo_email)
        
        # Orden y límite
        query += " ORDER BY fecha_envio DESC"
        
        if limite:
            query += " LIMIT ?"
            params.append(limite)
            
        logging.info(f"Query: {query}")
        logging.info(f"Params: {params}")
        
        cursor.execute(query, params)
        emails = cursor.fetchall()
        cursor.close()
        
        return emails
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener emails enviados: {e}")
        return []

def obtener_estadisticas_logs(conn):
    """
    Obtiene estadísticas de los logs de envíos.
    
    Args:
        conn: Conexión a la base de datos
        
    Returns:
        dict: Diccionario con estadísticas de envíos
    """
    try:
        cursor = conn.cursor()
        
        # Total de envíos
        cursor.execute("SELECT COUNT(*) FROM envios_log")
        total_envios = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Envíos exitosos
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'exitoso'")
        exitosos = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Envíos fallidos
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'fallido'")
        fallidos = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Sin email
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'sin_email'")
        sin_email = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Sin archivo
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'sin_archivo'")
        sin_archivo = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Envíos por importancia
        cursor.execute("""
            SELECT importancia, COUNT(*) 
            FROM envios_log 
            WHERE estado = 'exitoso' AND importancia IS NOT NULL
            GROUP BY importancia
        """)
        por_importancia = dict(cursor.fetchall() if cursor.fetchall() else [])
        
        # Envíos hoy
        cursor.execute("""
            SELECT COUNT(*) FROM envios_log 
            WHERE DATE(fecha_envio) = DATE('now', 'localtime')
        """)
        envios_hoy = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        cursor.close()
        
        return {
            'total_envios': total_envios,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'sin_email': sin_email,
            'sin_archivo': sin_archivo,
            'por_importancia': por_importancia,
            'envios_hoy': envios_hoy,
            'tasa_exito': (exitosos / total_envios * 100) if total_envios > 0 else 0
        }
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener estadísticas de logs: {e}")
        return {
            'total_envios': 0,
            'exitosos': 0,
            'fallidos': 0,
            'sin_email': 0,
            'sin_archivo': 0,
            'por_importancia': {},
            'envios_hoy': 0,
            'tasa_exito': 0
        }

def obtener_logs_envios(conn, limite=100, filtro_estado=None, filtro_titular=None):
    """
    Obtiene los logs de envíos con filtros opcionales.
    
    Args:
        conn: Conexión a la base de datos
        limite: Número máximo de registros a retornar
        filtro_estado: Filtrar por estado específico
        filtro_titular: Filtrar por titular específico
        
    Returns:
        tuple: (rows, columns) con los datos y nombres de columnas
    """
    try:
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='envios_log'")
        if not cursor.fetchone():
            # Si la tabla no existe, crear una versión simple
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS envios_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    titular TEXT,
                    email TEXT,
                    estado TEXT,
                    importancia TEXT,
                    numero_boletin TEXT,
                    mensaje_error TEXT
                )
            """)
            conn.commit()
            
            # Retornar columnas vacías para la primera ejecución
            return [], ['id', 'fecha_envio', 'titular', 'email', 'estado', 'importancia', 'numero_boletin', 'mensaje_error']
        
        # Construir la consulta con filtros
        query = "SELECT * FROM envios_log WHERE 1=1"
        params = []
        
        if filtro_estado:
            query += " AND estado = ?"
            params.append(filtro_estado)
            
        if filtro_titular:
            query += " AND titular LIKE ?"
            params.append(f"%{filtro_titular}%")
            
        query += " ORDER BY fecha_envio DESC LIMIT ?"
        params.append(limite)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Obtener nombres de columnas
        columns = [description[0] for description in cursor.description]
        
        cursor.close()
        return rows, columns
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener logs de envíos: {e}")
        return [], []

def limpiar_logs_antiguos(conn, dias=30):
    """
    Elimina logs de envíos más antiguos que el número especificado de días.
    
    Args:
        conn: Conexión a la base de datos
        dias: Número de días a mantener (por defecto 30)
        
    Returns:
        int: Número de registros eliminados
    """
    try:
        cursor = conn.cursor()
        
        # Verificar si existe la tabla de forma compatible
        from database import tabla_existe
        if not tabla_existe(conn, 'envios_log'):
            return 0
            
        if usar_supabase():
            # PostgreSQL syntax
            cursor.execute("""
                DELETE FROM envios_log 
                WHERE fecha_envio < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (dias,))
        else:
            # SQLite syntax
            cursor.execute("""
                DELETE FROM envios_log 
                WHERE fecha_envio < datetime('now', '-{} days', 'localtime')
            """.format(dias))
        
        eliminados = cursor.rowcount
        conn.commit()
        cursor.close()
        
        logging.info(f"Logs antiguos eliminados: {eliminados} registros")
        return eliminados
        
    except sqlite3.Error as e:
        logging.error(f"Error al limpiar logs antiguos: {e}")
        return 0
