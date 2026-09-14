from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.widgets.sphere_widget import SphereWidget


class CanvasPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("canvasPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sphere = SphereWidget(self)
        layout.addWidget(self.sphere)