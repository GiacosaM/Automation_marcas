#!/usr/bin/env python3
"""
Script para debuggar la conexión a Supabase y queries
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import crear_conexion, convertir_query_boolean, usar_supabase
from supabase_connection import crear_conexion_postgres

def test_connection():
    """Test básico de conexión y queries"""
    print("=== TEST DE CONEXIÓN Y QUERIES ===")
    
    # Verificar si estamos usando Supabase
    print(f"¿Usando Supabase?: {usar_supabase()}")
    
    try:
        # Crear conexión
        conn = crear_conexion()
        print(f"✓ Conexión creada exitosamente: {type(conn)}")
        
        # Test de query simple
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boletines")
        total = cursor.fetchone()[0]
        print(f"✓ Total boletines: {total}")
        
        # Test de query con boolean conversion
        query_original = "SELECT COUNT(*) FROM boletines WHERE reporte_generado = 1"
        query_convertida = convertir_query_boolean(query_original)
        print(f"Query original: {query_original}")
        print(f"Query convertida: {query_convertida}")
        
        # Ejecutar query convertida
        cursor.execute(query_convertida)
        generados = cursor.fetchone()[0]
        print(f"✓ Reportes generados: {generados}")
        
        # Test con fecha compleja
        query_fecha_compleja = """
            SELECT COUNT(*) FROM boletines 
            WHERE reporte_enviado = 0 
            AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
            AND date(substr(fecha_boletin, 7, 4) || '-' || 
                     substr(fecha_boletin, 4, 2) || '-' || 
                     substr(fecha_boletin, 1, 2), '+30 days') >= date('now')
        """
        query_convertida_compleja = convertir_query_boolean(query_fecha_compleja)
        print(f"Query fecha compleja original: {query_fecha_compleja.strip()}")
        print(f"Query fecha compleja convertida: {query_convertida_compleja.strip()}")
        
        # Test con fecha
        query_fecha_original = "SELECT COUNT(*) FROM boletines WHERE fecha_alta >= date('now', '-30 days')"
        query_fecha_convertida = convertir_query_boolean(query_fecha_original)
        print(f"Query fecha original: {query_fecha_original}")
        print(f"Query fecha convertida: {query_fecha_convertida}")
        
        # Ejecutar query de fecha
        cursor.execute(query_fecha_convertida)
        recientes = cursor.fetchone()[0]
        print(f"✓ Boletines últimos 30 días: {recientes}")
        
        # Test con reporte_enviado
        query_enviados = convertir_query_boolean("SELECT COUNT(*) FROM boletines WHERE reporte_enviado = 1")
        print(f"Query enviados: {query_enviados}")
        cursor.execute(query_enviados)
        enviados = cursor.fetchone()[0]
        print(f"✓ Reportes enviados: {enviados}")
        
        cursor.close()
        conn.close()
        print("✓ Conexión cerrada exitosamente")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
