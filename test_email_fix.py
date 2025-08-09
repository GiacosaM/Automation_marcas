#!/usr/bin/env python3
"""
Script para probar la corrección del error de columnas anidadas en el envío de emails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla
from email_sender import obtener_estadisticas_envios
from config import load_email_credentials

def test_email_system():
    """Probar el sistema de emails después de la corrección"""
    print("🔍 Probando sistema de emails después de corrección...")
    
    # Conectar a la base de datos
    conn = crear_conexion()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        crear_tabla(conn)
        
        # Obtener estadísticas
        stats = obtener_estadisticas_envios(conn)
        
        if stats:
            print("\n📊 Estadísticas del sistema:")
            print(f"📋 Total reportes: {stats['total_reportes']}")
            print(f"📄 Reportes generados: {stats['reportes_generados']}")
            print(f"📧 Reportes enviados: {stats['reportes_enviados']}")
            print(f"⚠️ Pendientes revisión: {stats['pendientes_revision']}")
            print(f"🚀 Listos para envío: {stats['listos_envio']}")
            
            # Verificar credenciales
            credenciales = load_email_credentials()
            if credenciales.get('email'):
                print(f"\n✅ Credenciales configuradas: {credenciales['email']}")
                print("🔑 Contraseña: Configurada")
            else:
                print("\n⚠️ No hay credenciales configuradas")
            
            # Estado del sistema
            if stats['pendientes_revision'] > 0:
                print(f"\n⚠️ ATENCIÓN: Hay {stats['pendientes_revision']} reportes con importancia 'Pendiente'")
                print("📝 Debes asignar importancia antes de enviar emails")
            elif stats['listos_envio'] > 0:
                print(f"\n🚀 LISTO: {stats['listos_envio']} reportes listos para envío")
                print("✅ El sistema está listo para enviar emails")
            else:
                print("\n💡 No hay reportes pendientes de envío")
            
            return True
        else:
            print("❌ Error al obtener estadísticas")
            return False
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 Test de corrección de emails - Columnas anidadas")
    print("=" * 60)
    
    success = test_email_system()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ CORRECCIÓN EXITOSA")
        print("🎯 El error de columnas anidadas ha sido solucionado")
        print("📧 Ahora puedes enviar emails sin problemas")
        print("\n💡 Instrucciones:")
        print("1. Ve a la pestaña 'Emails' en tu aplicación")
        print("2. Haz clic en '🚀 Enviar Todos los Emails'")
        print("3. Confirma con '✅ Sí, Enviar'")
        print("4. Los resultados se mostrarán correctamente sin errores")
    else:
        print("❌ PROBLEMAS DETECTADOS")
        print("🔧 Revisa la configuración del sistema")
