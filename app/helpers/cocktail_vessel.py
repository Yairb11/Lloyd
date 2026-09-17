import numpy as np
from manim import DOWN, GRAY_A, Line, Polygon, Text, VGroup, VMobject, WHITE

from app.config import (
    ANIM_CONTAINER_LABEL_BUFF,
    ANIM_CONTAINER_LABEL_FONT_SIZE,
    ANIM_CONTAINER_MIXING_HEIGHT,
    ANIM_CONTAINER_MIXING_W_BOT,
    ANIM_CONTAINER_MIXING_W_TOP,
    ANIM_CONTAINER_OUTLINE_STROKE_WIDTH,
    ANIM_CONTAINER_ROCKS_HEIGHT,
    ANIM_CONTAINER_ROCKS_W_BOT,
    ANIM_CONTAINER_ROCKS_W_TOP,
    ANIM_CONTAINER_SHAKER_HEIGHT,
    ANIM_CONTAINER_SHAKER_W_BOT,
    ANIM_CONTAINER_SHAKER_W_TOP,
    ANIM_CONTAINER_STEM_BASE_HALF_WIDTH,
    ANIM_CONTAINER_STEM_LENGTH,
    ANIM_CONTAINER_STEMMED_HEIGHT,
    ANIM_CONTAINER_STEMMED_W_BOT,
    ANIM_CONTAINER_STEMMED_W_TOP,
    ANIM_CONTAINER_TALL_HEIGHT,
    ANIM_CONTAINER_TALL_W_BOT,
    ANIM_CONTAINER_TALL_W_TOP,
    ANIM_LAYER_DEFAULT_OPACITY,
)


class Container(VGroup):
    """Parametric vessel supporting shaker, mixing glass, and serving glasses."""

    def __init__(self, c_type="rocks", label="", **kwargs):
        super().__init__(**kwargs)
        self.c_type = str(c_type).lower()
        self.label_text = label

        if "shaker" in self.c_type:
            w_top, w_bot, h = ANIM_CONTAINER_SHAKER_W_TOP, ANIM_CONTAINER_SHAKER_W_BOT, ANIM_CONTAINER_SHAKER_HEIGHT
            stem = False
        elif "mixing" in self.c_type:
            w_top, w_bot, h = ANIM_CONTAINER_MIXING_W_TOP, ANIM_CONTAINER_MIXING_W_BOT, ANIM_CONTAINER_MIXING_HEIGHT
            stem = False
        elif "coupe" in self.c_type or "martini" in self.c_type or "nick" in self.c_type:
            w_top, w_bot, h = ANIM_CONTAINER_STEMMED_W_TOP, ANIM_CONTAINER_STEMMED_W_BOT, ANIM_CONTAINER_STEMMED_HEIGHT
            stem = True
        elif "highball" in self.c_type or "collins" in self.c_type:
            w_top, w_bot, h = ANIM_CONTAINER_TALL_W_TOP, ANIM_CONTAINER_TALL_W_BOT, ANIM_CONTAINER_TALL_HEIGHT
            stem = False
        else:  # rocks / tumbler
            w_top, w_bot, h = ANIM_CONTAINER_ROCKS_W_TOP, ANIM_CONTAINER_ROCKS_W_BOT, ANIM_CONTAINER_ROCKS_HEIGHT
            stem = False

        self.w_top = w_top
        self.w_bot = w_bot
        self.h = h

        p_tl = np.array([-w_top / 2, h / 2, 0])
        p_tr = np.array([w_top / 2, h / 2, 0])
        p_br = np.array([w_bot / 2, -h / 2, 0])
        p_bl = np.array([-w_bot / 2, -h / 2, 0])

        self.outline = VMobject(color=WHITE, stroke_width=ANIM_CONTAINER_OUTLINE_STROKE_WIDTH)
        self.outline.set_points_as_corners([p_tl, p_bl, p_br, p_tr])
        self.add(self.outline)

        if stem:
            stem_line = Line(
                np.array([0, -h / 2, 0]),
                np.array([0, -h / 2 - ANIM_CONTAINER_STEM_LENGTH, 0]),
                stroke_width=ANIM_CONTAINER_OUTLINE_STROKE_WIDTH,
                color=WHITE,
            )
            base_line = Line(
                np.array([-ANIM_CONTAINER_STEM_BASE_HALF_WIDTH, -h / 2 - ANIM_CONTAINER_STEM_LENGTH, 0]),
                np.array([ANIM_CONTAINER_STEM_BASE_HALF_WIDTH, -h / 2 - ANIM_CONTAINER_STEM_LENGTH, 0]),
                stroke_width=ANIM_CONTAINER_OUTLINE_STROKE_WIDTH,
                color=WHITE,
            )
            self.add(stem_line, base_line)

        if label:
            self.lbl = Text(label, font_size=ANIM_CONTAINER_LABEL_FONT_SIZE, color=GRAY_A).next_to(
                self, DOWN, buff=ANIM_CONTAINER_LABEL_BUFF
            )
            self.add(self.lbl)
        else:
            self.lbl = None

    def get_layer_polygon(self, y_bot_rel, y_top_rel, color, opacity=ANIM_LAYER_DEFAULT_OPACITY):
        bot_center = self.outline.get_bottom()
        y_bot_abs = bot_center[1] + y_bot_rel
        y_top_abs = bot_center[1] + y_top_rel

        w_at_bot = self.w_bot + (self.w_top - self.w_bot) * (y_bot_rel / self.h)
        w_at_top = self.w_bot + (self.w_top - self.w_bot) * (y_top_rel / self.h)
        cx = bot_center[0]

        return Polygon(
            np.array([cx - w_at_bot / 2, y_bot_abs, 0]),
            np.array([cx + w_at_bot / 2, y_bot_abs, 0]),
            np.array([cx + w_at_top / 2, y_top_abs, 0]),
            np.array([cx - w_at_top / 2, y_top_abs, 0]),
            fill_color=color,
            fill_opacity=opacity,
            stroke_width=0,
        )


class VesselState:
    """Encapsulates vessel layers, solids, and volume metrics."""

    def __init__(self, container):
        self.container = container
        self.layers = VGroup()
        self.solids = VGroup()
        self.liquid_h = 0.0
        self.solid_h = 0.0
        self.liquid_colors = []

    def get_content_group(self):
        return VGroup(self.container, self.layers, self.solids)