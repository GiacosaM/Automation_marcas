# database.py - Versión modificada con campo importancia

import sqlite3
import logging
from datetime import datetime, timedelta

# Configuración del logging optimizado
logging.basicConfig(
    level=logging.WARNING,  # Solo registrar WARNING y ERROR por defecto
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boletines.log'),
        logging.StreamHandler()
    ]
)

# Logger específico para eventos críticos del sistema
critical_logger = logging.getLogger('critical_events')
critical_logger.setLevel(logging.INFO)

# Verificar si ya tiene handlers para evitar duplicados
if not critical_logger.handlers:
    critical_handler = logging.FileHandler('boletines.log')
    critical_handler.setFormatter(logging.Formatter('%(asctime)s - CRITICAL - %(message)s'))
    critical_logger.addHandler(critical_handler)

critical_logger.propagate = False

def crear_conexion():
    """Crea y devuelve una conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect('boletines.db')
        # Solo log en caso de problemas - no en uso normal
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con la base de datos: {e}")
        raise Exception(f"Error al conectar con la base de datos: {e}")

def crear_tabla(conn):
    """Crea las tablas 'boletines' y 'clientes' con índices si no existen."""
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Crear tabla boletines
        # Solo log la primera creación de tablas, no verificaciones rutinarias
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boletines'")
        tabla_existe = cursor.fetchone()
        
        if not tabla_existe:
            critical_logger.info("Creando tabla 'boletines' por primera vez...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boletines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_boletin TEXT,
                fecha_boletin TEXT,
                numero_orden TEXT,
                solicitante TEXT,
                agente TEXT,
                numero_expediente TEXT,
                clase TEXT,
                marca_custodia TEXT,
                marca_publicada TEXT,
                clases_acta TEXT,
                reporte_enviado BOOLEAN DEFAULT FALSE,
                fecha_envio_reporte DATE,
                fecha_creacion_reporte DATE,
                reporte_generado BOOLEAN DEFAULT FALSE,
                nombre_reporte TEXT,    
                ruta_reporte TEXT,
                titular TEXT,
                fecha_alta DATE DEFAULT (datetime('now', 'localtime')),
                observaciones TEXT,
                importancia TEXT DEFAULT 'Pendiente' CHECK (importancia IN ('Pendiente', 'Baja', 'Media', 'Alta'))
            )
        """)
        conn.commit()
        
        if not tabla_existe:
            critical_logger.info("Tabla 'boletines' creada exitosamente.")

        # Verificar si la columna importancia existe, si no, agregarla
        cursor.execute("PRAGMA table_info(boletines)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'importancia' not in columns:
            critical_logger.info("Agregando columna 'importancia' a la tabla existente...")
            cursor.execute("""
                ALTER TABLE boletines 
                ADD COLUMN importancia TEXT DEFAULT 'Pendiente' 
                CHECK (importancia IN ('Pendiente', 'Baja', 'Media', 'Alta'))
            """)
            conn.commit()
            critical_logger.info("Columna 'importancia' agregada correctamente.")

        # Crear tabla clientes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
        tabla_clientes_existe = cursor.fetchone()
        
        if not tabla_clientes_existe:
            critical_logger.info("Creando tabla 'clientes' por primera vez...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titular TEXT UNIQUE,
                email TEXT,
                telefono TEXT,
                direccion TEXT,
                ciudad TEXT,
                provincia TEXT,
                fecha_alta DATE DEFAULT (datetime('now', 'localtime')),
                fecha_modificacion DATE,
                CUIT integer UNIQUE
            )
        """)
        
        # Agregar columna provincia si no existe (para bases de datos existentes)
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN provincia TEXT")
            conn.commit()
            critical_logger.info("Columna 'provincia' agregada a tabla clientes.")
        except sqlite3.OperationalError:
            # La columna ya existe, continuar
            pass
        conn.commit()
        
        if not tabla_clientes_existe:
            critical_logger.info("Tabla 'clientes' creada exitosamente.")

        # Crear índice en boletines (solo log si es necesario)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_boletines
            ON boletines (numero_boletin, numero_orden, titular)
        ''')
        conn.commit()
        
        # Crear tabla envios_log
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='envios_log'")
        tabla_envios_existe = cursor.fetchone()
        
        if not tabla_envios_existe:
            critical_logger.info("Creando tabla 'envios_log' por primera vez...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS envios_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titular TEXT,
                email TEXT,
                fecha_envio DATETIME DEFAULT (datetime('now', 'localtime')),
                estado TEXT,
                error TEXT,
                numero_boletin TEXT,
                importancia TEXT
            )
        """)
        conn.commit()
        
        if not tabla_envios_existe:
            critical_logger.info("Tabla 'envios_log' creada exitosamente.")
        
        # Verificar y agregar columnas faltantes si la tabla ya existía
        try:
            cursor.execute("PRAGMA table_info(envios_log)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'numero_boletin' not in columns:
                cursor.execute("ALTER TABLE envios_log ADD COLUMN numero_boletin TEXT")
                critical_logger.info("Columna 'numero_boletin' agregada a envios_log")
                
            if 'importancia' not in columns:
                cursor.execute("ALTER TABLE envios_log ADD COLUMN importancia TEXT")
                critical_logger.info("Columna 'importancia' agregada a envios_log")
                
            conn.commit()
        except Exception as e:
            logging.warning(f"Error actualizando estructura de envios_log: {e}")
        
        # Crear índice en envios_log
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_envios_log
            ON envios_log (titular, fecha_envio, estado)
        ''')
        conn.commit()

    except sqlite3.Error as e:
        logging.error(f"Error al crear tablas o índice: {e}")
        raise Exception(f"Error al crear tablas o índice: {e}")
    finally:
        if cursor:
            cursor.close()

def insertar_datos(conn, datos_agrupados):
    """Inserta los datos agrupados en la tabla 'boletines', verificando duplicados."""
    try:
        cursor = conn.cursor()
        insertados = 0
        omitidos = 0
        
        for titular, registros in datos_agrupados.items():
            for registro in registros:
                # Verificar si el registro ya existe
                cursor.execute('''
                    SELECT COUNT(*) FROM boletines
                    WHERE numero_boletin = ? AND numero_orden = ? AND titular = ?
                ''', (
                    registro["Número de Boletín"],
                    registro["Número de Orden"],
                    titular
                ))
                if cursor.fetchone()[0] == 0:  # Si no existe, insertar
                    cursor.execute('''
                        INSERT INTO boletines (numero_boletin, titular, fecha_boletin, numero_orden, solicitante, agente, numero_expediente, clase, marca_custodia, marca_publicada, clases_acta, importancia)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        registro["Número de Boletín"],
                        titular,
                        registro["Fecha de Boletín"],
                        registro["Número de Orden"],
                        registro["Solicitante"],
                        registro["Agente"],
                        registro["Expediente"],
                        registro["Clase"],
                        registro["Marca en Custodia"],
                        registro["Marca Publicada"],
                        registro["Clases/Acta"],
                        'Pendiente'  # Valor por defecto para importancia
                    ))
                    insertados += 1
                else:
                    omitidos += 1
                    
        conn.commit()
        
        # Solo log si hubo inserción significativa
        if insertados > 0:
            critical_logger.info(f"Inserción completada: {insertados} nuevos registros, {omitidos} omitidos")
        elif omitidos > 50:  # Log solo si hay muchos registros omitidos  
            critical_logger.info(f"Procesamiento completado: {omitidos} registros ya existían")
        
        # Retornar resultado con información de la operación
        return {
            'success': True,
            'mensaje': f"Importación completada: {insertados} registros nuevos, {omitidos} omitidos",
            'estadisticas': {
                'total_procesados': insertados + omitidos,
                'insertados': insertados,
                'omitidos': omitidos
            }
        }
            
    except sqlite3.Error as e:
        logging.error(f"Error al insertar datos: {e}")
        return {
            'success': False,
            'mensaje': f"Error al insertar datos: {e}"
        }
    except Exception as e:
        logging.error(f"Error inesperado al insertar datos: {e}")
        return {
            'success': False,
            'mensaje': f"Error inesperado: {e}"
        }
    finally:
        cursor.close()

