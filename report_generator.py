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
            'clases_acta': record[10],
            'importancia': record[11]  # Agregar importancia
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
            # Crear PDF
            watermark = self.watermark_path if self._validate_watermark() else None
            pdf = ProfessionalReportPDF(watermark)
            pdf.add_page()
            
            # Título principal con importancia
            titulo_importancia = f"INFORME DE MARCAS PUBLICADAS - IMPORTANCIA {importancia.upper()}"
            pdf.add_title_section(
                titulo_importancia,
                f"Período: {mes_ano}"
            )
            
            # Cuadro de información
            pdf.add_info_box(titular, mes_ano, len(registros))
            
            # Separador con información de importancia
            pdf.add_section_divider(f"DETALLE DE REGISTROS - IMPORTANCIA {importancia.upper()}")
            
            # Agregar cada registro
            for i, registro in enumerate(registros, 1):
                record_data = self._format_record_data(registro)
                pdf.add_record_entry(record_data, i)
            
            # Guardar PDF con nombre que incluya importancia
            titular_limpio = self._clean_filename(titular)
           
            digitos_random = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            nombre_archivo = f"{mes_ano_archivo} - Informe {titular_limpio} - {importancia} - {digitos_random}.pdf"
            
            ruta_archivo = os.path.join(self.output_dir, nombre_archivo)  
            pdf.output(ruta_archivo)
            logger.info(f"Informe generado: {ruta_archivo}")
            
            # Retornar el nombre y la ruta del archivo
            return nombre_archivo, ruta_archivo
            
        except Exception as e:
            logger.error(f"Error al generar informe para {titular} (Importancia: {importancia}): {e}")
            raise


def generar_informe_pdf(conn, watermark_image: str = "imagenes/marca_agua.jpg"):
    """Función principal para mantener compatibilidad con el código anterior."""
    generator = ReportGenerator(watermark_image)
    return generator.generate_reports(conn)