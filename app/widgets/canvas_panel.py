from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.widgets.sphere_widget import SphereWidget


class CanvasPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("canvasPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sphere = SphereWidget(self)
        layout.addWidget(self.sphere)

        self.mic_toggle_button = QPushButton("Mic: Listening", self)
        self.mic_toggle_button.setObjectName("micToggleButton")
        self.mic_toggle_button.setCheckable(True)
        layout.addWidget(self.mic_toggle_button)