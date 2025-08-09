#!/usr/bin/env python3
"""
Parche para corregir la visibilidad de las pestañas en app.py
Este script aplicará una corrección específica
"""

import re

def aplicar_correccion():
    archivo = '/Users/martingiacosa/Desktop/Proyectos/Python/Automation/app.py'
    
    # Leer el archivo
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar el patrón problemático y reemplazarlo
    patron_original = r'(\s+)# Pestañas para organizar la funcionalidad - SIEMPRE VISIBLES\s+st\.subheader\("🔧 Gestión de Emails"\)\s+tab1, tab2, tab3, tab4, tab5 = st\.tabs\(\["🚀 Enviar Emails", "⚙️ Configuración", "📊 Historial de Envíos", "📋 Logs Detallados", "📁 Emails Enviados"\]\)'
    
    reemplazo = '''
                # Pestañas para organizar la funcionalidad - SIEMPRE VISIBLES
                st.subheader("🔧 Gestión de Emails")
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Enviar Emails", "⚙️ Configuración", "📊 Historial de Envíos", "📋 Logs Detallados", "📁 Emails Enviados"])'''
    
    # Aplicar el reemplazo
    if re.search(patron_original, contenido, re.MULTILINE):
        contenido_nuevo = re.sub(patron_original, reemplazo, contenido, flags=re.MULTILINE)
        
        # Guardar backup
        with open(archivo + '.backup', 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        # Guardar archivo corregido
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(contenido_nuevo)
        
        print("✅ Corrección aplicada exitosamente")
        print(f"💾 Backup guardado en: {archivo}.backup")
    else:
        print("❌ No se encontró el patrón para corregir")

if __name__ == "__main__":
    aplicar_correccion()
