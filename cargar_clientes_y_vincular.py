#!/usr/bin/env python3
"""
Script para cargar clientes desde un archivo externo (Excel/CSV) y vincularlos con marcas
basándose en el CUIT. Este script se ejecuta una sola vez para importar datos.

Uso:
    python cargar_clientes_y_vincular.py <ruta_archivo> [--formato=excel|csv] [--hoja=nombre_hoja]

Ejemplo:
    python cargar_clientes_y_vincular.py ./Documentos/clientes.xlsx --formato=excel --hoja=Clientes
    python cargar_clientes_y_vincular.py ./Documentos/clientes.csv --formato=csv
"""

import os
import sys
import argparse
import logging
import sqlite3
import pandas as pd
import time
from datetime import datetime
from paths import get_db_path, get_logs_dir

# Configurar logging
log_file = os.path.join(get_logs_dir(), "carga_clientes.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('carga_clientes')

def crear_conexion():
    """Crear conexión a la base de datos SQLite"""
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

def limpiar_cuit(cuit):
    """Limpia el CUIT eliminando guiones y espacios"""
    if pd.isna(cuit) or cuit is None:
        return ""
    return str(cuit).replace('-', '').replace(' ', '').strip()

def cargar_archivo(ruta_archivo, formato="excel", nombre_hoja=None):
    """Cargar datos desde un archivo CSV o Excel"""
    try:
        if formato.lower() == "excel":
            if nombre_hoja:
                df = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja)
            else:
                df = pd.read_excel(ruta_archivo)
        elif formato.lower() == "csv":
            df = pd.read_csv(ruta_archivo)
        else:
            logger.error(f"Formato no soportado: {formato}")
            return None

        logger.info(f"Archivo cargado con éxito: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Error al cargar archivo {ruta_archivo}: {e}")
        return None

def validar_datos(df):
    """Validar que el dataframe tenga las columnas mínimas necesarias"""
    columnas_requeridas = ['titular', 'cuit']
    columnas_opcionales = ['email', 'telefono', 'direccion', 'ciudad', 'provincia']
    
    # Convertir nombres de columnas a minúsculas para comparación
    df.columns = [col.lower() for col in df.columns]
    
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        logger.error(f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}")
        return False
        
    # Añadir columnas opcionales faltantes con valores vacíos
    for col in columnas_opcionales:
        if col not in df.columns:
            df[col] = ""
            logger.warning(f"Columna opcional {col} no encontrada. Se usarán valores vacíos.")
    
    # Eliminar filas con titular o CUIT vacío
    df_original = df.copy()
    df.dropna(subset=['titular', 'cuit'], inplace=True)
    
    # Verificar si se eliminaron filas
    filas_eliminadas = len(df_original) - len(df)
    if filas_eliminadas > 0:
        logger.warning(f"Se eliminaron {filas_eliminadas} filas con titular o CUIT vacío")
    
    # Limpiar CUITs
    df['cuit'] = df['cuit'].apply(limpiar_cuit)
    
    # Filtrar CUITs inválidos (deben tener 11 dígitos)
    df_validos = df[df['cuit'].str.len() == 11]
    cuits_invalidos = len(df) - len(df_validos)
    
    if cuits_invalidos > 0:
        logger.warning(f"Se encontraron {cuits_invalidos} CUITs con formato inválido")
        df = df_validos
    
    logger.info(f"Datos validados: {len(df)} registros válidos para procesar")
    return df

