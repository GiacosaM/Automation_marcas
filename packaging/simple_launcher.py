#!/usr/bin/env python3
"""
MiAppMarcas - Launcher Simple con Python Embebido
==================================================

Este launcher:
1. Verifica/crea entorno virtual al primer arranque
2. Instala dependencias automáticamente
3. Ejecuta Streamlit con Python embebido
4. Abre el navegador automáticamente

Para el cliente es tan simple como: Doble clic en el .exe
"""

import os
import sys
import subprocess
import time
import webbrowser
import logging
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Detectar si estamos en PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Ejecutando desde PyInstaller
    BASE_DIR = Path(sys.executable).parent
    RUNNING_FROM_BUNDLE = True
else:
    # Ejecutando desde script Python
    BASE_DIR = Path(__file__).parent.parent
    RUNNING_FROM_BUNDLE = False

# Directorios
PYTHON_DIR = BASE_DIR / "python"
VENV_DIR = BASE_DIR / ".venv"
APP_DIR = BASE_DIR / "app"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
LOG_FILE = BASE_DIR / "launcher.log"

# Configuración de Streamlit
STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# UTILIDADES
# ============================================================================

def print_header(text):
    """Imprime un encabezado visual"""
    width = 60
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")

def print_progress(message, progress=None):
    """Imprime mensaje de progreso"""
    if progress is not None:
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r{message} [{bar}] {progress}%", end='', flush=True)
    else:
        print(f"  → {message}")

def get_python_executable():
    """Obtiene la ruta al ejecutable Python correcto"""
    if sys.platform == 'win32':
        # Windows
        if VENV_DIR.exists():
            return VENV_DIR / "Scripts" / "python.exe"
        else:
            return PYTHON_DIR / "python.exe"
    else:
        # macOS/Linux
        if VENV_DIR.exists():
            return VENV_DIR / "bin" / "python"
        else:
            return PYTHON_DIR / "bin" / "python3"

def check_python_embedded():
    """Verifica que Python embebido existe"""
    python_exe = PYTHON_DIR / ("python.exe" if sys.platform == 'win32' else "bin/python3")
    
    if not python_exe.exists():
        logger.error(f"Python embebido no encontrado en: {python_exe}")
        logger.error(f"Asegúrate de que la carpeta 'python' existe en: {BASE_DIR}")
        return False
    
    return True

# ============================================================================
# GESTIÓN DE ENTORNO VIRTUAL
# ============================================================================

def is_first_run():
    """Verifica si es la primera ejecución"""
    return not VENV_DIR.exists()

def create_virtual_environment():
    """Crea el entorno virtual con Python embebido"""
    try:
        print_header("PRIMERA EJECUCIÓN - CONFIGURACIÓN INICIAL")
        print("  MiAppMarcas necesita configurar el entorno")
        print("  Esto tomará 1-2 minutos (solo esta vez)\n")
        
        logger.info("Creando entorno virtual...")
        print_progress("Creando entorno virtual", 10)
        
        python_exe = get_python_executable()
        
        # Crear venv
        result = subprocess.run(
            [str(python_exe), "-m", "venv", str(VENV_DIR)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.error(f"Error creando venv: {result.stderr}")
            return False
        
        print_progress("Entorno virtual creado", 30)
        logger.info("Entorno virtual creado exitosamente")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout creando entorno virtual")
        return False
    except Exception as e:
        logger.error(f"Error creando entorno virtual: {e}", exc_info=True)
        return False

def install_dependencies():
    """Instala las dependencias desde requirements.txt"""
    try:
        logger.info("Instalando dependencias...")
        print_progress("Instalando dependencias", 40)
        
        if not REQUIREMENTS_FILE.exists():
            logger.error(f"requirements.txt no encontrado en: {REQUIREMENTS_FILE}")
            return False
        
        venv_python = get_python_executable()
        
        # Actualizar pip
        print_progress("Actualizando pip", 45)
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            timeout=120
        )
        
        # Instalar dependencias
        print_progress("Instalando paquetes (esto puede tardar)", 50)
        
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            capture_output=True,
            text=True,
            timeout=900  # 15 minutos máximo
        )
        
        if result.returncode != 0:
            logger.error(f"Error instalando dependencias: {result.stderr}")
            return False
        
        print_progress("Dependencias instaladas", 90)
        logger.info("Dependencias instaladas exitosamente")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout instalando dependencias")
        return False
    except Exception as e:
        logger.error(f"Error instalando dependencias: {e}", exc_info=True)
        return False

def setup_environment():
    """Configura el entorno completo (primera ejecución)"""
    try:
        # Verificar Python embebido
        if not check_python_embedded():
            input("\nPresiona Enter para salir...")
            sys.exit(1)
        
        # Crear entorno virtual
        if not create_virtual_environment():
            print("\n❌ Error creando entorno virtual")
            logger.error("Falló la creación del entorno virtual")
            input("\nPresiona Enter para salir...")
            sys.exit(1)
        
        # Instalar dependencias
        if not install_dependencies():
            print("\n❌ Error instalando dependencias")
            logger.error("Falló la instalación de dependencias")
            input("\nPresiona Enter para salir...")
            sys.exit(1)
        
        print_progress("Configuración completada", 100)
        print("\n\n✅ Configuración completada exitosamente!")
        print("   Iniciando aplicación...\n")
        time.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error en setup: {e}", exc_info=True)
        return False

# ============================================================================
# GESTIÓN DE STREAMLIT
# ============================================================================

