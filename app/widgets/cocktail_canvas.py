import functools
import math

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPauseAnimation,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    QVariantAnimation,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

from app.config import (
    ANIM_CANVAS_FADE_MS,
    ANIM_CANVAS_HOLD_MS,
    ANIM_CANVAS_LOOP_COUNT,
    ANIM_CANVAS_SCENE_HEIGHT,
    ANIM_CANVAS_SCENE_WIDTH,
    ANIM_CANVAS_STEP_PAUSE_MS,
    ANIM_CANVAS_TITLE_PT,
    ANIM_CANVAS_STEP_TITLE_PT,
    ANIM_CANVAS_STEP_DESC_PT,
    ANIM_COLOR_DEFAULT_GARNISH,
    ANIM_COLOR_DEFAULT_LIQUID,
    ANIM_COLOR_DEFAULT_MUDDLE_BLEND,
    ANIM_COLOR_DEFAULT_SHAKE_BLEND,
    ANIM_COLOR_DEFAULT_STIR_BLEND,
    ANIM_COLOR_DEFAULT_STRAIN,
    ANIM_COLOR_FOAM,
    ANIM_GARNISH_SIDE_OFFSET,
    ANIM_GARNISH_SURFACE_Y_OFFSET,
    ANIM_ICE_CUBE_COUNT_PREP,
    ANIM_ICE_CUBE_COUNT_SERVING,
    ANIM_ICE_CUBE_HEIGHT_DELTA,
    ANIM_ICE_CUBE_X_SPACING,
    ANIM_ICE_CUBE_Y_OFFSET,
    ANIM_ICE_LARGE_HEIGHT_DELTA,
    ANIM_ICE_LARGE_Y_OFFSET,
    ANIM_LABEL_MIXING_GLASS,
    ANIM_LABEL_SERVING_GLASS,
    ANIM_LABEL_SHAKER,
    ANIM_LAYER_DEFAULT_OPACITY,
    ANIM_MEASURE_DASH_HEIGHT_SCALE,
    ANIM_MEASURE_DEFAULT_AMOUNT_ML,
    ANIM_MEASURE_FALLBACK_THICKNESS,
    ANIM_MEASURE_MAX_FILL_MARGIN,
    ANIM_MEASURE_MIN_AVAILABLE_HEIGHT,
    ANIM_MEASURE_STREAM_START_OFFSET,
    ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID,
    ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER,
    ANIM_MEASURE_TOP_MARGIN,
    ANIM_MEASURE_TOP_MIN_THICKNESS,
    ANIM_ML_TO_HEIGHT_SCALE,
    ANIM_MUDDLER_STROKES,
    ANIM_SHAKE_WIGGLE_COUNT,
    ANIM_SHAKE_WIGGLE_ROTATION,
    ANIM_SOLID_HEIGHT_DELTA,
    ANIM_SOLID_Y_OFFSET,
    ANIM_STEP_WRAP_WORDS_PER_LINE,
    ANIM_STIR_ORBIT_RADIUS_RATIO,
    ANIM_STIR_ORBIT_RY,
    ANIM_STIR_ORBIT_Y_OFFSET,
    ANIM_STRAIN_FOAM_THICKNESS,
    ANIM_STRAIN_RIM_MARGIN,
    ANIM_STRAIN_TILT_ANGLE,
    ANIM_VESSEL_LABEL_OPACITY,
    ANIM_VESSEL_PAIR_X_OFFSET,
    ANIM_VESSEL_Y_OFFSET,
    COLOR_CANVAS_BG,
)
from app.helpers import perf
from app.helpers.canvas_geometry import qp, vessel_shape
from app.helpers.canvas_items import (
    GroupItem,
    make_garnish,
    make_ice_cube,
    make_ice_rock,
    make_ice_sphere,
    make_label,
    make_layer,
    make_muddler,
    make_pour_curve,
    make_solid,
    make_spoon,
    make_stream,
    make_text,
    make_vessel,
)
from app.helpers.cocktail_recipe import (
    Recipe,
    is_top_step,
    needs_shaker,
    wrap_instruction,
)
from app.helpers.color_utils import hex_to_rgb, rgb_to_hex