def insertar_cliente(conn, cliente):
    """Inserta un cliente en la base de datos y vincula con marcas si corresponde"""
    try:
        cursor = conn.cursor()
        
        # Verificar si ya existe un cliente con el mismo titular
        cursor.execute('SELECT COUNT(*) FROM clientes WHERE titular = ?', (cliente['titular'],))
        if cursor.fetchone()[0] > 0:
            logger.info(f"Cliente omitido (ya existe): Titular {cliente['titular']}")
            return None
            
        # Verificar si ya existe un cliente con el mismo CUIT
        cursor.execute('SELECT COUNT(*) FROM clientes WHERE cuit = ?', (cliente['cuit'],))
        if cursor.fetchone()[0] > 0:
            logger.warning(f"Cliente omitido (CUIT duplicado): {cliente['cuit']} - {cliente['titular']}")
            return None
        
        # Nombre del titular para insertar (puede ser actualizado si se encuentra en la tabla Marcas)
        nombre_titular_final = cliente['titular']
        
        # Si hay un CUIT, verificar si existe en la tabla Marcas y comparar el nombre del titular
        if cliente['cuit']:
            cursor.execute('SELECT titular FROM Marcas WHERE cuit = ? LIMIT 1', (cliente['cuit'],))
            resultado_marca = cursor.fetchone()
            
            if resultado_marca and resultado_marca[0]:
                titular_en_marcas = resultado_marca[0]
                
                # Si los nombres no coinciden, usar el de la tabla Marcas
                if titular_en_marcas.strip() != cliente['titular'].strip():
                    logger.info(f"Actualizando nombre del cliente de '{cliente['titular']}' a '{titular_en_marcas}' según tabla Marcas")
                    nombre_titular_final = titular_en_marcas
        
        # Insertar el cliente con el nombre correcto
        cursor.execute('''
            INSERT INTO clientes (titular, email, telefono, direccion, ciudad, provincia, fecha_alta, cuit)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
        ''', (
            nombre_titular_final,
            cliente.get('email', ''), 
            cliente.get('telefono', ''), 
            cliente.get('direccion', ''), 
            cliente.get('ciudad', ''), 
            cliente.get('provincia', ''), 
            cliente['cuit']
        ))
        
        conn.commit()
        
        # Obtener el ID del cliente recién insertado
        cursor.execute("SELECT last_insert_rowid()")
        cliente_id = cursor.fetchone()[0]
        
        logger.info(f"Cliente insertado: ID {cliente_id}, Titular {nombre_titular_final}")
        
        # Vincular marcas existentes con este CUIT
        if cliente['cuit']:
            marcas_vinculadas = vincular_marcas_con_cliente(conn, cliente_id, cliente['cuit'])
            if marcas_vinculadas > 0:
                logger.info(f"Se vincularon {marcas_vinculadas} marcas al cliente '{nombre_titular_final}' con CUIT {cliente['cuit']}")
            
        return cliente_id
        
    except sqlite3.Error as e:
        logger.error(f"Error al insertar cliente {cliente['titular']}: {e}")
        conn.rollback()
        return None

def vincular_marcas_con_cliente(conn, cliente_id, cuit):
    """Vincula marcas con un cliente según el CUIT"""
    try:
        if not cuit or not cliente_id:
            return 0
            
        cursor = conn.cursor()
        
        # Limpiar y estandarizar el CUIT
        cuit_clean = limpiar_cuit(cuit)
        
        # Verificar que el cliente existe
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE id = ?", (cliente_id,))
        if cursor.fetchone()[0] == 0:
            logger.warning(f"No se puede vincular marcas: Cliente con ID {cliente_id} no existe")
            return 0
        
        # Obtener el nombre del titular para el log
        cursor.execute("SELECT titular FROM clientes WHERE id = ?", (cliente_id,))
        titular_result = cursor.fetchone()
        titular = titular_result[0] if titular_result else "Desconocido"
        
        # Ejecutar vinculación por CUIT
        cursor.execute("SELECT id, marca, cuit FROM Marcas WHERE cliente_id IS NULL")
        
        marcas_sin_asignar = cursor.fetchall()
        marcas_vinculadas = 0
        
        for marca in marcas_sin_asignar:
            marca_id = marca[0]
            marca_nombre = marca[1]
            marca_cuit = marca[2]
            
            if marca_cuit:
                # Limpiar el CUIT de la marca para comparación estricta
                marca_cuit_clean = limpiar_cuit(marca_cuit)
                
                # Comparar CUITs limpios
                if marca_cuit_clean == cuit_clean:
                    # Vincular la marca al cliente
                    cursor.execute("""
                        UPDATE Marcas SET cliente_id = ? WHERE id = ?
                    """, (cliente_id, marca_id))
                    
                    logger.info(f"✅ Vinculada marca ID {marca_id} '{marca_nombre}' con CUIT {marca_cuit} al cliente {cliente_id}")
                    marcas_vinculadas += 1
        
        conn.commit()
        
        # Verificar vinculaciones
        cursor.execute("SELECT COUNT(*) FROM Marcas WHERE cliente_id = ?", (cliente_id,))
        total_vinculadas = cursor.fetchone()[0]
        
        if total_vinculadas != marcas_vinculadas:
            logger.info(f"Total de marcas vinculadas al cliente {cliente_id}: {total_vinculadas} (nuevas: {marcas_vinculadas})")
        
        return marcas_vinculadas
            
    except sqlite3.Error as e:
        logger.error(f"Error al vincular marcas con cliente: {e}")
        conn.rollback()
        return 0

