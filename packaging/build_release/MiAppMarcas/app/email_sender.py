import smtplib
import sqlite3
import logging
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
import mimetypes
from email import encoders
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Importar funciones de logs desde database.py y paths.py
from database import insertar_log_envio
from paths import get_logs_dir
from email_utils import obtener_credenciales

# Configuración de logging optimizado para emails
logging.basicConfig(
    level=logging.WARNING,  # Solo registrar WARNING y ERROR por defecto
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(get_logs_dir(), 'email_sender.log')),
        logging.StreamHandler()
    ]
)

# Logger específico para eventos críticos de email
email_logger = logging.getLogger('email_events')
email_logger.setLevel(logging.INFO)
email_handler = logging.FileHandler(os.path.join(get_logs_dir(), 'boletines.log'))  # Usar el mismo archivo
email_handler.setFormatter(logging.Formatter('%(asctime)s - EMAIL - %(message)s'))
email_logger.addHandler(email_handler)
email_logger.propagate = False

# La configuración de email se obtiene dinámicamente con obtener_credenciales()
# en lugar de usar valores hardcodeados

def validar_email(email: str) -> bool:
    """
    Valida si un email tiene un formato correcto.
    """
    if not email:
        return False
    
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_credenciales_email(email_usuario: str, password_usuario: str) -> bool:
    """
    Valida las credenciales de email intentando conectar al servidor SMTP.
    """
    try:
        # Obtener la configuración de SMTP desde email_utils
        credenciales = obtener_credenciales()
        if not credenciales:
            raise Exception("No se pudieron obtener las credenciales de email")
        
        smtp_host = credenciales.get('smtp_host', 'smtp.gmail.com')  # Valor por defecto como fallback
        smtp_port = credenciales.get('smtp_port', 587)  # Valor por defecto como fallback
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(email_usuario, password_usuario)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Error validando credenciales: {e}")
        return False

def obtener_mensajes_predefinidos():
    """Diccionario con mensajes predefinidos según el valor de importancia."""
    return {
        "Alta": """
        Estimado/a,

        En virtud del servicio de custodia contratado sobre sus marcas, le informamos que, a partir del control mensual comparativo de presentaciones ante el INPI, se han detectado similitudes muy relevantes con sus registros, que a nuestro criterio ameritan ejercer el derecho de oposición de manera inmediata.
        Por tal motivo, le solicitamos se comunique a la mayor brevedad con nuestras oficinas,
        a fin de coordinar con nuestros profesionales las acciones necesarias para la protección de sus derechos marcarios.
        """,
        "Media": """
        Estimado/a,

        En virtud del servicio de custodia oportunamente contratado sobre sus marcas, le informamos que, como resultado del control mensual comparativo de presentaciones ante el INPI, se han detectado algunas similitudes leves con sus registros.
        Dichas coincidencias se detallan en el informe adjunto. A nuestro entender, no ameritan ejercer el derecho de oposición en esta instancia. No obstante, quedamos a su disposición para que, en caso de considerarlo necesario, pueda comunicarse con nuestros profesionales y evaluar conjuntamente los pasos a seguir.

        Saludos cordiales.
        """,
        "Baja": """
        Estimado/a,

        En virtud del servicio de custodia oportunamente contratado sobre sus marcas, le informamos que, como resultado del control mensual comparativo de presentaciones ante el INPI, se han detectado algunas similitudes leves con sus registros.
        Dichas coincidencias se detallan en el informe adjunto. A nuestro entender, no ameritan ejercer el derecho de oposición en esta instancia. No obstante, quedamos a su disposición para que, en caso de considerarlo necesario, pueda comunicarse con nuestros profesionales y evaluar conjuntamente los pasos a seguir.

        
        Saludos cordiales.
        """,
        "default": """
        Estimado/a,
        
        En virtud del servicio de custodia oportunamente contratado sobre sus marcas, nos complace informarle que hemos realizado el control mensual comparativo de presentaciones ante el INPI. Como resultado, nuestro sistema no ha detectado marcas similares que pudieran afectar los derechos que estamos protegiendo sobre sus registros.
        
        Saludos cordiales.
        """
    }

