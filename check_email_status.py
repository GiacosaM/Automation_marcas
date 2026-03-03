import sqlite3

# Conectar a la base de datos
print("Verificando automation_marcas.db...")
try:
    conn = sqlite3.connect('automation_marcas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tablas en automation_marcas.db: {[t[0] for t in tables]}")
    conn.close()
except Exception as e:
    print(f"Error con automation_marcas.db: {e}")

print("\nVerificando boletines.db en packaging/build_release/MiAppMarcas/app/...")
try:
    db_path = r'packaging\build_release\MiAppMarcas\app\boletines.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tablas en {db_path}: {[t[0] for t in tables]}")
    
    # Si existe la tabla boletines, usamos esta base de datos
    if 'boletines' in [t[0] for t in tables]:
        print(f"\n¡Tabla boletines encontrada en {db_path}!")
        conn = sqlite3.connect(db_path)
        
except Exception as e:
    print(f"Error con {db_path}: {e}")
    conn = sqlite3.connect('boletines.db')

cursor = conn.cursor()

print('=== ESTADÍSTICAS DE INFORMES ===')
cursor.execute("""
    SELECT 
        COUNT(*) as total_reportes,
        COUNT(CASE WHEN reporte_generado = 1 THEN 1 END) as reportes_generados,
        COUNT(CASE WHEN reporte_enviado = 1 THEN 1 END) as reportes_enviados,
        COUNT(CASE WHEN importancia = 'Pendiente' AND reporte_generado = 1 THEN 1 END) as pendientes_revision,
        COUNT(CASE WHEN reporte_generado = 1 AND reporte_enviado = 0 AND importancia IN ('Alta', 'Media', 'Baja') THEN 1 END) as listos_envio
    FROM boletines
""")

stats = cursor.fetchone()
print(f'Total reportes: {stats[0]}')
print(f'Reportes generados: {stats[1]}')
print(f'Reportes enviados: {stats[2]}')
print(f'Pendientes de revisión: {stats[3]}')
print(f'Listos para envío: {stats[4]}')

print('\n=== DETALLE DE IMPORTANCIAS ===')
cursor.execute('SELECT importancia, COUNT(*) FROM boletines WHERE reporte_generado = 1 GROUP BY importancia')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} informes')

print('\n=== INFORMES GENERADOS NO ENVIADOS ===')
cursor.execute('SELECT titular, importancia, reporte_generado, reporte_enviado FROM boletines WHERE reporte_generado = 1 AND reporte_enviado = 0 LIMIT 10')
for row in cursor.fetchall():
    print(f'{row[0]} - Importancia: {row[1]} - Generado: {row[2]} - Enviado: {row[3]}')

conn.close()