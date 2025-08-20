"""
Script para probar el rendimiento de las consultas SQL.
Este script ejecuta consultas con y sin optimización y compara los tiempos.
"""
import os
import sys
import time
import json
import logging
import pandas as pd
from datetime import datetime

# Agregar directorio raíz al path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("performance_test.log")
    ]
)

# Importar funciones originales y optimizadas
try:
    from database import crear_conexion, obtener_clientes
    from src.utils.db_optimizations import obtener_clientes_optimizado
    logging.info("✅ Módulos importados correctamente")
except ImportError as e:
    logging.error(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

class PerformanceTester:
    """Clase para probar el rendimiento de las consultas SQL"""
    
    def __init__(self):
        self.results = []
        self.conn = None
    
    def setup(self):
        """Preparar conexión a la base de datos"""
        try:
            self.conn = crear_conexion()
            return True
        except Exception as e:
            logging.error(f"❌ Error al crear conexión: {e}")
            return False
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.conn:
            self.conn.close()
    
    def test_original_query(self):
        """Probar consulta original"""
        if not self.conn:
            return None
        
        try:
            start_time = time.time()
            rows, columns = obtener_clientes(self.conn)
            end_time = time.time()
            
            execution_time = end_time - start_time
            row_count = len(rows)
            
            return {
                "type": "original",
                "query": "obtener_clientes",
                "rows": row_count,
                "time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"❌ Error en consulta original: {e}")
            return None
    
    def test_optimized_query(self, page=1, page_size=50):
        """Probar consulta optimizada"""
        if not self.conn:
            return None
        
        try:
            start_time = time.time()
            rows, columns, pagination = obtener_clientes_optimizado(self.conn, page, page_size)
            end_time = time.time()
            
            execution_time = end_time - start_time
            row_count = len(rows)
            
            return {
                "type": "optimized",
                "query": "obtener_clientes_optimizado",
                "rows": row_count,
                "total_rows": pagination["total_records"],
                "page": page,
                "page_size": page_size,
                "time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"❌ Error en consulta optimizada: {e}")
            return None
    
    def run_comparison_test(self, iterations=5):
        """Ejecutar prueba comparativa"""
        logging.info(f"Iniciando prueba comparativa con {iterations} iteraciones...")
        
        if not self.setup():
            return False
        
        results = {
            "original": [],
            "optimized": []
        }
        
        try:
            # Pruebas con consulta original
            logging.info("Ejecutando consultas originales...")
            for i in range(iterations):
                result = self.test_original_query()
                if result:
                    results["original"].append(result)
                    logging.info(f"  Iteración {i+1}: {result['rows']} filas en {result['time']:.4f}s")
            
            # Pruebas con consulta optimizada
            logging.info("Ejecutando consultas optimizadas...")
            for i in range(iterations):
                result = self.test_optimized_query()
                if result:
                    results["optimized"].append(result)
                    logging.info(f"  Iteración {i+1}: {result['rows']}/{result['total_rows']} filas en {result['time']:.4f}s")
            
            # Calcular estadísticas
            if results["original"] and results["optimized"]:
                orig_times = [r["time"] for r in results["original"]]
                opt_times = [r["time"] for r in results["optimized"]]
                
                orig_avg = sum(orig_times) / len(orig_times)
                opt_avg = sum(opt_times) / len(opt_times)
                
                improvement = ((orig_avg - opt_avg) / orig_avg) * 100
                
                logging.info("\n--- RESULTADOS ---")
                logging.info(f"Original: {orig_avg:.4f}s (promedio)")
                logging.info(f"Optimizada: {opt_avg:.4f}s (promedio)")
                logging.info(f"Mejora: {improvement:.2f}%")
                
                # Guardar resultados
                self.results = results
                self.save_results()
                
                return True
        except Exception as e:
            logging.error(f"❌ Error en prueba comparativa: {e}")
        finally:
            self.cleanup()
        
        return False
    
    def save_results(self):
        """Guardar resultados en archivo JSON"""
        if not self.results:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_results_{timestamp}.json"
            
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=4)
            
            logging.info(f"✅ Resultados guardados en {filename}")
        except Exception as e:
            logging.error(f"❌ Error al guardar resultados: {e}")

def main():
    """Función principal"""
    print("""
    =========================================
    🔍 Test de Rendimiento de Consultas SQL
    =========================================
    Este script ejecuta consultas con y sin 
    optimización y compara los tiempos.
    """)
    
    # Crear y ejecutar el tester
    tester = PerformanceTester()
    tester.run_comparison_test()

if __name__ == "__main__":
    main()
