import sys
import os

# Simular el comportamiento de get_base_dir() cuando se ejecuta como exe
def simular_get_base_dir():
    # Cuando es un ejecutable empaquetado, sys.executable apunta al .exe
    # Para MiAppMarcas.exe en packaging\build_release\MiAppMarcas\app\
    simulated_executable = r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app\MiAppMarcas.exe'
    base_dir = os.path.dirname(simulated_executable)
    return base_dir

def simular_get_data_dir():
    base_dir = simular_get_base_dir()
    # La función busca primero una ubicación específica para Martin, luego usa base_dir
    if os.path.exists("/Users/martingiacosa/Desktop/MiAppMarcas"):
        data_dir = "/Users/martingiacosa/Desktop/MiAppMarcas"
    else:
        data_dir = base_dir
    return data_dir

def simular_get_db_path():
    return os.path.join(simular_get_data_dir(), "boletines.db")

print("=== SIMULACIÓN DE RUTAS DEL EJECUTABLE ===")
print(f"Base dir simulado: {simular_get_base_dir()}")
print(f"Data dir simulado: {simular_get_data_dir()}")
print(f"DB path simulado: {simular_get_db_path()}")
print(f"¿Existe el archivo DB?: {os.path.exists(simular_get_db_path())}")

# Verificar si el archivo existe en la ruta actual
ruta_real = r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app\boletines.db'
print(f"\nRuta real de la BD: {ruta_real}")
print(f"¿Existe la BD real?: {os.path.exists(ruta_real)}")

# Comparar
if simular_get_db_path() != ruta_real:
    print(f"\n❌ PROBLEMA: La aplicación busca en: {simular_get_db_path()}")
    print(f"❌ Pero la BD real está en: {ruta_real}")
else:
    print("✅ Las rutas coinciden")

# Verificar también si existe una BD en el directorio de datos
bd_simulada = simular_get_db_path()
if os.path.exists(bd_simulada):
    print(f"\n✅ La BD existe en la ruta simulada: {bd_simulada}")
else:
    print(f"\n❌ La BD NO existe en la ruta simulada: {bd_simulada}")
    
# Listar archivos en el directorio donde debería estar la BD
dir_simulado = simular_get_data_dir()
print(f"\nArchivos en {dir_simulado}:")
if os.path.exists(dir_simulado):
    for archivo in os.listdir(dir_simulado):
        print(f"  - {archivo}")
else:
    print("  (El directorio no existe)")