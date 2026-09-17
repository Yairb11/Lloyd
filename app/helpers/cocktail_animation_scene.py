import numpy as np
from manim import (
    AnnularSector,
    BLUE_A,
    BOLD,
    Circle,
    Create,
    CubicBezier,
    Dot,
    DOWN,
    Ellipse,
    FadeIn,
    FadeOut,
    GOLD,
    LEFT,
    LIGHT_GRAY,
    Line,
    MoveAlongPath,
    ParametricFunction,
    PI,
    ReplacementTransform,
    RIGHT,
    RoundedRectangle,
    Scene,
    Square,
    Text,
    Triangle,
    UL,
    UP,
    VGroup,
    VMobject,
    WHITE,
    Wiggle,
    YELLOW,
    linear,
)

from app.config import (
    ANIM_CHILL_FADE_TARGET_OPACITY,
    ANIM_CHILL_FROST_STROKE_OPACITY,
    ANIM_CHILL_FROST_STROKE_WIDTH,
    ANIM_COLOR_DEFAULT_GARNISH,
    ANIM_COLOR_DEFAULT_INGREDIENT,
    ANIM_COLOR_DEFAULT_LIQUID,
    ANIM_COLOR_DEFAULT_MUDDLE_BLEND,
    ANIM_COLOR_DEFAULT_SHAKE_BLEND,
    ANIM_COLOR_DEFAULT_STIR_BLEND,
    ANIM_COLOR_DEFAULT_STRAIN,
    ANIM_COLOR_FOAM,
    ANIM_COLOR_ICE,
    ANIM_COLOR_MUDDLER_WOOD_DARK,
    ANIM_COLOR_MUDDLER_WOOD_DARKEST,
    ANIM_COLOR_MUDDLER_WOOD_LIGHT,
    ANIM_COLOR_MUDDLER_WOOD_MEDIUM,
    ANIM_COLOR_SPOON_INNER,
    ANIM_COLOR_SPOON_KNOB,
    ANIM_COLOR_SPOON_KNOB_STROKE,
    ANIM_COLOR_SPOON_METAL_DARK,
    ANIM_COLOR_SPOON_METAL_LIGHT,
    ANIM_DEFAULT_STEP_WAIT_S,
    ANIM_FINAL_WAIT_S,
    ANIM_GARNISH_DASH_BUFF,
    ANIM_GARNISH_DASH_RADIUS,
    ANIM_GARNISH_DEFAULT_SHAPE,
    ANIM_GARNISH_FADE_RUN_TIME,
    ANIM_GARNISH_FOAM_HEIGHT,
    ANIM_GARNISH_FOAM_OPACITY,
    ANIM_GARNISH_FOAM_WIDTH_RATIO,
    ANIM_GARNISH_HALF_CIRCLE_INNER_RADIUS,
    ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS,
    ANIM_GARNISH_LEAF_HEIGHT,
    ANIM_GARNISH_LEAF_WIDTH,
    ANIM_GARNISH_SIDE_OFFSET,
    ANIM_GARNISH_STROKE_WIDTH,
    ANIM_GARNISH_SURFACE_Y_OFFSET,
    ANIM_GARNISH_TRIANGLE_SCALE,
    ANIM_GARNISH_Z_INDEX,
    ANIM_ICE_CUBE_CORNER_RADIUS,
    ANIM_ICE_CUBE_COUNT_PREP,
    ANIM_ICE_CUBE_COUNT_SERVING,
    ANIM_ICE_CUBE_FILL_OPACITY,
    ANIM_ICE_CUBE_HEIGHT_DELTA,
    ANIM_ICE_CUBE_SIZE,
    ANIM_ICE_CUBE_X_SPACING,
    ANIM_ICE_CUBE_Y_OFFSET,
    ANIM_ICE_LARGE_FILL_OPACITY,
    ANIM_ICE_LARGE_HEIGHT_DELTA,
    ANIM_ICE_LARGE_Y_OFFSET,
    ANIM_ICE_ROCK_CORNER_RADIUS,
    ANIM_ICE_ROCK_SIZE,
    ANIM_ICE_SPHERE_RADIUS,
    ANIM_ICE_STROKE_WIDTH,
    ANIM_INGREDIENT_COMPACT_THRESHOLD,
    ANIM_INGREDIENT_DOT_RADIUS,
    ANIM_INGREDIENT_ENTRY_BUFF,
    ANIM_INGREDIENT_FONT_SIZE_COMPACT,
    ANIM_INGREDIENT_FONT_SIZE_NORMAL,
    ANIM_INGREDIENT_LIST_BUFF_COMPACT,
    ANIM_INGREDIENT_LIST_BUFF_NORMAL,
    ANIM_INGREDIENT_PANEL_BUFF,
    ANIM_ML_TO_HEIGHT_SCALE,
    ANIM_MEASURE_DASH_HEIGHT_SCALE,
    ANIM_MEASURE_DEFAULT_AMOUNT_ML,
    ANIM_MEASURE_FALLBACK_THICKNESS,
    ANIM_MEASURE_MAX_FILL_MARGIN,
    ANIM_MEASURE_MIN_AVAILABLE_HEIGHT,
    ANIM_MEASURE_STREAM_START_OFFSET,
    ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID,
    ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER,
    ANIM_MEASURE_STREAM_Z_INDEX,
    ANIM_MEASURE_TOP_MARGIN,
    ANIM_MEASURE_TOP_MIN_THICKNESS,
    ANIM_MUDDLE_MIN_HEIGHT,
    ANIM_MUDDLER_HANDLE_CORNER_RADIUS,
    ANIM_MUDDLER_HANDLE_HEIGHT_PADDING,
    ANIM_MUDDLER_HANDLE_MIN_HEIGHT,
    ANIM_MUDDLER_HANDLE_WIDTH,
    ANIM_MUDDLER_HEAD_CORNER_RADIUS,
    ANIM_MUDDLER_HEAD_HEIGHT,
    ANIM_MUDDLER_HEAD_WIDTH,
    ANIM_MUDDLER_POMMEL_RADIUS,
    ANIM_MUDDLER_STROKE_WIDTH,
    ANIM_SHAKE_WIGGLE_COUNT,
    ANIM_SHAKE_WIGGLE_ROTATION,
    ANIM_SHAKE_WIGGLE_RUN_TIME,
    ANIM_SOLID_HEIGHT_DELTA,
    ANIM_SOLID_LEAF_FILL_OPACITY,
    ANIM_SOLID_LEAF_HEIGHT,
    ANIM_SOLID_LEAF_WIDTH,
    ANIM_SOLID_SQUARE_FILL_OPACITY,
    ANIM_SOLID_SQUARE_SIDE,
    ANIM_SOLID_STROKE_WIDTH,
    ANIM_SOLID_Y_OFFSET,
    ANIM_SOLIDS_Z_INDEX,
    ANIM_SPOON_BOWL_HEIGHT,
    ANIM_SPOON_BOWL_WIDTH,
    ANIM_SPOON_INNER_HEIGHT,
    ANIM_SPOON_INNER_OPACITY,
    ANIM_SPOON_INNER_WIDTH,
    ANIM_SPOON_KNOB_RADIUS,
    ANIM_SPOON_SPIRAL_COUNT,
    ANIM_SPOON_SPIRAL_MARGIN,
    ANIM_SPOON_SPIRAL_X_OFFSET,
    ANIM_SPOON_SPIRAL_Y_STEP,
    ANIM_SPOON_STEM_HEIGHT_PADDING,
    ANIM_SPOON_STEM_STROKE_WIDTH,
    ANIM_SPOON_STROKE_WIDTH,
    ANIM_STEP_DESC_BUFF,
    ANIM_STEP_DESC_FONT_SIZE,
    ANIM_STEP_DESC_LINE_SPACING,
    ANIM_STEP_TITLE_FONT_SIZE,
    ANIM_STEP_TITLE_Y,
    ANIM_STEP_TRANSFORM_RUN_TIME,
    ANIM_STEP_WRAP_WORDS_PER_LINE,
    ANIM_STIR_ORBIT_ANGLE_PI_MULTIPLIER,
    ANIM_STIR_ORBIT_RADIUS_RATIO,
    ANIM_STIR_ORBIT_RUN_TIME,
    ANIM_STIR_ORBIT_RY,
    ANIM_STIR_ORBIT_Y_OFFSET,
    ANIM_STIR_SOLIDS_ROTATE,
    ANIM_STRAIN_FOAM_MIN_LIQUID_THICKNESS,
    ANIM_STRAIN_FOAM_THICKNESS,
    ANIM_STRAIN_FOAM_Z_INDEX,
    ANIM_STRAIN_POUR_STROKE_WIDTH,
    ANIM_STRAIN_RIM_MARGIN,
    ANIM_STRAIN_TILT_ANGLE,
    ANIM_STRAIN_TILT_BACK_RUN_TIME,
    ANIM_STRAIN_TILT_RUN_TIME,
    ANIM_STRAIN_TRANSFER_RUN_TIME,
    ANIM_TITLE_BUFF,
    ANIM_TITLE_FONT_SIZE,
    ANIM_TOOL_Z_INDEX,
    ANIM_VESSEL_CREATE_RUN_TIME,
    ANIM_VESSEL_PAIR_X_OFFSET,
    ANIM_VESSEL_Y_OFFSET,
)
from app.helpers.cocktail_vessel import Container, VesselState
from app.helpers.color_utils import hex_to_rgb, rgb_to_hex


