#!/usr/bin/env python3
"""
Demo de la nueva funcionalidad de Vista de Emails Enviados.
Muestra las capacidades y características principales.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, crear_tabla, obtener_emails_enviados, obtener_ruta_reporte_pdf

def demo_vista_emails():
    """
    Demostración de la nueva vista de emails enviados.
    """
    print("🎭 DEMO: Nueva Vista de Emails Enviados")
    print("=" * 60)
    print("Esta demostración muestra las nuevas capacidades implementadas\n")
    
    conn = crear_conexion()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        crear_tabla(conn)
        
        # 1. Mostrar capacidades de filtrado
        print("🔍 1. CAPACIDADES DE FILTRADO")
        print("-" * 30)
        
        # Sin filtros (todos)
        todos_emails = obtener_emails_enviados(conn, limite=50)
        print(f"📧 Total emails enviados: {len(todos_emails)}")
        
        if todos_emails:
            # Filtro por titular
            titular_ejemplo = todos_emails[0]['titular']
            filtro_titular = obtener_emails_enviados(conn, filtro_titular=titular_ejemplo[:10])
            print(f"🏢 Filtrado por '{titular_ejemplo[:10]}': {len(filtro_titular)} resultados")
            
            # Filtro por fechas (últimos 30 días)
            from datetime import datetime, timedelta
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
            fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            filtro_fecha = obtener_emails_enviados(
                conn, 
                filtro_fechas=(fecha_desde, fecha_hasta),
                limite=100
            )
            print(f"📅 Últimos 30 días: {len(filtro_fecha)} emails")
        
        # 2. Análisis de contenido
        print(f"\n📊 2. ANÁLISIS DE CONTENIDO")
        print("-" * 30)
        
        if todos_emails:
            total_boletines = sum(email['total_boletines'] for email in todos_emails)
            titulares_unicos = len(set(email['titular'] for email in todos_emails))
            promedio_boletines = total_boletines / len(todos_emails) if todos_emails else 0
            
            print(f"📄 Total boletines enviados: {total_boletines}")
            print(f"👥 Titulares únicos: {titulares_unicos}")
            print(f"📊 Promedio boletines/email: {promedio_boletines:.1f}")
            
            # Análisis por importancia
            importancias = {}
            for email in todos_emails:
                if email['importancia']:
                    importancias[email['importancia']] = importancias.get(email['importancia'], 0) + 1
            
            if importancias:
                print(f"⚡ Distribución por importancia:")
                for imp, count in importancias.items():
                    print(f"   {imp}: {count} emails")
        
        # 3. Verificación de PDFs
        print(f"\n📁 3. VERIFICACIÓN DE ARCHIVOS PDF")
        print("-" * 30)
        
        informes_dir = "informes"
        if os.path.exists(informes_dir):
            archivos_pdf = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
            print(f"📄 PDFs en directorio: {len(archivos_pdf)}")
            
            # Verificar coincidencias
            pdfs_encontrados = 0
            pdfs_faltantes = 0
            
            for email in todos_emails[:5]:  # Verificar primeros 5
                ruta_pdf = obtener_ruta_reporte_pdf(email['titular'], email['fecha_envio'])
                if ruta_pdf and os.path.exists(ruta_pdf):
                    pdfs_encontrados += 1
                    print(f"   ✅ {email['titular']}: {os.path.basename(ruta_pdf)}")
                else:
                    pdfs_faltantes += 1
                    print(f"   ❌ {email['titular']}: PDF no encontrado")
            
            print(f"\n📊 Resultado verificación (primeros 5):")
            print(f"   ✅ PDFs encontrados: {pdfs_encontrados}")
            print(f"   ❌ PDFs faltantes: {pdfs_faltantes}")
        else:
            print(f"⚠️ Directorio 'informes/' no existe")
        
        # 4. Ejemplo de datos detallados
        print(f"\n📋 4. EJEMPLO DE DATOS DETALLADOS")
        print("-" * 30)
        
        if todos_emails:
            email_ejemplo = todos_emails[0]
            print(f"📧 Email de ejemplo:")
            print(f"   Titular: {email_ejemplo['titular']}")
            print(f"   Email: {email_ejemplo['email']}")
            print(f"   Fecha: {email_ejemplo['fecha_envio'] or 'No especificada'}")
            print(f"   Boletines: {email_ejemplo['total_boletines']}")
            print(f"   Importancia: {email_ejemplo['importancia'] or 'No especificada'}")
            
            if email_ejemplo['numeros_boletines']:
                boletines_str = ', '.join(email_ejemplo['numeros_boletines'][:3])
                if len(email_ejemplo['numeros_boletines']) > 3:
                    boletines_str += f" (+ {len(email_ejemplo['numeros_boletines']) - 3} más)"
                print(f"   Números: {boletines_str}")
        
        # 5. Capacidades de la interfaz
        print(f"\n🎨 5. CARACTERÍSTICAS DE LA INTERFAZ")
        print("-" * 30)
        print("✅ Filtros avanzados:")
        print("   • Por titular (búsqueda parcial)")
        print("   • Por rango de fechas (desde/hasta)")
        print("   • Límite de resultados (25/50/100/200)")
        print("   • Actualización manual")
        
        print("\n✅ Información mostrada:")
        print("   • Datos completos del envío")
        print("   • Estadísticas agregadas")
        print("   • Lista expandible de boletines")
        print("   • Estado de archivos PDF")
        
        print("\n✅ Funcionalidades:")
        print("   • Descarga directa de PDFs")
        print("   • Vista expandible por email")
        print("   • Organización cronológica")
        print("   • Manejo de errores robusto")
        
        # 6. Instrucciones de uso
        print(f"\n🚀 6. CÓMO ACCEDER A LA NUEVA VISTA")
        print("-" * 30)
        print("1. Ejecuta la aplicación:")
        print("   streamlit run app.py")
        print("\n2. Navega a la sección 'Emails'")
        print("\n3. Haz clic en la pestaña '📁 Emails Enviados'")
        print("\n4. Utiliza los filtros para encontrar emails específicos")
        print("\n5. Expande un email para ver detalles completos")
        print("\n6. Descarga PDFs con el botón '📥 Descargar PDF'")
        
        print("\n" + "=" * 60)
        print("🎉 DEMOSTRACIÓN COMPLETADA")
        print("\nLa nueva vista de emails enviados está lista para usar!")
        print("Proporciona acceso completo al historial con descarga de PDFs.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la demostración: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    demo_vista_emails()

if __name__ == "__main__":
    main()
