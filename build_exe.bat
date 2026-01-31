@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>nul
echo Установка PyInstaller...
py -m pip install pyinstaller
if errorlevel 1 python -m pip install pyinstaller
if errorlevel 1 (
    echo Ошибка: Python не найден. Запустите из командной строки или установите Python.
    pause
    exit /b 1
)
echo.
echo Сборка exe (launcher)...
py -m PyInstaller arduino_to_flprog_GLOBAL_COMPLETE.spec --noconfirm --distpath .
if errorlevel 1 (
    python -m PyInstaller arduino_to_flprog_GLOBAL_COMPLETE.spec --noconfirm --distpath .
)
if errorlevel 1 (
    echo Ошибка сборки.
    pause
    exit /b 1
)
echo.
echo Готово. ino2ubi.exe в корне проекта.
pause
