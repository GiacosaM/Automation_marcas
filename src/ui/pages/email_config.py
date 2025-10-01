#!/usr/bin/env python3
"""
Página de configuración de email para el sistema de gestión de marcas.

Esta página permite configurar las credenciales de email para el envío
de notificaciones desde la aplicación. Las contraseñas se almacenan de 
forma segura usando el keyring del sistema operativo.
"""

import streamlit as st
import logging
from email_utils import (
    guardar_credenciales, 
    obtener_credenciales, 
    probar_envio,
    eliminar_credenciales
)

def show_email_config_page():
    """
    Muestra la página de configuración de email con el formulario
    para guardar y probar las credenciales de correo.
    """
    st.title("🔐 Configuración de Email")
    
    st.markdown("""
    Configure las credenciales para envío de correos electrónicos. 
    La contraseña se almacena de forma segura en el sistema usando keyring.
    """)
    
    # Obtener credenciales existentes (si hay)
    credenciales = obtener_credenciales()
    
    # Formulario para las credenciales
    with st.form("email_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Correo electrónico", 
                value=credenciales.get("email", "") if credenciales else "",
                help="Dirección de correo desde la que se enviarán notificaciones"
            )
            
            password = st.text_input(
                "Contraseña", 
                type="password",
                help="La contraseña se almacenará de forma segura en el sistema"
            )
        
        with col2:
            smtp_host = st.text_input(
                "Servidor SMTP", 
                value=credenciales.get("smtp_host", "smtp.gmail.com") if credenciales else "smtp.gmail.com",
                help="Ej: smtp.gmail.com, smtp.office365.com"
            )
            
            smtp_port = st.text_input(
                "Puerto SMTP", 
                value=str(credenciales.get("smtp_port", 587)) if credenciales else "587",
                help="Puerto para conexión TLS (generalmente 587)"
            )
        
        # Botones de acción
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            guardar = st.form_submit_button("💾 Guardar credenciales")
        with col2:
            probar = st.form_submit_button("📧 Probar conexión")
        with col3:
            eliminar = st.form_submit_button("🗑️ Eliminar credenciales", type="secondary")
        
        # Validar entrada y procesar formulario
        if guardar or probar:
            # Validaciones básicas
            if not email or not smtp_host or not smtp_port:
                st.error("Todos los campos son obligatorios")
                st.stop()
            
            try:
                smtp_port = int(smtp_port)
                if smtp_port <= 0:
                    raise ValueError()
            except ValueError:
                st.error("El puerto debe ser un número válido")
                st.stop()
                
            # Si es prueba, no necesita guardarse
            if probar:
                if not password and not credenciales:
                    st.error("Ingrese una contraseña para probar la conexión")
                    st.stop()
                
                # Usar la contraseña proporcionada o la almacenada
                test_password = password if password else credenciales.get("password", "")
                
                with st.spinner("Probando conexión..."):
                    success, message = probar_envio(email, smtp_host, smtp_port, test_password)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            # Si es guardar, almacenar credenciales
            if guardar:
                if not password and not credenciales:
                    st.error("Ingrese una contraseña para guardar las credenciales")
                    st.stop()
                
                # Usar la contraseña proporcionada o mantener la existente
                save_password = password if password else credenciales.get("password", "")
                
                with st.spinner("Guardando credenciales..."):
                    if guardar_credenciales(email, smtp_host, smtp_port, save_password):
                        st.success("Credenciales guardadas correctamente")
                    else:
                        st.error("Error al guardar las credenciales")
        
        # Eliminar credenciales
        if eliminar:
            with st.spinner("Eliminando credenciales..."):
                if eliminar_credenciales():
                    # Limpiar cualquier caché en la sesión
                    if 'email_credentials' in st.session_state:
                        del st.session_state['email_credentials']
                        
                    # Mostrar mensaje de éxito
                    st.success("✅ Credenciales eliminadas correctamente")
                    st.info("La aplicación reiniciará para aplicar los cambios...")
                    
                    # Esperar un momento para que se muestre el mensaje
                    import time
                    time.sleep(2)
                    
                    # Reiniciar la aplicación para reflejar los cambios
                    st.rerun()
                else:
                    st.error("❌ Error al eliminar las credenciales")
    
   

if __name__ == "__main__":
    # Configuración básica de logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar la página directamente (para pruebas)
    show_email_config_page()