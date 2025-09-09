import streamlit as st
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_verification_system import EmailVerificationSystem

class AuthenticationApp:
    def __init__(self):
        self.auth_system = EmailVerificationSystem()
        
        # Inicializar session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'login'

    def show_navigation(self):
        """Mostrar navegación entre páginas"""
        if not st.session_state.authenticated:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔑 Iniciar Sesión", use_container_width=True):
                    st.session_state.current_page = 'login'
                    st.rerun()
            
            with col2:
                if st.button("📝 Registrarse", use_container_width=True):
                    st.session_state.current_page = 'register'
                    st.rerun()
            
            with col3:
                if st.button("✅ Verificar Cuenta", use_container_width=True):
                    st.session_state.current_page = 'verify'
                    st.rerun()

    def login_page(self):
        """Página de inicio de sesión"""
        st.title("🔑 Iniciar Sesión")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu nombre de usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            submitted = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    with st.spinner("Verificando credenciales..."):
                        result = self.auth_system.login_user(username, password)
                    
                    if result['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_data = result['user_data']
                        st.success("¡Login exitoso! Redirigiendo...")
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.warning("Por favor completa todos los campos")
        
        st.markdown("---")
        st.info("💡 **¿No tienes cuenta?** Haz clic en 'Registrarse' para crear una nueva cuenta.")
        st.info("📧 **¿Ya te registraste?** Verifica tu cuenta con el código enviado a tu email.")

    def register_page(self):
        """Página de registro"""
        st.title("📝 Registrar Nueva Cuenta")
        st.markdown("---")
        
        with st.form("register_form"):
            username = st.text_input("👤 Nombre de Usuario", placeholder="Elige un nombre de usuario único")
            name = st.text_input("📝 Nombre Completo", placeholder="Tu nombre completo")
            email = st.text_input("📧 Email", placeholder="tu@email.com")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            confirm_password = st.text_input("🔒 Confirmar Contraseña", type="password", placeholder="Repite tu contraseña")
            
            submitted = st.form_submit_button("Registrarse", type="primary", use_container_width=True)
            
            if submitted:
                if username and name and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Las contraseñas no coinciden")
                    elif len(password) < 6:
                        st.error("❌ La contraseña debe tener al menos 6 caracteres")
                    elif "@" not in email or "." not in email:
                        st.error("❌ Ingresa un email válido")
                    else:
                        with st.spinner("Registrando usuario..."):
                            result = self.auth_system.register_user(username, email, password, name)
                        
                        if result['success']:
                            st.success("✅ " + result['message'])
                            st.info("📧 Revisa tu email y usa el código de verificación para activar tu cuenta.")
                            
                            # Mostrar código para testing (remover en producción)
                            if 'activation_code' in result:
                                st.code(f"Código de activación (para testing): {result['activation_code']}")
                            
                            st.balloons()
                        else:
                            st.error("❌ " + result['message'])
                else:
                    st.warning("⚠️ Por favor completa todos los campos")
        
        st.markdown("---")
        st.info("🔐 **Seguridad**: Tu contraseña será encriptada y nunca será almacenada en texto plano.")
        st.info("📧 **Verificación**: Recibirás un código de 6 dígitos en tu email para activar tu cuenta.")

    def verification_page(self):
        """Página de verificación de cuenta"""
        st.title("✅ Verificar Cuenta")
        st.markdown("---")
        
        st.info("📧 Ingresa tu email y el código de 6 dígitos que recibiste para activar tu cuenta.")
        
        with st.form("verification_form"):
            email = st.text_input("📧 Email", placeholder="Email usado en el registro")
            activation_code = st.text_input("🔢 Código de Activación", placeholder="Código de 6 dígitos", max_chars=6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                verify_submitted = st.form_submit_button("Verificar", type="primary", use_container_width=True)
            
            with col2:
                resend_submitted = st.form_submit_button("Reenviar Código", use_container_width=True)
            
            if verify_submitted:
                if email and activation_code:
                    if len(activation_code) != 6 or not activation_code.isdigit():
                        st.error("❌ El código debe tener exactamente 6 dígitos")
                    else:
                        with st.spinner("Verificando código..."):
                            result = self.auth_system.verify_activation_code(email, activation_code)
                        
                        if result['success']:
                            st.success("✅ " + result['message'])
                            st.balloons()
                            st.info("🔑 Ahora puedes iniciar sesión con tu usuario y contraseña.")
                        else:
                            st.error("❌ " + result['message'])
                else:
                    st.warning("⚠️ Por favor completa todos los campos")
            
            if resend_submitted:
                if email:
                    with st.spinner("Reenviando código..."):
                        result = self.auth_system.resend_activation_code(email)
                    
                    if result['success']:
                        st.success("✅ " + result['message'])
                    else:
                        st.error("❌ " + result['message'])
                else:
                    st.warning("⚠️ Ingresa tu email para reenviar el código")
        
        st.markdown("---")
        st.warning("⏰ **Importante**: Los códigos de activación expiran en 15 minutos.")
        st.info("📧 **¿No recibes el email?** Revisa tu carpeta de spam o solicita un nuevo código.")

    def dashboard_page(self):
        """Dashboard principal para usuarios autenticados"""
        user_data = st.session_state.user_data
        
        # Header con información del usuario
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.title(f"👋 Bienvenido, {user_data['username']}!")
        
        with col2:
            st.write(f"**Rol:** {user_data['role']}")
        
        with col3:
            if st.button("🚪 Cerrar Sesión", type="secondary"):
                st.session_state.authenticated = False
                st.session_state.user_data = None
                st.session_state.current_page = 'login'
                st.rerun()
        
        st.markdown("---")
        
        # Información del usuario
        with st.expander("👤 Información de la Cuenta", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📧 Email:** {user_data['email']}")
                st.write(f"**🆔 ID de Usuario:** {user_data['id']}")
            
            with col2:
                st.write(f"**👑 Rol:** {user_data['role']}")
                st.write(f"**✅ Estado:** Cuenta Verificada")
        
        # Contenido principal del dashboard
        st.markdown("### 📊 Panel Principal")
        
        # Aquí puedes agregar el contenido específico de tu aplicación
        tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "⚙️ Configuración", "📋 Reportes"])
        
        with tab1:
            st.info("🚧 Esta sección puede contener el dashboard principal de tu aplicación.")
            
            # Ejemplo de métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Usuarios", "150", "12")
            
            with col2:
                st.metric("Reportes Activos", "45", "-3")
            
            with col3:
                st.metric("Verificaciones", "89%", "5%")
            
            with col4:
                st.metric("Uptime", "99.9%", "0.1%")
        
        with tab2:
            st.info("⚙️ Aquí puedes agregar configuraciones específicas del usuario.")
            
            st.subheader("Preferencias de Usuario")
            
            theme = st.selectbox("🎨 Tema", ["Claro", "Oscuro", "Auto"])
            notifications = st.checkbox("📧 Recibir notificaciones por email", value=True)
            language = st.selectbox("🌍 Idioma", ["Español", "English"])
            
            if st.button("💾 Guardar Configuración"):
                st.success("✅ Configuración guardada exitosamente")
        
        with tab3:
            st.info("📋 Esta sección puede mostrar reportes específicos del usuario.")
            
            # Aquí puedes integrar con tu sistema existente de reportes
            st.write("Integración con sistema de reportes existente...")

    def run(self):
        """Ejecutar la aplicación"""
        st.set_page_config(
            page_title="Sistema de Autenticación",
            page_icon="🔐",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # CSS personalizado
        st.markdown("""
        <style>
        .stButton > button {
            border-radius: 10px;
            border: 1px solid #ddd;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stForm {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Verificar si el usuario está autenticado
        if st.session_state.authenticated:
            self.dashboard_page()
        else:
            # Mostrar navegación
            self.show_navigation()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mostrar página según selección
            if st.session_state.current_page == 'login':
                self.login_page()
            elif st.session_state.current_page == 'register':
                self.register_page()
            elif st.session_state.current_page == 'verify':
                self.verification_page()

def main():
    app = AuthenticationApp()
    app.run()

if __name__ == "__main__":
    main()
