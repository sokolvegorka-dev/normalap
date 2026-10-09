@echo off
chcp 65001 >nul
set "SRC=%~dp0"
set "DEST=%LOCALAPPDATA%\NormalapPack"
if exist "%DEST%" rmdir /s /q "%DEST%"
mkdir "%DEST%"
robocopy "%SRC%." "%DEST%" /E /NFL /NDL /NJH /NJS /nc /ns /np /XD build dist .flet __pycache__ .git site "assets\bowl\_chrome" "assets\bowl\srcvid" /XF _*.py _*.txt _*.bat
cd /d "%DEST%"
flet pack main.py -y -n NormaLap -i assets\icons\icon.ico --add-data data:data --add-data assets:assets --hidden-import matcher --hidden-import nutrition --hidden-import flet_video --hidden-import five_letters --hidden-import bowl_draw --hidden-import bowl_live --hidden-import weather --product-name НормаЛап --file-description "НормаЛап — подбор корма для питомца" --product-version 1.0.0 --company-name НормаЛап
echo PACK_EXIT=%errorlevel%
