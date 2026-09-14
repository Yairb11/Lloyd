from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app import config
from app.agent import get_reply
from app.widgets.chat_bubble import ChatBubble


class ChatPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chatPanel")
        self.setMinimumWidth(config.CHAT_PANEL_MIN_WIDTH)

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

        self._append_bubble(message, is_user=True)
        self.input.clear()

        reply = get_reply(message)
        self._append_bubble(str(reply), is_user=False)

    def _append_bubble(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user, self.history_content)
        self.history_layout.insertWidget(self.history_layout.count() - 1, bubble)
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.history_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())