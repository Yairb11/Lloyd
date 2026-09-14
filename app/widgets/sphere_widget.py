import math

from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QTimer, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QRadialGradient
from PyQt6.QtWidgets import QWidget

from app import config

ColorLike = QColor | str | Qt.GlobalColor


class SphereWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 200)

        self._base_radius: float = config.SPHERE_BASE_RADIUS
        self._phase: float = 0.0
        self._hue_phase: float = 0.0
        self._color_locked: bool = False
        self._color: QColor = QColor(config.SPHERE_COLOR_START)

        self._radius_animation = QPropertyAnimation(self, b"baseRadius", self)
        self._radius_animation.setDuration(config.SPHERE_GROW_SHRINK_DURATION_MS)
        self._radius_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._color_animation = QPropertyAnimation(self, b"color", self)
        self._color_animation.setDuration(config.SPHERE_COLOR_TRANSITION_DURATION_MS)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._timer = QTimer(self)
        self._timer.setInterval(config.SPHERE_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def get_base_radius(self) -> float:
        return self._base_radius

    def set_base_radius(self, value: float) -> None:
        self._base_radius = value
        self.update()

    baseRadius = pyqtProperty(float, get_base_radius, set_base_radius)

    def get_color(self) -> QColor:
        return self._color

    def set_color_property(self, value: QColor) -> None:
        self._color = QColor(value)
        self.update()

    color = pyqtProperty(QColor, get_color, set_color_property)

    def grow(self, amount: float | None = None) -> None:
        delta = config.SPHERE_PULSE_AMPLITUDE if amount is None else amount
        target = min(self._base_radius + delta, config.SPHERE_MAX_RADIUS)
        self._animate_radius_to(target)

    def shrink(self, amount: float | None = None) -> None:
        delta = config.SPHERE_PULSE_AMPLITUDE if amount is None else amount
        target = max(self._base_radius - delta, config.SPHERE_MIN_RADIUS)
        self._animate_radius_to(target)

    def set_color(self, color: ColorLike) -> None:
        self._color_locked = True
        self._color_animation.stop()
        self._color_animation.setStartValue(QColor(self._color))
        self._color_animation.setEndValue(QColor(color))
        self._color_animation.start()

    def release_color(self) -> None:
        self._color_locked = False

    def _animate_radius_to(self, target: float) -> None:
        self._radius_animation.stop()
        self._radius_animation.setStartValue(self._base_radius)
        self._radius_animation.setEndValue(target)
        self._radius_animation.start()

    def _on_tick(self) -> None:
        step = config.SPHERE_FRAME_INTERVAL_MS / 1000.0
        self._phase += config.SPHERE_PULSE_SPEED * step
        if not self._color_locked:
            self._hue_phase = (self._hue_phase + config.SPHERE_HUE_CYCLE_SPEED * step) % 360
            self._color = QColor.fromHsv(int(self._hue_phase), 160, 255)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pulse = math.sin(self._phase) * config.SPHERE_PULSE_AMPLITUDE
        radius = max(self._base_radius + pulse, 10.0)

        center_x = self.width() / 2
        center_y = self.height() / 2

        core = QColor(self._color).lighter(140)
        edge = QColor(self._color)
        edge.setAlpha(20)

        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0.0, core)
        gradient.setColorAt(0.6, self._color)
        gradient.setColorAt(1.0, edge)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(
            int(center_x - radius),
            int(center_y - radius),
            int(radius * 2),
            int(radius * 2),
        )