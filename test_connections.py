#!/usr/bin/env python3
"""
Script para probar diferentes métodos de conexión a Supabase
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

def test_supabase_sdk():
    """Test usando el SDK de Supabase"""
    print("=== TEST CON SDK DE SUPABASE ===")
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        print(f"URL: {url}")
        print(f"Key: {key[:20]}...")
        
        supabase = create_client(url, key)
        
        # Test básico
        result = supabase.table('boletines').select('count').execute()
        print(f"✓ SDK funcionando. Respuesta: {result}")
        
        return True
    except Exception as e:
        print(f"✗ Error con SDK: {e}")
        return False

def test_postgres_direct():
    """Test usando conexión directa a PostgreSQL"""
    print("\n=== TEST CON CONEXIÓN DIRECTA POSTGRESQL ===")
    try:
        # Credenciales actuales
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boletines")
        count = cursor.fetchone()[0]
        print(f"✓ Conexión directa funcionando. Boletines: {count}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Error con conexión directa: {e}")
        return False

def test_postgres_with_pooler():
    """Test usando conexión con connection pooler"""
    print("\n=== TEST CON CONNECTION POOLER ===")
    try:
        # Intentar con puerto 6543 (connection pooler)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=6543,  # Puerto del connection pooler
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boletines")
        count = cursor.fetchone()[0]
        print(f"✓ Connection pooler funcionando. Boletines: {count}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Error con connection pooler: {e}")
        return False

if __name__ == "__main__":
    print("Verificando métodos de conexión a Supabase...\n")
    
    # Mostrar variables de entorno (sin mostrar contraseñas completas)
    print("Variables de entorno:")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
    print(f"DB_HOST: {os.getenv('DB_HOST')}")
    print(f"DB_USER: {os.getenv('DB_USER')}")
    print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')[:5]}...")
    print()
    
    # Test diferentes métodos
    sdk_ok = test_supabase_sdk()
    direct_ok = test_postgres_direct()
    pooler_ok = test_postgres_with_pooler()
    
    print("\n=== RESUMEN ===")
    print(f"SDK de Supabase: {'✓' if sdk_ok else '✗'}")
    print(f"Conexión directa: {'✓' if direct_ok else '✗'}")
    print(f"Connection pooler: {'✓' if pooler_ok else '✗'}")
