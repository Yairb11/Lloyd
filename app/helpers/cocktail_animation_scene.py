from manim import *
from manim import config
import textwrap

class CocktailAnimationScene(Scene):
    def __init__(self, recipe_data):
        super().__init__()
        self.recipe_data = recipe_data

    def create_glass(self, glass_type: str) -> tuple[VGroup, Mobject]:
        g = glass_type.lower()
        base_y = -2.2

        if g in ("rocks", "old_fashioned", "lowball"):
            outline = Polygon(
                [-0.85, 0.2, 0],
                [-0.7, base_y, 0],
                [0.7, base_y, 0],
                [0.85, 0.2, 0],
                color=WHITE,
                stroke_width=3.5,
            )
            fill_shape = Polygon(
                [-0.8, -0.1, 0],
                [-0.68, base_y + 0.05, 0],
                [0.68, base_y + 0.05, 0],
                [0.8, -0.1, 0],
                stroke_width=0,
            )
            return VGroup(outline), fill_shape

        elif g in ("highball", "collins"):
            h = 3.2 if g == "collins" else 2.8
            w = 1.15 if g == "collins" else 1.25
            outline = RoundedRectangle(
                corner_radius=0.1, height=h, width=w, color=WHITE, stroke_width=3.5
            ).move_to([0, base_y + h / 2, 0])
            fill_shape = Rectangle(
                height=h - 0.5, width=w - 0.1, stroke_width=0
            ).align_to(outline, DOWN).shift(UP * 0.05)
            return VGroup(outline), fill_shape

        elif g == "martini":
            rim_y = 0.3
            stem_top_y = -0.9
            stem = Line([0, stem_top_y, 0], [0, base_y, 0], stroke_width=3.5, color=WHITE)
            foot = Line([-0.7, base_y, 0], [0.7, base_y, 0], stroke_width=3.5, color=WHITE)
            cone = Polygon(
                [-1.15, rim_y, 0],
                [0, stem_top_y, 0],
                [1.15, rim_y, 0],
                color=WHITE,
                stroke_width=3.5,
            )
            fill_shape = Polygon(
                [-0.98, rim_y - 0.15, 0],
                [0, stem_top_y + 0.05, 0],
                [0.98, rim_y - 0.15, 0],
                stroke_width=0,
            )
            return VGroup(cone, stem, foot), fill_shape

        elif g == "flute":
            bowl_h = 2.2
            bowl_w = 0.75
            rim_y = 0.4
            stem_top_y = rim_y - bowl_h
            bowl = RoundedRectangle(
                corner_radius=0.3, height=bowl_h, width=bowl_w, color=WHITE, stroke_width=3.5
            ).move_to([0, rim_y - bowl_h / 2, 0])
            stem = Line([0, stem_top_y, 0], [0, base_y, 0], stroke_width=3.5, color=WHITE)
            foot = Line([-0.55, base_y, 0], [0.55, base_y, 0], stroke_width=3.5, color=WHITE)
            fill_shape = RoundedRectangle(
                corner_radius=0.25, height=bowl_h - 0.4, width=bowl_w - 0.1, stroke_width=0
            ).align_to(bowl, DOWN).shift(UP * 0.05)
            return VGroup(bowl, stem, foot), fill_shape

        elif g == "nick_and_nora":
            rim_y = 0.3
            r = 0.85
            stem_top_y = rim_y - r
            bowl = Arc(
                radius=r, start_angle=PI, angle=PI, stroke_width=3.5, color=WHITE, arc_center=[0, rim_y, 0]
            )
            stem = Line([0, stem_top_y, 0], [0, base_y, 0], stroke_width=3.5, color=WHITE)
            foot = Line([-0.6, base_y, 0], [0.6, base_y, 0], stroke_width=3.5, color=WHITE)
            fill_shape = AnnularSector(
                inner_radius=0, outer_radius=r - 0.07, start_angle=PI, angle=PI, stroke_width=0, arc_center=[0, rim_y - 0.06, 0]
            )
            return VGroup(bowl, stem, foot), fill_shape

        else:
            rim_y = 0.3
            r = 1.05
            stem_top_y = rim_y - r
            bowl = Arc(
                radius=r, start_angle=PI, angle=PI, stroke_width=3.5, color=WHITE, arc_center=[0, rim_y, 0]
            )
            stem = Line([0, stem_top_y, 0], [0, base_y, 0], stroke_width=3.5, color=WHITE)
            foot = Line([-0.7, base_y, 0], [0.7, base_y, 0], stroke_width=3.5, color=WHITE)
            fill_shape = AnnularSector(
                inner_radius=0, outer_radius=r - 0.07, start_angle=PI, angle=PI, stroke_width=0, arc_center=[0, rim_y - 0.08, 0]
            )
            return VGroup(bowl, stem, foot), fill_shape

    def get_layer_shape(self, glass_type: str, y_bottom: float, y_top: float, width_max: float, color: str, opacity: float = 0.9) -> Mobject:
        g = glass_type.lower()
        if g in ("rocks", "old_fashioned", "lowball"):
            def w_at(y: float) -> float:
                t = (y - (-2.2)) / (0.2 - (-2.2))
                return 1.34 + t * (1.64 - 1.34) - 0.08
            wb = w_at(y_bottom) / 2
            wt = w_at(y_top) / 2
            return Polygon(
                [-wt, y_top, 0],
                [-wb, y_bottom, 0],
                [wb, y_bottom, 0],
                [wt, y_top, 0],
                fill_color=color,
                fill_opacity=opacity,
                stroke_width=0,
            )
        else:
            h = max(y_top - y_bottom, 0.05)
            return Rectangle(
                width=width_max,
                height=h,
                fill_color=color,
                fill_opacity=opacity,
                stroke_width=0,
            ).move_to([0, (y_bottom + y_top) / 2, 0])

    def construct(self):
        data = self.recipe_data
        ingredients = data.get("ingredients", [])
        steps = data.get("steps", [])
        glass_type = data.get("glass_type", "coupe").lower()

        is_built_in_glass = not any(s.get("action", "").lower() == "strain" for s in steps)

        if any("basil" in i["name"].lower() or "mint" in i["name"].lower() for i in ingredients):
            final_color = "#2E7D32"
        elif any("campari" in i["name"].lower() for i in ingredients):
            final_color = "#C41E3A"
        elif any("bourbon" in i["name"].lower() or "whiskey" in i["name"].lower() or "rye" in i["name"].lower() for i in ingredients):
            final_color = "#C86D27"
        else:
            final_color = ingredients[1]["color"] if len(ingredients) > 1 else "#E0A96D"

        title = Text(data.get("name", "Cocktail"), font_size=34, weight=BOLD).to_edge(UP, buff=0.35)
        self.play(FadeIn(title, shift=DOWN * 0.2))

        panel = VGroup()
        for ing in ingredients:
            dot = Dot(color=ing.get("color", "#FFFFFF"), radius=0.09)
            lbl = Text(f"{ing.get('amount', '')} {ing.get('name', '')}", font_size=16)
            panel.add(VGroup(dot, lbl).arrange(RIGHT, buff=0.18))

        panel.arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(UL, buff=0.55).shift(DOWN * 0.2)
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.2) for p in panel], lag_ratio=0.08))

        glass_group, glass_fill = self.create_glass(glass_type)

        if is_built_in_glass:
            glass_group.move_to([3.0, -1.0, 0])
            glass_fill.move_to([3.0, -1.0, 0])
            active_vessel = glass_group
            vessel_x = 3.0
            vessel_bottom = -2.15
            vessel_top_y = glass_group.get_top()[1]
            vessel_w = 1.35 if glass_type in ("rocks", "highball", "collins") else 1.6
            self.play(Create(glass_group))
        else:
            shaker = RoundedRectangle(
                corner_radius=0.15, height=3.6, width=1.8, color=LIGHT_GRAY, stroke_width=3.5
            ).move_to([1.8, -0.4, 0])
            glass_group.shift(RIGHT * 4.9)
            glass_fill.shift(RIGHT * 4.9)
            active_vessel = shaker
            vessel_x = 1.8
            vessel_bottom = shaker.get_bottom()[1] + 0.08
            vessel_top_y = shaker.get_top()[1]
            vessel_w = 1.65
            self.play(Create(shaker), Create(glass_group))

        current_fill_y = vessel_bottom
        liquid_layers = VGroup()
        added_ingredients = set()
        info_box = VGroup()
        sugar_cube_mobj = None

        for step in steps:
            self.remove(info_box)

            s_title = Text(step.get("title", ""), font_size=28, weight=BOLD, color=YELLOW)
            raw_instruction = step.get("instruction", "")
            wrapped_text = "\n".join(textwrap.wrap(raw_instruction, width=38))
            s_desc = Text(wrapped_text, font_size=19, line_spacing=1.2, color=WHITE)

            if s_desc.height > 2.0:
                s_desc.set_height(2.0)

            info_box = VGroup(s_title, s_desc).arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(DL, buff=0.45)
            self.play(FadeIn(info_box), run_time=0.25)

            action = step.get("action", "").lower()
            step_text = (step.get("title", "") + " " + step.get("instruction", "")).lower()

            if action == "prep_glass":
                if "sugar" in step_text:
                    sugar_ing = next((i for i in ingredients if "sugar" in i["name"].lower()), None)
                    if sugar_ing:
                        added_ingredients.add(sugar_ing["name"])

                    sugar_cube_mobj = Square(
                        side_length=0.38,
                        fill_color="#F8F9FA",
                        fill_opacity=1.0,
                        stroke_color=GREY_B,
                        stroke_width=2,
                    ).move_to([vessel_x, vessel_bottom + 0.19, 0])

                    self.play(FadeIn(sugar_cube_mobj, shift=DOWN * 1.5), run_time=0.4)
                    liquid_layers.add(sugar_cube_mobj)
                else:
                    ice_target = glass_group if not is_built_in_glass else active_vessel
                    glass_ice = VGroup(
                        Square(side_length=0.42, fill_color=WHITE, fill_opacity=0.55, stroke_width=1),
                        Square(side_length=0.42, fill_color=WHITE, fill_opacity=0.55, stroke_width=1),
                    ).arrange(UP, buff=0.08).move_to(ice_target.get_center() + DOWN * 0.3)
                    self.play(FadeIn(glass_ice), run_time=0.3)

            elif action == "chill":
                target_glass = glass_group if not is_built_in_glass else active_vessel
                frost = target_glass.copy().set_color(BLUE_B).set_stroke(width=4.5)
                self.play(Transform(target_glass, frost), run_time=0.4)

            elif action == "muddle":
                if sugar_cube_mobj is not None:
                    muddler = RoundedRectangle(
                        corner_radius=0.06, height=2.4, width=0.28, color=GREY_B, fill_opacity=1
                    ).move_to([vessel_x, vessel_top_y + 0.8, 0])
                    
                    self.play(muddler.animate.move_to([vessel_x, vessel_bottom + 1.25, 0]), run_time=0.35)
                    for _ in range(2):
                        self.play(muddler.animate.shift(UP * 0.2), run_time=0.1)
                        self.play(muddler.animate.shift(DOWN * 0.2), run_time=0.1)

                    paste_top_y = vessel_bottom + 0.24
                    dissolved_paste = self.get_layer_shape(glass_type, vessel_bottom, paste_top_y, vessel_w, "#5A1608").shift(RIGHT * vessel_x)

                    self.play(
                        Transform(liquid_layers, VGroup(dissolved_paste)),
                        FadeOut(muddler, shift=UP * 1.0),
                        run_time=0.35,
                    )
                    current_fill_y = paste_top_y
                    sugar_cube_mobj = None
                else:
                    muddle_candidates = [
                        i for i in ingredients
                        if any(k in i["name"].lower() for k in ("basil", "mint", "herb", "lemon", "lime"))
                        and i["name"] not in added_ingredients
                    ]
                    for item in muddle_candidates:
                        added_ingredients.add(item["name"])
                        if any(k in item["name"].lower() for k in ("basil", "mint", "leaf", "leaves")):
                            leaves = VGroup(
                                Ellipse(width=0.25, height=0.12, fill_color="#3B7A57", fill_opacity=1, stroke_width=0).rotate(0.3),
                                Ellipse(width=0.25, height=0.12, fill_color="#2E7D32", fill_opacity=1, stroke_width=0).rotate(-0.4),
                                Ellipse(width=0.22, height=0.10, fill_color="#43A047", fill_opacity=1, stroke_width=0).rotate(0.8),
                            ).arrange(RIGHT, buff=0.08).move_to([vessel_x, current_fill_y + 0.15, 0])
                            self.play(FadeIn(leaves, shift=DOWN * 1.2), run_time=0.35)
                            liquid_layers.add(leaves)
                            current_fill_y += 0.2
                        else:
                            item_col = item.get("color", "#F4E04D")
                            stream = Line(
                                [vessel_x, vessel_top_y + 0.8, 0],
                                [vessel_x, current_fill_y, 0],
                                stroke_color=item_col, stroke_width=4.5
                            )
                            rect = Rectangle(
                                width=vessel_w, height=0.45, fill_color=item_col, fill_opacity=0.9, stroke_width=0
                            ).move_to([vessel_x, current_fill_y + 0.45 / 2, 0])
                            current_fill_y += 0.45
                            liquid_layers.add(rect)
                            self.play(Create(stream), run_time=0.2)
                            self.play(GrowFromEdge(rect, DOWN), FadeOut(stream), run_time=0.35)

                    muddler = RoundedRectangle(
                        corner_radius=0.06, height=2.4, width=0.28, color=GREY_B, fill_opacity=1
                    ).move_to([vessel_x, vessel_top_y + 0.8, 0])
                    self.play(muddler.animate.shift(DOWN * 1.9), run_time=0.3)
                    for _ in range(2):
                        self.play(muddler.animate.shift(UP * 0.2), run_time=0.1)
                        self.play(muddler.animate.shift(DOWN * 0.2), run_time=0.1)
                    self.play(FadeOut(muddler, shift=UP * 0.8), run_time=0.2)

            elif action in ("measure", "combine", "pour"):
                unadded = [i for i in ingredients if i["name"] not in added_ingredients]
                matched_items = []
                for item in unadded:
                    keywords = [w.lower() for w in item["name"].split() if len(w) > 3]
                    if any(kw in step_text for kw in keywords):
                        matched_items.append(item)

                if not matched_items:
                    if "all" in step_text or "equal parts" in step_text or len(unadded) == 1:
                        matched_items = unadded
                    else:
                        matched_items = unadded[:1]

                for item in matched_items:
                    added_ingredients.add(item["name"])
                    iname = item["name"].lower()
                    item_col = item.get("color", "#FFFFFF")

                    if "bitter" in iname:
                        item_col = item.get("color", "#4A1208")
                        dashes = VGroup(
                            Dot(radius=0.07, color=item_col),
                            Dot(radius=0.06, color=item_col),
                            Dot(radius=0.07, color=item_col)
                        ).arrange(DOWN, buff=0.12).move_to([vessel_x, vessel_bottom + 0.55, 0])

                        base_layer = self.get_layer_shape(glass_type, vessel_bottom, vessel_bottom + 0.16, vessel_w, item_col).shift(RIGHT * vessel_x)
                        current_fill_y = max(current_fill_y, vessel_bottom + 0.16)
                        liquid_layers.add(base_layer)

                        self.play(FadeIn(dashes, shift=DOWN * 0.4), run_time=0.25)
                        self.play(GrowFromEdge(base_layer, DOWN), FadeOut(dashes), run_time=0.25)

                    elif is_built_in_glass:
                        step_h = 0.9 if "whiskey" in iname or "gin" in iname or "spirit" in iname else 0.35
                        layer_mobj = self.get_layer_shape(glass_type, current_fill_y, current_fill_y + step_h, vessel_w, item_col).shift(RIGHT * vessel_x)

                        stream = Line(
                            [vessel_x, vessel_top_y + 0.8, 0],
                            [vessel_x, current_fill_y, 0],
                            stroke_color=item_col,
                            stroke_width=4.5,
                        )
                        current_fill_y += step_h
                        liquid_layers.add(layer_mobj)

                        self.play(Create(stream), run_time=0.2)
                        self.play(GrowFromEdge(layer_mobj, DOWN), FadeOut(stream), run_time=0.35)

                    else:
                        layer_h = 1.7 / max(len(ingredients), 1)
                        stream = Line(
                            [vessel_x, vessel_top_y + 0.8, 0],
                            [vessel_x, current_fill_y, 0],
                            stroke_color=item_col,
                            stroke_width=4.5,
                        )
                        rect = Rectangle(
                            width=vessel_w,
                            height=layer_h,
                            fill_color=item_col,
                            fill_opacity=0.9,
                            stroke_width=0,
                        ).move_to([vessel_x, current_fill_y + layer_h / 2, 0])
                        current_fill_y += layer_h
                        liquid_layers.add(rect)

                        self.play(Create(stream), run_time=0.2)
                        self.play(GrowFromEdge(rect, DOWN), FadeOut(stream), run_time=0.35)

            elif action == "ice":
                if is_built_in_glass or "single" in step_text or "large" in step_text:
                    ice_cube = Square(side_length=0.55, fill_color=WHITE, fill_opacity=0.6, stroke_width=1.5).move_to(
                        [vessel_x, current_fill_y + 0.35, 0]
                    )
                    self.play(FadeIn(ice_cube, shift=DOWN * 0.4), run_time=0.35)
                    liquid_layers.add(ice_cube)
                else:
                    ice_cubes = VGroup(
                        Square(side_length=0.28, fill_color=WHITE, fill_opacity=0.7, stroke_width=1),
                        Square(side_length=0.28, fill_color=WHITE, fill_opacity=0.7, stroke_width=1),
                        Square(side_length=0.28, fill_color=WHITE, fill_opacity=0.7, stroke_width=1),
                    ).arrange(RIGHT, buff=0.08).next_to(current_fill_y * UP + active_vessel.get_center()[0] * RIGHT, UP, buff=0.08)
                    self.play(FadeIn(ice_cubes, shift=DOWN * 0.3), run_time=0.3)
                    liquid_layers.add(ice_cubes)

            elif action == "shake":
                blended_fill = Rectangle(
                    width=vessel_w,
                    height=max(current_fill_y - vessel_bottom, 1.2),
                    fill_color=final_color,
                    fill_opacity=0.95,
                    stroke_width=0,
                ).move_to([vessel_x, (vessel_bottom + current_fill_y) / 2, 0])

                shaker_assembly = VGroup(active_vessel, liquid_layers)
                self.play(Transform(liquid_layers, blended_fill), run_time=0.25)

                for _ in range(3):
                    self.play(shaker_assembly.animate.rotate(0.12).shift(UP * 0.15), run_time=0.08)
                    self.play(shaker_assembly.animate.rotate(-0.24).shift(DOWN * 0.3), run_time=0.08)
                    self.play(shaker_assembly.animate.rotate(0.12).shift(UP * 0.15), run_time=0.08)

            elif action == "stir":
                barspoon_shaft = Line(ORIGIN, UP * 3.2, stroke_color=LIGHT_GRAY, stroke_width=3.5)
                spoon_head = Ellipse(width=0.22, height=0.35, fill_color=GREY_A, fill_opacity=1, stroke_width=0).next_to(barspoon_shaft, DOWN, buff=0)
                barspoon = VGroup(barspoon_shaft, spoon_head).move_to([vessel_x, vessel_top_y + 0.8, 0])

                self.play(barspoon.animate.move_to([vessel_x, vessel_bottom + 1.25, 0]), run_time=0.35)

                orbit_x = 0.24
                for _ in range(3):
                    self.play(barspoon.animate.shift(RIGHT * orbit_x), run_time=0.12, rate_func=linear)
                    self.play(barspoon.animate.shift(LEFT * (orbit_x * 2)), run_time=0.18, rate_func=linear)
                    self.play(barspoon.animate.shift(RIGHT * orbit_x), run_time=0.12, rate_func=linear)

                if is_built_in_glass:
                    blended_fill = self.get_layer_shape(glass_type, vessel_bottom, min(current_fill_y + 0.15, -0.6), vessel_w, final_color, 0.92).shift(RIGHT * vessel_x)
                else:
                    blended_fill = Rectangle(
                        width=vessel_w,
                        height=max(current_fill_y - vessel_bottom, 1.2),
                        fill_color=final_color,
                        fill_opacity=0.92,
                        stroke_width=0,
                    ).move_to([vessel_x, (vessel_bottom + current_fill_y) / 2, 0])

                self.play(Transform(liquid_layers, blended_fill), FadeOut(barspoon, shift=UP * 1.2), run_time=0.4)

            elif action == "strain":
                rim_target = [glass_group.get_center()[0], glass_group.get_top()[1] - 0.15, 0]

                pour_arc = CubicBezier(
                    active_vessel.get_top() + LEFT * 0.2,
                    active_vessel.get_top() + UP * 0.6 + RIGHT * 0.4,
                    rim_target + UP * 0.5 + LEFT * 0.4,
                    rim_target,
                    color=final_color,
                    stroke_width=5.5,
                )
                glass_fill.set_fill(color=final_color, opacity=0.88)

                self.play(Create(pour_arc), run_time=0.35)
                self.play(FadeOut(liquid_layers), FadeIn(glass_fill), run_time=0.6)
                self.play(FadeOut(pour_arc), run_time=0.2)

            elif action == "garnish":
                target_glass = glass_group if not is_built_in_glass else active_vessel
                top_edge = target_glass.get_top()
                if any("basil" in i["name"].lower() or "mint" in i["name"].lower() for i in ingredients):
                    leaf1 = Ellipse(width=0.32, height=0.16, fill_color="#3B7A57", fill_opacity=1, stroke_width=0).rotate(PI / 4)
                    leaf2 = Ellipse(width=0.32, height=0.16, fill_color="#4E9B6E", fill_opacity=1, stroke_width=0).rotate(-PI / 4)
                    garnish_mob = VGroup(leaf1, leaf2).move_to(top_edge + UP * 0.1 + RIGHT * 0.35)
                elif any("orange" in i["name"].lower() or "twist" in i["name"].lower() or "peel" in step_text for i in ingredients) or "peel" in step_text:
                    garnish_mob = Arc(radius=0.28, start_angle=-PI / 3, angle=1.4 * PI, stroke_color="#FF8C00", stroke_width=4.5)
                    garnish_mob.move_to(top_edge + UP * 0.12 + RIGHT * 0.38)
                else:
                    garnish_mob = Triangle(fill_color=WHITE, fill_opacity=1, stroke_width=1).scale(0.18).rotate(-PI / 4)
                    garnish_mob.move_to(top_edge + UP * 0.12 + RIGHT * 0.65)

                self.play(FadeIn(garnish_mob, scale=1.3), run_time=0.35)

            self.wait(0.4)

        self.wait(1.5)