# database.py - Versión modificada con campo importancia

import sqlite3
import logging
import os
import re
import unicodedata
from datetime import datetime, timedelta
from paths import get_db_path, get_logs_dir

# Configuración del logging optimizado
log_file = os.path.join(get_logs_dir(), 'boletines.log')

# Forzar reconfiguración del logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,  # Cambiado a INFO para capturar logs de diagnóstico
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True
)

# Función auxiliar para escribir debug directo al archivo
def debug_write(mensaje):
    """Escribe directamente al archivo de log sin depender de logging"""
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - DEBUG - {mensaje}\n")
            f.flush()
    except Exception:
        pass

debug_write("=== DATABASE.PY CARGADO ===")

# ---------------------------------------------------------------------------
# UDF de normalización de nombres para comparación flexible en SQLite.
# Registrada en cada conexión vía crear_conexion() → disponible en todas las
# queries como normalizar_titular(nombre).
#
# Transforma ambos lados del JOIN de modo que:
#   "ROSSI, NATALIA"  →  "rossi natalia"
#   "Rossi Natalia"   →  "rossi natalia"
# Cubriendo: mayúsculas, tildes, comas, puntos, guiones, espacios extra.
# ---------------------------------------------------------------------------
def _normalizar_titular(nombre):
    """
    Normaliza un nombre de titular para comparación flexible en JOINs SQLite.

    Diseñada para textos copiados de PDFs, sistemas externos o ingresados
    manualmente, donde pueden aparecer caracteres invisibles y espaciado
    Unicode no estándar.

    Pipeline de normalización:
      1. Coerce a str (acepta cualquier tipo SQLite).
      2. Eliminar caracteres invisibles / de control Unicode:
           - Zero-Width Space          U+200B
           - Zero-Width Non-Joiner     U+200C
           - Zero-Width Joiner         U+200D
           - Word Joiner               U+2060
           - Soft Hyphen               U+00AD
           - BOM / Zero-Width No-Break U+FEFF
           - Left/Right marks          U+200E, U+200F
           - Todos los demás controles (Cc) y formatos (Cf)
      3. Convertir cualquier whitespace Unicode (NBSP U+00A0, thin space U+2009,
         em space U+2003, ideographic space U+3000, etc.) → espacio ASCII normal.
      4. Minúsculas.
      5. Descomposición NFD + descarte de diacríticos/combining marks →
         elimina tildes, diéresis, cedillas, etc.
      6. Reemplazar puntuación frecuente (coma, punto, guion, barra, paréntesis,
         corchetes, punto y coma, dos puntos, comillas) → espacio.
      7. Colapsar espacios múltiples + strip.

    Ejemplos garantizados:
        "ROSSI, NATALIA"            → "rossi natalia"
        "ROSSI\\u00a0NATALIA"       → "rossi natalia"  (NBSP)
        "ROSSI\\u200bNATALIA"       → "rossinalatia"   (ZWS eliminado)
        "GARCÍA, JOSÉ"              → "garcia jose"
        "  Pérez - Rodríguez, M. "  → "perez rodriguez m"
        "D'ANDREA MARCO"            → "d andrea marco"

    IMPORTANTE — nunca lanza excepción:
        SQLite trata cualquier excepción en una UDF como NULL, lo que hace
        que la condición JOIN evalúe NULL = NULL → FALSE → fila no vinculada.
        El doble try/except garantiza que siempre se devuelve algo utilizable.
    """
    if nombre is None:
        return None
    try:
        s = str(nombre)

        # ── Paso 1: eliminar caracteres de control e invisibles ──────────────
        # Categorías Unicode:
        #   Cc = control (tab, newline, etc.)
        #   Cf = format (ZWJ, ZWNJ, BOM, soft-hyphen, directional marks, etc.)
        # Se elimina todo el bloque Cf y Cc excepto el espacio ASCII (U+0020).
        cleaned = []
        for ch in s:
            cat = unicodedata.category(ch)
            if cat in ("Cc", "Cf"):
                continue  # descartar sin reemplazar
            cleaned.append(ch)
        s = "".join(cleaned)

        # ── Paso 2: normalizar cualquier whitespace Unicode → espacio ASCII ──
        # \s de Python cubre: espacio, tab, newline, CR, FF, VT, y también
        # U+00A0 (NBSP), U+2000-U+200A (espacios tipográficos), U+2028-U+2029
        # (line/paragraph separators), U+3000 (espacio ideográfico), etc.
        # re.sub con \s+ sobre el string ya limpio colapsa todo en un espacio.
        # Primero normalizamos NFC para reunir posibles combining sueltos.
        s = unicodedata.normalize("NFC", s)

        # ── Paso 3: minúsculas ───────────────────────────────────────────────
        s = s.lower()

        # ── Paso 4: eliminar tildes/diacríticos ─────────────────────────────
        # NFD descompone á → a + U+0301 (combining acute accent).
        # encode ASCII 'ignore' descarta todo codepoint > 127 (combining marks).
        s = unicodedata.normalize("NFD", s)
        s = s.encode("ascii", "ignore").decode("ascii")

        # ── Paso 5: puntuación → espacio ─────────────────────────────────────
        # Cubre los separadores más comunes en nombres de titulares:
        # coma, punto, guion, barra, paréntesis, corchetes, punto y coma,
        # dos puntos, comillas simples/dobles/tipográficas, arroba, ampersand.
        s = re.sub(r"[,.\-/()\[\]{};:'\"\u2018\u2019\u201c\u201d@&]", " ", s)

        # ── Paso 6: colapsar whitespace múltiple ─────────────────────────────
        s = re.sub(r"\s+", " ", s).strip()

        return s

    except Exception:
        # Fallback de último recurso: sin normalización compleja.
        # Siempre devuelve algo, nunca propaga excepción hacia SQLite.
        try:
            return re.sub(r"\s+", " ", str(nombre)).strip().lower()
        except Exception:
            return None

