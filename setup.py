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
    # Image assets (logo and gradients)
    ('', [
        'zoco.png',
        'pink.png',
        'blue.png',
    ]),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add path to .icns file if you have one
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
    'resources': ['fonts', 'zoco.png', 'pink.png', 'blue.png'],
}

setup(
    app=APP,
    name='zocoloco',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