class CocktailAnimationScene(Scene):
    def __init__(self, recipe_data=None, **kwargs):
        super().__init__(**kwargs)
        self.recipe_data = recipe_data or {}

    def construct(self):
        cocktail_name = self.recipe_data.get("name", "Cocktail")
        ingredients = self.recipe_data.get("ingredients", [])
        steps = self.recipe_data.get("steps", [])
        serving_glass_type = self.recipe_data.get("glass_type", "rocks")
        build_in_glass = self.recipe_data.get("build_in_serving_glass", False)
        has_foam = self.recipe_data.get("has_foam", False)

        # Map lookup
        ing_lookup = {}
        for ing in ingredients:
            ing_id = ing.get("id")
            ing_name = ing.get("name")
            color = ing.get("color_hex") or ing.get("color") or ANIM_COLOR_DEFAULT_INGREDIENT
            itype = ing.get("type", "liquid").lower()
            data = {"id": ing_id, "name": ing_name, "color": color, "type": itype}
            if ing_id:
                ing_lookup[ing_id] = data
            if ing_name:
                ing_lookup[ing_name] = data

        # Check vessel requirements
        needs_shaker = False
        needs_mixing_glass = False

        if not build_in_glass:
            for step in steps:
                act = step.get("action", {})
                target = act.get("target", "")
                act_name = act.get("name", "")
                if target == "shaker" or act_name == "shake":
                    needs_shaker = True
                elif target == "mixing_glass" or (act_name == "stir" and target != "serving_glass"):
                    needs_mixing_glass = True

        # Header Title
        title = Text(cocktail_name, font_size=ANIM_TITLE_FONT_SIZE, weight=BOLD, color=GOLD).to_edge(UP, buff=ANIM_TITLE_BUFF)
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=0.5)

        # Ingredients List with portions
        ing_vgroup = VGroup()
        for ing in ingredients:
            dot_col = ing.get("color_hex") or ing.get("color") or WHITE
            dot = Dot(radius=ANIM_INGREDIENT_DOT_RADIUS, color=dot_col)

            name = ing.get("name", "")
            amt = ing.get("amount")
            unit = ing.get("unit", "")

            if amt is not None:
                if isinstance(amt, (int, float)):
                    if unit == "ml":
                        amt_str = f"{amt}ml"
                    elif unit == "dash":
                        amt_str = f"{amt} dash" if amt == 1 else f"{amt} dashes"
                    elif unit == "count":
                        amt_str = f"{amt}"
                    elif unit:
                        amt_str = f"{amt} {unit}"
                    else:
                        amt_str = f"{amt}"
                else:
                    amt_str = str(amt)
                label_text = f"{name} - {amt_str}"
            else:
                label_text = name

            lbl = Text(
                label_text,
                font_size=ANIM_INGREDIENT_FONT_SIZE_COMPACT if len(ingredients) > ANIM_INGREDIENT_COMPACT_THRESHOLD else ANIM_INGREDIENT_FONT_SIZE_NORMAL,
                color=LIGHT_GRAY,
            )
            entry = VGroup(dot, lbl).arrange(RIGHT, buff=ANIM_INGREDIENT_ENTRY_BUFF)
            ing_vgroup.add(entry)

        if len(ing_vgroup) > 0:
            ing_vgroup.arrange(
                DOWN,
                aligned_edge=LEFT,
                buff=ANIM_INGREDIENT_LIST_BUFF_COMPACT if len(ingredients) > ANIM_INGREDIENT_COMPACT_THRESHOLD else ANIM_INGREDIENT_LIST_BUFF_NORMAL,
            )
            ing_vgroup.to_corner(UL, buff=ANIM_INGREDIENT_PANEL_BUFF)
            self.play(FadeIn(ing_vgroup, shift=RIGHT * 0.3), run_time=0.6)

        # Vessel instantiation
        vessels = {}
        on_screen_vessels = set()

        if build_in_glass:
            serving_glass = Container(serving_glass_type, label="Serving Glass").move_to(DOWN * ANIM_VESSEL_Y_OFFSET)
            vessels["serving_glass"] = VesselState(serving_glass)
            active_target = "serving_glass"
        else:
            prep_type = "shaker" if needs_shaker else "mixing_glass"
            prep_label = "Shaker" if needs_shaker else "Mixing Glass"
            prep_container = Container(prep_type, label=prep_label).move_to(
                LEFT * ANIM_VESSEL_PAIR_X_OFFSET + DOWN * ANIM_VESSEL_Y_OFFSET
            )
            serving_container = Container(serving_glass_type, label="Serving Glass").move_to(
                RIGHT * ANIM_VESSEL_PAIR_X_OFFSET + DOWN * ANIM_VESSEL_Y_OFFSET
            )

            vessels["prep"] = VesselState(prep_container)
            vessels["serving_glass"] = VesselState(serving_container)
            active_target = "prep"

        def ensure_vessel_visible(state):
            if state.container not in on_screen_vessels:
                self.play(Create(state.container), run_time=ANIM_VESSEL_CREATE_RUN_TIME)
                on_screen_vessels.add(state.container)

        step_title_mobj = VMobject()
        step_inst_mobj = VMobject()
        already_strained = False

        # Step Processing
        for step in steps:
            raw_title = step.get("title", "")
            raw_inst = step.get("instruction", "")

            words = raw_inst.split(" ")
            fmt_inst = ""
            for i, w in enumerate(words):
                fmt_inst += w + " "
                if (i + 1) % ANIM_STEP_WRAP_WORDS_PER_LINE == 0 and i != len(words) - 1:
                    fmt_inst += "\n"

            new_title = Text(raw_title, font_size=ANIM_STEP_TITLE_FONT_SIZE, weight=BOLD, color=YELLOW).move_to(UP * ANIM_STEP_TITLE_Y)
            new_inst = Text(fmt_inst.strip(), font_size=ANIM_STEP_DESC_FONT_SIZE, color=WHITE, line_spacing=ANIM_STEP_DESC_LINE_SPACING)
            new_inst.next_to(new_title, DOWN, buff=ANIM_STEP_DESC_BUFF)

            self.play(
                ReplacementTransform(step_title_mobj, new_title),
                ReplacementTransform(step_inst_mobj, new_inst),
                run_time=ANIM_STEP_TRANSFORM_RUN_TIME,
            )
            step_title_mobj = new_title
            step_inst_mobj = new_inst

            act = step.get("action", {})
            act_name = (act.get("name") if isinstance(act, dict) else str(act)).lower()
            target_key = act.get("target")

            is_top_step = (
                "top" in raw_title.lower()
                or "top with" in raw_inst.lower()
                or str(act.get("amount", "")).lower() == "top the cocktail"
            )

            if build_in_glass or target_key == "serving_glass" or already_strained or is_top_step:
                current_state = vessels["serving_glass"]
            elif target_key in ["shaker", "mixing_glass"]:
                current_state = vessels.get("prep", vessels.get("serving_glass"))
            else:
                current_state = vessels.get(active_target)

            ensure_vessel_visible(current_state)
            container = current_state.container
            cx = container.outline.get_bottom()[0]
            bot_y = container.outline.get_bottom()[1]
            top_y = container.outline.get_top()[1]

            # 1. Chill Action
            if act_name == "chill":
                frost = container.outline.copy().set_color(BLUE_A).set_stroke(
                    width=ANIM_CHILL_FROST_STROKE_WIDTH, opacity=ANIM_CHILL_FROST_STROKE_OPACITY
                )
                self.play(FadeIn(frost), run_time=0.4)
                self.play(frost.animate.set_opacity(ANIM_CHILL_FADE_TARGET_OPACITY), run_time=0.3)
                self.remove(frost)
                if not build_in_glass and "prep" in vessels:
                    ensure_vessel_visible(vessels["prep"])

            # 2. Ice Action
            elif act_name == "ice":
                ice_type = act.get("ice_type", "cubed")

                if ice_type in ["large_rock", "sphere"]:
                    if ice_type == "sphere":
                        ice = Circle(
                            radius=ANIM_ICE_SPHERE_RADIUS,
                            fill_color=ANIM_COLOR_ICE,
                            fill_opacity=ANIM_ICE_LARGE_FILL_OPACITY,
                            stroke_color=WHITE,
                            stroke_width=ANIM_ICE_STROKE_WIDTH,
                        )
                    else:
                        ice = RoundedRectangle(
                            corner_radius=ANIM_ICE_ROCK_CORNER_RADIUS,
                            height=ANIM_ICE_ROCK_SIZE,
                            width=ANIM_ICE_ROCK_SIZE,
                            fill_color=ANIM_COLOR_ICE,
                            fill_opacity=ANIM_ICE_LARGE_FILL_OPACITY,
                            stroke_color=WHITE,
                            stroke_width=ANIM_ICE_STROKE_WIDTH,
                        )
                    ice.move_to(np.array([cx, bot_y + current_state.solid_h + ANIM_ICE_LARGE_Y_OFFSET, 0]))
                    ice.set_z_index(ANIM_SOLIDS_Z_INDEX)
                    current_state.solid_h += ANIM_ICE_LARGE_HEIGHT_DELTA
                    self.play(FadeIn(ice, shift=DOWN * 0.8), run_time=0.35)
                    current_state.solids.add(ice)
                else:  # cubed / crushed
                    num_cubes = ANIM_ICE_CUBE_COUNT_PREP if "shaker" in container.c_type or "mixing" in container.c_type else ANIM_ICE_CUBE_COUNT_SERVING
                    for i in range(num_cubes):
                        ice = RoundedRectangle(
                            corner_radius=ANIM_ICE_CUBE_CORNER_RADIUS,
                            height=ANIM_ICE_CUBE_SIZE,
                            width=ANIM_ICE_CUBE_SIZE,
                            fill_color=ANIM_COLOR_ICE,
                            fill_opacity=ANIM_ICE_CUBE_FILL_OPACITY,
                            stroke_color=WHITE,
                            stroke_width=ANIM_ICE_STROKE_WIDTH,
                        )
                        offset_x = (i - (num_cubes - 1) / 2) * ANIM_ICE_CUBE_X_SPACING
                        y_pos = bot_y + current_state.solid_h + ANIM_ICE_CUBE_Y_OFFSET
                        ice.move_to(np.array([cx + offset_x, y_pos, 0]))
                        ice.set_z_index(ANIM_SOLIDS_Z_INDEX)
                        self.play(FadeIn(ice, shift=DOWN * 0.6), run_time=0.25)
                        current_state.solids.add(ice)
                    current_state.solid_h += ANIM_ICE_CUBE_HEIGHT_DELTA

            # 3. Measure / Add Action
            elif act_name == "measure":
                item_key = act.get("what", "")
                meta = ing_lookup.get(item_key, {"color": ANIM_COLOR_DEFAULT_LIQUID, "type": "liquid"})
                itype = meta["type"]
                col = meta["color"]

                if itype in ["liquid", "bitters"]:
                    amt = act.get("amount", ANIM_MEASURE_DEFAULT_AMOUNT_ML)

                    if is_top_step:
                        target_top = container.h - ANIM_MEASURE_TOP_MARGIN
                        thickness = max(target_top - current_state.liquid_h, ANIM_MEASURE_TOP_MIN_THICKNESS)
                    else:
                        if itype == "bitters" or act.get("unit") == "dash":
                            thickness = float(amt) * ANIM_MEASURE_DASH_HEIGHT_SCALE
                        elif isinstance(amt, (int, float)):
                            thickness = float(amt) * ANIM_ML_TO_HEIGHT_SCALE
                        else:
                            thickness = ANIM_MEASURE_FALLBACK_THICKNESS

                        max_avail = max((container.h - ANIM_MEASURE_MAX_FILL_MARGIN) - current_state.liquid_h, ANIM_MEASURE_MIN_AVAILABLE_HEIGHT)
                        thickness = min(thickness, max_avail)

                    layer = container.get_layer_polygon(
                        current_state.liquid_h, current_state.liquid_h + thickness, color=col
                    )

                    stream_start = np.array([cx, top_y + ANIM_MEASURE_STREAM_START_OFFSET, 0])
                    stream_end = np.array([cx, bot_y + current_state.liquid_h, 0])
                    stream = Line(
                        stream_start,
                        stream_end,
                        stroke_width=ANIM_MEASURE_STREAM_STROKE_WIDTH_LIQUID if itype == "liquid" else ANIM_MEASURE_STREAM_STROKE_WIDTH_OTHER,
                        color=col,
                    )
                    stream.set_z_index(ANIM_MEASURE_STREAM_Z_INDEX)

                    current_state.liquid_h += thickness
                    current_state.liquid_colors.append(col)

                    self.play(Create(stream), run_time=0.20)
                    self.play(FadeIn(layer, shift=UP * 0.05), run_time=0.35)
                    self.play(FadeOut(stream), run_time=0.15)
                    current_state.layers.add(layer)
                else:  # solid
                    if "leaf" in item_key or "basil" in item_key:
                        solid = Ellipse(
                            width=ANIM_SOLID_LEAF_WIDTH,
                            height=ANIM_SOLID_LEAF_HEIGHT,
                            fill_color=col,
                            fill_opacity=ANIM_SOLID_LEAF_FILL_OPACITY,
                            stroke_color=WHITE,
                            stroke_width=ANIM_SOLID_STROKE_WIDTH,
                        )
                    else:
                        solid = Square(
                            side_length=ANIM_SOLID_SQUARE_SIDE,
                            fill_color=col,
                            fill_opacity=ANIM_SOLID_SQUARE_FILL_OPACITY,
                            stroke_color=WHITE,
                            stroke_width=ANIM_SOLID_STROKE_WIDTH,
                        )
                    solid.move_to(np.array([cx, bot_y + current_state.solid_h + ANIM_SOLID_Y_OFFSET, 0]))
                    solid.set_z_index(ANIM_SOLIDS_Z_INDEX)
                    current_state.solid_h += ANIM_SOLID_HEIGHT_DELTA
                    self.play(FadeIn(solid, shift=DOWN * 0.8), run_time=0.35)
                    current_state.solids.add(solid)

            # 4. Shake Action
            elif act_name == "shake":
                if current_state.liquid_colors:
                    rgbs = [hex_to_rgb(c) for c in current_state.liquid_colors]
                    blended_hex = rgb_to_hex(np.mean(rgbs, axis=0))
                else:
                    blended_hex = ANIM_COLOR_DEFAULT_SHAKE_BLEND

                total_h = current_state.liquid_h
                merged = container.get_layer_polygon(0, total_h, color=blended_hex, opacity=0.92)

                rigidbody = current_state.get_content_group()
                self.play(Wiggle(
                    rigidbody, scale_value=1.0, rotation_angle=ANIM_SHAKE_WIGGLE_ROTATION,
                    n_wiggles=ANIM_SHAKE_WIGGLE_COUNT, run_time=ANIM_SHAKE_WIGGLE_RUN_TIME,
                ))

                self.play(
                    FadeOut(current_state.layers),
                    FadeOut(current_state.solids),
                    FadeIn(merged),
                    run_time=0.45,
                )

                current_state.layers = VGroup(merged)
                current_state.solids = VGroup()
                current_state.liquid_h = total_h
                current_state.solid_h = 0.0
                current_state.liquid_colors = [blended_hex]

            # 5. Muddle Action
            elif act_name == "muddle":
                if current_state.liquid_colors:
                    rgbs = [hex_to_rgb(c) for c in current_state.liquid_colors]
                    blended_hex = rgb_to_hex(np.mean(rgbs, axis=0))
                else:
                    blended_hex = ANIM_COLOR_DEFAULT_MUDDLE_BLEND

                m_head = RoundedRectangle(
                    corner_radius=ANIM_MUDDLER_HEAD_CORNER_RADIUS,
                    height=ANIM_MUDDLER_HEAD_HEIGHT,
                    width=ANIM_MUDDLER_HEAD_WIDTH,
                    fill_color=ANIM_COLOR_MUDDLER_WOOD_DARK,
                    fill_opacity=1,
                    stroke_color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
                    stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
                )
                groove = Line(
                    m_head.get_left() + RIGHT * 0.05,
                    m_head.get_right() + LEFT * 0.05,
                    stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
                    color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
                ).shift(DOWN * 0.08)

                handle_len = max(container.h + ANIM_MUDDLER_HANDLE_HEIGHT_PADDING, ANIM_MUDDLER_HANDLE_MIN_HEIGHT)
                m_handle = RoundedRectangle(
                    corner_radius=ANIM_MUDDLER_HANDLE_CORNER_RADIUS,
                    height=handle_len,
                    width=ANIM_MUDDLER_HANDLE_WIDTH,
                    fill_color=ANIM_COLOR_MUDDLER_WOOD_LIGHT,
                    fill_opacity=1,
                    stroke_color=ANIM_COLOR_MUDDLER_WOOD_MEDIUM,
                    stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
                ).next_to(m_head, UP, buff=-0.08)

                m_pommel = Circle(
                    radius=ANIM_MUDDLER_POMMEL_RADIUS,
                    fill_color=ANIM_COLOR_MUDDLER_WOOD_DARK,
                    fill_opacity=1,
                    stroke_color=ANIM_COLOR_MUDDLER_WOOD_DARKEST,
                    stroke_width=ANIM_MUDDLER_STROKE_WIDTH,
                ).next_to(m_handle, UP, buff=-0.06)

                muddler = VGroup(m_head, groove, m_handle, m_pommel)
                muddler.set_z_index(ANIM_TOOL_Z_INDEX)

                target_bot_y = bot_y + 0.05
                muddler.move_to(np.array([cx, target_bot_y + muddler.height / 2, 0]))

                self.play(FadeIn(muddler, shift=DOWN * 1.0), run_time=0.35)

                # Realistic press & twist strokes against glass bottom
                self.play(
                    muddler.animate.shift(DOWN * 0.05).rotate(0.20, about_point=muddler.get_bottom()),
                    run_time=0.25,
                )
                self.play(
                    muddler.animate.shift(UP * 0.15).rotate(-0.40, about_point=muddler.get_bottom()),
                    run_time=0.25,
                )
                self.play(
                    muddler.animate.shift(DOWN * 0.10).rotate(0.20, about_point=muddler.get_bottom()),
                    run_time=0.25,
                )
                self.play(FadeOut(muddler, shift=UP * 0.9), run_time=0.3)

                total_h = max(current_state.liquid_h, ANIM_MUDDLE_MIN_HEIGHT)
                merged = container.get_layer_polygon(0, total_h, color=blended_hex, opacity=0.92)

                self.play(
                    FadeOut(current_state.layers),
                    FadeOut(current_state.solids),
                    FadeIn(merged),
                    run_time=0.40,
                )
                current_state.layers = VGroup(merged)
                current_state.solids = VGroup()
                current_state.liquid_h = total_h
                current_state.solid_h = 0.0
                current_state.liquid_colors = [blended_hex]

            # 6. Stir Action
            elif act_name == "stir":
                if current_state.liquid_colors:
                    rgbs = [hex_to_rgb(c) for c in current_state.liquid_colors]
                    blended_hex = rgb_to_hex(np.mean(rgbs, axis=0))
                else:
                    blended_hex = ANIM_COLOR_DEFAULT_STIR_BLEND

                s_bowl = Ellipse(
                    width=ANIM_SPOON_BOWL_WIDTH,
                    height=ANIM_SPOON_BOWL_HEIGHT,
                    fill_color=ANIM_COLOR_SPOON_METAL_LIGHT,
                    fill_opacity=1,
                    stroke_color=ANIM_COLOR_SPOON_METAL_DARK,
                    stroke_width=ANIM_SPOON_STROKE_WIDTH,
                )
                s_inner = Ellipse(
                    width=ANIM_SPOON_INNER_WIDTH,
                    height=ANIM_SPOON_INNER_HEIGHT,
                    fill_color=ANIM_COLOR_SPOON_INNER,
                    fill_opacity=ANIM_SPOON_INNER_OPACITY,
                    stroke_width=0,
                ).shift(LEFT * 0.03)

                stem_len = container.h + ANIM_SPOON_STEM_HEIGHT_PADDING
                s_stem = Line(
                    s_bowl.get_top(),
                    s_bowl.get_top() + UP * stem_len,
                    stroke_width=ANIM_SPOON_STEM_STROKE_WIDTH,
                    color=ANIM_COLOR_SPOON_METAL_LIGHT,
                )

                s_spirals = VGroup()
                for y_off in np.linspace(ANIM_SPOON_SPIRAL_MARGIN, stem_len - ANIM_SPOON_SPIRAL_MARGIN, ANIM_SPOON_SPIRAL_COUNT):
                    s_spirals.add(
                        Line(
                            s_stem.get_start() + UP * y_off + LEFT * ANIM_SPOON_SPIRAL_X_OFFSET,
                            s_stem.get_start() + UP * (y_off + ANIM_SPOON_SPIRAL_Y_STEP) + RIGHT * ANIM_SPOON_SPIRAL_X_OFFSET,
                            stroke_width=ANIM_SPOON_STROKE_WIDTH,
                            color=ANIM_COLOR_SPOON_METAL_DARK,
                        )
                    )

                s_knob = Circle(
                    radius=ANIM_SPOON_KNOB_RADIUS,
                    fill_color=ANIM_COLOR_SPOON_KNOB,
                    fill_opacity=1,
                    stroke_color=ANIM_COLOR_SPOON_KNOB_STROKE,
                    stroke_width=1,
                ).next_to(s_stem, UP, buff=0)

                spoon = VGroup(s_bowl, s_inner, s_stem, s_spirals, s_knob)
                spoon.set_z_index(ANIM_TOOL_Z_INDEX)

                rx = min(container.w_bot, container.w_top) * ANIM_STIR_ORBIT_RADIUS_RATIO
                ry = ANIM_STIR_ORBIT_RY
                cy_orbit = bot_y + ANIM_STIR_ORBIT_Y_OFFSET + spoon.height / 2

                orbit = ParametricFunction(
                    lambda t: np.array([cx + rx * np.cos(t), cy_orbit + ry * np.sin(t), 0]),
                    t_range=[0, ANIM_STIR_ORBIT_ANGLE_PI_MULTIPLIER * PI],
                )

                spoon.move_to(np.array([cx + rx, cy_orbit, 0]))
                self.play(FadeIn(spoon, shift=DOWN * 0.8), run_time=0.35)

                if len(current_state.solids) > 0:
                    self.play(
                        MoveAlongPath(spoon, orbit),
                        current_state.solids.animate.rotate(ANIM_STIR_SOLIDS_ROTATE, about_point=container.get_center()),
                        run_time=ANIM_STIR_ORBIT_RUN_TIME,
                        rate_func=linear,
                    )
                else:
                    self.play(
                        MoveAlongPath(spoon, orbit),
                        run_time=ANIM_STIR_ORBIT_RUN_TIME,
                        rate_func=linear,
                    )

                self.play(FadeOut(spoon, shift=UP * 0.8), run_time=0.25)

                total_h = current_state.liquid_h
                merged = container.get_layer_polygon(0, total_h, color=blended_hex, opacity=0.92)
                self.play(
                    FadeOut(current_state.layers),
                    FadeIn(merged),
                    run_time=0.40,
                )
                current_state.layers = VGroup(merged)
                current_state.liquid_h = total_h
                current_state.liquid_colors = [blended_hex]

            # 7. Strain Action
            elif act_name == "strain":
                source_state = vessels.get("prep", current_state)
                dest_state = vessels["serving_glass"]
                ensure_vessel_visible(dest_state)

                straining_color = source_state.liquid_colors[0] if source_state.liquid_colors else ANIM_COLOR_DEFAULT_STRAIN

                rim_h = dest_state.container.h - ANIM_STRAIN_RIM_MARGIN
                if has_foam:
                    foam_thickness = ANIM_STRAIN_FOAM_THICKNESS
                    liquid_thickness = max(rim_h - foam_thickness - dest_state.liquid_h, ANIM_STRAIN_FOAM_MIN_LIQUID_THICKNESS)
                else:
                    foam_thickness = 0.0
                    liquid_thickness = min(source_state.liquid_h, rim_h - dest_state.liquid_h)

                strained_layer = dest_state.container.get_layer_polygon(
                    dest_state.liquid_h, dest_state.liquid_h + liquid_thickness, color=straining_color
                )
                dest_state.liquid_h += liquid_thickness
                dest_state.liquid_colors.append(straining_color)

                # Tilt pivot point at shaker's top-right lip
                source_cx = source_state.container.get_center()[0]
                source_top_y = source_state.container.outline.get_top()[1]
                tilt_point = np.array([source_cx + source_state.container.w_top / 2, source_top_y, 0])

                tilt_mobjects = VGroup(source_state.container, source_state.layers, source_state.solids)

                # Phase 1: Shaker and contents rotate to the right
                self.play(
                    tilt_mobjects.animate.rotate(-ANIM_STRAIN_TILT_ANGLE, about_point=tilt_point),
                    run_time=ANIM_STRAIN_TILT_RUN_TIME,
                )

                # Phase 2: Vessel stops rotating. Pour stream appears and shaker liquid vanishes into serving glass
                p_start = tilt_point + DOWN * 0.05 + RIGHT * 0.05
                p_end = np.array([dest_state.container.get_center()[0], dest_state.container.outline.get_top()[1], 0])
                pour_curve = CubicBezier(
                    p_start,
                    p_start + UP * 0.35 + RIGHT * 0.55,
                    p_end + UP * 0.65 + LEFT * 0.45,
                    p_end,
                    color=straining_color,
                    stroke_width=ANIM_STRAIN_POUR_STROKE_WIDTH,
                )

                fading_out = [FadeOut(mob) for mob in list(source_state.layers) + list(source_state.solids)]
                incoming = [FadeIn(strained_layer, shift=UP * 0.15)]
                foam_layer = None

                if has_foam:
                    foam_layer = dest_state.container.get_layer_polygon(
                        dest_state.liquid_h,
                        dest_state.liquid_h + foam_thickness,
                        color=ANIM_COLOR_FOAM,
                        opacity=1.0,
                    )
                    foam_layer.set_z_index(ANIM_STRAIN_FOAM_Z_INDEX)
                    dest_state.liquid_h += foam_thickness
                    incoming.append(FadeIn(foam_layer, shift=DOWN * 0.12))

                self.play(Create(pour_curve), run_time=0.20)
                self.play(*(fading_out + incoming), run_time=ANIM_STRAIN_TRANSFER_RUN_TIME)
                self.play(FadeOut(pour_curve), run_time=0.15)

                for sub in list(source_state.layers) + list(source_state.solids):
                    self.remove(sub)
                source_state.layers = VGroup()
                source_state.solids = VGroup()
                source_state.liquid_h = 0.0
                source_state.solid_h = 0.0
                source_state.liquid_colors = []

                # Phase 3: Empty shaker rotates back upright
                self.play(
                    source_state.container.animate.rotate(ANIM_STRAIN_TILT_ANGLE, about_point=tilt_point),
                    run_time=ANIM_STRAIN_TILT_BACK_RUN_TIME,
                )

                dest_state.layers.add(strained_layer)
                if foam_layer:
                    dest_state.layers.add(foam_layer)

                already_strained = True

            # 8. Garnish Action
            elif act_name == "garnish":
                dest_container = vessels["serving_glass"].container
                placement = act.get("placement", "float")
                g_col = act.get("color_hex", ANIM_COLOR_DEFAULT_GARNISH)
                g_shape = act.get("shape", ANIM_GARNISH_DEFAULT_SHAPE).lower()

                if "leaf" in g_shape:
                    garnish = Ellipse(
                        width=ANIM_GARNISH_LEAF_WIDTH, height=ANIM_GARNISH_LEAF_HEIGHT,
                        fill_color=g_col, fill_opacity=1, stroke_color=WHITE, stroke_width=ANIM_GARNISH_STROKE_WIDTH,
                    )
                elif "half circle" in g_shape:
                    garnish = AnnularSector(
                        inner_radius=ANIM_GARNISH_HALF_CIRCLE_INNER_RADIUS,
                        outer_radius=ANIM_GARNISH_HALF_CIRCLE_OUTER_RADIUS,
                        angle=PI,
                        start_angle=0,
                        fill_color=g_col,
                        fill_opacity=1,
                        stroke_color=WHITE,
                        stroke_width=ANIM_GARNISH_STROKE_WIDTH,
                    )
                elif "traingle" in g_shape or "triangle" in g_shape:
                    garnish = Triangle(
                        fill_color=g_col, fill_opacity=1, stroke_color=WHITE, stroke_width=ANIM_GARNISH_STROKE_WIDTH
                    ).scale(ANIM_GARNISH_TRIANGLE_SCALE)
                elif "dashes" in g_shape:
                    g1 = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=g_col)
                    g2 = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=g_col).next_to(g1, RIGHT, buff=ANIM_GARNISH_DASH_BUFF)
                    g3 = Dot(radius=ANIM_GARNISH_DASH_RADIUS, color=g_col).next_to(g2, RIGHT, buff=ANIM_GARNISH_DASH_BUFF)
                    garnish = VGroup(g1, g2, g3)
                elif "foam" in g_shape:
                    garnish = RoundedRectangle(
                        corner_radius=0.1,
                        height=ANIM_GARNISH_FOAM_HEIGHT,
                        width=dest_container.w_top * ANIM_GARNISH_FOAM_WIDTH_RATIO,
                        fill_color=WHITE,
                        fill_opacity=ANIM_GARNISH_FOAM_OPACITY,
                        stroke_width=0,
                    )
                else:  # square swatch / peel
                    garnish = Square(
                        side_length=ANIM_SOLID_SQUARE_SIDE, fill_color=g_col, fill_opacity=1,
                        stroke_color=WHITE, stroke_width=ANIM_GARNISH_STROKE_WIDTH,
                    )

                surf_y = dest_container.outline.get_bottom()[1] + vessels["serving_glass"].liquid_h + ANIM_GARNISH_SURFACE_Y_OFFSET
                cx_dest = dest_container.outline.get_bottom()[0]

                if placement == "rim":
                    garnish.move_to(dest_container.get_top() + LEFT * (dest_container.w_top / 2) + UP * ANIM_GARNISH_SURFACE_Y_OFFSET)
                elif placement == "side_of_ice":
                    garnish.move_to(np.array([cx_dest + ANIM_GARNISH_SIDE_OFFSET, surf_y, 0]))
                else:  # float
                    garnish.move_to(np.array([cx_dest, surf_y, 0]))

                garnish.set_z_index(ANIM_GARNISH_Z_INDEX)
                self.play(FadeIn(garnish, shift=DOWN * 0.3), run_time=ANIM_GARNISH_FADE_RUN_TIME)

            self.wait(ANIM_DEFAULT_STEP_WAIT_S)

        # Finale
        self.play(FadeOut(step_title_mobj), FadeOut(step_inst_mobj), run_time=0.4)
        self.wait(ANIM_FINAL_WAIT_S)