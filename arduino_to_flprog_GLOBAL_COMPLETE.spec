# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller arduino_to_flprog_GLOBAL_COMPLETE.spec
# exe = launcher, остальное (gui, parser, generator, constants) — скрипты рядом с exe.
# Иконка: icon.ico в папке .spec перед сборкой.

import os
import sys

block_cipher = None

_spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
_exe_name = 'ino2ubi'
_icon_path = os.path.join(_spec_dir, 'icon.ico')
_readme_path = os.path.join(_spec_dir, 'README.md')
_has_icon = os.path.isfile(_icon_path)

_datas = []
if _has_icon:
    _datas.append((_icon_path, '.'))
if os.path.isfile(_readme_path):
    _datas.append((_readme_path, '.'))

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'json', 'urllib.request', 'urllib.error', 'html', 'uuid', 'argparse',
        're', 'traceback', 'ssl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gui', 'generator', 'parser', 'constants'],
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
    name=_exe_name,
    icon=_icon_path if _has_icon else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
