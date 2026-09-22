import numpy as np
from manim import (
    AnnularSector, Circle, CubicBezier,
    DOWN, Dot, Ellipse,
    LEFT, LIGHT_GRAY, Line,
    PI, RIGHT, RoundedRectangle,
    Square, Text, Triangle,
    UP, VGroup, WHITE,
)

from app.animation.recipe import format_ingredient_label
from app.config import (
    ANIM_COLOR_ICE, ANIM_COLOR_MUDDLER_WOOD_DARK, ANIM_COLOR_MUDDLER_WOOD_DARKEST,
    ANIM_COLOR_MUDDLER_WOOD_LIGHT, ANIM_COLOR_MUDDLER_WOOD_MEDIUM, ANIM_COLOR_SPOON_INNER,
    ANIM_COLOR_SPOON_KNOB, ANIM_COLOR_SPOON_KNOB_STROKE, ANIM_COLOR_SPOON_METAL_DARK,
    ANIM_COLOR_SPOON_METAL_LIGHT, ANIM_GARNISH_DASH_BUFF, ANIM_GARNISH_DASH_RADIUS,
    ANIM_GARNISH_FOAM_CORNER_RADIUS, ANIM_GARNISH_FOAM_HEIGHT, ANIM_GARNISH_FOAM_OPACITY,
    ANIM_GARNISH_FOAM_WIDTH_RATIO, ANIM_GARNISH_HALF_CIRCLE_INNER_RADIUS, ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS,
    ANIM_GARNISH_LEAF_HEIGHT, ANIM_GARNISH_LEAF_WIDTH, ANIM_GARNISH_STROKE_WIDTH,
    ANIM_GARNISH_TRIANGLE_SCALE, ANIM_ICE_CUBE_CORNER_RADIUS, ANIM_ICE_CUBE_FILL_OPACITY,
    ANIM_ICE_CUBE_SIZE, ANIM_ICE_LARGE_FILL_OPACITY, ANIM_ICE_ROCK_CORNER_RADIUS,
    ANIM_ICE_ROCK_SIZE, ANIM_ICE_SPHERE_RADIUS, ANIM_ICE_STROKE_WIDTH,
    ANIM_INGREDIENT_DOT_RADIUS, ANIM_INGREDIENT_ENTRY_BUFF, ANIM_MUDDLER_GROOVE_DROP,
    ANIM_MUDDLER_GROOVE_INSET, ANIM_MUDDLER_HANDLE_CORNER_RADIUS, ANIM_MUDDLER_HANDLE_HEIGHT_PADDING,
    ANIM_MUDDLER_HANDLE_MIN_HEIGHT, ANIM_MUDDLER_HANDLE_OVERLAP, ANIM_MUDDLER_HANDLE_WIDTH,
    ANIM_MUDDLER_HEAD_CORNER_RADIUS, ANIM_MUDDLER_HEAD_HEIGHT, ANIM_MUDDLER_HEAD_WIDTH,
    ANIM_MUDDLER_POMMEL_OVERLAP, ANIM_MUDDLER_POMMEL_RADIUS, ANIM_MUDDLER_STROKE_WIDTH,
    ANIM_SOLID_LEAF_FILL_OPACITY, ANIM_SOLID_LEAF_HEIGHT, ANIM_SOLID_LEAF_WIDTH,
    ANIM_SOLID_SQUARE_FILL_OPACITY, ANIM_SOLID_SQUARE_SIDE, ANIM_SOLID_STROKE_WIDTH,
    ANIM_SPOON_BOWL_HEIGHT, ANIM_SPOON_BOWL_WIDTH, ANIM_SPOON_INNER_HEIGHT,
    ANIM_SPOON_INNER_OPACITY, ANIM_SPOON_INNER_WIDTH, ANIM_SPOON_INNER_X_SHIFT,
    ANIM_SPOON_KNOB_RADIUS, ANIM_SPOON_KNOB_STROKE_WIDTH, ANIM_SPOON_SPIRAL_COUNT,
    ANIM_SPOON_SPIRAL_MARGIN, ANIM_SPOON_SPIRAL_X_OFFSET, ANIM_SPOON_SPIRAL_Y_STEP,
    ANIM_SPOON_STEM_HEIGHT_PADDING, ANIM_SPOON_STEM_STROKE_WIDTH, ANIM_SPOON_STROKE_WIDTH,
    ANIM_STRAIN_POUR_CONTROL_1_OFFSET, ANIM_STRAIN_POUR_CONTROL_2_OFFSET, ANIM_STRAIN_POUR_START_OFFSET,
    ANIM_STRAIN_POUR_STROKE_WIDTH, ANIM_TOOL_Z_INDEX,
)


def _offset(dx, dy):
    return np.array([dx, dy, 0])