def obtener_datos(conn):
    """Obtiene todos los registros de boletines con datos de clientes mediante LEFT JOIN."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id, b.titular, b.marca_custodia, b.marca_publicada, b.numero_boletin, b.fecha_boletin, 
                b.numero_orden, 
                b.solicitante, b.agente, b.numero_expediente, b.clase, 
                b.clases_acta, 
                b.reporte_enviado, b.reporte_generado, b.fecha_alta, b.importancia,
                c.email, c.telefono, c.direccion, c.ciudad
            FROM boletines b
            LEFT JOIN clientes c ON b.titular = c.titular
        """)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        # Eliminado logging rutinario - solo registrar errores
        return rows, columns
    except sqlite3.Error as e:
        logging.error(f"Error al consultar datos: {e}")
        raise Exception(f"Error al consultar datos: {e}")
    finally:
        cursor.close()

def actualizar_registro(conn, id, numero_boletin, fecha_boletin, numero_orden, solicitante, 
                       agente, numero_expediente, clase, marca_custodia, marca_publicada, 
                       clases_acta, reporte_enviado, titular, reporte_generado, importancia=None):
    """Actualiza un registro en la tabla boletines."""
    try:
        cursor = conn.cursor()
        if importancia is not None:
            cursor.execute("""
                UPDATE boletines
                SET numero_boletin = ?, fecha_boletin = ?, numero_orden = ?, 
                    solicitante = ?, agente = ?, numero_expediente = ?, 
                    clase = ?, marca_custodia = ?, marca_publicada = ?, 
                    clases_acta = ?, reporte_enviado = ?, titular = ?, reporte_generado = ?, importancia = ?
                WHERE id = ?
            """, (
                numero_boletin, fecha_boletin, numero_orden, solicitante,
                agente, numero_expediente, clase, marca_custodia,
                marca_publicada, clases_acta, reporte_enviado, titular, reporte_generado,
                importancia, id
            ))
        else:
            cursor.execute("""
                UPDATE boletines
                SET numero_boletin = ?, fecha_boletin = ?, numero_orden = ?, 
                    solicitante = ?, agente = ?, numero_expediente = ?, 
                    clase = ?, marca_custodia = ?, marca_publicada = ?, 
                    clases_acta = ?, reporte_enviado = ?, titular = ?, reporte_generado = ?
                WHERE id = ?
            """, (
                numero_boletin, fecha_boletin, numero_orden, solicitante,
                agente, numero_expediente, clase, marca_custodia,
                marca_publicada, clases_acta, reporte_enviado, titular, reporte_generado,
                id
            ))
        conn.commit()
        # Solo log actualizaciones importantes (cambios de estado o importancia)
        if importancia is not None or reporte_enviado or reporte_generado:
            critical_logger.info(f"Registro actualizado (crítico): ID {id} - Importancia: {importancia}, Enviado: {reporte_enviado}, Generado: {reporte_generado}")
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar: {e}")
        raise Exception(f"Error al actualizar: {e}")
    finally:
        cursor.close()

