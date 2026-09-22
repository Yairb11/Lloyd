from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QGuiApplication, QScreen

from app.config import (
    MONITOR_NO_INDEX, MONITOR_ORIENTATION_LANDSCAPE, MONITOR_ORIENTATION_PORTRAIT,
    WINDOW_DEFAULT_SCREEN_RATIO, WINDOW_MIN_HEIGHT, WINDOW_MIN_VISIBLE_HEIGHT,
    WINDOW_MIN_VISIBLE_WIDTH, WINDOW_MIN_WIDTH,
)


class Monitor:
    def __init__(self, name: str, x: int, y: int, width: int, height: int, is_primary: bool, available: QRect) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_primary = is_primary
        self.available = available
        self.geometry = QRect(x, y, width, height)


def _to_monitor(screen: QScreen, primary: QScreen | None) -> Monitor:
    geometry = screen.geometry()
    return Monitor(
        name=screen.name(),
        x=geometry.x(),
        y=geometry.y(),
        width=geometry.width(),
        height=geometry.height(),
        is_primary=screen is primary,
        available=screen.availableGeometry(),
    )


def get_screens() -> list[Monitor]:
    primary = QGuiApplication.primaryScreen()
    return [_to_monitor(screen, primary) for screen in QGuiApplication.screens()]


def screen_count() -> int:
    return len(QGuiApplication.screens())


def layout_signature(screens: list[Monitor]) -> str:
    return "".join(
        MONITOR_ORIENTATION_LANDSCAPE if monitor.width >= monitor.height else MONITOR_ORIENTATION_PORTRAIT
        for monitor in screens
    )


def primary_screen(screens: list[Monitor]) -> Monitor | None:
    for monitor in screens:
        if monitor.is_primary:
            return monitor
    return screens[0] if screens else None


def find_screen_index(screens: list[Monitor], point: QPoint) -> int:
    for index, monitor in enumerate(screens):
        on_screen_x = monitor.x <= point.x() < monitor.x + monitor.width
        on_screen_y = monitor.y <= point.y() < monitor.y + monitor.height
        if on_screen_x and on_screen_y:
            return index
    return MONITOR_NO_INDEX


def find_screen(screens: list[Monitor], name: str, geometry: QRect | None) -> Monitor | None:
    named = [monitor for monitor in screens if monitor.name == name]
    if geometry is not None:
        for monitor in named:
            if monitor.geometry == geometry:
                return monitor
        for monitor in screens:
            if monitor.geometry == geometry:
                return monitor
    return named[0] if named else None


def bounding_box(screens: list[Monitor]) -> tuple[int, int, int, int]:
    min_x = min(monitor.x for monitor in screens)
    min_y = min(monitor.y for monitor in screens)
    max_x = max(monitor.x + monitor.width for monitor in screens)
    max_y = max(monitor.y + monitor.height for monitor in screens)
    return min_x, min_y, max_x, max_y


def total_size(screens: list[Monitor]) -> tuple[int, int]:
    min_x, min_y, max_x, max_y = bounding_box(screens)
    return max_x - min_x, max_y - min_y


def centered_rect(monitor: Monitor) -> QRect:
    available = monitor.available
    width = min(max(WINDOW_MIN_WIDTH, int(available.width() * WINDOW_DEFAULT_SCREEN_RATIO)), available.width())
    height = min(max(WINDOW_MIN_HEIGHT, int(available.height() * WINDOW_DEFAULT_SCREEN_RATIO)), available.height())
    rect = QRect(0, 0, width, height)
    rect.moveCenter(available.center())
    return rect


def fit(rect: QRect, monitor: Monitor) -> QRect:
    available = monitor.available
    fitted = QRect(rect)
    fitted.setWidth(min(max(fitted.width(), WINDOW_MIN_WIDTH), available.width()))
    fitted.setHeight(min(max(fitted.height(), WINDOW_MIN_HEIGHT), available.height()))
    fitted.moveLeft(min(max(fitted.left(), available.left()), available.right() - fitted.width() + 1))
    fitted.moveTop(min(max(fitted.top(), available.top()), available.bottom() - fitted.height() + 1))
    return fitted


def is_reachable(frame: QRect, screens: list[Monitor]) -> bool:
    band = QRect(frame.left(), frame.top(), frame.width(), min(WINDOW_MIN_VISIBLE_HEIGHT, frame.height()))
    required_width = min(WINDOW_MIN_VISIBLE_WIDTH, band.width())
    for monitor in screens:
        overlap = monitor.available.intersected(band)
        if not overlap.isEmpty() and overlap.width() >= required_width:
            return True
    return False