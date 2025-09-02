import sqlite3
import datetime
from datetime import datetime as dt

# Connect to the database
conn = sqlite3.connect('boletines.db')
cursor = conn.cursor()

# Get today's date
today = dt.now()
print(f"Today's date: {today.strftime('%d/%m/%Y')}")

# Get all bulletins that haven't been reported
cursor.execute("""
    SELECT numero_boletin, titular, fecha_boletin
    FROM boletines 
    WHERE reporte_enviado = 0 
    AND fecha_boletin IS NOT NULL 
    AND fecha_boletin != ''
""")

print("\nUnreported bulletins:")
bulletins = cursor.fetchall()
for row in bulletins:
    numero = row[0]
    titular = row[1]
    fecha_str = row[2]
    print(f"Boletin: {numero}, Titular: {titular}, Fecha: {fecha_str}")

# Now check how many are within the 0-30 day window
cursor.execute("""
    SELECT COUNT(*) 
    FROM boletines 
    WHERE reporte_enviado = 0 
    AND fecha_boletin IS NOT NULL 
    AND fecha_boletin != ''
    AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                   substr(fecha_boletin, 4, 2) || '-' || 
                                   substr(fecha_boletin, 1, 2))) <= 30
    AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                   substr(fecha_boletin, 4, 2) || '-' || 
                                   substr(fecha_boletin, 1, 2))) >= 0
""")
count = cursor.fetchone()[0]
print(f"\nTotal bulletins in 0-30 day range: {count}")

# List the bulletins in the 0-30 day window
cursor.execute("""
    SELECT numero_boletin, titular, fecha_boletin,
           CAST(julianday(date('now')) - 
                julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                              substr(fecha_boletin, 4, 2) || '-' || 
                              substr(fecha_boletin, 1, 2))) AS INTEGER) as dias_transcurridos
    FROM boletines 
    WHERE reporte_enviado = 0 
    AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
    AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                       substr(fecha_boletin, 4, 2) || '-' || 
                                       substr(fecha_boletin, 1, 2))) <= 30
    AND julianday(date('now')) - julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                       substr(fecha_boletin, 4, 2) || '-' || 
                                       substr(fecha_boletin, 1, 2))) >= 0
    ORDER BY dias_transcurridos ASC
""")

print("\nBulletins in 0-30 day range:")
for row in cursor.fetchall():
    numero = row[0]
    titular = row[1]
    fecha_str = row[2]
    dias = row[3]
    print(f"Boletin: {numero}, Titular: {titular}, Fecha: {fecha_str}, Días transcurridos: {dias}")

conn.close()
