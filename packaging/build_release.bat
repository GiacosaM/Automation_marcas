@echo off
REM ============================================================================
REM Script de Build para Windows - MiAppMarcas
REM ============================================================================

SETLOCAL EnableDelayedExpansion

REM Colores (no disponibles en CMD básico, solo texto)
echo ============================================================
echo   Building MiAppMarcas for Windows
echo ============================================================

REM Determinar la ruta del proyecto
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo.
echo [1/6] Limpiando builds anteriores...
if exist packaging\build_release rmdir /s /q packaging\build_release
if exist packaging\dist rmdir /s /q packaging\dist
if exist packaging\build rmdir /s /q packaging\build
mkdir packaging\build_release\MiAppMarcas

REM ============================================================================
REM Paso 2: Compilar el launcher con PyInstaller
REM ============================================================================

echo.
echo [2/6] Compilando launcher con PyInstaller...

REM Activar entorno virtual si existe
if exist build_venv\Scripts\activate.bat (
    call build_venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: build_venv not found, using system Python
)

cd packaging
pyinstaller --clean --noconfirm simple_launcher.spec

if errorlevel 1 (
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)

cd ..
echo Launcher compiled successfully

REM ============================================================================
REM Paso 3: Crear Python portable (usar Python del sistema en Windows)
REM ============================================================================

echo.
echo [3/6] Creando Python portable...

set PYTHON_DIR=%PROJECT_ROOT%\packaging\build_release\MiAppMarcas\python
mkdir "%PYTHON_DIR%"

REM En Windows, copiamos el Python del build_venv
if exist build_venv (
    xcopy /E /I /Q /Y build_venv\* "%PYTHON_DIR%\"
    echo Python portable created
) else (
    echo ERROR: build_venv not found
    pause
    exit /b 1
)

REM ============================================================================
REM Paso 4: Copiar archivos de la aplicación
REM ============================================================================

echo.
echo [4/6] Copiando archivos de la aplicacion...

set FINAL_PACKAGE=%PROJECT_ROOT%\packaging\build_release\MiAppMarcas
set APP_DIR=%FINAL_PACKAGE%\app

REM Crear directorio app
mkdir "%APP_DIR%"

REM Copiar launcher
copy /Y packaging\dist\MiAppMarcas.exe "%FINAL_PACKAGE%\"
echo Launcher copied

REM Copiar archivo principal
copy /Y app_refactored.py "%APP_DIR%\"
echo app_refactored.py copied

REM Copiar base de datos (buscar en múltiples ubicaciones)
if exist "%USERPROFILE%\Desktop\MiAppMarcas\boletines.db" (
    copy /Y "%USERPROFILE%\Desktop\MiAppMarcas\boletines.db" "%APP_DIR%\"
    echo boletines.db copied from Desktop
) else if exist boletines.db (
    copy /Y boletines.db "%APP_DIR%\"
    echo boletines.db copied from project
) else (
    echo Warning: boletines.db not found, will create new one
)

REM Copiar config
if exist config.json (
    copy /Y config.json "%APP_DIR%\"
    echo config.json copied
)

REM Copiar imágenes
if exist imagenes (
    xcopy /E /I /Q /Y imagenes "%APP_DIR%\imagenes"
    echo imagenes/ folder copied
)

REM Copiar carpeta src/ completa
if exist src (
    xcopy /E /I /Q /Y src "%APP_DIR%\src"
    echo src/ folder copied
)

REM Copiar módulos necesarios
echo Copying Python modules...
for %%M in (database.py email_sender.py professional_theme.py paths.py config.py auth_manager_simple.py database_extensions.py email_utils.py email_templates.py db_utils.py report_generator.py dashboard_charts.py extractor.py utilidades_reportes.py email_verification_system.py) do (
    if exist %%M (
        copy /Y %%M "%APP_DIR%\"
        echo %%M copied
    )
)

REM ============================================================================
REM Paso 5: Copiar requirements.txt
REM ============================================================================

echo.
echo [5/6] Copiando requirements.txt...

if exist requirements.txt (
    copy /Y requirements.txt "%FINAL_PACKAGE%\"
    echo requirements.txt copied from project
) else (
    echo ERROR: requirements.txt not found
)

REM ============================================================================
REM Paso 6: Crear documentación
REM ============================================================================

echo.
echo [6/6] Creando documentacion...

REM Crear LEEME.txt
(
echo ============================================================
echo    MiAppMarcas - Sistema de Gestion de Marcas
echo ============================================================
echo.
echo INSTALACION:
echo -----------
echo 1. Descomprimir este archivo donde desees
echo 2. No requiere instalacion adicional
echo.
echo PRIMERA EJECUCION:
echo -----------------
echo 1. Hacer doble clic en MiAppMarcas.exe
echo 2. ESPERAR 1-2 minutos ^(instalacion automatica^)
echo 3. El navegador se abrira automaticamente
echo.
echo EJECUCIONES SIGUIENTES:
echo ----------------------
echo 1. Doble clic en MiAppMarcas.exe
echo 2. Arranque instantaneo ^(5-10 segundos^)
echo.
echo DATOS:
echo ------
echo Todos los datos se guardan en la carpeta app/
echo - Base de datos: app/boletines.db
echo - Imagenes: app/imagenes/
echo - Configuracion: app/config.json
echo - Informes: app/informes/
echo.
echo SOLUCION DE PROBLEMAS:
echo ---------------------
echo 1. Si no inicia: Revisar launcher.log
echo 2. Si hay errores: Eliminar carpeta .venv y reiniciar
echo.
echo ============================================================
) > "%FINAL_PACKAGE%\LEEME.txt"

echo LEEME.txt created

REM Crear VERSION.txt
(
echo MiAppMarcas v1.0.0
echo Build date: %DATE% %TIME%
echo Platform: Windows
) > "%FINAL_PACKAGE%\VERSION.txt"

echo VERSION.txt created

REM ============================================================================
REM Build completado
REM ============================================================================

echo.
echo ============================================================
echo   BUILD COMPLETADO EXITOSAMENTE
echo ============================================================
echo.
echo Paquete generado en:
echo %FINAL_PACKAGE%
echo.
echo Siguiente paso: Probar el ejecutable
echo   cd packaging\build_release\MiAppMarcas
echo   MiAppMarcas.exe
echo.
echo Para distribuir:
echo   Comprimir la carpeta MiAppMarcas en un ZIP
echo.

pause
