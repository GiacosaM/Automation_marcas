#!/usr/bin/env python3
"""
Ejemplo de uso del generador de reportes profesional mejorado
Este script muestra cómo integrar el nuevo diseño con tu aplicación existente
"""

import sqlite3
import os
from report_generator import ReportGenerator
from paths import get_db_path, get_image_path

def generar_reportes_profesionales():
    """
    Función principal para generar reportes con el nuevo diseño profesional
    
    Características del nuevo diseño:
    - Encabezado con logo y nombre del estudio
    - Títulos en azul con tipografía elegante
    - Tabla resumen con estilo zebra
    - Detalle completo de registros
    - Pie de página con texto confidencial
    - Márgenes amplios y mejor distribución
    """
    
    print("🎨 Generando reportes con diseño profesional...")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(get_db_path())
        
        # Configurar el generador con ruta de marca de agua
        generator = ReportGenerator(
            watermark_path=get_image_path("marca_agua.jpg")  # Ruta a tu logo
            # El directorio de salida será automáticamente get_informes_dir()
        )
        
        # Generar todos los reportes pendientes
        resultado = generator.generate_reports(conn)
        
        # Mostrar resultados
        if resultado['success']:
            print(f"✅ Reportes generados exitosamente!")
            print(f"   📊 Total de reportes: {resultado['reportes_generados']}")
            print(f"   📋 Registros procesados: {resultado.get('registros_procesados', 0)}")
            
            if resultado.get('pendientes', 0) > 0:
                print(f"   ⚠️  Registros pendientes sin procesar: {resultado['pendientes']}")
                print(f"      💡 Cambia la importancia de 'Pendiente' para procesarlos")
        else:
            print(f"❌ Error al generar reportes: {resultado.get('message', 'Error desconocido')}")
        
        conn.close()
        
        return resultado
        
    except Exception as e:
        print(f"💥 Error durante la generación: {e}")
        return {'success': False, 'error': str(e)}

def personalizar_estudio_contable():
    """
    Función para personalizar el nombre del estudio contable
    Puedes modificar esta función para cambiar el nombre que aparece en los reportes
    """
    
    # Para cambiar el nombre del estudio, modifica esta línea en report_generator.py:
    # pdf = ProfessionalReportPDF(watermark, "TU NOMBRE DE ESTUDIO AQUÍ")
    
    print("💡 Para personalizar el nombre del estudio contable:")
    print("   1. Abre report_generator.py")
    print("   2. Busca la línea: ProfessionalReportPDF(watermark, \"ESTUDIO CONTABLE PROFESSIONAL\")")
    print("   3. Cambia el texto por el nombre de tu estudio")
    print("   4. Guarda el archivo")

def verificar_configuracion():
    """
    Verifica que la configuración esté correcta para generar reportes profesionales
    """
    
    print("🔍 Verificando configuración...")
    
    # Verificar base de datos
    if os.path.exists(get_db_path()):
        print("✅ Base de datos encontrada")
    else:
        print("❌ Base de datos no encontrada")
        return False
    
    # Verificar directorio de imágenes
    if os.path.exists('imagenes'):
        print("✅ Directorio de imágenes encontrado")
        
        # Verificar marca de agua
        watermark_paths = ['imagenes/marca_agua.jpg', 'imagenes/Logo.png']
        watermark_found = False
        for path in watermark_paths:
            if os.path.exists(path):
                print(f"✅ Marca de agua encontrada: {path}")
                watermark_found = True
                break
        
        if not watermark_found:
            print("⚠️  Marca de agua no encontrada")
            print("   💡 Coloca tu logo en imagenes/marca_agua.jpg o imagenes/Logo.png")
    else:
        print("⚠️  Directorio de imágenes no encontrado")
    
    # Verificar directorio de salida
    if not os.path.exists('informes'):
        os.makedirs('informes', exist_ok=True)
        print("✅ Directorio de informes creado")
    else:
        print("✅ Directorio de informes encontrado")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("🎨 GENERADOR DE REPORTES PROFESIONAL - NUEVO DISEÑO")
    print("=" * 70)
    
    # Verificar configuración
    if verificar_configuracion():
        print("\n" + "-" * 50)
        
        # Generar reportes
        resultado = generar_reportes_profesionales()
        
        if resultado['success'] and resultado['reportes_generados'] > 0:
            print("\n" + "-" * 50)
            print("🎉 ¡REPORTES GENERADOS CON ÉXITO!")
            print("=" * 70)
            print("✨ NUEVAS CARACTERÍSTICAS DEL DISEÑO:")
            print("   • 📋 Encabezado elegante con logo y fecha")
            print("   • 🎨 Títulos en azul profesional")
            print("   • 📊 Tabla de resumen con bordes finos")
            print("   • 🦓 Filas alternadas en gris claro (estilo zebra)")
            print("   • 📄 Detalle completo de cada registro")
            print("   • 🔒 Pie de página con texto confidencial")
            print("   • 📏 Márgenes amplios y mejor espaciado")
            print("=" * 70)
            
            # Mostrar archivos generados
            if os.path.exists('informes'):
                archivos = [f for f in os.listdir('informes') if f.endswith('.pdf')]
                if archivos:
                    print("📁 Archivos generados en el directorio 'informes':")
                    for archivo in sorted(archivos)[-5:]:  # Últimos 5
                        print(f"   📄 {archivo}")
        
        print("\n" + "-" * 50)
        personalizar_estudio_contable()
        
    else:
        print("\n❌ Configuración incompleta. Corrige los problemas y vuelve a intentar.")
    
    print("\n" + "=" * 70)
