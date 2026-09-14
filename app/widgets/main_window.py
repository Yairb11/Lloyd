from PyQt6.QtCore import QByteArray, QSettings, Qt
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut, QShowEvent
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget

from app import config, theme
from app.widgets.canvas_panel import CanvasPanel
from app.widgets.chat_panel import ChatPanel
from app.win_dark_mode import enable_dark_titlebar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.setStyleSheet(theme.build_stylesheet())

        self._is_fullscreen: bool = False
        self._dark_titlebar_applied: bool = False

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, central)
        self.splitter.setHandleWidth(config.SPLITTER_HANDLE_WIDTH)

        self.canvas_panel = CanvasPanel(self.splitter)
        self.chat_panel = ChatPanel(self.splitter)
        self.splitter.addWidget(self.canvas_panel)
        self.splitter.addWidget(self.chat_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

        self.setCentralWidget(central)

        self._setup_shortcuts()
        self._restore_settings()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(config.FULLSCREEN_SHORTCUT_F11), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence(config.FULLSCREEN_SHORTCUT_ESC), self, activated=self.toggle_fullscreen)

    def _restore_settings(self) -> None:
        settings = QSettings(config.ORG_NAME, config.APP_NAME)

        geometry = settings.value(config.SETTINGS_GEOMETRY_KEY)
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        else:
            self.resize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        splitter_state = settings.value(config.SETTINGS_SPLITTER_STATE_KEY)
        if isinstance(splitter_state, QByteArray):
            self.splitter.restoreState(splitter_state)
        else:
            width = self.width()
            self.splitter.setSizes([int(width * 0.75), int(width * 0.25)])

        self._is_fullscreen = self.isFullScreen()

    def toggle_fullscreen(self) -> None:
        if self._is_fullscreen:
            self.showNormal()
            self._is_fullscreen = False
        else:
            self.showFullScreen()
            self._is_fullscreen = True

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._dark_titlebar_applied:
            enable_dark_titlebar(int(self.winId()))
            self._dark_titlebar_applied = True

    def closeEvent(self, event: QCloseEvent) -> None:
        settings = QSettings(config.ORG_NAME, config.APP_NAME)
        settings.setValue(config.SETTINGS_GEOMETRY_KEY, self.saveGeometry())
        settings.setValue(config.SETTINGS_SPLITTER_STATE_KEY, self.splitter.saveState())
        super().closeEvent(event)