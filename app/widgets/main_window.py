from pathlib import Path
from PyQt6.QtCore import QByteArray, QEvent, QPoint, QSettings, Qt
from PyQt6.QtGui import QCloseEvent, QKeySequence, QMoveEvent, QResizeEvent, QShortcut, QShowEvent
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget

from app.config import (
    APP_NAME, CANVAS_POPUP_DEFAULT_HEIGHT, CANVAS_POPUP_DEFAULT_WIDTH,
    FULLSCREEN_SHORTCUT_ESC, FULLSCREEN_SHORTCUT_F11, HUD_POSITION_OFFSET,
    LOG_PREFIX_VOICE, MIC_BUTTON_LISTENING_TEXT, MIC_BUTTON_MUTED_TEXT,
    ORG_NAME, RECIPE_POPUP_DEFAULT_HEIGHT, RECIPE_POPUP_DEFAULT_WIDTH,
    SETTINGS_SPLITTER_STATE_KEY, SETTINGS_VOLUME_KEY, SPLITTER_DEFAULT_CANVAS_RATIO,
    SPLITTER_DEFAULT_CHAT_RATIO, SPLITTER_HANDLE_WIDTH, SPLITTER_STRETCH_CANVAS,
    SPLITTER_STRETCH_CHAT, TTS_VOLUME_PERCENT_DEFAULT, VIDEO_PREVIEW_DEFAULT_HEIGHT,
    VIDEO_PREVIEW_DEFAULT_WIDTH, VOICE_MSG_NO_COMMAND_HEARD, WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_TITLE,
)
from app.core import perf, qthread_support
from app.threads import VoiceListener
from app.widget_helpers.stylesheet import build_stylesheet
from app.widget_helpers.win_dark_mode import enable_dark_titlebar
from app.widget_helpers.window_placement import WindowPlacementManager
from app.widgets.canvas_panel import CanvasPanel
from app.widgets.chat_panel import ChatPanel
from app.widgets.cocktail_canvas_popup import CocktailCanvasPopup
from app.widgets.recipe_panel import TopRightRecipyWidget
from app.widgets.video_panel import TopLeftVideoWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._placement: WindowPlacementManager | None = None
        self._hud_ready: bool = False

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setStyleSheet(build_stylesheet())

        self._dark_titlebar_applied: bool = False

        self._agent_busy: bool = False
        self._is_rendering: bool = False
        self._tts_speaking: bool = False
        self._transcribing: bool = False
        self._voice_ready: bool = False

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, central)
        self.splitter.setHandleWidth(SPLITTER_HANDLE_WIDTH)

        self.canvas_panel = CanvasPanel(self.splitter)
        self.chat_panel = ChatPanel(
            on_thinking_started=self._on_thinking_started,
            on_thinking_ended=self._on_thinking_ended,
            on_voice_transcription_ended=self._on_transcribing_ended,
            on_speaking_started=self._on_speaking_started,
            on_speaking_ended=self._on_speaking_ended,
            on_speaking_amplitude=self._on_speaking_amplitude,
            on_render_success=self._on_render_success,
            on_render_ended=self._on_render_ended,
            on_recipe_ready=self._on_recipe_ready,
            on_animation_ready=self._on_animation_ready,
            on_video_render_started=self._on_video_render_started,
            parent=self.splitter
        )

        self.splitter.addWidget(self.canvas_panel)
        self.splitter.addWidget(self.chat_panel)
        self.splitter.setStretchFactor(0, SPLITTER_STRETCH_CANVAS)
        self.splitter.setStretchFactor(1, SPLITTER_STRETCH_CHAT)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        layout.addWidget(self.splitter)

        self.setCentralWidget(central)

        self._setup_shortcuts()
        self._restore_settings()
        self._setup_voice_listener()

        self.canvas_panel.mute_button.toggled.connect(self._on_mute_toggle)
        self.canvas_panel.volume_changed.connect(self.chat_panel.set_speech_volume)
        self._restore_volume()

        self.video_preview = TopLeftVideoWidget(self, width=VIDEO_PREVIEW_DEFAULT_WIDTH, height=VIDEO_PREVIEW_DEFAULT_HEIGHT)
        self.video_preview.hide()

        self.cocktail_popup = CocktailCanvasPopup(self, width=CANVAS_POPUP_DEFAULT_WIDTH, height=CANVAS_POPUP_DEFAULT_HEIGHT)
        self.cocktail_popup.export_requested.connect(self._on_export_requested)
        self.cocktail_popup.hide()

        self.recipe_widget = TopRightRecipyWidget(self, width=RECIPE_POPUP_DEFAULT_WIDTH, height=RECIPE_POPUP_DEFAULT_HEIGHT)
        self.recipe_widget.hide()

        self._hud_ready = True
        self._reposition_hud_widgets()
        self._raise_hud_widgets()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._placement is not None:
            self._placement.schedule_save()
        self._reposition_hud_widgets()
        self._raise_hud_widgets()

    def moveEvent(self, event: QMoveEvent) -> None:
        super().moveEvent(event)
        if self._placement is not None:
            self._placement.schedule_save()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self._placement is not None:
            self._placement.schedule_save()

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        self._reposition_hud_widgets()
        self._raise_hud_widgets()

    def _reposition_hud_widgets(self) -> None:
        if not self._hud_ready:
            return

        canvas = self.canvas_panel
        top_left = canvas.mapTo(self, QPoint(HUD_POSITION_OFFSET, HUD_POSITION_OFFSET))
        self.video_preview.move(top_left)
        self.cocktail_popup.move(top_left)

        recipe_x = canvas.width() - self.recipe_widget.width() - HUD_POSITION_OFFSET
        self.recipe_widget.move(canvas.mapTo(self, QPoint(recipe_x, HUD_POSITION_OFFSET)))

    def _raise_hud_widgets(self) -> None:
        if not self._hud_ready:
            return
        self.recipe_widget.raise_()
        self.video_preview.raise_()
        self.cocktail_popup.raise_()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(FULLSCREEN_SHORTCUT_F11), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence(FULLSCREEN_SHORTCUT_ESC), self, activated=self._on_escape_pressed)

    def _on_escape_pressed(self) -> None:
        if self.recipe_widget.isVisible():
            self.recipe_widget.close_panel()
            return
        if self.cocktail_popup.isVisible():
            self.cocktail_popup.close_panel()
            return
        if self.video_preview.isVisible():
            self.video_preview.close_panel()
            return
        self.toggle_fullscreen()

    def _restore_settings(self) -> None:
        self._placement = WindowPlacementManager(self)
        self._placement.restore()

        settings = QSettings(ORG_NAME, APP_NAME)
        splitter_state = settings.value(SETTINGS_SPLITTER_STATE_KEY)
        if isinstance(splitter_state, QByteArray):
            self.splitter.restoreState(splitter_state)
        else:
            width = self.width()
            self.splitter.setSizes([int(width * SPLITTER_DEFAULT_CANVAS_RATIO), int(width * SPLITTER_DEFAULT_CHAT_RATIO)])

    def _restore_volume(self) -> None:
        settings = QSettings(ORG_NAME, APP_NAME)
        percent = settings.value(SETTINGS_VOLUME_KEY, TTS_VOLUME_PERCENT_DEFAULT, type=int)
        self.canvas_panel.set_volume(percent)

    def _setup_voice_listener(self) -> None:
        self.voice_listener = VoiceListener(self)
        self.voice_listener.listener_ready.connect(self._on_listener_ready)
        self.voice_listener.wake_detected.connect(self._on_wake_detected)
        self.voice_listener.wake_word_detected.connect(self._on_wake_word_detected)
        self.voice_listener.stop_word_detected.connect(self._on_stop_word_detected)
        self.voice_listener.error_occurred.connect(self._on_voice_error)
        self.voice_listener.speech_started.connect(self._on_speech_started)
        self.voice_listener.speech_ended.connect(self._on_speech_ended)
        self.voice_listener.listening_amplitude.connect(self._on_listening_amplitude)
        self.voice_listener.transcribing_started.connect(self._on_transcribing_started)
        self.voice_listener.transcribing_ended.connect(self._on_transcribing_ended)

        self.canvas_panel.mic_toggle_button.setChecked(True)
        self.canvas_panel.mic_toggle_button.toggled.connect(self._on_mic_toggle)
        self.voice_listener.pause()

        self._refresh_busy_visuals()
        self.voice_listener.start()

    def _on_listener_ready(self) -> None:
        self._voice_ready = True
        button = self.canvas_panel.mic_toggle_button
        button.setEnabled(True)
        button.setText(MIC_BUTTON_MUTED_TEXT if button.isChecked() else MIC_BUTTON_LISTENING_TEXT)
        self._refresh_busy_visuals()

    def _on_wake_detected(self) -> None:
        self.canvas_panel.sphere.enter_listening()
        self.chat_panel.start_voice_transcription()
        perf.mark("wake.ui_shown")

    def _on_wake_word_detected(self, text: str) -> None:
        self.chat_panel.finish_voice_transcription(text)

    def _on_stop_word_detected(self) -> None:
        if not (self._agent_busy or self._tts_speaking or self._transcribing):
            return
        self.chat_panel.interrupt()

    def _on_speech_started(self):
        self.canvas_panel.sphere.enter_listening()

    def _on_speech_ended(self):
        self._refresh_busy_visuals()

    def _on_transcribing_started(self) -> None:
        self._transcribing = True
        self._refresh_busy_visuals()
        self.chat_panel.start_voice_transcription()

    def _on_transcribing_ended(self) -> None:
        self._transcribing = False
        self._refresh_busy_visuals()

    def _refresh_busy_visuals(self) -> None:
        if not self._voice_ready:
            self.canvas_panel.sphere.enter_thinking()
            return

        if self._is_rendering:
            self.canvas_panel.sphere.enter_rendering()
        elif self._agent_busy or self._transcribing:
            self.canvas_panel.sphere.enter_thinking()
        elif self._tts_speaking:
            self.canvas_panel.sphere.enter_speaking()
        else:
            self.canvas_panel.sphere.enter_default()

        if self._agent_busy or self._tts_speaking or self._transcribing:
            self.voice_listener.suspend()
        else:
            self.voice_listener.unsuspend()

    def _on_thinking_started(self):
        self._agent_busy = True
        self._refresh_busy_visuals()

    def _on_thinking_ended(self):
        self._agent_busy = False
        self._refresh_busy_visuals()

    def _on_animation_ready(self, spec: dict):
        self.video_preview.close_panel()
        self.cocktail_popup.play(spec)
        self._raise_hud_widgets()

    def _on_export_requested(self, spec: dict):
        self.chat_panel.request_render(spec)

    def _on_speaking_amplitude(self, level: float) -> None:
        self.canvas_panel.sphere.update_speaking_amplitude(level)

    def _on_listening_amplitude(self, level: float) -> None:
        self.canvas_panel.sphere.update_listening_amplitude(level)

    def _on_render_success(self, output_mp4_path: str):
        self._is_rendering = False
        self.cocktail_popup.export_settled()

        geometry = self.cocktail_popup.geometry()
        was_visible = self.cocktail_popup.isVisible()
        self.cocktail_popup.close_panel()

        if was_visible:
            self.video_preview.setGeometry(geometry)
        self.video_preview.play_video(output_mp4_path, title=Path(output_mp4_path).stem)

        self._raise_hud_widgets()
        self._refresh_busy_visuals()

    def _on_render_ended(self):
        self._is_rendering = False
        self.cocktail_popup.export_settled()
        self._refresh_busy_visuals()

    def _on_video_render_started(self, cocktail_name: str):
        self._is_rendering = True
        if not self.cocktail_popup.isVisible():
            self.video_preview.show_preparing(f"Creating {cocktail_name}...")
        self._refresh_busy_visuals()
        self._raise_hud_widgets()

    def _on_recipe_ready(self, data: dict):
        self.recipe_widget.show_recipe(data)
        self._reposition_hud_widgets()
        self._raise_hud_widgets()

    def _on_speaking_started(self):
        self._tts_speaking = True
        self._refresh_busy_visuals()

    def _on_speaking_ended(self):
        self._tts_speaking = False
        self._refresh_busy_visuals()

    def _on_mic_toggle(self, muted: bool) -> None:
        button = self.canvas_panel.mic_toggle_button
        if muted:
            self.voice_listener.pause()
            button.setText(MIC_BUTTON_MUTED_TEXT)
        else:
            self.voice_listener.resume()
            button.setText(MIC_BUTTON_LISTENING_TEXT)

    def _on_voice_error(self, message: str) -> None:
        print(f"{LOG_PREFIX_VOICE} {message}")
        if message == VOICE_MSG_NO_COMMAND_HEARD:
            self.chat_panel.finish_voice_transcription("")

    def _on_mute_toggle(self, checked: bool) -> None:
        self.chat_panel.set_speech_muted(checked)

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._dark_titlebar_applied:
            enable_dark_titlebar(int(self.winId()))
            self._dark_titlebar_applied = True
        if self._placement is not None:
            self._placement.confirm_placement()

    def closeEvent(self, event: QCloseEvent) -> None:
        qthread_support.log_running("closeEvent")

        if self._placement is not None:
            self._placement.save_now()
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTINGS_SPLITTER_STATE_KEY, self.splitter.saveState())
        settings.setValue(SETTINGS_VOLUME_KEY, self.canvas_panel.volume())

        self.voice_listener.stop()
        self.cocktail_popup.stop()
        self.chat_panel.shutdown()
        self.recipe_widget.shutdown()

        super().closeEvent(event)