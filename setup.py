"""
Setup script for creating a macOS .app bundle.

To build:
    pip install py2app
    python setup.py py2app

The .app will be created in the dist/ folder.
"""

from setuptools import setup
import os

APP = ['app.py']

# Include fonts, images, and other resources
DATA_FILES = [
    # Font files
    ('fonts', [
        'fonts/SpaceGrotesk-Bold.ttf',
        'fonts/SpaceGrotesk-Light.ttf',
        'fonts/SpaceGrotesk-Medium.ttf',
        'fonts/SpaceGrotesk-Regular.ttf',
        'fonts/SpaceGrotesk-SemiBold.ttf',
    ]),
    # Image assets
    ('assets', [
        'assets/zoco.png',
        'assets/pink.png',
        'assets/blue.png',
        'assets/bg.png',
        'assets/qr.png',
        'assets/zoco-young.gif',
        'assets/zoco-gh.png',
        'assets/x-logo.png',
        'assets/github-icon.svg',
        'assets/Globe.png',
    ]),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'zocoloco',
        'CFBundleDisplayName': 'zocoloco',
        'CFBundleIdentifier': 'com.zocoloco.telegram-scraper',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
    'packages': ['telethon', 'customtkinter', 'scraper', 'pyglet'],
    'includes': ['tkinter', 'asyncio', 'PIL', 'ctypes'],
    'excludes': ['PyInstaller', 'PyQt6'],
    'resources': ['fonts', 'assets'],
}

setup(
    app=APP,
    name='zocoloco',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
