@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Собираю Android-приложение НормаЛап...
echo.
echo Нужен интернет. Если Flutter и Android SDK ещё не стоят, Flet скачает их сам.
echo Это долго и занимает несколько гигабайт, один раз.
echo.
set "DEST=%LOCALAPPDATA%\NormalapBuild"
if exist "%DEST%" rmdir /s /q "%DEST%"
mkdir "%DEST%"
robocopy "%~dp0." "%DEST%" /E /NFL /NDL /NJH /NJS /nc /ns /np ^
  /XD build .flet __pycache__ dist .git site "assets\bowl\_chrome" "assets\bowl\srcvid"
if errorlevel 8 (
  echo Не удалось подготовить папку сборки.
  pause
  exit /b 1
)
pushd "%DEST%"
flet build apk --yes --product "НормаЛап"
set ERR=%errorlevel%
popd
if not "%ERR%"=="0" (
  echo.
  echo Сборка не удалась. Частая причина — нет места на диске или оборвался интернет.
  pause
  exit /b 1
)
echo.
echo Готово. Файл APK:
echo %DEST%\build\apk
echo.
echo Скопируйте APK на телефон Android и откройте его.
echo Если система спросит, разрешите установку из этого источника.
echo iPhone пока не собирается: для него нужен компьютер Apple.
pause
