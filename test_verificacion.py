#!/usr/bin/env python3
# test_verificacion.py

"""
Script para probar las modificaciones al sistema de verificación de titulares sin reportes
y asegurar que los mensajes de feedback funcionan correctamente.
"""

import sqlite3
import logging
from datetime import datetime
import calendar
from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes
from database import crear_conexion

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_verificacion')

def simular_escenario(nombre_escenario, funcion_setup):
    """
    Ejecuta una simulación de escenario para probar la verificación
    
    Args:
        nombre_escenario: Nombre descriptivo del escenario
        funcion_setup: Función que configura el escenario en la BD
    """
    logger.info(f"=== INICIANDO ESCENARIO: {nombre_escenario} ===")
    
    # Crear conexión a la base de datos
    conn = crear_conexion()
    
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        return
    
    try:
        # Preparar el escenario
        funcion_setup(conn)
        
        # Ejecutar verificación
        resultado = verificar_titulares_sin_reportes(conn)
        
        # Mostrar resultados
        logger.info(f"Resultado del escenario '{nombre_escenario}':")
        for key, value in resultado.items():
            logger.info(f"  {key}: {value}")
        
        # Generar mensaje que se mostraría en la interfaz
        titulares_sin_reportes = resultado.get("titulares_sin_reportes", 0)
        emails_enviados = resultado.get("emails_enviados", 0)
        ya_notificados = resultado.get("ya_notificados", 0)
        
        if titulares_sin_reportes == 0:
            mensaje = "✅ Verificación completada: Todos los titulares tienen reportes generados este mes."
        elif emails_enviados == 0 and ya_notificados > 0:
            mensaje = f"ℹ️ Verificación completada: {titulares_sin_reportes} titulares sin reportes, pero todos ya habían sido notificados previamente."
        else:
            mensaje = f"✅ Verificación completada: {emails_enviados} notificaciones enviadas a titulares sin reportes."
            
        logger.info(f"Mensaje de interfaz: {mensaje}")
        
    except Exception as e:
        logger.error(f"Error durante la simulación: {e}")
    finally:
        conn.close()
        logger.info(f"=== FIN DE ESCENARIO: {nombre_escenario} ===\n")

def configurar_escenario_todos_con_reportes(conn):
    """Configura el escenario donde todos los titulares tienen reportes"""
    cursor = conn.cursor()
    
    # Obtener mes y año actual
    fecha_actual = datetime.now()
    mes_actual = fecha_actual.month
    anio_actual = fecha_actual.year
    
    # Asegurar que cada titular tenga al menos un reporte en el mes actual
    cursor.execute("SELECT titular FROM clientes")
    titulares = [row[0] for row in cursor.fetchall()]
    
    for titular in titulares:
        # Verificar si ya tiene reportes este mes
        primer_dia = f"{anio_actual}-{mes_actual:02d}-01"
        ultimo_dia = f"{anio_actual}-{mes_actual:02d}-{calendar.monthrange(anio_actual, mes_actual)[1]:02d}"
        
        cursor.execute("""
            SELECT COUNT(*) FROM boletines 
            WHERE titular = ? 
            AND reporte_generado = 1
            AND fecha_alta BETWEEN ? AND ?
        """, (titular, primer_dia, ultimo_dia))
        
        tiene_reportes = cursor.fetchone()[0] > 0
        
        # Si no tiene reportes, crear uno ficticio para este test
        if not tiene_reportes:
            logger.info(f"Agregando reporte ficticio para {titular}")
            cursor.execute("""
                INSERT INTO boletines (titular, importancia, fecha_alta, reporte_generado)
                VALUES (?, 'Media', ?, 1)
            """, (titular, primer_dia))
    
    conn.commit()
    logger.info("Escenario configurado: todos los titulares tienen reportes")

def configurar_escenario_algunos_sin_reportes_sin_notificaciones(conn):
    """Configura el escenario donde algunos titulares no tienen reportes y no han sido notificados"""
    cursor = conn.cursor()
    
    # Obtener mes y año actual
    fecha_actual = datetime.now()
    mes_actual = fecha_actual.month
    anio_actual = fecha_actual.year
    
    # Limpiar cualquier notificación previa para este mes
    periodo_actual = f"{mes_actual:02d}-{anio_actual}"
    cursor.execute("DELETE FROM emails_enviados WHERE periodo_notificacion = ?", (periodo_actual,))
    
    # Seleccionar algunos titulares para quitarles los reportes
    cursor.execute("SELECT titular FROM clientes LIMIT 2")
    titulares_sin_reportes = [row[0] for row in cursor.fetchall()]
    
    for titular in titulares_sin_reportes:
        # Eliminar reportes de este mes
        primer_dia = f"{anio_actual}-{mes_actual:02d}-01"
        ultimo_dia = f"{anio_actual}-{mes_actual:02d}-{calendar.monthrange(anio_actual, mes_actual)[1]:02d}"
        
        cursor.execute("""
            DELETE FROM boletines 
            WHERE titular = ? 
            AND fecha_alta BETWEEN ? AND ?
        """, (titular, primer_dia, ultimo_dia))
    
    conn.commit()
    logger.info(f"Escenario configurado: {len(titulares_sin_reportes)} titulares sin reportes y sin notificaciones previas")

def configurar_escenario_algunos_sin_reportes_ya_notificados(conn):
    """Configura el escenario donde algunos titulares no tienen reportes pero ya han sido notificados"""
    cursor = conn.cursor()
    
    # Obtener mes y año actual
    fecha_actual = datetime.now()
    mes_actual = fecha_actual.month
    anio_actual = fecha_actual.year
    periodo_actual = f"{mes_actual:02d}-{anio_actual}"
    
    # Seleccionar algunos titulares para quitarles los reportes
    cursor.execute("SELECT titular, email FROM clientes LIMIT 2")
    titulares_sin_reportes = cursor.fetchall()
    
    for titular, email in titulares_sin_reportes:
        # Eliminar reportes de este mes
        primer_dia = f"{anio_actual}-{mes_actual:02d}-01"
        ultimo_dia = f"{anio_actual}-{mes_actual:02d}-{calendar.monthrange(anio_actual, mes_actual)[1]:02d}"
        
        cursor.execute("""
            DELETE FROM boletines 
            WHERE titular = ? 
            AND fecha_alta BETWEEN ? AND ?
        """, (titular, primer_dia, ultimo_dia))
        
        # Agregar registro de notificación previa
        cursor.execute("""
            INSERT INTO emails_enviados 
            (destinatario, asunto, mensaje, fecha_envio, status, tipo_email, titular, periodo_notificacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, f"Sin reportes generados para {mes_actual}/{anio_actual}", 
              f"Notificación previa para test", datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "enviado", "notificacion", titular, periodo_actual))
    
    conn.commit()
    logger.info(f"Escenario configurado: {len(titulares_sin_reportes)} titulares sin reportes pero ya notificados")

if __name__ == "__main__":
    logger.info("Iniciando pruebas de verificación de titulares sin reportes")
    
    # Ejecutar los diferentes escenarios de prueba
    simular_escenario("Todos los titulares tienen reportes", 
                     configurar_escenario_todos_con_reportes)
    
    simular_escenario("Algunos titulares sin reportes (sin notificaciones previas)", 
                     configurar_escenario_algunos_sin_reportes_sin_notificaciones)
    
    simular_escenario("Algunos titulares sin reportes (ya notificados)", 
                     configurar_escenario_algunos_sin_reportes_ya_notificados)
    
    logger.info("Pruebas completadas")
