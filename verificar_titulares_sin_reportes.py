"""
Módulo para verificar marcas sin reportes durante el mes en curso
"""

import smtplib
import sqlite3
import logging
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import calendar
from datetime import timedelta

# Función para obtener credenciales de email utilizando email_utils.py
def obtener_credenciales_email():
    """
    Obtiene las credenciales de email usando la función obtener_credenciales() de email_utils.py.

    Returns:
        tuple: (email_user, email_password, email_host, email_port)
    """
    from email_utils import obtener_credenciales
    
    try:
        # Obtener credenciales usando la función de email_utils.py
        credentials = obtener_credenciales()
        
        if not credentials:
            logging.error("No se encontraron credenciales de email")
            return None, None, None, None
            
        # Extraer valores del diccionario
        email_user = credentials.get('email')
        email_password = credentials.get('password')
        email_host = credentials.get('smtp_host')
        email_port = credentials.get('smtp_port')
        
        # Verificar que tenemos todos los datos necesarios
        if not all([email_user, email_password, email_host, email_port]):
            raise ValueError("Faltan campos obligatorios en las credenciales")
        
        # Asegurar que el puerto sea un entero
        try:
            email_port = int(email_port)
        except (TypeError, ValueError):
            raise ValueError(f"El puerto SMTP debe ser un número válido, se recibió: {email_port}")
        
        logging.info("Credenciales obtenidas correctamente desde email_utils")
        return email_user, email_password, email_host, email_port
        
    except Exception as e:
        logging.error(f"Error al obtener credenciales de email: {e}")
        return None, None, None, None

# Configuración de logging
from paths import get_logs_dir
import os

# Crear ruta al archivo de log usando la función de paths.py
log_file_path = os.path.join(get_logs_dir(), 'boletines.log')

