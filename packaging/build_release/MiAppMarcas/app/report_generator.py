# report_generator_optimized.py
import os
import logging
import unicodedata
from fpdf import FPDF
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Tuple, Optional
from professional_theme import ProfessionalTheme
from paths import get_logs_dir, get_informes_dir, get_config_file_path, get_logo_path, inicializar_assets

# Configurar logging
log_file = os.path.join(get_logs_dir(), 'boletines.log')
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Logger específico para eventos críticos de reportes
report_logger = logging.getLogger('report_events')
report_logger.setLevel(logging.INFO)
report_handler = logging.FileHandler(log_file)
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
            clases_acta_completo = record.get('clases_acta', '')
            # Extraer todas las clases (números antes de "/") para el resumen
            clases_resumen = ''
            if clases_acta_completo:
                # Dividir por espacios y extraer la parte antes de "/" de cada elemento
                partes = clases_acta_completo.split()
                clases = [parte.split('/')[0] for parte in partes if '/' in parte]
                clases_resumen = ', '.join(clases) if clases else clases_acta_completo
            
            row_data = [
                str(i + 1),
                record.get('boletin_corto', ''),
                record.get('numero_orden', ''),
                record.get('solicitante', ''),
                record.get('marca_publicada', ''),
                clases_resumen
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
    
    def __init__(self, watermark_path: str = None, output_dir: str = None):
        # Siempre utilizar get_logo_path() para obtener la ruta del logo
        self.watermark_path = get_logo_path()
        self.output_dir = output_dir if output_dir else get_informes_dir()
        self._ensure_output_directory()
        
        # Intentar inicializar assets si es necesario
        inicializar_assets()
    
    def _ensure_output_directory(self):
        """Crea el directorio de salida si no existe."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _validate_watermark(self) -> bool:
        """Valida si la imagen de marca de agua existe."""
        # Siempre intentar obtener la ruta del logo desde get_logo_path()
        logo_path = get_logo_path()
        if logo_path and os.path.exists(logo_path):
            self.watermark_path = logo_path
            logger.info(f"Logo encontrado mediante get_logo_path(): {logo_path}")
            return True
            
        logger.warning("No se encontró ningún logo válido mediante get_logo_path()")
        return False
        
        # Como último recurso, intentar las rutas tradicionales
        possible_paths = [
            os.path.join("imagenes", "marca_agua.jpg"),
            os.path.join("imagenes", "image1.jpg"),
            "imagenes/marca_agua.jpg",
            "imagenes/image1.jpg"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.watermark_path = path  # Actualizar con la ruta válida
                logger.info(f"Imagen de marca de agua encontrada en ruta alternativa: {path}")
                return True
        
        logger.warning("No se pudo encontrar la imagen del logo en ninguna ubicación")
        return False
    
    def _fetch_pending_records(self, conn, filtros=None):
        """Obtiene los registros pendientes de procesamiento.

        Args:
            conn:    Conexión SQLite activa.
            filtros: Dict opcional con claves:
                       'titulares'   → list[str] — solo incluir estos titulares.
                       'importancias'→ list[str] — solo incluir estas importancias.
                     Si es None o dict vacío se devuelven todos los registros procesables.
        """
        try:
            cursor = conn.cursor()

            where_clauses = [
                "reporte_generado = 0",
                "importancia != 'Pendiente'",
            ]
            params: list = []

            if filtros:
                titulares = filtros.get('titulares')
                importancias = filtros.get('importancias')

                if titulares:
                    ph = ','.join('?' * len(titulares))
                    where_clauses.append(f"titular IN ({ph})")
                    params.extend(titulares)

                if importancias:
                    ph = ','.join('?' * len(importancias))
                    where_clauses.append(f"importancia IN ({ph})")
                    params.extend(importancias)

            where_str = ' AND '.join(where_clauses)
            query = f'''
                SELECT titular, numero_boletin, fecha_boletin, numero_orden, solicitante, agente,
                       numero_expediente, clase, marca_custodia, marca_publicada, clases_acta, importancia
                FROM boletines
                WHERE {where_str}
                ORDER BY titular, importancia, fecha_boletin DESC, numero_orden
            '''
            cursor.execute(query, params)
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
        """Elimina acentos, reemplaza espacios por guiones bajos y descarta
        cualquier carácter no permitido en nombres de archivo."""
        # Descomponer caracteres acentuados y descartar los diacríticos
        nfd = unicodedata.normalize("NFD", str(filename))
        ascii_str = nfd.encode("ascii", "ignore").decode("ascii")
        # Reemplazar espacios por guiones bajos y filtrar caracteres inválidos
        cleaned = "".join(
            "_" if c == " " else c
            for c in ascii_str
            if c.isalnum() or c in ("-", "_", ".")
        )
        # Colapsar guiones bajos múltiples y quitar los extremos
        import re as _re
        return _re.sub(r"_+", "_", cleaned).strip("_")

    def _make_report_filename(self, titular: str, importancia: str, output_dir: str) -> str:
        """Genera un nombre de archivo PDF determinístico y trazable.

        Formato:  Informe_<TITULAR>_<IMPORTANCIA>_<YYYYMMDD_HHMMSS>.pdf

        Garantías:
        - Sin caracteres inválidos en sistemas de archivos Windows/Linux/macOS.
        - Sin números aleatorios: el timestamp hace cada generación única.
        - Sin sobrescritura: si el archivo ya existe (misma generación al segundo),
          agrega un contador _2, _3, ... hasta encontrar un nombre libre.
        - Largo máximo de 180 caracteres en el titular (compatible con MAX_PATH).

        Args:
            titular:     Nombre del titular del informe.
            importancia: Nivel de importancia (Alta, Media, Baja, etc.).
            output_dir:  Directorio de salida donde se guardará el PDF.

        Returns:
            str: Nombre de archivo seguro (sin ruta), listo para usar con output_dir.
        """
        titular_limpio = self._clean_filename(titular)[:180]
        importancia_limpia = self._clean_filename(importancia)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        base = f"Informe_{titular_limpio}_{importancia_limpia}_{timestamp}"
        nombre = f"{base}.pdf"

        # Evitar sobrescritura sin recurrir a números aleatorios
        if os.path.exists(os.path.join(output_dir, nombre)):
            counter = 2
            while os.path.exists(os.path.join(output_dir, f"{base}_{counter}.pdf")):
                counter += 1
            nombre = f"{base}_{counter}.pdf"

        return nombre
    
    def _mark_records_as_processed(self, conn, titular: str, importancia: str, nombre_reporte: str, ruta_reporte: str):
        """Marca como procesados SOLO los registros que aún no fueron generados.

        Condiciones del WHERE:
          reporte_generado = 0  → garantiza que no se sobreescriben registros ya
                                   generados pero no enviados (reporte_generado=1,
                                   reporte_enviado=0), que tendrían una ruta_reporte
                                   válida de una generación anterior.
          reporte_enviado  = 0  → no modificar registros ya enviados.
          titular + importancia → limitar al grupo exacto que se acaba de generar.
          importancia != 'Pendiente' → defensa en profundidad; _fetch_pending_records
                                        ya los excluye, pero se repite aquí por seguridad.
        """
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE boletines
                SET reporte_generado = 1,
                    fecha_creacion_reporte = datetime('now', 'localtime'),
                    nombre_reporte = ?,
                    ruta_reporte = ?
                WHERE reporte_generado = 0
                AND reporte_enviado = 0
                AND titular = ?
                AND importancia = ?
                AND importancia != 'Pendiente'
            ''', (nombre_reporte, ruta_reporte, titular, importancia))
            filas_afectadas = cursor.rowcount
            conn.commit()
            logger.info(
                f"Registros marcados como procesados: {filas_afectadas} fila(s) "
                f"para '{titular}' (Importancia: {importancia})"
            )
            if filas_afectadas == 0:
                logger.warning(
                    f"_mark_records_as_processed: 0 filas actualizadas para "
                    f"'{titular}' ({importancia}). ¿Ya fueron procesados antes?"
                )
        except Exception as e:
            # Deshacer cualquier cambio parcial antes de propagar el error
            try:
                conn.rollback()
                logger.warning(
                    f"Rollback ejecutado para '{titular}' ({importancia}) "
                    f"tras fallo en UPDATE."
                )
            except Exception as rb_err:
                logger.error(f"Rollback también falló: {rb_err}")
            logger.error(
                f"Error al actualizar la base de datos para '{titular}' "
                f"(Importancia: {importancia}): {e}"
            )
            raise
    
    def generate_reports(self, conn, filtros=None, on_progress=None):
        """Genera los informes PDF y retorna información del resultado.

        Args:
            conn:        Conexión SQLite activa.
            filtros:     Dict opcional con 'titulares' y/o 'importancias' para
                         limitar la generación a un subconjunto de registros.
                         None = generar todos los pendientes.
            on_progress: Callable opcional con firma (current, total, titular).
                         Se invoca después de cada informe (éxito o error) para
                         que la UI pueda actualizar una barra de progreso.
        """
        try:
            # Obtener registros pendientes (filtrados si se especificó)
            registros = self._fetch_pending_records(conn, filtros)
            
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
            mes_ano_archivo = mes_ingles.replace(fecha_actual.strftime("%B"), meses_castellano[fecha_actual.strftime("%B")]).replace(" ", "-")
            
            # Calcular el mes anterior correctamente
            fecha_mes_anterior = fecha_actual.replace(day=1) - timedelta(days=1)
            mes_anterior_ingles = fecha_mes_anterior.strftime("%B %Y")
            mes_ano_anterior = mes_anterior_ingles.replace(fecha_mes_anterior.strftime("%B"), meses_castellano[fecha_mes_anterior.strftime("%B")])
            
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
            errores_generacion = 0
            for (titular, importancia), registros_grupo in agrupados.items():

                # ── Paso 1: generar el PDF en disco ──────────────────────────────
                try:
                    nombre_archivo, ruta_archivo = self._generate_single_report(
                        titular, registros_grupo, mes_ano_anterior, mes_ano_archivo, importancia
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Error al generar PDF para '{titular}' "
                        f"(Importancia: {importancia}): {e}"
                    )
                    errores_generacion += 1
                    continue   # La BD no se toca: PDF nunca existió

                # ── Paso 2: registrar en BD solo si el PDF existe en disco ───────
                if not os.path.exists(ruta_archivo):
                    logger.error(
                        f"❌ El PDF no existe tras la generación para '{titular}' "
                        f"(Importancia: {importancia}). No se actualizará la BD."
                    )
                    errores_generacion += 1
                    continue

                try:
                    self._mark_records_as_processed(
                        conn, titular, importancia, nombre_archivo, ruta_archivo
                    )
                    reportes_generados += 1
                    logger.info(
                        f"✅ Informe generado para '{titular}' "
                        f"(Importancia: {importancia}) - {len(registros_grupo)} registros"
                    )
                except Exception as e:
                    # PDF creado pero BD no actualizada → riesgo de inconsistencia
                    logger.error(
                        f"❌ Error al actualizar BD para '{titular}' "
                        f"(Importancia: {importancia}): {e}. "
                        f"El PDF SÍ fue generado en: {ruta_archivo} — "
                        f"puede actualizarse manualmente si es necesario."
                    )
                    errores_generacion += 1

                # Notificar progreso al caller (UI) sin importar éxito/error
                if on_progress:
                    completados = reportes_generados + errores_generacion
                    try:
                        on_progress(completados, len(agrupados), titular)
                    except Exception:
                        pass  # El callback nunca debe interrumpir la generación
            
            # Resumen final
            logger.info(f"🎉 GENERACIÓN COMPLETADA:")
            logger.info(f"   • Informes generados exitosamente: {reportes_generados}/{len(agrupados)}")
            logger.info(f"   • Registros procesados: {sum(len(regs) for regs in agrupados.values())}")
            if pendientes > 0:
                logger.info(f"   • Registros pendientes sin procesar: {pendientes}")

            if errores_generacion > 0:
                logger.warning(f"⚠️  ATENCIÓN: {errores_generacion} informes fallaron")

            # Retornar información del resultado
            return {
                'success': True,
                'message': 'completed',
                'reportes_generados': reportes_generados,
                'total_titulares': len(agrupados),
                'registros_procesados': sum(len(regs) for regs in agrupados.values()),
                'pendientes': pendientes,
                'errores': errores_generacion
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
                              mes_ano_anterior: str, mes_ano_archivo: str, importancia: str) -> Tuple[str, str]:
        """Genera un informe individual para un titular con una importancia específica."""
        try:
            # Crear PDF con tema profesional
            watermark = self.watermark_path if self._validate_watermark() else None
            pdf = ProfessionalReportPDF(watermark, "ESTUDIO DE MARCAS Y PATENTES")
            pdf.add_page()
            
            # Título principal con importancia
            titulo_principal = f"INFORME DE MARCAS PUBLICADAS"
            #subtitulo = f"Clasificacion: {importancia.upper()} - Periodo: {mes_ano}"
            #pdf.add_main_title(titulo_principal, subtitulo)
            pdf.add_main_title(titulo_principal)
            
            # Sección de información general
            pdf.add_info_section(titular, mes_ano_anterior, len(registros))
            
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
            
            # Guardar PDF con nombre determinístico y trazable
            nombre_archivo = self._make_report_filename(titular, importancia, self.output_dir)
            ruta_archivo = os.path.join(self.output_dir, nombre_archivo)
            pdf.output(ruta_archivo)

            # Verificar que el archivo fue creado y tiene contenido real
            if not os.path.exists(ruta_archivo):
                raise RuntimeError(
                    f"pdf.output() no creó el archivo en disco: {ruta_archivo}"
                )
            if os.path.getsize(ruta_archivo) == 0:
                os.remove(ruta_archivo)
                raise RuntimeError(
                    f"El PDF generado está vacío (0 bytes), se descartó: {ruta_archivo}"
                )

            logger.info(f"Informe generado: {ruta_archivo}")
            return nombre_archivo, ruta_archivo

        except Exception as e:
            logger.error(f"Error al generar informe para {titular} (Importancia: {importancia}): {e}")
            raise


def generar_informe_pdf(conn, watermark_image: str = None, filtros=None, on_progress=None):
    """Función principal para mantener compatibilidad con el código anterior.

    Args:
        conn:          Conexión SQLite activa.
        watermark_image: Ignorado (se usa get_logo_path() internamente).
        filtros:       Dict opcional {'titulares': [...], 'importancias': [...]}.
                       None = generar todos los registros procesables.
        on_progress:   Callable(current, total, titular) para feedback de progreso.
    """
    generator = ReportGenerator(None)
    return generator.generate_reports(conn, filtros=filtros, on_progress=on_progress)