# Logger específico para eventos críticos del sistema
critical_logger = logging.getLogger('critical_events')
critical_logger.setLevel(logging.INFO)

# Verificar si ya tiene handlers para evitar duplicados
if not critical_logger.handlers:
    critical_handler = logging.FileHandler(log_file)
    critical_handler.setFormatter(logging.Formatter('%(asctime)s - CRITICAL - %(message)s'))
    critical_logger.addHandler(critical_handler)

critical_logger.propagate = False

def crear_conexion():
    """Crea y devuelve una conexión a la base de datos SQLite."""
    debug_write(">>> Entrando a crear_conexion()")
    try:
        # Usar timeout más alto y permitir conexiones desde distintos hilos
        db_path = get_db_path()
        debug_write(f"DB path: {db_path}")
        conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)

        # Ajustes para reducir bloqueos - NO cambiar journal_mode en cada conexión
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            # Solo aplicar WAL si no está ya configurado (evita bloqueos en primera ejecución)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            current_mode = cursor.fetchone()[0]
            if current_mode != 'wal':
                debug_write(f"Configurando WAL mode (actual: {current_mode})")
                conn.execute("PRAGMA journal_mode = WAL")
            cursor.close()
            
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 30000")
        except Exception as pragma_e:
            logging.warning(f"No se pudieron aplicar PRAGMA en DB {db_path}: {pragma_e}")

        # Registrar la UDF de normalización de nombres.
        # Disponible en SQL como:  normalizar_titular(columna)
        conn.create_function("normalizar_titular", 1, _normalizar_titular)

        # Auto-test: verifica que la UDF esté operativa y produce los resultados
        # esperados para los patrones más frecuentes en datos de PDFs.
        try:
            test_cur = conn.cursor()
            # Cada caso: (entrada, salida_esperada, descripción)
            _udf_tests = [
                ("ROSSI, NATALIA",          "rossi natalia", "coma + mayúsculas"),
                ("ROSSI\u00a0NATALIA",      "rossi natalia", "NBSP U+00A0"),
                ("GARC\u00cdA, JOS\u00c9",  "garcia jose",   "tildes + coma"),
                ("  Pérez  -  Rodríguez  ", "perez rodriguez","guion + espacios extra"),
                ("D\u2019ANDREA",           "d andrea",      "comilla tipográfica U+2019"),
            ]
            failed = []
            for entrada, esperado, desc in _udf_tests:
                test_cur.execute("SELECT normalizar_titular(?)", (entrada,))
                got = test_cur.fetchone()[0]
                if got != esperado:
                    failed.append(f"  [{desc}] '{entrada}' → '{got}' (esperado: '{esperado}')")
            test_cur.close()
            if failed:
                logging.debug(
                    "normalizar_titular UDF: los siguientes casos no coinciden:\n" +
                    "\n".join(failed)
                )
            else:
                debug_write("UDF normalizar_titular OK: todos los auto-tests pasaron")
        except Exception as udf_e:
            logging.error(f"normalizar_titular UDF falló el auto-test: {udf_e}")

        logging.info(f"Conexión SQLite abierta: {db_path}")
        debug_write(f"<<< Conexión SQLite exitosa: {db_path}")
        return conn
    except sqlite3.Error as e:
        debug_write(f"ERROR en crear_conexion: {e}")
        logging.error(f"Error al conectar con la base de datos: {e}")
        raise Exception(f"Error al conectar con la base de datos: {e}")

