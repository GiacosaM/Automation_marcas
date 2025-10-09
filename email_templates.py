"""
Este archivo contiene las plantillas HTML para los correos electrónicos
"""
import os
from paths import get_logo_path, inicializar_assets

def get_html_template():
    """
    Retorna la plantilla HTML básica para correos electrónicos profesionales.
    
    Nota: Esta plantilla incluye una referencia a una imagen con Content-ID 'company-logo@mimarca.com.ar'.
    Para que se muestre correctamente, se debe adjuntar una imagen con este Content-ID específico al email.
    Ejemplo de cómo adjuntar la imagen:
    
    img = MIMEImage(open(logo_path, 'rb').read())
    img.add_header('Content-ID', '<company-logo@mimarca.com.ar>')
    img.add_header('Content-Disposition', 'inline')
    """
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notificación de Servicio de Custodia</title>
        <style>
            body {
                font-family: Arial, Helvetica, sans-serif;
                line-height: 1.6;
                color: #333333;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #1a365d;
                color: #ffffff;
                padding: 25px;
                text-align: center;
            }
            .header img {
                max-height: 120px;
                margin-bottom: 15px;
            }
            .header h1 {
                margin: 0;
                font-size: 22px;
                font-weight: normal;
            }
            .content {
                background-color: #ffffff;
                padding: 30px;
                border: 1px solid #e0e0e0;
            }
            .content p {
                margin-bottom: 16px;
                text-align: justify;
            }
            .footer {
                font-size: 12px;
                color: #666666;
                text-align: center;
                margin-top: 20px;
                padding: 10px;
                background-color: #f7f7f7;
                border-top: 1px solid #e0e0e0;
            }
            .contact-info {
                margin-top: 20px;
                padding-top: 10px;
                border-top: 1px solid #e0e0e0;
                font-size: 14px;
                text-align: center;
            }
            .highlight {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
    <!-- Aquí va el logo simulado con HTML -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, Helvetica, sans-serif;">
      <tr>
        <td align="center" style="padding: 10px 0;">
          
            <!-- Logo de la empresa -->
            <div style="display:inline-block; vertical-align:middle; margin-right:10px;">
            <img src="cid:logo" alt="Logo Empresa" 
                style="max-height:120px; max-width:300px; border-radius:8px;">
            </div>
            
         

            <div>
            <h1>Servicio de Custodia de Marcas</h1>
            </div>
          </div>
        </td>
      </tr>
    </table>
</div>

            <div class="content">
                <!-- El contenido del mensaje se insertará aquí -->
                <div class="contact-info">
                    <p>
                        <strong>Mimarca.com.ar</strong><br>
                        Teléfono: +54 3425 00-4006<br>
                        Email: info@mimarca.com.ar<br>
                        Dirección: San Jerónimo 2084 (CP 3000) Santa Fe​, AR
                    </p>
                </div>
            </div>
            <div class="footer">
                <p>Este correo electrónico contiene información confidencial y está destinado exclusivamente para el uso de la persona o entidad a la que está dirigido. Si no es el destinatario indicado, queda notificado de que la divulgación, copia, distribución o toma de acción basada en el contenido está estrictamente prohibida.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def get_html_message_by_importance(importance):
    """
    Retorna el mensaje HTML correspondiente según la importancia
    """
    messages = {
        "Alta": """
                <p>Estimado/a,</p>
                
                <p>En virtud del servicio de custodia contratado sobre sus marcas, le informamos que, a partir del control mensual comparativo de presentaciones ante el INPI, se han detectado <span class="highlight">similitudes muy relevantes</span> con sus registros, que a nuestro criterio ameritan ejercer el <span class="highlight">derecho de oposición de manera inmediata</span>.</p>
                
                <p>Por tal motivo, le solicitamos se comunique a la <span class="highlight">mayor brevedad</span> con nuestras oficinas, a fin de coordinar con nuestros profesionales las acciones necesarias para la protección de sus derechos marcarios.</p>
        """,
        
        "Media": """
                <p>Estimado/a,</p>
                
                <p>En virtud del servicio de custodia oportunamente contratado sobre sus marcas, le informamos que, como resultado del control mensual comparativo de presentaciones ante el INPI, se han detectado algunas <span class="highlight">similitudes leves</span> con sus registros.</p>
                
                <p>Dichas coincidencias se detallan en el <span class="highlight">informe adjunto</span>. A nuestro entender, no ameritan ejercer el derecho de oposición en esta instancia. No obstante, quedamos a su disposición para que, en caso de considerarlo necesario, pueda comunicarse con nuestros profesionales y evaluar conjuntamente los pasos a seguir.</p>
                
                <p>Saludos cordiales.</p>
        """,
        
        "Baja": """
                <p>Estimado/a,</p>
                
                <p>En virtud del servicio de custodia oportunamente contratado sobre sus marcas, le informamos que, como resultado del control mensual comparativo de presentaciones ante el INPI, se han detectado algunas <span class="highlight">similitudes leves</span> con sus registros.</p>
                
                <p>Dichas coincidencias se detallan en el <span class="highlight">informe adjunto</span>. A nuestro entender, no ameritan ejercer el derecho de oposición en esta instancia. No obstante, quedamos a su disposición para que, en caso de considerarlo necesario, pueda comunicarse con nuestros profesionales y evaluar conjuntamente los pasos a seguir.</p>
                
                <p>Saludos cordiales.</p>
        """,
        
        "default": """
                <p>Estimado/a,</p>
                
                <p>En virtud del servicio de custodia oportunamente contratado sobre sus marcas, nos complace informarle que hemos realizado el control mensual comparativo de presentaciones ante el INPI. Como resultado, nuestro sistema no ha detectado marcas similares que pudieran afectar los derechos que estamos protegiendo sobre sus registros.</p>
                
                <p>Saludos cordiales.</p>
        """
    }
    
    return messages.get(importance, messages["default"])

def get_verification_email_html(username, activation_code):
    """
    Retorna el mensaje HTML para el correo de verificación
    """
    return f"""
                <p>Hola <span class="highlight">{username}</span>,</p>
                
                <p>Gracias por registrarte en nuestro sistema de gestión de marcas.</p>
                
                <p>Tu código de verificación es: <span class="highlight" style="font-size: 18px; background-color: #f7f7f7; padding: 5px 10px; border-radius: 4px;">{activation_code}</span></p>
                
                <p>Este código es válido por <span class="highlight">15 minutos</span>.</p>
                
                <p>Si no solicitaste este registro, por favor ignora este correo.</p>
                
                <p>Saludos cordiales,<br>
                Equipo de Estudio Contable</p>
    """
