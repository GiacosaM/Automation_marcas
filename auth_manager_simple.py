import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import time

class AuthManager:
    def __init__(self, db_path="boletines.db"):
        self.db_path = db_path
        self.setup_database()
        self.create_default_admin()

    def setup_database(self):
        """Configurar la base de datos de usuarios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_default_admin(self):
        """Crear usuario administrador por defecto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si ya existe un admin
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
            if cursor.fetchone()[0] == 0:
                # Crear hash de la contraseña
                hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute('''
                    INSERT INTO users (username, name, email, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'Administrador', 'admin@empresa.com', hashed_password, 'admin'))
                
                conn.commit()
                print("✅ Usuario administrador creado: admin/admin123")
            
            conn.close()
        except Exception as e:
            print(f"Error creando admin: {e}")

    def verify_user(self, username, password):
        """Verificar credenciales de usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT password_hash FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stored_password = result[0]
                # Verificar si es un hash bcrypt
                if stored_password.startswith('$2b$'):
                    return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                else:
                    # Contraseña en texto plano (para compatibilidad)
                    return password == stored_password
            
            return False
            
        except Exception as e:
            print(f"Error en verificación: {e}")
            return False

    def get_user_info(self, username):
        """Obtener información del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, name, email, role
                FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'username': result[0],
                    'name': result[1],
                    'email': result[2],
                    'role': result[3]
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo info: {e}")
            return None

def show_login():
    """Sistema de login simple y directo"""
    st.markdown("""
    <div style="max-width: 400px; margin: 2rem auto; padding: 2rem; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 16px; color: white; text-align: center;">
        <h2>🔐 Acceso al Sistema</h2>
        <p>Ingresa tus credenciales para continuar</p>
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <small>🔒 Sesión segura con timeout automático de 60 minutos</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Usuario", placeholder="admin")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="admin123")
            
            # Checkbox para recordar sesión (futuro)
            remember_me = st.checkbox("🔄 Mantener sesión activa", value=False, 
                                    help="Extiende el tiempo de sesión a 8 horas")
            
            if st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True, type="primary"):
                if username and password:
                    # Verificar credenciales
                    auth_manager = AuthManager()
                    
                    if auth_manager.verify_user(username, password):
                        # Obtener información del usuario
                        user_info = auth_manager.get_user_info(username)
                        
                        if user_info:
                            # Establecer session state
                            st.session_state['authenticated'] = True
                            st.session_state['user_info'] = user_info
                            st.session_state['last_activity'] = datetime.now()
                            
                            # Si seleccionó "mantener sesión", extender timeout
                            if remember_me:
                                st.session_state['extended_session'] = True
                            
                            st.success(f"✅ ¡Bienvenido {user_info['name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Error obteniendo información del usuario")
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.error("⚠️ Por favor completa todos los campos")
    
    # Información de prueba
    with st.expander("ℹ️ Credenciales de prueba"):
        st.write("**Usuario:** admin")
        st.write("**Contraseña:** admin123")

def check_authentication():
    """Verificar si el usuario está autenticado"""
    return st.session_state.get('authenticated', False)

def check_session_timeout():
    """Verificar si la sesión ha expirado"""
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        return False
    
    # Configurar timeout de sesión
    # 60 minutos normal, 8 horas si está marcado "mantener sesión"
    if st.session_state.get('extended_session', False):
        session_timeout_minutes = 480  # 8 horas
    else:
        session_timeout_minutes = 60   # 1 hora
    
    if 'last_activity' not in st.session_state:
        st.session_state['last_activity'] = datetime.now()
        return True
    
    # Verificar si ha pasado el tiempo límite
    time_elapsed = datetime.now() - st.session_state['last_activity']
    if time_elapsed.total_seconds() > (session_timeout_minutes * 60):
        # Sesión expirada
        logout_user()
        st.warning("⏰ Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return False
    
    # Actualizar última actividad
    st.session_state['last_activity'] = datetime.now()
    return True

def logout_user():
    """Cerrar sesión del usuario"""
    # Limpiar todas las variables de sesión relacionadas con autenticación
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'user_info' in st.session_state:
        del st.session_state['user_info']
    if 'last_activity' in st.session_state:
        del st.session_state['last_activity']
    
    # Limpiar otros datos de sesión específicos de la aplicación
    session_keys_to_clear = [
        'current_page', 'show_db_section', 'show_clientes_section', 
        'show_email_section', 'selected_record_id', 'selected_cliente_id',
        'db_data', 'clientes_data', 'pending_action', 'pending_data',
        'datos_insertados', 'email_credentials', 'confirmar_generar_informes',
        'email_config', 'confirmar_envio_emails', 'resultados_envio'
    ]
    
    for key in session_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def show_user_info():
    """Mostrar información del usuario logueado y botón de logout"""
    if 'user_info' in st.session_state and st.session_state['user_info']:
        user_info = st.session_state['user_info']
        
        # Mostrar información del usuario en la parte superior
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #2d2d2d 0%, #3a3a3a 100%); 
                    padding: 0.8rem; border-radius: 10px; margin-bottom: 1rem; 
                    display: flex; justify-content: space-between; align-items: center;
                    color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center;">
                <div style="background: #667eea; width: 40px; height: 40px; border-radius: 50%; 
                           display: flex; align-items: center; justify-content: center; 
                           margin-right: 12px; font-weight: bold; font-size: 16px;">
                    {user_info['name'][0].upper()}
                </div>
                <div>
                    <div style="font-weight: 600; font-size: 16px;">{user_info['name']}</div>
                    <div style="font-size: 12px; color: #bbb;">👤 {user_info['username']} | 🔑 {user_info['role']}</div>
                </div>
            </div>
            <div style="text-align: right; font-size: 12px; color: #bbb;">
                <div>📅 {datetime.now().strftime("%d/%m/%Y")}</div>
                <div>🕐 {datetime.now().strftime("%H:%M")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de logout en sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
                logout_user()
                st.success("✅ Sesión cerrada correctamente")
                time.sleep(1)
                st.rerun()
            
            # Mostrar tiempo de sesión restante
            if 'last_activity' in st.session_state:
                time_elapsed = datetime.now() - st.session_state['last_activity']
                
                # Calcular tiempo restante basado en tipo de sesión
                if st.session_state.get('extended_session', False):
                    total_minutes = 480  # 8 horas
                    session_type = "extendida"
                else:
                    total_minutes = 60   # 1 hora
                    session_type = "normal"
                
                remaining_minutes = total_minutes - int(time_elapsed.total_seconds() / 60)
                
                if remaining_minutes > 60:
                    # Mostrar en horas y minutos
                    hours = remaining_minutes // 60
                    minutes = remaining_minutes % 60
                    time_display = f"{hours}h {minutes}m"
                else:
                    time_display = f"{remaining_minutes}m"
                
                if remaining_minutes > 0:
                    # Color basado en tiempo restante
                    if remaining_minutes <= 5:
                        color = "#dc3545"  # Rojo
                        icon = "🔴"
                    elif remaining_minutes <= 15:
                        color = "#ffc107"  # Amarillo
                        icon = "🟡"
                    else:
                        color = "#28a745"  # Verde
                        icon = "🟢"
                    
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 8px; 
                               text-align: center; margin-top: 1rem; border-left: 4px solid {color};">
                        <small style="color: #666;">{icon} Sesión {session_type}: <strong>{time_display}</strong></small>
                    </div>
                    """, unsafe_allow_html=True)

def handle_authentication():
    """Manejar autenticación completa - función simple"""
    if not check_authentication():
        show_login()
        return False
    
    # Verificar timeout de sesión
    if not check_session_timeout():
        return False
    
    # Mostrar información del usuario si está autenticado
    show_user_info()
    return True
