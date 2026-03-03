import sys
import os
sys.path.append(r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app')

from paths import get_db_path, get_base_dir, get_data_dir

print("=== DEPURACIÓN DE RUTAS ===")
print(f"Base dir: {get_base_dir()}")
print(f"Data dir: {get_data_dir()}")
print(f"DB path: {get_db_path()}")
print(f"¿Existe el archivo DB?: {os.path.exists(get_db_path())}")

# Verificar si el archivo existe en la ruta actual
ruta_real = r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app\boletines.db'
print(f"\nRuta real de la BD: {ruta_real}")
print(f"¿Existe la BD real?: {os.path.exists(ruta_real)}")

# Comparar
if get_db_path() != ruta_real:
    print(f"\n❌ PROBLEMA: La aplicación busca en: {get_db_path()}")
    print(f"❌ Pero la BD real está en: {ruta_real}")
else:
    print("✅ Las rutas coinciden")