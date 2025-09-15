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
        # Habilitar soporte de foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
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
    """
    Inserta un nuevo cliente en la tabla 'clientes', verificando duplicados.
    Además, verifica si el CUIT ya existe en la tabla Marcas y compara el titular.
    Si los titulares no coinciden, usa el titular de la tabla Marcas.
    Luego vincula automáticamente todas las marcas con el mismo CUIT.
    
    Args:
        conn: Conexión a la base de datos
        titular: Nombre del titular
        email: Email del cliente
        telefono: Teléfono del cliente
        direccion: Dirección del cliente
        ciudad: Ciudad del cliente
        provincia: Provincia del cliente
        cuit: CUIT del cliente
        
    Returns:
        int: ID del cliente insertado o None si ocurre un error
    """
    try:
        cursor = conn.cursor()
        
        # Verificar si ya existe un cliente con el mismo titular
        cursor.execute('SELECT COUNT(*) FROM clientes WHERE titular = ?', (titular,))
        if cursor.fetchone()[0] > 0:
            logging.info(f"Cliente omitido (ya existe): Titular {titular}")
            raise Exception(f"Cliente con titular '{titular}' ya existe.")
        
        # Nombre del titular para insertar (puede ser actualizado si se encuentra en la tabla Marcas)
        nombre_titular_final = titular
        
        # Si hay un CUIT, verificar si existe en la tabla Marcas y comparar el nombre del titular
        if cuit:
            cursor.execute('SELECT titular FROM Marcas WHERE cuit = ? LIMIT 1', (cuit,))
            resultado_marca = cursor.fetchone()
            
            if resultado_marca and resultado_marca[0]:
                titular_en_marcas = resultado_marca[0]
                
                # Si los nombres no coinciden, usar el de la tabla Marcas
                if titular_en_marcas.strip() != titular.strip():
                    logging.info(f"Actualizando nombre del cliente de '{titular}' a '{titular_en_marcas}' según tabla Marcas")
                    nombre_titular_final = titular_en_marcas
        
        # Insertar el nuevo cliente con el nombre correcto
        cursor.execute('''
            INSERT INTO clientes (titular, email, telefono, direccion, ciudad, provincia, fecha_alta, cuit)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        ''', (nombre_titular_final, email, telefono, direccion, ciudad, provincia, cuit))
        
        conn.commit()
        
        # Obtener el ID del cliente recién insertado
        cursor.execute("SELECT last_insert_rowid()")
        cliente_id = cursor.fetchone()[0]
        
        logging.info(f"Cliente insertado: ID {cliente_id}, Titular {nombre_titular_final}")
        
        # Vincular marcas existentes con este CUIT
        if cuit:
            _vincular_marcas_con_cliente(conn, cliente_id, cuit)
            
        return cliente_id
        
    except sqlite3.Error as e:
        logging.error(f"Error al insertar cliente: {e}")
        if conn:
            conn.rollback()
        raise Exception(f"Error al insertar cliente: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()

def cliente_tiene_marcas(conn, cliente_id=None, cuit=None):
    """
    Verifica si un cliente tiene marcas asociadas, ya sea por su ID o su CUIT.
    
    Args:
        conn: Conexión a la base de datos
        cliente_id: ID del cliente (opcional)
        cuit: CUIT del cliente (opcional)
        
    Returns:
        bool: True si el cliente tiene marcas asociadas, False en caso contrario
    """
    try:
        if not cliente_id and not cuit:
            return False
            
        cursor = conn.cursor()
        has_marcas = False
        
        # Primero verificamos por cliente_id (relación directa)
        if cliente_id:
            cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?", (cliente_id,))
            count_by_id = cursor.fetchone()[0]
            has_marcas = count_by_id > 0
        
        # Si no hay marcas por ID y tenemos CUIT, verificamos por CUIT
        if not has_marcas and cuit:
            # Manejar casos donde CUIT puede ser string o int
            cuit_str = str(cuit) if not isinstance(cuit, str) else cuit
            cuit_int = int(cuit_str) if cuit_str.isdigit() else None
            
            if cuit_int is not None:
                cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cuit = ? OR cuit = ?", (cuit_str, cuit_int))
            else:
                cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cuit = ?", (cuit_str,))
            
            count_by_cuit = cursor.fetchone()[0]
            has_marcas = count_by_cuit > 0
        
        return has_marcas
        
    except sqlite3.Error as e:
        logging.error(f"Error al verificar marcas del cliente: {e}")
        return False
    finally:
        if cursor:
            cursor.close()


def obtener_clientes(conn, force_refresh=True):
    """
    Obtiene todos los registros de la tabla 'clientes' incluyendo un indicador 
    de si tienen marcas asociadas.
    
    Args:
        conn: Conexión a la base de datos
        force_refresh: Si es True, fuerza un PRAGMA query_only=0 para asegurar datos actualizados
        
    Returns:
        tuple: (list de filas, list de nombres de columnas)
    """
    try:
        cursor = conn.cursor()
        
        # Asegurar que no se use una versión en caché de la base de datos
        if force_refresh:
            cursor.execute("PRAGMA query_only=0")
            
        cursor.execute("""
            SELECT id, titular, email, telefono, direccion, ciudad, provincia, cuit
            FROM clientes
            ORDER BY titular ASC
        """)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] + ["tiene_marcas"]
        
        # Añadir indicador de si el cliente tiene marcas
        result = []
        for row in rows:
            cliente_id = row[0]
            cuit = row[7]  # Índice 7 corresponde a cuit en la consulta
            
            # Verificamos primero por cliente_id (relación directa) - esto es más preciso
            cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?", (cliente_id,))
            count_by_id = cursor.fetchone()[0]
            tiene_marcas_id = count_by_id > 0
            
            # También verificamos por coincidencia de CUIT (para detección de potenciales vinculaciones)
            # y lo almacenamos como dato separado para uso en la interfaz
            cuit_str = str(cuit) if cuit is not None else ""
            cuit_int = int(cuit_str) if cuit_str.isdigit() else None
            
            count_by_cuit = 0
            if cuit_int is not None:
                cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cuit = ? OR cuit = ?", 
                               (cuit_str, cuit_int))
                count_by_cuit = cursor.fetchone()[0]
            elif cuit_str:
                cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cuit = ?", (cuit_str,))
                count_by_cuit = cursor.fetchone()[0]
            
            # Crear una nueva fila con todos los datos originales más los indicadores
            new_row = list(row) + [1 if tiene_marcas_id else 0]  # 1=Tiene marcas asignadas, 0=No tiene
            result.append(new_row)
        
        logging.info("Datos de clientes obtenidos correctamente con indicador de marcas.")
        return result, columns
    except sqlite3.Error as e:
        logging.error(f"Error al consultar clientes: {e}")
        raise Exception(f"Error al consultar clientes: {e}")
    finally:
        if cursor:
            cursor.close()