SERVING_GLASS = "serving_glass"
PREP_VESSEL = "prep"
LIQUID_TYPES = ("liquid", "bitters")


class CanvasVesselState:
    def __init__(self, shape, item, origin_x: float, origin_y: float) -> None:
        self.shape = shape
        self.item = item
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.label_item = None
        self.layers: list = []
        self.solids: list = []
        self.liquid_h = 0.0
        self.solid_h = 0.0
        self.liquid_colors: list = []
        self.visible = False

    def bottom_y(self) -> float:
        return self.origin_y - self.shape.h / 2

    def top_y(self) -> float:
        return self.origin_y + self.shape.h / 2


def blend(colors: list, default_hex: str) -> str:
    if not colors:
        return default_hex
    rgbs = [hex_to_rgb(color) for color in colors]
    total = [sum(channel) / len(rgbs) for channel in zip(*rgbs)]
    return rgb_to_hex(total)


class CocktailCanvas(QGraphicsView):
    animation_started = pyqtSignal(str)
    animation_finished = pyqtSignal()
    loop_completed = pyqtSignal(int)
    step_changed = pyqtSignal(int, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(
            QRectF(
                -ANIM_CANVAS_SCENE_WIDTH / 2,
                -ANIM_CANVAS_SCENE_HEIGHT / 2,
                ANIM_CANVAS_SCENE_WIDTH,
                ANIM_CANVAS_SCENE_HEIGHT,
            )
        )
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setBackgroundBrush(QColor(COLOR_CANVAS_BG))

        self._sequence: QSequentialAnimationGroup | None = None
        self._recipe = None
        self._vessels: dict = {}
        self._active_target: str | None = None
        self._already_strained = False
        self._step_items: list = []
        self._fading_items: list = []

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def stop(self) -> None:
        if self._sequence is not None:
            self._sequence.stop()
            self._sequence.deleteLater()
            self._sequence = None
        self._scene.clear()
        self._vessels = {}
        self._step_items = []
        self._fading_items = []
        self._active_target = None
        self._already_strained = False

    def pause(self) -> None:
        if self._sequence is not None:
            self._sequence.pause()

    def resume(self) -> None:
        if self._sequence is not None:
            self._sequence.resume()

    def play_spec(self, spec: dict) -> None:
        self.stop()
        perf.mark("canvas.build_start")

        self._recipe = Recipe(spec)
        sequence = QSequentialAnimationGroup(self)

        self._add_title(sequence)
        self._setup_vessels()

        for index, step in enumerate(self._recipe.steps):
            step_group = self._build_step(index, step)
            if step_group is not None:
                sequence.addAnimation(step_group)
            sequence.addAnimation(QPauseAnimation(ANIM_CANVAS_STEP_PAUSE_MS))

        sequence.addAnimation(QPauseAnimation(ANIM_CANVAS_HOLD_MS))
        sequence.setLoopCount(ANIM_CANVAS_LOOP_COUNT)
        sequence.finished.connect(self.animation_finished.emit)
        sequence.currentLoopChanged.connect(self._on_loop_changed)

        self._sequence = sequence
        perf.mark("canvas.build_done")
        self.animation_started.emit(self._recipe.name)
        sequence.start()

    def _on_loop_changed(self, loop: int) -> None:
        for item in self._fading_items:
            item.setOpacity(0.0)
        self.loop_completed.emit(loop)

    def _track(self, item):
        self._scene.addItem(item)
        self._fading_items.append(item)
        return item

    def _fade_in(self, item, duration_ms: int = ANIM_CANVAS_FADE_MS, to: float = 1.0):
        item.setOpacity(0.0)
        animation = QPropertyAnimation(item, b"opacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(0.0)
        animation.setEndValue(to)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    def _fade_out(self, item, duration_ms: int = ANIM_CANVAS_FADE_MS, frm: float = 1.0):
        animation = QPropertyAnimation(item, b"opacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(frm)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        return animation

    def _move(self, item, from_x: float, from_y: float, to_x: float, to_y: float, duration_ms: int):
        animation = QPropertyAnimation(item, b"pos", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(qp(from_x, from_y))
        animation.setEndValue(qp(to_x, to_y))
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        return animation

    def _rotate(self, item, from_degrees: float, to_degrees: float, duration_ms: int):
        animation = QPropertyAnimation(item, b"rotation", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(from_degrees)
        animation.setEndValue(to_degrees)
        return animation

    def _add_title(self, sequence) -> None:
        title = make_text(self._recipe.name, ANIM_CANVAS_TITLE_PT, "#E0A96D", bold=True)
        title.setPos(qp(-ANIM_CANVAS_SCENE_WIDTH / 2 + 0.4, ANIM_CANVAS_SCENE_HEIGHT / 2 - 0.3))
        self._track(title)
        sequence.addAnimation(self._fade_in(title))

    def _setup_vessels(self) -> None:
        recipe = self._recipe
        base_y = -ANIM_VESSEL_Y_OFFSET

        if recipe.build_in_glass:
            self._add_vessel(SERVING_GLASS, recipe.glass_type, ANIM_LABEL_SERVING_GLASS, 0.0, base_y)
            self._active_target = SERVING_GLASS
            return

        if needs_shaker(recipe.steps):
            prep_type, prep_label = "shaker", ANIM_LABEL_SHAKER
        else:
            prep_type, prep_label = "mixing_glass", ANIM_LABEL_MIXING_GLASS

        self._add_vessel(PREP_VESSEL, prep_type, prep_label, -ANIM_VESSEL_PAIR_X_OFFSET, base_y)
        self._add_vessel(SERVING_GLASS, recipe.glass_type, ANIM_LABEL_SERVING_GLASS, ANIM_VESSEL_PAIR_X_OFFSET, base_y)
        self._active_target = PREP_VESSEL

    def _add_vessel(self, key: str, c_type: str, label: str, x: float, y: float) -> None:
        shape = vessel_shape(c_type)
        item = make_vessel(shape, label)
        item.setPos(qp(x, y))
        item.setOpacity(0.0)
        self._track(item)

        label_item = make_label(label)
        label_item.setPos(qp(x, y - shape.h / 2 - 0.35))
        label_item.setOpacity(0.0)
        self._track(label_item)

        state = CanvasVesselState(shape, item, x, y)
        state.label_item = label_item
        self._vessels[key] = state

    def _reveal_vessel(self, state, group) -> None:
        if state.visible:
            return
        state.visible = True
        group.addAnimation(self._fade_in(state.item))
        group.addAnimation(self._fade_in(state.label_item, to=ANIM_VESSEL_LABEL_OPACITY))

    def _select_state(self, action: dict, top_step: bool):
        target = action.get("target")
        if self._recipe.build_in_glass or target == SERVING_GLASS or self._already_strained or top_step:
            return self._vessels[SERVING_GLASS]
        if target in ("shaker", "mixing_glass"):
            return self._vessels.get(PREP_VESSEL, self._vessels[SERVING_GLASS])
        return self._vessels.get(self._active_target, self._vessels[SERVING_GLASS])

    def _build_step(self, index: int, step: dict):
        title = step.get("title", "")
        instruction = step.get("instruction", "")
        action = step.get("action", {})
        if not isinstance(action, dict):
            action = {}
        action_name = str(action.get("name", "")).lower()
        top_step = is_top_step(title, instruction, action)

        group = QSequentialAnimationGroup(self)
        group.addAnimation(self._build_step_text(index, title, instruction))

        state = self._select_state(action, top_step)
        reveal = QParallelAnimationGroup(self)
        self._reveal_vessel(state, reveal)
        if reveal.animationCount() > 0:
            group.addAnimation(reveal)

        builder = {
            "chill": self._build_chill,
            "ice": self._build_ice,
            "measure": self._build_measure,
            "shake": self._build_shake,
            "muddle": self._build_muddle,
            "stir": self._build_stir,
            "strain": self._build_strain,
            "garnish": self._build_garnish,
        }.get(action_name)

        if builder is not None:
            action_animation = builder(state, action, top_step)
            if action_animation is not None:
                group.addAnimation(action_animation)

        return group

    def _build_step_text(self, index: int, title: str, instruction: str):
        group = QParallelAnimationGroup(self)

        for old in self._step_items:
            group.addAnimation(self._fade_out(old))
        self._step_items = []

        title_item = make_text(title, ANIM_CANVAS_STEP_TITLE_PT, "#F2C94C", bold=True)
        title_item.setPos(qp(-ANIM_CANVAS_SCENE_WIDTH / 2 + 0.4, ANIM_CANVAS_SCENE_HEIGHT / 2 - 1.1))
        self._track(title_item)

        desc_item = make_text(
            wrap_instruction(instruction, ANIM_STEP_WRAP_WORDS_PER_LINE),
            ANIM_CANVAS_STEP_DESC_PT,
            "#E8E8E8",
        )
        desc_item.setPos(qp(-ANIM_CANVAS_SCENE_WIDTH / 2 + 0.4, ANIM_CANVAS_SCENE_HEIGHT / 2 - 1.6))
        self._track(desc_item)

        self._step_items = [title_item, desc_item]
        group.addAnimation(self._fade_in(title_item))
        group.addAnimation(self._fade_in(desc_item))

        group.finished.connect(functools.partial(self.step_changed.emit, index, title))
        return group

    def _build_chill(self, state, action, top_step):
        frost = make_vessel(state.shape, "")
        frost.setPos(qp(state.origin_x, state.origin_y))
        frost.setOpacity(0.0)
        self._track(frost)

        sequence = QSequentialAnimationGroup(self)
        sequence.addAnimation(self._fade_in(frost, to=0.7))
        sequence.addAnimation(self._fade_out(frost, frm=0.7))

        if not self._recipe.build_in_glass and PREP_VESSEL in self._vessels:
            reveal = QParallelAnimationGroup(self)
            self._reveal_vessel(self._vessels[PREP_VESSEL], reveal)
            if reveal.animationCount() > 0:
                sequence.addAnimation(reveal)

        return sequence

    def _build_ice(self, state, action, top_step):
        ice_type = action.get("ice_type", "cubed")

        if ice_type in ("sphere", "large_rock"):
            ice = make_ice_sphere() if ice_type == "sphere" else make_ice_rock()
            ice.setPos(qp(state.origin_x, state.bottom_y() + state.solid_h + ANIM_ICE_LARGE_Y_OFFSET))
            ice.setZValue(10)
            ice.setOpacity(0.0)
            self._track(ice)
            state.solids.append(ice)
            state.solid_h += ANIM_ICE_LARGE_HEIGHT_DELTA
            return self._fade_in(ice)

        count = ANIM_ICE_CUBE_COUNT_PREP if state is self._vessels.get(PREP_VESSEL) else ANIM_ICE_CUBE_COUNT_SERVING
        sequence = QSequentialAnimationGroup(self)
        for i in range(count):
            cube = make_ice_cube()
            offset_x = (i - (count - 1) / 2) * ANIM_ICE_CUBE_X_SPACING
            cube.setPos(qp(state.origin_x + offset_x, state.bottom_y() + state.solid_h + ANIM_ICE_CUBE_Y_OFFSET))
            cube.setZValue(10)
            cube.setOpacity(0.0)
            self._track(cube)
            state.solids.append(cube)
            sequence.addAnimation(self._fade_in(cube, duration_ms=ANIM_CANVAS_FADE_MS // 2))

        state.solid_h += ANIM_ICE_CUBE_HEIGHT_DELTA
        return sequence

    def _liquid_thickness(self, state, action, ingredient_type: str, top_step: bool) -> float:
        amount = action.get("amount", ANIM_MEASURE_DEFAULT_AMOUNT_ML)

        if top_step:
            target_top = state.shape.h - ANIM_MEASURE_TOP_MARGIN
            return max(target_top - state.liquid_h, ANIM_MEASURE_TOP_MIN_THICKNESS)

        if ingredient_type == "bitters" or action.get("unit") == "dash":
            thickness = float(amount) * ANIM_MEASURE_DASH_HEIGHT_SCALE
        elif isinstance(amount, (int, float)):
            thickness = float(amount) * ANIM_ML_TO_HEIGHT_SCALE
        else:
            thickness = ANIM_MEASURE_FALLBACK_THICKNESS

        available = max(
            (state.shape.h - ANIM_MEASURE_MAX_FILL_MARGIN) - state.liquid_h,
            ANIM_MEASURE_MIN_AVAILABLE_HEIGHT,
        )
        return min(thickness, available)

    def _build_measure(self, state, action, top_step):
        key = action.get("what", "")
        meta = self._recipe.ingredient_lookup.get(
            key, {"color": ANIM_COLOR_DEFAULT_LIQUID, "type": "liquid"}
        )

        if meta["type"] not in LIQUID_TYPES:
            solid = make_solid(key, meta["color"])
            solid.setPos(qp(state.origin_x, state.bottom_y() + state.solid_h + ANIM_SOLID_Y_OFFSET))
            solid.setZValue(10)
            solid.setOpacity(0.0)
            self._track(solid)
            state.solids.append(solid)
            state.solid_h += ANIM_SOLID_HEIGHT_DELTA
            return self._fade_in(solid)

        thickness = self._liquid_thickness(state, action, meta["type"], top_step)
        layer = make_layer(state.shape, state.liquid_h, state.liquid_h + thickness, meta["color"])
        layer.setPos(qp(state.origin_x, state.origin_y))
        layer.setOpacity(0.0)
        self._track(layer)

        stream = make_stream(
            state.origin_x,
            state.top_y() + ANIM_MEASURE_STREAM_START_OFFSET,
            state.bottom_y() + state.liquid_h,
            meta["color"],
            ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID
            if meta["type"] == "liquid"
            else ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER,
        )
        stream.setZValue(5)
        stream.setOpacity(0.0)
        self._track(stream)

        state.liquid_h += thickness
        state.liquid_colors.append(meta["color"])
        state.layers.append(layer)

        sequence = QSequentialAnimationGroup(self)
        sequence.addAnimation(self._fade_in(stream, duration_ms=ANIM_CANVAS_FADE_MS // 2))
        parallel = QParallelAnimationGroup(self)
        parallel.addAnimation(self._fade_in(layer, to=ANIM_LAYER_DEFAULT_OPACITY))
        parallel.addAnimation(self._fade_out(stream))
        sequence.addAnimation(parallel)
        return sequence

    def _merge(self, state, color: str, absorb_solids: bool):
        merged = make_layer(state.shape, 0.0, state.liquid_h, color)
        merged.setPos(qp(state.origin_x, state.origin_y))
        merged.setOpacity(0.0)
        self._track(merged)

        parallel = QParallelAnimationGroup(self)
        for old in state.layers:
            parallel.addAnimation(self._fade_out(old, frm=ANIM_LAYER_DEFAULT_OPACITY))
        if absorb_solids:
            for old in state.solids:
                parallel.addAnimation(self._fade_out(old))
        parallel.addAnimation(self._fade_in(merged, to=ANIM_LAYER_DEFAULT_OPACITY))

        state.layers = [merged]
        state.liquid_colors = [color]
        if absorb_solids:
            state.solids = []
            state.solid_h = 0.0
        return parallel

    def _content_group(self, state):
        group = GroupItem()
        group.setPos(qp(0, 0))
        self._scene.addItem(group)
        state.item.setParentItem(group)
        for child in state.layers + state.solids:
            child.setParentItem(group)
        return group

    def _build_shake(self, state, action, top_step):
        color = blend(state.liquid_colors, ANIM_COLOR_DEFAULT_SHAKE_BLEND)
        group = self._content_group(state)
        group.setTransformOriginPoint(qp(state.origin_x, state.origin_y))

        sequence = QSequentialAnimationGroup(self)
        degrees = math.degrees(ANIM_SHAKE_WIGGLE_ROTATION)
        current = 0.0
        for i in range(ANIM_SHAKE_WIGGLE_COUNT):
            target = degrees if i % 2 == 0 else -degrees
            sequence.addAnimation(self._rotate(group, current, target, ANIM_CANVAS_FADE_MS // 3))
            current = target
        sequence.addAnimation(self._rotate(group, current, 0.0, ANIM_CANVAS_FADE_MS // 3))
        sequence.addAnimation(self._merge(state, color, absorb_solids=True))
        return sequence

    def _build_muddle(self, state, action, top_step):
        color = blend(state.liquid_colors, ANIM_COLOR_DEFAULT_MUDDLE_BLEND)

        muddler = make_muddler(state.shape.h)
        base_y = state.bottom_y() + 0.3
        muddler.setPos(qp(state.origin_x, base_y))
        muddler.setZValue(15)
        muddler.setOpacity(0.0)
        self._track(muddler)

        sequence = QSequentialAnimationGroup(self)
        sequence.addAnimation(self._fade_in(muddler))

        current_y = base_y
        for lift, _twist in ANIM_MUDDLER_STROKES:
            next_y = current_y + lift
            sequence.addAnimation(
                self._move(
                    muddler, state.origin_x, current_y, state.origin_x, next_y,
                    ANIM_CANVAS_FADE_MS // 2,
                )
            )
            current_y = next_y

        sequence.addAnimation(self._fade_out(muddler))
        sequence.addAnimation(self._merge(state, color, absorb_solids=True))
        return sequence

    def _set_orbit_pos(self, item, cx: float, cy: float, rx: float, ry: float, value) -> None:
        angle = float(value)
        item.setPos(qp(cx + rx * math.cos(angle), cy + ry * math.sin(angle)))

    def _build_stir(self, state, action, top_step):
        color = blend(state.liquid_colors, ANIM_COLOR_DEFAULT_STIR_BLEND)

        spoon = make_spoon(state.shape.h)
        rx = min(state.shape.w_bot, state.shape.w_top) * ANIM_STIR_ORBIT_RADIUS_RATIO
        cy = state.bottom_y() + ANIM_STIR_ORBIT_Y_OFFSET
        spoon.setPos(qp(state.origin_x + rx, cy))
        spoon.setZValue(15)
        spoon.setOpacity(0.0)
        self._track(spoon)

        orbit = QVariantAnimation(self)
        orbit.setDuration(ANIM_CANVAS_FADE_MS * 4)
        orbit.setStartValue(0.0)
        orbit.setEndValue(4.0 * math.pi)
        orbit.setEasingCurve(QEasingCurve.Type.Linear)
        orbit.valueChanged.connect(
            functools.partial(
                self._set_orbit_pos, spoon, state.origin_x, cy, rx, ANIM_STIR_ORBIT_RY
            )
        )

        sequence = QSequentialAnimationGroup(self)
        sequence.addAnimation(self._fade_in(spoon))
        sequence.addAnimation(orbit)
        sequence.addAnimation(self._fade_out(spoon))
        sequence.addAnimation(self._merge(state, color, absorb_solids=False))
        return sequence

    def _build_strain(self, state, action, top_step):
        source = self._vessels.get(PREP_VESSEL, state)
        dest = self._vessels[SERVING_GLASS]

        color = source.liquid_colors[0] if source.liquid_colors else ANIM_COLOR_DEFAULT_STRAIN

        rim_h = dest.shape.h - ANIM_STRAIN_RIM_MARGIN
        if self._recipe.has_foam:
            thickness = max(rim_h - ANIM_STRAIN_FOAM_THICKNESS - dest.liquid_h, 0.6)
        else:
            thickness = min(source.liquid_h, rim_h - dest.liquid_h)

        strained = make_layer(dest.shape, dest.liquid_h, dest.liquid_h + thickness, color)
        strained.setPos(qp(dest.origin_x, dest.origin_y))
        strained.setOpacity(0.0)
        self._track(strained)
        dest.liquid_h += thickness
        dest.liquid_colors.append(color)

        foam = None
        if self._recipe.has_foam:
            foam = make_layer(
                dest.shape, dest.liquid_h, dest.liquid_h + ANIM_STRAIN_FOAM_THICKNESS, ANIM_COLOR_FOAM
            )
            foam.setPos(qp(dest.origin_x, dest.origin_y))
            foam.setZValue(13)
            foam.setOpacity(0.0)
            self._track(foam)
            dest.liquid_h += ANIM_STRAIN_FOAM_THICKNESS

        sequence = QSequentialAnimationGroup(self)

        reveal = QParallelAnimationGroup(self)
        self._reveal_vessel(dest, reveal)
        if reveal.animationCount() > 0:
            sequence.addAnimation(reveal)

        tilting = self._content_group(source)
        lip_x = source.origin_x + source.shape.w_top / 2
        lip_y = source.top_y()
        tilting.setTransformOriginPoint(qp(lip_x, lip_y))

        tilt_degrees = math.degrees(ANIM_STRAIN_TILT_ANGLE)
        sequence.addAnimation(self._rotate(tilting, 0.0, tilt_degrees, ANIM_CANVAS_FADE_MS))

        pour = make_pour_curve(lip_x, lip_y, dest.origin_x, dest.top_y(), color)
        pour.setOpacity(0.0)
        self._track(pour)
        sequence.addAnimation(self._fade_in(pour, duration_ms=ANIM_CANVAS_FADE_MS // 2))

        transfer = QParallelAnimationGroup(self)
        for old in source.layers:
            transfer.addAnimation(self._fade_out(old, frm=ANIM_LAYER_DEFAULT_OPACITY))
        for old in source.solids:
            transfer.addAnimation(self._fade_out(old))
        transfer.addAnimation(self._fade_in(strained, to=ANIM_LAYER_DEFAULT_OPACITY))
        if foam is not None:
            transfer.addAnimation(self._fade_in(foam, to=ANIM_LAYER_DEFAULT_OPACITY))
        sequence.addAnimation(transfer)

        sequence.addAnimation(self._fade_out(pour))
        sequence.addAnimation(self._rotate(tilting, tilt_degrees, 0.0, ANIM_CANVAS_FADE_MS))

        source.layers = []
        source.solids = []
        source.liquid_h = 0.0
        source.solid_h = 0.0
        source.liquid_colors = []

        dest.layers.append(strained)
        if foam is not None:
            dest.layers.append(foam)

        self._already_strained = True
        return sequence

    def _build_garnish(self, state, action, top_step):
        dest = self._vessels[SERVING_GLASS]
        placement = action.get("placement", "float")
        color = action.get("color_hex", ANIM_COLOR_DEFAULT_GARNISH)
        shape_name = action.get("shape", "half circle")

        garnish = make_garnish(shape_name, color, dest.shape.w_top * 0.85)
        surface_y = dest.bottom_y() + dest.liquid_h + ANIM_GARNISH_SURFACE_Y_OFFSET

        if placement == "rim":
            garnish.setPos(qp(dest.origin_x - dest.shape.w_top / 2, dest.top_y()))
        elif placement == "side_of_ice":
            garnish.setPos(qp(dest.origin_x + ANIM_GARNISH_SIDE_OFFSET, surface_y))
        else:
            garnish.setPos(qp(dest.origin_x, surface_y))

        garnish.setZValue(20)
        garnish.setOpacity(0.0)
        self._track(garnish)
        return self._fade_in(garnish)