def check_streamlit_running():
    """Verifica si Streamlit ya está corriendo en el puerto"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', STREAMLIT_PORT))
    sock.close()
    return result == 0

def start_streamlit():
    """Inicia el servidor de Streamlit"""
    try:
        logger.info("Iniciando Streamlit...")
        print_header("INICIANDO MIAPPMARCAS")
        
        # Verificar que la app existe
        app_file = APP_DIR / "app_refactored.py"
        if not app_file.exists():
            logger.error(f"Archivo de aplicación no encontrado: {app_file}")
            print(f"\n❌ Error: No se encontró {app_file}")
            return None
        
        # Verificar si ya está corriendo
        if check_streamlit_running():
            logger.info(f"Streamlit ya está corriendo en puerto {STREAMLIT_PORT}")
            print(f"  ℹ️  Streamlit ya está ejecutándose")
            print(f"  🌐 Abriendo navegador en {STREAMLIT_URL}\n")
            return "already_running"
        
        venv_python = get_python_executable()
        
        print(f"  🚀 Iniciando servidor...")
        print(f"  📂 Aplicación: {app_file.name}")
        print(f"  🌐 URL: {STREAMLIT_URL}\n")
        
        # Iniciar Streamlit
        cmd = [
            str(venv_python),
            "-m", "streamlit", "run",
            str(app_file),
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--global.developmentMode", "false",
            "--browser.serverAddress", "localhost"
        ]
        
        logger.info(f"Ejecutando: {' '.join(cmd)}")
        
        # Iniciar proceso en background
        if sys.platform == 'win32':
            # Windows: CREATE_NO_WINDOW
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # macOS/Linux
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        logger.info(f"Streamlit iniciado con PID: {process.pid}")
        
        # Esperar a que el servidor esté listo
        print("  ⏳ Esperando servidor...")
        max_wait = 30
        for i in range(max_wait):
            time.sleep(1)
            if check_streamlit_running():
                print("  ✅ Servidor listo!\n")
                logger.info("Servidor Streamlit listo")
                return process
            
            if i % 5 == 0 and i > 0:
                print(f"  ⏳ Esperando... ({i}/{max_wait}s)")
        
        logger.error("Timeout esperando a que Streamlit inicie")
        print("  ❌ El servidor tardó demasiado en iniciar")
        return None
        
    except Exception as e:
        logger.error(f"Error iniciando Streamlit: {e}", exc_info=True)
        print(f"\n❌ Error iniciando aplicación: {e}")
        return None

def open_browser():
    """Abre el navegador web en la URL de Streamlit"""
    try:
        print(f"  🌐 Abriendo navegador en {STREAMLIT_URL}...")
        time.sleep(2)  # Dar tiempo al servidor
        webbrowser.open(STREAMLIT_URL)
        logger.info("Navegador abierto")
        return True
    except Exception as e:
        logger.error(f"Error abriendo navegador: {e}")
        print(f"\n⚠️  No se pudo abrir el navegador automáticamente")
        print(f"   Por favor, abre manualmente: {STREAMLIT_URL}\n")
        return False

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal del launcher"""
    try:
        # Banner inicial
        print_header("MiAppMarcas - Sistema de Gestión de Marcas")
        
        logger.info("=" * 60)
        logger.info("Iniciando MiAppMarcas Launcher")
        logger.info(f"Directorio base: {BASE_DIR}")
        logger.info(f"Python embebido: {PYTHON_DIR}")
        logger.info(f"Entorno virtual: {VENV_DIR}")
        logger.info(f"Aplicación: {APP_DIR}")
        logger.info("=" * 60)
        
        # Primera ejecución: configurar entorno
        if is_first_run():
            logger.info("Primera ejecución detectada")
            if not setup_environment():
                logger.error("Falló la configuración inicial")
                input("\nPresiona Enter para salir...")
                sys.exit(1)
        else:
            logger.info("Entorno ya configurado, saltando setup")
            print("  ✅ Entorno ya configurado\n")
        
        # Iniciar Streamlit
        result = start_streamlit()
        
        if result is None:
            logger.error("No se pudo iniciar Streamlit")
            input("\nPresiona Enter para salir...")
            sys.exit(1)
        
        # Abrir navegador
        open_browser()
        
        # Mensaje final
        print("\n" + "=" * 60)
        print("  🎉 ¡MiAppMarcas está ejecutándose!")
        print(f"  🌐 URL: {STREAMLIT_URL}")
        print("\n  💡 Consejos:")
        print("     - Mantén esta ventana abierta")
        print("     - Para cerrar, cierra esta ventana")
        print("     - Revisa launcher.log si hay problemas")
        print("=" * 60 + "\n")
        
        logger.info("Launcher completado exitosamente")
        
        # Mantener el proceso vivo si es necesario
        if result != "already_running" and result is not None:
            print("  Presiona Ctrl+C para detener el servidor\n")
            try:
                result.wait()
            except KeyboardInterrupt:
                print("\n  🛑 Deteniendo servidor...")
                result.terminate()
                result.wait(timeout=5)
                print("  ✅ Servidor detenido\n")
        else:
            input("\n  Presiona Enter para cerrar esta ventana...\n")
        
    except KeyboardInterrupt:
        print("\n\n  🛑 Operación cancelada por el usuario")
        logger.info("Launcher cancelado por usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error no manejado: {e}", exc_info=True)
        print(f"\n❌ Error inesperado: {e}")
        print(f"   Revisa {LOG_FILE} para más detalles\n")
        input("\nPresiona Enter para salir...")
        sys.exit(1)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()
