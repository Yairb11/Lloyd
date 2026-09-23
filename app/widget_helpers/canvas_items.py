from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsTextItem

from app.config import (
    ANIM_CANVAS_LABEL_PT, ANIM_COLOR_ICE, ANIM_COLOR_MUDDLER_WOOD_DARK,
    ANIM_COLOR_MUDDLER_WOOD_DARKEST, ANIM_COLOR_MUDDLER_WOOD_LIGHT, ANIM_COLOR_SPOON_INNER,
    ANIM_COLOR_SPOON_KNOB, ANIM_COLOR_SPOON_METAL_DARK, ANIM_COLOR_SPOON_METAL_LIGHT,
    ANIM_CONTAINER_OUTLINE_STROKE_WIDTH, ANIM_CONTAINER_STEM_BASE_HALF_WIDTH, ANIM_CONTAINER_STEM_LENGTH,
    ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS, ANIM_GARNISH_LEAF_HEIGHT, ANIM_GARNISH_LEAF_WIDTH,
    ANIM_GARNISH_STROKE_WIDTH, ANIM_GARNISH_TRIANGLE_SCALE, ANIM_ICE_CUBE_CORNER_RADIUS,
    ANIM_ICE_CUBE_SIZE, ANIM_ICE_ROCK_CORNER_RADIUS, ANIM_ICE_ROCK_SIZE,
    ANIM_ICE_SPHERE_RADIUS, ANIM_ICE_STROKE_WIDTH, ANIM_LAYER_DEFAULT_OPACITY,
    ANIM_MUDDLER_HANDLE_MIN_HEIGHT, ANIM_MUDDLER_HANDLE_WIDTH, ANIM_MUDDLER_HEAD_HEIGHT,
    ANIM_MUDDLER_HEAD_WIDTH, ANIM_MUDDLER_STROKE_WIDTH, ANIM_SOLID_SQUARE_SIDE,
    ANIM_SOLID_STROKE_WIDTH, ANIM_SPOON_BOWL_HEIGHT, ANIM_SPOON_BOWL_WIDTH,
    ANIM_SPOON_STEM_STROKE_WIDTH, ANIM_SPOON_STROKE_WIDTH, ANIM_STRAIN_POUR_STROKE_WIDTH,
)
from app.widget_helpers.canvas_geometry import qp


class ShapeItem(QGraphicsObject):
    def __init__(self, path: QPainterPath, fill=None, stroke=None, stroke_width=0.0, parent=None):
        super().__init__(parent)
        self._path = path
        self._brush = QBrush(QColor(fill)) if fill else QBrush(Qt.BrushStyle.NoBrush)
        if stroke and stroke_width > 0:
            pen = QPen(QColor(stroke))
            pen.setWidthF(float(stroke_width))
            pen.setCosmetic(True)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self._pen = pen
        else:
            self._pen = QPen(Qt.PenStyle.NoPen)

    def boundingRect(self) -> QRectF:
        margin = self._pen.widthF()
        return self._path.boundingRect().adjusted(-margin, -margin, margin, margin)

    def shape(self) -> QPainterPath:
        return self._path

    def paint(self, painter, option, widget=None) -> None:
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawPath(self._path)

    def set_fill(self, color) -> None:
        self._brush = QBrush(QColor(color))
        self.update()


class GroupItem(QGraphicsObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None) -> None:
        return None


def make_text(text: str, point_size: int, color: str, bold: bool = False) -> QGraphicsTextItem:
    item = QGraphicsTextItem(text)
    font = QFont()
    font.setPointSize(point_size)
    font.setBold(bold)
    item.setFont(font)
    item.setDefaultTextColor(QColor(color))
    item.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
    return item



def trapezoid_path(w_bot: float, w_top: float, y_bot: float, y_top: float, cx: float = 0.0) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(qp(cx - w_bot / 2, y_bot))
    path.lineTo(qp(cx + w_bot / 2, y_bot))
    path.lineTo(qp(cx + w_top / 2, y_top))
    path.lineTo(qp(cx - w_top / 2, y_top))
    path.closeSubpath()
    return path


def vessel_path(shape) -> QPainterPath:
    half_h = shape.h / 2
    path = QPainterPath()
    path.moveTo(qp(-shape.w_top / 2, half_h))
    path.lineTo(qp(-shape.w_bot / 2, -half_h))
    path.lineTo(qp(shape.w_bot / 2, -half_h))
    path.lineTo(qp(shape.w_top / 2, half_h))

    if shape.stemmed:
        foot_y = -half_h - ANIM_CONTAINER_STEM_LENGTH
        path.moveTo(qp(0, -half_h))
        path.lineTo(qp(0, foot_y))
        path.moveTo(qp(-ANIM_CONTAINER_STEM_BASE_HALF_WIDTH, foot_y))
        path.lineTo(qp(ANIM_CONTAINER_STEM_BASE_HALF_WIDTH, foot_y))

    return path