def actualizar_cliente(conn, cliente_id, titular, email, telefono, direccion, ciudad, provincia, cuit):
    """
    Actualiza un cliente existente en la base de datos y vincula marcas con el mismo CUIT.
    Si el CUIT coincide con marcas existentes, verifica si el titular coincide y usa el de la tabla Marcas.
    
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
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        cursor = conn.cursor()
        
        # Obtener el CUIT antiguo para comparar si cambió
        cursor.execute("SELECT cuit FROM clientes WHERE id = ?", (cliente_id,))
        resultado = cursor.fetchone()
        if not resultado:
            logging.warning(f"Cliente con ID {cliente_id} no existe")
            return False
            
        cuit_antiguo = resultado[0]
        
        # Nombre del titular para actualizar (puede ser actualizado si se encuentra en la tabla Marcas)
        nombre_titular_final = titular
        
        # Si hay un CUIT y ha cambiado, verificar si existe en la tabla Marcas y comparar el nombre del titular
        if cuit and cuit != cuit_antiguo:
            cursor.execute('SELECT titular FROM Marcas WHERE cuit = ? LIMIT 1', (cuit,))
            resultado_marca = cursor.fetchone()
            
            if resultado_marca and resultado_marca[0]:
                titular_en_marcas = resultado_marca[0]
                
                # Si los nombres no coinciden, usar el de la tabla Marcas
                if titular_en_marcas.strip() != titular.strip():
                    logging.info(f"Actualizando nombre del cliente de '{titular}' a '{titular_en_marcas}' según tabla Marcas")
                    nombre_titular_final = titular_en_marcas
        
        # Actualizar el cliente con el nombre correcto
        cursor.execute("""
            UPDATE clientes 
            SET titular = ?, email = ?, telefono = ?, direccion = ?, ciudad = ?, provincia = ?, 
                cuit = ?, fecha_modificacion = datetime('now', 'localtime')
            WHERE id = ?
        """, (nombre_titular_final, email, telefono, direccion, ciudad, provincia, cuit, cliente_id))
        
        conn.commit()
        logging.info(f"Cliente actualizado: ID {cliente_id}, Titular: {nombre_titular_final}")
        
        # Si el CUIT cambió o existe, debemos vincular marcas que coincidan con ese CUIT
        if cuit:
            # Limpiamos y estandarizamos el CUIT para evitar problemas de formato
            cuit_clean = str(cuit).replace('-', '').replace(' ', '').strip()
            cuit_antiguo_clean = str(cuit_antiguo).replace('-', '').replace(' ', '').strip() if cuit_antiguo else ""
            
            cuit_cambio = (cuit_clean != cuit_antiguo_clean)
            logging.info(f"{'Cambio de CUIT' if cuit_cambio else 'Verificando vinculaciones'} para cliente {titular} (ID: {cliente_id})")
            logging.info(f"CUIT actual: {cuit} (limpio: {cuit_clean})")
            
            # Realizar la vinculación manual
            cursor.execute("""
                SELECT id, marca, cuit FROM Marcas WHERE cliente_id IS NULL
            """)
            
            marcas_sin_asignar = cursor.fetchall()
            marcas_vinculadas = 0
            
            # Mostrar marcas disponibles antes de vincular
            logging.info(f"Buscando marcas para vincular con CUIT {cuit_clean}")
            
            for marca_id, marca_nombre, marca_cuit in marcas_sin_asignar:
                if marca_cuit:
                    # Limpiar el CUIT de la marca para comparación estricta
                    marca_cuit_clean = str(marca_cuit).replace('-', '').replace(' ', '').strip()
                    logging.info(f"Comparando marca ID {marca_id} con CUIT {marca_cuit} (limpio: {marca_cuit_clean})")
                    
                    # Compara CUITs limpios como strings
                    if marca_cuit_clean == cuit_clean:
                        # Vincula la marca al cliente
                        cursor.execute("""
                            UPDATE Marcas SET cliente_id = ? WHERE id = ?
                        """, (cliente_id, marca_id))
                        
                        logging.info(f"✅ Vinculada marca ID {marca_id} '{marca_nombre}' con CUIT {marca_cuit} al cliente {cliente_id}")
                        marcas_vinculadas += 1
            
            conn.commit()
            logging.info(f"Total: Se vincularon {marcas_vinculadas} marcas al cliente '{titular}' (ID: {cliente_id}) con CUIT {cuit}")
            
            # Verificar que las vinculaciones funcionaron
            cursor.execute("""
                SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?
            """, (cliente_id,))
            
            total_vinculadas = cursor.fetchone()[0]
            logging.info(f"Total de marcas vinculadas al cliente {cliente_id}: {total_vinculadas}")
            
            # Forzar el refresco de datos en UI
            if marcas_vinculadas > 0:
                cursor.execute("""
                    UPDATE clientes SET fecha_modificacion = datetime('now', 'localtime') WHERE id = ?
                """, (cliente_id,))
                
                # Obtener detalles de las marcas vinculadas para el log
                if cuit_int is not None:
                    cursor.execute("""
                        SELECT id, marca, cuit
                        FROM Marcas
                        WHERE cliente_id = ? AND (cuit = ? OR cuit = ?)
                        LIMIT 5  -- Limitamos a 5 para no sobrecargar el log
                    """, (cliente_id, cuit_str, cuit_int))
                else:
                    cursor.execute("""
                        SELECT id, marca, cuit
                        FROM Marcas
                        WHERE cliente_id = ? AND cuit = ?
                        LIMIT 5  -- Limitamos a 5 para no sobrecargar el log
                    """, (cliente_id, cuit_str))
                
                for marca in cursor.fetchall():
                    logging.info(f"  - Marca '{marca[1]}' (ID: {marca[0]}, CUIT: {marca[2]}) vinculada al cliente {titular}")
            else:
                logging.info(f"No se encontraron marcas sin vincular con CUIT {cuit} (en ningún formato)")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar cliente: {e}")
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def eliminar_cliente(conn, id):
    """
    Elimina un registro de la tabla 'clientes' y desvincula sus marcas asociadas.
    
    Args:
        conn: Conexión a la base de datos
        id: ID del cliente a eliminar
        
    Returns:
        dict: Resultado de la operación con información sobre marcas desvinculadas
    """
    try:
        cursor = conn.cursor()
        
        # 1. Obtener información del cliente antes de eliminarlo (para log)
        cursor.execute("SELECT titular, cuit FROM clientes WHERE id = ?", (id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            logging.warning(f"No se encontró cliente con ID {id} para eliminar")
            return {"success": False, "error": f"No se encontró cliente con ID {id}"}
            
        titular, cuit = cliente
        
        # 2. Identificar las marcas vinculadas a este cliente
        cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?", (id,))
        marcas_count = cursor.fetchone()[0]
        
        # 3. Desvincular las marcas asociadas (NO eliminar las marcas)
        if marcas_count > 0:
            cursor.execute("""
                UPDATE Marcas 
                SET cliente_id = NULL 
                WHERE cliente_id = ?
            """, (id,))
            
            logging.info(f"Se desvincularon {marcas_count} marcas del cliente '{titular}' (ID: {id})")
        
        # 4. Eliminar el cliente
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conn.commit()
        
        logging.info(f"Cliente eliminado: '{titular}' (ID: {id}) con {marcas_count} marcas desvinculadas")
        
        return {
            "success": True, 
            "marcas_desvinculadas": marcas_count,
            "cliente": titular
        }
        
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar cliente: {e}")
        conn.rollback()
        raise Exception(f"Error al eliminar cliente: {e}")
    finally:
        if 'cursor' in locals():
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

def obtener_usuarios(conn):
    """Recuperar todos los usuarios de la tabla 'users'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, name, email, role, created_at, last_login, is_active, failed_login_attempts, locked_until
            FROM users
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return rows, columns
    except sqlite3.Error as e:
        logging.error(f"Error al obtener usuarios: {e}")
        raise Exception(f"Error al obtener usuarios: {e}")
    finally:
        cursor.close()

