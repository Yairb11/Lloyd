from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.config import (
    CHAT_HISTORY_SPACING,
    CHAT_INPUT_PLACEHOLDER,
    CHAT_INPUT_ROW_SPACING,
    CHAT_PANEL_MARGIN,
    CHAT_PANEL_MIN_WIDTH,
    CHAT_PANEL_SPACING,
    CHAT_SEND_BUTTON_TEXT,
    CHAT_STOP_BUTTON_TEXT,
    LOG_PREFIX_AGENT,
    OBJECT_NAME_CHAT_HISTORY,
    OBJECT_NAME_CHAT_PANEL,
    OBJECT_NAME_SEND_BUTTON,
)
from app.helpers.text import clean_text_for_speech
from app.threads import Agent, LloydSpeaker
from app.widgets.chat_bubble import ChatBubble
from app.widgets.typing_indicator import TypingIndicator


class ChatPanel(QWidget):
    def __init__(
        self,
        on_thinking_started=None,
        on_thinking_ended=None,
        on_speaking_started=None,
        on_speaking_ended=None,
        on_render_success=None,
        parent: QWidget | None = None
    ) -> None:

        super().__init__(parent)
        self.setObjectName(OBJECT_NAME_CHAT_PANEL)
        self.setMinimumWidth(CHAT_PANEL_MIN_WIDTH)

        self.on_thinking_started = on_thinking_started
        self.on_thinking_ended = on_thinking_ended
        self.on_speaking_started = on_speaking_started
        self.on_speaking_ended = on_speaking_ended
        self.on_render_success = on_render_success
        self.agent = None
        self._busy = False
        self._session_id: str | None = None
        self.lloyd_speaker = LloydSpeaker(self)
        self.lloyd_speaker.speech_started.connect(self.on_speaking_started)
        self.lloyd_speaker.speech_finished.connect(self.on_speaking_ended)
        self._typing_indicator: TypingIndicator | None = None

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
            self._stop_active_request()
        else:
            self._on_send()

    def _on_send(self) -> None:
        if self._busy:
            return
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.submit_message(message)

    def submit_message(self, message: str) -> None:
        message = message.strip()
        if not message or self._busy:
            return

        self._append_bubble(message, is_user=True)
        self.agent = Agent(message, session_id=self._session_id)
        self.agent.error_occurred.connect(self._on_agent_error)
        self.agent.show_reply.connect(self._on_show_reply)
        self.agent.show_status.connect(self._on_show_status)
        self.agent.thinking_started.connect(self._on_thinking_started)
        self.agent.thinking_ended.connect(self._on_thinking_ended)
        self.agent.render_succeeded.connect(self._on_render_succeeded)
        self.agent.session_id_updated.connect(self._on_session_id_updated)

        self._set_busy(True)
        self.agent.start()

    def _stop_active_request(self) -> None:
        if self.agent is not None:
            self.agent.stop_active_worker()
            self.agent = None

        self._hide_typing_indicator()
        self._set_busy(False)
        if self.on_thinking_ended is not None:
            self.on_thinking_ended()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.send_button.setText(CHAT_STOP_BUTTON_TEXT if busy else CHAT_SEND_BUTTON_TEXT)
        self.send_button.setProperty("busy", busy)
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)
        self.input.setEnabled(not busy)

    def _on_agent_error(self, message: str) -> None:
        if self.sender() is not self.agent:
            return
        print(f"{LOG_PREFIX_AGENT} {message}")

    def _on_thinking_started(self) -> None:
        if self.sender() is not self.agent:
            return
        self.on_thinking_started()
        self._show_typing_indicator()

    def _on_thinking_ended(self) -> None:
        if self.sender() is not self.agent:
            return
        self.on_thinking_ended()
        self._hide_typing_indicator()
        self._set_busy(False)

    def _show_typing_indicator(self) -> None:
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

    def _on_show_reply(self, reply: str) -> None:
        if self.sender() is not self.agent:
            return
        self._append_bubble(str(reply), is_user=False)

        speech_text = clean_text_for_speech(str(reply))
        if speech_text:
            self.lloyd_speaker.speak(speech_text)

    def _on_show_status(self, text: str) -> None:
        if self.sender() is not self.agent:
            return
        self._append_bubble(str(text), is_user=False)

    def _on_session_id_updated(self, session_id: str) -> None:
        if self.sender() is not self.agent:
            return
        self._session_id = session_id

    def _on_render_succeeded(self, output_mp4_path: str) -> None:
        if self.sender() is not self.agent:
            return
        if self.on_render_success is not None:
            self.on_render_success(output_mp4_path)

    def _append_bubble(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user, self.history_content)
        self.history_layout.insertWidget(self.history_layout.count() - 1, bubble)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.history_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
