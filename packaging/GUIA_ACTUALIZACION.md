# 🔄 Guía de Actualización y Distribución

## 📋 Flujo de Trabajo: Desarrollo → Distribución

### 1️⃣ Realizar Modificaciones en tu Código

Trabaja normalmente en tu proyecto:
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation
# Edita tus archivos Python, modifica la UI, actualiza la DB, etc.
```

### 2️⃣ Reconstruir el Paquete

Una vez que hayas terminado tus modificaciones, ejecuta:

```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./build_release.sh
```

**Tiempo estimado**: 30-60 segundos

**Qué hace este script**:
- ✅ Compila el launcher (7MB)
- ✅ Copia toda tu aplicación actualizada
- ✅ Copia la base de datos más reciente
- ✅ Copia imágenes, assets, config
- ✅ Genera requirements.txt actualizado
- ✅ Crea documentación para el usuario

### 3️⃣ Probar el Paquete Localmente

Antes de enviar al cliente, pruébalo:

```bash
cd build_release/MiAppMarcas
rm -rf .venv launcher.log  # Limpiar instalación previa
./MiAppMarcas
```

Verifica que:
- ✅ La aplicación inicia correctamente
- ✅ Las imágenes se muestran
- ✅ Los datos de la DB son correctos
- ✅ Todas las funcionalidades funcionan

### 4️⃣ Crear Paquete de Distribución

#### Para macOS (cliente con Mac):
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging/build_release
tar --exclude='.venv' --exclude='launcher.log' --exclude='__pycache__' --exclude='*.pyc' \
    -czf MiAppMarcas-v1.0.0-macos.tar.gz MiAppMarcas/
```

#### Para Windows (tu caso):
**NO puedes compilar para Windows desde macOS directamente**. Tienes 2 opciones:

**Opción A: Distribuir como Proyecto Python (RECOMENDADO para cross-platform)**
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation
tar --exclude='.venv' --exclude='build_venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='packaging/build_release' \
    --exclude='packaging/dist' --exclude='packaging/build' \
    -czf MiAppMarcas-Python-v1.0.0.tar.gz .
```

El cliente necesitará:
- Python 3.11+ instalado
- Ejecutar: `pip install -r requirements.txt`
- Ejecutar: `streamlit run app_refactored.py`

**Opción B: Compilar en Windows (MEJOR UX para cliente)**

Necesitas acceso a una máquina Windows (VM, servidor, o PC del cliente) para compilar.

---

## 🪟 Compilar Ejecutable para Windows

### Requisitos previos en Windows:
- Python 3.11 o 3.12 (NO uses 3.13, tiene problemas con PyInstaller)
- Git (para clonar el repositorio)

### Pasos en Windows:

1. **Clonar el repositorio**:
```cmd
git clone https://github.com/GiacosaM/Automation_marcas.git
cd Automation_marcas
```

2. **Crear entorno virtual**:
```cmd
python -m venv build_venv
build_venv\Scripts\activate
```

3. **Instalar PyInstaller**:
```cmd
pip install pyinstaller
```

4. **Modificar `build_release.sh` para Windows**:

Crea un archivo `build_release.bat`:

```batch
@echo off
echo ============================================================
echo   Building MiAppMarcas for Windows
echo ============================================================

REM Activar entorno virtual
call build_venv\Scripts\activate.bat

REM Paso 1: Limpiar builds anteriores
echo [1/6] Limpiando builds anteriores...
if exist build_release rmdir /s /q build_release
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Paso 2: Compilar launcher
echo [2/6] Compilando launcher...
cd packaging
pyinstaller --clean --noconfirm simple_launcher.spec
cd ..

REM Paso 3: Crear estructura del paquete
echo [3/6] Creando estructura...
mkdir build_release\MiAppMarcas
xcopy /E /I /Y packaging\dist\MiAppMarcas.exe build_release\MiAppMarcas\

REM Paso 4: Copiar Python portable
echo [4/6] Copiando Python...
mkdir build_release\MiAppMarcas\python
xcopy /E /I /Y build_venv\* build_release\MiAppMarcas\python\

REM Paso 5: Copiar aplicación
echo [5/6] Copiando aplicación...
mkdir build_release\MiAppMarcas\app
xcopy /Y app_refactored.py build_release\MiAppMarcas\app\
xcopy /Y boletines.db build_release\MiAppMarcas\app\
xcopy /Y config.json build_release\MiAppMarcas\app\
xcopy /E /I /Y imagenes build_release\MiAppMarcas\app\imagenes
xcopy /E /I /Y src build_release\MiAppMarcas\app\src

REM Copiar módulos Python
for %%f in (database.py email_sender.py professional_theme.py paths.py config.py auth_manager_simple.py database_extensions.py email_utils.py email_templates.py db_utils.py report_generator.py dashboard_charts.py extractor.py utilidades_reportes.py email_verification_system.py) do (
    xcopy /Y %%f build_release\MiAppMarcas\app\
)

REM Paso 6: Copiar requirements y docs
echo [6/6] Creando documentación...
xcopy /Y requirements.txt build_release\MiAppMarcas\

