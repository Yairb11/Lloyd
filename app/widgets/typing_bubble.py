import math
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from app.config import (
    CHAT_BUBBLE_RADIUS,
    COLOR_BUBBLE_AGENT_BG,
    COLOR_BUBBLE_TEXT,
    COLOR_BUBBLE_USER_BG,
    COLOR_TEXT_SECONDARY,
    TYPING_BOUNCE_HEIGHT,
    TYPING_BUBBLE_HEIGHT,
    TYPING_BUBBLE_WIDTH,
    TYPING_CYCLE_SPEED,
    TYPING_DOT_COUNT,
    TYPING_DOT_PHASE_OFFSET,
    TYPING_DOT_RADIUS,
    TYPING_DOT_SPACING,
    TYPING_FRAME_INTERVAL_MS,
)


class TypingBubble(QWidget):
    def __init__(self, parent: QWidget | None = None, is_user: bool = False) -> None:
        super().__init__(parent)
        self.setFixedSize(TYPING_BUBBLE_WIDTH, TYPING_BUBBLE_HEIGHT)
        self._phase = 0.0
        self._bg_color = COLOR_BUBBLE_USER_BG if is_user else COLOR_BUBBLE_AGENT_BG
        self._dot_color = COLOR_BUBBLE_TEXT if is_user else COLOR_TEXT_SECONDARY

        self._timer = QTimer(self)
        self._timer.setInterval(TYPING_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _on_tick(self) -> None:
        self._phase += TYPING_CYCLE_SPEED * (TYPING_FRAME_INTERVAL_MS / 1000.0)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor(self._bg_color))
        painter.drawRoundedRect(self.rect(), CHAT_BUBBLE_RADIUS, CHAT_BUBBLE_RADIUS)

        center_y = self.height() / 2
        start_x = (self.width() - TYPING_DOT_SPACING * (TYPING_DOT_COUNT - 1)) / 2

        painter.setBrush(QColor(self._dot_color))
        for i in range(TYPING_DOT_COUNT):
            offset = math.sin(self._phase - i * TYPING_DOT_PHASE_OFFSET) * TYPING_BOUNCE_HEIGHT
            dot_x = start_x + i * TYPING_DOT_SPACING
            dot_y = center_y - offset
            painter.drawEllipse(
                int(dot_x - TYPING_DOT_RADIUS),
                int(dot_y - TYPING_DOT_RADIUS),
                int(TYPING_DOT_RADIUS * 2),
                int(TYPING_DOT_RADIUS * 2),
            )