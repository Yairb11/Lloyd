from app.config import (
    COLOR_ACCENT, COLOR_RECIPE_BADGE_BG, COLOR_RECIPE_BADGE_TEXT,
    COLOR_RECIPE_DIVIDER, COLOR_RECIPE_TABLE_BG, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, FONT_SIZE_RECIPE_BADGE, FONT_SIZE_RECIPE_INGREDIENT,
    FONT_SIZE_RECIPE_STEP_BODY, FONT_SIZE_RECIPE_STEP_NUMBER, FONT_SIZE_RECIPE_TITLE,
    OBJECT_NAME_RECIPE_AMOUNT, OBJECT_NAME_RECIPE_AMOUNT_TOP_UP, OBJECT_NAME_RECIPE_BADGE,
    OBJECT_NAME_RECIPE_DIVIDER, OBJECT_NAME_RECIPE_INGREDIENT_NAME, OBJECT_NAME_RECIPE_SCROLL,
    OBJECT_NAME_RECIPE_SECTION_LINE, OBJECT_NAME_RECIPE_STEP_BODY, OBJECT_NAME_RECIPE_STEP_NUMBER,
    OBJECT_NAME_RECIPE_TABLE, OBJECT_NAME_RECIPE_TITLE, RECIPE_CARD_BADGE_HEIGHT,
    RECIPE_CARD_BADGE_PADDING_H, RECIPE_CARD_PIP_SIZE, RECIPE_CARD_TABLE_RADIUS,
)


def build_recipe_stylesheet() -> str:
    return f"""
    QWidget {{
        background: transparent;
        color: {COLOR_TEXT_SECONDARY};
    }}
    QLabel#{OBJECT_NAME_RECIPE_TITLE} {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_RECIPE_TITLE}px;
        font-weight: bold;
    }}
    QLabel#{OBJECT_NAME_RECIPE_BADGE} {{
        background-color: {COLOR_RECIPE_BADGE_BG};
        color: {COLOR_RECIPE_BADGE_TEXT};
        border: none;
        border-radius: {RECIPE_CARD_BADGE_HEIGHT // 2}px;
        padding: 0px {RECIPE_CARD_BADGE_PADDING_H}px;
        font-size: {FONT_SIZE_RECIPE_BADGE}px;
        font-weight: bold;
    }}
    QFrame#{OBJECT_NAME_RECIPE_TABLE} {{
        background-color: {COLOR_RECIPE_TABLE_BG};
        border: none;
        border-radius: {RECIPE_CARD_TABLE_RADIUS}px;
    }}
    QFrame#{OBJECT_NAME_RECIPE_DIVIDER} {{
        background-color: {COLOR_RECIPE_DIVIDER};
        border: none;
    }}
    QFrame#{OBJECT_NAME_RECIPE_SECTION_LINE} {{
        background-color: {COLOR_ACCENT};
        border: none;
    }}
    QLabel#{OBJECT_NAME_RECIPE_INGREDIENT_NAME} {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_RECIPE_INGREDIENT}px;
    }}
    QLabel#{OBJECT_NAME_RECIPE_AMOUNT} {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_RECIPE_INGREDIENT}px;
        font-weight: bold;
    }}
    QLabel#{OBJECT_NAME_RECIPE_AMOUNT_TOP_UP} {{
        color: {COLOR_TEXT_SECONDARY};
        font-size: {FONT_SIZE_RECIPE_INGREDIENT}px;
        font-style: italic;
    }}
    QLabel#{OBJECT_NAME_RECIPE_STEP_NUMBER} {{
        color: {COLOR_ACCENT};
        font-size: {FONT_SIZE_RECIPE_STEP_NUMBER}px;
        font-weight: bold;
    }}
    QLabel#{OBJECT_NAME_RECIPE_STEP_BODY} {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_RECIPE_STEP_BODY}px;
    }}
    QScrollArea#{OBJECT_NAME_RECIPE_SCROLL} {{
        background: transparent;
        border: none;
    }}
    """


def build_pip_style(color_hex: str) -> str:
    return (
        f"background-color: {color_hex}; border: none; "
        f"border-radius: {RECIPE_CARD_PIP_SIZE // 2}px;"
    )