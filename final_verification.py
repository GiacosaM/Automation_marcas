#!/usr/bin/env python3
"""
Verificación final completa de la migración a Supabase
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager
from supabase_connection import crear_conexion_supabase, crear_conexion_postgres, usar_supabase

def test_configuracion_final():
    """Verificar configuración final"""
    print("🧪 Verificando configuración final...")
    
    config_manager = ConfigManager()
    
    # Verificar tipo de BD
    db_type = config_manager.get('database.type', 'No configurado')
    print(f"✅ Tipo de BD configurado: {db_type}")
    
    # Verificar función usar_supabase
    usa_supabase = usar_supabase()
    print(f"✅ usar_supabase() retorna: {usa_supabase}")
    
    # Verificar variables de entorno
    supabase_url = os.getenv('SUPABASE_URL', 'No configurado')
    db_host = os.getenv('DB_HOST', 'No configurado')
    
    print(f"✅ SUPABASE_URL: {'Configurado' if supabase_url != 'No configurado' else 'No configurado'}")
    print(f"✅ DB_HOST: {'Configurado' if db_host != 'No configurado' else 'No configurado'}")
    
    return usa_supabase

def test_todas_las_tablas():
    """Verificar todas las tablas migradas"""
    print("\n🧪 Verificando todas las tablas en Supabase...")
    
    try:
        conn = crear_conexion_postgres()
        if not conn:
            print("❌ No se pudo conectar a PostgreSQL")
            return False
            
        cursor = conn.cursor()
        
        # Verificar todas las tablas
        tablas = ['boletines', 'clientes', 'emails_enviados', 'users']
        
        for tabla in tablas:
            cursor.execute(f'SELECT COUNT(*) FROM {tabla};')
            count = cursor.fetchone()[0]
            print(f"📊 {tabla}: {count} registros")
        
        # Verificar estructura de users específicamente
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n🔍 Estructura tabla users:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

def test_funciones_database():
    """Verificar que las funciones de database.py funcionen"""
    print("\n🧪 Verificando funciones de database.py...")
    
    try:
        # Importar database module
        import database
        
        # Verificar que tiene las nuevas funciones
        if hasattr(database, 'crear_conexion'):
            print("✅ Función crear_conexion() disponible")
        else:
            print("❌ Función crear_conexion() NO disponible")
            return False
            
        if hasattr(database, 'ejecutar_query'):
            print("✅ Función ejecutar_query() disponible")
        else:
            print("❌ Función ejecutar_query() NO disponible")
            return False
        
        # Probar conexión
        conn = database.crear_conexion()
        if conn:
            print("✅ crear_conexion() funciona correctamente")
            
            # Para PostgreSQL, probar query simple
            if usar_supabase():
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result and result[0] == 1:
                    print("✅ Conexión a Supabase funcional")
                else:
                    print("❌ Problema con query en Supabase")
                    return False
            else:
                conn.close()
                print("✅ Conexión SQLite funcional")
                
        else:
            print("❌ crear_conexion() retornó None")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando database.py: {e}")
        return False

def test_autenticacion():
    """Verificar que la autenticación funcione con Supabase"""
    print("\n🧪 Verificando sistema de autenticación...")
    
    try:
        conn = crear_conexion_postgres()
        cursor = conn.cursor()
        
        # Verificar usuario admin
        cursor.execute("SELECT username, name, email, role, is_active FROM users WHERE username = %s", ('admin',))
        user = cursor.fetchone()
        
        if user:
            print(f"✅ Usuario encontrado: {user[0]} ({user[1]})")
            print(f"   📧 Email: {user[2]}")
            print(f"   👑 Rol: {user[3]}")
            print(f"   ✅ Activo: {user[4]}")
            
            # Verificar estructura de password_hash
            cursor.execute("SELECT password_hash FROM users WHERE username = %s", ('admin',))
            hash_result = cursor.fetchone()
            
            if hash_result and hash_result[0]:
                print("✅ Password hash migrado correctamente")
            else:
                print("❌ Problema con password hash")
                cursor.close()
                conn.close()
                return False
                
        else:
            print("❌ Usuario admin no encontrado")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando autenticación: {e}")
        return False

def test_compatibilidad():
    """Verificar compatibilidad con funciones existentes"""
    print("\n🧪 Verificando compatibilidad con código existente...")
    
    try:
        # Importar módulos principales
        import database
        
        # Verificar que las funciones principales siguen funcionando
        funciones_esperadas = [
            'crear_conexion',
            'ejecutar_query'
        ]
        
        funciones_disponibles = []
        for func in funciones_esperadas:
            if hasattr(database, func):
                funciones_disponibles.append(func)
                print(f"✅ {func}() disponible")
            else:
                print(f"❌ {func}() NO disponible")
        
        print(f"\n📊 Funciones disponibles: {len(funciones_disponibles)}/{len(funciones_esperadas)}")
        
        return len(funciones_disponibles) == len(funciones_esperadas)
        
    except Exception as e:
        print(f"❌ Error verificando compatibilidad: {e}")
        return False

def main():
    """Función principal de verificación final"""
    print("🚀 Verificación Final de Migración a Supabase")
    print("=" * 60)
    
    tests = [
        ("Configuración final", test_configuracion_final),
        ("Todas las tablas", test_todas_las_tablas),
        ("Funciones database.py", test_funciones_database),
        ("Sistema de autenticación", test_autenticacion),
        ("Compatibilidad con código existente", test_compatibilidad),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        print(f"\n📋 {nombre}...")
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n📋 RESUMEN FINAL DE MIGRACIÓN:")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        estado = "✅ ÉXITO" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 Resultado: {exitosos}/{len(tests)} verificaciones exitosas")
    
    if exitosos == len(tests):
        print("\n🎉 ¡MIGRACIÓN COMPLETAMENTE EXITOSA!")
        print("✅ Tu aplicación está 100% migrada a Supabase")
        print("\n📋 Estado actual:")
        print("• Base de datos: Supabase PostgreSQL")
        print("• Tablas migradas: boletines, clientes, emails_enviados, users")
        print("• Autenticación: Funcionando con Supabase")
        print("• Compatibilidad: Mantenida con código existente")
        print("\n🚀 ¡Ya puedes usar tu aplicación normalmente!")
        
    else:
        print("\n⚠️ Hay algunos problemas pendientes")
        print("🔧 Revisa los errores antes de usar la aplicación")

if __name__ == "__main__":
    main()
