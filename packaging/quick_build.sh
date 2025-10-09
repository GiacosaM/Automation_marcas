#!/bin/bash

# ============================================================================
# Script de Compilación Rápida - MiAppMarcas
# ============================================================================
# Este script hace una compilación limpia y rápida sin las complicaciones
# del script completo.
# ============================================================================

set -e  # Salir si hay algún error

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/build_release"
FINAL_PACKAGE="$BUILD_DIR/MiAppMarcas"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   MiAppMarcas - Compilación Rápida${NC}"
echo -e "${BLUE}============================================${NC}\n"

# ============================================================================
# Paso 1: Limpiar build anterior
# ============================================================================

echo -e "${YELLOW}[1/5]${NC} Limpiando build anterior..."
rm -rf "$BUILD_DIR"
rm -rf "$SCRIPT_DIR/dist"
mkdir -p "$BUILD_DIR"
mkdir -p "$FINAL_PACKAGE"
mkdir -p "$FINAL_PACKAGE/app"

# ============================================================================
# Paso 2: Compilar launcher
# ============================================================================

echo -e "\n${YELLOW}[2/5]${NC} Compilando launcher..."

cd "$SCRIPT_DIR"

# Activar venv
if [ -d "$PROJECT_ROOT/build_venv" ]; then
    source "$PROJECT_ROOT/build_venv/bin/activate"
fi

# Compilar
pyinstaller --clean --noconfirm simple_launcher.spec > /dev/null 2>&1

# Mover ejecutable
mv "$SCRIPT_DIR/dist/MiAppMarcas" "$FINAL_PACKAGE/"
chmod +x "$FINAL_PACKAGE/MiAppMarcas"

echo -e "${GREEN}✓${NC} Launcher compilado"

# ============================================================================
# Paso 3: Preparar Python embebido
# ============================================================================

echo -e "\n${YELLOW}[3/5]${NC} Preparando Python embebido..."

PYTHON_DIR="$FINAL_PACKAGE/python"
mkdir -p "$PYTHON_DIR/bin"
mkdir -p "$PYTHON_DIR/lib"

# Crear symlink al Python del sistema
ln -sf "$(which python3)" "$PYTHON_DIR/bin/python3"
ln -sf "$(which python3)" "$PYTHON_DIR/bin/python"

echo -e "${GREEN}✓${NC} Python portable creado"

# ============================================================================
# Paso 4: Copiar archivos de la aplicación
# ============================================================================

echo -e "\n${YELLOW}[4/5]${NC} Copiando archivos de la aplicación..."

# Copiar archivos críticos
cp "$PROJECT_ROOT/app_refactored.py" "$FINAL_PACKAGE/app/"
echo -e "${GREEN}✓${NC} app_refactored.py"

# Copiar requirements.txt
cp "$PROJECT_ROOT/requirements.txt" "$FINAL_PACKAGE/"
echo -e "${GREEN}✓${NC} requirements.txt"

# Copiar carpeta src/
cp -R "$PROJECT_ROOT/src" "$FINAL_PACKAGE/app/"
echo -e "${GREEN}✓${NC} Carpeta src/ ($(find "$FINAL_PACKAGE/app/src" -name "*.py" | wc -l | xargs) archivos)"

# Copiar base de datos y config
if [ -f "$HOME/Desktop/MiAppMarcas/boletines.db" ]; then
    cp "$HOME/Desktop/MiAppMarcas/boletines.db" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} boletines.db (desde ~/Desktop/MiAppMarcas/)"
elif [ -f "$PROJECT_ROOT/boletines.db" ]; then
    cp "$PROJECT_ROOT/boletines.db" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} boletines.db (desde proyecto)"
fi

if [ -f "$HOME/Desktop/MiAppMarcas/config.json" ]; then
    cp "$HOME/Desktop/MiAppMarcas/config.json" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} config.json"
elif [ -f "$PROJECT_ROOT/config.json" ]; then
    cp "$PROJECT_ROOT/config.json" "$FINAL_PACKAGE/app/"
    echo -e "${GREEN}✓${NC} config.json"
fi

# Crear directorios necesarios
mkdir -p "$FINAL_PACKAGE/app/assets"
mkdir -p "$FINAL_PACKAGE/app/imagenes"
mkdir -p "$FINAL_PACKAGE/app/informes"
mkdir -p "$FINAL_PACKAGE/app/logs"
mkdir -p "$FINAL_PACKAGE/app/config"

