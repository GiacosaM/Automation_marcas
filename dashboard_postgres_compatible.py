#!/usr/bin/env python3
"""
Solución simple: crear una query compatible directamente para el dashboard
En lugar de hacer conversión automática compleja, vamos a reemplazar 
las queries problemáticas específicamente en los archivos del dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Vamos a crear una función que simplemente use queries ya compatibles con PostgreSQL
def get_dashboard_data_postgres_compatible(conn):
    """Función simplificada para obtener datos del dashboard compatible con PostgreSQL"""
    cursor = conn.cursor()
    
    # Estadísticas básicas
    cursor.execute("SELECT COUNT(*) FROM boletines")
    total_boletines = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_generado = TRUE")
    reportes_generados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = TRUE")
    reportes_enviados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT titular) FROM clientes")
    total_clientes = cursor.fetchone()[0]
    
    # Para fechas complejas, vamos a usar una aproximación más simple
    # En lugar de usar julianday, calculemos directamente días usando intervalos de PostgreSQL
    
    # Reportes próximos a vencer (entre 23 y 30 días desde fecha del boletín)
    query_proximos_vencer = """
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_enviado = FALSE 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND LENGTH(fecha_boletin) = 10
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '23 days' <= CURRENT_DATE
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' >= CURRENT_DATE
    """
    cursor.execute(query_proximos_vencer)
    proximos_vencer = cursor.fetchone()[0]
    
    # Reportes vencidos (más de 30 días)
    query_vencidos = """
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_enviado = FALSE 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND LENGTH(fecha_boletin) = 10
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' < CURRENT_DATE
    """
    cursor.execute(query_vencidos)
    reportes_vencidos = cursor.fetchone()[0]
    
    # Detalles de reportes próximos a vencer
    query_detalles_proximos = """
        SELECT numero_boletin, titular, fecha_boletin,
               EXTRACT(EPOCH FROM (TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' - CURRENT_DATE))/86400 as dias_restantes
        FROM boletines 
        WHERE reporte_enviado = FALSE 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND LENGTH(fecha_boletin) = 10
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '23 days' <= CURRENT_DATE
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' >= CURRENT_DATE
        ORDER BY dias_restantes ASC
        LIMIT 10
    """
    cursor.execute(query_detalles_proximos)
    detalles_proximos_vencer = cursor.fetchall()
    
    # Detalles de reportes vencidos
    query_detalles_vencidos = """
        SELECT numero_boletin, titular, fecha_boletin,
               EXTRACT(EPOCH FROM (CURRENT_DATE - (TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days')))/86400 as dias_vencido
        FROM boletines 
        WHERE reporte_enviado = FALSE 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
        AND LENGTH(fecha_boletin) = 10
        AND TO_DATE(fecha_boletin, 'DD/MM/YYYY') + INTERVAL '30 days' < CURRENT_DATE
        ORDER BY dias_vencido DESC
        LIMIT 10
    """
    cursor.execute(query_detalles_vencidos)
    detalles_vencidos = cursor.fetchall()
    
    # Timeline datos (últimos 30 días)
    query_timeline = """
        SELECT fecha_alta::date as fecha, COUNT(*) as cantidad
        FROM boletines 
        WHERE fecha_alta >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY fecha_alta::date
        ORDER BY fecha
    """
    cursor.execute(query_timeline)
    datos_timeline = cursor.fetchall()
    
    # Top titulares
    cursor.execute("""
        SELECT titular, COUNT(*) as cantidad
        FROM boletines
        GROUP BY titular
        ORDER BY cantidad DESC
        LIMIT 10
    """)
    top_titulares = cursor.fetchall()
    
    cursor.close()
    
    return {
        'total_boletines': total_boletines,
        'reportes_generados': reportes_generados,
        'reportes_enviados': reportes_enviados,
        'total_clientes': total_clientes,
        'proximos_vencer': proximos_vencer,
        'reportes_vencidos': reportes_vencidos,
        'detalles_proximos_vencer': detalles_proximos_vencer,
        'detalles_vencidos': detalles_vencidos,
        'datos_timeline': datos_timeline,
        'top_titulares': top_titulares
    }

if __name__ == "__main__":
    # Test de las queries
    from database import crear_conexion
    
    print("=== TEST DE QUERIES POSTGRESQL NATIVAS ===")
    
    try:
        conn = crear_conexion()
        data = get_dashboard_data_postgres_compatible(conn)
        
        print(f"✓ Total boletines: {data['total_boletines']}")
        print(f"✓ Reportes generados: {data['reportes_generados']}")
        print(f"✓ Reportes enviados: {data['reportes_enviados']}")
        print(f"✓ Total clientes: {data['total_clientes']}")
        print(f"✓ Próximos a vencer: {data['proximos_vencer']}")
        print(f"✓ Reportes vencidos: {data['reportes_vencidos']}")
        print(f"✓ Timeline datos: {len(data['datos_timeline'])} entradas")
        print(f"✓ Top titulares: {len(data['top_titulares'])} entradas")
        
        conn.close()
        
        print("\n🎉 ¡Todas las queries funcionan correctamente!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
