import math
import random

from PyQt6.QtCore import QElapsedTimer, QPointF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush, QColor, QConicalGradient, QPainter, QPainterPath, QPaintEvent, QPen, QRadialGradient,
)
from PyQt6.QtWidgets import QWidget

from app.config import (
    SPHERE_BASE_RADIUS, SPHERE_BODY_FOCAL_OFFSET, SPHERE_BODY_HIGHLIGHT_LIGHTEN,
    SPHERE_BODY_STOP_MID, SPHERE_BODY_WAVES, SPHERE_CHROMATIC_COLORS,
    SPHERE_CHROMATIC_RING_LAYERS, SPHERE_CHROMATIC_RING_RADIUS, SPHERE_CHROMATIC_SPIN_SPEED_DEG,
    SPHERE_CORE_MID_ALPHA_RATIO, SPHERE_CORE_STOP_MID, SPHERE_DEFORMATION_THRESHOLD,
    SPHERE_DRIFT_PERIOD_S, SPHERE_FRAME_INTERVAL_MS, SPHERE_HALO_FALLOFF_ALPHA_RATIO,
    SPHERE_HALO_FALLOFF_STOP, SPHERE_HALO_VOICE_BOOST, SPHERE_HUM_WAVES,
    SPHERE_INHALE_RATIO_LIMITS, SPHERE_LOOK_DEFAULT, SPHERE_LOOK_LISTENING,
    SPHERE_LOOK_RENDERING, SPHERE_LOOK_SPEAKING, SPHERE_LOOK_THINKING,
    SPHERE_MAX_BODY_SCALE, SPHERE_MAX_FRAME_DELTA_S, SPHERE_MIN_TIME_CONSTANT_S,
    SPHERE_MOTE_COLOR, SPHERE_MOTE_END_DISTANCE, SPHERE_MOTE_FADE_GAIN,
    SPHERE_MOTE_GLOW_RATIO, SPHERE_MOTE_MAX_COUNT, SPHERE_MOTE_SIZE,
    SPHERE_MOTE_SPAWN_PER_S, SPHERE_MOTE_SPEED, SPHERE_MOTE_SPIRAL_MIN_DISTANCE,
    SPHERE_MOTE_SPIRAL_SPEED, SPHERE_MOTE_START_DISTANCE, SPHERE_NODE_ELLIPSE_RATIO,
    SPHERE_NODE_GLOW_RATIO, SPHERE_NODE_HEAD_LIGHTEN, SPHERE_NODE_PRECESSION_SPEED,
    SPHERE_NODE_RADIUS_RATIO, SPHERE_NODE_TRAIL_ALPHA, SPHERE_NODE_TRAIL_MIN_SIZE_RATIO,
    SPHERE_NODE_TRAIL_REFERENCE_SPEED, SPHERE_NODE_TRAIL_SEGMENTS, SPHERE_NODE_TRAIL_SPACING,
    SPHERE_OUTLINE_SEGMENTS, SPHERE_RIM_EDGE_ALPHA_RATIO, SPHERE_RIM_STOP_PEAK,
    SPHERE_RIM_STOP_START, SPHERE_RIM_VOICE_BOOST, SPHERE_RIPPLE_WAVES,
    SPHERE_SMOKE_COLOR, SPHERE_SMOKE_STOP_START, SPHERE_SPECULAR_ALPHA,
    SPHERE_SPECULAR_COLOR, SPHERE_SPECULAR_OFFSET, SPHERE_SPECULAR_ROTATION_DEG,
    SPHERE_SPECULAR_SIZE, SPHERE_SWIRL_BLOBS, SPHERE_SWIRL_TILT,
    SPHERE_SWIRL_WOBBLE, SPHERE_SWIRL_WOBBLE_SPEED, SPHERE_VIEWPORT_FILL,
    SPHERE_VISIBILITY_THRESHOLD, SPHERE_VOICE_ENVELOPE_S, SPHERE_VOICE_FALL_S,
    SPHERE_VOICE_RISE_S, SPHERE_VOICE_TRANSIENT_GAIN, SPHERE_WIDGET_MIN_SIZE,
)

