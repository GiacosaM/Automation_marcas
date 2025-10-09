# -*- mode: python ; coding: utf-8 -*-
"""
MiAppMarcas - Configuración de PyInstaller
==========================================
Archivo de especificación para crear ejecutables standalone
de la aplicación de Gestión de Marcas.

Uso:
    pyinstaller MiAppMarcas.spec

Autor: Sistema de Gestión de Marcas
Versión: 1.0.0
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Obtener directorio base del proyecto
block_cipher = None
project_root = os.path.abspath('..')

# ============================================================================
# CONFIGURACIÓN DE RECOPILACIÓN DE DATOS
# ============================================================================

# Recopilar datos de Streamlit
streamlit_datas = collect_data_files('streamlit', include_py_files=True)
streamlit_hidden = collect_submodules('streamlit')

# Recopilar datos de otros paquetes importantes
altair_datas = collect_data_files('altair')
plotly_datas = collect_data_files('plotly')
pandas_datas = collect_data_files('pandas')
PIL_datas = collect_data_files('PIL')

# Recopilar todos los datos de paquetes problemáticos
validators_all = collect_all('validators')
watchdog_all = collect_all('watchdog')
tornado_all = collect_all('tornado')

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
app_tree_datas = []

# Agregar directorio src si existe
src_dir = os.path.join(project_root, 'src')
if os.path.exists(src_dir):
    app_tree_datas.append((src_dir, 'src'))

# Agregar directorio de imágenes si existe
img_dir = os.path.join(project_root, 'imagenes')
if os.path.exists(img_dir):
    app_tree_datas.append((img_dir, 'imagenes'))

# Agregar directorio .streamlit si existe
streamlit_dir = os.path.join(project_root, '.streamlit')
if os.path.exists(streamlit_dir):
    app_tree_datas.append((streamlit_dir, '.streamlit'))

# Agregar directorio Documentos si existe
docs_dir = os.path.join(project_root, 'Documentos')
if os.path.exists(docs_dir):
    app_tree_datas.append((docs_dir, 'Documentos'))

# Combinar todos los datos
all_datas = (
    streamlit_datas +
    altair_datas +
    plotly_datas +
    pandas_datas +
    PIL_datas +
    validators_all[0] +
    watchdog_all[0] +
    tornado_all[0] +
    app_datas +
    app_tree_datas
)

# ============================================================================
# MÓDULOS OCULTOS (HIDDEN IMPORTS)
# ============================================================================

hidden_imports = [
    # Streamlit core
    'streamlit',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    'streamlit.web',
    'streamlit.web.cli',
    
    # Componentes de Streamlit
    'streamlit.components.v1',
    'streamlit.elements',
    'streamlit.proto',
    
    # Backend de Streamlit
    'click',
    'click.core',
    'click.decorators',
    'tornado',
    'tornado.web',
    'tornado.websocket',
    'tornado.ioloop',
    
    # Watchdog (usado por Streamlit)
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    
    # Validación
    'validators',
    'validators.domain',
    'validators.email',
    'validators.url',
    
    # Procesamiento de datos
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    
    # Visualización
    'altair',
    'altair.vegalite',
    'altair.vegalite.v5',
    'plotly',
    'plotly.graph_objs',
    'matplotlib',
    'matplotlib.pyplot',
    
    # Imágenes
    'PIL',
    'PIL.Image',
    'PIL._imaging',
    
    # Base de datos
    'sqlite3',
    'sqlalchemy',
    
    # Email
    'smtplib',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.application',
    
    # Autenticación
    'bcrypt',
    'cryptography',
    
    # Gestión de rutas
    'appdirs',
    'pathlib',
    
    # Utilidades
    'json',
    'csv',
    'datetime',
    'logging',
    'threading',
    'queue',
    'tempfile',
    'shutil',
    
    # Requests y HTTP
    'requests',
    'urllib',
    'urllib.request',
    'http',
    'http.server',
    
    # Excel y documentos
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'fpdf',
    'reportlab',
    
    # Módulos de la aplicación
    'auth_manager_simple',
    'database',
    'database_extensions',
    'db_utils',
    'email_sender',
    'email_templates',
    'email_utils',
    'report_generator',
    'dashboard_charts',
    'professional_theme',
    'paths',
    'config',
] + streamlit_hidden + validators_all[1] + watchdog_all[1] + tornado_all[1]

# ============================================================================
# BINARIOS ADICIONALES
# ============================================================================

binaries = []

# ============================================================================
# ANÁLISIS DE LA APLICACIÓN
# ============================================================================

a = Analysis(
    ['launcher.py'],  # Buscar en el directorio actual (packaging/)
    pathex=[project_root],
    binaries=binaries,
    datas=all_datas,
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
        'distutils',
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
    console = False  # Sin consola en macOS
elif sys.platform == 'win32':  # Windows
    exe_name = 'MiAppMarcas.exe'
    console = True  # Con consola para ver logs en Windows
else:  # Linux
    exe_name = 'MiAppMarcas'
    console = True  # Con consola en Linux

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Comprimir con UPX si está disponible
    console=console,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'imagenes', 'icon.ico') if os.path.exists(os.path.join(project_root, 'imagenes', 'icon.ico')) else None,
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
        icon=os.path.join(project_root, 'imagenes', 'icon.icns') if os.path.exists(os.path.join(project_root, 'imagenes', 'icon.icns')) else None,
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
