from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.config import MIC_BUTTON_LISTENING_TEXT, OBJECT_NAME_CANVAS_PANEL, OBJECT_NAME_MIC_TOGGLE_BUTTON
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