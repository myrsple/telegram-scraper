# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for zocoloco Telegram Scraper.

To build:
    pyinstaller zocoloco.spec

The .app will be created in the dist/ folder.
"""

import os
from pathlib import Path

block_cipher = None

# Get the current directory
base_path = Path(os.getcwd())

# Data files to include
datas = [
    ('assets', 'assets'),
    ('fonts', 'fonts'),
    ('scraper', 'scraper'),
]

# Hidden imports for telethon and customtkinter
hidden_imports = [
    'telethon',
    'telethon.client',
    'telethon.tl',
    'telethon.tl.types',
    'telethon.tl.functions',
    'telethon.errors',
    'dotenv',
    'dotenv.main',
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pyglet',
    'pyglet.font',
    'asyncio',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.font',
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='zocoloco',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='zocoloco',
)

app = BUNDLE(
    coll,
    name='zocoloco.app',
    icon='assets/icon.icns',
    bundle_identifier='com.zocoloco.telegram-scraper',
    info_plist={
        'CFBundleName': 'zocoloco',
        'CFBundleDisplayName': 'zocoloco',
        'CFBundleVersion': '1.0.3',
        'CFBundleShortVersionString': '1.0.3',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
