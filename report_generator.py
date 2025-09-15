# report_generator_optimized.py
import os
import logging
import secrets  
from fpdf import FPDF
from datetime import datetime
from collections import defaultdict
from typing import List, Tuple, Optional
from professional_theme import ProfessionalTheme

# Configurar logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Logger específico para eventos críticos de reportes
report_logger = logging.getLogger('report_events')
report_logger.setLevel(logging.INFO)
report_handler = logging.FileHandler('boletines.log')
report_handler.setFormatter(logging.Formatter('%(asctime)s - REPORT - %(message)s'))
report_logger.addHandler(report_handler)
report_logger.propagate = False
logger = logging.getLogger(__name__)

class ProfessionalReportPDF(FPDF):
    """Clase PDF mejorada con diseño profesional y elegante"""
    
    def __init__(self, watermark_image: str = None, company_name: str = "Estudio Contable Professional"):
        super().__init__()
        self.watermark_image = watermark_image
        self.company_name = company_name
        self.theme = ProfessionalTheme()
        
        # Configurar márgenes más amplios
        self.set_auto_page_break(auto=True, margin=self.theme.get_layout('margin_bottom'))
        self.set_margins(
            left=self.theme.get_layout('margin_left'),
            top=self.theme.get_layout('margin_top'),
            right=self.theme.get_layout('margin_right')
        )
        
    def header(self):
        """Encabezado profesional con logo, nombre del estudio y fecha"""
        # Marca de agua / Logo
        self._add_watermark()
        
        # Nombre del Estudio Contable
        font_config = self.theme.get_font('header_company')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('primary_blue'))
        self.set_y(22)
        self.cell(0, 10, self.company_name.upper(), 0, 1, 'C')
        
        # Fecha actual
        fecha_actual = datetime.now().strftime("%d de %B de %Y")
        meses = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
            'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        for eng, esp in meses.items():
            fecha_actual = fecha_actual.replace(eng, esp)
            
        font_config = self.theme.get_font('header_info')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('medium_gray'))
        self.cell(0, 6, fecha_actual, 0, 1, 'C')
        
        # Línea inferior decorativa
        self.set_draw_color(*self.theme.get_color('border_color'))
        self.set_line_width(0.5)
        self.line(self.theme.get_layout('margin_left'), self.get_y() + 3, 
                 self.w - self.theme.get_layout('margin_right'), self.get_y() + 3)
        
        self.ln(10)
    
    def footer(self):
        """Pie de página profesional con numeración y texto confidencial"""
        self.set_y(-self.theme.get_layout('footer_height'))
        
        # Línea superior del pie
        self.set_draw_color(*self.theme.get_color('border_color'))
        self.set_line_width(0.5)
        self.line(self.theme.get_layout('margin_left'), self.get_y(), 
                 self.w - self.theme.get_layout('margin_right'), self.get_y())
        
        self.ln(3)
        
        # Texto confidencial (izquierda)
        font_config = self.theme.get_font('footer_text')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('confidential_text'))
        self.cell(0, 5, 'CONFIDENCIAL - Uso exclusivo del cliente', 0, 0, 'L')
        
        # Número de página (derecha)
        self.cell(0, 5, f'Página {self.page_no()}', 0, 0, 'R')
    
    def _add_watermark(self):
        """Agrega marca de agua / logo en esquina superior izquierda"""
        if self.watermark_image and os.path.exists(self.watermark_image):
            try:
                img_width = self.w * (self.theme.get_layout('watermark_size') / 100)
                x = self.theme.get_layout('margin_left') - 10
                y = 5
                self.image(self.watermark_image, x=x, y=y, w=img_width)
            except Exception as e:
                logger.warning(f"No se pudo agregar la marca de agua: {e}")
    
    def add_main_title(self, title: str, subtitle: str = None):
        """Agrega título principal con estilo profesional"""
        self.ln(5)
        
        # Título principal
        font_config = self.theme.get_font('main_title')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('primary_blue'))
        self.cell(0, 15, title, 0, 1, 'C')
        
        if subtitle:
            self.ln(3)
            font_config = self.theme.get_font('subtitle')
            self.set_font(font_config['family'], font_config['style'], font_config['size'])
            self.set_text_color(*self.theme.get_color('secondary_blue'))
            self.cell(0, 10, subtitle, 0, 1, 'C')
        
        self.ln(10)
    
    def add_info_section(self, titular: str, fecha_reporte: str, total_registros: int):
        """Agrega sección de información general con diseño elegante"""
        # Fondo azul claro
        self.set_fill_color(*self.theme.get_color('light_blue'))
        box_height = 28
        self.rect(self.theme.get_layout('margin_left'), self.get_y(), 
                 self.w - self.theme.get_layout('margin_left') - self.theme.get_layout('margin_right'), 
                 box_height, 'F')
        
        # Borde azul
        self.set_draw_color(*self.theme.get_color('primary_blue'))
        self.set_line_width(0.8)
        self.rect(self.theme.get_layout('margin_left'), self.get_y(), 
                 self.w - self.theme.get_layout('margin_left') - self.theme.get_layout('margin_right'), 
                 box_height)
        
        y_start = self.get_y()
        
        # Contenido
        font_config = self.theme.get_font('normal_text')
        self.set_font(font_config['family'], 'B', font_config['size'])
        self.set_text_color(*self.theme.get_color('dark_gray'))
        
        # Titular
        self.set_xy(self.theme.get_layout('margin_left') + 5, y_start + 6)
        self.cell(0, 6, f"TITULAR: {titular}", 0, 1, 'L')
        
        # Período y total
        self.set_xy(self.theme.get_layout('margin_left') + 5, y_start + 14)
        self.cell(90, 6, f"PERÍODO: {fecha_reporte}", 0, 0, 'L')
        self.set_x(self.theme.get_layout('margin_left') + 100)
        self.cell(0, 6, f"TOTAL DE REGISTROS: {total_registros}", 0, 1, 'L')
        
        self.set_y(y_start + box_height)
        self.ln(10)
    
    def add_section_separator(self, title: str = ""):
        """Agrega separador de sección elegante"""
        self.ln(5)
        
        if title:
            # Título de sección
            font_config = self.theme.get_font('section_title')
            self.set_font(font_config['family'], font_config['style'], font_config['size'])
            self.set_text_color(*self.theme.get_color('primary_blue'))
            self.cell(0, 8, title, 0, 1, 'L')
            self.ln(2)
        
        # Línea separadora
        self.set_draw_color(*self.theme.get_color('primary_blue'))
        self.set_line_width(0.8)
        self.line(self.theme.get_layout('margin_left'), self.get_y(), 
                 self.w - self.theme.get_layout('margin_right'), self.get_y())
        
        self.ln(8)
    
    def add_table_header(self, headers: List[str], col_widths: List[int]):
        """Agrega encabezado de tabla con estilo profesional"""
        # Fondo oscuro para encabezados
        self.set_fill_color(*self.theme.get_color('table_header'))
        self.set_text_color(*self.theme.get_color('white'))
        self.set_draw_color(*self.theme.get_color('border_color'))
        self.set_line_width(self.theme.TABLE['border_width'])
        
        font_config = self.theme.get_font('table_header')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.cell(width, self.theme.TABLE['header_height'], header, 1, 0, 'C', True)
        self.ln()
    
    def add_table_row(self, data: List[str], col_widths: List[int], is_alternate: bool = False):
        """Agrega fila de tabla con estilo zebra"""
        # Color de fondo alternado
        if is_alternate:
            self.set_fill_color(*self.theme.get_color('table_row_alt'))
        else:
            self.set_fill_color(*self.theme.get_color('white'))
        
        self.set_text_color(*self.theme.get_color('dark_gray'))
        self.set_draw_color(*self.theme.get_color('border_color'))
        
        font_config = self.theme.get_font('table_content')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        
        for i, (cell_data, width) in enumerate(zip(data, col_widths)):
            # Truncar texto si es muy largo
            text = str(cell_data) if cell_data else ""
            if len(text) > 25:
                text = text[:22] + "..."
            
            self.cell(width, self.theme.TABLE['row_height'], text, 1, 0, 'L', True)
        self.ln()
    
    def add_records_table(self, records_data: List[dict]):
        """Agrega tabla completa de registros con diseño profesional"""
        if not records_data:
            return
        
        # Verificar espacio para tabla
        if self.get_y() > 240:
            self.add_page()
        
        # Definir columnas y anchos
        headers = ["Nº", "Boletín", "Orden", "Solicitante", "Marca Publicada", "Clase"]
        col_widths = [15, 35, 20, 45, 45, 20]  # Total: 180mm (aprox.)
        
        # Agregar encabezado
        self.add_table_header(headers, col_widths)
        
        # Agregar filas
        for i, record in enumerate(records_data):
            # Verificar espacio para nueva fila
            if self.get_y() > 260:
                self.add_page()
                self.add_table_header(headers, col_widths)
            
            # Preparar datos de la fila
            row_data = [
                str(i + 1),
                record.get('boletin_corto', ''),
                record.get('numero_orden', ''),
                record.get('solicitante', ''),
                record.get('marca_publicada', ''),
                record.get('clase', '')
            ]
            
            # Agregar fila con estilo zebra
            self.add_table_row(row_data, col_widths, is_alternate=(i % 2 == 1))
        
        self.ln(10)
    
    def add_detailed_record(self, record_data: dict, record_number: int):
        """Agrega registro detallado con formato profesional"""
        # Verificar espacio
        if self.get_y() > 240:
            self.add_page()
        
        # Encabezado del registro
        font_config = self.theme.get_font('section_title')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('primary_blue'))
        
        # Fondo claro para el encabezado
        self.set_fill_color(*self.theme.get_color('light_gray'))
        self.cell(0, 8, f"REGISTRO Nº {record_number:03d}", 1, 1, 'L', True)
        
        # Contenido del registro
        font_config = self.theme.get_font('normal_text')
        self.set_font(font_config['family'], font_config['style'], font_config['size'])
        self.set_text_color(*self.theme.get_color('dark_gray'))
        
        # Campos principales
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
            if value:
                # Etiqueta en negrita
                self.set_font('Arial', 'B', 9)
                self.set_text_color(*self.theme.get_color('medium_gray'))
                self.cell(50, 6, f"{label}:", 0, 0, 'L')
                
                # Valor
                self.set_font('Arial', '', 9)
                self.set_text_color(*self.theme.get_color('dark_gray'))
                
                # Manejar texto largo
                value_str = str(value)
                if len(value_str) > 70:
                    self.cell(0, 6, value_str[:67] + "...", 0, 1, 'L')
                else:
                    self.cell(0, 6, value_str, 0, 1, 'L')
        
        # Separador sutil
        self.ln(3)
        self.set_draw_color(*self.theme.get_color('light_gray'))
        self.set_line_width(0.3)
        self.line(self.theme.get_layout('margin_left'), self.get_y(), 
                 self.w - self.theme.get_layout('margin_right'), self.get_y())
        self.ln(8)


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
    
    def _fetch_pending_records(self, conn):
        """Obtiene los registros pendientes de procesamiento para generar informes."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT titular, numero_boletin, fecha_boletin, numero_orden, solicitante, agente, 
                       numero_expediente, clase, marca_custodia, marca_publicada, clases_acta, importancia
                FROM boletines
                WHERE reporte_generado = 0 
                AND importancia != 'Pendiente'  -- ← NUEVA CONDICIÓN
                ORDER BY titular, importancia, fecha_boletin DESC, numero_orden
            ''')
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error al consultar la base de datos: {e}")
            raise
    
    def _format_record_data(self, record: Tuple) -> dict:
        """Formatea los datos del registro para el PDF."""
        boletin_texto = ""
        boletin_corto = ""
        if record[1] and record[2]:  # numero_boletin y fecha_boletin
            boletin_texto = f"BOLETÍN NRO. {record[1]} DEL {record[2]}"
            boletin_corto = f"Nº {record[1]}"
        
        return {
            'boletin': boletin_texto,
            'boletin_corto': boletin_corto,
            'numero_orden': record[3],
            'solicitante': record[4],
            'agente': record[5],
            'numero_expediente': record[6],
            'clase': record[7],
            'marca_custodia': record[8],
            'marca_publicada': record[9],
            'clases_acta': record[10],
            'importancia': record[11]
        }
    
    def _clean_filename(self, filename: str) -> str:
        """Limpia el nombre del archivo de caracteres no válidos."""
        return "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    
    def _mark_records_as_processed(self, conn, titular: str, importancia: str, nombre_reporte: str, ruta_reporte: str):
        """Marca los registros como procesados en la base de datos."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE boletines 
                SET reporte_generado = 1, 
                    fecha_creacion_reporte = datetime('now', 'localtime'),
                    nombre_reporte = ?,
                    ruta_reporte = ? 
                WHERE reporte_enviado = 0 
                AND titular = ?
                AND importancia = ?
                AND importancia != 'Pendiente'
            ''', (nombre_reporte, ruta_reporte, titular, importancia))
            conn.commit()
            logger.info(f"Registros de {titular} (Importancia: {importancia}) marcados como procesados en la base de datos")
        except Exception as e:
            logger.error(f"Error al actualizar la base de datos para {titular} (Importancia: {importancia}): {e}")
            raise
    
    def generate_reports(self, conn):
        """Genera los informes PDF y retorna información del resultado."""
        try:
            # Obtener registros pendientes
            registros = self._fetch_pending_records(conn)
            
            # Verificar si hay registros con importancia 'Pendiente' ANTES de procesar
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM boletines 
                WHERE reporte_generado = 0 AND importancia = 'Pendiente'
            ''')
            pendientes = cursor.fetchone()[0]
            
            # Obtener total de registros sin procesar
            cursor.execute('''
                SELECT COUNT(*) FROM boletines 
                WHERE reporte_generado = 0
            ''')
            total_sin_procesar = cursor.fetchone()[0]
            
            # Logging mejorado con más información
            if pendientes > 0:
                logger.info(f"📋 ESTADO DE REGISTROS:")
                logger.info(f"   • Total registros sin procesar: {total_sin_procesar}")
                logger.info(f"   • Registros con estado 'Pendiente' (no se procesarán): {pendientes}")
                logger.info(f"   • Registros listos para procesar: {len(registros)}")
                logger.warning(f"⚠️  HAY {pendientes} REGISTROS CON IMPORTANCIA 'PENDIENTE' QUE NO SERÁN PROCESADOS")
            
            if not registros:
                if pendientes > 0:
                    logger.info("❌ No hay registros listos para generar informes")
                    logger.info("💡 Sugerencia: Cambia la importancia de los registros 'Pendiente' para procesarlos")
                    return {
                        'success': False,
                        'message': 'pending_only',
                        'total_sin_procesar': total_sin_procesar,
                        'pendientes': pendientes,
                        'reportes_generados': 0
                    }
                else:
                    logger.info("✅ No hay registros pendientes para generar informes")
                    return {
                        'success': True,
                        'message': 'no_pending',
                        'total_sin_procesar': 0,
                        'pendientes': 0,
                        'reportes_generados': 0
                    }
            
            # Agrupar por titular + importancia (NUEVA LÓGICA)
            agrupados = defaultdict(list)
            for registro in registros:
                titular = registro[0]
                importancia = registro[11]  # La importancia está en la posición 11
                clave_agrupacion = (titular, importancia)
                agrupados[clave_agrupacion].append(registro)
            
            # Información del período
            fecha_actual = datetime.now()
            dia = fecha_actual.day
            
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
            
            # Log de inicio con resumen mejorado
            titulares_unicos = len(set(clave[0] for clave in agrupados.keys()))
            logger.info(f"🚀 INICIANDO GENERACIÓN DE INFORMES")
            logger.info(f"   • Período: {mes_ano}")
            logger.info(f"   • Titulares únicos: {titulares_unicos}")
            logger.info(f"   • Grupos (titular + importancia): {len(agrupados)}")
            logger.info(f"   • Total de registros: {len(registros)}")
            if pendientes > 0:
                logger.info(f"   • Registros excluidos (Pendientes): {pendientes}")
            
            # Generar PDF por cada grupo (titular + importancia)
            reportes_generados = 0
            for (titular, importancia), registros_grupo in agrupados.items():
                try:
                    nombre_archivo, ruta_archivo = self._generate_single_report(
                        titular, registros_grupo, mes_ano, mes_ano_archivo, importancia
                    )
                    
                    # Marcar los registros de este grupo específico como procesados
                    self._mark_records_as_processed(conn, titular, importancia, nombre_archivo, ruta_archivo)
                    reportes_generados += 1
                    
                    logger.info(f"✅ Informe generado para '{titular}' (Importancia: {importancia}) - {len(registros_grupo)} registros")
                    
                except Exception as e:
                    logger.error(f"❌ Error al generar informe para '{titular}' (Importancia: {importancia}): {e}")
                    # Continuar con el siguiente grupo en lugar de fallar completamente
                    continue
            
            # Resumen final
            logger.info(f"🎉 GENERACIÓN COMPLETADA:")
            logger.info(f"   • Informes generados exitosamente: {reportes_generados}/{len(agrupados)}")
            logger.info(f"   • Registros procesados: {sum(len(regs) for regs in agrupados.values())}")
            if pendientes > 0:
                logger.info(f"   • Registros pendientes sin procesar: {pendientes}")
            
            if reportes_generados < len(agrupados):
                logger.warning(f"⚠️  ATENCIÓN: {len(agrupados) - reportes_generados} informes fallaron")
            
            # Retornar información del resultado
            return {
                'success': True,
                'message': 'completed',
                'reportes_generados': reportes_generados,
                'total_titulares': len(agrupados),
                'registros_procesados': sum(len(regs) for regs in agrupados.values()),
                'pendientes': pendientes,
                'errores': len(agrupados) - reportes_generados
            }
        
        except Exception as e:
            logger.error(f"💥 ERROR CRÍTICO durante la generación de informes: {e}")
            return {
                'success': False,
                'message': 'error',
                'error': str(e),
                'reportes_generados': 0
            }
    
    def _generate_single_report(self, titular: str, registros: List[Tuple], 
                              mes_ano: str, mes_ano_archivo: str, importancia: str) -> Tuple[str, str]:
        """Genera un informe individual para un titular con una importancia específica."""
        try:
            # Crear PDF con tema profesional
            watermark = self.watermark_path if self._validate_watermark() else None
            pdf = ProfessionalReportPDF(watermark, "ESTUDIO CONTABLE")
            pdf.add_page()
            
            # Título principal con importancia
            titulo_principal = f"INFORME DE MARCAS PUBLICADAS"
            subtitulo = f"Clasificacion: {importancia.upper()} - Periodo: {mes_ano}"
            pdf.add_main_title(titulo_principal, subtitulo)
            
            # Sección de información general
            pdf.add_info_section(titular, mes_ano, len(registros))
            
            # Separador para tabla de resumen
            pdf.add_section_separator("RESUMEN DE REGISTROS")
            
            # Formatear datos para la tabla
            records_data = []
            for registro in registros:
                record_data = self._format_record_data(registro)
                records_data.append(record_data)
            
            # Agregar tabla de registros
            pdf.add_records_table(records_data)
            
            # Separador para detalles
            pdf.add_section_separator("DETALLE COMPLETO DE REGISTROS")
            
            # Agregar registros detallados
            for i, registro in enumerate(registros, 1):
                record_data = self._format_record_data(registro)
                pdf.add_detailed_record(record_data, i)
            
            # Guardar PDF con nombre que incluya importancia
            titular_limpio = self._clean_filename(titular)
            digitos_random = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            nombre_archivo = f"{mes_ano_archivo} - Informe {titular_limpio} - {importancia} - {digitos_random}.pdf"
            
            ruta_archivo = os.path.join(self.output_dir, nombre_archivo)  
            pdf.output(ruta_archivo)
            logger.info(f"Informe generado: {ruta_archivo}")
            
            return nombre_archivo, ruta_archivo
            
        except Exception as e:
            logger.error(f"Error al generar informe para {titular} (Importancia: {importancia}): {e}")
            raise


def generar_informe_pdf(conn, watermark_image: str = "imagenes/marca_agua.jpg"):
    """Función principal para mantener compatibilidad con el código anterior."""
    generator = ReportGenerator(watermark_image)
    return generator.generate_reports(conn)