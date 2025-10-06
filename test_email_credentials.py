#!/usr/bin/env python3
"""
Script para probar las credenciales de email y la conexión SMTP
"""

import os
import json
import logging
import smtplib
import keyring
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('email_test')

def test_credenciales_json():
    """Verificar si podemos obtener las credenciales usando email_utils"""
    try:
        logger.info("Verificando credenciales con email_utils.py...")
        
        # Importar la función para obtener las credenciales
        from email_utils import obtener_credenciales, get_credentials_file_path
        
        # Mostrar la ruta donde busca las credenciales
        credentials_path = get_credentials_file_path()
        logger.info(f"Buscando credenciales en: {credentials_path}")
        
        # Verificar si el archivo existe
        if not os.path.exists(credentials_path):
            logger.error(f"❌ El archivo de credenciales no existe en: {credentials_path}")
            return False, None
        
        # Obtener credenciales
        credentials = obtener_credenciales()
        
        # Verificar si se obtuvieron las credenciales
        if not credentials:
            logger.error(f"❌ No se pudieron obtener las credenciales usando email_utils.obtener_credenciales()")
            return False, None
        
        # Las credenciales están en un diccionario
            
        # Verificar campos requeridos
        required_fields = ['email', 'smtp_host', 'smtp_port']
        missing_fields = [field for field in required_fields if field not in credentials]
        
        if missing_fields:
            logger.error(f"❌ Faltan campos obligatorios en credenciales.json: {', '.join(missing_fields)}")
            return False, None
        
        # Verificar valores
        email = credentials.get('email')
        host = credentials.get('smtp_host')
        port = credentials.get('smtp_port')
        
        if not all([email, host, port]):
            logger.error("❌ Algunos campos tienen valores vacíos")
            return False, None
            
        # Verificar que el puerto sea un número
        try:
            port = int(port)
        except (ValueError, TypeError):
            logger.error(f"❌ El puerto '{port}' no es un número válido")
            return False, None
        
        logger.info(f"✓ Archivo credenciales.json válido - Email: {email}, Host: {host}, Puerto: {port}")
        return True, credentials
    
    except json.JSONDecodeError:
        logger.error("❌ El archivo credenciales.json no tiene un formato JSON válido")
        return False, None
    except Exception as e:
        logger.error(f"❌ Error al verificar credenciales.json: {e}")
        return False, None

def test_keyring():
    """Verificar si se puede obtener la contraseña desde keyring"""
    try:
        logger.info("Verificando acceso a keyring...")
        
        # Verificar credenciales.json primero
        cred_ok, credentials = test_credenciales_json()
        if not cred_ok or not credentials:
            return False, None
        
        email = credentials.get('email')
        
        # Obtener la contraseña directamente de las credenciales (ya recuperadas por obtener_credenciales)
        password = credentials.get('password')
        
        if not password:
            logger.error(f"❌ No se encontró contraseña en keyring para el usuario '{email}'")
            logger.info("💡 Puede configurar las credenciales usando: python configurar_email.py")
            return False, None
        
        logger.info(f"✓ Contraseña recuperada correctamente desde keyring para '{email}'")
        return True, password
    
    except Exception as e:
        logger.error(f"❌ Error al acceder a keyring: {e}")
        return False, None

def test_smtp_connection():
    """Verificar si podemos conectar al servidor SMTP"""
    try:
        logger.info("Probando conexión SMTP...")
        
        # Verificar credenciales primero
        cred_ok, credentials = test_credenciales_json()
        if not cred_ok or not credentials:
            return False
            
        # Verificar contraseña
        key_ok, password = test_keyring()
        if not key_ok or not password:
            return False
        
        # Obtener valores
        email = credentials.get('email')
        host = credentials.get('smtp_host')
        port = int(credentials.get('smtp_port'))
        
        # Probar conexión SMTP
        logger.info(f"Intentando conectar a {host}:{port}...")
        server = smtplib.SMTP(host, port)
        server.starttls()
        
        logger.info(f"Intentando autenticar como {email}...")
        server.login(email, password)
        
        logger.info("Cerrando conexión...")
        server.quit()
        
        logger.info(f"✓ Conexión SMTP exitosa a {host}:{port}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error(f"❌ Error de autenticación SMTP. Verifique usuario y contraseña")
        return False
    except smtplib.SMTPConnectError:
        logger.error(f"❌ No se pudo conectar al servidor SMTP {host}:{port}")
        return False
    except Exception as e:
        logger.error(f"❌ Error al probar conexión SMTP: {e}")
        return False

def enviar_email_prueba():
    """Enviar un email de prueba"""
    try:
        logger.info("Preparando envío de email de prueba...")
        
        # Verificar conexión SMTP primero
        if not test_smtp_connection():
            return False
            
        # Obtener credenciales
        cred_ok, credentials = test_credenciales_json()
        key_ok, password = test_keyring()
        
        email = credentials.get('email')
        host = credentials.get('smtp_host')
        port = int(credentials.get('smtp_port'))
        
        # Datos para el email de prueba
        destinatario = email  # Enviar a sí mismo para probar
        asunto = "Prueba de envío de email"
        mensaje = "Este es un email de prueba desde el sistema de gestión de marcas."
        
        # Crear mensaje
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = f"Sistema de Gestión de Marcas <{email}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Adjuntar texto plano
        msg.attach(MIMEText(mensaje, 'plain', 'utf-8'))
        
        # Enviar email
        logger.info(f"Enviando email de prueba a {destinatario}...")
        
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info("✓ Email de prueba enviado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al enviar email de prueba: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Iniciando diagnóstico de configuración de email...")
    
    # Prueba 1: Verificar credenciales.json
    print("\n1️⃣ Verificando archivo credenciales.json...")
    credenciales_ok, _ = test_credenciales_json()
    if not credenciales_ok:
        print("❌ Error en la configuración de credenciales.json")
        sys.exit(1)
    else:
        print("✅ Archivo credenciales.json correcto")
    
    # Prueba 2: Verificar keyring
    print("\n2️⃣ Verificando acceso a keyring...")
    keyring_ok, _ = test_keyring()
    if not keyring_ok:
        print("❌ Error al acceder a la contraseña en keyring")
        sys.exit(1)
    else:
        print("✅ Contraseña recuperada correctamente desde keyring")
    
    # Prueba 3: Verificar conexión SMTP
    print("\n3️⃣ Probando conexión SMTP...")
    smtp_ok = test_smtp_connection()
    if not smtp_ok:
        print("❌ Error en la conexión SMTP")
        sys.exit(1)
    else:
        print("✅ Conexión SMTP exitosa")
    
    # Prueba 4: Enviar email de prueba
    print("\n4️⃣ Enviando email de prueba...")
    email_ok = enviar_email_prueba()
    if not email_ok:
        print("❌ Error al enviar email de prueba")
        sys.exit(1)
    else:
        print("✅ Email de prueba enviado correctamente")
    
    print("\n🎉 Todas las pruebas completadas con éxito")