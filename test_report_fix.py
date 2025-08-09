#!/usr/bin/env python3
"""
Script de prueba para verificar los cambios en el generador de informes
"""

import sys
import os
from database import crear_conexion, crear_tabla

def mock_generar_informe_pdf(conn, watermark_image: str = "imagenes/marca_agua.jpg"):
    """
    Versión mock del generador de informes para probar la lógica sin dependencias
    """
    # Simular la lógica que implementamos
    cursor = conn.cursor()
    
    # Obtener registros pendientes (NO con importancia 'Pendiente')
    cursor.execute('''
        SELECT titular, numero_boletin, fecha_boletin, numero_orden, solicitante, 
               agente, numero_expediente, clase, marca_custodia, marca_publicada, 
               clases_acta, importancia 
        FROM boletines 
        WHERE reporte_generado = 0 AND importancia != 'Pendiente'
    ''')
    registros = cursor.fetchall()
    
    # Verificar si hay registros con importancia 'Pendiente'
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 0 AND importancia = 'Pendiente'
    ''')
    pendientes = cursor.fetchone()[0]
    
    # Obtener total de registros sin procesar
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 0
    ''')
    total_sin_procesar = cursor.fetchone()[0]
    
    print(f"📋 ESTADO DE REGISTROS:")
    print(f"   • Total registros sin procesar: {total_sin_procesar}")
    print(f"   • Registros con estado 'Pendiente' (no se procesarán): {pendientes}")
    print(f"   • Registros listos para procesar: {len(registros)}")
    
    if not registros:
        if pendientes > 0:
            print("❌ No hay registros listos para generar informes")
            print("💡 Sugerencia: Cambia la importancia de los registros 'Pendiente' para procesarlos")
            return {
                'success': False,
                'message': 'pending_only',
                'total_sin_procesar': total_sin_procesar,
                'pendientes': pendientes,
                'reportes_generados': 0
            }
        else:
            print("✅ No hay registros pendientes para generar informes")
            return {
                'success': True,
                'message': 'no_pending',
                'total_sin_procesar': 0,
                'pendientes': 0,
                'reportes_generados': 0
            }
    
    # Si hay registros para procesar, simular generación exitosa
    reportes_generados = len(set(r[0] for r in registros))  # Contar titulares únicos
    
    return {
        'success': True,
        'message': 'completed',
        'reportes_generados': reportes_generados,
        'total_titulares': reportes_generados,
        'registros_procesados': len(registros),
        'pendientes': pendientes,
        'errores': 0
    }

def test_scenarios():
    """Probar diferentes escenarios"""
    conn = crear_conexion()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        crear_tabla(conn)
        
        print("🧪 PROBANDO ESCENARIO ACTUAL")
        resultado = mock_generar_informe_pdf(conn)
        print(f"\n📊 RESULTADO:")
        print(f"   • Success: {resultado['success']}")
        print(f"   • Message: {resultado['message']}")
        print(f"   • Reportes generados: {resultado['reportes_generados']}")
        print(f"   • Pendientes: {resultado.get('pendientes', 0)}")
        
        # Simular mensaje que vería el usuario
        print(f"\n💬 MENSAJE PARA EL USUARIO:")
        if resultado['success']:
            if resultado['message'] == 'no_pending':
                print("✅ No hay informes pendientes de generación")
            elif resultado['message'] == 'completed':
                if resultado['reportes_generados'] > 0:
                    print(f"✅ Se generaron {resultado['reportes_generados']} informes correctamente")
                    if resultado.get('pendientes', 0) > 0:
                        print(f"ℹ️ {resultado['pendientes']} registros permanecen como 'Pendiente' y no fueron procesados")
                else:
                    print("⚠️ No se pudo generar ningún informe")
        else:
            if resultado['message'] == 'pending_only':
                print(f"⚠️ No se generaron informes. Los {resultado['pendientes']} registros están marcados como 'Pendiente'")
                print("💡 Cambia la importancia de los registros en la sección 'Historial' para poder procesarlos")
            else:
                print("❌ No se pudieron generar los informes")
    
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_scenarios()
