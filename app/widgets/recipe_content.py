import re
from typing import Any

from app.animation.recipe import ingredient_color, needs_shaker
from app.config import (
    RECIPE_CARD_DEFAULT_TITLE, RECIPE_DURATION_PATTERN, RECIPE_FOAM_LABEL,
    RECIPE_GLASS_LABELS, RECIPE_GLASS_LABEL_SUFFIX, RECIPE_METHOD_BUILT,
    RECIPE_METHOD_MIXING_GLASS, RECIPE_METHOD_SHAKER, RECIPE_STEP_NUMBER_FORMAT,
    RECIPE_TOP_UP_LABEL,
)

TOP_UP_AMOUNT: str = "top the cocktail"

_DURATION_RE = re.compile(RECIPE_DURATION_PATTERN, re.IGNORECASE)
_MULTI_SPACE_RE = re.compile(r"\s{2,}")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,;:!?])")
_SENTENCE_ENDINGS = ".!?"


def card_title(spec: dict[str, Any]) -> str:
    return str(spec.get("name") or RECIPE_CARD_DEFAULT_TITLE)


def glass_label(glass_type: Any) -> str:
    key = str(glass_type or "").strip().lower()
    if not key:
        return ""
    known = RECIPE_GLASS_LABELS.get(key)
    if known is not None:
        return known
    return f"{key.replace('_', ' ').title()} {RECIPE_GLASS_LABEL_SUFFIX}"


def method_label(spec: dict[str, Any]) -> str:
    if spec.get("build_in_serving_glass"):
        return RECIPE_METHOD_BUILT
    if needs_shaker(spec.get("steps") or []):
        return RECIPE_METHOD_SHAKER
    return RECIPE_METHOD_MIXING_GLASS


def badge_labels(spec: dict[str, Any]) -> list[str]:
    labels = [glass_label(spec.get("glass_type")), method_label(spec)]
    if spec.get("has_foam"):
        labels.append(RECIPE_FOAM_LABEL)
    return [label for label in labels if label]


def is_top_up(ingredient: dict[str, Any]) -> bool:
    return str(ingredient.get("amount", "")).strip().lower() == TOP_UP_AMOUNT


def amount_label(ingredient: dict[str, Any]) -> str:
    if is_top_up(ingredient):
        return RECIPE_TOP_UP_LABEL
    amount = ingredient.get("amount")
    if amount is None:
        return ""
    unit = str(ingredient.get("unit") or "").strip()
    return f"{_number_label(amount)} {unit}".strip()


def pip_color(ingredient: dict[str, Any]) -> str:
    return ingredient_color(ingredient)


def step_number(index: int) -> str:
    return RECIPE_STEP_NUMBER_FORMAT.format(index=index)


def instruction_text(step: dict[str, Any]) -> str:
    original = str(step.get("instruction", "")).strip()
    trimmed = _DURATION_RE.sub("", original)
    trimmed = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", _MULTI_SPACE_RE.sub(" ", trimmed)).strip()

    if not trimmed:
        return original
    if original[-1:] in _SENTENCE_ENDINGS and trimmed[-1] not in _SENTENCE_ENDINGS:
        trimmed += original[-1]
    return trimmed


def _number_label(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"