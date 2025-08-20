#!/usr/bin/env python3
"""
Script para probar la aplicación paso a paso
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test de importaciones"""
    print("=== TEST DE IMPORTACIONES ===")
    try:
        from database import crear_conexion, usar_supabase
        print("✓ database.py importado")
        
        from supabase_connection import crear_conexion_postgres
        print("✓ supabase_connection.py importado")
        
        return True
    except Exception as e:
        print(f"✗ Error en importaciones: {e}")
        return False

def test_database_connection():
    """Test de conexión usando la función de database.py"""
    print("\n=== TEST DE DATABASE.PY ===")
    try:
        from database import crear_conexion, usar_supabase
        
        print(f"¿Usando Supabase?: {usar_supabase()}")
        
        conn = crear_conexion()
        print(f"✓ Conexión creada: {type(conn)}")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boletines")
        count = cursor.fetchone()[0]
        print(f"✓ Query ejecutada. Boletines: {count}")
        
        cursor.close()
        conn.close()
        print("✓ Conexión cerrada")
        
        return True
    except Exception as e:
        print(f"✗ Error en database.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_function():
    """Test de la función get_dashboard_data"""
    print("\n=== TEST DE FUNCIÓN DASHBOARD ===")
    try:
        from database import crear_conexion
        from dashboard import get_dashboard_data
        
        conn = crear_conexion()
        data = get_dashboard_data(conn)
        print(f"✓ Dashboard data obtenida: {list(data.keys())}")
        conn.close()
        
        return True
    except Exception as e:
        print(f"✗ Error en dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Verificando aplicación paso a paso...\n")
    
    imports_ok = test_imports()
    if not imports_ok:
        print("Fallo en importaciones, abortando.")
        sys.exit(1)
    
    db_ok = test_database_connection()
    dashboard_ok = test_dashboard_function() if db_ok else False
    
    print("\n=== RESUMEN FINAL ===")
    print(f"Importaciones: {'✓' if imports_ok else '✗'}")
    print(f"Conexión DB: {'✓' if db_ok else '✗'}")
    print(f"Dashboard: {'✓' if dashboard_ok else '✗'}")
