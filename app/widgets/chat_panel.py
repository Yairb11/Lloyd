from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget
from thefuzz import fuzz

from app.config import (
    AGENT_RENDER_FAILED_PREFIX, AGENT_RENDER_STARTED_TEXT, AGENT_RENDER_STATUS_TEXT,
    ANIM_BACKEND, ANIM_BACKEND_BOTH, ANIM_BACKEND_CANVAS,
    ANIM_BACKEND_MANIM, CHAT_CLEAR_COMMAND_TEXT, CHAT_CLEAR_VOICE_MATCH_THRESHOLD,
    CHAT_CLEAR_VOICE_PHRASE, CHAT_HISTORY_SPACING, CHAT_INPUT_PLACEHOLDER,
    CHAT_INPUT_ROW_SPACING, CHAT_PANEL_MARGIN, CHAT_PANEL_MIN_WIDTH,
    CHAT_PANEL_SPACING, CHAT_SEND_BUTTON_TEXT, CHAT_STOP_BUTTON_TEXT,
    LOG_PREFIX_AGENT, OBJECT_NAME_CHAT_HISTORY, OBJECT_NAME_CHAT_PANEL,
    OBJECT_NAME_SEND_BUTTON,
)
from app.core import perf
from app.render import RenderController
from app.threads import Agent, LloydSpeaker
from app.widgets.chat_bubble import ChatBubble
from app.widgets.typing_indicator import TypingIndicator