def obtener_info_reportes_pendientes(conn):
    """
    Obtiene información detallada sobre reportes con importancia 'Pendiente'.
    Retorna un diccionario con la información para mostrar al usuario.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                titular, COUNT(*) as cantidad,
                GROUP_CONCAT(numero_boletin) as boletines,
                GROUP_CONCAT(marca_publicada) as marcas
            FROM boletines 
            WHERE reporte_generado = 1 AND reporte_enviado = 0 
            AND importancia = 'Pendiente'
            GROUP BY titular
            ORDER BY titular
        """)
        
        rows = cursor.fetchall()
        
        info_pendientes = {
            'total_reportes': 0,
            'total_titulares': len(rows),
            'detalles': []
        }
        
        for row in rows:
            titular, cantidad, boletines, marcas = row
            info_pendientes['total_reportes'] += cantidad
            info_pendientes['detalles'].append({
                'titular': titular,
                'cantidad': cantidad,
                'boletines': boletines.split(',') if boletines else [],
                'marcas': marcas.split(',') if marcas else []
            })
        
        return info_pendientes
    
    except sqlite3.Error as e:
        logging.error(f"Error al obtener información de reportes pendientes: {e}")
        return None
    finally:
        cursor.close()

def obtener_registros_pendientes_envio(conn):
    """
    Obtiene todos los registros con reporte_generado=True, reporte_enviado=False
    y importancia IN ('Baja', 'Media', 'Alta'), agrupados por (titular, importancia).
    También verifica si hay reportes con importancia 'Pendiente' que bloquean el envío.
    
    NUEVA LÓGICA: Un titular con múltiples importancias recibirá múltiples emails separados.
    """
    try:
        cursor = conn.cursor()
        
        # Primero verificar si hay reportes con importancia 'Pendiente'
        cursor.execute("""
            SELECT COUNT(*) as pendientes_count, 
                   GROUP_CONCAT(DISTINCT titular) as titulares_pendientes
            FROM boletines 
            WHERE reporte_generado = 1 AND reporte_enviado = 0 
            AND importancia = 'Pendiente'
        """)
        
        pendientes_result = cursor.fetchone()
        pendientes_count = pendientes_result[0] if pendientes_result else 0
        titulares_pendientes = pendientes_result[1] if pendientes_result else None
        
        if pendientes_count > 0:
            titulares_list = titulares_pendientes.split(',') if titulares_pendientes else []
            logging.warning(f"Se encontraron {pendientes_count} reportes con importancia 'Pendiente' que requieren revisión.")
            logging.warning(f"Titulares afectados: {', '.join(titulares_list)}")
            raise Exception(f"No se pueden enviar emails: hay {pendientes_count} reportes con importancia 'Pendiente' que requieren revisión manual. Titulares: {', '.join(titulares_list)}")
        
        # Si no hay pendientes, proceder con la consulta normal
        cursor.execute("""
            SELECT 
                b.id, b.titular, b.numero_boletin, b.fecha_boletin, 
                b.numero_orden, b.solicitante, b.agente, b.numero_expediente, 
                b.clase, b.marca_custodia, b.marca_publicada, b.clases_acta,
                b.observaciones, b.nombre_reporte, b.ruta_reporte, b.importancia,
                c.email, c.telefono, c.direccion, c.ciudad
            FROM boletines b
            LEFT JOIN clientes c ON b.titular = c.titular
            WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0 
            AND b.importancia IN ('Baja', 'Media', 'Alta')
            ORDER BY b.titular, b.importancia, b.numero_boletin
        """)
        
        rows = cursor.fetchall()
        
        # NUEVA LÓGICA: Agrupar por (titular, importancia)
        from collections import defaultdict
        registros_por_grupo = defaultdict(lambda: {
            'email': None,
            'telefono': None,
            'direccion': None,
            'ciudad': None,
            'boletines': []
        })
        
        for row in rows:
            titular = row[1]  # b.titular
            importancia = row[15]  # b.importancia
            clave_grupo = (titular, importancia)
            
            # Asignar datos del cliente (solo la primera vez)
            if not registros_por_grupo[clave_grupo]['email']:
                registros_por_grupo[clave_grupo]['email'] = row[16]  # c.email
                registros_por_grupo[clave_grupo]['telefono'] = row[17]  # c.telefono
                registros_por_grupo[clave_grupo]['direccion'] = row[18]  # c.direccion
                registros_por_grupo[clave_grupo]['ciudad'] = row[19]  # c.ciudad
            
            registros_por_grupo[clave_grupo]['boletines'].append({
                'id': row[0],
                'numero_boletin': row[2],
                'fecha_boletin': row[3],
                'numero_orden': row[4],
                'solicitante': row[5],
                'agente': row[6],
                'numero_expediente': row[7],
                'clase': row[8],
                'marca_custodia': row[9],
                'marca_publicada': row[10],
                'clases_acta': row[11],
                'observaciones': row[12],
                'nombre_reporte': row[13],
                'ruta_reporte': row[14],
                'importancia': row[15]
            })
        
        # Convertir a diccionario normal con claves string
        registros_por_cliente_importancia = {}
        for (titular, importancia), datos in registros_por_grupo.items():
            clave = f"{titular}|{importancia}"
            registros_por_cliente_importancia[clave] = datos
            registros_por_cliente_importancia[clave]['titular'] = titular
            registros_por_cliente_importancia[clave]['importancia'] = importancia
        
        titulares_unicos = len(set(clave.split('|')[0] for clave in registros_por_cliente_importancia.keys()))
        # Solo log para procesos de envío importantes
        email_logger.info(f"📊 Procesando envíos: {len(registros_por_cliente_importancia)} grupos, {titulares_unicos} titulares únicos")
        return registros_por_cliente_importancia
    
    except sqlite3.Error as e:
        logging.error(f"Error al obtener registros pendientes: {e}")
        raise Exception(f"Error al obtener registros pendientes: {e}")
    finally:
        cursor.close()

