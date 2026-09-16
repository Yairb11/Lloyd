import math
from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QTimer, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QRadialGradient
from PyQt6.QtWidgets import QWidget

from app.config import (
    SPHERE_BASE_RADIUS,
    SPHERE_COLOR_LISTENING,
    SPHERE_COLOR_SPEAKING,
    SPHERE_COLOR_START,
    SPHERE_COLOR_THINKING,
    SPHERE_COLOR_TRANSITION_DURATION_MS,
    SPHERE_CORE_LIGHTEN,
    SPHERE_EDGE_ALPHA,
    SPHERE_FRAME_INTERVAL_MS,
    SPHERE_GRADIENT_STOP_CORE,
    SPHERE_GRADIENT_STOP_EDGE,
    SPHERE_GRADIENT_STOP_MID,
    SPHERE_GROW_SHRINK_DURATION_MS,
    SPHERE_HUE_CYCLE_SPEED,
    SPHERE_IDLE_HUE_SATURATION,
    SPHERE_IDLE_HUE_VALUE,
    SPHERE_LISTENING_GROWTH,
    SPHERE_MAX_RADIUS,
    SPHERE_MIN_RADIUS,
    SPHERE_MIN_RENDER_RADIUS,
    SPHERE_ORBIT_HIGHLIGHT_LIGHTEN,
    SPHERE_PULSE_AMPLITUDE,
    SPHERE_PULSE_SPEED,
    SPHERE_SPEAKING_AMPLITUDE_GROWTH,
    SPHERE_SPEAKING_IDLE_BREATH_AMPLITUDE,
    SPHERE_SPEAKING_SMOOTHING_FALL,
    SPHERE_SPEAKING_SMOOTHING_RISE,
    SPHERE_THINKING_ORBIT_DOT_RADIUS,
    SPHERE_THINKING_ORBIT_RADIUS_RATIO,
    SPHERE_THINKING_ORBIT_SPEED,
    SPHERE_THINKING_PULSE_AMPLITUDE_MULTIPLIER,
    SPHERE_THINKING_PULSE_SPEED_MULTIPLIER,
    SPHERE_WIDGET_MIN_SIZE,
)

ColorLike = QColor | str | Qt.GlobalColor

