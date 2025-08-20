#!/usr/bin/env python3
"""
Script de migración simple de SQLite a Supabase
Sin dependencia de Streamlit
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_configuracion():
    """Verificar que las variables de entorno están configuradas"""
    variables_requeridas = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'DB_HOST',
        'DB_PASSWORD'
    ]
    
    faltantes = []
    for var in variables_requeridas:
        if not os.getenv(var):
            faltantes.append(var)
    
    if faltantes:
        print(f"❌ Faltan variables de entorno: {', '.join(faltantes)}")
        print("📋 Configura el archivo .env con tus credenciales de Supabase")
        return False
    
    print("✅ Configuración verificada")
    return True


def crear_tablas_supabase():
    """Crear tablas en Supabase"""
    print("\n🏗️ Creando estructura de tablas en Supabase...")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Configuración de conexión
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Conectar a PostgreSQL
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Crear tabla boletines - usando estructura SQLite original
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boletines (
                id SERIAL PRIMARY KEY,
                numero_boletin TEXT,
                fecha_boletin TEXT,
                numero_orden TEXT,
                solicitante TEXT,
                agente TEXT,
                numero_expediente TEXT,
                clase TEXT,
                marca_custodia TEXT,
                marca_publicada TEXT,
                clases_acta TEXT,
                reporte_enviado BOOLEAN DEFAULT FALSE,
                fecha_envio_reporte DATE,
                fecha_creacion_reporte DATE,
                reporte_generado BOOLEAN DEFAULT FALSE,
                nombre_reporte TEXT,    
                ruta_reporte TEXT,
                titular TEXT,
                fecha_alta DATE DEFAULT CURRENT_DATE,
                observaciones TEXT,
                importancia TEXT DEFAULT 'Pendiente' 
                    CHECK (importancia IN ('Pendiente', 'Baja', 'Media', 'Alta'))
            );
        """)
        
        # Crear tabla clientes - usando estructura SQLite original
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                titular TEXT UNIQUE,
                email TEXT,
                telefono TEXT,
                direccion TEXT,
                ciudad TEXT,
                fecha_alta DATE DEFAULT CURRENT_DATE,
                fecha_modificacion DATE,
                cuit INTEGER, 
                provincia TEXT
            );
        """)
        
        # Crear tabla emails_enviados - usando estructura SQLite original
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails_enviados (
                id SERIAL PRIMARY KEY,
                destinatario TEXT NOT NULL,
                asunto TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                tipo_email TEXT DEFAULT 'general',
                status TEXT DEFAULT 'pendiente',
                fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                titular TEXT DEFAULT NULL, 
                periodo_notificacion TEXT DEFAULT NULL
            );
        
        # Crear índices - usando índices similares a SQLite
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_boletines ON boletines(numero_boletin, numero_orden, titular);",
            "CREATE INDEX IF NOT EXISTS idx_boletines_titular ON boletines(titular);",
            "CREATE INDEX IF NOT EXISTS idx_boletines_importancia ON boletines(importancia);",
            "CREATE INDEX IF NOT EXISTS idx_clientes_titular ON clientes(titular);",
            "CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);",
            "CREATE INDEX IF NOT EXISTS idx_emails_titular ON emails_enviados(titular);",
            "CREATE INDEX IF NOT EXISTS idx_emails_status ON emails_enviados(status);",
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tablas creadas exitosamente en Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def exportar_datos_sqlite():
    """Exportar datos desde SQLite"""
    print("\n📤 Exportando datos desde SQLite...")
    
    if not os.path.exists('boletines.db'):
        print("⚠️ No se encontró base de datos SQLite: boletines.db")
        return {}
    
    try:
        import sqlite3
        import pandas as pd
        
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect('boletines.db')
        
        # Exportar cada tabla
        tablas = ['boletines', 'clientes', 'emails_enviados']
        datos_exportados = {}
        
        for tabla in tablas:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {tabla}", sqlite_conn)
                datos_exportados[tabla] = df
                print(f"📊 {tabla}: {len(df)} registros exportados")
            except Exception as e:
                print(f"⚠️ No se pudo exportar {tabla}: {e}")
        
        sqlite_conn.close()
        return datos_exportados
        
    except Exception as e:
        print(f"❌ Error exportando datos de SQLite: {e}")
        return {}


def importar_datos_a_supabase(datos_exportados):
    """Importar datos a Supabase"""
    print("\n📥 Importando datos a Supabase...")
    
    if not datos_exportados:
        print("⚠️ No hay datos para importar")
        return False
    
    try:
        import psycopg2
        
        # Configuración de conexión
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        for tabla, df in datos_exportados.items():
            if len(df) == 0:
                print(f"⚠️ {tabla}: Sin datos para importar")
                continue
            
            print(f"📥 Importando {tabla}...")
            
            # Preparar datos
            columnas = df.columns.tolist()
            
            # Remover columna 'id' si existe (PostgreSQL usa SERIAL)
            if 'id' in columnas:
                columnas.remove('id')
                df_clean = df[columnas]
            else:
                df_clean = df
            
            # Convertir a lista de tuplas
            datos = [tuple(row) for row in df_clean.values]
            
            # Crear query de inserción
            placeholders = ','.join(['%s'] * len(columnas))
            columnas_str = ','.join([f'"{col}"' for col in columnas])  # Escapar nombres de columna
            query = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
            
            print(f"📝 Query: {query}")
            print(f"📊 Columnas: {columnas}")
            
            # Insertar datos en lotes
            try:
                for i, row in enumerate(datos):
                    try:
                        cursor.execute(query, row)
                        if i % 100 == 0:  # Commit cada 100 registros
                            conn.commit()
                    except Exception as row_error:
                        print(f"⚠️ Error en fila {i}: {row_error}")
                        conn.rollback()
                        continue
                
                conn.commit()
                print(f"✅ {tabla}: {len(datos)} registros procesados")
            except Exception as e:
                print(f"❌ Error importando {tabla}: {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print("🎉 Migración de datos completada")
        return True
        
    except Exception as e:
        print(f"❌ Error importando datos: {e}")
        return False


def probar_conexion():
    """Probar conexión a Supabase"""
    print("\n🧪 Probando conexión a Supabase...")
    
    try:
        import psycopg2
        
        config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print("✅ Conexión exitosa a PostgreSQL")
        print(f"🐘 Versión: {version.split(',')[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def crear_backup_sqlite():
    """Crear backup de SQLite antes de migrar"""
    if os.path.exists('boletines.db'):
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"boletines_backup_{timestamp}.db"
            
            shutil.copy2('boletines.db', backup_name)
            print(f"📦 Backup creado: {backup_name}")
            return True
        except Exception as e:
            print(f"⚠️ No se pudo crear backup: {e}")
            return False
    return True


def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración de SQLite a Supabase")
    print("=" * 50)
    
    # 1. Verificar configuración
    if not verificar_configuracion():
        return
    
    # 2. Probar conexión
    if not probar_conexion():
        return
    
    # 3. Crear backup
    crear_backup_sqlite()
    
    # 4. Crear tablas
    if not crear_tablas_supabase():
        return
    
    # 5. Exportar datos
    datos = exportar_datos_sqlite()
    
    # 6. Importar datos
    if datos:
        success = importar_datos_a_supabase(datos)
        if success:
            print("\n🎉 ¡Migración completada exitosamente!")
            print("\n📋 Próximos pasos:")
            print("1. Verifica los datos en tu panel de Supabase")
            print("2. Cambia la configuración de la app para usar Supabase")
            print("3. Prueba la funcionalidad completa")
        else:
            print("\n❌ La migración falló durante la importación")
    else:
        print("\n✅ Estructura de tablas creada (sin datos para migrar)")


if __name__ == "__main__":
    main()
