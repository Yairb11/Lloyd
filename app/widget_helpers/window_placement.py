from PyQt6.QtCore import QByteArray, QObject, QRect, QSettings, Qt, QTimer
from PyQt6.QtWidgets import QMainWindow

from app.config import (
    APP_NAME, MONITOR_NO_INDEX, ORG_NAME,
    SETTINGS_GEOMETRY_LEAF, SETTINGS_NORMAL_RECT_LEAF, SETTINGS_SCREEN_NAME_LEAF,
    SETTINGS_SCREEN_RECT_LEAF, SETTINGS_WINDOW_GROUP, SETTINGS_WINDOW_STATE_LEAF,
    WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_RECT_FIELD_COUNT,
    WINDOW_RECT_SEPARATOR, WINDOW_SAVE_DEBOUNCE_MS, WINDOW_STATES,
    WINDOW_STATE_FULLSCREEN, WINDOW_STATE_MAXIMIZED, WINDOW_STATE_NORMAL,
)
from app.widget_helpers import monitors
from app.widget_helpers.monitors import Monitor


class WindowPlacement:
    def __init__(self, geometry: QByteArray | None, normal_rect: QRect | None, screen_name: str, screen_rect: QRect | None, state: str) -> None:
        self.geometry = geometry
        self.normal_rect = normal_rect
        self.screen_name = screen_name
        self.screen_rect = screen_rect
        self.state = state


def _key(signature: str, leaf: str) -> str:
    return f"{SETTINGS_WINDOW_GROUP}/{signature}/{leaf}"


def _rect_to_text(rect: QRect | None) -> str:
    if rect is None or rect.isEmpty():
        return ""
    values = (rect.x(), rect.y(), rect.width(), rect.height())
    return WINDOW_RECT_SEPARATOR.join(str(value) for value in values)


def _text_to_rect(value: object) -> QRect | None:
    if not isinstance(value, str):
        return None
    parts = value.split(WINDOW_RECT_SEPARATOR)
    if len(parts) != WINDOW_RECT_FIELD_COUNT:
        return None
    try:
        x, y, width, height = (int(part) for part in parts)
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return QRect(x, y, width, height)