def make_vessel(shape) -> ShapeItem:
    return ShapeItem(
        vessel_path(shape),
        fill=None,
        stroke="#FFFFFF",
        stroke_width=ANIM_CONTAINER_OUTLINE_STROKE_WIDTH,
    )


def make_layer(shape, y_bot: float, y_top: float, color: str) -> ShapeItem:
    item = ShapeItem(
        trapezoid_path(shape.width_at(y_bot), shape.width_at(y_top), y_bot - shape.h / 2, y_top - shape.h / 2),
        fill=color,
    )
    item.setOpacity(ANIM_LAYER_DEFAULT_OPACITY)
    return item


def _rounded(width: float, height: float, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(-width / 2, -height / 2, width, height), radius, radius)
    return path


def _ellipse(width: float, height: float) -> QPainterPath:
    path = QPainterPath()
    path.addEllipse(QRectF(-width / 2, -height / 2, width, height))
    return path


def make_dot(color: str, radius: float) -> ShapeItem:
    return ShapeItem(_ellipse(radius * 2, radius * 2), fill=color)


def make_ice_cube() -> ShapeItem:
    return ShapeItem(
        _rounded(ANIM_ICE_CUBE_SIZE, ANIM_ICE_CUBE_SIZE, ANIM_ICE_CUBE_CORNER_RADIUS),
        fill=ANIM_COLOR_ICE, stroke="#FFFFFF", stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def make_ice_rock() -> ShapeItem:
    return ShapeItem(
        _rounded(ANIM_ICE_ROCK_SIZE, ANIM_ICE_ROCK_SIZE, ANIM_ICE_ROCK_CORNER_RADIUS),
        fill=ANIM_COLOR_ICE, stroke="#FFFFFF", stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def make_ice_sphere() -> ShapeItem:
    return ShapeItem(
        _ellipse(ANIM_ICE_SPHERE_RADIUS * 2, ANIM_ICE_SPHERE_RADIUS * 2),
        fill=ANIM_COLOR_ICE, stroke="#FFFFFF", stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def make_solid(item_key: str, color: str) -> ShapeItem:
    if "leaf" in item_key or "basil" in item_key or "mint" in item_key:
        return ShapeItem(
            _ellipse(ANIM_GARNISH_LEAF_WIDTH, ANIM_GARNISH_LEAF_HEIGHT),
            fill=color, stroke="#FFFFFF", stroke_width=ANIM_SOLID_STROKE_WIDTH,
        )
    return ShapeItem(
        _rounded(ANIM_SOLID_SQUARE_SIDE, ANIM_SOLID_SQUARE_SIDE, 0.0),
        fill=color, stroke="#FFFFFF", stroke_width=ANIM_SOLID_STROKE_WIDTH,
    )


def make_garnish(shape_name: str, color: str, rim_width: float) -> ShapeItem:
    name = (shape_name or "").lower()

    if "leaf" in name:
        return ShapeItem(
            _ellipse(ANIM_GARNISH_LEAF_WIDTH, ANIM_GARNISH_LEAF_HEIGHT),
            fill=color, stroke="#FFFFFF", stroke_width=ANIM_GARNISH_STROKE_WIDTH,
        )

    if "half circle" in name:
        radius = ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS
        path = QPainterPath()
        path.moveTo(qp(-radius, 0))
        path.arcTo(QRectF(-radius, -radius, radius * 2, radius * 2), 180.0, 180.0)
        path.closeSubpath()
        return ShapeItem(path, fill=color, stroke="#FFFFFF", stroke_width=ANIM_GARNISH_STROKE_WIDTH)

    if "traingle" in name or "triangle" in name:
        side = ANIM_GARNISH_TRIANGLE_SCALE * 2
        path = QPainterPath()
        path.moveTo(qp(0, side / 2))
        path.lineTo(qp(-side / 2, -side / 2))
        path.lineTo(qp(side / 2, -side / 2))
        path.closeSubpath()
        return ShapeItem(path, fill=color, stroke="#FFFFFF", stroke_width=ANIM_GARNISH_STROKE_WIDTH)

    if "foam" in name:
        return ShapeItem(
            _rounded(rim_width, ANIM_GARNISH_LEAF_HEIGHT, ANIM_ICE_CUBE_CORNER_RADIUS),
            fill="#FFFFFF",
        )

    if "dashes" in name:
        path = QPainterPath()
        for index in (-1, 0, 1):
            path.addEllipse(QRectF(index * 0.2 - 0.06, -0.06, 0.12, 0.12))
        return ShapeItem(path, fill=color)

    return ShapeItem(
        _rounded(ANIM_SOLID_SQUARE_SIDE, ANIM_SOLID_SQUARE_SIDE, 0.0),
        fill=color, stroke="#FFFFFF", stroke_width=ANIM_GARNISH_STROKE_WIDTH,
    )


def make_muddler(container_height: float) -> GroupItem:
    group = GroupItem()
    handle_length = max(container_height + 0.8, ANIM_MUDDLER_HANDLE_MIN_HEIGHT)

    head = ShapeItem(
        _rounded(ANIM_MUDDLER_HEAD_WIDTH, ANIM_MUDDLER_HEAD_HEIGHT, 0.06),
        fill=ANIM_COLOR_MUDDLER_WOOD_DARK,
        stroke=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
        parent=group,
    )
    head.setPos(qp(0, 0))

    handle = ShapeItem(
        _rounded(ANIM_MUDDLER_HANDLE_WIDTH, handle_length, 0.07),
        fill=ANIM_COLOR_MUDDLER_WOOD_LIGHT,
        stroke=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
        parent=group,
    )
    handle.setPos(qp(0, ANIM_MUDDLER_HEAD_HEIGHT / 2 + handle_length / 2 - 0.08))

    pommel = ShapeItem(
        _ellipse(0.3, 0.3),
        fill=ANIM_COLOR_MUDDLER_WOOD_DARK,
        stroke=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
        parent=group,
    )
    pommel.setPos(qp(0, ANIM_MUDDLER_HEAD_HEIGHT / 2 + handle_length - 0.08))

    return group


def make_spoon(container_height: float) -> GroupItem:
    group = GroupItem()
    stem_length = container_height + 1.0

    bowl = ShapeItem(
        _ellipse(ANIM_SPOON_BOWL_WIDTH, ANIM_SPOON_BOWL_HEIGHT),
        fill=ANIM_COLOR_SPOON_METAL_LIGHT,
        stroke=ANIM_COLOR_SPOON_METAL_DARK,
        stroke_width=ANIM_SPOON_STROKE_WIDTH,
        parent=group,
    )
    bowl.setPos(qp(0, 0))

    inner = ShapeItem(_ellipse(0.18, 0.30), fill=ANIM_COLOR_SPOON_INNER, parent=group)
    inner.setPos(qp(-0.03, 0))
    inner.setOpacity(0.6)

    stem_path = QPainterPath()
    stem_path.moveTo(qp(0, 0))
    stem_path.lineTo(qp(0, stem_length))
    stem = ShapeItem(
        stem_path,
        stroke=ANIM_COLOR_SPOON_METAL_LIGHT,
        stroke_width=ANIM_SPOON_STEM_STROKE_WIDTH,
        parent=group,
    )
    stem.setPos(qp(0, ANIM_SPOON_BOWL_HEIGHT / 2))

    knob = ShapeItem(
        _ellipse(0.18, 0.18),
        fill=ANIM_COLOR_SPOON_KNOB,
        stroke=ANIM_COLOR_SPOON_METAL_DARK,
        stroke_width=ANIM_SPOON_STROKE_WIDTH,
        parent=group,
    )
    knob.setPos(qp(0, ANIM_SPOON_BOWL_HEIGHT / 2 + stem_length))

    return group


def make_stream(x: float, y_top: float, y_bot: float, color: str, width: float) -> ShapeItem:
    path = QPainterPath()
    path.moveTo(qp(x, y_top))
    path.lineTo(qp(x, y_bot))
    return ShapeItem(path, stroke=color, stroke_width=width)


def make_pour_curve(start_x: float, start_y: float, end_x: float, end_y: float, color: str) -> ShapeItem:
    path = QPainterPath()
    path.moveTo(qp(start_x, start_y))
    path.cubicTo(
        qp(start_x + 0.55, start_y + 0.35),
        qp(end_x - 0.45, end_y + 0.65),
        qp(end_x, end_y),
    )
    return ShapeItem(path, stroke=color, stroke_width=ANIM_STRAIN_POUR_STROKE_WIDTH)


def make_label(text: str) -> QGraphicsTextItem:
    return make_text(text, ANIM_CANVAS_LABEL_PT, "#B0B0B0", bold=False)
