# -*- mode: python ; coding: utf-8 -*-
"""
Especificación ULTRA MINIMALISTA para PyInstaller
Diseñada para Python 3.13 con máxima simplicidad
Sin hooks de distutils ni complicaciones
+ Incluye metadatos de paquetes para Streamlit
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None

# Punto de entrada
a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    # Datos mínimos esenciales + METADATOS DE PAQUETES
    datas=[
        ('../app_refactored.py', '.'),
        ('../boletines.db', '.'),
        ('../config.json', '.'),
        ('../imagenes', 'imagenes'),
    ] + copy_metadata('streamlit') + copy_metadata('altair') + copy_metadata('pandas') + copy_metadata('plotly'),
    # Imports ocultos MÍNIMOS - solo los estrictamente necesarios
    hiddenimports=[
        # Streamlit core
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.web.bootstrap',
        
        # Tornado (servidor de Streamlit)
        'tornado',
        'tornado.web',
        'tornado.ioloop',
        
        # Básicos
        'sqlite3',
        'appdirs',
        'bcrypt',
        
        # Data handling básico
        'pandas',
        'numpy',
        
        # Visualización básica
        'altair',
        'plotly',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # CRÍTICO: Excluir distutils Y desactivar su hook
    excludes=[
        'distutils', 
        '_distutils_hack',
        'setuptools.distutils',
        # Otros módulos innecesarios
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'test',
        'unittest',
    ],
    # NUEVO: Desactivar hooks problemáticos
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MiAppMarcas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Mostrar consola para debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MiAppMarcas',
)
