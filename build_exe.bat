@echo off
chcp 65001 >nul
echo Установка PyInstaller...
py -m pip install pyinstaller
if errorlevel 1 (
    python -m pip install pyinstaller
)
echo.
echo Сборка exe...
py -m PyInstaller arduino_to_flprog_GLOBAL_COMPLETE.spec --noconfirm
if errorlevel 1 (
    python -m PyInstaller arduino_to_flprog_GLOBAL_COMPLETE.spec --noconfirm
)
echo.
echo Готово. exe: dist\ArduinoToFLProg.exe
pause