def actualizar_importancia_boletin(conn, boletin_id, importancia):
    """Actualiza específicamente la importancia de un boletín."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE boletines 
            SET importancia = ?
            WHERE id = ? AND reporte_enviado = 0
        """, (importancia, boletin_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            # Solo log cambios de importancia significativos
            if importancia in ['Alta', 'Media']:
                critical_logger.info(f"Importancia actualizada a {importancia} para boletín ID {boletin_id}")
            return True
        else:
            logging.warning(f"No se pudo actualizar importancia para boletín ID {boletin_id} (posiblemente ya enviado)")
            return False
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar importancia: {e}")
        raise Exception(f"Error al actualizar importancia: {e}")
    finally:
        cursor.close()

def obtener_boletines_para_clasificar(conn):
    """Obtiene boletines con reporte generado pero no enviado para clasificar."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id, b.titular, b.numero_boletin, b.fecha_boletin, 
                b.numero_orden, b.solicitante, b.marca_custodia, 
                b.marca_publicada, b.importancia,
                c.email
            FROM boletines b
            LEFT JOIN clientes c ON b.titular = c.titular
            WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0
            ORDER BY b.titular, b.numero_boletin, b.numero_orden
        """)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return rows, columns
    except sqlite3.Error as e:
        logging.error(f"Error al consultar boletines para clasificar: {e}")
        raise Exception(f"Error al consultar boletines para clasificar: {e}")
    finally:
        cursor.close()

