from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.config import (
    MIC_BUTTON_LISTENING_TEXT,
    MUTE_BUTTON_ICON_MUTED,
    MUTE_BUTTON_ICON_UNMUTED,
    MUTE_BUTTON_MARGIN,
    MUTE_BUTTON_SIZE,
    OBJECT_NAME_CANVAS_PANEL,
    OBJECT_NAME_MIC_TOGGLE_BUTTON,
    OBJECT_NAME_MUTE_BUTTON,
)
from app.widgets.sphere_widget import SphereWidget


class CanvasPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(OBJECT_NAME_CANVAS_PANEL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sphere = SphereWidget(self)
        layout.addWidget(self.sphere)

        self.mic_toggle_button = QPushButton(MIC_BUTTON_LISTENING_TEXT, self)
        self.mic_toggle_button.setObjectName(OBJECT_NAME_MIC_TOGGLE_BUTTON)
        self.mic_toggle_button.setCheckable(True)
        layout.addWidget(self.mic_toggle_button)

        self.mute_button = QPushButton(MUTE_BUTTON_ICON_UNMUTED, self)
        self.mute_button.setObjectName(OBJECT_NAME_MUTE_BUTTON)
        self.mute_button.setCheckable(True)
        self.mute_button.setFixedSize(MUTE_BUTTON_SIZE, MUTE_BUTTON_SIZE)
        self.mute_button.toggled.connect(self._on_mute_button_toggled)
        self.mute_button.raise_()

    def _on_mute_button_toggled(self, checked: bool) -> None:
        self.mute_button.setText(MUTE_BUTTON_ICON_MUTED if checked else MUTE_BUTTON_ICON_UNMUTED)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        sphere_rect = self.sphere.geometry()
        x = sphere_rect.right() - MUTE_BUTTON_SIZE - MUTE_BUTTON_MARGIN
        y = sphere_rect.bottom() - MUTE_BUTTON_SIZE - MUTE_BUTTON_MARGIN
        self.mute_button.move(x, y)
        self.mute_button.raise_()