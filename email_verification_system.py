import sqlite3
import bcrypt
import smtplib
import random
import string
import logging
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from paths import get_db_path, get_data_dir, get_logs_dir

# Cargar variables de entorno
load_dotenv()

# Configurar logging
log_file = os.path.join(get_logs_dir(), 'email_verification.log')
logging.basicConfig(level=logging.INFO, filename=log_file)
logger = logging.getLogger(__name__)

class EmailVerificationSystem:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else get_db_path()
        self.credentials_missing = False  # Por defecto, asumimos que las credenciales existen
        self.last_rate_limit_error = None  # Para almacenar errores de límite de tasa
        self.setup_database()
        self.load_email_config()
        
        # Registrar la configuración actual
        self._log_current_config()

    def load_email_config(self):
        """Cargar configuración de email desde credentials.json usando el sistema centralizado"""
        try:
            # Importar y usar exclusivamente el sistema centralizado de credenciales
            from email_utils import obtener_credenciales
            credentials = obtener_credenciales()
            
            if credentials:
                # Buscar campos de email con diferentes nombres posibles
                email = credentials.get('email') or credentials.get('email_user') or credentials.get('user')
                password = credentials.get('password') or credentials.get('email_password')
                
                # Buscar campos de servidor SMTP con diferentes nombres posibles
                smtp_host = (credentials.get('smtp_host') or credentials.get('smtp_server') or 
                            credentials.get('server') or 'smtp.gmail.com')
                
                # Obtener puerto y convertirlo a entero si es necesario
                smtp_port_raw = credentials.get('smtp_port') or credentials.get('port') or 587
                smtp_port = int(smtp_port_raw) if isinstance(smtp_port_raw, str) else smtp_port_raw
                
                if email and password:
                    logger.info(f"Usando credenciales de email desde sistema centralizado para {email}")
                    logger.info(f"Servidor SMTP: {smtp_host}:{smtp_port}")
                    
                    self.smtp_server = smtp_host
                    self.smtp_port = smtp_port
                    self.email_user = email
                    self.email_password = password
                    self.sender_name = 'Sistema de Verificación - Estudio Contable'
                    self.credentials_missing = False
                    return
            else:
                logger.warning("No se encontraron credenciales válidas en el sistema centralizado")
                self.setup_default_email_config()
                self.credentials_missing = True
        except Exception as e:
            logger.error(f"Error al cargar credenciales desde sistema centralizado: {e}")
            self.setup_default_email_config()
            self.credentials_missing = True

    def _log_current_config(self):
        """Registra la configuración actual de email (sin exponer la contraseña)"""
        if self.credentials_missing:
            logger.warning("No hay credenciales de email configuradas.")
            return
            
        # Solo registramos información que no sea sensible
        logger.info("=== Configuración actual de email ===")
        logger.info(f"Usuario: {self.email_user}")
        logger.info(f"Servidor SMTP: {self.smtp_server}")
        logger.info(f"Puerto SMTP: {self.smtp_port}")
        logger.info(f"¿Hay contraseña? {'Sí' if self.email_password else 'No'}")
        logger.info("===================================")

    def create_default_email_config(self):
        """Mensaje informativo sobre la necesidad de configurar credenciales"""
        logger.info("Se necesita configurar credenciales en el sistema centralizado")
        self.setup_default_email_config()

    def setup_default_email_config(self):
        """Configuración por defecto cuando no hay credenciales configuradas"""
        self.smtp_server = ''
        self.smtp_port = 587
        self.email_user = ''
        self.email_password = ''
        self.sender_name = 'Sistema de Verificación'
        self.credentials_missing = True  # Indicador de que faltan credenciales

    def setup_database(self):
        """Configurar la base de datos con los campos necesarios para verificación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla users existe
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='users'
        ''')
        
        if cursor.fetchone() is None:
            # Crear tabla users completa
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 0,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    verification_token TEXT,
                    is_verified INTEGER DEFAULT 0,
                    activation_code TEXT,
                    code_created_at TIMESTAMP
                )
            ''')
        else:
            # Agregar campos faltantes si la tabla ya existe
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN activation_code TEXT')
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN code_created_at TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # La columna ya existe
        
        conn.commit()
        conn.close()
        logger.info("Base de datos configurada correctamente.")

    def generate_activation_code(self):
        """Generar un código de activación de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))

    def hash_password(self, password):
        """Crear hash de la contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, password_hash):
        """Verificar contraseña contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def register_user(self, username, email, password, name=None):
        """
        Registrar un nuevo usuario y enviar código de activación
        
        Args:
            username: Nombre de usuario único
            email: Email del usuario
            password: Contraseña en texto plano
            name: Nombre completo del usuario (opcional)
        
        Returns:
            dict: {'success': bool, 'message': str, 'activation_code': str (solo para testing)}
        """
        # Verificar si hay credenciales de email configuradas
        if self.credentials_missing or not self.email_user or not self.email_password:
            return {
                'success': False, 
                'message': '⚠️ No hay credenciales de email configuradas en el sistema centralizado. Por favor configure las credenciales usando las herramientas de administración antes de registrar usuarios.',
                'error_type': 'missing_credentials'
            }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'message': 'Usuario o email ya existe'}
            
            # Generar código de activación
            activation_code = self.generate_activation_code()
            password_hash = self.hash_password(password)
            
            # Si no se proporciona name, usar el username
            if name is None:
                name = username
            
            # Insertar usuario
            cursor.execute('''
                INSERT INTO users (username, name, email, password_hash, activation_code, code_created_at, is_active, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            ''', (username, name, email, password_hash, activation_code, datetime.now()))
            
            conn.commit()
            conn.close()
            
            # Enviar código por email
            email_sent = self.send_activation_code(email, username, activation_code)
            
            if email_sent:
                logger.info(f"Usuario {username} registrado exitosamente. Código enviado a {email}")
                return {
                    'success': True, 
                    'message': 'Usuario registrado. Revisa tu email para el código de activación.',
                    'activation_code': activation_code  # Solo para testing - remover en producción
                }
            else:
                message = 'Usuario registrado, pero hubo un problema enviando el email.'
                if self.credentials_missing:
                    message += ' No se encontraron credenciales de email configuradas en el sistema centralizado.'
                else:
                    message += ' Verifique la configuración del servidor SMTP y credenciales.'
                
                return {
                    'success': True, 
                    'message': message,
                    'activation_code': activation_code  # Solo para testing
                }
                
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}")
            return {'success': False, 'message': f'Error al registrar usuario: {str(e)}'}

    def send_activation_code(self, email, username, activation_code):
        """
        Enviar código de activación por email - versión ultra simplificada
        
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            # Si las credenciales no están disponibles, actualizar desde el sistema centralizado
            if self.credentials_missing or not self.email_user or not self.email_password:
                # Intentar recargar las credenciales una vez más
                from email_utils import obtener_credenciales
                credentials = obtener_credenciales()
                
                if credentials:
                    # Buscar campos de email con diferentes nombres posibles - NO sobreescribimos el parámetro email
                    sender_email = credentials.get('email') or credentials.get('email_user') or credentials.get('user')
                    password = credentials.get('password') or credentials.get('email_password')
                    
                    # Buscar campos de servidor SMTP con diferentes nombres posibles
                    smtp_host = (credentials.get('smtp_host') or credentials.get('smtp_server') or 
                                credentials.get('server') or 'smtp.gmail.com')
                    
                    # Obtener puerto y convertirlo a entero si es necesario
                    smtp_port_raw = credentials.get('smtp_port') or credentials.get('port') or 587
                    smtp_port = int(smtp_port_raw) if isinstance(smtp_port_raw, str) else smtp_port_raw
                    
                    if sender_email and password:
                        logger.info(f"Recargando credenciales antes de enviar: {sender_email}")
                        logger.info(f"Servidor SMTP recargado: {smtp_host}:{smtp_port}")
                        logger.info(f"Email destinatario permanece: {email}")
                        
                        self.smtp_server = smtp_host
                        self.smtp_port = smtp_port
                        self.email_user = sender_email
                        self.email_password = password
                        self.credentials_missing = False
                else:
                    logger.warning("⚠️ Credenciales de email no configuradas o incompletas en el sistema centralizado")
                    return False
            
            # VERSIÓN 3 (MODIFICADA): HTML con estilos e imagen incorporada
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.image import MIMEImage
            import os
            
            # Crear mensaje plano
            text_body = f"""Hola {username},

