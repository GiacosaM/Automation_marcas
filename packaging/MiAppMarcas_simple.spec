# -*- mode: python ; coding: utf-8 -*-
"""
MiAppMarcas - Configuración Simplificada de PyInstaller
=======================================================
Versión simplificada para mejor compatibilidad con Python 3.13+

Uso:
    pyinstaller MiAppMarcas_simple.spec

Autor: Sistema de Gestión de Marcas
Versión: 1.0.1
"""

import sys
import os
from pathlib import Path

# Obtener directorio base del proyecto
block_cipher = None
project_root = os.path.abspath('..')

# ============================================================================
# ARCHIVOS Y DIRECTORIOS A INCLUIR
# ============================================================================

# Archivos de datos de la aplicación
app_datas = [
    (os.path.join(project_root, 'boletines.db'), '.'),
    (os.path.join(project_root, 'config.json'), '.'),
    (os.path.join(project_root, 'app_refactored.py'), '.'),
]

# Directorios completos a incluir
if os.path.exists(os.path.join(project_root, 'src')):
    app_datas.append((os.path.join(project_root, 'src'), 'src'))

if os.path.exists(os.path.join(project_root, 'imagenes')):
    app_datas.append((os.path.join(project_root, 'imagenes'), 'imagenes'))

if os.path.exists(os.path.join(project_root, '.streamlit')):
    app_datas.append((os.path.join(project_root, '.streamlit'), '.streamlit'))

# ============================================================================
# MÓDULOS OCULTOS (HIDDEN IMPORTS) - Simplificado
# ============================================================================

hidden_imports = [
    # Streamlit esenciales
    'streamlit',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    'streamlit.runtime.scriptrunner.script_runner',
    'streamlit.web',
    'streamlit.web.cli',
    
    # Procesamiento de datos
    'pandas',
    'numpy',
    
    # Visualización
    'altair',
    'plotly',
    'matplotlib',
    
    # Imágenes
    'PIL',
    'PIL.Image',
    
    # Base de datos
    'sqlite3',
    
    # Email
    'smtplib',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    
    # Autenticación
    'bcrypt',
    
    # Gestión de rutas
    'appdirs',
    
    # Utilidades
    'json',
    'datetime',
    'logging',
    'threading',
    'tempfile',
    
    # Módulos de la aplicación
    'auth_manager_simple',
    'database',
    'email_sender',
]

# ============================================================================
# ANÁLISIS DE LA APLICACIÓN
# ============================================================================

a = Analysis(
    ['launcher.py'],
    pathex=[project_root],
    binaries=[],
    datas=app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test',
        'tests',
        'pytest',
        'setuptools',
        'pip',
        'wheel',
        'distutils',  # Excluir explícitamente para Python 3.13+
        '_distutils_hack',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# EMPAQUETADO
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================================
# CONFIGURACIÓN DEL EJECUTABLE
# ============================================================================

# Determinar configuración según el sistema operativo
if sys.platform == 'darwin':  # macOS
    exe_name = 'MiAppMarcas'
    console = False
elif sys.platform == 'win32':  # Windows
    exe_name = 'MiAppMarcas.exe'
    console = True
else:  # Linux
    exe_name = 'MiAppMarcas'
    console = True

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ============================================================================
# COLECCIÓN FINAL
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MiAppMarcas'
)

# ============================================================================
# BUNDLE PARA macOS (.app)
# ============================================================================

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='MiAppMarcas.app',
        icon=None,
        bundle_identifier='com.estudiocontable.miappmarcas',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleName': 'MiAppMarcas',
            'CFBundleDisplayName': 'Sistema de Gestión de Marcas',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025 Estudio Contable',
        },
    )
