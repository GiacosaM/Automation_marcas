#!/usr/bin/env python3
# setup_automatizacion.py

"""
Script para configurar la ejecución automática del verificador de titulares sin reportes.
Este script:
1. Verifica la instalación de dependencias necesarias
2. Configura el cron job (en sistemas Unix/macOS)
3. Prepara la base de datos para soportar las notificaciones automáticas
"""

import os
import sys
import subprocess
import platform
import sqlite3
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_automatizacion.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('setup_automatizacion')

def print_header(text):
    """Imprime un encabezado con formato"""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")

def instalar_dependencias():
    """Instalar dependencias necesarias para la ejecución automática"""
    print_header("VERIFICACIÓN DE DEPENDENCIAS")
    
    # Lista de paquetes requeridos
    required_packages = ['schedule', 'python-crontab']
    
    for package in required_packages:
        try:
            # Intentar importar el paquete
            __import__(package)
            print(f"✅ {package} ya está instalado")
        except ImportError:
            print(f"❌ {package} no está instalado. Instalando...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} instalado correctamente")
            except Exception as e:
                print(f"❌ Error al instalar {package}: {e}")
                logger.error(f"Error al instalar {package}: {e}")

def configurar_base_datos():
    """Configurar la base de datos para soportar notificaciones automáticas"""
    print_header("CONFIGURACIÓN DE BASE DE DATOS")
    
    try:
        # Conectar a la base de datos
        print("Conectando a la base de datos...")
        conn = sqlite3.connect('boletines.db')
        cursor = conn.cursor()
        
        # Verificar si la tabla emails_enviados existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails_enviados'")
        if not cursor.fetchone():
            print("Creando tabla emails_enviados...")
            cursor.execute("""
                CREATE TABLE emails_enviados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    destinatario TEXT NOT NULL,
                    asunto TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    tipo_email TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'pendiente',
                    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    titular TEXT DEFAULT NULL
                )
            """)
            conn.commit()
            print("✅ Tabla emails_enviados creada correctamente")
        else:
            print("✅ Tabla emails_enviados ya existe")
            
            # Verificar si la columna titular existe
            cursor.execute("PRAGMA table_info(emails_enviados)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'titular' not in columns:
                print("Añadiendo columna 'titular' a la tabla emails_enviados...")
                cursor.execute("ALTER TABLE emails_enviados ADD COLUMN titular TEXT DEFAULT NULL")
                conn.commit()
                print("✅ Columna 'titular' añadida correctamente")
            else:
                print("✅ Columna 'titular' ya existe")
        
        # Cerrar conexión
        conn.close()
        print("Base de datos configurada correctamente")
        
    except Exception as e:
        print(f"❌ Error al configurar la base de datos: {e}")
        logger.error(f"Error al configurar la base de datos: {e}")

def instalar_cron_job():
    """Instalar el cron job para la ejecución automática"""
    print_header("CONFIGURACIÓN DE EJECUCIÓN AUTOMÁTICA")
    
    system = platform.system()
    
    if system in ['Darwin', 'Linux']:  # macOS o Linux
        try:
            from crontab import CronTab
            
            # Obtener el usuario actual
            user = os.environ.get('USER', os.environ.get('USERNAME', 'root'))
            
            # Crear o abrir crontab del usuario
            cron = CronTab(user=user)
            
            # Ruta absoluta al script
            script_path = os.path.abspath('ejecucion_programada.py')
            working_dir = os.path.dirname(script_path)
            
            # Verificar si ya existe un cron job para nuestro script
            existing_job = None
            for job in cron:
                if 'ejecucion_programada.py' in job.command:
                    existing_job = job
                    break
            
            if existing_job:
                print(f"✅ Ya existe un cron job configurado: {existing_job}")
                
                # Preguntar si desea actualizarlo
                response = input("¿Desea actualizarlo? [y/N]: ").strip().lower()
                if response == 'y':
                    cron.remove(existing_job)
                    print("Cron job eliminado. Configurando uno nuevo...")
                else:
                    print("Manteniendo el cron job existente")
                    return
            
            # Crear comando con ruta absoluta y cambio de directorio
            command = f'cd {working_dir} && {sys.executable} {script_path} >> {working_dir}/verificacion_log.txt 2>&1'
            
            # Crear nuevo trabajo cron para ejecutar el primer día de cada mes a las 8:00 AM
            job = cron.new(command=command, comment='Verificación mensual de titulares sin reportes')
            job.setall('0 8 1 * *')  # Primer día de cada mes a las 8:00 AM
            
            # Guardar crontab
            cron.write()
            
            print(f"✅ Cron job configurado correctamente: {job}")
            print(f"Se ejecutará automáticamente el primer día de cada mes a las 8:00 AM")
            
        except ImportError:
            print("❌ No se pudo importar python-crontab. Intente instalarlo con: pip install python-crontab")
        except Exception as e:
            print(f"❌ Error al configurar el cron job: {e}")
            logger.error(f"Error al configurar el cron job: {e}")
            
    elif system == 'Windows':
        print("Sistema Windows detectado")
        print("Para configurar la ejecución automática en Windows:")
        print("1. Abra el Programador de tareas de Windows")
        print("2. Cree una tarea básica con las siguientes características:")
        print(f"   - Programa: {sys.executable}")
        print(f"   - Argumentos: {os.path.abspath('ejecucion_programada.py')}")
        print(f"   - Iniciar en: {os.path.dirname(os.path.abspath('ejecucion_programada.py'))}")
        print("   - Programar: Mensual, día 1 de cada mes a las 8:00 AM")
        print("   - Activar la opción de ejecutarse aunque el usuario no haya iniciado sesión")
    else:
        print(f"Sistema operativo no reconocido: {system}")
        print("Configure la ejecución automática manualmente según su sistema operativo")

def verificar_permisos_ejecucion():
    """Verificar y configurar permisos de ejecución para los scripts"""
    print_header("CONFIGURANDO PERMISOS DE EJECUCIÓN")
    
    # Lista de scripts que necesitan permisos de ejecución
    scripts = ['ejecucion_programada.py', 'verificar_titulares_sin_reportes.py']
    
    system = platform.system()
    if system in ['Darwin', 'Linux']:
        for script in scripts:
            if os.path.exists(script):
                try:
                    print(f"Configurando permisos para {script}...")
                    os.chmod(script, 0o755)  # rwxr-xr-x
                    print(f"✅ Permisos configurados para {script}")
                except Exception as e:
                    print(f"❌ Error al configurar permisos para {script}: {e}")
    else:
        print("En Windows no es necesario configurar permisos de ejecución específicos")

def main():
    """Función principal del script"""
    print_header(f"CONFIGURACIÓN DE AUTOMATIZACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Instalar dependencias
        instalar_dependencias()
        
        # Configurar base de datos
        configurar_base_datos()
        
        # Verificar permisos de ejecución
        verificar_permisos_ejecucion()
        
        # Instalar cron job
        instalar_cron_job()
        
        print_header("CONFIGURACIÓN COMPLETADA")
        print("✅ El sistema está listo para ejecutar verificaciones automáticas")
        print("  - Para ejecutar manualmente: python3 ejecucion_programada.py")
        print("  - Las verificaciones automáticas se ejecutarán el día 1 de cada mes a las 8:00 AM")
        print("  - Mientras la aplicación esté en ejecución, verificará automáticamente")
        print("    el día 1 de cada mes a las 8:00 AM")
        print("  - Los resultados de la verificación se guardarán en verificacion_log.txt")
        print("  - El historial de emails enviados estará disponible en la aplicación")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        logger.error(f"Error durante la configuración: {e}", exc_info=True)
        print("Por favor, revise el archivo setup_automatizacion.log para más detalles")

if __name__ == "__main__":
    main()
