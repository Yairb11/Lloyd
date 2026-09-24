from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QSlider, QVBoxLayout

from app.config import (
    OBJECT_NAME_VOLUME_POPUP, OBJECT_NAME_VOLUME_SLIDER, TTS_VOLUME_PERCENT_MAX,
    TTS_VOLUME_PERCENT_MIN, VOLUME_LABEL_FORMAT, VOLUME_POPUP_HEIGHT,
    VOLUME_POPUP_MARGIN, VOLUME_POPUP_SPACING, VOLUME_POPUP_WIDTH,
    VOLUME_SLIDER_PAGE_STEP, VOLUME_SLIDER_SINGLE_STEP,
)


class VolumePopup(QFrame):
    volume_changed = pyqtSignal(int)
    hover_entered = pyqtSignal()
    hover_left = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName(OBJECT_NAME_VOLUME_POPUP)
        self.setFixedSize(VOLUME_POPUP_WIDTH, VOLUME_POPUP_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            VOLUME_POPUP_MARGIN, VOLUME_POPUP_MARGIN, VOLUME_POPUP_MARGIN, VOLUME_POPUP_MARGIN
        )
        layout.setSpacing(VOLUME_POPUP_SPACING)

        self._value_label = QLabel(self)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

        self._slider = QSlider(Qt.Orientation.Vertical, self)
        self._slider.setObjectName(OBJECT_NAME_VOLUME_SLIDER)
        self._slider.setRange(TTS_VOLUME_PERCENT_MIN, TTS_VOLUME_PERCENT_MAX)
        self._slider.setSingleStep(VOLUME_SLIDER_SINGLE_STEP)
        self._slider.setPageStep(VOLUME_SLIDER_PAGE_STEP)
        self._slider.valueChanged.connect(self._on_slider_value_changed)
        layout.addWidget(self._slider, 1, Qt.AlignmentFlag.AlignHCenter)

        self._refresh_label(self._slider.value())
        self.hide()

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, percent: int) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(percent)
        self._slider.blockSignals(False)
        self._refresh_label(self._slider.value())

    def is_adjusting(self) -> bool:
        return self._slider.isSliderDown()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.hover_entered.emit()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.hover_left.emit()

    def _on_slider_value_changed(self, percent: int) -> None:
        self._refresh_label(percent)
        self.volume_changed.emit(percent)

    def _refresh_label(self, percent: int) -> None:
        self._value_label.setText(VOLUME_LABEL_FORMAT.format(percent))