def procesar_clientes(conn, df):
    """Procesa cada cliente del dataframe y lo inserta en la base de datos"""
    start_time = time.time()
    total = len(df)
    insertados = 0
    omitidos = 0
    
    logger.info(f"Iniciando procesamiento de {total} clientes")
    
    # Crear tablas si no existen
    verificar_tablas(conn)
    
    # Procesar cada cliente
    for index, row in df.iterrows():
        # Convertir fila a diccionario
        cliente = row.to_dict()
        
        # Insertar cliente
        try:
            resultado = insertar_cliente(conn, cliente)
            if resultado:
                insertados += 1
            else:
                omitidos += 1
        except Exception as e:
            logger.error(f"Error procesando cliente {cliente.get('titular', 'desconocido')}: {e}")
            omitidos += 1
        
        # Mostrar progreso cada 10 registros
        if (index + 1) % 10 == 0 or index == total - 1:
            porcentaje = ((index + 1) / total) * 100
            tiempo_transcurrido = time.time() - start_time
            logger.info(f"Progreso: {index + 1}/{total} ({porcentaje:.1f}%) - Tiempo: {tiempo_transcurrido:.1f}s")
    
    tiempo_total = time.time() - start_time
    logger.info(f"Procesamiento finalizado en {tiempo_total:.1f} segundos")
    logger.info(f"Resumen: {insertados} clientes insertados, {omitidos} omitidos, {total} total")
    
    return insertados, omitidos

def verificar_tablas(conn):
    """Verifica que las tablas necesarias existan en la base de datos"""
    try:
        cursor = conn.cursor()
        
        # Verificar tabla clientes
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'
        """)
        
        if not cursor.fetchone():
            logger.warning("La tabla 'clientes' no existe. Creando tabla...")
            cursor.execute("""
                CREATE TABLE clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titular TEXT NOT NULL,
                    email TEXT,
                    telefono TEXT,
                    direccion TEXT,
                    ciudad TEXT,
                    provincia TEXT,
                    cuit TEXT,
                    fecha_alta TEXT,
                    fecha_modificacion TEXT
                )
            """)
            conn.commit()
            logger.info("Tabla 'clientes' creada correctamente")
        
        # Verificar tabla Marcas
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='Marcas'
        """)
        
        if not cursor.fetchone():
            logger.warning("La tabla 'Marcas' no existe. El script no podrá vincular marcas.")
    
    except sqlite3.Error as e:
        logger.error(f"Error al verificar tablas: {e}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Cargar clientes desde un archivo y vincularlos con marcas.')
    parser.add_argument('archivo', help='Ruta al archivo de clientes (Excel o CSV)')
    parser.add_argument('--formato', default='excel', choices=['excel', 'csv'], 
                        help='Formato del archivo (excel o csv)')
    parser.add_argument('--hoja', default=None, help='Nombre de la hoja en caso de Excel')
    
    args = parser.parse_args()
    
    # Verificar existencia del archivo
    if not os.path.exists(args.archivo):
        logger.error(f"El archivo {args.archivo} no existe")
        sys.exit(1)
    
    # Crear conexión a la base de datos
    conn = crear_conexion()
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        # Cargar datos del archivo
        df = cargar_archivo(args.archivo, args.formato, args.hoja)
        if df is None:
            logger.error("No se pudieron cargar los datos del archivo")
            sys.exit(1)
        
        # Validar datos
        df_validado = validar_datos(df)
        if not isinstance(df_validado, pd.DataFrame):
            logger.error("Los datos no pasaron la validación")
            sys.exit(1)
        
        # Procesar clientes
        insertados, omitidos = procesar_clientes(conn, df_validado)
        
        logger.info(f"\n{'='*50}\nRESUMEN FINAL\n{'='*50}")
        logger.info(f"Archivo procesado: {args.archivo}")
        logger.info(f"Total de registros en el archivo: {len(df)}")
        logger.info(f"Registros válidos: {len(df_validado)}")
        logger.info(f"Clientes insertados: {insertados}")
        logger.info(f"Clientes omitidos: {omitidos}")
        logger.info(f"{'='*50}")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()