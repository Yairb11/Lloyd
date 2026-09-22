import ctypes
import sys
from ctypes import wintypes

from app.config import WIN_DWM_IMMERSIVE_DARK_MODE_ATTRIBUTE


def enable_dark_titlebar(window_handle: int) -> None:
    if sys.platform != "win32":
        return
    value = ctypes.c_int(1)
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(window_handle),
            WIN_DWM_IMMERSIVE_DARK_MODE_ATTRIBUTE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except (AttributeError, OSError):
        pass
