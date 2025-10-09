#!/bin/bash

# ============================================================================
# Script de Construcción del Paquete MiAppMarcas
# ============================================================================
# 
# Este script:
# 1. Compila el launcher con PyInstaller
# 2. Descarga Python embebido (si no existe)
# 3. Crea la estructura de carpetas final
# 4. Copia todos los archivos necesarios
# 5. Genera el paquete distribuible (.zip o .tar.gz)
#
# Resultado: carpeta MiAppMarcas/ lista para distribuir
# ============================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/build_release"
DIST_DIR="$SCRIPT_DIR/dist"
FINAL_PACKAGE="$BUILD_DIR/MiAppMarcas"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   MiAppMarcas - Build Release Package${NC}"
echo -e "${BLUE}================================================${NC}\n"

# ============================================================================
# Paso 1: Limpiar builds anteriores
# ============================================================================

echo -e "${YELLOW}[1/6]${NC} Limpiando builds anteriores..."
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$FINAL_PACKAGE"

# ============================================================================
# Paso 2: Compilar launcher con PyInstaller
# ============================================================================

echo -e "\n${YELLOW}[2/6]${NC} Compilando launcher con PyInstaller..."

cd "$SCRIPT_DIR"

# Activar venv si existe
if [ -d "$PROJECT_ROOT/build_venv" ]; then
    source "$PROJECT_ROOT/build_venv/bin/activate"
    echo -e "${GREEN}✓${NC} Virtual environment activado"
fi

# Compilar
pyinstaller --clean --noconfirm simple_launcher.spec

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Launcher compilado exitosamente"
else
    echo -e "${RED}✗${NC} Error compilando launcher"
    exit 1
fi

# Mover ejecutable a carpeta final
mv "$DIST_DIR/MiAppMarcas" "$FINAL_PACKAGE/"
if [ "$(uname)" == "Darwin" ]; then
    chmod +x "$FINAL_PACKAGE/MiAppMarcas"
fi

# ============================================================================
# Paso 3: Preparar Python embebido
# ============================================================================

echo -e "\n${YELLOW}[3/6]${NC} Preparando Python embebido..."

PYTHON_VERSION="3.13.5"
PYTHON_DIR="$FINAL_PACKAGE/python"

if [ "$(uname)" == "Darwin" ]; then
    # macOS: usar el Python del sistema o pyenv
    echo -e "  → Creando Python portable para macOS..."
    
    # Opción 1: Copiar Python del sistema (más simple)
    mkdir -p "$PYTHON_DIR/bin"
    mkdir -p "$PYTHON_DIR/lib"
    
    # Crear symlink al Python del sistema
    ln -sf "$(which python3)" "$PYTHON_DIR/bin/python3"
    ln -sf "$(which python3)" "$PYTHON_DIR/bin/python"
    
    echo -e "${GREEN}✓${NC} Python portable creado (usando Python del sistema)"
    
elif [ "$(uname)" == "Linux" ]; then
    # Linux: similar a macOS
    echo -e "  → Creando Python portable para Linux..."
    mkdir -p "$PYTHON_DIR/bin"
    ln -sf "$(which python3)" "$PYTHON_DIR/bin/python3"
    ln -sf "$(which python3)" "$PYTHON_DIR/bin/python"
    echo -e "${GREEN}✓${NC} Python portable creado"
else
    echo -e "${RED}✗${NC} Sistema operativo no soportado: $(uname)"
    exit 1
fi

# ============================================================================
# Paso 4: Copiar archivos de la aplicación
# ============================================================================

echo -e "\n${YELLOW}[4/6]${NC} Copiando archivos de la aplicación..."

# Crear directorio app
mkdir -p "$FINAL_PACKAGE/app"

# Copiar archivo principal
cp "$PROJECT_ROOT/app_refactored.py" "$FINAL_PACKAGE/app/"
echo -e "${GREEN}✓${NC} app_refactored.py copiado"

# Copiar base de datos
# Intentar copiar desde ~/Desktop/MiAppMarcas/ (donde la app la guarda realmente)
# Si no existe, copiar desde el proyecto
if [ -f "$HOME/Desktop/MiAppMarcas/boletines.db" ]; then
    cp "$HOME/Desktop/MiAppMarcas/boletines.db" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} boletines.db copiado (desde ~/Desktop/MiAppMarcas/)"
elif [ -f "$PROJECT_ROOT/boletines.db" ]; then
    cp "$PROJECT_ROOT/boletines.db" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} boletines.db copiado (desde proyecto)"
else
    echo -e "${YELLOW}⚠${NC} boletines.db no encontrado, se creará uno nuevo"
fi

# Copiar config.json (múltiples ubicaciones posibles)
if [ -f "$HOME/Desktop/MiAppMarcas/config.json" ]; then
    cp "$HOME/Desktop/MiAppMarcas/config.json" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} config.json copiado (desde ~/Desktop/MiAppMarcas/)"
elif [ -f "$PROJECT_ROOT/config.json" ]; then
    cp "$PROJECT_ROOT/config.json" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} config.json copiado (desde proyecto)"
else
    echo -e "${YELLOW}⚠${NC} config.json no encontrado"
fi

# Crear directorios necesarios para la aplicación
mkdir -p "$FINAL_PACKAGE/app/assets"
mkdir -p "$FINAL_PACKAGE/app/imagenes"
mkdir -p "$FINAL_PACKAGE/app/informes"
mkdir -p "$FINAL_PACKAGE/app/logs"
mkdir -p "$FINAL_PACKAGE/app/config"

