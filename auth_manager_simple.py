import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime

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
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Usuario", placeholder="admin")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="admin123")
            
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

def handle_authentication():
    """Manejar autenticación completa - función simple"""
    if not check_authentication():
        show_login()
        return False
    return True