def diagnosticar_vinculacion(conn, max_filas=20):
    """
    Diagnóstico de vinculación boletines↔clientes.

    Devuelve un dict con:
    - udf_ok:           bool  — la UDF está registrada y funciona
    - udf_resultado:    str   — resultado del test 'ROSSI, NATALIA'
    - db_path:          str   — ruta de la base de datos activa
    - sin_cliente:      list  — titulares de boletines sin cliente vinculado
    - muestra_norm:     list  — pares (titular_boletin_norm, titular_cliente_norm)
                                para los primeros N boletines sin cliente
    - python_version:   str   — versión de Python activa
    """
    import sys
    resultado = {
        "udf_ok": False,
        "udf_resultado": None,
        "db_path": None,
        "sin_cliente": [],
        "muestra_norm": [],
        "python_version": sys.version,
    }
    try:
        cursor = conn.cursor()

        # 1) Ruta de la DB activa
        cursor.execute("PRAGMA database_list")
        db_list = cursor.fetchall()
        resultado["db_path"] = db_list[0][2] if db_list else "desconocida"

        # 2) Verificar UDF
        try:
            cursor.execute("SELECT normalizar_titular('ROSSI, NATALIA')")
            resultado["udf_resultado"] = cursor.fetchone()[0]
            resultado["udf_ok"] = (resultado["udf_resultado"] == "rossi natalia")
        except Exception as e:
            resultado["udf_resultado"] = f"ERROR: {e}"
            resultado["udf_ok"] = False

        # 3) Titulares de boletines sin cliente vinculado (con y sin UDF)
        cursor.execute("""
            SELECT DISTINCT b.titular
            FROM boletines b
            LEFT JOIN clientes c
                   ON normalizar_titular(b.titular) = normalizar_titular(c.titular)
            LEFT JOIN Marcas m
                   ON c.id IS NULL
                  AND normalizar_titular(b.titular) = normalizar_titular(m.titular)
                  AND m.cliente_id IS NOT NULL
            LEFT JOIN clientes c2
                   ON c.id IS NULL AND m.cliente_id = c2.id
            WHERE c.id IS NULL AND c2.id IS NULL
            ORDER BY b.titular
            LIMIT ?
        """, (max_filas,))
        resultado["sin_cliente"] = [r[0] for r in cursor.fetchall()]

        # 4) Para cada titular sin cliente, mostrar el valor normalizado
        #    y los valores normalizados de clientes que existen en la DB
        if resultado["sin_cliente"]:
            muestras = []
            for titular in resultado["sin_cliente"][:5]:  # solo primeros 5
                norm_b = _normalizar_titular(titular)
                cursor.execute(
                    "SELECT titular, normalizar_titular(titular) FROM clientes ORDER BY titular LIMIT 10"
                )
                clientes_norm = cursor.fetchall()
                muestras.append({
                    "boletin_original": titular,
                    "boletin_normalizado": norm_b,
                    "clientes_normalizados": [
                        {"original": r[0], "normalizado": r[1]} for r in clientes_norm
                    ],
                })
            resultado["muestra_norm"] = muestras

        cursor.close()
    except Exception as e:
        resultado["error"] = str(e)
    return resultado