echo BUILD COMPLETADO EXITOSAMENTE
pause
```

5. **Ejecutar el build**:
```cmd
build_release.bat
```

6. **Crear ZIP para distribución**:
```cmd
cd build_release
"C:\Program Files\7-Zip\7z.exe" a -tzip MiAppMarcas-v1.0.0-windows.zip MiAppMarcas\
```

---

## 📦 Qué Entregar al Cliente

### Estructura del Paquete:
```
MiAppMarcas-v1.0.0-windows.zip
└── MiAppMarcas/
    ├── MiAppMarcas.exe          # Ejecutable principal (~7-10MB)
    ├── LEEME.txt                 # Instrucciones
    ├── VERSION.txt               # Información de versión
    ├── requirements.txt          # Dependencias
    ├── python/                   # Python portable
    │   └── [archivos de Python]
    └── app/                      # Tu aplicación
        ├── app_refactored.py
        ├── boletines.db
        ├── config.json
        ├── imagenes/
        ├── src/
        └── [módulos .py]
```

### Tamaño aproximado:
- **Paquete comprimido**: ~80-150 MB
- **Descomprimido (sin .venv)**: ~200-300 MB
- **Con .venv instalado**: ~1-1.5 GB

---

## 📝 Instrucciones para el Cliente (Windows)

Crea un archivo `INSTRUCCIONES_CLIENTE.txt`:

```text
============================================================
   MiAppMarcas - Sistema de Gestión de Marcas
   Versión 1.0.0
============================================================

INSTALACIÓN:
-----------
1. Descomprimir el archivo MiAppMarcas-v1.0.0-windows.zip
2. Mover la carpeta "MiAppMarcas" donde desees
   (Ej: C:\Programas\MiAppMarcas o tu Escritorio)

PRIMERA EJECUCIÓN:
-----------------
1. Abrir la carpeta MiAppMarcas
2. Hacer doble clic en "MiAppMarcas.exe"
3. ESPERAR 1-2 minutos (instalación automática)
   - Se mostrará una barra de progreso
   - Se abrirá automáticamente el navegador

EJECUCIONES SIGUIENTES:
----------------------
1. Doble clic en "MiAppMarcas.exe"
2. Arranque instantáneo (5-10 segundos)
3. El navegador se abre automáticamente

DATOS Y ARCHIVOS:
----------------
Todos los datos se guardan en:
  MiAppMarcas/app/

- Base de datos: app/boletines.db
- Imágenes: app/imagenes/
- Configuración: app/config.json
- Informes: app/informes/
- Logs: app/logs/

SOLUCIÓN DE PROBLEMAS:
---------------------
1. Si no inicia: Revisar "launcher.log"
2. Si hay errores: Eliminar carpeta ".venv" y reiniciar
3. Antivirus: Agregar MiAppMarcas.exe a excepciones

REQUISITOS:
----------
- Windows 10 o superior (64-bit)
- 2GB de espacio en disco
- Conexión a internet (primera vez)

SOPORTE:
--------
Email: tu-email@ejemplo.com
```

---

## 🔄 Actualizaciones

### Para actualizar la aplicación del cliente:

1. **Crear nueva versión**:
```bash
./build_release.sh
```

2. **Cambiar número de versión**:
Edita `VERSION.txt` en el paquete generado

3. **Distribuir solo los cambios** (actualización ligera):
```bash
# Comprimir solo la carpeta app/
cd build_release/MiAppMarcas
zip -r MiAppMarcas-update-v1.0.1.zip app/
```

4. **Instrucciones al cliente**:
```text
ACTUALIZACIÓN RÁPIDA:
1. Cerrar MiAppMarcas si está ejecutándose
2. Descomprimir MiAppMarcas-update-v1.0.1.zip
3. Reemplazar la carpeta "app" completa
4. Iniciar MiAppMarcas.exe normalmente
```

---

## 🚀 Comandos Rápidos

### Flujo completo (después de modificar código):
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./build_release.sh
cd build_release
tar --exclude='.venv' --exclude='*.log' -czf MiAppMarcas-v1.0.0-macos.tar.gz MiAppMarcas/
```

### Solo reconstruir (sin comprimir):
```bash
cd /Users/martingiacosa/Desktop/Proyectos/Python/Automation/packaging
./build_release.sh
```

### Probar localmente:
```bash
cd build_release/MiAppMarcas
rm -rf .venv launcher.log
./MiAppMarcas
```

---

## ⚠️ Notas Importantes

1. **Versionado**: Actualiza `VERSION.txt` en cada release
2. **Base de datos**: Si cambias el esquema, documenta la migración
3. **Config**: `config.json` contiene credenciales - ¡No subir a Git!
4. **Imágenes**: Incluye todas las imágenes necesarias en `imagenes/`
5. **Testing**: SIEMPRE prueba antes de enviar al cliente
6. **Backup**: El cliente debe hacer backup de `app/boletines.db` regularmente

---

## 📊 Checklist Pre-Distribución

Antes de enviar al cliente, verifica:

- [ ] Todas las funcionalidades probadas
- [ ] Base de datos incluida y funcional
- [ ] Imágenes y assets copiados
- [ ] config.json configurado correctamente
- [ ] requirements.txt actualizado
- [ ] VERSION.txt con número correcto
- [ ] LEEME.txt actualizado
- [ ] Paquete comprimido creado
- [ ] Tamaño del archivo razonable (<200MB comprimido)
- [ ] Probado en máquina limpia (sin .venv preexistente)
