import smtplib
import sqlite3
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_sender.log'),
        logging.StreamHandler()
    ]
)

# Configuración de email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def obtener_mensajes_predefinidos():
    """Diccionario con mensajes predefinidos según el valor de observaciones."""
    return {
        "1": """
        Estimado/a cliente,
        
        Le informamos que hemos encontrado marcas de su interés publicadas en el boletín oficial.
        Adjunto encontrará el reporte detallado con la información correspondiente.
        
        Quedamos a su disposición para cualquier consulta.
        
        Saludos cordiales.
        """,
        "2": """
        Estimado/a cliente,
        
        Le notificamos sobre nuevas publicaciones de marcas que requieren su atención inmediata.
        Por favor, revise el reporte adjunto para más detalles.
        
        Si necesita asesoramiento, no dude en contactarnos.
        
        Saludos cordiales.
        """,
        "3": """
        Estimado/a cliente,
        
        Hemos detectado marcas relacionadas con su área de interés en las últimas publicaciones.
        El reporte adjunto contiene toda la información relevante.
        
        Quedamos a su disposición.
        
        Saludos cordiales.
        """,
        "default": """
        Estimado/a cliente,
        
        Le enviamos el reporte de marcas correspondiente al período actual.
        Adjunto encontrará la información detallada.
        
        Saludos cordiales.
        """
    }

def obtener_registros_pendientes_envio(conn):
    """
    Obtiene todos los registros con reporte_generado=True y reporte_enviado=False
    agrupados por cliente.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id, b.titular, b.numero_boletin, b.fecha_boletin, 
                b.numero_orden, b.solicitante, b.agente, b.numero_expediente, 
                b.clase, b.marca_custodia, b.marca_publicada, b.clases_acta,
                b.observaciones, b.nombre_reporte, b.ruta_reporte,
                c.email, c.telefono, c.direccion, c.ciudad
            FROM boletines b
            LEFT JOIN clientes c ON b.titular = c.titular
            WHERE b.reporte_generado = 1 AND b.reporte_enviado = 0
            ORDER BY b.titular, b.numero_boletin
        """)
        
        rows = cursor.fetchall()
        
        # Agrupar por titular
        registros_por_cliente = {}
        for row in rows:
            titular = row[1]  # b.titular
            if titular not in registros_por_cliente:
                registros_por_cliente[titular] = {
                    'email': row[15],  # c.email
                    'telefono': row[16],  # c.telefono
                    'direccion': row[17],  # c.direccion
                    'ciudad': row[18],  # c.ciudad
                    'boletines': []
                }
            
            registros_por_cliente[titular]['boletines'].append({
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
                'ruta_reporte': row[14]
            })
        
        logging.info(f"Se encontraron {len(registros_por_cliente)} clientes con reportes pendientes de envío.")
        return registros_por_cliente
    
    except sqlite3.Error as e:
        logging.error(f"Error al obtener registros pendientes: {e}")
        raise Exception(f"Error al obtener registros pendientes: {e}")
    finally:
        cursor.close()

def crear_mensaje_email(titular, boletines_data, observaciones_principal=None):
    """
    Crea el contenido del mensaje de email basado en las observaciones.
    """
    mensajes = obtener_mensajes_predefinidos()
    
    # Usar la observación del primer boletín o la observación principal
    observacion_key = observaciones_principal or boletines_data[0].get('observaciones', 'default')
    mensaje_base = mensajes.get(str(observacion_key), mensajes['default'])
    
    # Agregar información de los boletines
    mensaje_detalle = f"\n\nDETALLE DE BOLETINES:\n"
    mensaje_detalle += "=" * 50 + "\n"
    
    for boletin in boletines_data:
        mensaje_detalle += f"""
Boletín: {boletin['numero_boletin']}
Fecha: {boletin['fecha_boletin']}
Orden: {boletin['numero_orden']}
Marca en Custodia: {boletin['marca_custodia']}
Marca Publicada: {boletin['marca_publicada']}
Clase: {boletin['clase']}
Expediente: {boletin['numero_expediente']}
Solicitante: {boletin['solicitante']}
Agente: {boletin['agente']}
{'-' * 30}
"""
    
    return mensaje_base + mensaje_detalle

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
                logging.warning(f"Archivo no encontrado: {ruta_completa}")
    
    return None, None

