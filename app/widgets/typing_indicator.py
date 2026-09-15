from PyQt6.QtWidgets import QHBoxLayout, QWidget

from app.widgets.typing_bubble import TypingBubble

class TypingIndicator(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bubble = TypingBubble(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._bubble)
        layout.addStretch(1)

    def stop(self) -> None:
        self._bubble.stop()