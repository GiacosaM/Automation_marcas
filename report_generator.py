# report_generator_optimized.py
import os
import logging
import secrets  
from fpdf import FPDF
from datetime import datetime
from collections import defaultdict
from typing import List, Tuple, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfessionalReportPDF(FPDF):
    
    
    def __init__(self, watermark_image: str = None, company_name: str = "Estudio Contable"):
        super().__init__()
        self.watermark_image = watermark_image
        self.company_name = company_name
        self.page_count = 0
        
    def header(self):
        """Configura el encabezado de cada página."""
        # Marca de agua en margen superior izquierdo
        self._add_watermark()
        
        # Encabezado principal (con margen ajustado para no solaparse con la imagen)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(70, 70, 70)
        # Posicionar el texto más a la derecha para evitar solapamiento
        self.set_x(90)  # Empezar desde 60mm para dejar espacio a la imagen
        self.cell(0, 8, self.company_name, 0, 1, 'L')
        
        # Línea separadora (también con margen ajustado)
        self.set_draw_color(200, 200, 200)
        self.line(20, 25, 190, 25)
        self.ln(5)
    
    def footer(self):
        """Configura el pie de página."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Número de página
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        
        # Fecha de generación
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.set_y(-15)
        self.cell(0, 10, f'Generado el: {fecha_generacion}', 0, 0, 'R')
    
    def _add_watermark(self):
        """Agrega la marca de agua en el margen superior izquierdo."""
        if self.watermark_image and os.path.exists(self.watermark_image):
            try:
                # Tamaño reducido de la marca de agua (15% del ancho de página)
                img_width = self.w * 0.15
                
                # Posición en margen superior izquierdo
                x = 15  # Margen izquierdo de 15mm
                y = 0  # Margen superior de 10mm
                
                # Agregar imagen
                self.image(self.watermark_image, x=x, y=y, w=img_width)
                
            except Exception as e:
                logger.warning(f"No se pudo agregar la marca de agua: {e}")
    
    def add_title_section(self, title: str, subtitle: str = None):
        """Agrega una sección de título profesional."""
        self.ln(10)
        
        # Título principal
        self.set_font('Arial', 'B', 18)
        self.set_text_color(30, 30, 30)
        self.cell(0, 12, title, 0, 1, 'C')
        
        if subtitle:
            self.ln(5)
            self.set_font('Arial', 'B', 14)
            self.set_text_color(60, 60, 60)
            self.cell(0, 10, subtitle, 0, 1, 'C')
        
        self.ln(10)
    
    def add_info_box(self, titular: str, fecha_reporte: str, total_registros: int):
        """Agrega un cuadro de información general."""
        # Fondo del cuadro
        self.set_fill_color(240, 248, 255)
        self.rect(20, self.get_y(), 170, 25, 'F')
        
        # Borde del cuadro
        self.set_draw_color(100, 149, 237)
        self.rect(20, self.get_y(), 170, 25)
        
        # Contenido del cuadro
        y_start = self.get_y()
        self.set_font('Arial', 'B', 11)
        self.set_text_color(30, 30, 30)
        
        self.set_xy(25, y_start + 5)
        self.cell(0, 6, f"Titular: {titular}", 0, 1, 'L')
        
        self.set_xy(25, y_start + 12)
        self.cell(80, 6, f"Período del reporte: {fecha_reporte}", 0, 0, 'L')
        self.set_xy(25, y_start + 18)
        self.cell(0, 6, f"Total de registros: {total_registros}", 0, 1, 'L')
        
        self.ln(20)
    
    def add_section_divider(self, text: str = ""):
        """Agrega un separador de sección."""
        self.ln(5)
        self.set_draw_color(180, 180, 180)
        self.line(20, self.get_y(), 190, self.get_y())
        
        if text:
            self.ln(5)
            self.set_font('Arial', 'B', 12)
            self.set_text_color(80, 80, 80)
            self.cell(0, 8, text, 0, 1, 'C')
        
        self.ln(5)
    
    def add_record_entry(self, record_data: dict, record_number: int):
        """Agrega una entrada de registro con formato profesional."""
        # Verificar espacio disponible
        if self.get_y() > 250:
            self.add_page()
        
        # Encabezado del registro
        self.set_font('Arial', 'B', 11)
        self.set_text_color(25, 25, 112)
        self.cell(0, 8, f"REGISTRO #{record_number:03d}", 0, 1, 'L')
        
        # Línea bajo el encabezado
        self.set_draw_color(25, 25, 112)
        self.line(20, self.get_y(), 100, self.get_y())
        self.ln(3)
        
        # Campos del registro
        self.set_font('Arial', '', 10)
        self.set_text_color(40, 40, 40)
        
        fields = [
            ("Boletín", record_data.get('boletin', '')),
            ("Número de Orden", record_data.get('numero_orden', '')),
            ("Solicitante", record_data.get('solicitante', '')),
            ("Agente", record_data.get('agente', '')),
            ("Número de Expediente", record_data.get('numero_expediente', '')),
            ("Clase", record_data.get('clase', '')),
            ("Marca en Custodia", record_data.get('marca_custodia', '')),
            ("Marca Publicada", record_data.get('marca_publicada', '')),
            ("Clases/Acta", record_data.get('clases_acta', ''))
        ]
        
        for label, value in fields:
            if value:  # Solo mostrar campos con valor
                self.set_font('Arial', 'B', 9)
                self.set_text_color(70, 70, 70)
                self.cell(50, 6, f"{label}:", 0, 0, 'L')
                
                self.set_font('Arial', '', 9)
                self.set_text_color(30, 30, 30)
                
                # Manejar texto largo
                if len(str(value)) > 60:
                    self.cell(0, 6, str(value)[:60] + "...", 0, 1, 'L')
                else:
                    self.cell(0, 6, str(value), 0, 1, 'L')
        
        self.ln(5)


class ReportGenerator:
    """Clase principal para generar informes de marcas."""
    
    def __init__(self, watermark_path: str = None, output_dir: str = "informes"):
        self.watermark_path = watermark_path
        self.output_dir = output_dir
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Crea el directorio de salida si no existe."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _validate_watermark(self) -> bool:
        """Valida si la imagen de marca de agua existe."""
        if not self.watermark_path:
            return False
        
        # Intentar diferentes rutas posibles
        possible_paths = [
            self.watermark_path,
            os.path.join("imagenes", "marca_agua.jpg"),
            os.path.join("imagenes", "image1.jpg"),
            "imagenes/marca_agua.jpg",
            "imagenes/image1.jpg"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.watermark_path = path  # Actualizar con la ruta válida
                logger.info(f"Imagen de marca de agua encontrada: {path}")
                return True
        
        logger.warning(f"Imagen de marca de agua no encontrada en ninguna de estas ubicaciones: {possible_paths}")
        return False
    
    def _fetch_pending_records(self, conn) -> List[Tuple]:
        """Obtiene los registros pendientes de la base de datos."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT titular, numero_boletin, fecha_boletin, numero_orden, solicitante, agente, 
                       numero_expediente, clase, marca_custodia, marca_publicada, clases_acta
                FROM boletines
                WHERE reporte_generado = 0
                ORDER BY titular, fecha_boletin DESC, numero_orden
            ''')
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error al consultar la base de datos: {e}")
            raise
    
    def _format_record_data(self, record: Tuple) -> dict:
        """Formatea los datos del registro para el PDF."""
        boletin_texto = ""
        if record[1] and record[2]:  # numero_boletin y fecha_boletin
            boletin_texto = f"BOLETÍN NRO. {record[1]} DEL {record[2]}"
        
        return {
            'boletin': boletin_texto,
            'numero_orden': record[3],
            'solicitante': record[4],
            'agente': record[5],
            'numero_expediente': record[6],
            'clase': record[7],
            'marca_custodia': record[8],
            'marca_publicada': record[9],
            'clases_acta': record[10]
        }
    
    def _clean_filename(self, filename: str) -> str:
        """Limpia el nombre del archivo de caracteres no válidos."""
        return "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    
    def _mark_records_as_processed(self, conn, titular: str, nombre_reporte: str, ruta_reporte: str):
        """Marca los registros de un titular específico como procesados en la base de datos."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE boletines 
                SET reporte_generado = 1, 
                    fecha_creacion_reporte = datetime('now', 'localtime'),
                    nombre_reporte = ?,
                    ruta_reporte = ? 
                WHERE reporte_enviado = 0 AND titular = ?
            ''', (nombre_reporte, ruta_reporte, titular))
            conn.commit()
            logger.info(f"Registros de {titular} marcados como procesados en la base de datos")
        except Exception as e:
            logger.error(f"Error al actualizar la base de datos para {titular}: {e}")
            raise
    
    def generate_reports(self, conn):
        """Genera los informes PDF ."""
        try:
            # Obtener registros pendientes
            registros = self._fetch_pending_records(conn)
            
            if not registros:
                logger.info("No hay registros pendientes para generar informes")
                return
            
            # Agrupar por titular
            agrupados = defaultdict(list)
            for registro in registros:
                titular = registro[0]
                agrupados[titular].append(registro)
            
            # Información del período
            fecha_actual = datetime.now()
            dia = fecha_actual.day  # Obtiene el número del día (1-31)
            # Diccionario de meses en castellano
            meses_castellano = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            mes_ingles = fecha_actual.strftime("%B %Y")
            mes_ano = mes_ingles.replace(fecha_actual.strftime("%B"), meses_castellano[fecha_actual.strftime("%B")])
            mes_ano_archivo = fecha_actual.strftime("%B-%Y")
            
            logger.info(f"Generando {len(agrupados)} informes para el período {mes_ano}")
            
            # Generar PDF por cada titular y actualizar sus registros individualmente
            for titular, registros_titular in agrupados.items():
                nombre_archivo, ruta_archivo = self._generate_single_report(
                    titular, registros_titular, mes_ano, mes_ano_archivo
                )
                
                # Marcar los registros de este titular específico como procesados
                self._mark_records_as_processed(conn, titular, nombre_archivo, ruta_archivo)
            
            logger.info("Generación de informes completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error durante la generación de informes: {e}")
            raise
    
    def _generate_single_report(self, titular: str, registros: List[Tuple], 
                              mes_ano: str, mes_ano_archivo: str) -> Tuple[str, str]:
        """Genera un informe individual para un titular."""
        try:
            # Crear PDF
            watermark = self.watermark_path if self._validate_watermark() else None
            pdf = ProfessionalReportPDF(watermark)
            pdf.add_page()
            
            # Título principal
            pdf.add_title_section(
                "INFORME DE MARCAS PUBLICADAS",
                f"Período: {mes_ano}"
            )
            
            # Cuadro de información
            pdf.add_info_box(titular, mes_ano, len(registros))
            
            # Separador
            pdf.add_section_divider("DETALLE DE REGISTROS")
            
            # Agregar cada registro
            for i, registro in enumerate(registros, 1):
                record_data = self._format_record_data(registro)
                pdf.add_record_entry(record_data, i)
            
            # Guardar PDF
            titular_limpio = self._clean_filename(titular)
           
            digitos_random = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            nombre_archivo = f"{mes_ano_archivo} - Informe {titular_limpio} - {digitos_random}.pdf"
            
            ruta_archivo = os.path.join(self.output_dir, nombre_archivo)  
            pdf.output(ruta_archivo)
            logger.info(f"Informe generado: {ruta_archivo}")
            
            # Retornar el nombre y la ruta del archivo
            return nombre_archivo, ruta_archivo
            
        except Exception as e:
            logger.error(f"Error al generar informe para {titular}: {e}")
            raise


def generar_informe_pdf(conn, watermark_image: str = "imagenes/marca_agua.jpg"):
    """Función principal para mantener compatibilidad con el código anterior."""
    generator = ReportGenerator(watermark_image)
    generator.generate_reports(conn)