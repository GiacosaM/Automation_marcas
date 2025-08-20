"""
Script para inicializar las optimizaciones de rendimiento en la aplicación.
Este script debe ejecutarse una vez para configurar todo el entorno.
"""
import os
import sys
import json
import time
import argparse
import logging
import streamlit as st
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("optimization_init.log")
    ]
)

# Agregar directorio raíz al path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def check_requirements():
    """Verificar que todos los requisitos estén instalados"""
    logging.info("Verificando requisitos...")
    
    try:
        import psycopg2
        import streamlit
        import pandas
        import supabase
        logging.info("✅ Todos los requisitos están instalados")
        return True
    except ImportError as e:
        logging.error(f"❌ Error de requisitos: {e}")
        logging.info("Ejecuta 'pip install -r requirements.txt' para instalar los requisitos")
        return False

def verify_files_exist():
    """Verificar que todos los archivos necesarios existan"""
    logging.info("Verificando archivos necesarios...")
    
    required_files = [
        "src/utils/db_optimizations.py",
        "src/utils/connection_pool.py",
        "src/utils/db_indexer.py",
        "src/ui/pages/optimization.py",
        "src/ui/pages/optimization_config.py",
        "config.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logging.error(f"❌ Faltan archivos necesarios: {', '.join(missing_files)}")
        return False
    else:
        logging.info("✅ Todos los archivos necesarios están presentes")
        return True

def create_performance_log():
    """Crear archivo de log de rendimiento si no existe"""
    logging.info("Configurando log de rendimiento...")
    
    perf_log_path = "performance.log"
    if not os.path.exists(perf_log_path):
        try:
            with open(perf_log_path, "w") as f:
                f.write("# Log de rendimiento de consultas SQL\n")
                f.write("# Formato: FECHA - PERF - FUNCIÓN - TIEMPO\n")
            logging.info(f"✅ Archivo de log de rendimiento creado: {perf_log_path}")
        except Exception as e:
            logging.error(f"❌ Error al crear archivo de log: {e}")
    else:
        logging.info(f"✅ Archivo de log de rendimiento ya existe: {perf_log_path}")

def verify_config():
    """Verificar la configuración"""
    logging.info("Verificando configuración...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Verificar secciones necesarias
        required_sections = ["database", "cache", "use_optimized_pages"]
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            logging.warning(f"⚠️ Faltan secciones en config.json: {', '.join(missing_sections)}")
            
            # Añadir secciones faltantes
            if "database" not in config:
                config["database"] = {
                    "pool_min_connections": 2,
                    "pool_max_connections": 10,
                    "statement_timeout": 10000,
                    "idle_timeout": 60
                }
            
            if "cache" not in config:
                config["cache"] = {
                    "ttl": 60,
                    "dashboard_enabled": True,
                    "lists_enabled": True
                }
            
            if "use_optimized_pages" not in config:
                config["use_optimized_pages"] = True
            
            # Guardar configuración actualizada
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            logging.info("✅ Configuración actualizada")
        else:
            logging.info("✅ Configuración correcta")
        
        return True
    except Exception as e:
        logging.error(f"❌ Error al verificar configuración: {e}")
        return False

def initialize_optimizations():
    """Inicializar todas las optimizaciones"""
    logging.info("Iniciando proceso de optimización...")
    
    # Verificar requisitos
    if not check_requirements():
        return False
    
    # Verificar archivos
    if not verify_files_exist():
        return False
    
    # Verificar configuración
    if not verify_config():
        return False
    
    # Crear log de rendimiento
    create_performance_log()
    
    # Mostrar mensaje de éxito
    logging.info("🎉 Optimizaciones inicializadas correctamente")
    logging.info("\nPróximos pasos:")
    logging.info("1. Ejecuta 'streamlit run app_refactored.py' para iniciar la aplicación")
    logging.info("2. Ve a la sección '⚡ Optimización' en el menú lateral")
    logging.info("3. Ejecuta la creación de índices desde la pestaña 'Índices y Estructura'")
    logging.info("4. Configura las opciones de caché y conexiones según tus necesidades")
    logging.info("\n¡Listo para disfrutar de una aplicación más rápida! 🚀")
    
    return True

if __name__ == "__main__":
    # Mensaje de bienvenida
    print("""
    =========================================================
    🚀 Inicializador de Optimizaciones para Supabase/PostgreSQL
    =========================================================
    Este script configurará todas las optimizaciones para
    mejorar el rendimiento de la aplicación con Supabase.
    """)
    
    # Pedir confirmación
    response = input("¿Deseas continuar? (S/n): ")
    if response.lower() not in ["", "s", "si", "y", "yes"]:
        print("Operación cancelada.")
        sys.exit(0)
    
    # Inicializar optimizaciones
    if initialize_optimizations():
        print("\n✅ Optimizaciones inicializadas correctamente")
    else:
        print("\n❌ Error al inicializar optimizaciones. Revisa el log para más detalles.")
