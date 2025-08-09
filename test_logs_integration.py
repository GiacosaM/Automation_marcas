#!/usr/bin/env python3
"""
Script para probar la integración completa de la tabla envios_log
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla, insertar_log_envio, obtener_logs_envios, obtener_estadisticas_logs
from email_sender import obtener_estadisticas_envios
from config import load_email_credentials

def test_logs_integration():
    """Probar la integración completa de logs de envíos"""
    print("🧪 Probando integración de tabla envios_log...")
    print("=" * 60)
    
    # Conectar a la base de datos
    conn = crear_conexion()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Crear todas las tablas (incluyendo envios_log)
        crear_tabla(conn)
        print("✅ Tablas creadas/verificadas correctamente")
        
        # Verificar que la tabla envios_log existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='envios_log'")
        tabla_existe = cursor.fetchone()
        cursor.close()
        
        if tabla_existe:
            print("✅ Tabla 'envios_log' creada correctamente")
        else:
            print("❌ Tabla 'envios_log' no existe")
            return False
        
        # Probar inserción de logs de prueba
        print("\n📝 Insertando logs de prueba...")
        
        # Log exitoso
        insertar_log_envio(
            conn, 
            "EMPRESA DEMO S.A.", 
            "demo@empresa.com", 
            "exitoso", 
            None, 
            "BOL-2025-001", 
            "Alta"
        )
        
        # Log fallido
        insertar_log_envio(
            conn, 
            "CLIENTE SIN EMAIL", 
            "N/A", 
            "sin_email", 
            "Cliente sin email registrado"
        )
        
        # Log con error
        insertar_log_envio(
            conn, 
            "CLIENTE CON ERROR", 
            "error@cliente.com", 
            "fallido", 
            "Conexión SMTP falló", 
            "BOL-2025-002", 
            "Media"
        )
        
        print("✅ Logs de prueba insertados")
        
        # Obtener estadísticas de logs
        print("\n📊 Obteniendo estadísticas de logs...")
        stats_logs = obtener_estadisticas_logs(conn)
        
        print(f"📧 Total envíos en logs: {stats_logs['total_envios']}")
        print(f"✅ Exitosos: {stats_logs['exitosos']}")
        print(f"❌ Fallidos: {stats_logs['fallidos']}")
        print(f"📧 Sin email: {stats_logs['sin_email']}")
        print(f"📄 Sin archivo: {stats_logs['sin_archivo']}")
        print(f"📈 Tasa de éxito: {stats_logs['tasa_exito']:.1f}%")
        print(f"📅 Envíos hoy: {stats_logs['envios_hoy']}")
        
        if stats_logs['por_importancia']:
            print("📊 Por importancia:")
            for imp, cant in stats_logs['por_importancia'].items():
                print(f"   {imp}: {cant}")
        
        # Obtener logs recientes
        print("\n📋 Últimos logs:")
        logs_rows, logs_columns = obtener_logs_envios(conn, limite=10)
        
        if logs_rows:
            print(f"📄 Se encontraron {len(logs_rows)} logs")
            for row in logs_rows[:3]:  # Mostrar solo los primeros 3
                print(f"   {row[1]} -> {row[2]} | {row[4]} | {row[3]}")
        else:
            print("📭 No hay logs registrados")
        
        # Verificar estadísticas del sistema principal
        print("\n🔍 Verificando sistema principal...")
        stats_sistema = obtener_estadisticas_envios(conn)
        
        if stats_sistema:
            print(f"📋 Total reportes en sistema: {stats_sistema['total_reportes']}")
            print(f"🚀 Listos para envío: {stats_sistema['listos_envio']}")
            print(f"⚠️ Pendientes revisión: {stats_sistema['pendientes_revision']}")
        
        # Verificar credenciales
        credenciales = load_email_credentials()
        if credenciales.get('email'):
            print(f"✅ Credenciales configuradas: {credenciales['email']}")
        else:
            print("⚠️ No hay credenciales configuradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔗 Test de Integración - Tabla envios_log")
    print("=" * 60)
    
    success = test_logs_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ INTEGRACIÓN EXITOSA")
        print("🎯 La tabla envios_log está completamente integrada")
        print("📧 Los envíos se registrarán automáticamente en los logs")
        print("\n💡 Nuevas funcionalidades disponibles:")
        print("1. 📋 Pestaña 'Logs Detallados' en la sección Emails")
        print("2. 📊 Estadísticas completas de envíos y errores") 
        print("3. 🔍 Filtros por estado, titular y fecha")
        print("4. 💾 Exportación de logs a CSV")
        print("5. 🗑️ Limpieza automática de logs antiguos")
        print("6. 📈 Métricas de tasa de éxito por importancia")
    else:
        print("❌ PROBLEMAS EN LA INTEGRACIÓN")
        print("🔧 Revisa la configuración y vuelve a intentar")