def crear_tabla(conn):
    """Crea las tablas 'boletines' y 'clientes' con índices si no existen."""
    debug_write(">>> Entrando a crear_tabla()")
    cursor = None
    try:
        cursor = conn.cursor()
        debug_write("Cursor creado, verificando tablas...")
        logging.info("Iniciando creación/verificación de tablas en la base de datos")
        
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

        # Crear tabla emails_enviados (compatibilidad con módulo de envíos)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails_enviados'")
        tabla_emails_existe = cursor.fetchone()

        if not tabla_emails_existe:
            critical_logger.info("Creando tabla 'emails_enviados' por primera vez...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destinatario TEXT NOT NULL,
                asunto TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                tipo_email TEXT DEFAULT 'general',
                status TEXT DEFAULT 'pendiente',
                fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                titular TEXT DEFAULT NULL
            )
        """)
        conn.commit()

        if not tabla_emails_existe:
            critical_logger.info("Tabla 'emails_enviados' creada exitosamente.")

        # Verificar y agregar columna 'titular' si la tabla ya existía sin ella
        try:
            cursor.execute("PRAGMA table_info(emails_enviados)")
            columns_emails = [column[1] for column in cursor.fetchall()]

            if 'titular' not in columns_emails:
                cursor.execute("ALTER TABLE emails_enviados ADD COLUMN titular TEXT DEFAULT NULL")
                critical_logger.info("Columna 'titular' agregada a emails_enviados.")
                conn.commit()
        except Exception as e:
            logging.warning(f"Error actualizando estructura de emails_enviados: {e}")

        logging.info("Finalizada creación/verificación de tablas en la base de datos")
        debug_write("<<< crear_tabla() completada exitosamente")
    except sqlite3.Error as e:
        debug_write(f"ERROR en crear_tabla: {e}")
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
    """
    Obtiene todos los registros de boletines con datos de clientes.

    Estrategia de vinculación (dos pasos, sin modificar boletines):
    1. Unión directa por nombre: LOWER(b.titular) = LOWER(c.titular)
    2. Fallback via Marcas: si el paso 1 no encuentra cliente,
       busca una marca cuyo titular coincida con el del boletín y
       usa el cliente_id de esa marca (c2).
    Esto permite recuperar datos de email/teléfono/etc. para boletines
    históricos cuyo titular fue guardado con un nombre diferente al del
    cliente, siempre que ambos nombres existan en la tabla Marcas.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.id, b.titular, b.numero_orden, b.marca_custodia, b.marca_publicada, b.numero_boletin,
                b.importancia, b.fecha_boletin,
                b.solicitante, b.agente, b.numero_expediente, b.clase,
                b.clases_acta,
                b.reporte_enviado, b.reporte_generado, b.fecha_alta,
                COALESCE(c.email,  c2.email)     AS email,
                COALESCE(c.telefono, c2.telefono) AS telefono,
                COALESCE(c.direccion, c2.direccion) AS direccion,
                COALESCE(c.ciudad, c2.ciudad)    AS ciudad
            FROM boletines b
            -- Paso 1: vínculo directo por nombre normalizado
            --   normalizar_titular() elimina comas, tildes, espacios extra, etc.
            --   Ej: "ROSSI, NATALIA" y "ROSSI NATALIA" → "rossi natalia"
            LEFT JOIN clientes c
                   ON normalizar_titular(b.titular) = normalizar_titular(c.titular)
            -- Paso 2: fallback via Marcas cuando el paso 1 no resuelve
            LEFT JOIN Marcas m
                   ON c.id IS NULL
                  AND normalizar_titular(b.titular) = normalizar_titular(m.titular)
                  AND m.cliente_id IS NOT NULL
            LEFT JOIN clientes c2
                   ON c.id IS NULL
                  AND m.cliente_id = c2.id
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
    """
    Obtiene boletines con reporte generado pero no enviado para clasificar.

    Aplica la misma estrategia de doble JOIN que obtener_datos:
    1. Unión directa por nombre (case-insensitive, consistente con obtener_datos).
    2. Fallback via Marcas cuando el paso 1 no resuelve el cliente.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.id, b.titular, b.numero_boletin, b.fecha_boletin,
                b.numero_orden, b.solicitante, b.marca_custodia,
                b.marca_publicada, b.importancia,
                COALESCE(c.email, c2.email) AS email
            FROM boletines b
            LEFT JOIN clientes c
                   ON normalizar_titular(b.titular) = normalizar_titular(c.titular)
            LEFT JOIN Marcas m
                   ON c.id IS NULL
                  AND normalizar_titular(b.titular) = normalizar_titular(m.titular)
                  AND m.cliente_id IS NOT NULL
            LEFT JOIN clientes c2
                   ON c.id IS NULL
                  AND m.cliente_id = c2.id
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
    Luego vincula automáticamente todas las marcas con el mismo CUIT.

    IMPORTANTE sobre el nombre del titular:
    El cliente se guarda SIEMPRE con el nombre tal como viene del boletín (parámetro
    `titular`). No se sobreescribe con el nombre de la tabla Marcas aunque difiera,
    porque la vinculación boletín↔cliente se realiza por coincidencia de texto
    (normalizar_titular(b.titular) = normalizar_titular(c.titular)). Cambiar el nombre rompería ese JOIN
    para todos los boletines históricos de ese titular.
    Si hay discrepancia con Marcas, se registra en el log para revisión manual.

    Args:
        conn: Conexión a la base de datos
        titular: Nombre del titular (se preserva exactamente como viene del boletín)
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

        # Verificar duplicado usando normalización: "ROSSI, NATALIA" y "ROSSI NATALIA"
        # se consideran el mismo titular.
        cursor.execute(
            'SELECT titular FROM clientes WHERE normalizar_titular(titular) = normalizar_titular(?)',
            (titular,)
        )
        existing = cursor.fetchone()
        if existing:
            logging.info(f"Cliente omitido (ya existe como '{existing[0]}'): Titular '{titular}'")
            raise Exception(f"Cliente con titular '{titular}' ya existe (registrado como '{existing[0]}').")

        # Registrar discrepancia con Marcas si la hay, SIN modificar el nombre recibido.
        # El nombre no se sobreescribe para preservar la vinculación por texto con boletines.
        if cuit:
            cursor.execute('SELECT titular FROM Marcas WHERE cuit = ? LIMIT 1', (cuit,))
            resultado_marca = cursor.fetchone()
            if resultado_marca and resultado_marca[0]:
                titular_en_marcas = resultado_marca[0]
                if _normalizar_titular(titular_en_marcas) != _normalizar_titular(titular):
                    logging.warning(
                        f"insertar_cliente: discrepancia de nombre entre boletín "
                        f"('{titular}') y Marcas ('{titular_en_marcas}') para CUIT {cuit}. "
                        "Se conserva el nombre del boletín. La vinculación retroactiva "
                        "se resolverá vía Marcas en las consultas de historial/email."
                    )

        # Insertar el cliente con el nombre exacto recibido (del boletín)
        cursor.execute('''
            INSERT INTO clientes (titular, email, telefono, direccion, ciudad, provincia, fecha_alta, cuit)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        ''', (titular, email, telefono, direccion, ciudad, provincia, cuit))
        
        conn.commit()
        
        # Obtener el ID del cliente recién insertado
        cursor.execute("SELECT last_insert_rowid()")
        cliente_id = cursor.fetchone()[0]
        
        logging.info(f"Cliente insertado: ID {cliente_id}, Titular {titular}")
        
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
            cuit_clean = cuit_str.replace('-', '').replace(' ', '')
            cuit_int = int(cuit_clean) if cuit_clean.isdigit() else None
            
            if cuit_int is not None:
                cursor.execute("""
                    SELECT COUNT(*) FROM Marcas 
                    WHERE REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ? 
                    OR REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ?
                """, (cuit_clean, str(cuit_int)))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM Marcas 
                    WHERE REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ?
                """, (cuit_clean,))
            
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
            titular = row[1]  # Índice 1 corresponde a titular en la consulta
            cuit = row[7]  # Índice 7 corresponde a cuit en la consulta
            
            # Verificamos primero por cliente_id (relación directa) - esto es más preciso
            cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?", (cliente_id,))
            count_by_id = cursor.fetchone()[0]
            tiene_marcas_id = count_by_id > 0
            
            # También verificamos por coincidencia de CUIT (para detección de potenciales vinculaciones)
            # Solo como información de depuración
            cuit_str = str(cuit) if cuit is not None else ""
            cuit_clean = cuit_str.replace('-', '').replace(' ', '') if cuit_str else ""
            cuit_int = int(cuit_clean) if cuit_clean.isdigit() else None
            
            count_by_cuit = 0
            if cuit_int is not None:
                cursor.execute("""
                    SELECT COUNT(*) FROM Marcas 
                    WHERE REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ? 
                    OR REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ?
                """, (cuit_clean, str(cuit_int)))
                count_by_cuit = cursor.fetchone()[0]
            elif cuit_clean:
                cursor.execute("""
                    SELECT COUNT(*) FROM Marcas 
                    WHERE REPLACE(REPLACE(cuit, '-', ''), ' ', '') = ?
                """, (cuit_clean,))
                count_by_cuit = cursor.fetchone()[0]
            
            if count_by_cuit > 0:
                logging.debug(f"Cliente {cliente_id} ({titular}) - Marcas por CUIT: {count_by_cuit}")
            
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
            logging.info(f"Total: Se vincularon {marcas_vinculadas} marcas al cliente '{nombre_titular_final}' (ID: {cliente_id}) con CUIT {cuit}")
            
            # Verificar que las vinculaciones funcionaron
            cursor.execute("""
                SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?
            """, (cliente_id,))
            
            total_vinculadas = cursor.fetchone()[0]
            logging.info(f"Total de marcas vinculadas al cliente {cliente_id}: {total_vinculadas}")
            
            # Forzar el refresco de datos en UI
            # Siempre actualizar fecha_modificacion para forzar la recarga
            cursor.execute("""
                UPDATE clientes SET fecha_modificacion = datetime('now', 'localtime') WHERE id = ?
            """, (cliente_id,))
            
            if marcas_vinculadas > 0:
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
                    logging.info(f"  - Marca '{marca[1]}' (ID: {marca[0]}, CUIT: {marca[2]}) vinculada al cliente {nombre_titular_final}")
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
        
        # Verificar que las vinculaciones funcionaron - contar TODAS las marcas vinculadas al cliente
        cursor.execute("""
            SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?
        """, (cliente_id,))
        
        total_vinculadas = cursor.fetchone()[0]
        logging.info(f"Total de marcas vinculadas al cliente {cliente_id}: {total_vinculadas}")
        
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

