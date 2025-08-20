#!/usr/bin/env python3
"""
Test específico para queries complejas de fecha con julianday
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import convertir_query_boolean

def test_complex_date_queries():
    """Test queries complejas que están fallando"""
    
    # Query problemática del dashboard
    query_problematica = """
        SELECT numero_boletin, titular, fecha_boletin,
               CAST(julianday(date(substr(fecha_boletin, 7, 4) || '-' || 
                                  substr(fecha_boletin, 4, 2) || '-' || 
                                  substr(fecha_boletin, 1, 2), '+30 days')) - 
                    julianday(date('now')) AS INTEGER) as dias_restantes
        FROM boletines 
        WHERE reporte_enviado = 0 
        AND fecha_boletin IS NOT NULL AND fecha_boletin != ''
    """
    
    print("=== TEST DE QUERY COMPLEJA ===")
    print("Query original:")
    print(query_problematica.strip())
    
    query_convertida = convertir_query_boolean(query_problematica)
    print("\nQuery convertida:")
    print(query_convertida.strip())
    
    # Test de queries más simples paso a paso
    print("\n=== TESTS PASO A PASO ===")
    
    test_cases = [
        "date('now')",
        "date(substr(fecha_boletin, 7, 4) || '-' || substr(fecha_boletin, 4, 2) || '-' || substr(fecha_boletin, 1, 2))",
        "date(substr(fecha_boletin, 7, 4) || '-' || substr(fecha_boletin, 4, 2) || '-' || substr(fecha_boletin, 1, 2), '+30 days')",
        "julianday(date('now'))",
        "julianday(date(substr(fecha_boletin, 7, 4) || '-' || substr(fecha_boletin, 4, 2) || '-' || substr(fecha_boletin, 1, 2), '+30 days'))",
        "CAST(julianday(date(substr(fecha_boletin, 7, 4) || '-' || substr(fecha_boletin, 4, 2) || '-' || substr(fecha_boletin, 1, 2), '+30 days')) - julianday(date('now')) AS INTEGER)"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        converted = convertir_query_boolean(test_case)
        print(f"\nTest {i}:")
        print(f"Original:  {test_case}")
        print(f"Convertido: {converted}")

if __name__ == "__main__":
    test_complex_date_queries()