def insertar_usuario(conn, username, email, role, is_active):
    """Insertar un nuevo usuario en la tabla 'users'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, name, email, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (username, username, email, 'default_hash', role, is_active))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error al insertar usuario: {e}")
        raise Exception(f"Error al insertar usuario: {e}")
    finally:
        cursor.close()

def actualizar_usuario(conn, user_id, username, email, role, is_active):
    """Actualizar los datos de un usuario en la tabla 'users'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET username = ?, email = ?, role = ?, is_active = ?, last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (username, email, role, is_active, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar usuario: {e}")
        raise Exception(f"Error al actualizar usuario: {e}")
    finally:
        cursor.close()

def eliminar_usuario(conn, user_id):
    """Eliminar un usuario de la tabla 'users'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM users
            WHERE id = ?
        """, (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar usuario: {e}")
        raise Exception(f"Error al eliminar usuario: {e}")
    finally:
        cursor.close()
        
# ================================
# FUNCIONES PARA TABLA MARCAS
# ================================

def _vincular_marcas_con_cliente(conn, cliente_id, cuit):
    """
    Vincula todas las marcas con un determinado CUIT con el cliente_id.
    Esta es una función auxiliar privada usada por insertar_cliente y actualizar_cliente.
    
    Args:
        conn: Conexión a la base de datos
        cliente_id: ID del cliente a vincular
        cuit: CUIT para buscar marcas relacionadas
        
    Returns:
        int: Número de marcas vinculadas
    """
    try:
        if not cuit or not cliente_id:
            return 0
            
        cursor = conn.cursor()
        
        # Limpiar y estandarizar el CUIT (eliminar guiones y espacios)
        cuit_clean = str(cuit).replace('-', '').replace(' ', '').strip()
        
        # Asegurar compatibilidad entre string e int para CUIT
        cuit_str = cuit_clean
        cuit_int = int(cuit_clean) if cuit_clean.isdigit() else None
        
        # Registrar información de depuración
        logging.info(f"Vinculando marcas para el CUIT: {cuit_clean} (original: {cuit})")
        
        # Verificar que el cliente existe
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE id = ?", (cliente_id,))
        if cursor.fetchone()[0] == 0:
            logging.warning(f"No se puede vincular marcas: Cliente con ID {cliente_id} no existe")
            return 0
        
        # Obtener el nombre del titular para el log
        cursor.execute("SELECT titular FROM clientes WHERE id = ?", (cliente_id,))
        titular_result = cursor.fetchone()
        titular = titular_result[0] if titular_result else "Desconocido"
        
        # Ejecutar vinculación manual por CUIT con conversión de tipos
        # Esta vinculación es mucho más directa y compatible con las diferencias entre INTEGER y TEXT
        cursor.execute("""
            SELECT id, marca, cuit FROM Marcas WHERE cliente_id IS NULL
        """)
        
        marcas_sin_asignar = cursor.fetchall()
        marcas_vinculadas = 0
        
        for marca_id, marca_nombre, marca_cuit in marcas_sin_asignar:
            if marca_cuit:
                # Limpiar el CUIT de la marca para comparación estricta
                marca_cuit_clean = str(marca_cuit).replace('-', '').replace(' ', '').strip()
                
                # Compara CUITs limpios como strings
                if marca_cuit_clean == cuit_clean:
                    # Vincula la marca al cliente
                    cursor.execute("""
                        UPDATE Marcas SET cliente_id = ? WHERE id = ?
                    """, (cliente_id, marca_id))
                    
                    logging.info(f"✅ Vinculada marca ID {marca_id} '{marca_nombre}' con CUIT {marca_cuit} al cliente {cliente_id}")
                    marcas_vinculadas += 1
        
        conn.commit()
        logging.info(f"Total: Se vincularon {marcas_vinculadas} marcas al cliente '{titular}' (ID: {cliente_id}) con CUIT {cuit}")
        
        # Verificar que las vinculaciones funcionaron
        cursor.execute("""
            SELECT COUNT(*) FROM Marcas WHERE cliente_id = ? AND REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ?
        """, (cliente_id, cuit_clean))
        
        total_vinculadas = cursor.fetchone()[0]
        logging.info(f"Total de marcas vinculadas al cliente {cliente_id} con CUIT {cuit_clean}: {total_vinculadas}")
        
        filas_afectadas = cursor.rowcount
        conn.commit()
        
        if filas_afectadas > 0:
            logging.info(f"Se vincularon {filas_afectadas} marcas al cliente '{titular}' (ID: {cliente_id}) con CUIT {cuit}")
            
        return filas_afectadas
            
    except sqlite3.Error as e:
        logging.error(f"Error al vincular marcas con cliente: {e}")
        conn.rollback()
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()

def insertar_marca(conn, marca, codigo_marca, clase, acta=None, custodia=None, cuit=None, titular=None, nrocon=None, email=None, cliente_id=None):
    """
    Inserta una nueva marca en la tabla 'marcas'.
    Si existe un cliente con el mismo CUIT, establece automáticamente la relación.
    
    Args:
        conn: Conexión a la base de datos
        marca: Nombre de la marca
        codigo_marca: Código de la marca
        clase: Clase de la marca
        acta: Número de acta
        custodia: Indicador de custodia
        cuit: CUIT del titular
        titular: Nombre del titular
        
    Returns:
        int: ID de la marca insertada o None si ocurre un error
    """
    try:
        cursor = conn.cursor()
        cliente_id = None
        cliente_nombre = None
        
        # Si se proporciona un CUIT, buscar el cliente correspondiente
        if cuit:
            # Asegurar compatibilidad entre string e int para CUIT
            cuit_str = str(cuit) if isinstance(cuit, (int, float)) else cuit
            cuit_int = int(cuit) if isinstance(cuit, str) and cuit.isdigit() else None
            
            # Intentar buscar el cliente con CUIT como string y como int
            # Ordenar por id DESC para tomar el cliente más reciente con ese CUIT
            if cuit_int is not None:
                cursor.execute("SELECT id, titular, cuit FROM clientes WHERE cuit = ? OR cuit = ? ORDER BY id DESC LIMIT 1", (cuit_str, cuit_int))
            else:
                cursor.execute("SELECT id, titular, cuit FROM clientes WHERE cuit = ? ORDER BY id DESC LIMIT 1", (cuit_str,))
                
            cliente_result = cursor.fetchone()
            if cliente_result:
                cliente_id = cliente_result[0]
                cliente_nombre = cliente_result[1]
                cliente_cuit = cliente_result[2]
                logging.info(f"Vinculando marca '{marca}' con cliente '{cliente_nombre}' (ID: {cliente_id}, CUIT: {cliente_cuit})")
            else:
                logging.info(f"No se encontró cliente con CUIT {cuit} para vincular con marca '{marca}'")
        
        # Insertar la nueva marca
        cursor.execute("""
            INSERT INTO Marcas (marca, codigo_marca, clase, acta, custodia, cuit, cliente_id, titular, nrocon, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (marca, codigo_marca, clase, acta, custodia, cuit, cliente_id, titular, nrocon, email))
        
        # Obtener el ID de la marca recién insertada
        cursor.execute("SELECT last_insert_rowid()")
        marca_id = cursor.fetchone()[0]
        
        conn.commit()
        
        # Después de insertar la marca, verificamos de nuevo si existe un cliente con el mismo CUIT
        # Este paso es necesario en caso de que el cliente haya sido insertado entre nuestra verificación y nuestra inserción
        if cuit:
            # Asegurar compatibilidad entre string e int para CUIT
            cuit_str = str(cuit) if isinstance(cuit, (int, float)) else cuit
            cuit_int = int(cuit) if isinstance(cuit, str) and cuit.isdigit() else None
            
            # Intentar buscar el cliente más reciente (mayor ID) con CUIT como string y como int
            if cuit_int is not None:
                cursor.execute("SELECT id FROM clientes WHERE cuit = ? OR cuit = ? ORDER BY id DESC LIMIT 1", (cuit_str, cuit_int))
            else:
                cursor.execute("SELECT id FROM clientes WHERE cuit = ? ORDER BY id DESC LIMIT 1", (cuit_str,))
                
            cliente_result = cursor.fetchone()
            if cliente_result and cliente_result[0]:
                cliente_id_reciente = cliente_result[0]
                
                # Actualizar la marca recién insertada con el cliente_id más reciente
                cursor.execute("""
                    UPDATE Marcas SET cliente_id = ? WHERE id = ?
                """, (cliente_id_reciente, marca_id))
                conn.commit()
                logging.info(f"Marca ID {marca_id} vinculada automáticamente con cliente ID {cliente_id_reciente} (el más reciente)")
            else:
                logging.info(f"No se encontró cliente con CUIT {cuit} para vincular con marca ID {marca_id}")
        
        if cliente_id:
            logging.info(f"Marca insertada y vinculada: '{marca}' (ID: {marca_id}) con cliente '{cliente_nombre}' (ID: {cliente_id})")
        else:
            logging.info(f"Marca insertada sin vincular: '{marca}' (ID: {marca_id})")
        
        return marca_id
        
    except sqlite3.Error as e:
        logging.error(f"Error al insertar marca: {e}")
        conn.rollback()
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()

def actualizar_marca(conn, marca_id, marca, codigo_marca, clase, acta=None, custodia=None, cuit=None, titular=None, nrocon=None, email=None, cliente_id=None):
    """
    Actualiza una marca existente en la tabla 'marcas'.
    Si el CUIT cambia, verifica y actualiza la relación con el cliente correspondiente.
    
    Args:
        conn: Conexión a la base de datos
        marca_id: ID de la marca a actualizar
        marca: Nombre de la marca
        codigo_marca: Código de la marca
        clase: Clase de la marca
        acta: Número de acta
        custodia: Indicador de custodia
        cuit: CUIT del titular
        titular: Nombre del titular
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        cursor = conn.cursor()
        
        # Obtener el CUIT actual para ver si cambió
        cursor.execute("SELECT cuit FROM Marcas WHERE id = ?", (marca_id,))
        result = cursor.fetchone()
        if not result:
            logging.warning(f"Marca con ID {marca_id} no encontrada")
            return False
            
        cuit_antiguo = result[0]
        cliente_id = None
        
        # Si se proporciona un CUIT (nuevo o existente), intentar vincular con cliente
        if cuit:
            cursor.execute("SELECT id FROM clientes WHERE cuit = ?", (cuit,))
            cliente_result = cursor.fetchone()
            if cliente_result:
                cliente_id = cliente_result[0]
                logging.info(f"Actualizando vinculación de marca ID {marca_id} con cliente ID {cliente_id}")
            else:
                logging.info(f"No se encontró cliente con CUIT {cuit} para vincular con marca ID {marca_id}")
        
        # Actualizar la marca
        # Actualizar la marca con todos los campos
        cursor.execute("""
            UPDATE Marcas
            SET marca = ?, codigo_marca = ?, clase = ?, 
                acta = ?, custodia = ?, cuit = ?, titular = ?,
                nrocon = ?, email = ?, cliente_id = ?
            WHERE id = ?
        """, (marca, codigo_marca, clase, acta, custodia, cuit, titular, 
              nrocon, email, cliente_id, marca_id))
        
        conn.commit()
        logging.info(f"Marca ID {marca_id} actualizada")
        
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar marca: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def obtener_marcas(conn, filtro_cuit=None, filtro_cliente_id=None):
    """
    Obtiene las marcas de la base de datos, con filtros opcionales.
    
    Args:
        conn: Conexión a la base de datos
        filtro_cuit: Filtrar marcas por CUIT específico
        filtro_cliente_id: Filtrar marcas por ID de cliente
        
    Returns:
        tuple: (filas, columnas) con los datos y nombres de columnas
    """
    try:
        cursor = conn.cursor()
        
        # Construir consulta con JOIN para obtener datos del cliente relacionado
        query = """
            SELECT m.id, m.marca, m.codigo_marca, m.clase, m.acta, m.custodia,
                   m.cuit, m.cliente_id, m.titular, m.nrocon, m.email,
                   c.titular as cliente_nombre
            FROM Marcas m
            LEFT JOIN clientes c ON m.cliente_id = c.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si se especifican
        if filtro_cuit:
            query += " AND m.cuit = ?"
            params.append(filtro_cuit)
            
        if filtro_cliente_id:
            query += " AND m.cliente_id = ?"
            params.append(filtro_cliente_id)
            
        query += " ORDER BY m.id DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return rows, columns
        
    except sqlite3.Error as e:
        logging.error(f"Error al consultar marcas: {e}")
        raise Exception(f"Error al consultar marcas: {e}")
    finally:
        if cursor:
            cursor.close()


def obtener_marcas_por_cliente(conn, cliente_id):
    """
    Obtiene todas las marcas vinculadas a un cliente específico.
    
    Args:
        conn: Conexión a la base de datos
        cliente_id: ID del cliente
        
    Returns:
        list: Lista de diccionarios con la información de las marcas
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, marca, codigo_marca, clase, acta, custodia, cuit, titular, nrocon, email
            FROM Marcas
            WHERE cliente_id = ?
            ORDER BY marca
        """, (cliente_id,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            # Convertir cada fila a un diccionario
            marca_dict = {columns[i]: row[i] for i in range(len(columns))}
            results.append(marca_dict)
            
        return results
        
    except sqlite3.Error as e:
        logging.error(f"Error al obtener marcas por cliente: {e}")
        return []


def eliminar_marca(conn, marca_id):
    """
    Elimina una marca de la base de datos.
    
    Args:
        conn: Conexión a la base de datos
        marca_id: ID de la marca a eliminar
        
    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Marcas WHERE id = ?", (marca_id,))
        conn.commit()
        
        filas_afectadas = cursor.rowcount
        if filas_afectadas > 0:
            logging.info(f"Marca ID {marca_id} eliminada")
            return True
        else:
            logging.warning(f"No se encontró marca con ID {marca_id}")
            return False
            
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar marca: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()