Tu código de verificación es: {activation_code}

Este código es válido por 15 minutos.

Saludos,
mimarca.com.ar"""
            
            # Crear mensaje multipart
            msg = MIMEMultipart('related')
            msg['From'] = self.email_user
            msg['To'] = email
            msg['Subject'] = f"Código de Verificación: {activation_code}"
            
            # Subparte alternativa para texto/html
            alt_part = MIMEMultipart('alternative')
            msg.attach(alt_part)
            
            # Adjuntar texto plano
            alt_part.attach(MIMEText(text_body, 'plain', 'utf-8'))
            
            # Crear HTML con referencia a imagen
            html_body = f"""
            <html>
              <head>
                <style>
                  body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                  .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                  .header {{ background-color: #1a365d;; color: white; padding: 10px; text-align: center; }}
                  .content {{ padding: 20px; border: 1px solid #ddd; }}
                  .code {{ font-size: 24px; font-weight: bold; color: #000000; }}
                  .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1>Estudio de Marcas y Patentes</h1>
                    <h2>Código de Verificación</h2>
                  </div>
                  <div class="content">
                    <p>Hola <strong>{username}</strong>,</p>
                    <p>Tu código de verificación es: <span class="code">{activation_code}</span></p>
                    <p>Este código es válido por <strong>15 minutos</strong>.</p>
                    <p>Saludos,<br>mimarca.com.ar</p>
                  </div>
                  <div class="footer">
                    <p>Este es un mensaje automático, por favor no responda a este correo.</p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Adjuntar HTML
            alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # No adjuntamos logo para esta versión - quitamos esa parte para simplificar
            
            # El mensaje ya se ha creado arriba con tipo 'related'
            
            # Enviar email - con más detalle en los pasos para detectar donde falla
            try:
                logger.info(f"Conectando a servidor {self.smtp_server}:{self.smtp_port}")
                
                if not self.smtp_server:
                    logger.error("Error: SMTP server está vacío")
                    return False
                    
                # Crear servidor con timeout
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                
                logger.info("Iniciando TLS")
                server.starttls()
                
                # Validar que tenemos credenciales
                if not self.email_user or not self.email_password:
                    logger.error("Error: Credenciales incompletas (usuario o contraseña vacíos)")
                    return False
                
                logger.info(f"Intentando login con usuario {self.email_user}")
                server.login(self.email_user, self.email_password)
                
                # Validar que el destinatario no está vacío
                if not email:
                    logger.error("Error: Email destinatario está vacío")
                    return False
                
                logger.info(f"Enviando email a {email}")
                msg_content = msg.as_string()
                logger.debug(f"Tamaño del mensaje: {len(msg_content)} bytes")
                
                # Envío ultra simple sin usar as_string()
                result = server.sendmail(self.email_user, [email], msg_content)
                
                if result:
                    logger.warning(f"Resultados parciales al enviar email: {result}")
                
                server.quit()
                logger.info(f"Código de activación enviado exitosamente a {email}")
                return True
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"Destinatario rechazado: {e}")
                return False
            except smtplib.SMTPDataError as e:
                error_code = getattr(e, 'smtp_code', None)
                error_msg = getattr(e, 'smtp_error', b'').decode('utf-8', 'ignore')
                
                if error_code == 550 and 'Unusual sending activity' in error_msg:
                    logger.error(f"Error: Límite de envío de Zoho excedido. Hay que esperar un tiempo: {error_msg}")
                    self.last_rate_limit_error = error_msg
                    return False
                else:
                    logger.error(f"Error de datos SMTP: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error detallado en el envío de email: {str(e)}")
                raise  # Re-lanzamos la excepción para capturarla en los manejadores específicos
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"Error de conexión al servidor SMTP: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"Desconexión del servidor SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False

    def verify_activation_code(self, email, activation_code):
        """
        Verificar código de activación
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # La verificación no necesita credenciales de email directamente, pero las comprobamos
        # por consistencia y para poder notificar al usuario si hay problemas
        if self.credentials_missing or not self.email_user or not self.email_password:
            return {
                'success': False, 
                'message': '⚠️ No hay credenciales de email configuradas en el sistema centralizado. Por favor configure las credenciales usando las herramientas de administración.',
                'error_type': 'missing_credentials'
            }
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar usuario por email
            cursor.execute('''
                SELECT id, activation_code, code_created_at, is_active, is_verified 
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'message': 'Email no encontrado'}
            
            user_id, stored_code, code_created_at, is_active, is_verified = user
            
            if is_active and is_verified:
                return {'success': False, 'message': 'La cuenta ya está activada'}
            
            if not stored_code:
                return {'success': False, 'message': 'No hay código de activación pendiente'}
            
            # Verificar si el código ha expirado (15 minutos)
            if code_created_at:
                code_time = datetime.strptime(code_created_at, '%Y-%m-%d %H:%M:%S.%f')
                if datetime.now() - code_time > timedelta(minutes=15):
                    return {'success': False, 'message': 'El código ha expirado. Solicita uno nuevo.'}
            
            # Verificar código
            if stored_code != activation_code:
                return {'success': False, 'message': 'Código incorrecto'}
            
            # Activar cuenta
            cursor.execute('''
                UPDATE users 
                SET is_active = 1, is_verified = 1, activation_code = NULL, code_created_at = NULL
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Usuario con email {email} activado exitosamente")
            return {'success': True, 'message': 'Cuenta activada exitosamente. Ya puedes iniciar sesión.'}
            
        except Exception as e:
            logger.error(f"Error al verificar código de activación: {e}")
            return {'success': False, 'message': f'Error al verificar código: {str(e)}'}

    def resend_activation_code(self, email):
        """
        Reenviar código de activación
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # Verificar si hay credenciales de email configuradas
        if self.credentials_missing or not self.email_user or not self.email_password:
            return {
                'success': False, 
                'message': '⚠️ No hay credenciales de email configuradas en el sistema centralizado. Por favor configure las credenciales usando las herramientas de administración.',
                'error_type': 'missing_credentials'
            }
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar que el usuario existe y no está activado
            cursor.execute('''
                SELECT id, username, is_active, is_verified 
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'message': 'Email no encontrado'}
            
            user_id, username, is_active, is_verified = user
            
            if is_active and is_verified:
                return {'success': False, 'message': 'La cuenta ya está activada'}
            
            # Generar nuevo código
            activation_code = self.generate_activation_code()
            
            # Actualizar código en base de datos
            cursor.execute('''
                UPDATE users 
                SET activation_code = ?, code_created_at = ?
                WHERE id = ?
            ''', (activation_code, datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            
            # Enviar nuevo código
            logger.info(f"Intentando enviar código de activación a {email} con credenciales de {self.email_user}")
            logger.info(f"Servidor SMTP: {self.smtp_server}:{self.smtp_port}")
            email_sent = self.send_activation_code(email, username, activation_code)
            
            if email_sent:
                return {'success': True, 'message': 'Nuevo código enviado a tu email'}
            else:
                logger.error(f"Error al enviar email a {email}. Credenciales missing: {self.credentials_missing}")
                if self.credentials_missing:
                    return {'success': False, 'message': 'No hay credenciales de email configuradas en el sistema centralizado. Por favor configúrelas primero.'}
                elif self.last_rate_limit_error:
                    # Mensaje específico para límite de tasa
                    return {'success': False, 'message': f'No se puede enviar el email en este momento. El servidor ha detectado demasiados envíos y ha limitado temporalmente la cuenta. Por favor intente más tarde.'}
                else:
                    # Mensaje simple pero informativo
                    return {'success': False, 'message': f'Error al enviar el código de activación al email {email}. Las credenciales del sistema centralizado funcionan correctamente, pero hay un problema al enviar el mensaje específico.'}
                
        except Exception as e:
            logger.error(f"Error al reenviar código: {e}")
            return {'success': False, 'message': f'Error al reenviar código: {str(e)}'}

    def login_user(self, username, password):
        """
        Autenticar usuario (solo si está activo)
        
        Returns:
            dict: {'success': bool, 'message': str, 'user_data': dict}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar usuario
            cursor.execute('''
                SELECT id, username, email, password_hash, role, is_active, is_verified, failed_login_attempts, locked_until
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}
            
            user_id, username, email, password_hash, role, is_active, is_verified, failed_attempts, locked_until = user
            
            # Verificar si está bloqueado
            if locked_until:
                lock_time = datetime.strptime(locked_until, '%Y-%m-%d %H:%M:%S.%f')
                if datetime.now() < lock_time:
                    return {'success': False, 'message': 'Cuenta bloqueada temporalmente'}
            
            # Verificar si está activo
            if not is_active or not is_verified:
                return {'success': False, 'message': 'Cuenta no activada. Verifica tu email.'}
            
            # Verificar contraseña
            if not self.verify_password(password, password_hash):
                # Incrementar intentos fallidos
                failed_attempts += 1
                
                if failed_attempts >= 5:
                    # Bloquear por 30 minutos
                    locked_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users 
                        SET failed_login_attempts = ?, locked_until = ?
                        WHERE id = ?
                    ''', (failed_attempts, locked_until, user_id))
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET failed_login_attempts = ?
                        WHERE id = ?
                    ''', (failed_attempts, user_id))
                
                conn.commit()
                conn.close()
                
                return {'success': False, 'message': f'Contraseña incorrecta. Intentos restantes: {5 - failed_attempts}'}
            
            # Login exitoso - resetear intentos fallidos y actualizar último login
            cursor.execute('''
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE id = ?
            ''', (datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Login exitoso para usuario {username}")
            
            user_data = {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }
            
            return {'success': True, 'message': 'Login exitoso', 'user_data': user_data}
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return {'success': False, 'message': f'Error en login: {str(e)}'}

    def get_user_by_email(self, email):
        """Obtener datos del usuario por email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, is_active, is_verified, created_at
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': user[4],
                    'is_verified': user[5],
                    'created_at': user[6]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return None
