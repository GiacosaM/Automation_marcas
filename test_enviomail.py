
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔹 Configuración del correo del cliente
SMTP_SERVER = "smtp.zoho.com"     # Servidor SMTP de Zoho
SMTP_PORT = 587                   # Puerto TLS
USER = "ivigo@mimarca.com.ar"   # Reemplazar con la cuenta del cliente
PASSWORD = "Igna2024*"   # Reemplazar con la pass del cliente

# 🔹 Destinatario (vos mismo para verificar que llega)
TO_EMAIL = "martingiacosa@gmail.com"

def enviar_correo_prueba():
    try:
        # Crear el mensaje
        msg = MIMEMultipart()
        msg["From"] = USER
        msg["To"] = "martingiacosa@gmail.com"
        msg["Subject"] = "Prueba de Envío desde cuenta del cliente"

        cuerpo = "Este es un correo de prueba enviado desde la cuenta del cliente."
        msg.attach(MIMEText(cuerpo, "plain"))

        # Conectar al servidor SMTP
        print(f"Conectando a {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Inicia conexión segura
        server.login(USER, PASSWORD)  # Login con las credenciales
        server.sendmail(USER, TO_EMAIL, msg.as_string())  # Enviar correo
        server.quit()

        print(f"✅ Correo enviado correctamente a {TO_EMAIL}")

    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

if __name__ == "__main__":
    enviar_correo_prueba()
