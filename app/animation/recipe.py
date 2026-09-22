from app.config import ANIM_COLOR_DEFAULT_INGREDIENT, ANIM_DEFAULT_COCKTAIL_NAME, ANIM_DEFAULT_GLASS_TYPE


class Recipe:
    def __init__(self, data):
        self.name = data.get("name", ANIM_DEFAULT_COCKTAIL_NAME)
        self.glass_type = data.get("glass_type", ANIM_DEFAULT_GLASS_TYPE)
        self.ingredients = data.get("ingredients", [])
        self.steps = data.get("steps", [])
        self.build_in_glass = data.get("build_in_serving_glass", False)
        self.has_foam = data.get("has_foam", False)
        self.ingredient_lookup = build_ingredient_lookup(self.ingredients)


def build_ingredient_lookup(ingredients):
    lookup = {}
    for ingredient in ingredients:
        ing_id = ingredient.get("id")
        ing_name = ingredient.get("name")
        data = {
            "id": ing_id,
            "name": ing_name,
            "color": ingredient.get("color_hex") or ingredient.get("color") or ANIM_COLOR_DEFAULT_INGREDIENT,
            "type": ingredient.get("type", "liquid").lower(),
        }
        if ing_id:
            lookup[ing_id] = data
        if ing_name:
            lookup[ing_name] = data
    return lookup


def format_ingredient_amount(amount, unit):
    if not isinstance(amount, (int, float)):
        return str(amount)
    if unit == "ml":
        return f"{amount}ml"
    if unit == "dash":
        return f"{amount} dash" if amount == 1 else f"{amount} dashes"
    if unit == "count" or not unit:
        return f"{amount}"
    return f"{amount} {unit}"


def format_ingredient_label(ingredient):
    name = ingredient.get("name", "")
    amount = ingredient.get("amount")
    if amount is None:
        return name
    return f"{name} - {format_ingredient_amount(amount, ingredient.get('unit', ''))}"


def wrap_instruction(text, words_per_line):
    words = text.split(" ")
    wrapped = ""
    for i, word in enumerate(words):
        wrapped += word + " "
        if (i + 1) % words_per_line == 0 and i != len(words) - 1:
            wrapped += "\n"
    return wrapped.strip()


def needs_shaker(steps):
    for step in steps:
        action = step.get("action", {})
        if action.get("target", "") == "shaker" or action.get("name", "") == "shake":
            return True
    return False


def is_top_step(title, instruction, action):
    return (
        "top" in title.lower()
        or "top with" in instruction.lower()
        or str(action.get("amount", "")).lower() == "top the cocktail"
    )
