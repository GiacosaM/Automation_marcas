"""
Test para verificar el funcionamiento del script verificar_titulares_sin_reportes.py
"""
import unittest
import sqlite3
import os
from datetime import datetime, timedelta
import calendar
from unittest.mock import patch, MagicMock
import logging

# Importar la función principal a testear
from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes

class TestVerificarMarcasSinReportes(unittest.TestCase):
    """
    Pruebas para el sistema de verificación de marcas sin reportes
    """
    
    def setUp(self):
        """
        Configurar el entorno de prueba
        """
        # Crear una base de datos temporal para las pruebas
        self.db_path = "test_boletines.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Crear las tablas necesarias
        self.crear_tablas_prueba()
        
        # Insertar datos de prueba
        self.insertar_datos_prueba()
        
        # Configuración del logger para los tests
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def tearDown(self):
        """
        Limpiar después de las pruebas
        """
        # Cerrar conexión y eliminar la base de datos de prueba
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def crear_tablas_prueba(self):
        """
        Crear las tablas necesarias para las pruebas
        """
        # Tabla clientes
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            codigo TEXT,
            titular TEXT NOT NULL,
            email TEXT
        )
        ''')
        
        # Tabla Marcas
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Marcas (
            id INTEGER PRIMARY KEY,
            codtit TEXT,
            titular TEXT NOT NULL,
            codigo_marca TEXT,
            marca TEXT NOT NULL,
            clase TEXT,
            acta TEXT,
            nrocon TEXT,
            custodia TEXT,
            cuit TEXT,
            email TEXT,
            cliente_id INTEGER
        )
        ''')
        
        # Tabla boletines
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS boletines (
            id INTEGER PRIMARY KEY,
            titular TEXT NOT NULL,
            marca_publicada TEXT,
            marca_custodia TEXT,
            fecha_alta TEXT,
            reporte_generado INTEGER DEFAULT 0
        )
        ''')
        
        # Tabla emails_enviados
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails_enviados (
            id INTEGER PRIMARY KEY,
            destinatario TEXT NOT NULL,
            asunto TEXT,
            mensaje TEXT,
            fecha_envio TEXT,
            status TEXT,
            tipo_email TEXT,
            titular TEXT,
            periodo_notificacion TEXT,
            marcas_sin_reportes TEXT
        )
        ''')
        
        self.conn.commit()
    
    def insertar_datos_prueba(self):
        """
        Insertar datos de prueba en las tablas
        """
        # Fecha actual para los tests
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        # Insertar clientes
        self.cursor.executemany('''
        INSERT INTO clientes (codigo, titular, email)
        VALUES (?, ?, ?)
        ''', [
            ('C001', 'Cliente Prueba 1', 'cliente1@ejemplo.com'),
            ('C002', 'Cliente Prueba 2', 'cliente2@ejemplo.com'),
            ('C003', 'Cliente Prueba 3', 'cliente3@ejemplo.com')
        ])
        
        # Insertar marcas
        self.cursor.executemany('''
        INSERT INTO Marcas (codtit, titular, codigo_marca, marca, clase)
        VALUES (?, ?, ?, ?, ?)
        ''', [
            ('C001', 'Cliente Prueba 1', 'M001', 'Marca 1', '35'),
            ('C001', 'Cliente Prueba 1', 'M002', 'Marca 2', '38'),
            ('C001', 'Cliente Prueba 1', 'M003', 'Marca 3', '42'),
            ('C002', 'Cliente Prueba 2', 'M004', 'Marca 4', '9'),
            ('C002', 'Cliente Prueba 2', 'M005', 'Marca 5', '35'),
            ('C003', 'Cliente Prueba 3', 'M006', 'Marca 6', '25')
        ])
        
        # Insertar boletines (reportes)
        # Cliente 1: tiene reportes para Marca 1 y Marca 2, pero no para Marca 3
        # Cliente 2: tiene reportes para todas sus marcas
        # Cliente 3: no tiene reportes para ninguna marca
        primer_dia_mes = f"{anio_actual}-{mes_actual:02d}-01"
        
        self.cursor.executemany('''
        INSERT INTO boletines (titular, marca_publicada, marca_custodia, fecha_alta, reporte_generado)
        VALUES (?, ?, ?, ?, ?)
        ''', [
            ('Cliente Prueba 1', 'Marca 1', 'Marca 1', primer_dia_mes, 1),
            ('Cliente Prueba 1', 'Marca 2', 'Marca 2', primer_dia_mes, 1),
            ('Cliente Prueba 2', 'Marca 4', 'Marca 4', primer_dia_mes, 1),
            ('Cliente Prueba 2', 'Marca 5', 'Marca 5', primer_dia_mes, 1),
            # No hay reportes para Marca 3 y Marca 6
        ])
        
        self.conn.commit()
    
    def test_verificacion_marcas_sin_reportes(self):
        """
        Test para verificar que se detectan marcas sin reportes correctamente.
        """
        # Ejecutar la verificación sin enviar emails reales (solo probamos la detección)
        with patch('verificar_titulares_sin_reportes.obtener_credenciales_email') as mock_credenciales:
            mock_credenciales.return_value = (None, None)  # Esto evitará que se envíen emails
            
            # Ejecutar la función principal
            resultado = verificar_titulares_sin_reportes(self.conn)
        
        # Verificaciones
        self.assertEqual(resultado['estado'], 'completado')
        
        # Debe haber dos titulares con marcas sin reportes:
        # Cliente 1 (marca 3) y Cliente 3 (marca 6)
        self.assertEqual(resultado['titulares_con_marcas_sin_reportes'], 2)
        
        # Como no proporcionamos credenciales, no se deberían haber enviado emails
        self.assertEqual(resultado['emails_enviados'], 0)
    
    def test_deteccion_marcas_correctas(self):
        """
        Test para verificar que se detectan las marcas correctas sin reportes
        """
        # Fecha actual para el test
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        # Calcular el primer y último día del mes actual
        primer_dia = f"{anio_actual}-{mes_actual:02d}-01"
        ultimo_dia = f"{anio_actual}-{mes_actual:02d}-{calendar.monthrange(anio_actual, mes_actual)[1]:02d}"
        
        # Verificar manualmente qué marcas no tienen reportes
        cursor = self.conn.cursor()
        
        # Marcas del Cliente 1
        cursor.execute("""
            SELECT m.marca FROM Marcas m
            WHERE m.titular = 'Cliente Prueba 1'
            AND NOT EXISTS (
                SELECT 1 FROM boletines b 
                WHERE (b.marca_publicada = m.marca OR b.marca_custodia = m.marca)
                AND b.reporte_generado = 1
                AND b.fecha_alta BETWEEN ? AND ?
            )
        """, (primer_dia, ultimo_dia))
        
        marcas_sin_reportes_cliente1 = [row[0] for row in cursor.fetchall()]
        self.assertEqual(len(marcas_sin_reportes_cliente1), 1)
        self.assertIn('Marca 3', marcas_sin_reportes_cliente1)
        
        # Marcas del Cliente 3
        cursor.execute("""
            SELECT m.marca FROM Marcas m
            WHERE m.titular = 'Cliente Prueba 3'
            AND NOT EXISTS (
                SELECT 1 FROM boletines b 
                WHERE (b.marca_publicada = m.marca OR b.marca_custodia = m.marca)
                AND b.reporte_generado = 1
                AND b.fecha_alta BETWEEN ? AND ?
            )
        """, (primer_dia, ultimo_dia))
        
        marcas_sin_reportes_cliente3 = [row[0] for row in cursor.fetchall()]
        self.assertEqual(len(marcas_sin_reportes_cliente3), 1)
        self.assertIn('Marca 6', marcas_sin_reportes_cliente3)

    @patch('verificar_titulares_sin_reportes.obtener_credenciales_email')
    @patch('verificar_titulares_sin_reportes.smtplib.SMTP')
    @patch('email_templates.get_html_template')
    def test_envio_email(self, mock_get_template, mock_smtp, mock_credenciales):
        """
        Test para verificar que el envío de email funcione correctamente 
        cuando se proporcionan credenciales válidas
        """
        # Configurar mocks para simular credenciales válidas y servidor SMTP
        mock_credenciales.return_value = ('test@example.com', 'password')
        
        # Mock para la plantilla HTML
        mock_get_template.return_value = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <div class="container">
                <div class="content">
                <!-- El contenido del mensaje se insertará aquí -->
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear un servidor SMTP simulado
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Ejecutar la función principal
        resultado = verificar_titulares_sin_reportes(self.conn)
        
        # Verificaciones
        self.assertEqual(resultado['estado'], 'completado')
        self.assertEqual(resultado['titulares_con_marcas_sin_reportes'], 2)
        
        # Ahora deberían haberse enviado emails
        self.assertEqual(resultado['emails_enviados'], 2)
        
        # Verificar que se llamó al método starttls
        mock_server.starttls.assert_called()
        
        # Verificar que se llamó al método login con las credenciales correctas
        mock_server.login.assert_called_with('test@example.com', 'password')
        
        # Verificar que se llamó al método send_message dos veces (uno para cada cliente)
        self.assertEqual(mock_server.send_message.call_count, 2)
        
        # Verificar que se registró en la base de datos
        self.cursor.execute("SELECT COUNT(*) FROM emails_enviados WHERE tipo_email = 'notificacion_marcas'")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 2)
        
        # Verificar que los emails contenían las marcas correctas
        self.cursor.execute("SELECT titular, marcas_sin_reportes FROM emails_enviados WHERE tipo_email = 'notificacion_marcas'")
        registros = self.cursor.fetchall()
        
        titulares_notificados = [registro[0] for registro in registros]
        self.assertIn('Cliente Prueba 1', titulares_notificados)
        self.assertIn('Cliente Prueba 3', titulares_notificados)
        
        for titular, marcas in registros:
            if titular == 'Cliente Prueba 1':
                self.assertIn('Marca 3', marcas)
            elif titular == 'Cliente Prueba 3':
                self.assertIn('Marca 6', marcas)

if __name__ == '__main__':
    unittest.main()
