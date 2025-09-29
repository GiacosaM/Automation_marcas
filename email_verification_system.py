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
        self.setup_database()
        self.load_email_config()

    def load_email_config(self):
        """Cargar configuración de email desde archivo .env o JSON"""
        # Primero intentar cargar desde variables de entorno (.env)
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if email_user and email_password:
            logger.info("Usando credenciales de email desde archivo .env")
            self.smtp_server = 'smtp.gmail.com'
            self.smtp_port = 587
            self.email_user = email_user
            self.email_password = email_password
            self.sender_name = 'Sistema de Verificación - Estudio Contable'
            return
        
        # Si no hay variables de entorno, intentar archivo JSON
        try:
            with open('email_config.json', 'r') as f:
                config = json.load(f)
                self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
                self.smtp_port = config.get('smtp_port', 587)
                self.email_user = config.get('email_user', '')
                self.email_password = config.get('email_password', '')
                self.sender_name = config.get('sender_name', 'Sistema de Verificación')
                logger.info("Usando credenciales de email desde email_config.json")
        except FileNotFoundError:
            logger.warning("Archivo email_config.json no encontrado y no hay variables de entorno.")
            self.create_default_email_config()
        except Exception as e:
            logger.error(f"Error al cargar configuración de email: {e}")
            self.setup_default_email_config()

    def create_default_email_config(self):
        """Crear archivo de configuración de email por defecto"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "martingiacosa@gmail.com",
            "email_password": "aall wvdj jytz kyij",
            "sender_name": "Sistema de Verificación"
        }
        
        with open('email_config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        
        logger.info("Archivo email_config.json creado. Por favor configura tus credenciales de email.")
        self.setup_default_email_config()

    def setup_default_email_config(self):
        """Configuración por defecto cuando no hay archivo de configuración"""
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email_user = ''
        self.email_password = ''
        self.sender_name = 'Sistema de Verificación'

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
                return {
                    'success': True, 
                    'message': 'Usuario registrado, pero hubo un problema enviando el email. Contacta al administrador.',
                    'activation_code': activation_code  # Solo para testing
                }
                
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}")
            return {'success': False, 'message': f'Error al registrar usuario: {str(e)}'}

    def send_activation_code(self, email, username, activation_code):
        """
        Enviar código de activación por email usando formato HTML profesional
        
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Credenciales de email no configuradas")
                return False
            
            # Importar plantillas HTML
            from email_templates import get_html_template, get_verification_email_html
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.image import MIMEImage
            import os
            
            # Crear mensaje usando MIMEMultipart para soporte HTML
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.email_user}>"
            msg['To'] = email
            msg['Subject'] = "Código de Verificación - Sistema de Marcas"
            
            # Crear versión texto plano como fallback
            text_body = f"""Hola {username},

Gracias por registrarte en nuestro sistema.

Tu código de verificación es: {activation_code}

Este código es válido por 15 minutos.

Si no solicitaste este registro, ignora este email.

Saludos,
Sistema de Verificación - Estudio Contable"""
            
            # Obtener plantilla HTML y reemplazar el contenido
            html_template = get_html_template()
            verification_content = get_verification_email_html(username, activation_code)
            html_content = html_template.replace('<!-- El contenido del mensaje se insertará aquí -->', verification_content)
            
            # Adjuntar partes al mensaje
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Agregar logo si existe
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes', 'Logo.png')
            if os.path.exists(logo_path):
                try:
                    with open(logo_path, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-ID', '<logo>')
                        img.add_header('Content-Disposition', 'inline')
                        msg.attach(img)
                except Exception as e:
                    logger.warning(f"Error al adjuntar logo: {e}")
            
            # Enviar email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, [email], msg.as_string())
            server.quit()
            
            logger.info(f"Código de activación enviado a {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False

    def verify_activation_code(self, email, activation_code):
        """
        Verificar código de activación
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
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
            email_sent = self.send_activation_code(email, username, activation_code)
            
            if email_sent:
                return {'success': True, 'message': 'Nuevo código enviado a tu email'}
            else:
                return {'success': False, 'message': 'Error al enviar email. Contacta al administrador.'}
                
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
