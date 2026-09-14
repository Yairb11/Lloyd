from PyQt6.QtCore import QByteArray, QSettings, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut, QShowEvent
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget
from pathlib import Path

from app import config, theme
from app.threads import VoiceListener
from app.widgets.canvas_panel import CanvasPanel
from app.widgets.chat_panel import ChatPanel
from app.widgets.top_left_video_widget import TopLeftVideoWidget
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
        self.chat_panel = ChatPanel(
            on_thinking_started=self._on_thinking_started, 
            on_thinking_ended=self._on_thinking_ended,
            on_speaking_started=self._on_speaking_started,
            on_speaking_ended=self._on_speaking_ended,
            on_render_success=self._on_render_success,
            parent=self.splitter
        )
        self.splitter.addWidget(self.canvas_panel)
        self.splitter.addWidget(self.chat_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

        self.setCentralWidget(central)

        self._setup_shortcuts()
        self._restore_settings()
        self._setup_voice_listener()

        self.video_preview = TopLeftVideoWidget(self, width=420, height=260)
        self.video_preview.move(25, 25)
        self.video_preview.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.video_preview.move(25, 25)
        self.video_preview.raise_()

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

    def _setup_voice_listener(self) -> None:
        self.voice_listener = VoiceListener(self)
        self.voice_listener.wake_word_detected.connect(self._on_wake_word_detected)
        self.voice_listener.error_occurred.connect(self._on_voice_error)
        self.voice_listener.speech_started.connect(self._on_speach_started)
        self.voice_listener.speech_ended.connect(self._on_speach_ended)

        #========================================================================================================
        #self.canvas_panel.mic_toggle_button.toggled.connect(self._on_mic_toggle)
        self._on_mic_toggle(True)
        #========================================================================================================
        
        self.voice_listener.start()

    def _on_wake_word_detected(self, text: str) -> None:
        self.chat_panel.submit_message(text)

    def _on_speach_started(self):
        # Change sphere to blue, big and a little shrink and grow
        sphere = self.canvas_panel.sphere
        sphere.set_color(config.SPHERE_COLOR_LISTENING)
        sphere.grow()

    def _on_speach_ended(self):
        # Change back the sphere to ohere colors, with breathing animation
        sphere = self.canvas_panel.sphere
        sphere.shrink()
        sphere.release_color()

    def _on_thinking_started(self):
        # Change the sphere to thinking mode view
        pass

    def _on_thinking_ended(self):
        # Change back the sphere to ohere colors, with breathing animation
        pass

    def _on_render_success(self, output_mp4_path: str):
        self.video_preview.play_video(output_mp4_path, title=Path(output_mp4_path).stem)

    def _on_speaking_started(self):
        # Change the sphere to speaking mode view
        pass

    def _on_speaking_ended(self):
        # Change back the sphere to ohere colors, with breathing animation
        pass


    def _on_mic_toggle(self, muted: bool) -> None:
        button = self.canvas_panel.mic_toggle_button
        if muted:
            self.voice_listener.pause()
            button.setText("Mic: Muted")
        else:
            self.voice_listener.resume()
            button.setText("Mic: Listening")

    def _on_voice_error(self, message: str) -> None:
        print(f"[Lloyd voice] {message}")

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
        self.voice_listener.stop()

        settings = QSettings(config.ORG_NAME, config.APP_NAME)
        settings.setValue(config.SETTINGS_GEOMETRY_KEY, self.saveGeometry())
        settings.setValue(config.SETTINGS_SPLITTER_STATE_KEY, self.splitter.saveState())
        super().closeEvent(event)