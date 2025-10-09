#!/usr/bin/env python3
"""
Utilidades para la gestión segura de credenciales de email y envío de notificaciones.

Este módulo proporciona funciones para guardar y recuperar credenciales de forma segura
para el envío de emails desde la aplicación, utilizando keyring para almacenar 
contraseñas de forma segura en el sistema operativo.
"""

import os
import json
import keyring
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Importar funciones para manejo de directorios
from paths import get_data_dir, get_config_file_path

# Constante para el servicio en keyring
SERVICE_ID = "MiAppMarcas_Email"

def get_credentials_file_path():
    """
    Obtiene la ruta al archivo de credenciales de email.
    
    Returns:
        str: Ruta absoluta al archivo credentials.json
    """
    config_dir = os.path.join(get_data_dir(), "config")
    
    # Crear el directorio de configuración si no existe
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    return os.path.join(config_dir, "credentials.json")

def guardar_credenciales(email, smtp_host, smtp_port, password):
    """
    Guarda las credenciales de email de forma segura.
    
    Las credenciales SMTP (email, host y puerto) se guardan en un archivo JSON,
    mientras que la contraseña se guarda en el keyring del sistema operativo.
    
    Args:
        email (str): Dirección de correo electrónico
        smtp_host (str): Servidor SMTP (ej. smtp.gmail.com)
        smtp_port (int): Puerto SMTP (ej. 587)
        password (str): Contraseña del correo (se guarda en keyring)
        
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        # Guardar email, host y puerto en JSON
        credentials = {
            "email": email,
            "smtp_host": smtp_host,
            "smtp_port": int(smtp_port)
        }
        
        # Obtener ruta del archivo de credenciales
        credentials_path = get_credentials_file_path()
        
        # Guardar en archivo JSON
        with open(credentials_path, 'w') as file:
            json.dump(credentials, file, indent=4)
        
        # Guardar contraseña en keyring
        keyring.set_password(SERVICE_ID, email, password)
        
        logging.info(f"Credenciales guardadas correctamente para {email}")
        return True
        
    except Exception as e:
        logging.error(f"Error al guardar credenciales: {e}")
        return False

def obtener_credenciales():
    """
    Recupera las credenciales de email almacenadas.
    
    Lee el archivo JSON para obtener email, host y puerto,
    y recupera la contraseña desde el keyring del sistema.
    
    Returns:
        dict: Diccionario con las credenciales (email, smtp_host, smtp_port, password)
              o None si no se pudieron obtener
    """
    try:
        # Obtener ruta del archivo de credenciales
        credentials_path = get_credentials_file_path()
        
        # Verificar si existe el archivo
        if not os.path.exists(credentials_path):
            logging.warning("No existen credenciales guardadas")
            return None
            
        # Leer credenciales del archivo JSON
        with open(credentials_path, 'r') as file:
            credentials = json.load(file)
            
        # Obtener email
        email = credentials.get("email")
        if not email:
            logging.warning("Email no encontrado en credenciales")
            return None
            
        # Recuperar contraseña del keyring
        password = keyring.get_password(SERVICE_ID, email)
        if not password:
            logging.warning(f"Contraseña no encontrada en keyring para {email}")
            return None
            
        # Agregar la contraseña al diccionario de credenciales
        credentials["password"] = password
        
        return credentials
        
    except Exception as e:
        logging.error(f"Error al obtener credenciales: {e}")
        return None

def probar_envio(email, smtp_host, smtp_port, password):
    """
    Envía un email de prueba para verificar las credenciales.
    
    Intenta enviar un correo al mismo remitente para validar
    que las credenciales son correctas.
    
    Args:
        email (str): Dirección de correo electrónico
        smtp_host (str): Servidor SMTP
        smtp_port (int): Puerto SMTP
        password (str): Contraseña del correo
        
    Returns:
        tuple: (bool, str) - (Éxito, Mensaje)
    """
    try:
        # Crear el mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = email
        mensaje['To'] = email
        mensaje['Subject'] = "Prueba de configuración de correo"
        
        # Cuerpo del mensaje
        cuerpo = """
        Este es un correo de prueba para verificar la configuración de credenciales SMTP.
        
        Si estás recibiendo este mensaje, la configuración ha sido exitosa.
        
        Sistema de Gestión de Marcas
        """
        
        mensaje.attach(MIMEText(cuerpo, 'plain'))
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        
        # Iniciar sesión
        server.login(email, password)
        
        # Enviar email
        server.send_message(mensaje)
        
        # Cerrar conexión
        server.quit()
        
        return True, "Conexión exitosa. Se ha enviado un correo de prueba a tu dirección."
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error en prueba de envío: {error_msg}")
        
        # Mensajes de error más amigables según el tipo de error
        if "Authentication" in error_msg:
            return False, "Error de autenticación: Verifica tu correo y contraseña"
        elif "getaddrinfo" in error_msg:
            return False, "Error de conexión: Verifica el servidor SMTP y tu conexión a internet"
        else:
            return False, f"Error al enviar correo de prueba: {error_msg}"

def eliminar_credenciales():
    """
    Elimina las credenciales guardadas.
    
    Borra el archivo JSON y elimina la contraseña del keyring.
    También limpia cualquier caché de credenciales en la sesión de Streamlit.
    
    Returns:
        bool: True si se eliminaron correctamente, False en caso contrario
    """
    try:
        logging.info("Iniciando proceso de eliminación de credenciales...")
        
        # Obtener ruta del archivo de credenciales
        credentials_path = get_credentials_file_path()
        
        email_to_delete = None
        
        # Verificar si existe el archivo
        if os.path.exists(credentials_path):
            # Leer email para eliminar contraseña del keyring
            try:
                with open(credentials_path, 'r') as file:
                    credentials = json.load(file)
                    email_to_delete = credentials.get("email")
                    logging.info(f"Email encontrado para eliminar: {email_to_delete}")
            except json.JSONDecodeError:
                logging.warning("Archivo de credenciales corrupto o vacío")
            except Exception as e:
                logging.error(f"Error al leer archivo de credenciales: {e}")
            
            # Eliminar archivo físicamente
            try:
                os.remove(credentials_path)
                logging.info(f"Archivo de credenciales eliminado: {credentials_path}")
            except Exception as e:
                logging.error(f"Error al eliminar archivo de credenciales: {e}")
        else:
            logging.info("No existe archivo de credenciales para eliminar")
        
        # Eliminar contraseña del keyring si se encontró un email
        if email_to_delete:
            try:
                keyring.delete_password(SERVICE_ID, email_to_delete)
                logging.info(f"Contraseña eliminada del keyring para {email_to_delete}")
            except keyring.errors.PasswordDeleteError:
                logging.warning(f"No se encontró contraseña en keyring para {email_to_delete}")
            except Exception as e:
                logging.error(f"Error al eliminar contraseña del keyring: {e}")
                
        # Limpiar todas las cachés posibles en Streamlit
        try:
            import streamlit as st
            
            # Limpiar caché de email_credentials
            if 'email_credentials' in st.session_state:
                del st.session_state['email_credentials']
                logging.info("Caché de email_credentials eliminada de la sesión")
                
            # Limpiar otras cachés relacionadas con email
            for key in list(st.session_state.keys()):
                if 'email' in key.lower() or 'credential' in key.lower():
                    del st.session_state[key]
                    logging.info(f"Caché adicional eliminada: {key}")
                    
        except ImportError:
            logging.info("Streamlit no disponible, no se limpiaron cachés de sesión")
        except Exception as e:
            logging.error(f"Error al limpiar caché de Streamlit: {e}")
        
        # Crear archivo vacío para indicar que no hay credenciales
        try:
            with open(credentials_path, 'w') as file:
                json.dump({}, file)
            logging.info("Creado archivo de credenciales vacío")
        except Exception as e:
            logging.warning(f"No se pudo crear archivo de credenciales vacío: {e}")
            
        logging.info("Proceso de eliminación de credenciales completado con éxito")
        return True
        
    except Exception as e:
        logging.error(f"Error general al eliminar credenciales: {e}", exc_info=True)
        return False

# Si se ejecuta como script principal, mostrar información
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Utilidad para gestión de credenciales de email")
    print(f"Archivo de credenciales: {get_credentials_file_path()}")
    
    # Verificar si existen credenciales
    credenciales = obtener_credenciales()
    if credenciales:
        print(f"Credenciales encontradas para: {credenciales.get('email')}")
        print(f"Servidor SMTP: {credenciales.get('smtp_host')}:{credenciales.get('smtp_port')}")
    else:
        print("No se encontraron credenciales guardadas.")
