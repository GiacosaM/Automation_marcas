#!/usr/bin/env python3
# verificador_programado.py

"""
Componente para añadir a la aplicación Streamlit que verifica
periódicamente si debe ejecutarse la validación de titulares sin reportes
"""

import streamlit as st
import threading
import time
import sys
from datetime import datetime, timedelta
import logging
from verificar_titulares_sin_reportes import ejecutar_verificacion_periodica
from database import crear_conexion

# Importar schedule con manejo de excepciones
try:
    import schedule
except ImportError:
    st.error("""
    El módulo 'schedule' no está instalado. 
    
    Por favor, ejecuta el siguiente comando para instalarlo:
    ```
    pip install schedule
    ```
    
    O ejecuta el script de configuración automática:
    ```
    python setup_automatizacion.py
    ```
    """)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verificacion_automatica.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('verificador_programado')

# Variable global para controlar el hilo de ejecución
_thread_running = False
_verificador_thread = None

def ejecutar_verificacion_si_primer_dia_mes():
    """Ejecuta la verificación solo si es el primer día del mes"""
    today = datetime.now()
    if today.day == 1:  # Es el primer día del mes
        return ejecutar_verificacion()
    else:
        logger.info("No es el primer día del mes, omitiendo verificación programada")
        return None

def ejecutar_verificacion():
    """Ejecutar la verificación programada"""
    try:
        logger.info("Iniciando verificación programada...")
        # Realizar la verificación
        resumen = verificar_automaticamente()
        
        # Actualizar el mensaje para mostrar en la interfaz
        st.session_state.verificacion_mensaje = f"✅ Verificación realizada: {resumen}"
        
        return resumen
    except Exception as e:
        logger.error(f"Error en verificación programada: {e}")
        st.session_state.verificacion_mensaje = f"❌ Error durante la verificación: {str(e)}"

def verificador_thread():
    """Función que se ejecuta en un hilo separado para programar tareas"""
    global _thread_running
    
    logger.info("Hilo verificador iniciado")
    
    # Programar la verificación para el primer día de cada mes a las 8:00 AM
    schedule.every().day.at("08:00").do(ejecutar_verificacion_si_primer_dia_mes)
    
    # Para pruebas, también podemos programarla para que se ejecute cada día a cierta hora
    #schedule.every().day.at("20:00").do(ejecutar_verificacion)
    
    # Loop principal del hilo
    while _thread_running:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto si hay tareas pendientes
    
    logger.info("Hilo verificador detenido")

def iniciar_verificador():
    """Inicia el hilo verificador si no está ya en ejecución"""
    global _thread_running, _verificador_thread
    
    if _thread_running:
        return
    
    _thread_running = True
    _verificador_thread = threading.Thread(target=verificador_thread, daemon=True)
    _verificador_thread.start()
    logger.info("Verificador programado iniciado")

def detener_verificador():
    """Detiene el hilo verificador"""
    global _thread_running
    
    if not _thread_running:
        return
    
    _thread_running = False
    logger.info("Señal de detención enviada al verificador programado")

def mostrar_panel_verificacion():
    """Muestra un panel de control para la verificación programada en Streamlit"""
    st.subheader("⏰ Verificación Programada de Titulares sin Reportes")
    
    # Verificar si schedule está disponible
    try:
        import schedule
        schedule_disponible = True
    except ImportError:
        schedule_disponible = False
        st.warning("""
        ⚠️ El módulo 'schedule' no está instalado. La verificación automática dentro de la aplicación
        no estará disponible, pero el cron job del sistema seguirá funcionando.
        
        Para habilitar la verificación automática dentro de la aplicación, ejecute:
        ```
        pip install schedule
        ```
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        Este componente verifica automáticamente los titulares sin reportes
        el primer día de cada mes a las 8:00 AM y envía notificaciones por email.
        """)
        
        # Mostrar próxima ejecución
        proximo_mes = datetime.now().replace(day=1) + timedelta(days=32)
        proximo_mes = proximo_mes.replace(day=1, hour=8, minute=0, second=0, microsecond=0)
        st.write(f"📅 **Próxima verificación programada:** {proximo_mes.strftime('%d/%m/%Y %H:%M')}")
        
        # Verificar si hay tareas cron configuradas
        try:
            import subprocess
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0 and 'ejecucion_programada.py' in result.stdout:
                st.success("✅ Cron job configurado correctamente en el sistema")
            else:
                st.warning("⚠️ No se detectó cron job para la verificación automática")
        except Exception:
            # Si no se puede verificar cron, simplemente no mostramos nada
            pass
        
        # Mostrar resultados de verificaciones recientes
        if "ultimas_verificaciones" in st.session_state and st.session_state.ultimas_verificaciones:
            st.write("📊 **Verificaciones recientes:**")
            
            for verificacion in reversed(st.session_state.ultimas_verificaciones):
                ya_notificados = verificacion.get("ya_notificados", 0)
                st.markdown(f"""
                *{verificacion["fecha"]}*: {verificacion["titulares_sin_reportes"]} titulares sin reportes, 
                {verificacion["emails_enviados"]} emails enviados, 
                {ya_notificados} ya notificados anteriormente, 
                {verificacion["errores"]} errores
                """)
    
    with col2:
        # Botón para ejecutar verificación manual
        if st.button("🔍 Ejecutar verificación ahora", use_container_width=True):
            with st.spinner("Ejecutando verificación..."):
                ejecutar_verificacion()
                # El mensaje de éxito se mostrará en la siguiente recarga
                st.rerun()  # Recargar para mostrar resultados actualizados
        
        # Mostrar mensaje de estado si existe
        if "verificacion_mensaje" in st.session_state:
            # Usar el mensaje guardado durante la ejecución
            st.write(st.session_state.verificacion_mensaje)
            # Opcionalmente, podemos limpiar el mensaje después de mostrarlo una vez
            # para que no persista indefinidamente
            # del st.session_state.verificacion_mensaje
        
        # Botón para ejecutar el script de configuración
        if not schedule_disponible:
            if st.button("⚙️ Configurar automatización", use_container_width=True):
                st.info("Ejecutando configuración en segundo plano...")
                try:
                    import subprocess
                    subprocess.Popen([sys.executable, "setup_automatizacion.py"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    st.success("✅ Configuración iniciada en segundo plano")
                except Exception as e:
                    st.error(f"❌ Error al iniciar configuración: {e}")

def inicializar_verificador_en_app():
    """
    Función principal para inicializar el verificador en la aplicación Streamlit.
    Debe llamarse al inicio de la aplicación.
    """
    # Verificar si schedule está disponible
    try:
        import schedule
        
        # Iniciar el hilo verificador cuando la aplicación carga
        if "verificador_iniciado" not in st.session_state:
            iniciar_verificador()
            st.session_state.verificador_iniciado = True
            
    except ImportError:
        # Si schedule no está disponible, registrar pero no bloquear la app
        logging.warning("No se pudo iniciar el verificador programado: módulo 'schedule' no disponible")
        # No bloqueamos la aplicación, simplemente no inicializamos el verificador

# Ejemplo de uso en una página de administración
if __name__ == "__main__":
    st.title("Panel de Administración")
    
    inicializar_verificador_en_app()
    mostrar_panel_verificacion()
