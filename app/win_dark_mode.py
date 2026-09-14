import ctypes
import sys
from ctypes import wintypes

_DWMWA_USE_IMMERSIVE_DARK_MODE: int = 20


def enable_dark_titlebar(window_handle: int) -> None:
    if sys.platform != "win32":
        return
    value = ctypes.c_int(1)
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(window_handle),
            _DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except (AttributeError, OSError):
        pass