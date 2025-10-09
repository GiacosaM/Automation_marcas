"""
Utilidades para gestionar la base de datos SQLite, incluyendo:
- Funciones de copia de seguridad con timestamp
- Funciones de restauración
- Verificación de integridad
"""

import os
import shutil
import sqlite3
import logging
import datetime
from pathlib import Path
import glob

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_operations.log"),
        logging.StreamHandler()
    ]
)

# Nombre de la base de datos principal
DB_NAME = "boletines.db"

def get_db_directory():
    """
    Obtiene el directorio donde está almacenada la base de datos
    
    Returns:
        str: Ruta al directorio de la base de datos
    """
    # Usar el directorio actual donde se ejecuta la aplicación, 
    # para mantener compatibilidad con el código existente
    db_dir = os.path.abspath(os.path.dirname(__file__))
    
    logger.info(f"Usando directorio para base de datos: {db_dir}")
    
    return db_dir

def get_backup_directory():
    """
    Obtiene o crea el directorio para almacenar copias de seguridad
    
    Returns:
        str: Ruta al directorio de backups
    """
    # Crear la carpeta de backups en el directorio del proyecto
    backup_dir = os.path.join(get_db_directory(), "backups_db")
    
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
            logger.info(f"Directorio de backups creado: {backup_dir}")
        except Exception as e:
            logger.error(f"Error al crear directorio para backups: {e}")
    
    return backup_dir

def get_db_path(db_name="boletines.db"):
    """
    Obtiene la ruta completa a la base de datos
    
    Args:
        db_name (str): Nombre del archivo de base de datos
    
    Returns:
        str: Ruta completa al archivo de base de datos
    """
    # Usar siempre el mismo nombre de archivo para mantener compatibilidad
    db_dir = get_db_directory()
    return os.path.join(db_dir, "boletines.db")

def initialize_db(db_path=None):
    """
    Inicializa la base de datos con las tablas necesarias si no existen
    
    Args:
        db_path (str, optional): Ruta a la base de datos. Si es None, se usa la ruta por defecto
        
    Returns:
        sqlite3.Connection: Conexión a la base de datos
    """
    if db_path is None:
        db_path = get_db_path()
    
    # Verificar si la base de datos ya existe
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        logger.info(f"La base de datos ya existe en {db_path}. No se inicializará.")
        try:
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error al conectar a la base de datos existente: {e}")
            raise
    
    # Verificar si el directorio existe
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear las tablas necesarias si no existen
        # Tabla de boletines
        cursor.execute('''
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
            importancia TEXT DEFAULT 'Pendiente' 
                CHECK (importancia IN ('Pendiente', 'Baja', 'Media', 'Alta'))
        )
        ''')
        
        # Tabla de clientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titular TEXT UNIQUE,
            email TEXT,
            telefono TEXT,
            direccion TEXT,
            ciudad TEXT,
            provincia TEXT,
            cuit INTEGER,
            fecha_alta DATE DEFAULT (datetime('now', 'localtime')),
            fecha_modificacion DATE
        )
        ''')
        
        # Tabla de marcas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codtit INTEGER,
            titular TEXT,
            codigo_marca TEXT,
            marca TEXT,
            clase INTEGER,
            acta TEXT,
            nrocon TEXT,
            custodia TEXT,
            cuit TEXT,
            email TEXT,
            cliente_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES Clientes(id)
        )
        ''')
        
        # Tabla de emails enviados
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails_enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destinatario TEXT NOT NULL,
            asunto TEXT,
            mensaje TEXT,
            fecha_envio TEXT,
            status TEXT,
            tipo_email TEXT,
            titular TEXT,
            periodo_notificacion TEXT,
            marcas_sin_reportes TEXT
        )
        ''')
        
        # Crear índices para mejorar rendimiento
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_boletines
        ON boletines (numero_boletin, numero_orden, titular)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_marcas_titular
        ON Marcas (titular)
        ''')
        
        conn.commit()
        logger.info(f"Base de datos inicializada en: {db_path}")
        return conn
        
    except sqlite3.Error as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise

