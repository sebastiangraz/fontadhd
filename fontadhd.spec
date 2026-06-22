# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the fontadhd desktop GUI.
#
#   pip install -e ".[build]"
#   pyinstaller fontadhd.spec
#
# Produces a windowed (no-console) app:
#   - Windows: dist/fontadhd/fontadhd.exe   (needs the Edge WebView2 runtime,
#              present on Windows 11 by default)
#   - macOS:   dist/fontadhd.app
# Builds are per-OS; run this on the OS you are targeting (no cross-compile).

import sys

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=[],
    # Bundle fontadhd.py (imported by gui) and the web assets next to the app.
    datas=[('web', 'web'), ('fontadhd.py', '.')],
    hiddenimports=['webview'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fontadhd',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='fontadhd',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='fontadhd.app',
        bundle_identifier='se.live.graz.fontadhd',
    )
