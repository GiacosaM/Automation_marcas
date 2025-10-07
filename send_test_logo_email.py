#!/usr/bin/env python3
"""
Script de prueba: construye y envía un solo email usando la misma lógica de logo embebido.
Envía el correo a martin_giacosa@hotmail.com. Usa las credenciales definidas por email_utils.obtener_credenciales().
"""
import os
import mimetypes
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from email_templates import get_html_template
from paths import get_assets_dir
from email_utils import obtener_credenciales


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('test_send_logo')

    creds = obtener_credenciales()
    if not creds:
        logger.error('No se obtuvieron credenciales desde email_utils.obtener_credenciales()')
        return

    email_user = creds.get('email')
    email_password = creds.get('password')
    email_host = creds.get('smtp_host')
    email_port = creds.get('smtp_port')

    if not all([email_user, email_password, email_host, email_port]):
        logger.error('Faltan campos en las credenciales: %s', creds)
        return

    try:
        email_port = int(email_port)
    except Exception:
        logger.warning('Puerto SMTP no es un entero, intentando usar como está: %s', email_port)

    destinatario = 'martin_giacosa@hotmail.com'

    # Datos simples para el cuerpo
    nombre_mes = datetime.now().strftime('%B')
    anio_reporte = datetime.now().year

    text_body = f"Estimado/a,\n\nEste es un correo de prueba para verificar el logo embebido (CID).\n\nSaludos."

    contenido_especifico = f"<p>Prueba de logo embebido para {nombre_mes} {anio_reporte}.</p>"

    html_template = get_html_template()
    html_content = html_template.replace('<!-- El contenido del mensaje se insertará aquí -->', contenido_especifico)

    # Crear estructura multipart/related
    msg_root = MIMEMultipart('related')
    msg_root['From'] = email_user
    msg_root['To'] = destinatario
    msg_root['Subject'] = f"[PRUEBA] Logo embebido - {nombre_mes} {anio_reporte}"

    msg_alternative = MIMEMultipart('alternative')
    msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg_alternative.attach(MIMEText(html_content, 'html', 'utf-8'))
    msg_root.attach(msg_alternative)

    # Buscar logo
    logo_path = os.path.join(get_assets_dir(), 'Logo.png')
    if not os.path.exists(logo_path):
        alt_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes', 'Logo.png'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes', 'Logo1.png'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logo.png')
        ]
        for p in alt_paths:
            if os.path.exists(p):
                logo_path = p
                break

    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                img_data = f.read()
                # Intentar detectar tipo MIME por extensión
                mime_type, _ = mimetypes.guess_type(logo_path)
                if mime_type and mime_type.startswith('image/'):
                    subtype = mime_type.split('/')[1]
                else:
                    # Fallback a la extensión
                    subtype = os.path.splitext(logo_path)[1].lstrip('.').lower() or 'png'
                img = MIMEImage(img_data, _subtype=subtype)
                img.add_header('Content-ID', '<logo>')
                img.add_header('Content-Disposition', 'inline; filename="Logo.png"')
                msg_root.attach(img)
                logger.info('Logo adjuntado desde %s con Content-ID <logo>', logo_path)
        except Exception as e:
            logger.warning('Error al adjuntar logo: %s', e)
    else:
        logger.warning('No se encontró el archivo de logo en ninguna ruta esperada. Buscado primermente: %s', logo_path)

    # Enviar
    try:
        server = smtplib.SMTP(email_host, email_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email_user, email_password)
        server.sendmail(email_user, [destinatario], msg_root.as_string())
        server.quit()
        logger.info('Correo de prueba enviado a %s', destinatario)
    except Exception as e:
        logger.error('Error al enviar correo de prueba: %s', e)


if __name__ == '__main__':
    main()