def determinar_importancia_principal(boletines_data):
    """
    Determina el nivel de importancia más alto entre los boletines.
    Prioridad: Alta > Media > Baja
    """
    prioridad = {
        'Alta': 3,
        'Media': 2,
        'Baja': 1
    }
    
    max_importancia = 'Baja'
    max_prioridad = -1
    
    for boletin in boletines_data:
        importancia = boletin.get('importancia', 'Baja')
        if importancia in prioridad and prioridad[importancia] > max_prioridad:
            max_prioridad = prioridad[importancia]
            max_importancia = importancia
    
    return max_importancia

def crear_mensaje_email(titular, importancia, boletines_data):
    """
    Crea el contenido del mensaje de email basado en la importancia específica del grupo.
    NUEVA LÓGICA: Usa directamente la importancia del grupo (titular + importancia).
    Ahora retorna tanto la versión texto plano como la versión HTML.
    """
    # Importar la plantilla HTML
    from email_templates import get_html_template, get_html_message_by_importance
    
    # Versión texto plano (mantener para compatibilidad)
    mensajes = obtener_mensajes_predefinidos()
    mensaje_texto = mensajes.get(importancia, mensajes['default'])
    
    # Versión HTML
    html_content = get_html_template()
    
    # Reemplazar el contenido del mensaje según la importancia
    mensaje_html_contenido = get_html_message_by_importance(importancia)
    html_content = html_content.replace('<!-- El contenido del mensaje se insertará aquí -->', mensaje_html_contenido)
    
    return {
        'texto': mensaje_texto,
        'html': html_content
    }

