import sys
import os
sys.path.append(r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app')

import sqlite3
from email_sender import obtener_estadisticas_envios

conn = sqlite3.connect(r'c:\Users\Iara\Desktop\Automation\Automation_marcas\packaging\build_release\MiAppMarcas\app\boletines.db')
stats = obtener_estadisticas_envios(conn)

print('=== STATS DESDE LA FUNCIÓN DEL EJECUTABLE ===')
print(f'total_reportes: {stats["total_reportes"]}')
print(f'reportes_generados: {stats["reportes_generados"]}')
print(f'reportes_enviados: {stats["reportes_enviados"]}')
print(f'pendientes_revision: {stats["pendientes_revision"]}')
print(f'listos_envio: {stats["listos_envio"]}')

print(f'\n=== EVALUACIÓN DE CONDICIONES ===')
print(f'pendientes_revision == 0: {stats["pendientes_revision"] == 0}')
print(f'listos_envio > 0: {stats["listos_envio"] > 0}')
print(f'¿Debería aparecer el botón?: {stats["pendientes_revision"] == 0 and stats["listos_envio"] > 0}')

conn.close()