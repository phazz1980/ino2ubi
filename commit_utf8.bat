@echo off
chcp 65001 >nul
REM Для коммитов с русским текстом: создайте файл msg.txt в UTF-8 и запустите:
REM   commit_utf8.bat
REM Файл msg.txt должен содержать сообщение коммита (кодировка UTF-8).
"C:\Program Files\Git\bin\git.exe" add -A
if exist msg.txt (
    "C:\Program Files\Git\bin\git.exe" commit -F msg.txt
) else (
    echo Создайте msg.txt с текстом коммита (UTF-8) и запустите снова.
    pause
    exit /b 1
)
"C:\Program Files\Git\bin\git.exe" push
