#!/usr/bin/env python3
"""
Script para corregir el problema de las pestañas en app.py
"""

import os

def buscar_estructura_condicional(archivo):
    """Busca la estructura condicional problemática"""
    with open(archivo, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    estructura = []
    for i, line in enumerate(lines):
        if 'tab1, tab2, tab3, tab4, tab5' in line:
            print(f"Línea {i+1}: Pestañas encontradas")
            # Buscar hacia atrás para encontrar la estructura condicional
            for j in range(max(0, i-20), i):
                if 'if stats[' in lines[j] and ('pendientes_revision' in lines[j] or 'listos_envio' in lines[j]):
                    print(f"Línea {j+1}: Condicional problemático: {lines[j].strip()}")
                    estructura.append((j+1, lines[j].strip()))
            
            # Buscar hacia adelante para encontrar el else correspondiente
            nivel_indentacion = len(line) - len(line.lstrip())
            for j in range(i+1, min(len(lines), i+500)):
                if lines[j].strip().startswith('else:'):
                    indentacion_else = len(lines[j]) - len(lines[j].lstrip())
                    if indentacion_else <= nivel_indentacion:
                        print(f"Línea {j+1}: Else correspondiente: {lines[j].strip()}")
                        estructura.append((j+1, lines[j].strip()))
                        break
    
    return estructura

def encontrar_problema():
    archivo = '/Users/martingiacosa/Desktop/Proyectos/Python/Automation/app.py'
    print("🔍 Analizando la estructura del archivo app.py...")
    
    estructura = buscar_estructura_condicional(archivo)
    
    if estructura:
        print("\n📋 Estructura problemática encontrada:")
        for linea, contenido in estructura:
            print(f"  Línea {linea}: {contenido}")
    else:
        print("❌ No se encontró la estructura problemática")

if __name__ == "__main__":
    encontrar_problema()
