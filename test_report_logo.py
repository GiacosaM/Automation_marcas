#!/usr/bin/env python3
"""
Script de prueba para verificar que el generador de reportes usa correctamente
el logo desde la ruta de assets.
"""

import os
import sqlite3
import logging
from paths import get_logo_path, inicializar_assets, get_db_path, get_assets_dir
from report_generator import ReportGenerator

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_logo_path():
    """Prueba que la función get_logo_path() retorna una ruta válida al logo."""
    # Asegurarnos de inicializar los assets
    inicializar_assets()
    
    # Obtener la ruta al logo
    logo_path = get_logo_path()
    
    # Verificar que la ruta no es None
    assert logo_path is not None, "La ruta al logo no debería ser None"
    
    # Verificar que la ruta existe
    assert os.path.exists(logo_path), f"La ruta al logo no existe: {logo_path}"
    
    logger.info(f"✅ Prueba de ruta de logo exitosa: {logo_path}")
    return logo_path

def test_report_generator():
    """Prueba que el generador de reportes utiliza correctamente el logo."""
    # Crear un generador de reportes sin especificar ruta al logo
    generator = ReportGenerator()
    
    # Validar que puede encontrar el logo
    assert generator._validate_watermark() is True, "El generador debería encontrar el logo"
    
    # Verificar que la ruta al logo es la esperada (desde assets)
    assets_dir = get_assets_dir()
    expected_prefix = assets_dir
    
    # Verificar que la ruta al logo comienza con el directorio de assets
    # o es una de las rutas alternativas válidas
    valid_logo = (
        generator.watermark_path.startswith(expected_prefix) or
        "marca_agua.jpg" in generator.watermark_path or
        "logo.jpg" in generator.watermark_path
    )
    
    assert valid_logo, f"La ruta del logo debería estar en assets o ser una alternativa válida, pero es: {generator.watermark_path}"
    
    logger.info(f"✅ Prueba de generador de reportes exitosa: {generator.watermark_path}")
    return generator.watermark_path

if __name__ == "__main__":
    print("\n===== PRUEBA DE INTEGRACIÓN DE LOGO EN REPORTES =====")
    print("🔍 Iniciando pruebas de logo en reportes")
    
    try:
        # Probar la función get_logo_path()
        logo_path = test_logo_path()
        print(f"✅ Logo encontrado en: {logo_path}")
        
        # Probar el generador de reportes
        report_logo = test_report_generator()
        print(f"✅ Logo que usará el reporte: {report_logo}")
        
        print("\n===== RESULTADOS =====")
        print("✅ Directorio de assets: ", get_assets_dir())
        print("✅ Ruta del logo: ", logo_path)
        print("✅ Ruta que usará el reporte: ", report_logo)
        print("\n✅ TODAS LAS PRUEBAS EXITOSAS")
        print("=========================================")
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
        raise