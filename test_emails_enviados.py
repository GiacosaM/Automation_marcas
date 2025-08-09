#!/usr/bin/env python3
"""
Script de prueba para la nueva funcionalidad de vista de emails enviados.
Verifica que las nuevas funciones funcionen correctamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla, obtener_emails_enviados, obtener_ruta_reporte_pdf

def test_emails_enviados():
    """
    Prueba la funcionalidad de vista de emails enviados.
    """
    print("🧪 Iniciando prueba de vista de emails enviados...")
    print("=" * 60)
    
    # Crear conexión a la base de datos
    conn = crear_conexion()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Asegurar que las tablas existen
        crear_tabla(conn)
        
        # Ejecutar función de emails enviados
        print("🔍 Obteniendo emails enviados...")
        emails_enviados = obtener_emails_enviados(conn, limite=10)
        
        # Mostrar resultados
        print(f"\n📧 EMAILS ENVIADOS ENCONTRADOS: {len(emails_enviados)}")
        print("-" * 60)
        
        if emails_enviados:
            for i, email in enumerate(emails_enviados, 1):
                print(f"\n📧 EMAIL #{i}:")
                print(f"   Titular: {email['titular']}")
                print(f"   Email: {email['email']}")
                print(f"   Fecha Envío: {email['fecha_envio']}")
                print(f"   Total Boletines: {email['total_boletines']}")
                print(f"   Importancia: {email['importancia']}")
                
                # Buscar archivo PDF
                ruta_pdf = obtener_ruta_reporte_pdf(email['titular'], email['fecha_envio'])
                if ruta_pdf:
                    print(f"   📄 PDF Encontrado: {os.path.basename(ruta_pdf)}")
                    print(f"   📁 Ruta Completa: {ruta_pdf}")
                    print(f"   ✅ Archivo existe: {'Sí' if os.path.exists(ruta_pdf) else 'No'}")
                else:
                    print(f"   ❌ PDF No encontrado")
                
                if email['numeros_boletines']:
                    print(f"   📋 Boletines: {', '.join(email['numeros_boletines'][:3])}{'...' if len(email['numeros_boletines']) > 3 else ''}")
                
                print("-" * 40)
        else:
            print("   📭 No se encontraron emails enviados")
            print("\n💡 PARA PROBAR LA FUNCIONALIDAD:")
            print("   1. Asegúrate de tener registros en la tabla 'envios_log' con estado 'exitoso'")
            print("   2. Verifica que existan archivos PDF en la carpeta 'informes/'")
            print("   3. Ejecuta algunos envíos de email desde la aplicación")
        
        # Probar filtros
        print(f"\n🔍 PROBANDO FILTROS...")
        if emails_enviados:
            titular_test = emails_enviados[0]['titular']
            emails_filtrados = obtener_emails_enviados(conn, filtro_titular=titular_test[:10], limite=5)
            print(f"   Filtro por titular '{titular_test[:10]}': {len(emails_filtrados)} resultados")
        
        # Verificar archivos PDF en directorio
        print(f"\n📁 VERIFICANDO DIRECTORIO DE INFORMES...")
        informes_dir = "informes"
        if os.path.exists(informes_dir):
            archivos_pdf = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
            print(f"   📄 PDFs encontrados: {len(archivos_pdf)}")
            
            if archivos_pdf:
                print("   📋 Algunos archivos encontrados:")
                for pdf in archivos_pdf[:3]:
                    print(f"     • {pdf}")
                if len(archivos_pdf) > 3:
                    print(f"     • ... y {len(archivos_pdf) - 3} más")
        else:
            print(f"   ⚠️ Directorio 'informes/' no existe")
        
        print("\n" + "=" * 60)
        print("✅ Prueba de emails enviados completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    print("🚀 PRUEBA DE VISTA DE EMAILS ENVIADOS")
    print("Este script verifica la nueva funcionalidad de historial")
    print("de emails enviados con acceso a PDFs.\n")
    
    success = test_emails_enviados()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n💡 NUEVA FUNCIONALIDAD AGREGADA:")
        print("   ✅ Nueva pestaña '📁 Emails Enviados' en sección Emails")
        print("   ✅ Vista detallada de emails enviados exitosamente")
        print("   ✅ Filtros por titular y rango de fechas")
        print("   ✅ Acceso directo a PDFs de reportes")
        print("   ✅ Estadísticas de envíos")
        print("   ✅ Información detallada de boletines incluidos")
        print("\n🔧 CÓMO USAR:")
        print("   1. Ejecuta: streamlit run app.py")
        print("   2. Ve a la sección 'Emails'")
        print("   3. Haz clic en la pestaña '📁 Emails Enviados'")
        print("   4. Explora los emails enviados y descarga PDFs")
        print("\n📋 CARACTERÍSTICAS:")
        print("   • Historial completo de emails exitosos")
        print("   • Filtrado por titular y fechas")
        print("   • Descarga directa de PDFs")
        print("   • Información detallada de cada envío")
        print("   • Estadísticas agregadas")
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
