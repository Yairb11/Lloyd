from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.config import CHAT_BUBBLE_MAX_WIDTH, OBJECT_NAME_AGENT_BUBBLE, OBJECT_NAME_USER_BUBBLE


class ChatBubble(QWidget):
    def __init__(self, text: str, is_user: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        label = QLabel(text, self)
        label.setObjectName(OBJECT_NAME_USER_BUBBLE if is_user else OBJECT_NAME_AGENT_BUBBLE)
        label.setWordWrap(True)
        label.setMaximumWidth(CHAT_BUBBLE_MAX_WIDTH)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if is_user:
            layout.addStretch(1)
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch(1)
