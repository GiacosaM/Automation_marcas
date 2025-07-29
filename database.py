# database.py - Versión modificada con campo importancia

import sqlite3
import logging

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boletines.log'),
        logging.StreamHandler()
    ]
)

def crear_conexion():
    """Crea y devuelve una conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect('boletines.db')
        logging.info("Conexión a la base de datos establecida.")
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
        logging.info("Intentando crear la tabla 'boletines'...")
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
        logging.info("Tabla 'boletines' creada o verificada correctamente.")

        # Verificar si la columna importancia existe, si no, agregarla
        cursor.execute("PRAGMA table_info(boletines)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'importancia' not in columns:
            logging.info("Agregando columna 'importancia' a la tabla existente...")
            cursor.execute("""
                ALTER TABLE boletines 
                ADD COLUMN importancia TEXT DEFAULT 'Pendiente' 
                CHECK (importancia IN ('Pendiente', 'Baja', 'Media', 'Alta'))
            """)
            conn.commit()
            logging.info("Columna 'importancia' agregada correctamente.")

        # Crear tabla clientes
        logging.info("Intentando crear la tabla 'clientes'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titular TEXT UNIQUE,
                email TEXT,
                telefono TEXT,
                direccion TEXT,
                ciudad TEXT,
                fecha_alta DATE DEFAULT (datetime('now', 'localtime')),
                fecha_modificacion DATE
            )
        """)
        conn.commit()
        logging.info("Tabla 'clientes' creada o verificada correctamente.")

        # Crear índice en boletines
        logging.info("Intentando crear índice en 'boletines'...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_boletines
            ON boletines (numero_boletin, numero_orden, titular)
        ''')
        conn.commit()
        logging.info("Índice 'idx_boletines' creado o verificado correctamente.")

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
                    logging.debug(f"Insertado registro: Boletín {registro['Número de Boletín']}, Orden {registro['Número de Orden']}, Titular {titular}")
                else:
                    logging.info(f"Registro omitido (ya existe): Boletín {registro['Número de Boletín']}, Orden {registro['Número de Orden']}, Titular {titular}")
        conn.commit()
        logging.info("Inserción de datos completada.")
    except sqlite3.Error as e:
        logging.error(f"Error al insertar datos: {e}")
        raise Exception(f"Error al insertar datos: {e}")
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
        logging.info("Datos obtenidos correctamente desde la base de datos.")
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
        logging.info(f"Registro actualizado: ID {id}")
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
            logging.info(f"Importancia actualizada para boletín ID {boletin_id}: {importancia}")
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
        cursor.execute("DELETE FROM boletines WHERE id = ?", (id,))
        conn.commit()
        logging.info(f"Registro eliminado: ID {id}")
    except sqlite3.Error as e:
        logging.error(f"Error al eliminar: {e}")
        raise Exception(f"Error al eliminar: {e}")
    finally:
        cursor.close()

def insertar_cliente(conn, titular, email, telefono, direccion, ciudad):
    """Inserta un nuevo cliente en la tabla 'clientes', verificando duplicados."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM clientes WHERE titular = ?
        ''', (titular,))
        if cursor.fetchone()[0] == 0:  # Si no existe, insertar
            cursor.execute('''
                INSERT INTO clientes (titular, email, telefono, direccion, ciudad, fecha_alta)
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ''', (titular, email, telefono, direccion, ciudad))
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
            SELECT id, titular, email, telefono, direccion, ciudad
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

def actualizar_cliente(conn, id, titular, email, telefono, direccion, ciudad):
    """Actualiza un registro en la tabla 'clientes'."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes
            SET titular = ?, email = ?, telefono = ?, direccion = ?, ciudad = ?, fecha_modificacion = datetime('now', 'localtime')
            WHERE id = ?
        """, (titular, email, telefono, direccion, ciudad, id))
        conn.commit()
        logging.info(f"Cliente actualizado: ID {id}")
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar cliente: {e}")
        raise Exception(f"Error al actualizar cliente: {e}")
    finally:
        cursor.close()

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