def connect_db(db_path=None):
    """
    Conecta a la base de datos, usando la misma que la aplicación principal
    
    Args:
        db_path (str, optional): Ruta a la base de datos. Si es None, se usa la ruta por defecto
        
    Returns:
        sqlite3.Connection: Conexión a la base de datos
    """
    # Importar la función de conexión de la aplicación principal
    # para garantizar que siempre usemos la misma base de datos
    try:
        from database import crear_conexion
        conn = crear_conexion()
        logger.info(f"Conexión a la base de datos establecida utilizando crear_conexion()")
        return conn
    except Exception as e:
        # Si falla, intentar conectar directamente
        logger.warning(f"No se pudo usar crear_conexion(): {e}. Usando conexión directa.")
        
        if db_path is None:
            db_path = get_db_path()
            
        if not os.path.exists(db_path):
            logger.info(f"La base de datos no existe en {db_path}. Inicializando...")
            return initialize_db(db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            logger.info(f"Conexión a la base de datos establecida: {db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise

def create_backup(db_path=None, backup_name=None):
    """
    Crea una copia de seguridad de la base de datos con timestamp
    
    Args:
        db_path (str, optional): Ruta a la base de datos. Si es None, se usa la ruta por defecto
        backup_name (str, optional): Nombre personalizado para el backup. Si es None, se usa timestamp
        
    Returns:
        str: Ruta al archivo de backup creado o None si falla
    """
    if db_path is None:
        db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.error(f"La base de datos no existe en {db_path}. No se puede crear backup.")
        return None
    
    backup_dir = get_backup_directory()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if backup_name:
        backup_file = f"{backup_name}_{timestamp}.db"
    else:
        db_filename = os.path.basename(db_path)
        name_without_ext = os.path.splitext(db_filename)[0]
        backup_file = f"{name_without_ext}_backup_{timestamp}.db"
    
    backup_path = os.path.join(backup_dir, backup_file)
    
    try:
        # Conectar a la base de datos para asegurar que está cerrada antes de copiar
        conn = sqlite3.connect(db_path)
        # Crear un backup usando la API de SQLite
        backup_conn = sqlite3.connect(backup_path)
        
        conn.backup(backup_conn)
        
        # Cerrar conexiones
        backup_conn.close()
        conn.close()
        
        logger.info(f"Backup creado exitosamente en: {backup_path}")
        return backup_path
    
    except sqlite3.Error as e:
        logger.error(f"Error de SQLite al crear backup: {e}")
        # Intentar un enfoque alternativo: copia de archivo
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup creado mediante copia de archivo: {backup_path}")
            return backup_path
        except Exception as e2:
            logger.error(f"Error al copiar archivo para backup: {e2}")
            return None
    except Exception as e:
        logger.error(f"Error desconocido al crear backup: {e}")
        return None

def list_backups(pattern=None):
    """
    Lista todas las copias de seguridad disponibles
    
    Args:
        pattern (str, optional): Patrón para filtrar backups (por ejemplo, 'boletines_*')
        
    Returns:
        list: Lista de rutas a archivos de backup ordenados por fecha (más reciente primero)
    """
    backup_dir = get_backup_directory()
    
    if pattern:
        search_pattern = os.path.join(backup_dir, pattern)
    else:
        search_pattern = os.path.join(backup_dir, "*.db")
    
    # Obtener todas las rutas que coinciden con el patrón
    backup_files = glob.glob(search_pattern)
    
    # Ordenar por fecha de modificación (más reciente primero)
    backup_files.sort(key=os.path.getmtime, reverse=True)
    
    return backup_files

def restore_backup(backup_path, target_path=None):
    """
    Restaura una copia de seguridad a la ubicación de la base de datos
    
    Args:
        backup_path (str): Ruta al archivo de backup
        target_path (str, optional): Ruta destino. Si es None, se usa la ruta por defecto
        
    Returns:
        bool: True si la restauración fue exitosa, False en caso contrario
    """
    if not os.path.exists(backup_path):
        logger.error(f"El archivo de backup no existe: {backup_path}")
        return False
    
    if target_path is None:
        target_path = get_db_path()
    
    # Crear un backup de la base de datos actual antes de restaurar
    if os.path.exists(target_path):
        pre_restore_backup = create_backup(target_path, backup_name="pre_restore")
        if not pre_restore_backup:
            logger.warning("No se pudo crear backup de seguridad antes de restaurar")
    
    try:
        # Cerrar todas las conexiones a la DB actual
        # (Esto es un intento, pero puede que no funcione si hay otras conexiones activas)
        try:
            conn = sqlite3.connect(target_path)
            conn.close()
        except:
            pass
        
        # Copiar el backup a la ubicación destino
        shutil.copy2(backup_path, target_path)
        logger.info(f"Backup restaurado exitosamente desde {backup_path} a {target_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error al restaurar backup: {e}")
        return False

def verify_db_integrity(db_path=None):
    """
    Verifica la integridad de la base de datos
    
    Args:
        db_path (str, optional): Ruta a la base de datos. Si es None, se usa la ruta por defecto
        
    Returns:
        bool: True si la base de datos está íntegra, False si hay errores
    """
    if db_path is None:
        db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.error(f"La base de datos no existe en {db_path}")
        return False
    
    try:
        # Intentar usar la función de la aplicación principal
        try:
            from database import crear_conexion
            conn = crear_conexion()
            logger.info("Usando conexión de la aplicación principal para verificar integridad")
        except Exception as e:
            logger.warning(f"No se pudo usar crear_conexion(): {e}")
            conn = sqlite3.connect(db_path)
            
        cursor = conn.cursor()
        
        # Ejecutar la verificación de integridad de SQLite
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        # Verificar también la estructura de tablas principales
        try:
            # Verificar algunas tablas clave
            for tabla in ['boletines', 'Clientes', 'Marcas', 'emails_enviados']:
                cursor.execute(f"SELECT 1 FROM {tabla} LIMIT 1")
                cursor.fetchone()  # Consumir el resultado
            logger.info("Todas las tablas principales existen y son accesibles")
        except sqlite3.Error as e:
            logger.warning(f"Error al verificar tablas: {e}")
            # No fallamos aquí, pero lo registramos
        
        conn.close()
        
        if result and result[0] == "ok":
            logger.info("Verificación de integridad: OK")
            return True
        else:
            logger.error(f"Verificación de integridad falló: {result}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Error al verificar integridad: {e}")
        return False

def migrate_existing_db(source_db_path):
    """
    Migra una base de datos existente a la ubicación estándar del sistema
    
    Args:
        source_db_path (str): Ruta a la base de datos existente
        
    Returns:
        bool: True si la migración fue exitosa, False en caso contrario
    """
    if not os.path.exists(source_db_path):
        logger.error(f"La base de datos origen no existe: {source_db_path}")
        return False
    
    target_db_path = get_db_path()
    
    # Verificar si la fuente y el destino son el mismo archivo
    if os.path.abspath(source_db_path) == os.path.abspath(target_db_path):
        logger.info(f"La base de datos ya está en la ubicación correcta: {target_db_path}")
        return True
    
    # Si ya existe la DB en la ubicación estándar, hacer backup
    if os.path.exists(target_db_path):
        backup_path = create_backup(target_db_path, backup_name="pre_migration")
        if not backup_path:
            logger.error("No se pudo crear backup antes de migrar. Abortando migración.")
            return False
    
    try:
        # Copia la base de datos existente a la nueva ubicación
        shutil.copy2(source_db_path, target_db_path)
        logger.info(f"Base de datos migrada exitosamente de {source_db_path} a {target_db_path}")
        
        # Verificar integridad de la base de datos migrada
        if verify_db_integrity(target_db_path):
            logger.info("Verificación de integridad post-migración exitosa")
        else:
            logger.warning("La base de datos migrada tiene problemas de integridad")
        
        return True
    except Exception as e:
        logger.error(f"Error al migrar la base de datos: {e}")
        return False

# Ejemplo de uso
if __name__ == "__main__":
    # Mostrar la ubicación de la base de datos
    db_path = get_db_path()
    print(f"Ubicación de la base de datos: {db_path}")
    
    # Inicializar la base de datos
    conn = connect_db()
    conn.close()
    
    # Crear un backup
    backup_path = create_backup()
    if backup_path:
        print(f"Backup creado en: {backup_path}")
    
    # Listar backups disponibles
    backups = list_backups()
    print("Backups disponibles:")
    for backup in backups:
        modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(backup))
        print(f" - {os.path.basename(backup)} ({modified_time})")