# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller arduino_to_flprog_GLOBAL_COMPLETE.spec
# Иконка exe: положите icon.ico в ту же папку, что и этот .spec файл, перед сборкой.
# Иконка окна: если icon.ico нет, в exe подставляется стандартная иконка Qt.

import os
import sys

block_cipher = None

_spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
sys.path.insert(0, _spec_dir)
import constants
_exe_name = 'ino2ubi_v{}'.format(constants.VERSION)
_icon_path = os.path.join(_spec_dir, 'icon.ico')
_readme_path = os.path.join(_spec_dir, 'README.md')
_has_icon = os.path.isfile(_icon_path)

_datas = []
if _has_icon:
    _datas.append((_icon_path, '.'))
if os.path.isfile(_readme_path):
    _datas.append((_readme_path, '.'))

a = Analysis(
    ['arduino_to_flprog_GLOBAL_COMPLETE.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'constants', 'parser', 'generator', 'gui'
    ],
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
    console=False,  # Без консоли (GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
