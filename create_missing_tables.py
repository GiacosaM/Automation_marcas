#!/usr/bin/env python3
"""
Script para crear tabla envios_log en Supabase
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def crear_tabla_envios_log():
    """Crear tabla envios_log en Supabase"""
    print("🏗️ Creando tabla envios_log en Supabase...")
    
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
        
        # Crear tabla envios_log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS envios_log (
                id SERIAL PRIMARY KEY,
                titular TEXT,
                email TEXT,
                fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estado TEXT,
                error TEXT,
                numero_boletin TEXT,
                importancia TEXT,
                fecha_envio_default TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Crear índices para envios_log
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_envios_log ON envios_log(titular, fecha_envio, estado);",
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tabla envios_log creada exitosamente en Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tabla envios_log: {e}")
        return False

if __name__ == "__main__":
    crear_tabla_envios_log()
