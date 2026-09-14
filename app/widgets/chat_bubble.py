from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app import config


class ChatBubble(QWidget):
    def __init__(self, text: str, is_user: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        label = QLabel(text, self)
        label.setObjectName("userBubble" if is_user else "agentBubble")
        label.setWordWrap(True)
        label.setMaximumWidth(config.CHAT_BUBBLE_MAX_WIDTH)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if is_user:
            layout.addStretch(1)
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch(1)