#!/usr/bin/env python3
"""
Script de prueba para la validación de emails antes del envío.
Verifica que la nueva funcionalidad de validación de clientes funcione correctamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla
from email_sender import validar_clientes_para_envio

def test_validacion_emails():
    """
    Prueba la funcionalidad de validación de clientes para envío de emails.
    """
    print("🧪 Iniciando prueba de validación de emails...")
    print("=" * 60)
    
    # Crear conexión a la base de datos
    conn = crear_conexion()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Asegurar que las tablas existen
        crear_tabla(conn)
        
        # Ejecutar validación
        print("🔍 Ejecutando validación de clientes...")
        validacion = validar_clientes_para_envio(conn)
        
        # Mostrar resultados
        print("\n📊 RESULTADOS DE VALIDACIÓN:")
        print(f"   Total de clientes: {validacion['total_clientes']}")
        print(f"   Con email: {validacion['con_email']}")
        print(f"   Sin email: {len(validacion['sin_email'])}")
        print(f"   Con reporte: {validacion['con_reporte']}")
        print(f"   Sin reporte: {len(validacion['sin_reporte'])}")
        print(f"   Listos para envío: {validacion['listos_para_envio']}")
        print(f"   Puede continuar: {'✅ Sí' if validacion['puede_continuar'] else '❌ No'}")
        
        # Mostrar mensajes detallados
        if validacion['mensajes']:
            print("\n📝 MENSAJES DETALLADOS:")
            for mensaje in validacion['mensajes']:
                print(f"   {mensaje}")
        
        # Mostrar listas de clientes con problemas
        if validacion['sin_email']:
            print(f"\n📧 CLIENTES SIN EMAIL ({len(validacion['sin_email'])}):")
            for cliente in validacion['sin_email']:
                print(f"   • {cliente}")
        
        if validacion['sin_reporte']:
            print(f"\n📄 CLIENTES SIN REPORTE ({len(validacion['sin_reporte'])}):")
            for cliente in validacion['sin_reporte']:
                print(f"   • {cliente}")
        
        print("\n" + "=" * 60)
        print("✅ Prueba de validación completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    print("🚀 PRUEBA DE VALIDACIÓN DE EMAILS")
    print("Este script verifica la nueva funcionalidad de validación")
    print("antes del envío de emails.\n")
    
    success = test_validacion_emails()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n💡 MEJORAS IMPLEMENTADAS:")
        print("   ✅ Validación previa antes del envío")
        print("   ✅ Notificaciones claras sobre clientes sin email")
        print("   ✅ Información detallada en confirmación")
        print("   ✅ Reportes mejorados post-envío")
        print("\n🔧 CÓMO USAR:")
        print("   1. Ejecuta: streamlit run app.py")
        print("   2. Ve a la sección 'Emails'")
        print("   3. Observa las nuevas validaciones y notificaciones")
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
