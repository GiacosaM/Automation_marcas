#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la generación de informes por titular
"""

import sqlite3
from collections import defaultdict
from datetime import datetime

def diagnosticar_generacion_informes():
    """Diagnostica cómo se están agrupando los registros para los informes."""
    
    conn = sqlite3.connect('boletines.db')
    cursor = conn.cursor()
    
    print("🔍 DIAGNÓSTICO DE GENERACIÓN DE INFORMES")
    print("=" * 60)
    
    # 1. Verificar registros pendientes
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 0
    ''')
    total_pendientes = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 0 AND importancia = 'Pendiente'
    ''')
    pendientes_importancia = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 0 AND importancia != 'Pendiente'
    ''')
    listos_procesar = cursor.fetchone()[0]
    
    print(f"📊 ESTADO ACTUAL:")
    print(f"   • Total registros sin procesar: {total_pendientes}")
    print(f"   • Con importancia 'Pendiente': {pendientes_importancia}")
    print(f"   • Listos para procesar: {listos_procesar}")
    print()
    
    # 2. Mostrar agrupación por titular + importancia
    cursor.execute('''
        SELECT titular, numero_boletin, fecha_boletin, importancia
        FROM boletines
        WHERE reporte_generado = 0 AND importancia != 'Pendiente'
        ORDER BY titular, importancia, fecha_boletin DESC
    ''')
    
    registros = cursor.fetchall()
    
    if not registros:
        print("❌ No hay registros listos para procesar")
        print("💡 Verifica que:")
        print("   - Haya registros con reporte_generado = 0")
        print("   - Los registros no tengan importancia = 'Pendiente'")
        conn.close()
        return
    
    # Agrupar por titular + importancia (NUEVA LÓGICA)
    agrupados = defaultdict(list)
    for registro in registros:
        titular = registro[0]
        importancia = registro[3]
        clave_agrupacion = (titular, importancia)
        agrupados[clave_agrupacion].append(registro)
    
    titulares_unicos = len(set(clave[0] for clave in agrupados.keys()))
    
    print(f"📋 AGRUPACIÓN POR TITULAR + IMPORTANCIA:")
    print(f"   • Titulares únicos: {titulares_unicos}")
    print(f"   • Grupos (titular + importancia): {len(agrupados)}")
    print()
    
    for i, ((titular, importancia), registros_grupo) in enumerate(agrupados.items(), 1):
        print(f"{i}. TITULAR: {titular} | IMPORTANCIA: {importancia}")
        print(f"   📄 Cantidad de registros: {len(registros_grupo)}")
        print(f"   📋 Boletines:")
        for reg in registros_grupo:
            print(f"      - {reg[1]} | {reg[2]} | {reg[3]}")
        print()
    
    # 3. Simular nombres de archivos que se generarían
    fecha_actual = datetime.now()
    meses_castellano = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
        'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
        'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    mes_ingles = fecha_actual.strftime("%B %Y")
    mes_ano_archivo = fecha_actual.strftime("%B-%Y")
    
    print(f"📁 ARCHIVOS QUE SE GENERARÍAN:")
    print(f"   • Período: {mes_ano_archivo}")
    print()
    
    def clean_filename(filename):
        return "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    
    for i, ((titular, importancia), registros_grupo) in enumerate(agrupados.items(), 1):
        titular_limpio = clean_filename(titular)
        nombre_archivo = f"{mes_ano_archivo} - Informe {titular_limpio} - {importancia} - XXXXXX.pdf"
        print(f"{i}. {nombre_archivo}")
        print(f"   🗂️  Incluirá {len(registros_grupo)} registros con importancia {importancia}")
    
    print()
    print("🎯 CONCLUSIÓN:")
    if len(agrupados) > 1:
        print(f"✅ Se generarán {len(agrupados)} informes separados (por titular + importancia)")
        print(f"✅ Titulares únicos: {titulares_unicos}")
        print(f"✅ Un mismo titular puede tener múltiples informes si tiene registros con diferentes importancias")
    elif len(agrupados) == 1:
        print(f"ℹ️  Se generará 1 informe (solo hay 1 combinación titular + importancia)")
    else:
        print(f"❌ No se generará ningún informe")
    
    # 4. Verificar si hay registros ya procesados
    cursor.execute('''
        SELECT COUNT(*) FROM boletines 
        WHERE reporte_generado = 1
    ''')
    ya_procesados = cursor.fetchone()[0]
    
    print(f"📈 HISTORIAL:")
    print(f"   • Reportes ya generados anteriormente: {ya_procesados}")
    
    if ya_procesados > 0:
        cursor.execute('''
            SELECT titular, COUNT(*) as cantidad, MIN(fecha_creacion_reporte) as primera_fecha
            FROM boletines 
            WHERE reporte_generado = 1
            GROUP BY titular
            ORDER BY cantidad DESC
            LIMIT 5
        ''')
        procesados_por_titular = cursor.fetchall()
        
        print(f"   • Top 5 titulares con informes generados:")
        for titular, cantidad, fecha in procesados_por_titular:
            print(f"      - {titular}: {cantidad} registros (desde {fecha})")
    
    conn.close()

if __name__ == "__main__":
    diagnosticar_generacion_informes()