def eliminar_registro(conn, id):
    """Elimina un registro de la tabla boletines."""
    try:
        cursor = conn.cursor()
        # Obtener información del registro antes de eliminarlo
        cursor.execute("SELECT titular, numero_boletin, numero_orden FROM boletines WHERE id = ?", (id,))
        registro_info = cursor.fetchone()
        
        cursor.execute("DELETE FROM boletines WHERE id = ?", (id,))
        conn.commit()
        
        # Log solo eliminaciones importantes
        if registro_info:
            critical_logger.info(f"Registro eliminado: ID {id} - {registro_info[0]} (Boletín: {registro_info[1]}, Orden: {registro_info[2]})")
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar: {e}")
        raise Exception(f"Error al eliminar: {e}")
    finally:
        cursor.close()

def insertar_cliente(conn, titular, email, telefono, direccion, ciudad, provincia, cuit):
    """Inserta un nuevo cliente en la tabla 'clientes', verificando duplicados."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM clientes WHERE titular = ?
        ''', (titular,))
        if cursor.fetchone()[0] == 0:  # Si no existe, insertar
            cursor.execute('''
                INSERT INTO clientes (titular, email, telefono, direccion, ciudad, provincia, fecha_alta, cuit)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'),?)
            ''', (titular, email, telefono, direccion, ciudad, provincia, cuit))
            conn.commit()
            logging.info(f"Cliente insertado: Titular {titular}")
        else:
            logging.info(f"Cliente omitido (ya existe): Titular {titular}")
            raise Exception(f"Cliente con titular '{titular}' ya existe.")
    except sqlite3.Error as e:
        logging.error(f"Error al insertar cliente: {e}")
        raise Exception(f"Error al insertar cliente: {e}")
    finally:
        cursor.close()

def obtener_clientes(conn):
    """Obtiene todos los registros de la tabla 'clientes'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titular, email, telefono, direccion, ciudad, provincia, cuit
            FROM clientes
        """)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        logging.info("Datos de clientes obtenidos correctamente.")
        return rows, columns
    except sqlite3.Error as e:
        logging.error(f"Error al consultar clientes: {e}")
        raise Exception(f"Error al consultar clientes: {e}")
    finally:
        cursor.close()

def actualizar_cliente(conn, id, titular, email, telefono, direccion, ciudad, provincia, cuit):
    """Actualiza un registro en la tabla 'clientes'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes
            SET titular = ?, email = ?, telefono = ?, direccion = ?, ciudad = ?, provincia = ?, fecha_modificacion = datetime('now', 'localtime'), cuit = ?
            WHERE id = ?
        """, (titular, email, telefono, direccion, ciudad, provincia, cuit, id))
        conn.commit()
        logging.info(f"Cliente actualizado: ID {id}")
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar cliente: {e}")
        raise Exception(f"Error al actualizar cliente: {e}")
    finally:
        cursor.close()

def actualizar_cliente(conn, cliente_id, titular, email, telefono, direccion, ciudad, provincia, cuit):
    """
    Actualiza un cliente existente en la base de datos.
    
    Args:
        conn: Conexión a la base de datos
        cliente_id: ID del cliente a actualizar
        titular: Nombre del titular
        email: Email del cliente
        telefono: Teléfono del cliente
        direccion: Dirección del cliente
        ciudad: Ciudad del cliente
        provincia: Provincia del cliente
        cuit: CUIT del cliente
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes 
            SET titular = ?, email = ?, telefono = ?, direccion = ?, ciudad = ?, provincia = ?, cuit = ?
            WHERE id = ?
        """, (titular, email, telefono, direccion, ciudad, provincia, cuit, cliente_id))
        
        conn.commit()
        cursor.close()
        
        return True
        
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        conn.rollback()
        return False

def eliminar_cliente(conn, id):
    """Elimina un registro de la tabla 'clientes'."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conn.commit()
        logging.info(f"Cliente eliminado: ID {id}")
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar cliente: {e}")
        raise Exception(f"Error al eliminar cliente: {e}")
    finally:
        cursor.close()