class ChatPanel(QWidget):
    def __init__(
        self,
        on_thinking_started=None,
        on_thinking_ended=None,
        on_voice_transcription_ended=None,
        on_speaking_started=None,
        on_speaking_ended=None,
        on_speaking_amplitude=None,
        on_render_success=None,
        on_render_ended=None,
        on_recipe_ready=None,
        on_animation_ready=None,
        on_video_render_started=None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName(OBJECT_NAME_CHAT_PANEL)
        self.setMinimumWidth(CHAT_PANEL_MIN_WIDTH)

        self.on_thinking_started = on_thinking_started
        self.on_thinking_ended = on_thinking_ended
        self.on_voice_transcription_ended = on_voice_transcription_ended
        self.on_speaking_started = on_speaking_started
        self.on_speaking_ended = on_speaking_ended
        self.on_speaking_amplitude = on_speaking_amplitude
        self.on_render_success = on_render_success
        self.on_render_ended = on_render_ended
        self.on_recipe_ready = on_recipe_ready
        self.on_animation_ready = on_animation_ready
        self.on_video_render_started = on_video_render_started

        self._busy = False
        self._speaking = False
        self._voice_transcribing = False
        self._speech_muted = False
        self._typing_indicator: TypingIndicator | None = None
        self._voice_transcribing_indicator: TypingIndicator | None = None

        self.lloyd_speaker = LloydSpeaker(self)
        self.lloyd_speaker.speech_started.connect(self._on_speech_started)
        self.lloyd_speaker.speech_finished.connect(self._on_speech_finished)
        self.lloyd_speaker.amplitude_changed.connect(self._on_speaking_amplitude)
        self.lloyd_speaker.engine_ready.connect(self._on_engine_ready)
        self.lloyd_speaker.start()

        self.render_controller = RenderController(self)
        self.render_controller.render_started.connect(self._on_render_started)
        self.render_controller.render_finished.connect(self._on_render_finished)
        self.render_controller.render_cached.connect(self._on_render_cached)
        self.render_controller.render_failed.connect(self._on_render_failed)

        self.agent = Agent(self)
        self.agent.error_occurred.connect(self._on_agent_error)
        self.agent.speak_sentence.connect(self._on_speak_sentence)
        self.agent.speech_complete.connect(self._on_speech_complete)
        self.agent.show_reply.connect(self._on_show_reply)
        self.agent.show_status.connect(self._on_show_status)
        self.agent.thinking_started.connect(self._on_thinking_started)
        self.agent.thinking_ended.connect(self._on_thinking_ended)
        self.agent.recipe_ready.connect(self._on_recipe_ready)
        self.agent.animation_ready.connect(self._on_animation_ready)
        self.agent.start()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CHAT_PANEL_MARGIN, CHAT_PANEL_MARGIN, CHAT_PANEL_MARGIN, CHAT_PANEL_MARGIN)
        layout.setSpacing(CHAT_PANEL_SPACING)

        self.history_content = QWidget()
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(CHAT_HISTORY_SPACING)
        self.history_layout.addStretch(1)

        self.history_scroll = QScrollArea(self)
        self.history_scroll.setObjectName(OBJECT_NAME_CHAT_HISTORY)
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setWidget(self.history_content)
        self.history_scroll.verticalScrollBar().rangeChanged.connect(self._on_history_range_changed)
        layout.addWidget(self.history_scroll)

        input_row = QHBoxLayout()
        input_row.setSpacing(CHAT_INPUT_ROW_SPACING)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText(CHAT_INPUT_PLACEHOLDER)
        input_row.addWidget(self.input)

        self.send_button = QPushButton(CHAT_SEND_BUTTON_TEXT, self)
        self.send_button.setObjectName(OBJECT_NAME_SEND_BUTTON)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

        self.send_button.clicked.connect(self._on_send_button_clicked)
        self.input.returnPressed.connect(self._on_send)

    def _on_send_button_clicked(self) -> None:
        if self._busy:
            self.interrupt()
        else:
            self._on_send()

    def _on_send(self) -> None:
        if self._busy or self._speaking:
            return
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.submit_message(message)

    def submit_message(self, message: str, *, via_voice: bool = False) -> None:
        message = message.strip()
        if not message or self._busy:
            return

        if self._is_clear_chat_command(message, via_voice=via_voice):
            self._clear_chat()
            return

        if not via_voice:
            perf.start("text")

        self._append_bubble(message, is_user=True)
        self.render_controller.set_last_message(message)
        self._set_busy(True)
        perf.mark("agent.submitted")
        self.agent.submit(message)

    def _is_clear_chat_command(self, message: str, *, via_voice: bool) -> bool:
        normalized = message.lower()
        if via_voice:
            return fuzz.ratio(CHAT_CLEAR_VOICE_PHRASE, normalized) >= CHAT_CLEAR_VOICE_MATCH_THRESHOLD
        return normalized == CHAT_CLEAR_COMMAND_TEXT

    def _clear_chat(self) -> None:
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.agent.reset_session()

    def start_voice_transcription(self) -> None:
        if self._busy or self._voice_transcribing:
            return
        self._voice_transcribing = True
        self._set_busy(True)
        self._show_voice_transcribing_indicator()

    def finish_voice_transcription(self, text: str) -> None:
        if not self._voice_transcribing:
            return
        self._voice_transcribing = False
        self._hide_voice_transcribing_indicator()
        self._set_busy(False)
        if self.on_voice_transcription_ended is not None:
            self.on_voice_transcription_ended()

        text = text.strip()
        if text:
            self.submit_message(text, via_voice=True)

    def interrupt(self) -> None:
        if self._voice_transcribing:
            self._voice_transcribing = False
            self._hide_voice_transcribing_indicator()
            self._set_busy(False)
            if self.on_voice_transcription_ended is not None:
                self.on_voice_transcription_ended()
            return

        self.agent.interrupt()
        self.lloyd_speaker.stop()
        self.render_controller.cancel()
        self._hide_typing_indicator()
        self._set_busy(False)
        if self.on_render_ended is not None:
            self.on_render_ended()
        if self.on_thinking_ended is not None:
            self.on_thinking_ended()

    def set_speech_muted(self, muted: bool) -> None:
        self._speech_muted = muted
        if muted:
            self.lloyd_speaker.stop()

    def shutdown(self) -> None:
        self.render_controller.shutdown()
        self.agent.shutdown()
        self.lloyd_speaker.shutdown()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.send_button.setText(CHAT_STOP_BUTTON_TEXT if busy else CHAT_SEND_BUTTON_TEXT)
        self.send_button.setProperty("busy", busy)
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)
        self._refresh_input_locked()

    def _on_engine_ready(self, name: str) -> None:
        print(f"{LOG_PREFIX_AGENT} tts engine: {name}")

    def _on_speech_started(self) -> None:
        self._speaking = True
        self._refresh_input_locked()
        if self.on_speaking_started is not None:
            self.on_speaking_started()

    def _on_speech_finished(self) -> None:
        self._speaking = False
        self._refresh_input_locked()
        if self.on_speaking_ended is not None:
            self.on_speaking_ended()

    def _on_speaking_amplitude(self, level: float) -> None:
        if self.on_speaking_amplitude is not None:
            self.on_speaking_amplitude(level)

    def _refresh_input_locked(self) -> None:
        self.input.setEnabled(not self._busy and not self._speaking)
        self.send_button.setEnabled(not self._speaking)

    def _on_agent_error(self, message: str) -> None:
        print(f"{LOG_PREFIX_AGENT} {message}")

    def _on_thinking_started(self) -> None:
        if self.on_thinking_started is not None:
            self.on_thinking_started()
        self._show_typing_indicator()

    def _on_thinking_ended(self) -> None:
        if self.on_thinking_ended is not None:
            self.on_thinking_ended()
        self._hide_typing_indicator()
        self._set_busy(False)

    def _on_speak_sentence(self, sentence: str) -> None:
        if self._speech_muted:
            return
        perf.mark("tts.requested", once=True)
        self.lloyd_speaker.enqueue(sentence)

    def _on_speech_complete(self) -> None:
        if self._speech_muted:
            return
        self.lloyd_speaker.finish()

    def _on_animation_ready(self, spec: dict) -> None:
        if ANIM_BACKEND in (ANIM_BACKEND_CANVAS, ANIM_BACKEND_BOTH):
            if self.on_animation_ready is not None:
                self.on_animation_ready(spec)
        if ANIM_BACKEND in (ANIM_BACKEND_MANIM, ANIM_BACKEND_BOTH):
            self.render_controller.request(spec)

    def request_render(self, spec: dict) -> None:
        self.render_controller.request(dict(spec))

    def _on_render_started(self, cocktail_name: str) -> None:
        self._append_bubble(AGENT_RENDER_STARTED_TEXT, is_user=False)
        if self.on_video_render_started is not None:
            self.on_video_render_started(cocktail_name)

    def _on_render_finished(self, path: str) -> None:
        self._append_bubble(AGENT_RENDER_STATUS_TEXT, is_user=False)
        if self.on_render_success is not None:
            self.on_render_success(path)

    def _on_render_cached(self, path: str) -> None:
        if self.on_render_success is not None:
            self.on_render_success(path)

    def _on_render_failed(self, message: str) -> None:
        self._append_bubble(f"{AGENT_RENDER_FAILED_PREFIX} {message}", is_user=False)
        if self.on_render_ended is not None:
            self.on_render_ended()

    def _show_typing_indicator(self) -> None:
        if self._typing_indicator is not None:
            return
        self._typing_indicator = TypingIndicator(self.history_content)
        self.history_layout.insertWidget(self.history_layout.count() - 1, self._typing_indicator)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _hide_typing_indicator(self) -> None:
        if self._typing_indicator is None:
            return
        self._typing_indicator.stop()
        self.history_layout.removeWidget(self._typing_indicator)
        self._typing_indicator.deleteLater()
        self._typing_indicator = None

    def _show_voice_transcribing_indicator(self) -> None:
        self._voice_transcribing_indicator = TypingIndicator(self.history_content, is_user=True)
        self.history_layout.insertWidget(self.history_layout.count() - 1, self._voice_transcribing_indicator)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _hide_voice_transcribing_indicator(self) -> None:
        if self._voice_transcribing_indicator is None:
            return
        self._voice_transcribing_indicator.stop()
        self.history_layout.removeWidget(self._voice_transcribing_indicator)
        self._voice_transcribing_indicator.deleteLater()
        self._voice_transcribing_indicator = None

    def _on_show_reply(self, reply: str) -> None:
        self._append_bubble(str(reply), is_user=False)

    def _on_show_status(self, text: str) -> None:
        self._append_bubble(str(text), is_user=False)

    def _on_recipe_ready(self, data: dict) -> None:
        if self.on_recipe_ready is not None:
            self.on_recipe_ready(data)

    def _append_bubble(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user, self.history_content)
        self.history_layout.insertWidget(self.history_layout.count() - 1, bubble)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.history_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_history_range_changed(self, minimum: int, maximum: int) -> None:
        self.history_scroll.verticalScrollBar().setValue(maximum)
