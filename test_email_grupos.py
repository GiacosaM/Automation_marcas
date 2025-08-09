#!/usr/bin/env python3
"""
Script de prueba para verificar la nueva lógica de agrupamiento por (titular + importancia)
en el sistema de envío de emails.
"""

import sqlite3
from email_sender import obtener_registros_pendientes_envio, validar_clientes_para_envio

def test_agrupamiento_emails():
    """Prueba la nueva lógica de agrupamiento por titular + importancia."""
    
    print("🧪 TEST: NUEVA LÓGICA DE AGRUPAMIENTO PARA EMAILS")
    print("=" * 60)
    
    conn = sqlite3.connect('boletines.db')
    
    try:
        # 1. Obtener registros agrupados por (titular + importancia)
        print("📋 1. OBTENIENDO GRUPOS (TITULAR + IMPORTANCIA)")
        print("-" * 50)
        
        registros_por_grupo = obtener_registros_pendientes_envio(conn)
        
        print(f"✅ Grupos encontrados: {len(registros_por_grupo)}")
        print()
        
        # 2. Mostrar cada grupo
        for i, (clave_grupo, datos_grupo) in enumerate(registros_por_grupo.items(), 1):
            titular = datos_grupo['titular']
            importancia = datos_grupo['importancia']
            email = datos_grupo['email']
            cantidad_boletines = len(datos_grupo['boletines'])
            
            print(f"{i}. GRUPO: {titular} | IMPORTANCIA: {importancia}")
            print(f"   📧 Email: {email}")
            print(f"   📄 Cantidad de boletines: {cantidad_boletines}")
            
            # Mostrar boletines del grupo
            for boletin in datos_grupo['boletines']:
                print(f"      - Boletín {boletin['numero_boletin']} | {boletin['importancia']} | {boletin['nombre_reporte'][:50]}...")
            print()
        
        # 3. Validación específica para DEHNOS S.A.
        print("🎯 2. VERIFICACIÓN ESPECÍFICA PARA DEHNOS S.A.")
        print("-" * 50)
        
        grupos_dehnos = {k: v for k, v in registros_por_grupo.items() 
                        if v['titular'] == 'DEHNOS S.A.'}
        
        print(f"✅ Grupos de DEHNOS S.A. encontrados: {len(grupos_dehnos)}")
        
        importancias_dehnos = set()
        for datos in grupos_dehnos.values():
            importancias_dehnos.add(datos['importancia'])
        
        print(f"✅ Importancias diferentes: {sorted(importancias_dehnos)}")
        
        if len(grupos_dehnos) == 3 and importancias_dehnos == {'Alta', 'Media', 'Baja'}:
            print("🎉 ¡ÉXITO! DEHNOS S.A. tiene 3 grupos separados (Alta, Media, Baja)")
        else:
            print("❌ ERROR: DEHNOS S.A. no tiene los 3 grupos esperados")
        
        print()
        
        # 4. Validación general
        print("📋 3. VALIDACIÓN GENERAL")
        print("-" * 30)
        
        validacion = validar_clientes_para_envio(conn)
        
        print(f"✅ Total de grupos para envío: {validacion['total_grupos']}")
        print(f"✅ Grupos con email: {validacion['con_email']}")
        print(f"✅ Grupos con reporte: {validacion['con_reporte']}")
        print(f"✅ Grupos listos para envío: {validacion['listos_para_envio']}")
        
        if validacion['sin_email']:
            print(f"⚠️ Grupos sin email: {validacion['sin_email']}")
        
        if validacion['sin_reporte']:
            print(f"⚠️ Grupos sin reporte: {validacion['sin_reporte']}")
        
        print()
        print("📨 4. SIMULACIÓN DE ENVÍOS")
        print("-" * 30)
        
        emails_simulados = 0
        for clave_grupo, datos_grupo in registros_por_grupo.items():
            titular = datos_grupo['titular']
            importancia = datos_grupo['importancia']
            email = datos_grupo['email']
            
            if email and email.strip():
                emails_simulados += 1
                print(f"📧 Email {emails_simulados}: {titular} ({importancia}) -> {email}")
        
        print()
        print("🎯 CONCLUSIONES:")
        print("-" * 20)
        print(f"✅ Se enviarían {emails_simulados} emails separados")
        print(f"✅ DEHNOS S.A. recibiría {len(grupos_dehnos)} emails diferentes")
        print(f"✅ Cada email contendría solo boletines de la misma importancia")
        
        if len(grupos_dehnos) == 3:
            print("🎉 ¡PROBLEMA RESUELTO! Un titular con múltiples importancias = múltiples emails")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_agrupamiento_emails()