# ================================
# FUNCIONES PARA TABLA ENVIOS_LOG
# ================================

def insertar_log_envio(conn, titular, email, estado, error=None, numero_boletin=None, importancia=None):
    """
    Inserta un registro en la tabla envios_log.
    
    Args:
        conn: Conexión a la base de datos
        titular: Nombre del titular
        email: Email del destinatario
        estado: Estado del envío ('exitoso', 'fallido', 'sin_email', 'sin_archivo')
        error: Mensaje de error si el envío falló
        numero_boletin: Número de boletín relacionado
        importancia: Importancia del reporte
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO envios_log (titular, email, estado, error, numero_boletin, importancia)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (titular, email, estado, error, numero_boletin, importancia))
        
        conn.commit()
        
        # Log crítico para todos los envíos de email (exitosos y fallidos)
        if estado == 'exitoso':
            critical_logger.info(f"📧 EMAIL ENVIADO: {titular} ({importancia}) → {email}")
        elif estado == 'fallido':
            critical_logger.error(f"❌ EMAIL FALLIDO: {titular} → {email} | Error: {error}")
        elif estado in ['sin_email', 'sin_archivo']:
            critical_logger.warning(f"⚠️ EMAIL OMITIDO: {titular} - {estado.replace('_', ' ').title()}")
        
    except sqlite3.Error as e:
        logging.error(f"Error al insertar log de envío: {e}")
        raise Exception(f"Error al insertar log de envío: {e}")
    finally:
        if cursor:
            cursor.close()

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
        
        return rows, columns
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener logs de envíos: {e}")
        raise Exception(f"Error al obtener logs de envíos: {e}")
    finally:
        if cursor:
            cursor.close()

def obtener_estadisticas_logs(conn):
    """
    Obtiene estadísticas de los logs de envíos.
    
    Returns:
        dict: Diccionario con estadísticas de envíos
    """
    try:
        cursor = conn.cursor()
        
        # Total de envíos
        cursor.execute("SELECT COUNT(*) FROM envios_log")
        total_envios = cursor.fetchone()[0]
        
        # Envíos exitosos
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'exitoso'")
        exitosos = cursor.fetchone()[0]
        
        # Envíos fallidos
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'fallido'")
        fallidos = cursor.fetchone()[0]
        
        # Sin email
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'sin_email'")
        sin_email = cursor.fetchone()[0]
        
        # Sin archivo
        cursor.execute("SELECT COUNT(*) FROM envios_log WHERE estado = 'sin_archivo'")
        sin_archivo = cursor.fetchone()[0]
        
        # Envíos por importancia
        cursor.execute("""
            SELECT importancia, COUNT(*) 
            FROM envios_log 
            WHERE estado = 'exitoso' AND importancia IS NOT NULL
            GROUP BY importancia
        """)
        por_importancia = dict(cursor.fetchall())
        
        # Envíos hoy
        cursor.execute("""
            SELECT COUNT(*) FROM envios_log 
            WHERE DATE(fecha_envio) = DATE('now', 'localtime')
        """)
        envios_hoy = cursor.fetchone()[0]
        
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
        raise Exception(f"Error al obtener estadísticas de logs: {e}")
    finally:
        if cursor:
            cursor.close()

def limpiar_logs_antiguos(conn, dias=30):
    """
    Elimina logs de envíos más antiguos que el número especificado de días.
    
    Args:
        conn: Conexión a la base de datos
        dias: Número de días a mantener (por defecto 30)
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM envios_log 
            WHERE fecha_envio < datetime('now', '-{} days', 'localtime')
        """.format(dias))
        
        eliminados = cursor.rowcount
        conn.commit()
        
        logging.info(f"Logs antiguos eliminados: {eliminados} registros")
        return eliminados
        
    except sqlite3.Error as e:
        logging.error(f"Error al limpiar logs antiguos: {e}")
        raise Exception(f"Error al limpiar logs antiguos: {e}")
    finally:
        if cursor:
            cursor.close()

def obtener_emails_enviados(conn, filtro_fechas=None, filtro_titular=None, limite=None):
    """
    Obtiene lista de emails enviados exitosamente con información del reporte asociado.
    NUEVA LÓGICA: Agrupa por (titular + importancia + fecha) para mostrar emails separados correctamente.
    
    Args:
        conn: Conexión a la base de datos
        filtro_fechas: Tupla (fecha_desde, fecha_hasta) para filtrar por rango de fechas
        filtro_titular: Texto para filtrar por titular
        limite: Número máximo de registros a retornar
    
    Returns:
        List[Dict]: Lista de emails enviados con información del reporte
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Query simplificada usando directamente envios_log y agrupando por titular+importancia
        query = """
            SELECT 
                el.titular,
                el.email,
                COALESCE(el.fecha_envio, el.fecha_envio_default) as fecha_envio_real,
                el.importancia,
                COUNT(*) as total_boletines,
                GROUP_CONCAT(DISTINCT el.numero_boletin) as numeros_boletines,
                MIN(el.fecha_envio_default) as primera_fecha,
                MAX(el.fecha_envio_default) as ultima_fecha,
                DATE(COALESCE(el.fecha_envio, el.fecha_envio_default)) as fecha_grupo
            FROM envios_log el
            WHERE el.estado = 'exitoso'
        """
        
        params = []
        
        # Aplicar filtros
        if filtro_fechas and len(filtro_fechas) == 2:
            query += " AND DATE(COALESCE(el.fecha_envio, el.fecha_envio_default)) BETWEEN ? AND ?"
            params.extend(filtro_fechas)
        
        if filtro_titular:
            query += " AND el.titular LIKE ?"
            params.append(f"%{filtro_titular}%")
        
        # Agrupar por titular + importancia + fecha para mostrar emails separados
        query += " GROUP BY el.titular, el.importancia, DATE(COALESCE(el.fecha_envio, el.fecha_envio_default))"
        
        # Ordenar por fecha más reciente primero
        query += " ORDER BY fecha_envio_real DESC"
        
        # Aplicar límite si se especifica
        if limite:
            query += f" LIMIT {limite}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        emails_enviados = []
        for row in rows:
            email_info = {
                'titular': row[0],
                'email': row[1],
                'fecha_envio': row[2],
                'importancia': row[3],
                'total_boletines': row[4] or 0,
                'numeros_boletines': row[5].split(',') if row[5] else [],
                'fecha_primer_envio': row[6],
                'fecha_ultimo_envio': row[7],
                'fecha_grupo': row[8]
            }
            emails_enviados.append(email_info)
        
        logging.info(f"Obtenidos {len(emails_enviados)} emails enviados")
        return emails_enviados
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener emails enviados: {e}")
        raise Exception(f"Error al obtener emails enviados: {e}")
    finally:
        if cursor:
            cursor.close()

