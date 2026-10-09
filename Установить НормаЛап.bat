@echo off
chcp 65001 >nul
cd /d "%~dp0"
python установить_ярлык.py
if errorlevel 1 pause
echo.
echo Готово. Ищите «НормаЛап» на рабочем столе и в меню Пуск.
pause