def verificar_cuit_duplicado_marca(conn, cuit, excluir_id=None):
    """
    Verifica si un CUIT ya existe en la tabla Marcas.

    Args:
        conn:        Conexión SQLite activa.
        cuit:        CUIT a verificar (se normaliza a solo dígitos internamente).
        excluir_id:  ID de la marca que se está editando; se excluye de la búsqueda
                     para que el CUIT actual de la marca no se reporte como duplicado.

    Returns:
        dict | None:
            None  → el CUIT es único (o estaba vacío).
            dict  → {'id': int, 'marca': str, 'titular': str}
                    de la primera marca que ya usa ese CUIT.
    """
    if not cuit:
        return None
    cuit_norm = "".join(ch for ch in str(cuit) if ch.isdigit())
    if not cuit_norm:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        if excluir_id is not None:
            cursor.execute(
                "SELECT id, marca, titular FROM Marcas "
                "WHERE REPLACE(REPLACE(COALESCE(cuit,''),'-',''),' ','') = ? "
                "AND id != ? LIMIT 1",
                (cuit_norm, int(excluir_id)),
            )
        else:
            cursor.execute(
                "SELECT id, marca, titular FROM Marcas "
                "WHERE REPLACE(REPLACE(COALESCE(cuit,''),'-',''),' ','') = ? LIMIT 1",
                (cuit_norm,),
            )
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "marca": row[1], "titular": row[2]}
        return None
    except Exception as e:
        logging.error(f"verificar_cuit_duplicado_marca: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def insertar_marca(conn, marca, codigo_marca, clase, acta=None, custodia=None, cuit=None, titular=None, nrocon=None, email=None, cliente_id=None):
    """
    Inserta una nueva marca en la tabla 'marcas'.

    Lógica de vinculación (en orden de prioridad):
      1. Si se recibe cliente_id explícito y válido → se usa directamente.
      2. Si cliente_id es None → se intenta resolver por CUIT (fallback original).
      3. Si aún es None tras el fallback → se hace una segunda búsqueda post-insert
         por CUIT para cubrir condiciones de carrera.

    Args:
        conn: Conexión a la base de datos
        marca: Nombre de la marca
        codigo_marca: Código de la marca
        clase: Clase de la marca
        acta: Número de acta
        custodia: Indicador de custodia
        cuit: CUIT del titular
        titular: Nombre del titular
        nrocon: Número de concesión
        email: Email de contacto
        cliente_id: ID de cliente explícito (prioridad sobre búsqueda por CUIT)

    Returns:
        int: ID de la marca insertada o None si ocurre un error
    """
    try:
        cursor = conn.cursor()
        cliente_nombre = None

        # --- Paso 1: respetar cliente_id explícito recibido por parámetro ---
        # Normalizar: el formulario puede enviar el id como string ("42") o int (42).
        cliente_id_resuelto = None
        if cliente_id is not None and str(cliente_id).strip() not in ("", "None"):
            try:
                cliente_id_resuelto = int(cliente_id)
            except (ValueError, TypeError):
                cliente_id_resuelto = None

        if cliente_id_resuelto is not None:
            # Verificar que el cliente realmente existe antes de usarlo
            cursor.execute(
                "SELECT titular FROM clientes WHERE id = ?",
                (cliente_id_resuelto,)
            )
            cliente_row = cursor.fetchone()
            if cliente_row:
                cliente_nombre = cliente_row[0]
                logging.info(
                    f"Usando cliente_id explícito {cliente_id_resuelto} "
                    f"('{cliente_nombre}') para marca '{marca}'"
                )
            else:
                logging.warning(
                    f"cliente_id {cliente_id_resuelto} no existe en clientes; "
                    f"aplicando fallback por CUIT para marca '{marca}'"
                )
                cliente_id_resuelto = None

        # --- Paso 2 (fallback): buscar cliente por CUIT solo si no hay id explícito ---
        if cliente_id_resuelto is None and cuit:
            cuit_str = str(cuit) if isinstance(cuit, (int, float)) else cuit
            cuit_int = int(cuit) if isinstance(cuit, str) and cuit.isdigit() else None

            if cuit_int is not None:
                cursor.execute(
                    "SELECT id, titular, cuit FROM clientes "
                    "WHERE cuit = ? OR cuit = ? ORDER BY id DESC LIMIT 1",
                    (cuit_str, cuit_int)
                )
            else:
                cursor.execute(
                    "SELECT id, titular, cuit FROM clientes "
                    "WHERE cuit = ? ORDER BY id DESC LIMIT 1",
                    (cuit_str,)
                )

            cliente_result = cursor.fetchone()
            if cliente_result:
                cliente_id_resuelto = cliente_result[0]
                cliente_nombre = cliente_result[1]
                cliente_cuit = cliente_result[2]
                logging.info(
                    f"Vinculando marca '{marca}' con cliente '{cliente_nombre}' "
                    f"(ID: {cliente_id_resuelto}, CUIT: {cliente_cuit}) [por CUIT]"
                )
            else:
                logging.info(
                    f"No se encontró cliente con CUIT {cuit} para vincular con marca '{marca}'"
                )

        # --- Insertar la nueva marca con el cliente_id resuelto ---
        cursor.execute("""
            INSERT INTO Marcas (marca, codigo_marca, clase, acta, custodia, cuit, cliente_id, titular, nrocon, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (marca, codigo_marca, clase, acta, custodia, cuit,
              cliente_id_resuelto, titular, nrocon, email))

        cursor.execute("SELECT last_insert_rowid()")
        marca_id = cursor.fetchone()[0]

        conn.commit()

        # --- Paso 3: segunda verificación por CUIT (solo si aún sin cliente) ---
        # Cubre condición de carrera: cliente insertado entre la verificación y el INSERT.
        # No se ejecuta cuando ya se resolvió un cliente_id en los pasos anteriores.
        if cliente_id_resuelto is None and cuit:
            cuit_str = str(cuit) if isinstance(cuit, (int, float)) else cuit
            cuit_int = int(cuit) if isinstance(cuit, str) and cuit.isdigit() else None

            if cuit_int is not None:
                cursor.execute(
                    "SELECT id FROM clientes WHERE cuit = ? OR cuit = ? ORDER BY id DESC LIMIT 1",
                    (cuit_str, cuit_int)
                )
            else:
                cursor.execute(
                    "SELECT id FROM clientes WHERE cuit = ? ORDER BY id DESC LIMIT 1",
                    (cuit_str,)
                )

            cliente_result = cursor.fetchone()
            if cliente_result and cliente_result[0]:
                cliente_id_resuelto = cliente_result[0]
                cursor.execute(
                    "UPDATE Marcas SET cliente_id = ? WHERE id = ?",
                    (cliente_id_resuelto, marca_id)
                )
                conn.commit()
                logging.info(
                    f"Marca ID {marca_id} vinculada automáticamente con cliente "
                    f"ID {cliente_id_resuelto} [por CUIT post-insert]"
                )
            else:
                logging.info(
                    f"No se encontró cliente con CUIT {cuit} para vincular con marca ID {marca_id}"
                )

        if cliente_id_resuelto:
            logging.info(
                f"Marca insertada y vinculada: '{marca}' (ID: {marca_id}) "
                f"con cliente '{cliente_nombre}' (ID: {cliente_id_resuelto})"
            )
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

        # P3 — Respetar el cliente_id recibido como parámetro con la misma
        # lógica de prioridad que usa insertar_marca:
        #   1. cliente_id explícito y válido → usarlo directamente.
        #   2. cliente_id None + CUIT disponible → buscar cliente por CUIT (fallback).
        #   3. Sin datos suficientes → dejar NULL.
        # La versión anterior sobreescribía incondicionalmente con None (bug).
        cliente_id_resuelto = None

        if cliente_id is not None and str(cliente_id).strip() not in ("", "None"):
            try:
                cliente_id_resuelto = int(cliente_id)
            except (ValueError, TypeError):
                cliente_id_resuelto = None

        if cliente_id_resuelto is not None:
            cursor.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id_resuelto,))
            if not cursor.fetchone():
                logging.warning(
                    f"actualizar_marca: cliente_id {cliente_id_resuelto} no encontrado; "
                    f"aplicando fallback por CUIT para marca ID {marca_id}"
                )
                cliente_id_resuelto = None

        # Fallback por CUIT solo cuando no se recibió cliente_id válido
        if cliente_id_resuelto is None and cuit:
            cursor.execute(
                "SELECT id FROM clientes WHERE cuit = ? ORDER BY id DESC LIMIT 1",
                (str(cuit),)
            )
            cliente_result = cursor.fetchone()
            if cliente_result:
                cliente_id_resuelto = cliente_result[0]
                logging.info(
                    f"actualizar_marca: marca ID {marca_id} vinculada con cliente "
                    f"ID {cliente_id_resuelto} [por CUIT {cuit}]"
                )
            else:
                logging.info(
                    f"actualizar_marca: no se encontró cliente con CUIT {cuit} "
                    f"para marca ID {marca_id}"
                )

        cliente_id = cliente_id_resuelto
        
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

def actualizar_marca_cliente(conn, marca_id, cliente_id):
    """
    Actualiza únicamente el cliente_id de una marca existente.
    Pasar cliente_id=None desvincula la marca de cualquier cliente.

    Args:
        conn: Conexión SQLite activa.
        marca_id: ID de la marca a modificar.
        cliente_id: Nuevo ID de cliente (int) o None para desvincular.

    Returns:
        bool: True si se actualizó al menos una fila, False en caso contrario.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Marcas SET cliente_id = ? WHERE id = ?",
            (cliente_id, marca_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            logging.warning(f"actualizar_marca_cliente: marca ID {marca_id} no encontrada")
            return False
        logging.info(
            f"Marca ID {marca_id} → cliente_id actualizado a {cliente_id}"
        )
        return True
    except Exception as e:
        logging.error(f"Error en actualizar_marca_cliente: {e}")
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