@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Собираю Windows-приложение НормаЛап...
flet pack main.py -y -n Normalap -i assets\icons\icon.ico --add-data data:data --add-data assets:assets --hidden-import matcher --hidden-import nutrition --hidden-import flet_video --product-name НормаЛап --file-description "НормаЛап — подбор корма для питомца" --product-version 1.0.0 --company-name НормаЛап
if errorlevel 1 (
  echo Сборка не удалась.
  pause
  exit /b 1
)
python установить_ярлык.py
echo.
echo Готово. Ярлык «НормаЛап» на рабочем столе запускает установленное приложение.
pause