# Copiar imágenes
if [ -d "$HOME/Desktop/MiAppMarcas/imagenes" ]; then
    cp "$HOME/Desktop/MiAppMarcas/imagenes/"* "$FINAL_PACKAGE/app/imagenes/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Imágenes copiadas"
fi

# Copiar módulos Python necesarios
echo -e "\n${BLUE}Copiando módulos Python...${NC}"
MODULES=(
    database.py
    email_sender.py
    professional_theme.py
    paths.py
    config.py
    auth_manager_simple.py
    database_extensions.py
    email_utils.py
    email_templates.py
    db_utils.py
    report_generator.py
    dashboard_charts.py
    extractor.py
    utilidades_reportes.py
    email_verification_system.py
)

for module in "${MODULES[@]}"; do
    if [ -f "$PROJECT_ROOT/$module" ]; then
        cp "$PROJECT_ROOT/$module" "$FINAL_PACKAGE/app/"
        echo -e "${GREEN}✓${NC} $module"
    fi
done

# ============================================================================
# Paso 5: Verificar archivos críticos
# ============================================================================

echo -e "\n${YELLOW}[5/5]${NC} Verificando archivos críticos..."

VERIFICATION_PASSED=true

# Verificar requirements.txt
if [ -f "$FINAL_PACKAGE/requirements.txt" ]; then
    echo -e "${GREEN}✓${NC} requirements.txt"
else
    echo -e "${RED}✗${NC} requirements.txt FALTANTE"
    VERIFICATION_PASSED=false
fi

# Verificar carpeta src/
SRC_FILES=$(find "$FINAL_PACKAGE/app/src" -name "*.py" 2>/dev/null | wc -l | xargs)
if [ "$SRC_FILES" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Carpeta src/ ($SRC_FILES archivos)"
else
    echo -e "${RED}✗${NC} Carpeta src/ vacía o faltante"
    VERIFICATION_PASSED=false
fi

# Verificar app_refactored.py
if [ -f "$FINAL_PACKAGE/app/app_refactored.py" ]; then
    echo -e "${GREEN}✓${NC} app_refactored.py"
else
    echo -e "${RED}✗${NC} app_refactored.py FALTANTE"
    VERIFICATION_PASSED=false
fi

# Verificar módulos Python
MODULES_COUNT=$(ls "$FINAL_PACKAGE/app/"*.py 2>/dev/null | wc -l | xargs)
echo -e "${GREEN}✓${NC} Módulos Python ($MODULES_COUNT archivos)"

# Verificar ejecutable
if [ -f "$FINAL_PACKAGE/MiAppMarcas" ]; then
    echo -e "${GREEN}✓${NC} Ejecutable MiAppMarcas"
else
    echo -e "${RED}✗${NC} Ejecutable FALTANTE"
    VERIFICATION_PASSED=false
fi

# ============================================================================
# Resumen Final
# ============================================================================

echo -e "\n${BLUE}============================================${NC}"

if [ "$VERIFICATION_PASSED" = true ]; then
    echo -e "${GREEN}✓ BUILD COMPLETADO EXITOSAMENTE${NC}"
else
    echo -e "${RED}⚠ BUILD COMPLETADO CON ADVERTENCIAS${NC}"
fi

echo -e "${BLUE}============================================${NC}\n"

PACKAGE_SIZE=$(du -sh "$FINAL_PACKAGE" 2>/dev/null | cut -f1)
echo -e "📦 Ubicación: ${GREEN}$FINAL_PACKAGE${NC}"
echo -e "📊 Tamaño: ${YELLOW}$PACKAGE_SIZE${NC}\n"

echo -e "${YELLOW}PRÓXIMOS PASOS:${NC}"
echo -e "   1. Probar el ejecutable:"
echo -e "      ${BLUE}cd build_release/MiAppMarcas${NC}"
echo -e "      ${BLUE}rm -rf .venv launcher.log${NC}"
echo -e "      ${BLUE}./MiAppMarcas${NC}\n"
echo -e "   2. Si funciona correctamente, comprimir:"
echo -e "      ${BLUE}cd build_release${NC}"
echo -e "      ${BLUE}tar --exclude='.venv' --exclude='*.log' -czf MiAppMarcas-v1.0.0.tar.gz MiAppMarcas/${NC}\n"

echo -e "${GREEN}¡Listo!${NC} 🚀\n"
