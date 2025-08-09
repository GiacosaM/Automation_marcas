#!/usr/bin/env python3
"""
Script para probar la funcionalidad de alertas de vencimiento.
Simula algunos registros con fechas que están próximas a vencer.
"""

import sqlite3
from datetime import datetime, timedelta

def crear_datos_prueba_vencimiento():
    """Crear algunos registros de prueba que estén próximos a vencer."""
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    # Obtener fecha actual
    hoy = datetime.now()
    
    # Crear fechas de prueba en formato DD/MM/YYYY
    # Algunos próximos a vencer (25-28 días atrás)
    fecha_proximo_1 = (hoy - timedelta(days=25)).strftime('%d/%m/%Y')
    fecha_proximo_2 = (hoy - timedelta(days=27)).strftime('%d/%m/%Y')
    
    # Algunos vencidos (más de 30 días atrás)
    fecha_vencido_1 = (hoy - timedelta(days=35)).strftime('%d/%m/%Y')
    fecha_vencido_2 = (hoy - timedelta(days=40)).strftime('%d/%m/%Y')
    
    print(f"📅 Fecha actual: {hoy.strftime('%d/%m/%Y')}")
    print(f"⏰ Fechas próximas a vencer: {fecha_proximo_1}, {fecha_proximo_2}")
    print(f"🚨 Fechas vencidas: {fecha_vencido_1}, {fecha_vencido_2}")
    print()
    
    # Datos de prueba
    registros_prueba = [
        # Próximos a vencer
        ('BOL-TEST-001', fecha_proximo_1, '99001', 'Empresa Test A', 'Agente Test', 'EXP-TEST-001', '35', 'Marca Test A', 'Marca Test A Publicada', '35', 0, 'EMPRESA TEST A S.A.', 0, 'Alta'),
        ('BOL-TEST-002', fecha_proximo_2, '99002', 'Empresa Test B', 'Agente Test', 'EXP-TEST-002', '42', 'Marca Test B', 'Marca Test B Publicada', '42', 0, 'EMPRESA TEST B LTDA.', 0, 'Media'),
        
        # Vencidos
        ('BOL-TEST-003', fecha_vencido_1, '99003', 'Empresa Test C', 'Agente Test', 'EXP-TEST-003', '25', 'Marca Test C', 'Marca Test C Publicada', '25', 0, 'EMPRESA TEST C S.R.L.', 0, 'Alta'),
        ('BOL-TEST-004', fecha_vencido_2, '99004', 'Empresa Test D', 'Agente Test', 'EXP-TEST-004', '12', 'Marca Test D', 'Marca Test D Publicada', '12', 0, 'EMPRESA TEST D S.A.', 0, 'Pendiente'),
    ]
    
    # Verificar si ya existen registros de prueba
    cursor.execute("SELECT COUNT(*) FROM boletines WHERE numero_boletin LIKE 'BOL-TEST-%'")
    existentes = cursor.fetchone()[0]
    
    if existentes > 0:
        print(f"⚠️ Ya existen {existentes} registros de prueba. Eliminándolos primero...")
        cursor.execute("DELETE FROM boletines WHERE numero_boletin LIKE 'BOL-TEST-%'")
    
    # Insertar nuevos registros de prueba
    for registro in registros_prueba:
        cursor.execute('''
            INSERT INTO boletines (
                numero_boletin, fecha_boletin, numero_orden, solicitante, agente, 
                numero_expediente, clase, marca_custodia, marca_publicada, clases_acta,
                reporte_enviado, titular, reporte_generado, importancia
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', registro)
    
    conn.commit()
    
    print(f"✅ Se insertaron {len(registros_prueba)} registros de prueba")
    print()
    
    # Verificar que las consultas funcionen
    print("🧪 Verificando las consultas de vencimiento:")
    
    # Consulta para próximos a vencer
    cursor.execute("""
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_enviado = 0 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND date(substr(fecha_boletin, 7, 4) || '-' || 
                 substr(fecha_boletin, 4, 2) || '-' || 
                 substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
        AND date(substr(fecha_boletin, 7, 4) || '-' || 
                 substr(fecha_boletin, 4, 2) || '-' || 
                 substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
    """)
    proximos = cursor.fetchone()[0]
    
    # Consulta para vencidos
    cursor.execute("""
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_enviado = 0 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND date(substr(fecha_boletin, 7, 4) || '-' || 
                 substr(fecha_boletin, 4, 2) || '-' || 
                 substr(fecha_boletin, 1, 2), '+30 days') < date('now')
    """)
    vencidos = cursor.fetchone()[0]
    
    print(f"⏰ Reportes próximos a vencer: {proximos}")
    print(f"🚨 Reportes vencidos: {vencidos}")
    
    # Mostrar detalles de los próximos a vencer
    if proximos > 0:
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) - 
                        julianday(date('now')) AS INTEGER) as dias_restantes
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+23 days') <= date('now')
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
            ORDER BY dias_restantes ASC
        """)
        detalles = cursor.fetchall()
        
        print("\n📋 Detalles de reportes próximos a vencer:")
        for detalle in detalles:
            print(f"  - {detalle[0]} | {detalle[1]} | {detalle[2]} | {detalle[3]} días restantes")
    
    # Mostrar detalles de los vencidos
    if vencidos > 0:
        cursor.execute("""
            SELECT numero_boletin, titular, fecha_boletin,
                   CAST(julianday(date('now')) - 
                        julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                      substr(fecha_boletin, 4, 2) || '-' || 
                                      substr(fecha_boletin, 1, 2), '+30 days')) AS INTEGER) as dias_vencido
            FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') < date('now')
            ORDER BY dias_vencido DESC
        """)
        detalles = cursor.fetchall()
        
        print("\n🚨 Detalles de reportes vencidos:")
        for detalle in detalles:
            print(f"  - {detalle[0]} | {detalle[1]} | {detalle[2]} | {detalle[3]} días vencido")
    
    conn.close()
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("Ahora puedes ejecutar: streamlit run app.py")
    print("Ve al Dashboard para ver las nuevas alertas de vencimiento en acción.")

def limpiar_datos_prueba():
    """Eliminar los datos de prueba."""
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM boletines WHERE numero_boletin LIKE 'BOL-TEST-%'")
    existentes = cursor.fetchone()[0]
    
    if existentes > 0:
        cursor.execute("DELETE FROM boletines WHERE numero_boletin LIKE 'BOL-TEST-%'")
        conn.commit()
        print(f"🗑️ Se eliminaron {existentes} registros de prueba")
    else:
        print("ℹ️ No hay registros de prueba para eliminar")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'limpiar':
        limpiar_datos_prueba()
    else:
        crear_datos_prueba_vencimiento()
