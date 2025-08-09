#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de envío de emails
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla
from email_sender import obtener_estadisticas_envios, obtener_registros_pendientes_envio
from config import load_email_credentials

def test_email_functionality():
    """Prueba la funcionalidad de envío de emails"""
    print("🧪 Probando funcionalidad de envío de emails...")
    
    # Verificar conexión a la base de datos
    print("\n1. Verificando conexión a la base de datos...")
    conn = crear_conexion()
    if conn:
        print("   ✅ Conexión exitosa")
        
        try:
            crear_tabla(conn)
            print("   ✅ Tabla verificada/creada")
            
            # Obtener estadísticas
            print("\n2. Obteniendo estadísticas de envíos...")
            stats = obtener_estadisticas_envios(conn)
            if stats:
                print(f"   📊 Total reportes: {stats['total_reportes']}")
                print(f"   📄 Reportes generados: {stats['reportes_generados']}")
                print(f"   📧 Reportes enviados: {stats['reportes_enviados']}")
                print(f"   ⚠️ Pendientes revisión: {stats['pendientes_revision']}")
                print(f"   🚀 Listos para envío: {stats['listos_envio']}")
                
                # Verificar si hay reportes listos para envío
                if stats['listos_envio'] > 0:
                    print(f"\n3. Verificando reportes listos para envío...")
                    try:
                        registros = obtener_registros_pendientes_envio(conn)
                        print(f"   ✅ Se encontraron {len(registros)} clientes con reportes listos")
                        
                        for titular, datos in list(registros.items())[:3]:  # Mostrar solo los primeros 3
                            email = datos.get('email', 'Sin email')
                            cantidad = len(datos.get('boletines', []))
                            print(f"   - {titular}: {cantidad} reportes, email: {email}")
                    except Exception as e:
                        print(f"   ❌ Error al obtener registros: {e}")
                else:
                    print(f"\n3. No hay reportes listos para envío")
            else:
                print("   ❌ Error al obtener estadísticas")
            
            # Verificar credenciales
            print(f"\n4. Verificando credenciales de email...")
            credentials = load_email_credentials()
            if credentials['email']:
                print(f"   ✅ Email configurado: {credentials['email']}")
                print(f"   ✅ Password: {'Configurado' if credentials['password'] else 'No configurado'}")
            else:
                print(f"   ⚠️ No hay credenciales configuradas")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            conn.close()
    else:
        print("   ❌ Error de conexión")
    
    print(f"\n✅ Prueba completada.")

if __name__ == "__main__":
    test_email_functionality()