# Configurar logging para registrar solo WARNING, ERROR y CRITICAL
logging.basicConfig(
    level=logging.WARNING,  # Cambio de INFO a WARNING para reducir mensajes
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('verificacion_reportes')
# Ya no registramos mensaje INFO de creación de archivo

def obtener_nombre_mes(numero_mes):
    """Retorna el nombre del mes en español dado su número (1-12)"""
    nombres_meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    # Ajustamos el índice ya que los meses van de 1-12 pero los índices de 0-11
    return nombres_meses[numero_mes - 1]

def verificar_titulares_sin_reportes(conn):
    """
    Verifica las marcas que no tienen reportes generados durante el mes en curso
    y envía un correo electrónico de notificación al titular listando todas las marcas afectadas.
    
    Args:
        conn: Conexión a la base de datos SQLite
    
    Returns:
        dict: Un diccionario con información sobre el resultado de la verificación y envío
    """
    try:
        # Obtener el mes y año actual
        fecha_actual = datetime.now()
        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year
        
        # Calcular el primer y último día del mes pasado
        primer_dia_mes_pasado = (fecha_actual.replace(day=1) - timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_pasado = fecha_actual.replace(day=1) - timedelta(days=1)
        
        # Usar el mes y año del mes pasado para el reporte
        mes_reporte = primer_dia_mes_pasado.month
        anio_reporte = primer_dia_mes_pasado.year
        nombre_mes = obtener_nombre_mes(mes_reporte)
        
        # Definir el periodo actual como string (formato: MM-YYYY)
        periodo_actual = f"{mes_actual:02d}-{anio_actual}"

        primer_dia = primer_dia_mes_pasado.strftime("%Y-%m-%d")
        ultimo_dia = ultimo_dia_mes_pasado.strftime("%Y-%m-%d")
        
        logger.info(f"Verificando marcas sin reportes entre {primer_dia} y {ultimo_dia}")
        
        cursor = conn.cursor()
        
        # Obtener todos los titulares únicos con sus emails
        cursor.execute("""
            SELECT DISTINCT m.titular, c.email 
            FROM Marcas m
            JOIN clientes c ON m.titular = c.titular
            WHERE c.email IS NOT NULL AND c.email != ''
        """)
        
        titulares = cursor.fetchall()
        
        if not titulares:
            logger.warning("No se encontraron titulares con emails registrados")
            return {"estado": "error", "mensaje": "No hay titulares con emails registrados"}
        
        # Inicializar contadores
        titulares_con_marcas_sin_reportes = []
        emails_enviados = 0
        ya_notificados = 0
        errores = 0
        
        # Verificar si existen las columnas necesarias en la tabla emails_enviados
        cursor.execute("PRAGMA table_info(emails_enviados)")
        columnas = [col[1] for col in cursor.fetchall()]
        tiene_columna_periodo = 'periodo_notificacion' in columnas
        tiene_columna_marcas = 'marcas_sin_reportes' in columnas
        
        if not tiene_columna_periodo:
            logger.warning("La tabla emails_enviados no tiene la columna periodo_notificacion. Se intentará agregarla.")
            try:
                cursor.execute("""
                    ALTER TABLE emails_enviados 
                    ADD COLUMN periodo_notificacion TEXT DEFAULT NULL
                """)
                conn.commit()
                tiene_columna_periodo = True
                logger.info("Columna periodo_notificacion agregada correctamente")
            except Exception as e:
                logger.error(f"No se pudo agregar la columna periodo_notificacion: {e}")
        
        if not tiene_columna_marcas:
            logger.warning("La tabla emails_enviados no tiene la columna marcas_sin_reportes. Se intentará agregarla.")
            try:
                cursor.execute("""
                    ALTER TABLE emails_enviados 
                    ADD COLUMN marcas_sin_reportes TEXT DEFAULT NULL
                """)
                conn.commit()
                tiene_columna_marcas = True
                logger.info("Columna marcas_sin_reportes agregada correctamente")
            except Exception as e:
                logger.error(f"No se pudo agregar la columna marcas_sin_reportes: {e}")
        
        for titular, email in titulares:
            # Obtener todas las marcas del titular
            cursor.execute("""
                SELECT codigo_marca, marca, clase 
                FROM Marcas 
                WHERE titular = ?
            """, (titular,))
            
            marcas = cursor.fetchall()
            
            if not marcas:
                logger.info(f"El titular '{titular}' no tiene marcas registradas")
                continue
            
            # Verificar qué marcas no tienen reportes en el mes actual
            marcas_sin_reportes = []
            
            for codigo_marca, marca, clase in marcas:
                cursor.execute("""
                    SELECT COUNT(*) FROM boletines 
                    WHERE (marca_publicada = ? OR marca_custodia = ?)
                    AND reporte_generado = 1
                    AND fecha_alta BETWEEN ? AND ?
                """, (marca, marca, primer_dia, ultimo_dia))
                
                tiene_reportes = cursor.fetchone()[0] > 0
                
                if not tiene_reportes:
                    marcas_sin_reportes.append((codigo_marca, marca, clase))
            
            # Si todas las marcas tuvieron reportes, no enviar nada
            if not marcas_sin_reportes:
                logger.info(f"Todas las marcas del titular '{titular}' tienen reportes en el mes actual")
                continue
                
            logger.info(f"El titular '{titular}' tiene {len(marcas_sin_reportes)} marcas sin reportes en el mes actual")
            titulares_con_marcas_sin_reportes.append(titular)
            
            # Verificar si ya se ha enviado una notificación para este titular en este periodo
            ya_notificado = False
            if tiene_columna_periodo:
                cursor.execute("""
                    SELECT COUNT(*) FROM emails_enviados 
                    WHERE tipo_email = 'notificacion_marcas' 
                    AND titular = ? 
                    AND periodo_notificacion = ?
                """, (titular, periodo_actual))
                ya_notificado = cursor.fetchone()[0] > 0
            
            if ya_notificado:
                logger.info(f"Ya se ha enviado una notificación a '{titular}' para el periodo {periodo_actual}")
                ya_notificados += 1
                continue
            
                # Intentar enviar email de notificación
            try:
                # Obtener credenciales de email (usando una función independiente de streamlit)
                email_user, email_password, email_host, email_port = obtener_credenciales_email()
                
                
                
                if not email_user or not email_password:
                    logger.error("No se encontraron credenciales de email configuradas")
                    errores += 1
                    continue                # Importar plantillas HTML
                from email_templates import get_html_template
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.image import MIMEImage
                import os
                
                # Crear mensaje usando MIMEMultipart para soporte HTML
                msg = MIMEMultipart('alternative')
                # Importante: usar EXACTAMENTE el mismo email que se usa para autenticar
                msg['From'] = email_user
                msg['To'] = email
                msg['Subject'] = f"Notificación: CUSTODIA DE MARCAS - {nombre_mes} {anio_reporte}"
                
                # Crear lista HTML de marcas sin reportes
                lista_marcas_html = ""
                for codigo_marca, marca, clase in marcas_sin_reportes:
                    lista_marcas_html += f"<li><span class=\"highlight\">{marca}</span> (Clase {clase}, Código {codigo_marca})</li>"
                
                # Crear versión texto plano como fallback
                text_body = f"""Estimado {titular},

Le informamos que durante el mes de {nombre_mes} {anio_reporte} las siguientes marcas de su titularidad no han tenido reportes generados:

{', '.join([f"{m[1]} (Clase {m[2]})" for m in marcas_sin_reportes])}

Si cree que esto es un error o requiere información adicional, por favor contáctenos.

Saludos cordiales,
Sistema de Gestión de Marcas"""
                
                # Contenido específico para este tipo de notificación
                contenido_especifico = f"""
                <p>Estimado/a <span class="highlight">{titular}</span>,</p>
                
                <p> En virtud del servicio de custodia oportunamente contratado sobre sus marcas, nos complace informarle que hemos realizado el control mensual comparativo de presentaciones ante el INPI <span class="highlight">{nombre_mes} {anio_reporte}</span>. Como resultado, <span class="highlight"> nuestro sistema no ha detectado marcas similares que pudieran afectar los derechos que estamos protegiendo sobre sus registros.</span></p>
                <ul style="margin-left: 25px; margin-bottom: 20px;">
                    {lista_marcas_html}
                </ul>
                
                <p>Esta notificación es informativa y podría indicar que no se han detectado novedades relevantes para estas marcas durante el período mencionado.</p>
                
                <p>Si considera que debería haber recibido información sobre estas marcas o requiere cualquier aclaración adicional, no dude en contactarnos.</p>
                
                <p>Saludos cordiales,<br>
                Equipo de Gestión de Marcas</p>
                """
                
                # Obtener plantilla HTML y reemplazar el contenido
                html_template = get_html_template()
                html_content = html_template.replace('<!-- El contenido del mensaje se insertará aquí -->', contenido_especifico)
                
                # Adjuntar partes al mensaje
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                
                # Agregar logo si existe
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
                            img = MIMEImage(img_file.read())
                            img.add_header('Content-ID', '<logo>')
                            img.add_header('Content-Disposition', 'inline')
                            msg.attach(img)
                    except Exception as e:
                        logger.warning(f"Error al adjuntar logo: {e}")
                    
                # Enviar email - usando el método exacto que funciona en email_verification_system.py
                port = int(email_port) if isinstance(email_port, str) else email_port
                server = smtplib.SMTP(email_host, port)
                server.ehlo()  # Identificarse con el servidor
                server.starttls()
                server.ehlo()  # Identificarse nuevamente después de TLS
                server.login(email_user, email_password)
                
                # Usar sendmail en lugar de send_message (importante para evitar el error de relay)
                msg_content = msg.as_string()
                server.sendmail(email_user, [email], msg_content)
                server.quit()
                
                # Registrar envío en la tabla emails_enviados
                try:
                    # Crear un resumen del mensaje en lugar de almacenar todo el HTML
                    resumen_mensaje = f"Notificación: Marcas sin reportes para {nombre_mes} {anio_reporte}"
                    
                    # Crear un string con las marcas sin reportes
                    marcas_str = ", ".join([f"{m[1]} (Clase {m[2]})" for m in marcas_sin_reportes])
                    
                    if tiene_columna_periodo and tiene_columna_marcas:
                        cursor.execute("""
                            INSERT INTO emails_enviados 
                            (destinatario, asunto, mensaje, fecha_envio, status, tipo_email, titular, periodo_notificacion, marcas_sin_reportes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (email, msg['Subject'], resumen_mensaje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                            "enviado", "notificacion_marcas", titular, periodo_actual, marcas_str))
                    elif tiene_columna_periodo:
                        cursor.execute("""
                            INSERT INTO emails_enviados 
                            (destinatario, asunto, mensaje, fecha_envio, status, tipo_email, titular, periodo_notificacion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (email, msg['Subject'], resumen_mensaje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                            "enviado", "notificacion_marcas", titular, periodo_actual))
                    else:
                        # Inserción básica si no existen las columnas adicionales
                        cursor.execute("""
                            INSERT INTO emails_enviados 
                            (destinatario, asunto, mensaje, fecha_envio, status, tipo_email, titular)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (email, msg['Subject'], resumen_mensaje, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                            "enviado", "notificacion_marcas", titular))
                    
                    conn.commit()
                    logger.info(f"Registro de envío guardado en la base de datos")
                except Exception as e:
                    logger.warning(f"No se pudo registrar el envío en la base de datos: {e}")
                
                logger.info(f"Email de notificación enviado a {email} ({titular})")
                emails_enviados += 1
                
            except Exception as e:
                logger.error(f"Error al enviar email a {email} ({titular}): {e}")
                errores += 1
        
        # Resumen de la operación
        logger.info(f"Verificación completada: {len(titulares_con_marcas_sin_reportes)} titulares con marcas sin reportes, {emails_enviados} emails enviados, {ya_notificados} ya notificados, {errores} errores")
        
        return {
            "estado": "completado",
            "titulares_con_marcas_sin_reportes": len(titulares_con_marcas_sin_reportes),
            "emails_enviados": emails_enviados,
            "ya_notificados": ya_notificados,
            "errores": errores,
            "fecha_verificacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        logger.error(f"Error durante la verificación de titulares sin reportes: {e}")
        return {"estado": "error", "mensaje": str(e)}

def ejecutar_verificacion_periodica():
    """
    Ejecuta la verificación periódica de titulares sin reportes.
    Esta función está diseñada para ser llamada automáticamente por un scheduler.
    """
    try:
        from database import crear_conexion
        
        conn = crear_conexion()
        if conn:
            resultado = verificar_titulares_sin_reportes(conn)
            conn.close()
            
            logger.info(f"Verificación periódica ejecutada con resultado: {resultado}")
            return resultado
        else:
            logger.error("No se pudo conectar a la base de datos")
            return {"estado": "error", "mensaje": "Error de conexión a la base de datos"}
    
    except Exception as e:
        logger.error(f"Error al ejecutar verificación periódica: {e}")
        return {"estado": "error", "mensaje": str(e)}

if __name__ == "__main__":
    # Ejecutar verificación al llamar el script directamente
    from database import crear_conexion
    
    conn = crear_conexion()
    if conn:
        resultado = verificar_titulares_sin_reportes(conn)
        conn.close()
        
        print("Resultado de la verificación:")
        for key, value in resultado.items():
            print(f"  {key}: {value}")
    else:
        print("Error: No se pudo conectar a la base de datos")