FULL_TURN: float = 2.0 * math.pi

LOOK_FIELDS: tuple[str, ...] = (
    "scale_min", "scale_max", "breath_period_s", "inhale_ratio", "drift_px",
    "body_color", "edge_color", "edge_alpha",
    "core_color", "core_intensity", "core_extent",
    "rim_color", "rim_alpha",
    "halo_color", "halo_alpha", "halo_extent",
    "chromatic", "smoke",
    "swirl", "swirl_speed", "swirl_light", "swirl_dark",
    "nodes", "node_orbit", "node_speed", "node_color",
    "motes", "hum",
    "voice_expansion", "voice_body", "voice_ripple",
    "transition_s",
)


class SphereMode:
    DEFAULT = "default"
    LISTENING = "listening"
    THINKING = "thinking"
    RENDERING = "rendering"
    SPEAKING = "speaking"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _ease(progress: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * _clamp(progress))


def _approach_amount(delta_s: float, time_constant_s: float) -> float:
    return 1.0 - math.exp(-delta_s / max(time_constant_s, SPHERE_MIN_TIME_CONSTANT_S))


def _breath_wave(cycle: float, inhale_ratio: float) -> float:
    inhale = _clamp(inhale_ratio, *SPHERE_INHALE_RATIO_LIMITS)
    if cycle < inhale:
        return _ease(cycle / inhale)
    return 1.0 - _ease((cycle - inhale) / (1.0 - inhale))


def _wave_sum(waves: tuple[tuple[int, float, float, float], ...], theta: float, time_s: float) -> float:
    return sum(
        weight * math.sin(lobes * theta + speed * time_s + phase)
        for lobes, speed, weight, phase in waves
    )


def _with_alpha(color: QColor, alpha: float) -> QColor:
    tinted = QColor(color)
    tinted.setAlphaF(_clamp(alpha))
    return tinted


def _mix(current: float | QColor, goal: float | QColor, amount: float) -> float | QColor:
    if isinstance(goal, QColor):
        return QColor.fromRgbF(
            current.redF() + (goal.redF() - current.redF()) * amount,
            current.greenF() + (goal.greenF() - current.greenF()) * amount,
            current.blueF() + (goal.blueF() - current.blueF()) * amount,
            current.alphaF() + (goal.alphaF() - current.alphaF()) * amount,
        )
    return current + (goal - current) * amount


def _paint_glow(painter: QPainter, point: QPointF, radius: float, color: QColor, alpha: float) -> None:
    gradient = QRadialGradient(point, radius)
    gradient.setColorAt(0.0, _with_alpha(color, alpha))
    gradient.setColorAt(1.0, _with_alpha(color, 0.0))
    painter.setBrush(QBrush(gradient))
    painter.drawEllipse(point, radius, radius)


class SphereLook:
    __slots__ = LOOK_FIELDS

    def __init__(self, values: dict[str, float | str]) -> None:
        for name in LOOK_FIELDS:
            value = values[name]
            setattr(self, name, QColor(value) if isinstance(value, str) else float(value))

    def copy(self) -> "SphereLook":
        clone = SphereLook.__new__(SphereLook)
        for name in LOOK_FIELDS:
            value = getattr(self, name)
            setattr(clone, name, QColor(value) if isinstance(value, QColor) else value)
        return clone

    def approach(self, target: "SphereLook", amount: float) -> None:
        for name in LOOK_FIELDS:
            setattr(self, name, _mix(getattr(self, name), getattr(target, name), amount))


class Mote:
    __slots__ = ("angle", "distance", "speed", "size")

    def __init__(self, angle: float, distance: float, speed: float, size: float) -> None:
        self.angle = angle
        self.distance = distance
        self.speed = speed
        self.size = size


class SphereWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(SPHERE_WIDGET_MIN_SIZE, SPHERE_WIDGET_MIN_SIZE)

        self._looks: dict[str, SphereLook] = {
            SphereMode.DEFAULT: SphereLook(SPHERE_LOOK_DEFAULT),
            SphereMode.LISTENING: SphereLook(SPHERE_LOOK_LISTENING),
            SphereMode.THINKING: SphereLook(SPHERE_LOOK_THINKING),
            SphereMode.RENDERING: SphereLook(SPHERE_LOOK_RENDERING),
            SphereMode.SPEAKING: SphereLook(SPHERE_LOOK_SPEAKING),
        }
        self._mode: str = SphereMode.DEFAULT
        self._target: SphereLook = self._looks[self._mode]
        self._look: SphereLook = self._target.copy()

        self._smoke_color = QColor(SPHERE_SMOKE_COLOR)
        self._specular_color = QColor(SPHERE_SPECULAR_COLOR)
        self._mote_color = QColor(SPHERE_MOTE_COLOR)
        self._chromatic_colors = [QColor(color) for color in SPHERE_CHROMATIC_COLORS]

        self._time_s: float = 0.0
        self._breath_cycle: float = 0.0
        self._swirl_phase: float = 0.0
        self._node_angle: float = 0.0
        self._node_precession: float = 0.0

        self._voice_target: float = 0.0
        self._voice_fast: float = 0.0
        self._voice_slow: float = 0.0

        self._rng = random.Random()
        self._motes: list[Mote] = []
        self._mote_budget: float = 0.0

        self._clock = QElapsedTimer()
        self._clock.start()

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(SPHERE_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def enter_default(self) -> None:
        self._enter(SphereMode.DEFAULT)

    def enter_listening(self) -> None:
        self._enter(SphereMode.LISTENING)

    def enter_thinking(self) -> None:
        self._enter(SphereMode.THINKING)

    def enter_rendering(self) -> None:
        self._enter(SphereMode.RENDERING)

    def enter_speaking(self) -> None:
        self._enter(SphereMode.SPEAKING)

    def update_listening_amplitude(self, level: float) -> None:
        self._feed_voice(SphereMode.LISTENING, level)

    def update_speaking_amplitude(self, level: float) -> None:
        self._feed_voice(SphereMode.SPEAKING, level)

    def _enter(self, mode: str) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self._target = self._looks[mode]
        self._voice_target = 0.0

    def _feed_voice(self, mode: str, level: float) -> None:
        if self._mode == mode:
            self._voice_target = _clamp(level)

    def _voice_transient(self) -> float:
        return max(0.0, self._voice_fast - self._voice_slow) * SPHERE_VOICE_TRANSIENT_GAIN

    def _on_tick(self) -> None:
        delta_s = min(self._clock.restart() / 1000.0, SPHERE_MAX_FRAME_DELTA_S)
        self._time_s += delta_s
        self._look.approach(self._target, _approach_amount(delta_s, self._target.transition_s))

        look = self._look
        breath_step = delta_s / max(look.breath_period_s, SPHERE_MIN_TIME_CONSTANT_S)
        self._breath_cycle = (self._breath_cycle + breath_step) % 1.0
        self._swirl_phase += look.swirl_speed * delta_s
        self._node_angle += look.node_speed * delta_s
        self._node_precession += SPHERE_NODE_PRECESSION_SPEED * delta_s

        self._advance_voice(delta_s)
        self._advance_motes(delta_s)
        self.update()

    def _advance_voice(self, delta_s: float) -> None:
        rising = self._voice_target > self._voice_fast
        response_s = SPHERE_VOICE_RISE_S if rising else SPHERE_VOICE_FALL_S
        self._voice_fast += (self._voice_target - self._voice_fast) * _approach_amount(delta_s, response_s)
        self._voice_slow += (self._voice_fast - self._voice_slow) * _approach_amount(
            delta_s, SPHERE_VOICE_ENVELOPE_S
        )

    def _advance_motes(self, delta_s: float) -> None:
        self._mote_budget += SPHERE_MOTE_SPAWN_PER_S * self._look.motes * delta_s
        while self._mote_budget >= 1.0:
            self._mote_budget -= 1.0
            if len(self._motes) < SPHERE_MOTE_MAX_COUNT:
                self._motes.append(self._spawn_mote())

        for mote in self._motes:
            mote.distance -= mote.speed * delta_s
            spiral_distance = max(mote.distance, SPHERE_MOTE_SPIRAL_MIN_DISTANCE)
            mote.angle += SPHERE_MOTE_SPIRAL_SPEED * delta_s / spiral_distance
        self._motes = [mote for mote in self._motes if mote.distance > SPHERE_MOTE_END_DISTANCE]

    def _spawn_mote(self) -> Mote:
        return Mote(
            angle=self._rng.uniform(0.0, FULL_TURN),
            distance=self._rng.uniform(*SPHERE_MOTE_START_DISTANCE),
            speed=self._rng.uniform(*SPHERE_MOTE_SPEED),
            size=self._rng.uniform(*SPHERE_MOTE_SIZE),
        )

    def _radius_unit(self) -> float:
        available = min(self.width(), self.height()) / 2.0
        return min(SPHERE_BASE_RADIUS, available * SPHERE_VIEWPORT_FILL / SPHERE_MAX_BODY_SCALE)

    def _current_scale(self) -> float:
        look = self._look
        breath = _breath_wave(self._breath_cycle, look.inhale_ratio)
        scale = look.scale_min + (look.scale_max - look.scale_min) * breath
        return scale + look.voice_expansion * self._voice_slow

    def paintEvent(self, event: QPaintEvent) -> None:
        look = self._look
        radius = self._radius_unit() * self._current_scale()
        drift = look.drift_px * math.sin(FULL_TURN * self._time_s / SPHERE_DRIFT_PERIOD_S)
        center = QPointF(self.width() / 2.0, self.height() / 2.0 + drift)
        outline = self._build_outline(center, radius)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        self._paint_halo(painter, center, radius)
        self._paint_chromatic_ring(painter, center, radius)
        self._paint_body(painter, outline, center, radius)

        painter.save()
        painter.setClipPath(outline)
        self._paint_swirl(painter, center, radius)
        self._paint_core(painter, center, radius)
        self._paint_smoke(painter, center, radius)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        self._paint_nodes(painter, center, radius)
        self._paint_motes(painter, center, radius)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        self._paint_rim(painter, center, radius)
        self._paint_specular(painter, center, radius)
        painter.restore()
        painter.end()

    def _build_outline(self, center: QPointF, radius: float) -> QPainterPath:
        look = self._look
        layers = [
            (level, waves)
            for level, waves in (
                (look.voice_body * self._voice_slow, SPHERE_BODY_WAVES),
                (look.voice_ripple * (self._voice_fast + self._voice_transient()), SPHERE_RIPPLE_WAVES),
                (look.hum, SPHERE_HUM_WAVES),
            )
            if level > SPHERE_DEFORMATION_THRESHOLD
        ]

        path = QPainterPath()
        for index in range(SPHERE_OUTLINE_SEGMENTS):
            theta = FULL_TURN * index / SPHERE_OUTLINE_SEGMENTS
            offset = sum(level * _wave_sum(waves, theta, self._time_s) for level, waves in layers)
            distance = radius * (1.0 + offset)
            point = QPointF(center.x() + math.cos(theta) * distance, center.y() + math.sin(theta) * distance)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        return path

    def _paint_halo(self, painter: QPainter, center: QPointF, radius: float) -> None:
        look = self._look
        alpha = look.halo_alpha * (1.0 + SPHERE_HALO_VOICE_BOOST * self._voice_slow)
        if alpha < SPHERE_VISIBILITY_THRESHOLD:
            return

        extent = max(look.halo_extent, 1.0 + SPHERE_VISIBILITY_THRESHOLD)
        outer = radius * extent
        edge_stop = 1.0 / extent
        falloff_stop = edge_stop + (1.0 - edge_stop) * SPHERE_HALO_FALLOFF_STOP

        gradient = QRadialGradient(center, outer)
        gradient.setColorAt(0.0, _with_alpha(look.halo_color, alpha))
        gradient.setColorAt(edge_stop, _with_alpha(look.halo_color, alpha))
        gradient.setColorAt(falloff_stop, _with_alpha(look.halo_color, alpha * SPHERE_HALO_FALLOFF_ALPHA_RATIO))
        gradient.setColorAt(1.0, _with_alpha(look.halo_color, 0.0))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, outer, outer)

    def _paint_chromatic_ring(self, painter: QPainter, center: QPointF, radius: float) -> None:
        strength = self._look.chromatic
        if strength < SPHERE_VISIBILITY_THRESHOLD:
            return

        gradient = QConicalGradient(center, (self._time_s * SPHERE_CHROMATIC_SPIN_SPEED_DEG) % 360.0)
        last_index = len(self._chromatic_colors) - 1
        for index, color in enumerate(self._chromatic_colors):
            gradient.setColorAt(index / last_index, color)

        ring_radius = radius * SPHERE_CHROMATIC_RING_RADIUS
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for width_ratio, alpha in SPHERE_CHROMATIC_RING_LAYERS:
            painter.setOpacity(strength * alpha)
            painter.setPen(QPen(QBrush(gradient), radius * width_ratio))
            painter.drawEllipse(center, ring_radius, ring_radius)
        painter.restore()

    def _paint_body(self, painter: QPainter, outline: QPainterPath, center: QPointF, radius: float) -> None:
        look = self._look
        focal = QPointF(
            center.x() + radius * SPHERE_BODY_FOCAL_OFFSET[0],
            center.y() + radius * SPHERE_BODY_FOCAL_OFFSET[1],
        )
        gradient = QRadialGradient(center, radius, focal)
        gradient.setColorAt(0.0, look.body_color.lighter(SPHERE_BODY_HIGHLIGHT_LIGHTEN))
        gradient.setColorAt(SPHERE_BODY_STOP_MID, look.body_color)
        gradient.setColorAt(1.0, _with_alpha(look.edge_color, look.edge_alpha))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(outline)

    def _paint_swirl(self, painter: QPainter, center: QPointF, radius: float) -> None:
        look = self._look
        if look.swirl < SPHERE_VISIBILITY_THRESHOLD:
            return

        for orbit, size, speed, offset, light, alpha in SPHERE_SWIRL_BLOBS:
            angle = self._swirl_phase * speed + offset
            wobble = 1.0 + SPHERE_SWIRL_WOBBLE * math.sin(self._time_s * SPHERE_SWIRL_WOBBLE_SPEED + offset)
            distance = radius * orbit * wobble
            point = QPointF(
                center.x() + math.cos(angle) * distance,
                center.y() + math.sin(angle) * distance * SPHERE_SWIRL_TILT,
            )
            color = look.swirl_light if light else look.swirl_dark
            _paint_glow(painter, point, radius * size, color, look.swirl * alpha)

    def _paint_core(self, painter: QPainter, center: QPointF, radius: float) -> None:
        look = self._look
        if look.core_intensity < SPHERE_VISIBILITY_THRESHOLD:
            return

        extent = radius * look.core_extent
        gradient = QRadialGradient(center, extent)
        gradient.setColorAt(0.0, _with_alpha(look.core_color, look.core_intensity))
        gradient.setColorAt(
            SPHERE_CORE_STOP_MID,
            _with_alpha(look.core_color, look.core_intensity * SPHERE_CORE_MID_ALPHA_RATIO),
        )
        gradient.setColorAt(1.0, _with_alpha(look.core_color, 0.0))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, extent, extent)

    def _paint_smoke(self, painter: QPainter, center: QPointF, radius: float) -> None:
        strength = self._look.smoke
        if strength < SPHERE_VISIBILITY_THRESHOLD:
            return

        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, _with_alpha(self._smoke_color, 0.0))
        gradient.setColorAt(SPHERE_SMOKE_STOP_START, _with_alpha(self._smoke_color, 0.0))
        gradient.setColorAt(1.0, _with_alpha(self._smoke_color, strength))
        painter.setBrush(QBrush(gradient))
        extent = radius * SPHERE_MAX_BODY_SCALE
        painter.drawEllipse(center, extent, extent)

    def _paint_nodes(self, painter: QPainter, center: QPointF, radius: float) -> None:
        look = self._look
        if look.nodes < SPHERE_VISIBILITY_THRESHOLD:
            return

        semi_major = radius * look.node_orbit
        semi_minor = semi_major * SPHERE_NODE_ELLIPSE_RATIO
        cos_tilt = math.cos(self._node_precession)
        sin_tilt = math.sin(self._node_precession)
        node_radius = radius * SPHERE_NODE_RADIUS_RATIO
        spacing = SPHERE_NODE_TRAIL_SPACING * look.node_speed / SPHERE_NODE_TRAIL_REFERENCE_SPEED
        head_color = look.node_color.lighter(SPHERE_NODE_HEAD_LIGHTEN)

        for partner_offset in (0.0, math.pi):
            for step in range(SPHERE_NODE_TRAIL_SEGMENTS, -1, -1):
                fade = 1.0 - step / (SPHERE_NODE_TRAIL_SEGMENTS + 1)
                angle = self._node_angle + partner_offset - step * spacing
                x = math.cos(angle) * semi_major
                y = math.sin(angle) * semi_minor
                point = QPointF(
                    center.x() + x * cos_tilt - y * sin_tilt,
                    center.y() + x * sin_tilt + y * cos_tilt,
                )
                size = node_radius * (
                    SPHERE_NODE_TRAIL_MIN_SIZE_RATIO + (1.0 - SPHERE_NODE_TRAIL_MIN_SIZE_RATIO) * fade
                )
                if step == 0:
                    _paint_glow(painter, point, size * SPHERE_NODE_GLOW_RATIO, look.node_color, look.nodes)
                    _paint_glow(painter, point, size, head_color, look.nodes)
                else:
                    alpha = look.nodes * SPHERE_NODE_TRAIL_ALPHA * fade
                    _paint_glow(painter, point, size * SPHERE_NODE_GLOW_RATIO, look.node_color, alpha)

    def _paint_motes(self, painter: QPainter, center: QPointF, radius: float) -> None:
        strength = self._look.motes
        if strength < SPHERE_VISIBILITY_THRESHOLD or not self._motes:
            return

        for mote in self._motes:
            distance = radius * mote.distance
            point = QPointF(
                center.x() + math.cos(mote.angle) * distance,
                center.y() + math.sin(mote.angle) * distance,
            )
            alpha = strength * _clamp((1.0 - mote.distance) * SPHERE_MOTE_FADE_GAIN)
            _paint_glow(painter, point, mote.size * SPHERE_MOTE_GLOW_RATIO, self._mote_color, alpha)

    def _paint_rim(self, painter: QPainter, center: QPointF, radius: float) -> None:
        look = self._look
        alpha = look.rim_alpha * (1.0 + SPHERE_RIM_VOICE_BOOST * self._voice_fast)
        if alpha < SPHERE_VISIBILITY_THRESHOLD:
            return

        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, _with_alpha(look.rim_color, 0.0))
        gradient.setColorAt(SPHERE_RIM_STOP_START, _with_alpha(look.rim_color, 0.0))
        gradient.setColorAt(SPHERE_RIM_STOP_PEAK, _with_alpha(look.rim_color, alpha))
        gradient.setColorAt(1.0, _with_alpha(look.rim_color, alpha * SPHERE_RIM_EDGE_ALPHA_RATIO))
        painter.setBrush(QBrush(gradient))
        extent = radius * SPHERE_MAX_BODY_SCALE
        painter.drawEllipse(center, extent, extent)

    def _paint_specular(self, painter: QPainter, center: QPointF, radius: float) -> None:
        width = radius * SPHERE_SPECULAR_SIZE[0]
        height = radius * SPHERE_SPECULAR_SIZE[1]
        if width <= 0.0:
            return

        painter.save()
        painter.translate(
            center.x() + radius * SPHERE_SPECULAR_OFFSET[0],
            center.y() + radius * SPHERE_SPECULAR_OFFSET[1],
        )
        painter.rotate(SPHERE_SPECULAR_ROTATION_DEG)
        painter.scale(1.0, height / width)
        _paint_glow(painter, QPointF(0.0, 0.0), width, self._specular_color, SPHERE_SPECULAR_ALPHA)
        painter.restore()
