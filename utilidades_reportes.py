#!/usr/bin/env python3
"""
Script utilitario para cambiar la importancia de registros pendientes
y poder generar reportes de demostración
"""

import sqlite3
import os

def mostrar_registros_pendientes():
    """Muestra los registros con importancia 'Pendiente'"""
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT titular, COUNT(*) as cantidad
        FROM boletines 
        WHERE importancia = 'Pendiente' AND reporte_generado = 0
        GROUP BY titular
        ORDER BY cantidad DESC
    ''')
    
    registros = cursor.fetchall()
    conn.close()
    
    if registros:
        print("📋 Registros con importancia 'Pendiente':")
        for titular, cantidad in registros:
            print(f"   • {titular}: {cantidad} registros")
        return registros
    else:
        print("✅ No hay registros pendientes")
        return []

def cambiar_importancia_temporal(titular=None, nueva_importancia='Alta', limite=3):
    """
    Cambia temporalmente la importancia de algunos registros para generar reportes de prueba
    """
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    try:
        if titular:
            # Cambiar registros de un titular específico
            cursor.execute('''
                UPDATE boletines 
                SET importancia = ? 
                WHERE titular = ? 
                AND importancia = 'Pendiente' 
                AND reporte_generado = 0
                LIMIT ?
            ''', (nueva_importancia, titular, limite))
        else:
            # Cambiar algunos registros de cualquier titular
            cursor.execute('''
                UPDATE boletines 
                SET importancia = ? 
                WHERE importancia = 'Pendiente' 
                AND reporte_generado = 0
                LIMIT ?
            ''', (nueva_importancia, limite))
        
        registros_actualizados = cursor.rowcount
        conn.commit()
        
        print(f"✅ Se cambiaron {registros_actualizados} registros a importancia '{nueva_importancia}'")
        return registros_actualizados
        
    except Exception as e:
        print(f"❌ Error al cambiar importancia: {e}")
        return 0
    finally:
        conn.close()

def restaurar_importancia_pendiente():
    """Restaura todos los registros modificados a 'Pendiente'"""
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE boletines 
            SET importancia = 'Pendiente' 
            WHERE reporte_generado = 0 
            AND importancia IN ('Alta', 'Media', 'Baja')
        ''')
        
        registros_restaurados = cursor.rowcount
        conn.commit()
        
        print(f"🔄 Se restauraron {registros_restaurados} registros a 'Pendiente'")
        return registros_restaurados
        
    except Exception as e:
        print(f"❌ Error al restaurar: {e}")
        return 0
    finally:
        conn.close()

def generar_reportes_demo():
    """Genera reportes de demostración cambiando temporalmente algunos registros"""
    from report_generator import ReportGenerator
    
    print("🎨 Generando reportes de demostración...")
    
    # Cambiar algunos registros para demo
    cambios = cambiar_importancia_temporal(nueva_importancia='Alta', limite=2)
    cambiar_importancia_temporal(nueva_importancia='Media', limite=1)
    
    if cambios > 0:
        # Generar reportes
        conn = sqlite3.connect('boletines.db')
        generator = ReportGenerator(
            watermark_path="imagenes/marca_agua.jpg",
            output_dir="informes"
        )
        
        resultado = generator.generate_reports(conn)
        conn.close()
        
        if resultado['success']:
            print(f"✅ Se generaron {resultado['reportes_generados']} reportes de demostración")
            
            # Mostrar archivos generados
            if os.path.exists('informes'):
                archivos = [f for f in os.listdir('informes') 
                           if f.endswith('.pdf') and 'September-2025' in f]
                if archivos:
                    print("📄 Reportes generados:")
                    for archivo in sorted(archivos)[-5:]:
                        print(f"   • {archivo}")
        else:
            print(f"❌ Error al generar reportes: {resultado.get('message', 'Error desconocido')}")
    
    return cambios > 0

def menu_principal():
    """Menú principal del script"""
    while True:
        print("\n" + "=" * 60)
        print("🛠️  UTILIDADES PARA REPORTES PROFESIONALES")
        print("=" * 60)
        print("1. 📋 Mostrar registros pendientes")
        print("2. 🎨 Generar reportes de demostración")
        print("3. ⚙️  Cambiar importancia manualmente")
        print("4. 🔄 Restaurar todos a 'Pendiente'")
        print("5. 🚪 Salir")
        print("=" * 60)
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == '1':
            print("\n📋 REGISTROS PENDIENTES:")
            print("-" * 40)
            mostrar_registros_pendientes()
            
        elif opcion == '2':
            print("\n🎨 GENERANDO REPORTES DE DEMOSTRACIÓN:")
            print("-" * 40)
            if generar_reportes_demo():
                print("\n💡 Los reportes se han generado en la carpeta 'informes'")
                print("🎨 Puedes ver el nuevo diseño profesional:")
                print("   • Encabezado elegante con logo")
                print("   • Títulos en azul profesional")
                print("   • Tabla con estilo zebra")
                print("   • Separadores elegantes")
                print("   • Pie de página confidencial")
                
                restaurar = input("\n¿Quieres restaurar los registros a 'Pendiente'? (y/n): ")
                if restaurar.lower().strip() in ['y', 'yes', 'sí', 's']:
                    restaurar_importancia_pendiente()
            
        elif opcion == '3':
            print("\n⚙️  CAMBIO MANUAL DE IMPORTANCIA:")
            print("-" * 40)
            registros = mostrar_registros_pendientes()
            
            if registros:
                print("\nTitulares disponibles:")
                for i, (titular, cantidad) in enumerate(registros[:5], 1):
                    print(f"{i}. {titular} ({cantidad} registros)")
                
                try:
                    seleccion = int(input("\nSelecciona un titular (número): ")) - 1
                    if 0 <= seleccion < len(registros):
                        titular_seleccionado = registros[seleccion][0]
                        
                        print("\nImportancias disponibles:")
                        print("1. Alta")
                        print("2. Media") 
                        print("3. Baja")
                        
                        imp_seleccion = int(input("Selecciona importancia (1-3): "))
                        importancias = ['Alta', 'Media', 'Baja']
                        
                        if 1 <= imp_seleccion <= 3:
                            nueva_imp = importancias[imp_seleccion - 1]
                            limite = int(input(f"¿Cuántos registros cambiar? (max 10): ") or "3")
                            limite = min(limite, 10)
                            
                            cambiar_importancia_temporal(titular_seleccionado, nueva_imp, limite)
                        else:
                            print("❌ Selección inválida")
                    else:
                        print("❌ Selección inválida")
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
            
        elif opcion == '4':
            print("\n🔄 RESTAURANDO REGISTROS:")
            print("-" * 40)
            confirmacion = input("¿Estás seguro de restaurar TODOS los registros a 'Pendiente'? (y/n): ")
            if confirmacion.lower().strip() in ['y', 'yes', 'sí', 's']:
                restaurar_importancia_pendiente()
            else:
                print("❌ Operación cancelada")
                
        elif opcion == '5':
            print("\n👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida. Por favor selecciona 1-5.")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    print("🛠️  UTILIDADES PARA REPORTES PROFESIONALES")
    print("Este script te ayuda a probar el nuevo diseño de reportes")
    print("cambiando temporalmente la importancia de algunos registros.\n")
    
    if not os.path.exists('boletines.db'):
        print("❌ No se encontró la base de datos 'boletines.db'")
        print("Asegúrate de estar en el directorio correcto.")
    else:
        menu_principal()
