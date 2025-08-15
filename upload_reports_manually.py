#!/usr/bin/env python3
"""
Subida manual de reportes a Google Drive
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def upload_reports_manually():
    """Subir reportes manualmente a Google Drive"""
    
    print("📤 SUBIDA MANUAL DE REPORTES")
    print("=" * 40)
    
    # Buscar archivos PDF en la carpeta informes
    informes_dir = "informes"
    if not os.path.exists(informes_dir):
        print(f"❌ Carpeta {informes_dir} no encontrada")
        return
    
    pdf_files = [f for f in os.listdir(informes_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("⚠️ No se encontraron archivos PDF para subir")
        return
    
    print(f"📊 Encontrados {len(pdf_files)} archivos PDF:")
    for i, file in enumerate(pdf_files, 1):
        print(f"   {i}. {file}")
    
    print("\n🔑 Intentando autenticación...")
    try:
        from google_drive_manager import GoogleDriveManager
        drive_manager = GoogleDriveManager()
        
        if drive_manager.authenticate():
            print("✅ Autenticación exitosa")
            
            successful_uploads = 0
            failed_uploads = 0
            
            for file in pdf_files:
                file_path = os.path.join(informes_dir, file)
                print(f"\n📤 Subiendo {file}...")
                
                try:
                    # Extraer información del nombre del archivo
                    # Formato esperado: "Mes-Año - Informe EMPRESA - Importancia - Numero.pdf"
                    parts = file.replace('.pdf', '').split(' - ')
                    if len(parts) >= 4:
                        fecha_str = parts[0]  # "Mes-Año"
                        titular = parts[2]    # "EMPRESA"
                        importancia = parts[3]  # "Importancia"
                        numero = parts[4] if len(parts) > 4 else "000000"
                        
                        from datetime import datetime
                        # Convertir fecha_str a datetime (aproximado)
                        fecha_reporte = datetime.now()
                        
                        result = drive_manager.upload_report(
                            file_path=file_path,
                            titular=titular,
                            fecha_reporte=fecha_reporte,
                            importancia=importancia,
                            numero_boletin=numero
                        )
                        
                        if result['success']:
                            print(f"✅ {file} subido exitosamente")
                            successful_uploads += 1
                        else:
                            print(f"❌ Error subiendo {file}: {result['message']}")
                            failed_uploads += 1
                    else:
                        print(f"⚠️ Formato de nombre no reconocido: {file}")
                        failed_uploads += 1
                
                except Exception as e:
                    print(f"❌ Error procesando {file}: {e}")
                    failed_uploads += 1
            
            print(f"\n📊 RESUMEN:")
            print(f"✅ Subidos exitosamente: {successful_uploads}")
            print(f"❌ Fallidos: {failed_uploads}")
            
        else:
            print("❌ Error de autenticación")
            print("💡 Ejecuta primero la configuración de Google Drive")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    upload_reports_manually()