def obtener_archivo_reporte(boletines_data):
    """
    Obtiene la ruta del archivo de reporte a adjuntar.
    Usa el primer boletín que tenga archivo de reporte.
    """
    for boletin in boletines_data:
        if boletin.get('ruta_reporte') and boletin.get('nombre_reporte'):
            ruta_completa = boletin['ruta_reporte']
            if os.path.exists(ruta_completa):
                return ruta_completa, boletin['nombre_reporte']
            else:
                # Solo log archivos faltantes críticos
                if not archivo_adjunto:
                    email_logger.warning(f"⚠️ Archivo de reporte faltante para {titular} ({importancia})")
    
    return None, None

def enviar_email(destinatario, asunto, mensaje, archivo_adjunto=None, nombre_archivo=None, 
                email_usuario=None, password_usuario=None):
    """
    Envía un email con archivo adjunto opcional.
    Soporta contenido HTML y texto plano como fallback.
    Incluye validaciones mejoradas.
    """
    try:
        # Validar email del destinatario
        if not validar_email(destinatario):
            raise Exception(f"Email del destinatario no válido: {destinatario}")
        
        # Validar email del remitente
        if not validar_email(email_usuario):
            raise Exception(f"Email del remitente no válido: {email_usuario}")
        
        # Crear mensaje con estructura multipart/related -> multipart/alternative (texto + html)
        msg_root = MIMEMultipart('related')
        msg_alternative = MIMEMultipart('alternative')
        msg_root['From'] = f"Estudio de Marcas y Patentes <{email_usuario}>"
        msg_root['To'] = destinatario
        msg_root['Subject'] = asunto

        # Adjuntar texto y html al alternative
        if isinstance(mensaje, dict) and 'texto' in mensaje and 'html' in mensaje:
            msg_alternative.attach(MIMEText(mensaje['texto'], 'plain', 'utf-8'))
            msg_alternative.attach(MIMEText(mensaje['html'], 'html', 'utf-8'))
        else:
            msg_alternative.attach(MIMEText(mensaje, 'plain', 'utf-8'))

        # Adjuntar alternative al root
        msg_root.attach(msg_alternative)

        # Agregar logo si existe (mismo comportamiento que verificar_titulares_sin_reportes.py)
        from paths import get_assets_dir
        logo_path = os.path.join(get_assets_dir(), 'Logo.png')
        # Buscar también en otras ubicaciones posibles si no existe en assets
        if not os.path.exists(logo_path):
            alt_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes', 'Logo.png'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes', 'Logo1.png'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logo.png')
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    logo_path = path
                    break

        if os.path.exists(logo_path):
            try:
                with open(logo_path, 'rb') as img_file:
                    img_data = img_file.read()
                    # Intentar detectar tipo MIME por extensión
                    mime_type, _ = mimetypes.guess_type(logo_path)
                    if mime_type and mime_type.startswith('image/'):
                        subtype = mime_type.split('/')[1]
                    else:
                        ext = os.path.splitext(logo_path)[1].lstrip('.').lower()
                        subtype = ext if ext else 'png'
                    img = MIMEImage(img_data, _subtype=subtype)
                    # Asegurarse de que el Content-ID coincida exactamente con cid:logo usado en la plantilla
                    img.add_header('Content-ID', '<logo>')
                    img.add_header('Content-Disposition', 'inline; filename="Logo.png"')
                    msg_root.attach(img)
                    logger.info(f"Logo adjuntado desde {logo_path} con Content-ID <logo>")
            except Exception as e:
                logging.warning(f"Error al adjuntar logo: {e}")
        else:
            logging.warning(f"No se encontró el archivo de logo en ninguna ruta esperada. Buscado: {logo_path}")
        
        # Agregar archivo adjunto si existe
        if archivo_adjunto and os.path.exists(archivo_adjunto):
            try:
                with open(archivo_adjunto, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {nombre_archivo or os.path.basename(archivo_adjunto)}'
                )
                msg_root.attach(part)
                logging.info(f"Archivo adjunto agregado: {nombre_archivo}")
            except Exception as e:
                logging.warning(f"Error al adjuntar archivo: {e}")
                # Continuar sin archivo adjunto
        elif archivo_adjunto:
            logging.warning(f"Archivo adjunto no encontrado: {archivo_adjunto}")
        
        # Obtener la configuración de SMTP desde email_utils
        credenciales = obtener_credenciales()
        if not credenciales:
            raise Exception("No se pudieron obtener las credenciales de email")
        
        smtp_host = credenciales.get('smtp_host', 'smtp.gmail.com')  # Valor por defecto como fallback
        smtp_port = credenciales.get('smtp_port', 587)  # Valor por defecto como fallback
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(email_usuario, password_usuario)
        
        # Enviar email (usar msg_root si existe, sino msg para compatibilidad)
        if 'msg_root' in locals():
            text = msg_root.as_string()
        elif 'msg' in locals():
            text = msg.as_string()
        else:
            raise Exception("No se encontró el mensaje para enviar (msg_root/msg)")

        server.sendmail(email_usuario, destinatario, text)
        server.quit()
        
        email_logger.info(f"📧 Email enviado exitosamente: {destinatario}")
        return True
        
    except Exception as e:
        email_logger.error(f"❌ Error al enviar email a {destinatario}: {e}")
        return False

