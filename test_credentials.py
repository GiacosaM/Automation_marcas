#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de credenciales de email
"""

import json
from config import load_email_credentials, save_email_credentials, validate_email_format

def test_credentials():
    """Prueba las funciones de credenciales"""
    print("🧪 Probando funcionalidad de credenciales de email...")
    
    # Cargar credenciales actuales
    print("\n1. Cargando credenciales actuales...")
    credentials = load_email_credentials()
    print(f"   Email: {credentials.get('email', 'No configurado')}")
    print(f"   Password: {'Configurado' if credentials.get('password') else 'No configurado'}")
    
    # Validar formato de email
    if credentials.get('email'):
        print(f"\n2. Validando formato de email...")
        if validate_email_format(credentials['email']):
            print("   ✅ Formato válido")
        else:
            print("   ❌ Formato inválido")
    
    # Mostrar contenido del archivo credenciales.json
    print(f"\n3. Contenido actual de credenciales.json:")
    try:
        with open('credenciales.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"   Email: {data.get('email', 'No encontrado')}")
            print(f"   Password: {'***' if data.get('password') else 'No encontrado'}")
            print(f"   Otros campos: {len([k for k in data.keys() if k not in ['email', 'password']])} campos adicionales")
    except FileNotFoundError:
        print("   ⚠️ Archivo credenciales.json no encontrado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Prueba completada. Las credenciales están {'configuradas' if credentials.get('email') else 'sin configurar'}.")

if __name__ == "__main__":
    test_credentials()