def enviar_email(destinatario, asunto, mensaje, archivo_adjunto=None, nombre_archivo=None, 
                email_usuario=None, password_usuario=None):
    """
    Envía un email con archivo adjunto opcional.
    """
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = email_usuario
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Agregar cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'plain', 'utf-8'))
        
        # Agregar archivo adjunto si existe
        if archivo_adjunto and os.path.exists(archivo_adjunto):
            with open(archivo_adjunto, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {nombre_archivo or os.path.basename(archivo_adjunto)}'
            )
            msg.attach(part)
            logging.info(f"Archivo adjunto agregado: {nombre_archivo}")
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_usuario, password_usuario)
        
        # Enviar email
        text = msg.as_string()
        server.sendmail(email_usuario, destinatario, text)
        server.quit()
        
        logging.info(f"Email enviado exitosamente a: {destinatario}")
        return True
    
    except Exception as e:
        logging.error(f"Error al enviar email a {destinatario}: {e}")
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

def procesar_envio_emails(conn, email_usuario, password_usuario):
    """
    Función principal para procesar y enviar todos los emails pendientes.
    """
    resultados = {
        'exitosos': [],
        'fallidos': [],
        'sin_email': [],
        'sin_archivo': []
    }
    
    try:
        # Obtener registros pendientes
        registros_por_cliente = obtener_registros_pendientes_envio(conn)
        
        if not registros_por_cliente:
            logging.info("No hay reportes pendientes de envío.")
            return resultados
        
        # Procesar cada cliente
        for titular, datos_cliente in registros_por_cliente.items():
            try:
                # Verificar si tiene email
                if not datos_cliente['email']:
                    logging.warning(f"Cliente {titular} no tiene email registrado.")
                    resultados['sin_email'].append(titular)
                    continue
                
                # Obtener archivo de reporte
                archivo_reporte, nombre_reporte = obtener_archivo_reporte(datos_cliente['boletines'])
                
                if not archivo_reporte:
                    logging.warning(f"No se encontró archivo de reporte para {titular}.")
                    resultados['sin_archivo'].append(titular)
                    continue
                
                # Crear mensaje
                mes_actual = datetime.now().strftime("%B %Y")
                asunto = f"Reporte de marcas encontradas en el periodo {mes_actual}"
                mensaje = crear_mensaje_email(titular, datos_cliente['boletines'])
                
                # Enviar email
                if enviar_email(
                    destinatario=datos_cliente['email'],
                    asunto=asunto,
                    mensaje=mensaje,
                    archivo_adjunto=archivo_reporte,
                    nombre_archivo=nombre_reporte,
                    email_usuario=email_usuario,
                    password_usuario=password_usuario
                ):
                    # Actualizar estado en base de datos
                    boletines_ids = [b['id'] for b in datos_cliente['boletines']]
                    actualizar_estado_envio(conn, boletines_ids)
                    
                    resultados['exitosos'].append({
                        'titular': titular,
                        'email': datos_cliente['email'],
                        'cantidad_boletines': len(datos_cliente['boletines'])
                    })
                else:
                    resultados['fallidos'].append({
                        'titular': titular,
                        'email': datos_cliente['email'],
                        'error': 'Error en envío de email'
                    })
            
            except Exception as e:
                logging.error(f"Error procesando cliente {titular}: {e}")
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
    """
    reporte = f"""
REPORTE DE ENVÍO DE EMAILS
==========================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ENVÍOS EXITOSOS: {len(resultados['exitosos'])}
"""
    
    for envio in resultados['exitosos']:
        reporte += f"- {envio['titular']} ({envio['email']}) - {envio['cantidad_boletines']} boletines\n"
    
    reporte += f"\nENVÍOS FALLIDOS: {len(resultados['fallidos'])}\n"
    for fallo in resultados['fallidos']:
        reporte += f"- {fallo['titular']} ({fallo['email']}) - Error: {fallo['error']}\n"
    
    reporte += f"\nCLIENTES SIN EMAIL: {len(resultados['sin_email'])}\n"
    for cliente in resultados['sin_email']:
        reporte += f"- {cliente}\n"
    
    reporte += f"\nCLIENTES SIN ARCHIVO DE REPORTE: {len(resultados['sin_archivo'])}\n"
    for cliente in resultados['sin_archivo']:
        reporte += f"- {cliente}\n"
    
    return reporte