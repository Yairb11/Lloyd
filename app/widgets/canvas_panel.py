from PyQt6.QtCore import QEvent, QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from app.config import (
    MIC_BUTTON_LOADING_TEXT, MUTE_BUTTON_ICON_MUTED, MUTE_BUTTON_ICON_UNMUTED,
    MUTE_BUTTON_MARGIN, MUTE_BUTTON_SIZE, OBJECT_NAME_CANVAS_PANEL,
    OBJECT_NAME_MIC_TOGGLE_BUTTON, OBJECT_NAME_MUTE_BUTTON, TTS_VOLUME_PERCENT_DEFAULT,
    TTS_VOLUME_PERCENT_MAX, TTS_VOLUME_PERCENT_MIN, VOLUME_POPUP_GAP,
    VOLUME_POPUP_HIDE_DELAY_MS,
)
from app.widgets.sphere_widget import SphereWidget
from app.widgets.volume_popup import VolumePopup


class CanvasPanel(QWidget):
    volume_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(OBJECT_NAME_CANVAS_PANEL)

        self._last_audible_volume = TTS_VOLUME_PERCENT_DEFAULT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sphere = SphereWidget(self)
        layout.addWidget(self.sphere)

        self.mic_toggle_button = QPushButton(MIC_BUTTON_LOADING_TEXT, self)
        self.mic_toggle_button.setObjectName(OBJECT_NAME_MIC_TOGGLE_BUTTON)
        self.mic_toggle_button.setCheckable(True)
        self.mic_toggle_button.setEnabled(False)
        layout.addWidget(self.mic_toggle_button)

        self.mute_button = QPushButton(MUTE_BUTTON_ICON_UNMUTED, self)
        self.mute_button.setObjectName(OBJECT_NAME_MUTE_BUTTON)
        self.mute_button.setCheckable(True)
        self.mute_button.setFixedSize(MUTE_BUTTON_SIZE, MUTE_BUTTON_SIZE)
        self.mute_button.toggled.connect(self._on_mute_button_toggled)
        self.mute_button.installEventFilter(self)
        self.mute_button.raise_()

        self.volume_popup = VolumePopup(self)
        self.volume_popup.volume_changed.connect(self._on_volume_changed)
        self.volume_popup.hover_entered.connect(self._cancel_volume_popup_hide)
        self.volume_popup.hover_left.connect(self._schedule_volume_popup_hide)

        self._volume_popup_hide_timer = QTimer(self)
        self._volume_popup_hide_timer.setSingleShot(True)
        self._volume_popup_hide_timer.setInterval(VOLUME_POPUP_HIDE_DELAY_MS)
        self._volume_popup_hide_timer.timeout.connect(self._hide_volume_popup)

    def volume(self) -> int:
        return self.volume_popup.value()

    def set_volume(self, percent: int) -> None:
        percent = max(TTS_VOLUME_PERCENT_MIN, min(TTS_VOLUME_PERCENT_MAX, percent))
        self.volume_popup.set_value(percent)
        self._on_volume_changed(percent)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.mute_button:
            if event.type() == QEvent.Type.Enter:
                self._show_volume_popup()
            elif event.type() == QEvent.Type.Leave:
                self._schedule_volume_popup_hide()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        sphere_rect = self.sphere.geometry()
        x = sphere_rect.right() - MUTE_BUTTON_SIZE - MUTE_BUTTON_MARGIN
        y = sphere_rect.bottom() - MUTE_BUTTON_SIZE - MUTE_BUTTON_MARGIN
        self.mute_button.move(x, y)
        self.mute_button.raise_()
        self._position_volume_popup()
        self.volume_popup.raise_()

    def _on_mute_button_toggled(self, checked: bool) -> None:
        self.mute_button.setText(MUTE_BUTTON_ICON_MUTED if checked else MUTE_BUTTON_ICON_UNMUTED)
        if not checked and self.volume_popup.value() == TTS_VOLUME_PERCENT_MIN:
            self.set_volume(self._last_audible_volume)

    def _on_volume_changed(self, percent: int) -> None:
        if percent > TTS_VOLUME_PERCENT_MIN:
            self._last_audible_volume = percent
        self.mute_button.setChecked(percent == TTS_VOLUME_PERCENT_MIN)
        self.volume_changed.emit(percent)

    def _show_volume_popup(self) -> None:
        self._volume_popup_hide_timer.stop()
        self._position_volume_popup()
        self.volume_popup.show()
        self.volume_popup.raise_()

    def _hide_volume_popup(self) -> None:
        if self.volume_popup.is_adjusting():
            return
        self.volume_popup.hide()

    def _schedule_volume_popup_hide(self) -> None:
        self._volume_popup_hide_timer.start()

    def _cancel_volume_popup_hide(self) -> None:
        self._volume_popup_hide_timer.stop()

    def _position_volume_popup(self) -> None:
        button_rect = self.mute_button.geometry()
        x = button_rect.center().x() - self.volume_popup.width() // 2
        y = button_rect.top() - self.volume_popup.height() - VOLUME_POPUP_GAP
        self.volume_popup.move(x, y)