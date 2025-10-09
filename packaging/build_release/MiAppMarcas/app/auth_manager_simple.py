import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import time
from paths import get_db_path

class AuthManager:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else get_db_path()
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
    """Sistema de login con una interfaz profesional y centralizada."""

    # Estilos globales para un look moderno y consistente (UI-only)
    st.markdown(
        """
        <style>
            /* Fondo suave con degradado */
            html, body { background: linear-gradient(135deg, #f5f7ff 0%, #f7f2ff 100%) !important; }

            /* Reducir marco/margen superior y centrar contenido */
            .block-container { padding-top: 1.25rem !important; padding-bottom: 2rem !important; max-width: 900px; }
            [data-testid="stHeader"] { background: transparent !important; }

            /* Tipografía y colores base */
            :root { --primary: #6b6ee8; --primary-dark: #5a5ed6; --accent: #8b5cf6; --text: #212529; --muted: #6c757d; }

            /* Tarjeta visual para formularios (cards) */
            [data-testid="stForm"] {
                background: #000000; border: 1px solid #ececf1; border-radius: 16px;
                box-shadow: 0 10px 24px rgba(17, 17, 26, 0.08);
                padding: 1.25rem 1.25rem 1rem 1.25rem; margin: 0 auto 1rem auto; width: 100%; max-width: 520px;
            }

            /* Header elegante con logo */
            .auth-header { text-align: center; margin: 0 auto 1.5rem auto; max-width: 520px; }
            .auth-header img { width: 92px; height: auto; border-radius: 12px; margin-bottom: 0.5rem; }
            .auth-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; background: linear-gradient(90deg, var(--primary), var(--accent)); -webkit-background-clip: text; background-clip: text; color: transparent; }
            .auth-header p { color: var(--muted); margin-top: 0.35rem; font-size: 0.95rem; }

            /* Tabs centradas y más visibles */
            .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 2px solid #e9ecef; margin-bottom: 0.5rem; }
            .stTabs [data-baseweb="tab"] { padding: 0.8rem 1rem; font-weight: 600; color: #6c757d; }
            .stTabs [data-baseweb="tab"][aria-selected="true"] { border-bottom: 2px solid var(--primary); color: var(--primary); }

            /* Inputs con foco elegante */
            .stTextInput input, .stPassword input { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; }
            .stTextInput input:focus, .stPassword input:focus { outline: none !important; border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(107, 110, 232, 0.15) !important; }

            /* Botones con degradado y hover (solo en el área de auth) */
            .auth-area .stButton > button, [data-testid="stForm"] .stButton > button {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
                color: #fff !important; border: none !important; border-radius: 12px !important;
                padding: 0.55rem 1rem !important; font-weight: 700 !important; letter-spacing: .2px;
                box-shadow: 0 6px 18px rgba(107, 110, 232, .25) !important; transition: all .2s ease !important;
            }
            .auth-area .stButton > button:hover, [data-testid="stForm"] .stButton > button:hover {
                transform: translateY(-1px); box-shadow: 0 8px 22px rgba(139, 92, 246, .3) !important;
                background: linear-gradient(135deg, var(--primary-dark) 0%, var(--accent) 100%) !important;
            }

            /* Botones secundarios planos */
            .auth-links .stButton > button { background: #f6f7ff !important; color: var(--primary) !important; border: 1px solid #e7e9ff !important; }
            .auth-links .stButton > button:hover { background: #eef0ff !important; }

            /* Responsive tweaks */
            @media (max-width: 640px) {
                [data-testid="stForm"] { padding: 1rem; border-radius: 12px; }
                .auth-header h1 { font-size: 1.35rem; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inicializar el estado del modo de autenticación si no existe
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

    # Contenedor principal de autenticación
    if st.session_state.auth_mode in ['login', 'register']:
        with st.container():
            # Área de autenticación (para scoping de estilos)
            st.markdown('<div class="auth-area">', unsafe_allow_html=True)

            st.markdown(
                """
                <div class="auth-header">
                    <img src="https://mimarca.com.ar/templates/yootheme/cache/10/logo-10f1f883.webp" alt="Logo">
                    <h1>Mi Marca · Portal</h1>
                    <p>Estudio Contable — Marcas y Patentes</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            login_tab, register_tab = st.tabs(["🔑 Iniciar Sesión", "📝 Crear Cuenta"])

            with login_tab:
                _show_login_form()

            with register_tab:
                _show_register_form()

            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.auth_mode == 'verify':
        _show_verify_form()
    
    elif st.session_state.auth_mode == 'resend':
        _show_resend_form()

def _show_login_form():
    """Mostrar formulario de login con campos de entrada de ancho ajustado."""
    with st.form("login_form", clear_on_submit=True):
        # Centrar y limitar ancho de inputs
        c1, c2, c3 = st.columns([1, 5, 1])
        with c2:
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario", key="login_username")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingrese su contraseña", key="login_password")
            remember_me = st.checkbox("🔄 Mantener sesión activa", value=False, help="Extiende el tiempo de sesión a 8 horas")

        # Botón principal ancho completo dentro del form (mejor UX)
        if st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True, type="primary"):
            if username and password:
                # ... (resto del código de login sin cambios)
                from email_verification_system import EmailVerificationSystem
                email_auth = EmailVerificationSystem()
                result = email_auth.login_user(username, password)
                
                if result['success']:
                    user_data = result['user_data']
                    st.session_state['authenticated'] = True
                    st.session_state['user_info'] = {
                        'username': user_data['username'],
                        'name': user_data.get('name', user_data['username']),
                        'email': user_data['email'],
                        'role': user_data['role']
                    }
                    st.session_state['last_activity'] = datetime.now()
                    st.session_state['extended_session'] = remember_me
                    st.success("✅ Login exitoso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    auth_manager = AuthManager()
                    if auth_manager.verify_user(username, password):
                        user_info = auth_manager.get_user_info(username)
                        if user_info:
                            st.session_state['authenticated'] = True
                            st.session_state['user_info'] = user_info
                            st.session_state['last_activity'] = datetime.now()
                            st.session_state['extended_session'] = remember_me
                            st.success("✅ Login exitoso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Error obteniendo información del usuario")
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.warning("⚠️ Por favor complete todos los campos")

    # Acciones secundarias bajo el form con estilo consistente
    st.markdown('<div class="auth-links">', unsafe_allow_html=True)
    l1, l2 = st.columns(2)
    with l1:
        if st.button("🛡️ Verificar Cuenta", use_container_width=True, key="verify_account_btn"):
            st.session_state.auth_mode = 'verify'
            st.rerun()
    with l2:
        if st.button("� Reenviar Código", use_container_width=True, key="resend_code_btn"):
            st.session_state.auth_mode = 'resend'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def _show_register_form():
    """Mostrar formulario de registro con verificación por email"""
    st.info("💡 Recibirás un código de verificación en tu email para activar tu cuenta.")
    
    with st.form("register_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([1, 5, 1])
        with c2:
            username = st.text_input("👤 Nombre de Usuario", placeholder="Elige un nombre de usuario único", key="register_username")
            name = st.text_input("📝 Nombre Completo", placeholder="Tu nombre completo", key="register_name")
            email = st.text_input("📧 Email", placeholder="tu@email.com", key="register_email")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres", key="register_password")
            confirm_password = st.text_input("🔒 Confirmar Contraseña", type="password", placeholder="Repite tu contraseña", key="register_confirm_password")
        
        if st.form_submit_button("📝 Registrarse", use_container_width=True, type="primary"):
            if username and name and email and password and confirm_password:
                if password != confirm_password:
                    st.error("❌ Las contraseñas no coinciden")
                elif len(password) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                elif "@" not in email or "." not in email:
                    st.error("❌ Ingresa un email válido")
                else:
                    with st.spinner("Registrando usuario..."):
                        from email_verification_system import EmailVerificationSystem
                        email_auth = EmailVerificationSystem()
                        result = email_auth.register_user(username, email, password, name)
                    
                    if result['success']:
                        st.success("✅ " + result['message'])
                        st.info("📧 Revisa tu email para activar tu cuenta.")
                        if 'activation_code' in result:
                            with st.expander("🔧 Código para Testing (Solo Desarrollo)", expanded=False):
                                st.code(f"Código de activación: {result['activation_code']}")
                        time.sleep(2)
                        st.session_state.auth_mode = 'verify'
                        st.rerun()
                    else:
                        st.error("❌ " + result['message'])
                        # Mostrar mensaje específico cuando faltan credenciales de email
                        if 'error_type' in result and result['error_type'] == 'missing_credentials':
                            st.warning("""
                            ### ⚙️ Configuración Requerida
                            Para habilitar el registro de usuarios, primero debe configurar las credenciales de email en el panel de administración.
                            
                            **Pasos:**
                            1. Acceda como administrador
                            2. Vaya a la sección de Configuración
                            3. Configure las credenciales de email en la sección correspondiente
                            """)
                            
            else:
                st.warning("⚠️ Por favor completa todos los campos")

def _show_verify_form():
    """Mostrar un formulario de verificación de cuenta limpio y centrado."""
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-header">
            <h1>✅ Verificar Cuenta</h1>
            <p>Ingresa el código de 6 dígitos que recibiste en tu email.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("verify_form", clear_on_submit=False):
            c1, c2, c3 = st.columns([1, 5, 1])
            with c2:
                email = st.text_input("📧 Email", placeholder="Email usado en el registro", key="verify_email")
                activation_code = st.text_input("🔢 Código de Activación", placeholder="Código de 6 dígitos", max_chars=6, key="verify_code")
            
            if st.form_submit_button("✅ Verificar", type="primary", use_container_width=True):
                if email and activation_code:
                    if len(activation_code) != 6 or not activation_code.isdigit():
                        st.error("❌ El código debe tener exactamente 6 dígitos.")
                    else:
                        with st.spinner("Verificando código..."):
                            from email_verification_system import EmailVerificationSystem
                            email_auth = EmailVerificationSystem()
                            result = email_auth.verify_activation_code(email, activation_code)
                        
                        if result['success']:
                            st.success("✅ " + result['message'])
                            st.info("🔑 Ahora puedes iniciar sesión.")
                            time.sleep(2)
                            st.session_state.auth_mode = 'login'
                            st.rerun()
                        else:
                            st.error("❌ " + result['message'])
                            # Mostrar mensaje específico cuando faltan credenciales de email
                            if 'error_type' in result and result['error_type'] == 'missing_credentials':
                                st.warning("""
                                ### ⚙️ Configuración Requerida
                                Para habilitar la verificación de usuarios, primero debe configurar las credenciales de email en el panel de administración.
                                
                                **Pasos:**
                                1. Acceda como administrador
                                2. Vaya a la sección de Configuración
                                3. Configure las credenciales de email en la sección correspondiente
                                """)
                else:
                    st.warning("⚠️ Por favor completa todos los campos.")
        
        st.markdown("---")
        st.warning("⏰ **Importante**: Los códigos expiran en 15 minutos.")
        st.info("📧 **¿No recibes el email?** Revisa tu spam o solicita un nuevo código.")

        if st.button("← Volver al Login", use_container_width=True, key="verify_back_btn"):
            st.session_state.auth_mode = 'login'
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

def _show_resend_form():
    """Mostrar un formulario para reenviar código de verificación."""
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-header">
            <h1>🔄 Reenviar Código</h1>
            <p>Ingresa tu email para recibir un nuevo código de activación.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("resend_form", clear_on_submit=False):
            c1, c2, c3 = st.columns([1, 5, 1])
            with c2:
                email = st.text_input("📧 Email", placeholder="Email usado en el registro", key="resend_email_input")
            
            if st.form_submit_button("📤 Reenviar Código", type="primary", use_container_width=True):
                if email:
                    with st.spinner("Enviando nuevo código..."):
                        from email_verification_system import EmailVerificationSystem
                        email_auth = EmailVerificationSystem()
                        result = email_auth.resend_activation_code(email)
                    
                    if result['success']:
                        st.success("✅ " + result['message'])
                        st.info("📧 Revisa tu email para el nuevo código.")
                        time.sleep(2)
                        st.session_state.auth_mode = 'verify'
                        st.rerun()
                    else:
                        st.error("❌ " + result['message'])
                        # Mostrar mensaje específico cuando faltan credenciales de email
                        if 'error_type' in result and result['error_type'] == 'missing_credentials':
                            st.warning("""
                            ### ⚙️ Configuración Requerida
                            Para habilitar el reenvío de códigos, primero debe configurar las credenciales de email en el panel de administración.
                            
                            **Pasos:**
                            1. Acceda como administrador
                            2. Vaya a la sección de Configuración
                            3. Configure las credenciales de email en la sección correspondiente
                            """)
                else:
                    st.warning("⚠️ Ingresa tu email para reenviar el código.")
        
        if st.button("← Volver al Login", use_container_width=True, key="resend_back_btn"):
            st.session_state.auth_mode = 'login'
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

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
        
        # Header principal limpio sin botón
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #2d2d2d 0%, #3a3a3a 100%); 
                    padding: 0.8rem 1.5rem; border-radius: 10px; margin-bottom: 1rem; 
                    display: flex; align-items: center;
                    color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; flex-grow: 1;">
                <div style="background: #667eea; width: 40px; height: 40px; border-radius: 50%; 
                           display: flex; align-items: center; justify-content: center; 
                           margin-right: 12px; font-weight: bold; font-size: 16px;">
                    {user_info['name'][0].upper()}
                </div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; font-size: 16px;">{user_info['name']}</div>
                    <div style="font-size: 12px; color: #bbb;">👤 {user_info['email']} | 🔑 {user_info['role']} | 📅 {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de logout solo en sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Usuario Activo")
            st.markdown(f"**{user_info['name']}**")
            st.markdown(f"*{user_info['role']}*")
            
            # Botón estilizado para logout
            st.markdown("""
            <style>
            .sidebar-logout-btn .stButton > button {
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 0.5rem 1rem !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3) !important;
                width: 100% !important;
            }
            
            .sidebar-logout-btn .stButton > button:hover {
                background: linear-gradient(135deg, #c82333 0%, #bd2130 100%) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4) !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Contenedor con clase para el estilo
            with st.container():
                st.markdown('<div class="sidebar-logout-btn">', unsafe_allow_html=True)
                if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True, key="logout_sidebar"):
                    logout_user()
                    st.success("✅ Sesión cerrada")
                    time.sleep(1)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
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
