# -*- coding: utf-8 -*-
"""Ставит ярлык НормаЛап на рабочий стол и в меню Пуск — как обычное приложение."""
from pathlib import Path
import os
import sys

APP = Path(__file__).resolve().parent
BAT = APP / "Запустить НормаЛап.bat"
ICON = APP / "assets" / "icons" / "icon.ico"
EXE_CANDIDATES = [
    APP / "dist" / "Normalap" / "Normalap.exe",
    APP / "dist" / "Normalap.exe",
    APP / "dist" / "НормаЛап" / "НормаЛап.exe",
    APP / "dist" / "НормаЛап.exe",
]


def target():
    for p in EXE_CANDIDATES:
        if p.exists():
            return p
    return BAT


def make_shortcut(path: Path, target_path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    ps = rf"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{str(path).replace("'", "''")}')
$s.TargetPath = '{str(target_path).replace("'", "''")}'
$s.WorkingDirectory = '{str(target_path.parent).replace("'", "''")}'
$s.WindowStyle = 1
$s.Description = 'НормаЛап — подбор корма для питомца'
$icon = '{str(ICON).replace("'", "''")}'
if (Test-Path $icon) {{ $s.IconLocation = $icon }}
$s.Save()
"""
    import subprocess
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main():
    t = target()
    desktop = Path(os.path.join(os.environ.get("USERPROFILE", str(Path.home())), "Desktop"))
    start = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    make_shortcut(desktop / "НормаЛап.lnk", t)
    make_shortcut(start / "НормаЛап.lnk", t)
    print("Ярлыки созданы:")
    print(" ", desktop / "НормаЛап.lnk")
    print(" ", start / "НормаЛап.lnk")
    print("Запуск:", t)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Не удалось создать ярлык:", e)
        sys.exit(1)