def obtener_ruta_reporte_pdf(titular, fecha_envio=None):
    """
    Obtiene la ruta del archivo PDF del reporte para un titular específico.
    
    Args:
        titular: Nombre del titular
        fecha_envio: Fecha de envío para ubicar el archivo correcto
    
    Returns:
        str: Ruta del archivo PDF o None si no se encuentra
    """
    import os
    import glob
    from datetime import datetime
    
    try:
        # Directorio donde se almacenan los informes
        informes_dir = "informes"
        
        if not os.path.exists(informes_dir):
            return None
        
        # Buscar archivos PDF que contengan el nombre del titular
        # Formato típico: "Month-Year - Informe TITULAR - ID.pdf"
        patron_busqueda = f"*{titular.replace(' ', '*')}*.pdf"
        archivos_encontrados = glob.glob(os.path.join(informes_dir, patron_busqueda))
        
        if not archivos_encontrados:
            # Búsqueda más amplia si no se encuentra exacto
            patron_busqueda = f"*Informe*{titular.split()[0]}*.pdf"
            archivos_encontrados = glob.glob(os.path.join(informes_dir, patron_busqueda))
        
        if archivos_encontrados:
            # Si hay fecha de envío, buscar el archivo más reciente a esa fecha
            if fecha_envio:
                try:
                    fecha_ref = datetime.strptime(fecha_envio.split()[0], '%Y-%m-%d')
                    # Filtrar archivos por fecha de modificación
                    archivos_validos = []
                    for archivo in archivos_encontrados:
                        fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo))
                        if fecha_mod <= fecha_ref + timedelta(days=1):  # Permitir 1 día de margen
                            archivos_validos.append((archivo, fecha_mod))
                    
                    if archivos_validos:
                        # Retornar el más reciente
                        archivo_mas_reciente = max(archivos_validos, key=lambda x: x[1])
                        return archivo_mas_reciente[0]
                except:
                    pass
            
            # Retornar el archivo más reciente si no hay filtro de fecha específico
            archivo_mas_reciente = max(archivos_encontrados, key=os.path.getmtime)
            return archivo_mas_reciente
        
        return None
        
    except Exception as e:
        logging.error(f"Error al buscar archivo PDF para {titular}: {e}")
        return None

