import os
import sys
import subprocess
from pathlib import Path

import pystray
from pystray import MenuItem as Item
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent

APP_SCRIPT = BASE_DIR / "main.py"

ICON_FILE = BASE_DIR / "app_icon.ico"

app_process = None

CREATE_NO_WINDOW = 0x08000000


def get_python_executable():
    """
    Ищет Python из виртуального окружения.
    Лучше использовать pythonw.exe, чтобы не открывалась консоль.
    """
    candidates = [
        BASE_DIR / ".venv" / "Scripts" / "pythonw.exe",
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable).with_name("pythonw.exe"),
        Path(sys.executable),
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return "python"


def create_default_icon():
    """
    Создаёт простую иконку, если app_icon.ico не найден.
    """
    image = Image.new("RGBA", (64, 64), (30, 90, 200, 255))
    draw = ImageDraw.Draw(image)

    draw.ellipse((8, 8, 56, 56), fill=(255, 255, 255, 255))
    draw.text((22, 20), "B", fill=(30, 90, 200, 255))

    return image


def load_icon():
    if ICON_FILE.exists():
        return Image.open(ICON_FILE)

    return create_default_icon()


def is_app_running():
    return app_process is not None and app_process.poll() is None


def start_app(icon=None, item=None):
    """
    Запускает основную программу.
    """
    global app_process

    if is_app_running():
        if icon:
            icon.notify("Приложение уже запущено", "bonscanAI")
        return

    if not APP_SCRIPT.exists():
        if icon:
            icon.notify(f"Не найден файл: {APP_SCRIPT}", "Ошибка")
        return

    creation_flags = CREATE_NO_WINDOW if os.name == "nt" else 0

    app_process = subprocess.Popen(
        [get_python_executable(), str(APP_SCRIPT)],
        cwd=str(BASE_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )

    if icon:
        icon.notify("Приложение запущено", "bonscanAI")


def stop_app(icon=None, item=None):
    """
    Останавливает запущенную программу.
    """
    global app_process

    if is_app_running():
        app_process.terminate()

        try:
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_process.kill()

        app_process = None

        if icon:
            icon.notify("Приложение остановлено", "bonscanAI")


def exit_tray(icon, item):
    """
    Закрывает трей-приложение.
    """
    stop_app()
    icon.stop()


def main():
    menu = pystray.Menu(
        Item("Запустить bonscanAI", start_app, default=True),
        Item("Остановить bonscanAI", stop_app),
        Item("Выход", exit_tray),
    )

    tray_icon = pystray.Icon(
        name="bonscanAI",
        icon=load_icon(),
        title="bonscanAI",
        menu=menu,
    )

    tray_icon.run()


if __name__ == "__main__":
    main()