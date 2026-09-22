import numpy as np
from manim import (
    AnimationGroup, BLUE_A, BOLD,
    Create, DOWN, FadeIn,
    FadeOut, GOLD, LEFT,
    Line, MoveAlongPath, ParametricFunction,
    PI, ReplacementTransform, RIGHT,
    Scene, Succession, Text,
    UL, UP, VGroup,
    VMobject, WHITE, Wiggle,
    YELLOW, linear,
)

from app.animation.props import (
    create_garnish, create_ice_cube, create_ice_rock,
    create_ice_sphere, create_ingredient_entry, create_muddler,
    create_pour_curve, create_solid_ingredient, create_stir_spoon,
)
from app.animation.recipe import Recipe, is_top_step, needs_shaker, wrap_instruction
from app.animation.vessel import Container, VesselState
from app.config import (
    ANIM_CHILL_FADE_IN_RUN_TIME, ANIM_CHILL_FADE_OUT_RUN_TIME, ANIM_CHILL_FADE_TARGET_OPACITY,
    ANIM_CHILL_FROST_STROKE_OPACITY, ANIM_CHILL_FROST_STROKE_WIDTH, ANIM_COLOR_DEFAULT_GARNISH,
    ANIM_COLOR_DEFAULT_LIQUID, ANIM_COLOR_DEFAULT_MUDDLE_BLEND, ANIM_COLOR_DEFAULT_SHAKE_BLEND,
    ANIM_COLOR_DEFAULT_STIR_BLEND, ANIM_COLOR_DEFAULT_STRAIN, ANIM_COLOR_FOAM,
    ANIM_DEFAULT_STEP_WAIT_S, ANIM_FINALE_FADE_RUN_TIME, ANIM_FINAL_WAIT_S,
    ANIM_GARNISH_DEFAULT_SHAPE, ANIM_GARNISH_FADE_RUN_TIME, ANIM_GARNISH_FADE_SHIFT,
    ANIM_GARNISH_SIDE_OFFSET, ANIM_GARNISH_SURFACE_Y_OFFSET, ANIM_GARNISH_Z_INDEX,
    ANIM_ICE_CUBE_COUNT_PREP, ANIM_ICE_CUBE_COUNT_SERVING, ANIM_ICE_CUBE_FADE_RUN_TIME,
    ANIM_ICE_CUBE_FADE_SHIFT, ANIM_ICE_CUBE_HEIGHT_DELTA, ANIM_ICE_CUBE_LAG_RATIO,
    ANIM_ICE_CUBE_X_SPACING, ANIM_ICE_CUBE_Y_OFFSET, ANIM_ICE_LARGE_FADE_RUN_TIME,
    ANIM_ICE_LARGE_FADE_SHIFT, ANIM_ICE_LARGE_HEIGHT_DELTA, ANIM_ICE_LARGE_Y_OFFSET,
    ANIM_INGREDIENT_COMPACT_THRESHOLD, ANIM_INGREDIENT_FONT_SIZE_COMPACT, ANIM_INGREDIENT_FONT_SIZE_NORMAL,
    ANIM_INGREDIENT_LIST_BUFF_COMPACT, ANIM_INGREDIENT_LIST_BUFF_NORMAL, ANIM_INGREDIENT_LIST_FADE_RUN_TIME,
    ANIM_INGREDIENT_LIST_FADE_SHIFT, ANIM_INGREDIENT_PANEL_BUFF, ANIM_LABEL_MIXING_GLASS,
    ANIM_LABEL_SERVING_GLASS, ANIM_LABEL_SHAKER, ANIM_MEASURE_DASH_HEIGHT_SCALE,
    ANIM_MEASURE_DEFAULT_AMOUNT_ML, ANIM_MEASURE_FALLBACK_THICKNESS, ANIM_MEASURE_LAYER_FADE_RUN_TIME,
    ANIM_MEASURE_LAYER_FADE_SHIFT, ANIM_MEASURE_MAX_FILL_MARGIN, ANIM_MEASURE_MIN_AVAILABLE_HEIGHT,
    ANIM_MEASURE_STREAM_CREATE_RUN_TIME, ANIM_MEASURE_STREAM_START_OFFSET, ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID,
    ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER, ANIM_MEASURE_STREAM_Z_INDEX, ANIM_MEASURE_TOP_MARGIN,
    ANIM_MEASURE_TOP_MIN_THICKNESS, ANIM_ML_TO_HEIGHT_SCALE, ANIM_MUDDLER_BOTTOM_OFFSET,
    ANIM_MUDDLER_FADE_IN_RUN_TIME, ANIM_MUDDLER_FADE_IN_SHIFT, ANIM_MUDDLER_FADE_OUT_RUN_TIME,
    ANIM_MUDDLER_FADE_OUT_SHIFT, ANIM_MUDDLER_STROKES, ANIM_MUDDLER_STROKE_RUN_TIME,
    ANIM_MUDDLE_MERGE_RUN_TIME, ANIM_MUDDLE_MIN_HEIGHT, ANIM_SHAKE_MERGE_RUN_TIME,
    ANIM_SHAKE_WIGGLE_COUNT, ANIM_SHAKE_WIGGLE_ROTATION, ANIM_SHAKE_WIGGLE_RUN_TIME,
    ANIM_SHAKE_WIGGLE_SCALE, ANIM_SOLIDS_Z_INDEX, ANIM_SOLID_FADE_RUN_TIME,
    ANIM_SOLID_FADE_SHIFT, ANIM_SOLID_HEIGHT_DELTA, ANIM_SOLID_Y_OFFSET,
    ANIM_SPOON_FADE_IN_RUN_TIME, ANIM_SPOON_FADE_IN_SHIFT, ANIM_SPOON_FADE_OUT_RUN_TIME,
    ANIM_SPOON_FADE_OUT_SHIFT, ANIM_STEP_DESC_BUFF, ANIM_STEP_DESC_FONT_SIZE,
    ANIM_STEP_DESC_LINE_SPACING, ANIM_STEP_TITLE_FONT_SIZE, ANIM_STEP_TITLE_Y,
    ANIM_STEP_TRANSFORM_RUN_TIME, ANIM_STEP_WRAP_WORDS_PER_LINE, ANIM_STIR_MERGE_RUN_TIME,
    ANIM_STIR_ORBIT_ANGLE_PI_MULTIPLIER, ANIM_STIR_ORBIT_RADIUS_RATIO, ANIM_STIR_ORBIT_RUN_TIME,
    ANIM_STIR_ORBIT_RY, ANIM_STIR_ORBIT_Y_OFFSET, ANIM_STIR_SOLIDS_ROTATE,
    ANIM_STRAIN_FOAM_FADE_SHIFT, ANIM_STRAIN_FOAM_MIN_LIQUID_THICKNESS, ANIM_STRAIN_FOAM_OPACITY,
    ANIM_STRAIN_FOAM_THICKNESS, ANIM_STRAIN_FOAM_Z_INDEX, ANIM_STRAIN_LAYER_FADE_SHIFT,
    ANIM_STRAIN_POUR_CREATE_RUN_TIME, ANIM_STRAIN_POUR_FADE_RUN_TIME, ANIM_STRAIN_RIM_MARGIN,
    ANIM_STRAIN_TILT_ANGLE, ANIM_STRAIN_TILT_BACK_RUN_TIME, ANIM_STRAIN_TILT_RUN_TIME,
    ANIM_STRAIN_TRANSFER_RUN_TIME, ANIM_TITLE_BUFF, ANIM_TITLE_FADE_RUN_TIME,
    ANIM_TITLE_FADE_SHIFT, ANIM_TITLE_FONT_SIZE, ANIM_VESSEL_CREATE_RUN_TIME,
    ANIM_VESSEL_PAIR_X_OFFSET, ANIM_VESSEL_Y_OFFSET,
)
from app.core.color import hex_to_rgb, rgb_to_hex