class SphereMode:
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class SphereWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(SPHERE_WIDGET_MIN_SIZE, SPHERE_WIDGET_MIN_SIZE)

        self._mode: str = SphereMode.IDLE

        self._base_radius: float = SPHERE_BASE_RADIUS
        self._phase: float = 0.0
        self._hue_phase: float = 0.0
        self._color_locked: bool = False
        self._color: QColor = QColor(SPHERE_COLOR_START)

        self._pulse_speed: float = SPHERE_PULSE_SPEED
        self._pulse_amplitude: float = SPHERE_PULSE_AMPLITUDE

        self._orbit_angle: float = 0.0

        self._speaking_amplitude_target: float = 0.0
        self._speaking_amplitude_smoothed: float = 0.0

        self._radius_animation = QPropertyAnimation(self, b"baseRadius", self)
        self._radius_animation.setDuration(SPHERE_GROW_SHRINK_DURATION_MS)
        self._radius_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._color_animation = QPropertyAnimation(self, b"color", self)
        self._color_animation.setDuration(SPHERE_COLOR_TRANSITION_DURATION_MS)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._timer = QTimer(self)
        self._timer.setInterval(SPHERE_FRAME_INTERVAL_MS)
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
        delta = SPHERE_PULSE_AMPLITUDE if amount is None else amount
        target = min(self._base_radius + delta, SPHERE_MAX_RADIUS)
        self._animate_radius_to(target)

    def shrink(self, amount: float | None = None) -> None:
        delta = SPHERE_PULSE_AMPLITUDE if amount is None else amount
        target = max(self._base_radius - delta, SPHERE_MIN_RADIUS)
        self._animate_radius_to(target)

    def set_color(self, color: ColorLike) -> None:
        self._color_locked = True
        self._color_animation.stop()
        self._color_animation.setStartValue(QColor(self._color))
        self._color_animation.setEndValue(QColor(color))
        self._color_animation.start()

    def release_color(self) -> None:
        self._color_locked = False

    def enter_idle(self) -> None:
        self._mode = SphereMode.IDLE
        self._pulse_speed = SPHERE_PULSE_SPEED
        self._pulse_amplitude = SPHERE_PULSE_AMPLITUDE
        self._speaking_amplitude_target = 0.0
        self._speaking_amplitude_smoothed = 0.0
        self.release_color()
        self._animate_radius_to(SPHERE_BASE_RADIUS)

    def enter_listening(self) -> None:
        self._mode = SphereMode.LISTENING
        self.set_color(SPHERE_COLOR_LISTENING)
        target = min(SPHERE_BASE_RADIUS + SPHERE_LISTENING_GROWTH, SPHERE_MAX_RADIUS)
        self._animate_radius_to(target)

    def enter_thinking(self) -> None:
        self._mode = SphereMode.THINKING
        self._pulse_speed = SPHERE_PULSE_SPEED * SPHERE_THINKING_PULSE_SPEED_MULTIPLIER
        self._pulse_amplitude = SPHERE_PULSE_AMPLITUDE * SPHERE_THINKING_PULSE_AMPLITUDE_MULTIPLIER
        self._orbit_angle = 0.0
        self.set_color(SPHERE_COLOR_THINKING)
        self._animate_radius_to(SPHERE_BASE_RADIUS)

    def enter_speaking(self) -> None:
        self._mode = SphereMode.SPEAKING
        self.set_color(SPHERE_COLOR_SPEAKING)
        self._speaking_amplitude_target = 0.0
        self._speaking_amplitude_smoothed = 0.0
        self._animate_radius_to(SPHERE_BASE_RADIUS)

    def update_speaking_amplitude(self, level: float) -> None:
        if self._mode != SphereMode.SPEAKING:
            return
        self._speaking_amplitude_target = max(0.0, min(1.0, level))

    def _animate_radius_to(self, target: float, duration_ms: int | None = None) -> None:
        self._radius_animation.stop()
        self._radius_animation.setDuration(
            SPHERE_GROW_SHRINK_DURATION_MS if duration_ms is None else duration_ms
        )
        self._radius_animation.setStartValue(self._base_radius)
        self._radius_animation.setEndValue(target)
        self._radius_animation.start()

    def _on_tick(self) -> None:
        step = SPHERE_FRAME_INTERVAL_MS / 1000.0
        self._phase += self._pulse_speed * step

        if not self._color_locked:
            self._hue_phase = (self._hue_phase + SPHERE_HUE_CYCLE_SPEED * step) % 360
            self._color = QColor.fromHsv(int(self._hue_phase), SPHERE_IDLE_HUE_SATURATION, SPHERE_IDLE_HUE_VALUE)

        if self._mode == SphereMode.THINKING:
            self._orbit_angle = (self._orbit_angle + SPHERE_THINKING_ORBIT_SPEED * step) % 360

        if self._mode == SphereMode.SPEAKING:
            rising = self._speaking_amplitude_target > self._speaking_amplitude_smoothed
            rate = SPHERE_SPEAKING_SMOOTHING_RISE if rising else SPHERE_SPEAKING_SMOOTHING_FALL
            self._speaking_amplitude_smoothed += (
                self._speaking_amplitude_target - self._speaking_amplitude_smoothed
            ) * rate

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._mode == SphereMode.SPEAKING:
            offset = SPHERE_SPEAKING_IDLE_BREATH_AMPLITUDE * math.sin(self._phase)
            offset += self._speaking_amplitude_smoothed * SPHERE_SPEAKING_AMPLITUDE_GROWTH
        else:
            offset = math.sin(self._phase) * self._pulse_amplitude

        radius = max(self._base_radius + offset, SPHERE_MIN_RENDER_RADIUS)

        center_x = self.width() / 2
        center_y = self.height() / 2

        core = QColor(self._color).lighter(SPHERE_CORE_LIGHTEN)
        edge = QColor(self._color)
        edge.setAlpha(SPHERE_EDGE_ALPHA)

        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(SPHERE_GRADIENT_STOP_CORE, core)
        gradient.setColorAt(SPHERE_GRADIENT_STOP_MID, self._color)
        gradient.setColorAt(SPHERE_GRADIENT_STOP_EDGE, edge)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(
            int(center_x - radius),
            int(center_y - radius),
            int(radius * 2),
            int(radius * 2),
        )

        if self._mode == SphereMode.THINKING:
            self._paint_orbit_highlight(painter, center_x, center_y, radius)

    def _paint_orbit_highlight(self, painter: QPainter, center_x: float, center_y: float, radius: float) -> None:
        angle_rad = math.radians(self._orbit_angle)
        orbit_radius = radius * SPHERE_THINKING_ORBIT_RADIUS_RATIO
        dot_x = center_x + math.cos(angle_rad) * orbit_radius
        dot_y = center_y + math.sin(angle_rad) * orbit_radius
        dot_radius = SPHERE_THINKING_ORBIT_DOT_RADIUS

        painter.setBrush(QColor(self._color).lighter(SPHERE_ORBIT_HIGHLIGHT_LIGHTEN))
        painter.drawEllipse(
            int(dot_x - dot_radius),
            int(dot_y - dot_radius),
            int(dot_radius * 2),
            int(dot_radius * 2),
        )