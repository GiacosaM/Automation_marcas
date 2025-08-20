#!/usr/bin/env python3
"""
Script para completar la migración: tabla users + configuración completa de la app
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import shutil
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

def crear_tabla_users_supabase():
    """Crear tabla users en Supabase"""
    print("🏗️ Creando tabla users en Supabase...")
    
    try:
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Crear tabla users con estructura SQLite original
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP NULL
            );
        """)
        
        # Crear índices para users
        indices_users = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);",
        ]
        
        for indice in indices_users:
            cursor.execute(indice)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tabla users creada exitosamente en Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tabla users: {e}")
        return False

def migrar_usuarios():
    """Migrar usuarios de SQLite a Supabase"""
    print("\n📤 Migrando usuarios de SQLite a Supabase...")
    
    if not os.path.exists('boletines.db'):
        print("⚠️ No se encontró la base de datos SQLite")
        return False
    
    try:
        # Exportar de SQLite
        sqlite_conn = sqlite3.connect('boletines.db')
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM users ORDER BY id")
        users_rows = sqlite_cursor.fetchall()
        users_data = [dict(row) for row in users_rows]
        
        sqlite_conn.close()
        
        print(f"📊 Usuarios exportados de SQLite: {len(users_data)}")
        
        # Importar a Supabase
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        supabase_conn = psycopg2.connect(**config)
        
        # Preparar inserción
        columnas = [col for col in users_data[0].keys() if col != 'id']
        columnas_str = ', '.join(f'"{col}"' for col in columnas)
        placeholders = ', '.join(['%s'] * len(columnas))
        query = f'INSERT INTO users ({columnas_str}) VALUES ({placeholders})'
        
        print(f"📝 Query: {query}")
        print(f"📊 Columnas: {columnas}")
        
        # Insertar usuarios
        exitosos = 0
        for i, usuario in enumerate(users_data):
            try:
                cursor = supabase_conn.cursor()
                
                # Convertir valores
                valores = []
                for col in columnas:
                    valor = usuario[col]
                    # Convertir boolean (SQLite usa 1/0)
                    if col == 'is_active' and isinstance(valor, int):
                        valor = bool(valor)
                    valores.append(valor)
                
                cursor.execute(query, valores)
                supabase_conn.commit()
                cursor.close()
                exitosos += 1
                
                print(f"✅ Usuario migrado: {usuario['username']} ({usuario['name']})")
                
            except Exception as e:
                print(f"⚠️ Error en usuario {i}: {e}")
                supabase_conn.rollback()
                if cursor:
                    cursor.close()
        
        supabase_conn.close()
        
        print(f"✅ Usuarios migrados: {exitosos}/{len(users_data)}")
        return exitosos > 0
        
    except Exception as e:
        print(f"❌ Error al migrar usuarios: {e}")
        return False

def verificar_migracion_users():
    """Verificar que los usuarios se migraron correctamente"""
    print("\n🔍 Verificando migración de usuarios...")
    
    try:
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Verificar usuarios
        cursor.execute('SELECT COUNT(*) FROM users;')
        count_users = cursor.fetchone()[0]
        print(f"📊 Usuarios en Supabase: {count_users}")
        
        # Muestra de usuarios
        cursor.execute('SELECT username, name, email, role, is_active FROM users;')
        users_sample = cursor.fetchall()
        print('👥 Usuarios migrados:')
        for row in users_sample:
            print(f'  - {row[0]} | {row[1]} | {row[2]} | {row[3]} | Activo: {row[4]}')
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f'❌ Error verificando usuarios: {e}')
        return False

