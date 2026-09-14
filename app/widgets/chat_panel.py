from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app import config
from app.threads import Agent, LloydSpeaker
from app.helpers.text import clean_text_for_speech
from app.widgets.chat_bubble import ChatBubble


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
        self.setObjectName("chatPanel")
        self.setMinimumWidth(config.CHAT_PANEL_MIN_WIDTH)

        self.on_thinking_started = on_thinking_started
        self.on_thinking_ended = on_thinking_ended
        self.on_speaking_started = on_speaking_started
        self.on_speaking_ended = on_speaking_ended
        self.on_render_success = on_render_success
        self.agent = None
        self.lloyd_speaker = LloydSpeaker(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.history_content = QWidget()
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(8)
        self.history_layout.addStretch(1)

        self.history_scroll = QScrollArea(self)
        self.history_scroll.setObjectName("chatHistory")
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setWidget(self.history_content)
        layout.addWidget(self.history_scroll)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Message Lloyd...")
        input_row.addWidget(self.input)

        self.send_button = QPushButton("Send", self)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

        self.send_button.clicked.connect(self._on_send)
        self.input.returnPressed.connect(self._on_send)

    def _on_send(self) -> None:
        message = self.input.text().strip()
        if not message:
            return
        self.input.clear()
        self.submit_message(message)

    def submit_message(self, message: str) -> None:
        message = message.strip()
        if not message:
            return

        self._append_bubble(message, is_user=True)
        self.agent = Agent(message)
        self.agent.error_occurred.connect(self._on_agent_error)
        self.agent.show_reply.connect(self._on_show_reply)
        self.agent.thinking_started.connect(self._on_thinking_started)
        self.agent.thinking_ended.connect(self._on_thinking_ended)
        self.agent.render_succeeded.connect(self.on_render_success)

        self.agent.start()

    def _on_agent_error(self, message: str) -> None:    
        print(f"[Lloyd agent] {message}")

    def _on_thinking_started(self) -> None:
        self.on_thinking_started()
        # SEE 3 DOTS MOVING INSIDE THE BUBBLE MESSAGES AS THE NON USER

    def _on_thinking_ended(self) -> None:
        self.on_thinking_ended()
        # STOP SEEN 3 DOTS MOVING INSIDE THE BUBBLE MESSAGES AS THE NON USER

    def _on_show_reply(self, reply: str) -> None:
        self._append_bubble(str(reply), is_user=False)

        speech_text = clean_text_for_speech(str(reply))
        if speech_text:
            self.lloyd_speaker.speak(speech_text)
        

    def _append_bubble(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user, self.history_content)
        self.history_layout.insertWidget(self.history_layout.count() - 1, bubble)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.history_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())