def actualizar_estado_envio(conn, boletines_ids):
    """
    Actualiza el campo reporte_enviado a TRUE para los boletines especificados.
    """
    try:
        cursor = conn.cursor()
        ids_placeholder = ','.join(['?' for _ in boletines_ids])
        
        cursor.execute(f"""
            UPDATE boletines 
            SET reporte_enviado = 1, fecha_envio_reporte = datetime('now', 'localtime')
            WHERE id IN ({ids_placeholder})
        """, boletines_ids)
        
        conn.commit()
        logging.info(f"Estado de envío actualizado para {len(boletines_ids)} registros.")
    
    except sqlite3.Error as e:
        logging.error(f"Error al actualizar estado de envío: {e}")
        raise Exception(f"Error al actualizar estado de envío: {e}")
    finally:
        cursor.close()

def validar_clientes_para_envio(conn):
    """
    Valida los grupos (titular + importancia) antes del envío de emails y retorna un reporte de validación.
    NUEVA LÓGICA: Validación por grupo (titular + importancia) en lugar de solo titular.
    
    Returns:
        dict: Información sobre la validación de grupos
    """
    validacion = {
        'total_grupos': 0,
        'con_email': 0,
        'sin_email': [],
        'con_reporte': 0,
        'sin_reporte': [],
        'listos_para_envio': 0,
        'puede_continuar': True,
        'mensajes': []
    }
    
    try:
        # Obtener registros pendientes de envío agrupados por (titular + importancia)
        registros_por_grupo = obtener_registros_pendientes_envio(conn)
        
        if not registros_por_grupo:
            validacion['mensajes'].append("No hay reportes pendientes de envío.")
            return validacion
        
        validacion['total_grupos'] = len(registros_por_grupo)
        
        # Analizar cada grupo (titular + importancia)
        for clave_grupo, datos_grupo in registros_por_grupo.items():
            titular = datos_grupo['titular']
            importancia = datos_grupo['importancia']
            identificador_grupo = f"{titular} ({importancia})"
            
            # Verificar si tiene email
            if not datos_grupo['email'] or not datos_grupo['email'].strip():
                validacion['sin_email'].append(identificador_grupo)
                validacion['mensajes'].append(f"⚠️ Grupo '{identificador_grupo}' no tiene email registrado")
            else:
                validacion['con_email'] += 1
            
            # Verificar si tiene archivo de reporte
            archivo_reporte, _ = obtener_archivo_reporte(datos_grupo['boletines'])
            if not archivo_reporte:
                validacion['sin_reporte'].append(identificador_grupo)
                validacion['mensajes'].append(f"⚠️ Grupo '{identificador_grupo}' no tiene archivo de reporte")
            else:
                validacion['con_reporte'] += 1
            
            # Grupo listo si tiene email Y reporte
            if (datos_grupo['email'] and datos_grupo['email'].strip() and archivo_reporte):
                validacion['listos_para_envio'] += 1
        
        # Agregar mensajes de resumen
        if validacion['sin_email']:
            validacion['mensajes'].append(f"📧 {len(validacion['sin_email'])} grupos sin email no recibirán reportes")
        
        if validacion['sin_reporte']:
            validacion['mensajes'].append(f"📄 {len(validacion['sin_reporte'])} grupos sin archivo de reporte")
        
        if validacion['listos_para_envio'] == 0:
            validacion['puede_continuar'] = False
            validacion['mensajes'].append("❌ No hay grupos listos para recibir emails")
        else:
            validacion['mensajes'].append(f"✅ {validacion['listos_para_envio']} grupos listos para recibir emails")
    
    except Exception as e:
        validacion['puede_continuar'] = False
        validacion['mensajes'].append(f"❌ Error durante la validación: {str(e)}")
        logging.error(f"Error en validación de grupos: {e}")
    
    return validacion

