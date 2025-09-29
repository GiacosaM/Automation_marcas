#!/usr/bin/env python3
"""
Script de prueba para el generador de reportes mejorado
Genera un reporte de muestra para verificar el nuevo diseño profesional
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from report_generator import ReportGenerator
from paths import get_db_path, get_image_path, get_informes_dir

def create_test_data():
    """Crea datos de prueba en la base de datos"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Datos de muestra
    test_records = [
        (
            'EMPRESA DEMO S.A.',  # titular
            '12345',  # numero_boletin
            '2025-09-01',  # fecha_boletin
            '001',  # numero_orden
            'SOLICITANTE DEMO',  # solicitante
            'AGENTE DEMO',  # agente
            'EXP-2025-001',  # numero_expediente
            '35',  # clase
            'MARCA DEMO 1',  # marca_custodia
            'MARCA DEMO 1',  # marca_publicada
            'Clase 35: Servicios',  # clases_acta
            'Alta',  # importancia
            0,  # reporte_generado
            0   # reporte_enviado
        ),
        (
            'EMPRESA DEMO S.A.',
            '12346',
            '2025-09-02',
            '002',
            'SOLICITANTE DEMO 2',
            'AGENTE DEMO 2',
            'EXP-2025-002',
            '42',
            'MARCA DEMO 2',
            'MARCA DEMO 2',
            'Clase 42: Tecnología',
            'Alta',
            0,
            0
        ),
        (
            'EMPRESA DEMO S.A.',
            '12347',
            '2025-09-03',
            '003',
            'SOLICITANTE DEMO 3',
            'AGENTE DEMO 3',
            'EXP-2025-003',
            '25',
            'MARCA DEMO 3',
            'MARCA DEMO 3',
            'Clase 25: Vestimenta',
            'Alta',
            0,
            0
        )
    ]
    
    # Limpiar registros de prueba existentes
    cursor.execute("DELETE FROM boletines WHERE titular = 'EMPRESA DEMO S.A.'")
    
    # Insertar registros de prueba
    cursor.executemany('''
        INSERT INTO boletines (
            titular, numero_boletin, fecha_boletin, numero_orden, 
            solicitante, agente, numero_expediente, clase, 
            marca_custodia, marca_publicada, clases_acta, 
            importancia, reporte_generado, reporte_enviado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_records)
    
    conn.commit()
    print(f"✅ Se insertaron {len(test_records)} registros de prueba")
    return conn

def test_report_generation():
    """Prueba la generación de reportes con el nuevo diseño"""
    print("🚀 Iniciando prueba del generador de reportes mejorado...")
    
    try:
        # Crear datos de prueba
        conn = create_test_data()
        
        # Crear generador de reportes
        generator = ReportGenerator(
            watermark_path=get_image_path("marca_agua.jpg")
            # output_dir será automáticamente get_informes_dir()
        )
        
        # Generar reportes
        print("📄 Generando reportes...")
        result = generator.generate_reports(conn)
        
        # Mostrar resultados
        if result['success']:
            print(f"✅ Generación exitosa!")
            print(f"   📊 Reportes generados: {result['reportes_generados']}")
            print(f"   📋 Registros procesados: {result.get('registros_procesados', 0)}")
            print(f"   📁 Ubicación: {generator.output_dir}/")
            
            # Listar archivos generados
            if os.path.exists(generator.output_dir):
                archivos = [f for f in os.listdir(generator.output_dir) 
                           if f.endswith('.pdf') and 'EMPRESA DEMO' in f]
                if archivos:
                    print(f"   📄 Archivos generados:")
                    for archivo in archivos[-3:]:  # Mostrar últimos 3
                        print(f"      • {archivo}")
        else:
            print(f"❌ Error en la generación: {result.get('message', 'Error desconocido')}")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error durante la prueba: {e}")
        return False
    
    return True

def cleanup_test_data():
    """Limpia los datos de prueba"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("DELETE FROM boletines WHERE titular = 'EMPRESA DEMO S.A.'")
        conn.commit()
        conn.close()
        print("🧹 Datos de prueba eliminados")
    except Exception as e:
        print(f"⚠️  Error al limpiar datos de prueba: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🎨 PRUEBA DEL GENERADOR DE REPORTES PROFESIONAL")
    print("=" * 60)
    
    # Ejecutar prueba
    success = test_report_generation()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("💡 Revisa los archivos PDF generados en la carpeta 'informes'")
        print("🎨 El nuevo diseño incluye:")
        print("   • Encabezado profesional con logo y fecha")
        print("   • Títulos en azul con tipografía elegante")
        print("   • Tabla con estilo zebra y bordes finos")
        print("   • Pie de página con texto confidencial")
        print("   • Márgenes amplios y mejor distribución")
        
        # Preguntar si quiere limpiar datos de prueba
        print("\n¿Deseas eliminar los datos de prueba? (y/n): ", end="")
        if input().lower().strip() in ['y', 'yes', 'sí', 's']:
            cleanup_test_data()
    else:
        print("\n" + "=" * 60)
        print("❌ LA PRUEBA FALLÓ")
        print("=" * 60)
        print("🔍 Revisa los logs para más detalles del error")