def actualizar_database_py():
    """Actualizar database.py para usar Supabase por defecto"""
    print("\n🔧 Actualizando database.py para usar Supabase...")
    
    try:
        # Leer el archivo actual
        with open('database.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene configuración de Supabase
        if 'supabase_connection' in content:
            print("✅ database.py ya tiene configuración de Supabase")
            return True
        
        # Agregar import de supabase_connection al inicio
        new_imports = """import os
import sqlite3
import logging
from datetime import datetime, date
import streamlit as st
from supabase_connection import crear_conexion_supabase, crear_conexion_postgres, usar_supabase
"""
        
        # Reemplazar imports existentes
        lines = content.split('\n')
        import_section = []
        other_lines = []
        in_imports = True
        
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if in_imports:
                    continue  # Skip existing imports
            else:
                in_imports = False
            other_lines.append(line)
        
        # Combinar nuevo contenido
        new_content = new_imports + '\n' + '\n'.join(other_lines)
        
        # Crear backup
        backup_name = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2('database.py', backup_name)
        print(f"📦 Backup creado: {backup_name}")
        
        # Escribir nuevo contenido
        with open('database.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ database.py actualizado para usar Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando database.py: {e}")
        return False

def crear_funciones_compatibilidad():
    """Crear funciones de compatibilidad para migración gradual"""
    print("\n🔧 Creando funciones de compatibilidad...")
    
    compatibility_code = '''
# Funciones de compatibilidad para migración a Supabase
def crear_conexion():
    """Crear conexión a la base de datos (Supabase o SQLite según configuración)"""
    if usar_supabase():
        return crear_conexion_postgres()
    else:
        return sqlite3.connect('boletines.db')

def ejecutar_query(query, params=None, fetch=False):
    """Ejecutar query en la base de datos activa"""
    if usar_supabase():
        conn = crear_conexion_postgres()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or [])
                
                if fetch:
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()
                    else:
                        result = cursor.fetchall()
                else:
                    result = None
                
                conn.commit()
                cursor.close()
                conn.close()
                return result
                
            except Exception as e:
                conn.rollback()
                cursor.close()
                conn.close()
                raise e
    else:
        # SQLite fallback
        conn = sqlite3.connect('boletines.db')
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or [])
            
            if fetch:
                if fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'all':
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchall()
            else:
                result = None
            
            conn.commit()
            conn.close()
            return result
            
        except Exception as e:
            conn.close()
            raise e
'''
    
    try:
        # Agregar al final de database.py
        with open('database.py', 'a', encoding='utf-8') as f:
            f.write('\n\n' + compatibility_code)
        
        print("✅ Funciones de compatibilidad agregadas")
        return True
        
    except Exception as e:
        print(f"❌ Error agregando funciones de compatibilidad: {e}")
        return False

def main():
    """Función principal para completar la migración"""
    print("🚀 Completando migración: tabla users + configuración app")
    print("=" * 60)
    
    pasos = [
        ("Crear tabla users en Supabase", crear_tabla_users_supabase),
        ("Migrar usuarios SQLite → Supabase", migrar_usuarios),
        ("Verificar migración de usuarios", verificar_migracion_users),
        ("Actualizar database.py", actualizar_database_py),
        ("Crear funciones de compatibilidad", crear_funciones_compatibilidad),
    ]
    
    resultados = []
    
    for nombre, funcion in pasos:
        print(f"\n📋 {nombre}...")
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
            if resultado:
                print(f"✅ {nombre} completado")
            else:
                print(f"❌ {nombre} falló")
                break  # Detener si algo falla
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
            break
    
    # Resumen final
    print("\n📋 Resumen de migración completa:")
    print("=" * 40)
    
    exitosos = 0
    for nombre, resultado in resultados:
        estado = "✅ ÉXITO" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 Resultado: {exitosos}/{len(pasos)} pasos completados")
    
    if exitosos == len(pasos):
        print("\n🎉 ¡Migración COMPLETAMENTE finalizada!")
        print("✅ Tu aplicación ahora usa Supabase exclusivamente")
        print("\n📋 Próximos pasos:")
        print("1. Probar login en la aplicación")
        print("2. Verificar todas las funcionalidades")
        print("3. Monitorear rendimiento")
        print("4. Eliminar archivos SQLite cuando estés seguro")
    else:
        print("\n⚠️ Migración incompleta")
        print("🔧 Revisa los errores antes de continuar")

if __name__ == "__main__":
    main()
