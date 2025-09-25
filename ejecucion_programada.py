#!/usr/bin/env python3
# ejecucion_programada.py

"""
Script para la ejecución programada de la verificación de titulares sin reportes.
Ideal para ser ejecutado por cron o cualquier otro programador de tareas.

Ejemplo de configuración cron para ejecutar el primer día de cada mes a las 8 AM:
0 8 1 * * cd /ruta/al/proyecto && python3 ejecucion_programada.py >> verificacion_log.txt 2>&1
"""

import os
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verificacion_automatica.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ejecucion_programada')

def main():
    """Función principal para la ejecución programada"""
    logger.info("=" * 80)
    logger.info(f"INICIANDO VERIFICACIÓN AUTOMÁTICA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        # Asegurarnos de que estamos en el directorio correcto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        logger.info(f"Directorio de trabajo: {os.getcwd()}")
        
        # Importar la función de verificación
        from verificar_titulares_sin_reportes import ejecutar_verificacion_periodica
        
        # Ejecutar la verificación
        resultado = ejecutar_verificacion_periodica()
        
        # Registrar resultados
        logger.info(f"Resultado de la verificación: {resultado}")
        logger.info(f"Titulares con marcas sin reportes: {resultado.get('titulares_con_marcas_sin_reportes', 'N/A')}")
        logger.info(f"Emails enviados: {resultado.get('emails_enviados', 'N/A')}")
        logger.info(f"Errores: {resultado.get('errores', 'N/A')}")
        
        # Indicar finalización exitosa
        logger.info("Verificación automática completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error durante la ejecución programada: {e}", exc_info=True)
    
    finally:
        logger.info("=" * 80)
        logger.info(f"FIN DE VERIFICACIÓN AUTOMÁTICA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

if __name__ == "__main__":
    main()