SERVING_GLASS = "serving_glass"
PREP_VESSEL = "prep"
LIQUID_TYPES = ("liquid", "bitters")


class StepContext:
    def __init__(self, action, state, top_step):
        self.action = action
        self.state = state
        self.container = state.container
        outline = self.container.outline
        self.cx = outline.get_bottom()[0]
        self.bot_y = outline.get_bottom()[1]
        self.top_y = outline.get_top()[1]
        self.is_top_step = top_step


def _blend_liquid_colors(state, default_hex):
    if not state.liquid_colors:
        return default_hex
    rgbs = [hex_to_rgb(color) for color in state.liquid_colors]
    return rgb_to_hex(np.mean(rgbs, axis=0))


def _create_foam_layer(dest):
    foam = dest.container.get_layer_polygon(
        dest.liquid_h,
        dest.liquid_h + ANIM_STRAIN_FOAM_THICKNESS,
        color=ANIM_COLOR_FOAM,
        opacity=ANIM_STRAIN_FOAM_OPACITY,
    )
    foam.set_z_index(ANIM_STRAIN_FOAM_Z_INDEX)
    dest.liquid_h += ANIM_STRAIN_FOAM_THICKNESS
    return foam


class CocktailAnimationScene(Scene):
    def __init__(self, recipe_data=None, **kwargs):
        super().__init__(**kwargs)
        self.recipe_data = recipe_data or {}

        self._recipe = None
        self._vessels = {}
        self._on_screen_vessels = set()
        self._active_target = None
        self._already_strained = False
        self._step_title = VMobject()
        self._step_inst = VMobject()
        self._action_handlers = {
            "chill": self._chill,
            "ice": self._add_ice,
            "measure": self._measure,
            "shake": self._shake,
            "muddle": self._muddle,
            "stir": self._stir,
            "strain": self._strain,
            "garnish": self._garnish,
        }

    def construct(self):
        self._recipe = Recipe(self.recipe_data)

        self._show_title()
        self._show_ingredient_panel()
        self._setup_vessels()

        for step in self._recipe.steps:
            self._play_step(step)

        self._play_finale()

    def _show_title(self):
        title = Text(
            self._recipe.name, font_size=ANIM_TITLE_FONT_SIZE, weight=BOLD, color=GOLD
        ).to_edge(UP, buff=ANIM_TITLE_BUFF)
        self.play(FadeIn(title, shift=DOWN * ANIM_TITLE_FADE_SHIFT), run_time=ANIM_TITLE_FADE_RUN_TIME)

    def _show_ingredient_panel(self):
        ingredients = self._recipe.ingredients
        if not ingredients:
            return

        compact = len(ingredients) > ANIM_INGREDIENT_COMPACT_THRESHOLD
        font_size = ANIM_INGREDIENT_FONT_SIZE_COMPACT if compact else ANIM_INGREDIENT_FONT_SIZE_NORMAL
        panel = VGroup(*(create_ingredient_entry(ingredient, font_size) for ingredient in ingredients))
        panel.arrange(
            DOWN,
            aligned_edge=LEFT,
            buff=ANIM_INGREDIENT_LIST_BUFF_COMPACT if compact else ANIM_INGREDIENT_LIST_BUFF_NORMAL,
        )
        panel.to_corner(UL, buff=ANIM_INGREDIENT_PANEL_BUFF)
        self.play(
            FadeIn(panel, shift=RIGHT * ANIM_INGREDIENT_LIST_FADE_SHIFT),
            run_time=ANIM_INGREDIENT_LIST_FADE_RUN_TIME,
        )

    def _setup_vessels(self):
        recipe = self._recipe
        vessel_y = DOWN * ANIM_VESSEL_Y_OFFSET

        if recipe.build_in_glass:
            serving = Container(recipe.glass_type, label=ANIM_LABEL_SERVING_GLASS).move_to(vessel_y)
            self._vessels[SERVING_GLASS] = VesselState(serving)
            self._active_target = SERVING_GLASS
            return

        if needs_shaker(recipe.steps):
            prep_type, prep_label = "shaker", ANIM_LABEL_SHAKER
        else:
            prep_type, prep_label = "mixing_glass", ANIM_LABEL_MIXING_GLASS
        prep = Container(prep_type, label=prep_label).move_to(LEFT * ANIM_VESSEL_PAIR_X_OFFSET + vessel_y)
        serving = Container(recipe.glass_type, label=ANIM_LABEL_SERVING_GLASS).move_to(
            RIGHT * ANIM_VESSEL_PAIR_X_OFFSET + vessel_y
        )
        self._vessels[PREP_VESSEL] = VesselState(prep)
        self._vessels[SERVING_GLASS] = VesselState(serving)
        self._active_target = PREP_VESSEL

    def _ensure_vessel_visible(self, state):
        if state.container not in self._on_screen_vessels:
            self.play(Create(state.container), run_time=ANIM_VESSEL_CREATE_RUN_TIME)
            self._on_screen_vessels.add(state.container)

    def _play_finale(self):
        self.play(
            FadeOut(self._step_title), FadeOut(self._step_inst), run_time=ANIM_FINALE_FADE_RUN_TIME
        )
        self.wait(ANIM_FINAL_WAIT_S)

    def _play_step(self, step):
        title = step.get("title", "")
        instruction = step.get("instruction", "")
        self._show_step_text(title, instruction)

        action = step.get("action", {})
        action_name = (action.get("name") if isinstance(action, dict) else str(action)).lower()
        top_step = is_top_step(title, instruction, action)

        state = self._select_vessel_state(action, top_step)
        self._ensure_vessel_visible(state)
        context = StepContext(action, state, top_step)

        handler = self._action_handlers.get(action_name)
        if handler is not None:
            handler(context)

        self.wait(ANIM_DEFAULT_STEP_WAIT_S)

    def _show_step_text(self, title, instruction):
        new_title = Text(
            title, font_size=ANIM_STEP_TITLE_FONT_SIZE, weight=BOLD, color=YELLOW
        ).move_to(UP * ANIM_STEP_TITLE_Y)
        new_inst = Text(
            wrap_instruction(instruction, ANIM_STEP_WRAP_WORDS_PER_LINE),
            font_size=ANIM_STEP_DESC_FONT_SIZE,
            color=WHITE,
            line_spacing=ANIM_STEP_DESC_LINE_SPACING,
        )
        new_inst.next_to(new_title, DOWN, buff=ANIM_STEP_DESC_BUFF)

        self.play(
            ReplacementTransform(self._step_title, new_title),
            ReplacementTransform(self._step_inst, new_inst),
            run_time=ANIM_STEP_TRANSFORM_RUN_TIME,
        )
        self._step_title = new_title
        self._step_inst = new_inst

    def _select_vessel_state(self, action, top_step):
        target = action.get("target")
        if self._recipe.build_in_glass or target == SERVING_GLASS or self._already_strained or top_step:
            return self._vessels[SERVING_GLASS]
        if target in ("shaker", "mixing_glass"):
            return self._vessels.get(PREP_VESSEL, self._vessels.get(SERVING_GLASS))
        return self._vessels.get(self._active_target)

    def _merge_layers(self, state, merged, total_h, color, run_time, *, absorb_solids):
        fading = [FadeOut(state.layers)]
        if absorb_solids:
            fading.append(FadeOut(state.solids))
        self.play(*fading, FadeIn(merged), run_time=run_time)

        state.layers = VGroup(merged)
        state.liquid_h = total_h
        state.liquid_colors = [color]
        if absorb_solids:
            state.solids = VGroup()
            state.solid_h = 0.0

    def _clear_vessel_contents(self, state):
        for sub in list(state.layers) + list(state.solids):
            self.remove(sub)
        state.layers = VGroup()
        state.solids = VGroup()
        state.liquid_h = 0.0
        state.solid_h = 0.0
        state.liquid_colors = []

    def _chill(self, ctx):
        frost = ctx.container.outline.copy().set_color(BLUE_A).set_stroke(
            width=ANIM_CHILL_FROST_STROKE_WIDTH, opacity=ANIM_CHILL_FROST_STROKE_OPACITY
        )
        self.play(
            Succession(
                FadeIn(frost, run_time=ANIM_CHILL_FADE_IN_RUN_TIME),
                frost.animate(run_time=ANIM_CHILL_FADE_OUT_RUN_TIME).set_opacity(
                    ANIM_CHILL_FADE_TARGET_OPACITY
                ),
            )
        )
        self.remove(frost)
        if not self._recipe.build_in_glass and PREP_VESSEL in self._vessels:
            self._ensure_vessel_visible(self._vessels[PREP_VESSEL])

    def _add_ice(self, ctx):
        ice_type = ctx.action.get("ice_type", "cubed")
        if ice_type == "sphere":
            self._add_large_ice(ctx, create_ice_sphere())
        elif ice_type == "large_rock":
            self._add_large_ice(ctx, create_ice_rock())
        else:
            self._add_ice_cubes(ctx)

    def _add_large_ice(self, ctx, ice):
        state = ctx.state
        ice.move_to(np.array([ctx.cx, ctx.bot_y + state.solid_h + ANIM_ICE_LARGE_Y_OFFSET, 0]))
        ice.set_z_index(ANIM_SOLIDS_Z_INDEX)
        state.solid_h += ANIM_ICE_LARGE_HEIGHT_DELTA
        self.play(FadeIn(ice, shift=DOWN * ANIM_ICE_LARGE_FADE_SHIFT), run_time=ANIM_ICE_LARGE_FADE_RUN_TIME)
        state.solids.add(ice)

    def _add_ice_cubes(self, ctx):
        state = ctx.state
        is_prep_vessel = "shaker" in ctx.container.c_type or "mixing" in ctx.container.c_type
        num_cubes = ANIM_ICE_CUBE_COUNT_PREP if is_prep_vessel else ANIM_ICE_CUBE_COUNT_SERVING

        fades = []
        for i in range(num_cubes):
            ice = create_ice_cube()
            offset_x = (i - (num_cubes - 1) / 2) * ANIM_ICE_CUBE_X_SPACING
            y_pos = ctx.bot_y + state.solid_h + ANIM_ICE_CUBE_Y_OFFSET
            ice.move_to(np.array([ctx.cx + offset_x, y_pos, 0]))
            ice.set_z_index(ANIM_SOLIDS_Z_INDEX)
            fades.append(FadeIn(ice, shift=DOWN * ANIM_ICE_CUBE_FADE_SHIFT))
            state.solids.add(ice)

        if fades:
            self.play(
                AnimationGroup(*fades, lag_ratio=ANIM_ICE_CUBE_LAG_RATIO),
                run_time=ANIM_ICE_CUBE_FADE_RUN_TIME * num_cubes * ANIM_ICE_CUBE_LAG_RATIO
                + ANIM_ICE_CUBE_FADE_RUN_TIME,
            )
        state.solid_h += ANIM_ICE_CUBE_HEIGHT_DELTA

    def _measure(self, ctx):
        item_key = ctx.action.get("what", "")
        meta = self._recipe.ingredient_lookup.get(item_key, {"color": ANIM_COLOR_DEFAULT_LIQUID, "type": "liquid"})

        if meta["type"] in LIQUID_TYPES:
            self._pour_liquid(ctx, meta["type"], meta["color"])
        else:
            self._drop_solid(ctx, item_key, meta["color"])

    def _liquid_thickness(self, ctx, ingredient_type):
        container, state, action = ctx.container, ctx.state, ctx.action
        amount = action.get("amount", ANIM_MEASURE_DEFAULT_AMOUNT_ML)

        if ctx.is_top_step:
            target_top = container.h - ANIM_MEASURE_TOP_MARGIN
            return max(target_top - state.liquid_h, ANIM_MEASURE_TOP_MIN_THICKNESS)

        if ingredient_type == "bitters" or action.get("unit") == "dash":
            thickness = float(amount) * ANIM_MEASURE_DASH_HEIGHT_SCALE
        elif isinstance(amount, (int, float)):
            thickness = float(amount) * ANIM_ML_TO_HEIGHT_SCALE
        else:
            thickness = ANIM_MEASURE_FALLBACK_THICKNESS

        max_available = max(
            (container.h - ANIM_MEASURE_MAX_FILL_MARGIN) - state.liquid_h, ANIM_MEASURE_MIN_AVAILABLE_HEIGHT
        )
        return min(thickness, max_available)

    def _pour_liquid(self, ctx, ingredient_type, color):
        state = ctx.state
        thickness = self._liquid_thickness(ctx, ingredient_type)
        layer = ctx.container.get_layer_polygon(state.liquid_h, state.liquid_h + thickness, color=color)

        stream = Line(
            np.array([ctx.cx, ctx.top_y + ANIM_MEASURE_STREAM_START_OFFSET, 0]),
            np.array([ctx.cx, ctx.bot_y + state.liquid_h, 0]),
            stroke_width=(
                ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID
                if ingredient_type == "liquid"
                else ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER
            ),
            color=color,
        )
        stream.set_z_index(ANIM_MEASURE_STREAM_Z_INDEX)

        state.liquid_h += thickness
        state.liquid_colors.append(color)

        self.play(
            Succession(
                Create(stream, run_time=ANIM_MEASURE_STREAM_CREATE_RUN_TIME),
                AnimationGroup(
                    FadeIn(layer, shift=UP * ANIM_MEASURE_LAYER_FADE_SHIFT),
                    FadeOut(stream),
                    run_time=ANIM_MEASURE_LAYER_FADE_RUN_TIME,
                ),
            )
        )
        state.layers.add(layer)

    def _drop_solid(self, ctx, item_key, color):
        state = ctx.state
        solid = create_solid_ingredient(item_key, color)
        solid.move_to(np.array([ctx.cx, ctx.bot_y + state.solid_h + ANIM_SOLID_Y_OFFSET, 0]))
        solid.set_z_index(ANIM_SOLIDS_Z_INDEX)
        state.solid_h += ANIM_SOLID_HEIGHT_DELTA
        self.play(FadeIn(solid, shift=DOWN * ANIM_SOLID_FADE_SHIFT), run_time=ANIM_SOLID_FADE_RUN_TIME)
        state.solids.add(solid)

    def _shake(self, ctx):
        state = ctx.state
        blended_hex = _blend_liquid_colors(state, ANIM_COLOR_DEFAULT_SHAKE_BLEND)
        total_h = state.liquid_h
        merged = ctx.container.get_layer_polygon(0, total_h, color=blended_hex)

        self.play(
            Succession(
                Wiggle(
                    state.get_content_group(),
                    scale_value=ANIM_SHAKE_WIGGLE_SCALE,
                    rotation_angle=ANIM_SHAKE_WIGGLE_ROTATION,
                    n_wiggles=ANIM_SHAKE_WIGGLE_COUNT,
                    run_time=ANIM_SHAKE_WIGGLE_RUN_TIME,
                ),
                AnimationGroup(
                    FadeOut(state.layers),
                    FadeOut(state.solids),
                    FadeIn(merged),
                    run_time=ANIM_SHAKE_MERGE_RUN_TIME,
                ),
            )
        )

        state.layers = VGroup(merged)
        state.liquid_h = total_h
        state.liquid_colors = [blended_hex]
        state.solids = VGroup()
        state.solid_h = 0.0

    def _muddle(self, ctx):
        state, container = ctx.state, ctx.container
        blended_hex = _blend_liquid_colors(state, ANIM_COLOR_DEFAULT_MUDDLE_BLEND)

        muddler = create_muddler(container.h)
        muddler.move_to(np.array([ctx.cx, ctx.bot_y + ANIM_MUDDLER_BOTTOM_OFFSET + muddler.height / 2, 0]))

        strokes = [
            muddler.animate(run_time=ANIM_MUDDLER_STROKE_RUN_TIME)
            .shift(UP * lift)
            .rotate(twist, about_point=muddler.get_bottom())
            for lift, twist in ANIM_MUDDLER_STROKES
        ]

        self.play(
            Succession(
                FadeIn(
                    muddler,
                    shift=DOWN * ANIM_MUDDLER_FADE_IN_SHIFT,
                    run_time=ANIM_MUDDLER_FADE_IN_RUN_TIME,
                ),
                *strokes,
                FadeOut(
                    muddler,
                    shift=UP * ANIM_MUDDLER_FADE_OUT_SHIFT,
                    run_time=ANIM_MUDDLER_FADE_OUT_RUN_TIME,
                ),
            )
        )

        total_h = max(state.liquid_h, ANIM_MUDDLE_MIN_HEIGHT)
        merged = container.get_layer_polygon(0, total_h, color=blended_hex)
        self._merge_layers(state, merged, total_h, blended_hex, ANIM_MUDDLE_MERGE_RUN_TIME, absorb_solids=True)

    def _stir(self, ctx):
        state, container = ctx.state, ctx.container
        blended_hex = _blend_liquid_colors(state, ANIM_COLOR_DEFAULT_STIR_BLEND)

        spoon = create_stir_spoon(container.h)

        cx = ctx.cx
        rx = min(container.w_bot, container.w_top) * ANIM_STIR_ORBIT_RADIUS_RATIO
        ry = ANIM_STIR_ORBIT_RY
        cy_orbit = ctx.bot_y + ANIM_STIR_ORBIT_Y_OFFSET + spoon.height / 2
        orbit = ParametricFunction(
            lambda t: np.array([cx + rx * np.cos(t), cy_orbit + ry * np.sin(t), 0]),
            t_range=[0, ANIM_STIR_ORBIT_ANGLE_PI_MULTIPLIER * PI],
        )

        spoon.move_to(np.array([cx + rx, cy_orbit, 0]))

        orbit_animations = [MoveAlongPath(spoon, orbit)]
        if len(state.solids) > 0:
            orbit_animations.append(
                state.solids.animate.rotate(ANIM_STIR_SOLIDS_ROTATE, about_point=container.get_center())
            )

        self.play(
            Succession(
                FadeIn(
                    spoon,
                    shift=DOWN * ANIM_SPOON_FADE_IN_SHIFT,
                    run_time=ANIM_SPOON_FADE_IN_RUN_TIME,
                ),
                AnimationGroup(
                    *orbit_animations,
                    run_time=ANIM_STIR_ORBIT_RUN_TIME,
                    rate_func=linear,
                ),
                FadeOut(
                    spoon,
                    shift=UP * ANIM_SPOON_FADE_OUT_SHIFT,
                    run_time=ANIM_SPOON_FADE_OUT_RUN_TIME,
                ),
            )
        )

        total_h = state.liquid_h
        merged = container.get_layer_polygon(0, total_h, color=blended_hex)
        self._merge_layers(state, merged, total_h, blended_hex, ANIM_STIR_MERGE_RUN_TIME, absorb_solids=False)

    def _strain(self, ctx):
        source = self._vessels.get(PREP_VESSEL, ctx.state)
        dest = self._vessels[SERVING_GLASS]
        self._ensure_vessel_visible(dest)

        color = source.liquid_colors[0] if source.liquid_colors else ANIM_COLOR_DEFAULT_STRAIN
        strained_layer = self._create_strained_layer(source, dest, color)

        source_container = source.container
        lip = np.array(
            [
                source_container.get_center()[0] + source_container.w_top / 2,
                source_container.outline.get_top()[1],
                0,
            ]
        )
        tilting = VGroup(source_container, source.layers, source.solids)

        self.play(
            tilting.animate.rotate(-ANIM_STRAIN_TILT_ANGLE, about_point=lip),
            run_time=ANIM_STRAIN_TILT_RUN_TIME,
        )

        pour_target = np.array([dest.container.get_center()[0], dest.container.outline.get_top()[1], 0])
        pour_curve = create_pour_curve(lip, pour_target, color)

        fading_out = [FadeOut(mob) for mob in list(source.layers) + list(source.solids)]
        incoming = [FadeIn(strained_layer, shift=UP * ANIM_STRAIN_LAYER_FADE_SHIFT)]
        foam_layer = None
        if self._recipe.has_foam:
            foam_layer = _create_foam_layer(dest)
            incoming.append(FadeIn(foam_layer, shift=DOWN * ANIM_STRAIN_FOAM_FADE_SHIFT))

        self.play(
            Succession(
                Create(pour_curve, run_time=ANIM_STRAIN_POUR_CREATE_RUN_TIME),
                AnimationGroup(*(fading_out + incoming), run_time=ANIM_STRAIN_TRANSFER_RUN_TIME),
                FadeOut(pour_curve, run_time=ANIM_STRAIN_POUR_FADE_RUN_TIME),
            )
        )

        self._clear_vessel_contents(source)

        self.play(
            source.container.animate.rotate(ANIM_STRAIN_TILT_ANGLE, about_point=lip),
            run_time=ANIM_STRAIN_TILT_BACK_RUN_TIME,
        )

        dest.layers.add(strained_layer)
        if foam_layer is not None:
            dest.layers.add(foam_layer)

        self._already_strained = True

    def _create_strained_layer(self, source, dest, color):
        rim_h = dest.container.h - ANIM_STRAIN_RIM_MARGIN
        if self._recipe.has_foam:
            liquid_thickness = max(
                rim_h - ANIM_STRAIN_FOAM_THICKNESS - dest.liquid_h, ANIM_STRAIN_FOAM_MIN_LIQUID_THICKNESS
            )
        else:
            liquid_thickness = min(source.liquid_h, rim_h - dest.liquid_h)

        layer = dest.container.get_layer_polygon(dest.liquid_h, dest.liquid_h + liquid_thickness, color=color)
        dest.liquid_h += liquid_thickness
        dest.liquid_colors.append(color)
        return layer

    def _garnish(self, ctx):
        serving = self._vessels[SERVING_GLASS]
        dest = serving.container
        action = ctx.action
        placement = action.get("placement", "float")
        color = action.get("color_hex", ANIM_COLOR_DEFAULT_GARNISH)
        shape = action.get("shape", ANIM_GARNISH_DEFAULT_SHAPE).lower()

        garnish = create_garnish(shape, color, dest)

        surface_y = dest.outline.get_bottom()[1] + serving.liquid_h + ANIM_GARNISH_SURFACE_Y_OFFSET
        dest_cx = dest.outline.get_bottom()[0]

        if placement == "rim":
            garnish.move_to(dest.get_top() + LEFT * (dest.w_top / 2) + UP * ANIM_GARNISH_SURFACE_Y_OFFSET)
        elif placement == "side_of_ice":
            garnish.move_to(np.array([dest_cx + ANIM_GARNISH_SIDE_OFFSET, surface_y, 0]))
        else:
            garnish.move_to(np.array([dest_cx, surface_y, 0]))

        garnish.set_z_index(ANIM_GARNISH_Z_INDEX)
        self.play(FadeIn(garnish, shift=DOWN * ANIM_GARNISH_FADE_SHIFT), run_time=ANIM_GARNISH_FADE_RUN_TIME)