def limpiar_logs_antiguos(conn, dias=30):
    """
    Elimina logs de envío más antiguos que el número de días especificado.
    Mantiene registros críticos y errores importantes.
    """
    try:
        cursor = conn.cursor()
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        # Contar registros antes de eliminar
        cursor.execute("""
            SELECT COUNT(*) FROM envios_log 
            WHERE fecha_envio < ? AND estado NOT IN ('fallido')
        """, (fecha_limite,))
        registros_a_eliminar = cursor.fetchone()[0]
        
        if registros_a_eliminar > 0:
            # Eliminar solo logs exitosos antiguos, mantener errores
            cursor.execute("""
                DELETE FROM envios_log 
                WHERE fecha_envio < ? AND estado = 'exitoso'
            """, (fecha_limite,))
            conn.commit()
            
            critical_logger.info(f"🧹 Limpieza de logs: {registros_a_eliminar} registros antiguos eliminados (conservando errores)")
            return registros_a_eliminar
        else:
            return 0
            
    except sqlite3.Error as e:
        logging.error(f"Error al limpiar logs antiguos: {e}")
        raise Exception(f"Error al limpiar logs antiguos: {e}")
    finally:
        if cursor:
            cursor.close()

def optimizar_archivo_log():
    """
    Optimiza el archivo de log rotando logs muy grandes.
    """
    try:
        import os
        log_file = 'boletines.log'
        
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            # Si el archivo es mayor a 50MB, crear respaldo y limpiar
            if size > 50 * 1024 * 1024:  # 50MB
                import shutil
                from datetime import datetime
                
                # Crear respaldo
                backup_name = f"boletines_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                shutil.copy2(log_file, backup_name)
                
                # Mantener solo las últimas 1000 líneas del log actual
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    with open(log_file, 'w') as f:
                        f.write(f"# Log optimizado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# Respaldo creado: {backup_name}\n")
                        f.writelines(lines[-1000:])  # Últimas 1000 líneas
                    
                    return f"Log optimizado. Respaldo: {backup_name}"
        
        return "Log no requiere optimización"
        
    except Exception as e:
        logging.error(f"Error al optimizar archivo de log: {e}")
        return f"Error: {e}"