def create_ingredient_entry(ingredient, font_size):
    dot = Dot(
        radius=ANIM_INGREDIENT_DOT_RADIUS,
        color=ingredient.get("color_hex") or ingredient.get("color") or WHITE,
    )
    label = Text(format_ingredient_label(ingredient), font_size=font_size, color=LIGHT_GRAY)
    return VGroup(dot, label).arrange(RIGHT, buff=ANIM_INGREDIENT_ENTRY_BUFF)


def create_ice_sphere():
    return Circle(
        radius=ANIM_ICE_SPHERE_RADIUS,
        fill_color=ANIM_COLOR_ICE,
        fill_opacity=ANIM_ICE_LARGE_FILL_OPACITY,
        stroke_color=WHITE,
        stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def create_ice_rock():
    return RoundedRectangle(
        corner_radius=ANIM_ICE_ROCK_CORNER_RADIUS,
        height=ANIM_ICE_ROCK_SIZE,
        width=ANIM_ICE_ROCK_SIZE,
        fill_color=ANIM_COLOR_ICE,
        fill_opacity=ANIM_ICE_LARGE_FILL_OPACITY,
        stroke_color=WHITE,
        stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def create_ice_cube():
    return RoundedRectangle(
        corner_radius=ANIM_ICE_CUBE_CORNER_RADIUS,
        height=ANIM_ICE_CUBE_SIZE,
        width=ANIM_ICE_CUBE_SIZE,
        fill_color=ANIM_COLOR_ICE,
        fill_opacity=ANIM_ICE_CUBE_FILL_OPACITY,
        stroke_color=WHITE,
        stroke_width=ANIM_ICE_STROKE_WIDTH,
    )


def create_solid_ingredient(item_key, color):
    if "leaf" in item_key or "basil" in item_key:
        return Ellipse(
            width=ANIM_SOLID_LEAF_WIDTH,
            height=ANIM_SOLID_LEAF_HEIGHT,
            fill_color=color,
            fill_opacity=ANIM_SOLID_LEAF_FILL_OPACITY,
            stroke_color=WHITE,
            stroke_width=ANIM_SOLID_STROKE_WIDTH,
        )
    return Square(
        side_length=ANIM_SOLID_SQUARE_SIDE,
        fill_color=color,
        fill_opacity=ANIM_SOLID_SQUARE_FILL_OPACITY,
        stroke_color=WHITE,
        stroke_width=ANIM_SOLID_STROKE_WIDTH,
    )


def create_muddler(container_height):
    head = RoundedRectangle(
        corner_radius=ANIM_MUDDLER_HEAD_CORNER_RADIUS,
        height=ANIM_MUDDLER_HEAD_HEIGHT,
        width=ANIM_MUDDLER_HEAD_WIDTH,
        fill_color=ANIM_COLOR_MUDDLER_WOOD_DARK,
        fill_opacity=1,
        stroke_color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
    )
    groove = Line(
        head.get_left() + RIGHT * ANIM_MUDDLER_GROOVE_INSET,
        head.get_right() + LEFT * ANIM_MUDDLER_GROOVE_INSET,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
        color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
    ).shift(DOWN * ANIM_MUDDLER_GROOVE_DROP)

    handle_length = max(container_height + ANIM_MUDDLER_HANDLE_HEIGHT_PADDING, ANIM_MUDDLER_HANDLE_MIN_HEIGHT)
    handle = RoundedRectangle(
        corner_radius=ANIM_MUDDLER_HANDLE_CORNER_RADIUS,
        height=handle_length,
        width=ANIM_MUDDLER_HANDLE_WIDTH,
        fill_color=ANIM_COLOR_MUDDLER_WOOD_LIGHT,
        fill_opacity=1,
        stroke_color=ANIM_COLOR_MUDDLER_WOOD_MEDIUM,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
    ).next_to(head, UP, buff=-ANIM_MUDDLER_HANDLE_OVERLAP)

    pommel = Circle(
        radius=ANIM_MUDDLER_POMMEL_RADIUS,
        fill_color=ANIM_COLOR_MUDDLER_WOOD_DARK,
        fill_opacity=1,
        stroke_color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
        stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
    ).next_to(handle, UP, buff=-ANIM_MUDDLER_POMMEL_OVERLAP)

    muddler = VGroup(head, groove, handle, pommel)
    muddler.set_z_index(ANIM_TOOL_Z_INDEX)
    return muddler


def create_stir_spoon(container_height):
    stem_length = container_height + ANIM_SPOON_STEM_HEIGHT_PADDING

    bowl = Ellipse(
        width=ANIM_SPOON_BOWL_WIDTH,
        height=ANIM_SPOON_BOWL_HEIGHT,
        fill_color=ANIM_COLOR_SPOON_METAL_LIGHT,
        fill_opacity=1,
        stroke_color=ANIM_COLOR_SPOON_METAL_DARK,
        stroke_width=ANIM_SPOON_STROKE_WIDTH,
    )
    inner = Ellipse(
        width=ANIM_SPOON_INNER_WIDTH,
        height=ANIM_SPOON_INNER_HEIGHT,
        fill_color=ANIM_COLOR_SPOON_INNER,
        fill_opacity=ANIM_SPOON_INNER_OPACITY,
        stroke_width=0,
    ).shift(LEFT * ANIM_SPOON_INNER_X_SHIFT)

    stem = Line(
        bowl.get_top(),
        bowl.get_top() + UP * stem_length,
        stroke_width=ANIM_SPOON_STEM_STROKE_WIDTH,
        color=ANIM_COLOR_SPOON_METAL_LIGHT,
    )

    spirals = VGroup()
    for y_off in np.linspace(
        ANIM_SPOON_SPIRAL_MARGIN, stem_length - ANIM_SPOON_SPIRAL_MARGIN, ANIM_SPOON_SPIRAL_COUNT
    ):
        spirals.add(
            Line(
                stem.get_start() + UP * y_off + LEFT * ANIM_SPOON_SPIRAL_X_OFFSET,
                stem.get_start() + UP * (y_off + ANIM_SPOON_SPIRAL_Y_STEP) + RIGHT * ANIM_SPOON_SPIRAL_X_OFFSET,
                stroke_width=ANIM_SPOON_STROKE_WIDTH,
                color=ANIM_COLOR_SPOON_METAL_DARK,
            )
        )

    knob = Circle(
        radius=ANIM_SPOON_KNOB_RADIUS,
        fill_color=ANIM_COLOR_SPOON_KNOB,
        fill_opacity=1,
        stroke_color=ANIM_COLOR_SPOON_KNOB_STROKE,
        stroke_width=ANIM_SPOON_KNOB_STROKE_WIDTH,
    ).next_to(stem, UP, buff=0)

    spoon = VGroup(bowl, inner, stem, spirals, knob)
    spoon.set_z_index(ANIM_TOOL_Z_INDEX)
    return spoon


def create_pour_curve(lip_point, target_point, color):
    start = lip_point + _offset(*ANIM_STRAIN_POUR_START_OFFSET)
    return CubicBezier(
        start,
        start + _offset(*ANIM_STRAIN_POUR_CONTROL_1_OFFSET),
        target_point + _offset(*ANIM_STRAIN_POUR_CONTROL_2_OFFSET),
        target_point,
        color=color,
        stroke_width=ANIM_STRAIN_POUR_STROKE_WIDTH,
    )


def create_garnish(shape, color, dest_container):
    if "leaf" in shape:
        return Ellipse(
            width=ANIM_GARNISH_LEAF_WIDTH,
            height=ANIM_GARNISH_LEAF_HEIGHT,
            fill_color=color,
            fill_opacity=1,
            stroke_color=WHITE,
            stroke_width=ANIM_GARNISH_STROKE_WIDTH,
        )
    if "half circle" in shape:
        return AnnularSector(
            inner_radius=ANIM_GARNISH_HALF_CIRCLE_INNER_RADIUS,
            outer_radius=ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS,
            angle=PI,
            start_angle=0,
            fill_color=color,
            fill_opacity=1,
            stroke_color=WHITE,
            stroke_width=ANIM_GARNISH_STROKE_WIDTH,
        )
    if "traingle" in shape or "triangle" in shape:
        return Triangle(
            fill_color=color, fill_opacity=1, stroke_color=WHITE, stroke_width=ANIM_GARNISH_STROKE_WIDTH
        ).scale(ANIM_GARNISH_TRIANGLE_SCALE)
    if "dashes" in shape:
        first = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=color)
        second = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=color).next_to(first, RIGHT, buff=ANIM_GARNISH_DASH_BUFF)
        third = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=color).next_to(second, RIGHT, buff=ANIM_GARNISH_DASH_BUFF)
        return VGroup(first, second, third)
    if "foam" in shape:
        return RoundedRectangle(
            corner_radius=ANIM_GARNISH_FOAM_CORNER_RADIUS,
            height=ANIM_GARNISH_FOAM_HEIGHT,
            width=dest_container.w_top * ANIM_GARNISH_FOAM_WIDTH_RATIO,
            fill_color=WHITE,
            fill_opacity=ANIM_GARNISH_FOAM_OPACITY,
            stroke_width=0,
        )
    return Square(
        side_length=ANIM_SOLID_SQUARE_SIDE,
        fill_color=color,
        fill_opacity=1,
        stroke_color=WHITE,
        stroke_width=ANIM_GARNISH_STROKE_WIDTH,
    )
