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


