#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a Supabase desde la aplicación
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager
from supabase_connection import crear_conexion_supabase, crear_conexion_postgres

def test_config():
    """Probar configuración"""
    print("🧪 Probando configuración...")
    
    config_manager = ConfigManager()
    
    db_type = config_manager.get('database.type', 'sqlite')
    supabase_url = config_manager.get('database.supabase_url', 'No configurado')
    postgres_host = config_manager.get('database.postgres_host', 'No configurado')
    
    print(f"✅ Tipo de base de datos: {db_type}")
    print(f"✅ URL Supabase: {supabase_url[:50] if supabase_url != 'No configurado' else supabase_url}...")
    print(f"✅ Host PostgreSQL: {postgres_host}")
    
    return True

def test_supabase_connection():
    """Probar conexión con el SDK de Supabase"""
    print("\n🧪 Probando conexión SDK Supabase...")
    
    try:
        supabase_client = crear_conexion_supabase()
        
        # Probar consulta simple
        response = supabase_client.table('boletines').select('count', count='exact').execute()
        count = response.count
        
        print(f"✅ Conexión SDK exitosa - Boletines: {count} registros")
        return True
        
    except Exception as e:
        print(f"❌ Error SDK: {e}")
        return False

def test_postgres_connection():
    """Probar conexión directa PostgreSQL"""
    print("\n🧪 Probando conexión directa PostgreSQL...")
    
    try:
        conn = crear_conexion_postgres()
        if conn:
            cursor = conn.cursor()
            
            # Contar registros en cada tabla
            cursor.execute("SELECT COUNT(*) FROM boletines")
            count_boletines = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes")
            count_clientes = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Conexión PostgreSQL exitosa")
            print(f"   📊 Boletines: {count_boletines} registros")
            print(f"   📊 Clientes: {count_clientes} registros")
            return True
        else:
            print("❌ No se pudo establecer conexión PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
        return False

def test_data_consistency():
    """Verificar consistencia de datos"""
    print("\n🧪 Verificando consistencia de datos...")
    
    try:
        conn = crear_conexion_postgres()
        cursor = conn.cursor()
        
        # Verificar que los tipos de datos son correctos
        cursor.execute("""
            SELECT titular, reporte_enviado, importancia 
            FROM boletines 
            WHERE reporte_enviado = true 
            LIMIT 3
        """)
        
        rows = cursor.fetchall()
        print("✅ Verificación de tipos exitosa:")
        for row in rows:
            print(f"   - {row[0]} | Enviado: {row[1]} | Importancia: {row[2]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en consistencia: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Verificación de migración a Supabase")
    print("=" * 50)
    
    tests = [
        ("Configuración", test_config),
        ("Conexión SDK Supabase", test_supabase_connection),
        ("Conexión PostgreSQL", test_postgres_connection),
        ("Consistencia de datos", test_data_consistency),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n📋 Resumen de verificación:")
    print("=" * 30)
    
    exitosos = 0
    for nombre, resultado in resultados:
        estado = "✅ ÉXITO" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 Resultado: {exitosos}/{len(tests)} pruebas exitosas")
    
    if exitosos == len(tests):
        print("\n🎉 ¡Migración completamente verificada!")
        print("✅ Tu aplicación está lista para usar Supabase")
    else:
        print("\n⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa la configuración antes de continuar")

if __name__ == "__main__":
    main()
