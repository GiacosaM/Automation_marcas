#!/usr/bin/env python3
"""
Script para verificar si hay credenciales de email cargadas en el sistema.
"""
import os
import sys
import logging

# Configurar logging básico para ver información en consola
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

print("Verificando credenciales de email...")

# Agregar directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Método 1: Verificar usando email_utils.py
try:
    from email_utils import obtener_credenciales
    
    print("\n1. Verificando usando email_utils.obtener_credenciales():")
    credenciales = obtener_credenciales()
    
    if credenciales and credenciales.get('email'):
        print(f"✅ Credenciales encontradas:")
        print(f"  📧 Email: {credenciales.get('email')}")
        print(f"  🔒 Password: {'********' if credenciales.get('password') else 'No configurada'}")
        print(f"  🖥️ SMTP Host: {credenciales.get('smtp_host', 'smtp.gmail.com')}")
        print(f"  🔌 SMTP Port: {credenciales.get('smtp_port', 587)}")
    else:
        print("❌ No se encontraron credenciales usando email_utils.obtener_credenciales()")
except Exception as e:
    print(f"❌ Error al verificar credenciales con email_utils: {e}")

# Método 2: Verificar usando config.py
try:
    from config import load_email_credentials
    
    print("\n2. Verificando usando config.load_email_credentials():")
    credenciales = load_email_credentials()
    
    if credenciales and credenciales.get('email'):
        print(f"✅ Credenciales encontradas:")
        print(f"  📧 Email: {credenciales.get('email')}")
        print(f"  🔒 Password: {'********' if credenciales.get('password') else 'No configurada'}")
        print(f"  🖥️ SMTP Host: {credenciales.get('smtp_host', 'smtp.gmail.com')}")
        print(f"  🔌 SMTP Port: {credenciales.get('smtp_port', 587)}")
    else:
        print("❌ No se encontraron credenciales usando config.load_email_credentials()")
except Exception as e:
    print(f"❌ Error al verificar credenciales con config.py: {e}")

# Método 3: Verificar usando email_verification_system.py
try:
    from email_verification_system import EmailVerificationSystem
    
    print("\n3. Verificando usando EmailVerificationSystem:")
    email_system = EmailVerificationSystem()
    
    if email_system.email_user and email_system.email_password:
        print(f"✅ Credenciales encontradas:")
        print(f"  📧 Email: {email_system.email_user}")
        print(f"  🔒 Password: {'********' if email_system.email_password else 'No configurada'}")
        print(f"  🖥️ SMTP Server: {email_system.smtp_server}")
        print(f"  🔌 SMTP Port: {email_system.smtp_port}")
    else:
        print("❌ No se encontraron credenciales usando EmailVerificationSystem")
except Exception as e:
    print(f"❌ Error al verificar credenciales con EmailVerificationSystem: {e}")

# Verificar archivos de configuración
print("\n4. Verificando archivos de configuración:")

# Verificar archivo email_config.json
if os.path.exists('email_config.json'):
    print("✅ Archivo email_config.json encontrado")
else:
    print("❌ Archivo email_config.json no encontrado")

# Verificar archivo credentials.json en directorio de datos
try:
    from paths import get_data_dir
    config_dir = os.path.join(get_data_dir(), "config")
    credentials_path = os.path.join(config_dir, "credentials.json")
    
    if os.path.exists(credentials_path):
        print(f"✅ Archivo credentials.json encontrado en {credentials_path}")
        
        # Verificar el contenido del archivo
        try:
            import json
            with open(credentials_path, 'r') as f:
                content = json.load(f)
                if content and isinstance(content, dict) and content.get('email'):
                    print(f"  📄 Contenido: El archivo contiene credenciales para {content.get('email')}")
                else:
                    print(f"  ⚠️ Contenido: El archivo está vacío o no contiene credenciales válidas")
        except Exception as e:
            print(f"  ❌ Error al leer el contenido: {e}")
    else:
        print(f"❌ Archivo credentials.json no encontrado en {credentials_path}")
except Exception as e:
    print(f"❌ Error al verificar credentials.json: {e}")

# Resumen y recomendaciones
print("\n----- RESUMEN Y RECOMENDACIONES -----")

# Verificar si alguno de los métodos encontró credenciales
credenciales_encontradas = False

try:
    # Verificar si hay credenciales en email_utils
    from email_utils import obtener_credenciales
    credenciales1 = obtener_credenciales()
    
    # Verificar si hay credenciales en config
    from config import load_email_credentials
    credenciales2 = load_email_credentials()
    
    # Verificar si hay credenciales en EmailVerificationSystem
    from email_verification_system import EmailVerificationSystem
    email_system = EmailVerificationSystem()
    credenciales3 = bool(email_system.email_user and email_system.email_password)
    
    # Determinar si se encontraron credenciales
    if (credenciales1 and credenciales1.get('email')) or (credenciales2 and credenciales2.get('email')) or credenciales3:
        credenciales_encontradas = True
        
    # Mostrar resumen
    if credenciales_encontradas:
        print("✅ CREDENCIALES: Se encontraron credenciales de email configuradas en al menos un sistema.")
        
        # Mostrar dónde se encontraron
        sources = []
        if credenciales1 and credenciales1.get('email'):
            sources.append("credenciales.json")
        if credenciales2 and credenciales2.get('email'):
            sources.append("config.py")
        if credenciales3:
            sources.append(".env o email_config.json")
            
        print(f"📌 Origen de las credenciales: {', '.join(sources)}")
        
        # Verificar si hay inconsistencias
        if len(sources) > 1:
            print("⚠️ ADVERTENCIA: Las credenciales están configuradas en múltiples fuentes, lo que podría causar inconsistencias.")
    else:
        print("❌ CREDENCIALES: No se encontraron credenciales de email configuradas.")
        print("⚠️ El sistema no podrá enviar emails de verificación o notificaciones.")
        print("""
📝 Para configurar credenciales, puede hacer lo siguiente:
  1. Usando el panel de administración en la interfaz web
  2. Modificando el archivo credentials.json directamente
  3. Configurando variables de entorno EMAIL_USER y EMAIL_PASSWORD
""")
        
except Exception as e:
    print(f"❌ Error al generar el resumen: {e}")

print("\nVerificación de credenciales completada.")