class WindowPlacementManager(QObject):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._restoring = False
        self._target: Monitor | None = None
        self._target_state = WINDOW_STATE_NORMAL

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(WINDOW_SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self.save_now)

    def restore(self) -> None:
        self._restoring = True
        try:
            screens = monitors.get_screens()
            if not screens:
                self._window.resize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
                return

            placement = self._load(monitors.layout_signature(screens))
            monitor = self._resolve_monitor(screens, placement)
            if monitor is None:
                return

            self._target = monitor
            self._target_state = placement.state
            self._apply_rect(placement, monitor, screens)
            self._apply_state(placement.state)
        finally:
            self._restoring = False

    def _resolve_monitor(self, screens: list[Monitor], placement: WindowPlacement) -> Monitor | None:
        found = monitors.find_screen(screens, placement.screen_name, placement.screen_rect)
        if found is not None:
            return found
        if placement.normal_rect is not None:
            index = monitors.find_screen_index(screens, placement.normal_rect.center())
            if index != MONITOR_NO_INDEX:
                return screens[index]
        return monitors.primary_screen(screens)

    def _apply_rect(self, placement: WindowPlacement, monitor: Monitor, screens: list[Monitor]) -> None:
        window = self._window

        restored = False
        if placement.geometry is not None:
            restored = window.restoreGeometry(placement.geometry)

        window.setWindowState(Qt.WindowState.WindowNoState)

        if not restored or window.geometry().isEmpty():
            rect = placement.normal_rect or monitors.centered_rect(monitor)
            window.setGeometry(monitors.fit(rect, monitor))

        frame = window.frameGeometry()
        if not monitor.available.intersects(frame) or not monitors.is_reachable(frame, screens):
            window.setGeometry(monitors.fit(window.geometry(), monitor))

    def _apply_state(self, state: str) -> None:
        if state == WINDOW_STATE_FULLSCREEN:
            self._window.setWindowState(Qt.WindowState.WindowFullScreen)
        elif state == WINDOW_STATE_MAXIMIZED:
            self._window.setWindowState(Qt.WindowState.WindowMaximized)

    def confirm_placement(self) -> None:
        if self._target is None:
            return
        QTimer.singleShot(0, self._reassert_monitor)

    def _reassert_monitor(self) -> None:
        monitor = self._target
        self._target = None
        if monitor is None:
            return

        window = self._window
        current = window.screen()
        if current is not None and current.name() == monitor.name:
            return

        self._restoring = True
        try:
            state = self._target_state
            if state in (WINDOW_STATE_FULLSCREEN, WINDOW_STATE_MAXIMIZED):
                window.showNormal()
            window.setGeometry(monitors.fit(window.geometry(), monitor))
            if state == WINDOW_STATE_FULLSCREEN:
                window.showFullScreen()
            elif state == WINDOW_STATE_MAXIMIZED:
                window.showMaximized()
        finally:
            self._restoring = False

    def schedule_save(self) -> None:
        if self._restoring:
            return
        self._save_timer.start()

    def save_now(self) -> None:
        self._save_timer.stop()
        if self._restoring:
            return
        screens = monitors.get_screens()
        if not screens:
            return
        placement = self._capture(screens)
        if placement is not None:
            self._store(monitors.layout_signature(screens), placement)

    def _capture(self, screens: list[Monitor]) -> WindowPlacement | None:
        window = self._window
        if window.isMinimized():
            return None

        if window.isFullScreen():
            state = WINDOW_STATE_FULLSCREEN
        elif window.isMaximized():
            state = WINDOW_STATE_MAXIMIZED
        else:
            state = WINDOW_STATE_NORMAL

        normal_rect = window.geometry() if state == WINDOW_STATE_NORMAL else window.normalGeometry()
        if normal_rect.isEmpty():
            normal_rect = window.geometry()

        monitor = None
        screen = window.screen()
        if screen is not None:
            monitor = monitors.find_screen(screens, screen.name(), screen.geometry())
        if monitor is None:
            index = monitors.find_screen_index(screens, window.frameGeometry().center())
            monitor = screens[index] if index != MONITOR_NO_INDEX else monitors.primary_screen(screens)
        if monitor is None:
            return None

        return WindowPlacement(
            geometry=window.saveGeometry(),
            normal_rect=normal_rect,
            screen_name=monitor.name,
            screen_rect=monitor.geometry,
            state=state,
        )

    def _store(self, signature: str, placement: WindowPlacement) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(_key(signature, SETTINGS_GEOMETRY_LEAF), placement.geometry)
        settings.setValue(_key(signature, SETTINGS_WINDOW_STATE_LEAF), placement.state)
        settings.setValue(_key(signature, SETTINGS_SCREEN_NAME_LEAF), placement.screen_name)
        settings.setValue(_key(signature, SETTINGS_SCREEN_RECT_LEAF), _rect_to_text(placement.screen_rect))
        settings.setValue(_key(signature, SETTINGS_NORMAL_RECT_LEAF), _rect_to_text(placement.normal_rect))

    def _load(self, signature: str) -> WindowPlacement:
        settings = QSettings(ORG_NAME, APP_NAME)
        geometry = settings.value(_key(signature, SETTINGS_GEOMETRY_LEAF))
        screen_name = settings.value(_key(signature, SETTINGS_SCREEN_NAME_LEAF))
        state = settings.value(_key(signature, SETTINGS_WINDOW_STATE_LEAF))

        return WindowPlacement(
            geometry=geometry if isinstance(geometry, QByteArray) else None,
            normal_rect=_text_to_rect(settings.value(_key(signature, SETTINGS_NORMAL_RECT_LEAF))),
            screen_name=screen_name if isinstance(screen_name, str) else "",
            screen_rect=_text_to_rect(settings.value(_key(signature, SETTINGS_SCREEN_RECT_LEAF))),
            state=state if state in WINDOW_STATES else WINDOW_STATE_NORMAL,
        )