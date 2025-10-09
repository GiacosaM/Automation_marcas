# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec para MiAppMarcas Simple Launcher
Este spec crea un ejecutable pequeño que:
- Solo contiene el código del launcher
- NO incluye Python/Streamlit (esos van en carpetas separadas)
- Tamaño final: ~5-10MB
"""

block_cipher = None

a = Analysis(
    ['simple_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir todo lo pesado, solo queremos el launcher
        'streamlit',
        'pandas',
        'numpy',
        'altair',
        'plotly',
        'matplotlib',
        'PIL',
        'tornado',
        'jinja2',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MiAppMarcas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Mantener consola para ver mensajes
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
