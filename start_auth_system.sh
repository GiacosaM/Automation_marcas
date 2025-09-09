#!/bin/bash

echo "🚀 Iniciando Sistema de Verificación de Usuarios por Email"
echo "=========================================================="
echo ""
echo "📋 Verificando dependencias..."

# Verificar que Python está instalado
if command -v python3 &> /dev/null; then
    echo "✅ Python3 encontrado: $(python3 --version)"
else
    echo "❌ Python3 no encontrado. Por favor instala Python 3.8+"
    exit 1
fi

# Verificar que Streamlit está instalado
if python3 -c "import streamlit" &> /dev/null; then
    echo "✅ Streamlit encontrado"
else
    echo "⚠️ Streamlit no encontrado. Instalando..."
    pip3 install streamlit
fi

echo ""
echo "🔧 Configuración del sistema:"
echo "• Base de datos: boletines.db"
echo "• Configuración de email: email_config.json"
echo ""

# Verificar configuración de email
if [ -f "email_config.json" ]; then
    echo "✅ Archivo de configuración de email encontrado"
    
    # Verificar si las credenciales están configuradas
    if grep -q "tu_email@gmail.com" email_config.json; then
        echo "⚠️ ADVERTENCIA: Credenciales de email no configuradas"
        echo "📝 Edita email_config.json para configurar el envío de emails"
    else
        echo "📧 Credenciales de email configuradas"
    fi
else
    echo "❌ Archivo email_config.json no encontrado"
    exit 1
fi

echo ""
echo "🧪 Ejecutando pruebas del sistema..."
python3 test_auth_system.py

echo ""
echo "🌐 Iniciando aplicación web..."
echo "📍 URL: http://localhost:8501"
echo "🛑 Para detener la aplicación: Ctrl+C"
echo ""

# Iniciar Streamlit
streamlit run auth_app.py
