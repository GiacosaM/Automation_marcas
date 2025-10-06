import unittest
import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import crear_conexion
from db_migrations.create_verificaciones_log import crear_tabla_verificaciones_log

class TestVerificacionesLog(unittest.TestCase):
    def setUp(self):
        """Preparar el ambiente de prueba"""
        self.conn = crear_conexion()
        self.cursor = self.conn.cursor()
        
    def tearDown(self):
        """Limpiar después de cada test"""
        self.conn.close()
        
    def test_tabla_existe(self):
        """Verificar que la tabla existe con la estructura correcta"""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='verificaciones_log'
        """)
        self.assertIsNotNone(self.cursor.fetchone())
        
    def test_indice_existe(self):
        """Verificar que el índice existe"""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_verificaciones_mes'
        """)
        self.assertIsNotNone(self.cursor.fetchone())
        
    def test_insertar_registro(self):
        """Verificar que podemos insertar un registro exitosamente"""
        mes_actual = datetime.now().strftime('%Y-%m')
        try:
            self.cursor.execute("""
                INSERT INTO verificaciones_log 
                (mes_ejecutado, resultado, titulares_procesados) 
                VALUES (?, 'exitosa', 42)
            """, (mes_actual,))
            self.conn.commit()
            
            # Verificar que se insertó
            self.cursor.execute("""
                SELECT mes_ejecutado, resultado, titulares_procesados 
                FROM verificaciones_log 
                WHERE mes_ejecutado = ?
            """, (mes_actual,))
            
            registro = self.cursor.fetchone()
            self.assertIsNotNone(registro)
            self.assertEqual(registro[0], mes_actual)
            self.assertEqual(registro[1], 'exitosa')
            self.assertEqual(registro[2], 42)
            
        finally:
            # Limpiar el registro de prueba
            self.cursor.execute("DELETE FROM verificaciones_log WHERE mes_ejecutado = ?", (mes_actual,))
            self.conn.commit()
            
    def test_constraint_resultado(self):
        """Verificar que el check constraint de resultado funciona"""
        mes_actual = datetime.now().strftime('%Y-%m')
        with self.assertRaises(Exception):
            self.cursor.execute("""
                INSERT INTO verificaciones_log 
                (mes_ejecutado, resultado) 
                VALUES (?, 'invalido')
            """, (mes_actual,))
            
    def test_default_timestamp(self):
        """Verificar que el timestamp por defecto se genera"""
        mes_actual = datetime.now().strftime('%Y-%m')
        try:
            self.cursor.execute("""
                INSERT INTO verificaciones_log 
                (mes_ejecutado, resultado) 
                VALUES (?, 'en_progreso')
            """, (mes_actual,))
            self.conn.commit()
            
            self.cursor.execute("""
                SELECT fecha_ejecucion 
                FROM verificaciones_log 
                WHERE mes_ejecutado = ?
            """, (mes_actual,))
            
            registro = self.cursor.fetchone()
            self.assertIsNotNone(registro)
            self.assertIsNotNone(registro[0])  # Verifica que hay un timestamp
            
        finally:
            # Limpiar el registro de prueba
            self.cursor.execute("DELETE FROM verificaciones_log WHERE mes_ejecutado = ?", (mes_actual,))
            self.conn.commit()

if __name__ == '__main__':
    unittest.main()