def procesar_envio_emails(conn, email_usuario=None, password_usuario=None):
    """
    Función principal para procesar y enviar todos los emails pendientes.
    Incluye validación de reportes con importancia 'Pendiente'.
    """
    # Obtener credenciales desde email_utils si no se proporcionan
    if email_usuario is None or password_usuario is None:
        credenciales = obtener_credenciales()
        if credenciales:
            email_usuario = credenciales.get('email')
            password_usuario = credenciales.get('password')
    
    resultados = {
        'exitosos': [],
        'fallidos': [],
        'sin_email': [],
        'sin_archivo': [],
        'bloqueado_por_pendientes': False,
        'info_pendientes': None
    }
    
    try:
        # Verificar primero si hay reportes pendientes que bloqueen el envío
        try:
            registros_por_cliente = obtener_registros_pendientes_envio(conn)
        except Exception as validation_error:
            # Si hay reportes pendientes, obtener información detallada
            info_pendientes = obtener_info_reportes_pendientes(conn)
            resultados['bloqueado_por_pendientes'] = True
            resultados['info_pendientes'] = info_pendientes
            
            logging.error(f"Envío bloqueado: {str(validation_error)}")
            return resultados
        
        if not registros_por_cliente:
            logging.info("No hay reportes pendientes de envío.")
            return resultados
        
        # Validar credenciales de email antes de procesar
        if not validar_credenciales_email(email_usuario, password_usuario):
            raise Exception("Credenciales de email inválidas. Verifique su email y contraseña.")
        
        # NUEVA LÓGICA: Procesar cada grupo (titular + importancia)
        for clave_grupo, datos_grupo in registros_por_cliente.items():
            try:
                titular = datos_grupo['titular']
                importancia = datos_grupo['importancia']
                
                # Verificar si tiene email
                if not datos_grupo['email']:
                    logging.warning(f"Grupo {titular} ({importancia}) no tiene email registrado.")
                    resultados['sin_email'].append(f"{titular} ({importancia})")
                    
                    # Registrar en logs
                    try:
                        insertar_log_envio(conn, titular, 'N/A', 'sin_email', 'Cliente sin email registrado', 'N/A', importancia)
                    except Exception as log_error:
                        logging.error(f"Error registrando log: {log_error}")
                    
                    continue
                
                # Obtener archivo de reporte específico para esta importancia
                archivo_reporte, nombre_reporte = obtener_archivo_reporte(datos_grupo['boletines'])
                
                if not archivo_reporte:
                    logging.warning(f"No se encontró archivo de reporte para {titular} ({importancia}).")
                    resultados['sin_archivo'].append(f"{titular} ({importancia})")
                    
                    # Registrar en logs
                    try:
                        insertar_log_envio(conn, titular, datos_grupo['email'], 'sin_archivo', 'Archivo de reporte no encontrado', 'N/A', importancia)
                    except Exception as log_error:
                        logging.error(f"Error registrando log: {log_error}")
                    
                    continue
                
                # Crear mensaje específico para esta importancia
                # Formatear mes en español (no depender de locale del sistema)
                now = datetime.now()
                meses_es = [
                    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
                ]
                mes_anterior = f"{meses_es[now.month - 2].capitalize()} {now.year}" if now.month > 1 else f"Diciembre {now.year - 1}"
                
                # Personalizar el asunto según la importancia
                if importancia.lower() == 'baja':
                    asunto = f"Custodia de Marcas con deteccion de similares  - {mes_anterior}"
                else:
                    asunto = f"Custodia de Marcas con deteccion de similitudes relevantes - {mes_anterior}"
            
                mensaje = crear_mensaje_email(titular, importancia, datos_grupo['boletines'])
                
                # Enviar email
                if enviar_email(
                    destinatario=datos_grupo['email'],
                    asunto=asunto,
                    mensaje=mensaje,
                    archivo_adjunto=archivo_reporte,
                    nombre_archivo=nombre_reporte,
                    email_usuario=email_usuario,
                    password_usuario=password_usuario
                ):
                    # Actualizar estado en base de datos
                    boletines_ids = [b['id'] for b in datos_grupo['boletines']]
                    actualizar_estado_envio(conn, boletines_ids)
                    
                    # Registrar envío exitoso en logs
                    try:
                        # Obtener información del primer boletín para los logs
                        primer_boletin = datos_grupo['boletines'][0] if datos_grupo['boletines'] else {}
                        numero_boletin = primer_boletin.get('numero_boletin', 'N/A')
                        
                        insertar_log_envio(
                            conn, 
                            titular, 
                            datos_grupo['email'], 
                            'exitoso', 
                            None, 
                            numero_boletin, 
                            importancia
                        )
                    except Exception as log_error:
                        logging.error(f"Error registrando log exitoso: {log_error}")
                    
                    resultados['exitosos'].append({
                        'titular': titular,
                        'importancia': importancia,
                        'email': datos_grupo['email'],
                        'cantidad_boletines': len(datos_grupo['boletines'])
                    })
                else:
                    # Registrar envío fallido en logs
                    try:
                        primer_boletin = datos_grupo['boletines'][0] if datos_grupo['boletines'] else {}
                        numero_boletin = primer_boletin.get('numero_boletin', 'N/A')
                        
                        insertar_log_envio(
                            conn, 
                            titular, 
                            datos_grupo['email'], 
                            'fallido', 
                            'Error en envío de email', 
                            numero_boletin, 
                            importancia
                        )
                    except Exception as log_error:
                        logging.error(f"Error registrando log fallido: {log_error}")
                    
                    resultados['fallidos'].append({
                        'titular': titular,
                        'importancia': importancia,
                        'email': datos_grupo['email'],
                        'error': 'Error en envío de email'
                    })
            
            except Exception as e:
                titular = datos_grupo.get('titular', 'N/A')
                importancia = datos_grupo.get('importancia', 'N/A')
                logging.error(f"Error procesando grupo {titular} ({importancia}): {e}")
                resultados['fallidos'].append({
                    'titular': titular,
                    'importancia': importancia,
                    'email': datos_grupo.get('email', 'N/A'),
                    'error': str(e)
                })
            
            except Exception as e:
                logging.error(f"Error procesando cliente Compose a response in Spanish: {titular}: {e}")
                resultados['fallidos'].append({
                    'titular': titular,
                    'email': datos_cliente.get('email', 'N/A'),
                    'error': str(e)
                })
    
    except Exception as e:
        logging.error(f"Error general en procesamiento de emails: {e}")
        raise Exception(f"Error general en procesamiento de emails: {e}")
    
    return resultados