# Copiar imágenes desde múltiples ubicaciones posibles
if [ -d "$HOME/Desktop/MiAppMarcas/imagenes" ]; then
    cp -r "$HOME/Desktop/MiAppMarcas/imagenes/"* "$FINAL_PACKAGE/app/imagenes/" 2>/dev/null
    echo -e "${GREEN}✓${NC} Imágenes copiadas (desde ~/Desktop/MiAppMarcas/imagenes/)"
fi
if [ -d "$PROJECT_ROOT/imagenes" ]; then
    cp -r "$PROJECT_ROOT/imagenes/"* "$FINAL_PACKAGE/app/imagenes/" 2>/dev/null
    echo -e "${GREEN}✓${NC} Imágenes copiadas (desde proyecto/imagenes/)"
fi

# Copiar assets si existen
if [ -d "$HOME/Desktop/MiAppMarcas/assets" ]; then
    cp -r "$HOME/Desktop/MiAppMarcas/assets/"* "$FINAL_PACKAGE/app/assets/" 2>/dev/null
    echo -e "${GREEN}✓${NC} Assets copiados (desde ~/Desktop/MiAppMarcas/assets/)"
fi

# Copiar carpeta src/ completa (arquitectura modular)
if [ -d "$PROJECT_ROOT/src" ]; then
    cp -r "$PROJECT_ROOT/src" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} Carpeta src/ copiada"
fi

# Copiar módulos necesarios
for module in database.py email_sender.py professional_theme.py paths.py config.py auth_manager_simple.py database_extensions.py email_utils.py email_templates.py db_utils.py report_generator.py dashboard_charts.py extractor.py utilidades_reportes.py email_verification_system.py; do
    if [ -f "$PROJECT_ROOT/$module" ]; then
        cp "$PROJECT_ROOT/$module" "$FINAL_PACKAGE/app/"
        echo -e "${GREEN}✓${NC} $module copiado"
    fi
done

# ============================================================================
# Paso 5: Crear requirements.txt
# ============================================================================

# ============================================================================
# Paso 5: Copiar requirements.txt del proyecto
# ============================================================================

echo -e "\n${YELLOW}[5/6]${NC} Copiando requirements.txt..."

if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    cp "$PROJECT_ROOT/requirements.txt" "$FINAL_PACKAGE/requirements.txt"
    echo -e "${GREEN}✓${NC} requirements.txt copiado desde proyecto"
else
    # Fallback: crear requirements.txt básico
    cat > "$FINAL_PACKAGE/requirements.txt" << 'EOF'
# Dependencias principales
streamlit>=1.28.0
streamlit-option-menu>=0.4.0
pandas>=2.0.0
numpy>=1.24.0
altair>=5.0.0
plotly>=5.14.0
Pillow>=10.0.0

# Backend y utilidades
tornado>=6.3
bcrypt>=4.0.0
appdirs>=1.4.4

# Opcional pero recomendado
watchdog>=3.0.0
EOF
    echo -e "${YELLOW}⚠${NC}  requirements.txt generado (no encontrado en proyecto)"
fi

# ============================================================================
# Paso 6: Crear documentación
# ============================================================================

echo -e "\n${YELLOW}[6/6]${NC} Creando documentación..."

# README para usuarios
cat > "$FINAL_PACKAGE/LEEME.txt" << 'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              MiAppMarcas - Gestión de Marcas              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

INSTRUCCIONES DE USO:
---------------------

1. PRIMERA VEZ:
   - Haz doble clic en "MiAppMarcas" (o MiAppMarcas.exe)
   - Espera 1-2 minutos mientras se configura automáticamente
   - El navegador se abrirá automáticamente

2. USOS SIGUIENTES:
   - Haz doble clic en "MiAppMarcas"
   - El navegador se abrirá en 3-5 segundos
   - ¡Listo!

NOTAS IMPORTANTES:
------------------
• NO muevas ni borres las carpetas "python" o ".venv"
• Puedes mover toda la carpeta MiAppMarcas a otro lugar
• Los datos se guardan en la carpeta "app"
• Si hay problemas, revisa el archivo "launcher.log"

SOPORTE:
--------
Email: soporte@tuempresa.com
Teléfono: +54 XXX XXXX

EOF

# Archivo de versión
cat > "$FINAL_PACKAGE/VERSION.txt" << EOF
MiAppMarcas
Versión: 1.0.0
Fecha: $(date +%Y-%m-%d)
Python: $PYTHON_VERSION
EOF

echo -e "${GREEN}✓${NC} Documentación creada"

# ============================================================================
# Resumen Final
# ============================================================================

echo -e "\n${BLUE}================================================${NC}"
echo -e "${GREEN}✓ BUILD COMPLETADO EXITOSAMENTE${NC}"
echo -e "${BLUE}================================================${NC}\n"

echo -e "📦 Paquete generado en:"
echo -e "   ${GREEN}$FINAL_PACKAGE${NC}\n"

# Calcular tamaño
PACKAGE_SIZE=$(du -sh "$FINAL_PACKAGE" | cut -f1)
echo -e "📊 Tamaño del paquete: ${YELLOW}$PACKAGE_SIZE${NC}\n"

echo -e "📁 Contenido:"
ls -lh "$FINAL_PACKAGE" | tail -n +2 | awk '{printf "   %s  %s\n", $9, $5}'

echo -e "\n${YELLOW}PRÓXIMOS PASOS:${NC}"
echo -e "   1. Prueba el ejecutable:"
echo -e "      ${BLUE}cd $FINAL_PACKAGE && ./MiAppMarcas${NC}"
echo -e "   2. Para distribuir, comprime la carpeta:"
echo -e "      ${BLUE}cd $BUILD_DIR && tar -czf MiAppMarcas-v1.0.0.tar.gz MiAppMarcas/${NC}"
echo -e "   3. Envía el .tar.gz a tus clientes\n"

echo -e "${GREEN}¡Listo! 🎉${NC}\n"
