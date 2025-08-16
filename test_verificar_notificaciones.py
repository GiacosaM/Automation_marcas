#!/usr/bin/env python3
# test_verificar_notificaciones.py

import os
import sys
import sqlite3
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Importar funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import crear_conexion
from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes

def simular_ejecucion_mensual():
    """
    Simula la ejecución mensual de la verificación de titulares sin reportes
    """
    print("=" * 80)
    print(f"EJECUTANDO VERIFICACIÓN DE TITULARES SIN REPORTES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Configurar archivo de credenciales para testing
    if not os.path.exists('credenciales.json'):
        try:
            if os.path.exists('test_credenciales.json'):
                os.rename('test_credenciales.json', 'credenciales.json')
                print("Archivo test_credenciales.json renombrado a credenciales.json para testing")
        except Exception as e:
            print(f"No se pudo configurar archivo de credenciales: {e}")
    
    # Crear conexión a la base de datos
    conn = crear_conexion()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        # Obtener información de la base de datos antes de ejecutar
        print("\nESTADO ACTUAL:")
        imprimir_estado_actual(conn)
        
        # Ejecutar la función de verificación
        print("\nEJECUTANDO VERIFICACIÓN...")
        verificar_titulares_sin_reportes(conn)
        
        # Verificar resultados
        print("\nESTADO DESPUÉS DE LA VERIFICACIÓN:")
        imprimir_estado_actual(conn)
        
        # Mostrar emails enviados
        print("\nEMAILS DE NOTIFICACIÓN ENVIADOS:")
        imprimir_emails_notificacion(conn)
        
    except Exception as e:
        print(f"ERROR DURANTE LA EJECUCIÓN: {e}")
    
    finally:
        if conn:
            conn.close()

def imprimir_estado_actual(conn):
    """Imprime información sobre el estado actual de la base de datos"""
    cursor = conn.cursor()
    
    # Total de clientes
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]
    print(f"Total de clientes en la base de datos: {total_clientes}")
    
    # Total de boletines del mes actual
    mes_actual = datetime.now().strftime('%Y-%m')
    cursor.execute(f"SELECT COUNT(*) FROM boletines WHERE fecha_boletin LIKE '{mes_actual}%'")
    boletines_mes_actual = cursor.fetchone()[0]
    print(f"Total de boletines del mes actual: {boletines_mes_actual}")
    
    # Clientes con boletines este mes
    cursor.execute(f"""
        SELECT COUNT(DISTINCT titular) 
        FROM boletines 
        WHERE fecha_boletin LIKE '{mes_actual}%'
    """)
    clientes_con_boletines = cursor.fetchone()[0]
    print(f"Clientes con boletines este mes: {clientes_con_boletines}")
    
    # Clientes sin boletines este mes
    clientes_sin_boletines = total_clientes - clientes_con_boletines
    print(f"Clientes sin boletines este mes: {clientes_sin_boletines}")
    
    cursor.close()

def imprimir_emails_notificacion(conn):
    """Imprime los emails de notificación enviados"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT destinatario, asunto, fecha_envio, status
            FROM emails_enviados
            WHERE tipo_email = 'notificacion'
            ORDER BY fecha_envio DESC
        """)
        
        emails = cursor.fetchall()
        
        if emails:
            print(f"Se encontraron {len(emails)} emails de notificación:")
            
            for i, (destinatario, asunto, fecha_envio, status) in enumerate(emails, 1):
                print(f"\n{i}. Email a: {destinatario}")
                print(f"   Asunto: {asunto}")
                print(f"   Fecha: {fecha_envio}")
                print(f"   Estado: {status}")
                print("-" * 50)
        else:
            print("No se encontraron emails de notificación enviados.")
    
    except sqlite3.Error as e:
        print(f"Error al consultar emails: {e}")
    
    finally:
        cursor.close()

if __name__ == "__main__":
    simular_ejecucion_mensual()
    print("\nTest completado.")