def generar_reporte_envios(resultados):
    """
    Genera un reporte de los resultados del envío de emails.
    Incluye información sobre reportes bloqueados por importancia 'Pendiente'.
    """
    reporte = f"""
REPORTE DE ENVÍO DE EMAILS
==========================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    # Si el envío fue bloqueado por reportes pendientes
    if resultados.get('bloqueado_por_pendientes', False):
        reporte += "⚠️  ENVÍO BLOQUEADO POR REPORTES PENDIENTES ⚠️\n"
        reporte += "=" * 50 + "\n"
        
        info_pendientes = resultados.get('info_pendientes')
        if info_pendientes:
            reporte += f"Total de reportes pendientes: {info_pendientes['total_reportes']}\n"
            reporte += f"Titulares afectados: {info_pendientes['total_titulares']}\n\n"
            
            reporte += "DETALLE POR TITULAR:\n"
            for detalle in info_pendientes['detalles']:
                reporte += f"- {detalle['titular']}: {detalle['cantidad']} reportes\n"
                reporte += f"  Boletines: {', '.join(detalle['boletines'][:5])}{'...' if len(detalle['boletines']) > 5 else ''}\n"
            
            reporte += "\n🔧 ACCIÓN REQUERIDA:\n"
            reporte += "Por favor revise y asigne importancia (Alta/Media/Baja) a los reportes marcados como 'Pendiente'\n"
            reporte += "antes de intentar enviar los emails nuevamente.\n\n"
        
        return reporte
    
    # Reporte normal si no hay bloqueos
    reporte += f"ENVÍOS EXITOSOS: {len(resultados['exitosos'])}\n"
    for envio in resultados['exitosos']:
        reporte += f"✅ {envio['titular']} ({envio['email']}) - {envio['cantidad_boletines']} boletines\n"
    
    reporte += f"\nENVÍOS FALLIDOS: {len(resultados['fallidos'])}\n"
    for fallo in resultados['fallidos']:
        reporte += f"❌ {fallo['titular']} ({fallo['email']}) - Error: {fallo['error']}\n"
    
    reporte += f"\nCLIENTES SIN EMAIL: {len(resultados['sin_email'])}\n"
    for cliente in resultados['sin_email']:
        reporte += f"📧 {cliente}\n"
    
    reporte += f"\nCLIENTES SIN ARCHIVO DE REPORTE: {len(resultados['sin_archivo'])}\n"
    for cliente in resultados['sin_archivo']:
        reporte += f"📄 {cliente}\n"
    
    # Resumen final
    total_procesados = len(resultados['exitosos']) + len(resultados['fallidos'])
    if total_procesados > 0:
        tasa_exito = (len(resultados['exitosos']) / total_procesados) * 100
        reporte += f"\n📊 RESUMEN:\n"
        reporte += f"Tasa de éxito: {tasa_exito:.1f}%\n"
        reporte += f"Emails enviados exitosamente: {len(resultados['exitosos'])}\n"
        reporte += f"Total intentos: {total_procesados}\n"
    
    return reporte

def obtener_estadisticas_envios(conn):
    """
    Obtiene estadísticas generales sobre el estado de los envíos.
    """
    try:
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reportes,
                COUNT(CASE WHEN reporte_generado = 1 THEN 1 END) as reportes_generados,
                COUNT(CASE WHEN reporte_enviado = 1 THEN 1 END) as reportes_enviados,
                COUNT(CASE WHEN importancia = 'Pendiente' AND reporte_generado = 1 THEN 1 END) as pendientes_revision,
                COUNT(CASE WHEN reporte_generado = 1 AND reporte_enviado = 0 AND importancia IN ('Alta', 'Media', 'Baja') THEN 1 END) as listos_envio
            FROM boletines
        """)
        
        stats = cursor.fetchone()
        
        return {
            'total_reportes': stats[0],
            'reportes_generados': stats[1],
            'reportes_enviados': stats[2],
            'pendientes_revision': stats[3],
            'listos_envio': stats[4]
        }
    
    except sqlite3.Error as e:
        logging.error(f"Error al obtener estadísticas: {e}")
        return None
    finally:
        cursor.close()