def limpieza_automatica_logs(conn):
    """
    Ejecuta limpieza automática de logs basada en configuración.
    Se ejecuta automáticamente al iniciar la aplicación.
    """
    try:
        import os
        from datetime import datetime, timedelta
        
        resultado = {
            'logs_eliminados': 0,
            'archivo_optimizado': False,
            'mensaje': ''
        }
        
        # 1. Verificar si es necesario limpiar logs antiguos (cada 7 días)
        config_file = 'log_config.txt'
        ultima_limpieza = None
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    fecha_str = f.read().strip()
                    ultima_limpieza = datetime.fromisoformat(fecha_str)
            except:
                pass
        
        ahora = datetime.now()
        debe_limpiar = (
            ultima_limpieza is None or 
            (ahora - ultima_limpieza).days >= 7
        )
        
        if debe_limpiar:
            # Ejecutar limpieza de logs antiguos (30+ días)
            eliminados = limpiar_logs_antiguos(conn, 30)
            resultado['logs_eliminados'] = eliminados
            
            # Actualizar fecha de última limpieza
            with open(config_file, 'w') as f:
                f.write(ahora.isoformat())
            
            if eliminados > 0:
                critical_logger.info(f"🤖 Limpieza automática: {eliminados} logs antiguos eliminados")
        
        # 2. Verificar si el archivo de log necesita optimización
        log_file = 'boletines.log'
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            # Auto-optimizar si supera 100MB (más agresivo que manual)
            if size > 100 * 1024 * 1024:  # 100MB
                resultado_opt = optimizar_archivo_log()
                if "optimizado" in resultado_opt.lower():
                    resultado['archivo_optimizado'] = True
                    critical_logger.info("🤖 Optimización automática del archivo de log ejecutada")
        
        # 3. Limpiar archivos de respaldo muy antiguos (90+ días)
        directorio = '.'
        for archivo in os.listdir(directorio):
            if archivo.startswith('boletines_backup_') and archivo.endswith('.log'):
                try:
                    fecha_archivo = os.path.getmtime(archivo)
                    fecha_dt = datetime.fromtimestamp(fecha_archivo)
                    
                    if (ahora - fecha_dt).days > 90:
                        os.remove(archivo)
                        critical_logger.info(f"🤖 Respaldo antiguo eliminado: {archivo}")
                except:
                    pass
        
        # Generar mensaje de resultado
        if resultado['logs_eliminados'] > 0 or resultado['archivo_optimizado']:
            resultado['mensaje'] = f"Limpieza automática completada: {resultado['logs_eliminados']} logs eliminados"
        else:
            resultado['mensaje'] = "Sistema de logs en buen estado"
            
        return resultado
        
    except Exception as e:
        logging.error(f"Error en limpieza automática: {e}")
        return {'logs_eliminados': 0, 'archivo_optimizado': False, 'mensaje': f'Error: {e}'}

def configurar_limpieza_logs():
    """
    Retorna la configuración actual de limpieza de logs.
    """
    import os
    
    config = {
        'dias_conservar_exitosos': 30,
        'dias_conservar_errores': 365,  # Errores se conservan 1 año
        'frecuencia_limpieza_dias': 7,
        'tamaño_maximo_mb': 50,
        'tamaño_auto_optimizacion_mb': 100,
        'respaldos_conservar_dias': 90
    }
    
    # Verificar tamaño actual del log
    log_file = 'boletines.log'
    if os.path.exists(log_file):
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        config['tamaño_actual_mb'] = round(size_mb, 2)
    else:
        config['tamaño_actual_mb'] = 0
    
    # Verificar última limpieza
    config_file = 'log_config.txt'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                fecha_str = f.read().strip()
                config['ultima_limpieza'] = fecha_str
        except:
            config['ultima_limpieza'] = 'Nunca'
    else:
        config['ultima_limpieza'] = 'Nunca'
    
    return config