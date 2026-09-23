import copy
from typing import Any
from claude_agent_sdk import tool
from jsonschema import ValidationError, validate

from app.core import perf

NAME: str = "show_recipe"

ROUTING: str = (
    "the user asks what is in a named cocktail or asks for its recipe, rather than "
    "asking to be walked through building it -> show_recipe"
)

DESCRIPTION: str = (
    "Display the recipe card for one named cocktail on the user's screen. Call this "
    "AFTER you have already written your spoken reply as plain text. The card is "
    "shown in full all at once, so the spec carries the COMPLETE build for the whole "
    "drink -- every ingredient and every step -- unlike your spoken reply, which is "
    "paced one checkpoint at a time. Each step is a single instruction sentence, with "
    "no separate heading. Ground every measurement, glass, ice and technique in IBA "
    "Official Cocktails, Difford's Guide or the Cocktail Codex root templates, use "
    "metric units only, and never invent a novelty variation. The spec is validated "
    "against this schema before the card is drawn: a missing field, a misspelled enum "
    "value or an extra property rejects the whole call."
)

RESULT: str = "Recipe card shown."
ERROR_SCHEMA: str = "The recipe spec was rejected by the schema:"

_GLASSES: list[str] = ["coupe", "rocks", "highball", "martini", "nick_and_nora"]

SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "RecipeCardSpec",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "name",
        "build_in_serving_glass",
        "glass_type",
        "has_foam",
        "ingredients",
        "steps",
    ],
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-z0-9_]+$",
            "description": "Lowercase snake_case id for this drink, e.g. old_fashioned.",
        },
        "name": {
            "type": "string",
            "description": "Display name shown as the card title, e.g. Old Fashioned.",
        },
        "build_in_serving_glass": {
            "type": "boolean",
            "description": (
                "True when the drink is assembled directly in the glass it is served "
                "in and never strained, as with an Old Fashioned or a highball. False "
                "when a shaker or mixing glass is used and the drink is strained over."
            ),
        },
        "glass_type": {"type": "string", "enum": _GLASSES},
        "has_foam": {
            "type": "boolean",
            "description": "True only when the drink contains egg white or aquafaba.",
        },
        "ingredients": {
            "type": "array",
            "minItems": 1,
            "description": (
                "Every ingredient in the drink, in the order it is added. Listed on "
                "the card with a colour pip and its measure. Step actions reference "
                "these by id."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "name", "type", "amount", "color_hex"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-z0-9_]+$",
                        "description": (
                            "Lowercase snake_case id, unique within this drink. The what "
                            "field of a measure step must match one of these exactly."
                        ),
                    },
                    "name": {
                        "type": "string",
                        "description": "Display name of the ingredient, e.g. London Dry Gin.",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["liquid", "solid", "bitters"],
                        "description": (
                            "liquid is poured, solid is dropped in such as a sugar cube "
                            "or mint leaves, bitters is dashed in."
                        ),
                    },
                    "amount": {
                        "oneOf": [
                            {"type": "number", "minimum": 0},
                            {"type": "string", "enum": ["top the cocktail"]},
                        ],
                        "description": "A number in the given unit, or the string top the cocktail.",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["ml", "count", "dash"],
                        "description": (
                            "ml for liquids, count for solids, dash for bitters. Never "
                            "oz. Omit it when amount is top the cocktail."
                        ),
                    },
                    "color_hex": {
                        "type": "string",
                        "pattern": "^#[0-9A-Fa-f]{6}$",
                        "description": (
                            "The ingredient's real colour in the glass, drawn as the "
                            "colour pip beside its name. Campari #C81A17, bourbon "
                            "#B85A1E, gin #F2F2F0, sweet vermouth #6E1A11, lime juice "
                            "#D4E157."
                        ),
                    },
                },
            },
        },
        "steps": {
            "type": "array",
            "minItems": 2,
            "description": (
                "The build in order, numbered on the card. The FIRST step must always "
                "be a chill action targeting serving_glass with a glass matching "
                "glass_type. The garnish, if there is one, is the final step."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["instruction", "action"],
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": (
                            "The whole step as one short imperative sentence, shown "
                            "beside its number on the card. There is no separate title."
                        ),
                    },
                    "action": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name"],
                        "description": (
                            "What the step does. Only the fields relevant to this "
                            "action name. technique and style are shown on the card as "
                            "chips beside the instruction."
                        ),
                        "properties": {
                            "name": {
                                "type": "string",
                                "enum": [
                                    "chill", "measure", "ice", "muddle",
                                    "stir", "shake", "strain", "garnish",
                                ],
                                "description": (
                                    "chill frosts a glass, measure pours one ingredient, ice "
                                    "adds ice, muddle presses solids, stir and shake agitate, "
                                    "strain transfers into the serving glass, garnish finishes."
                                ),
                            },
                            "target": {
                                "type": "string",
                                "enum": ["shaker", "mixing_glass", "serving_glass"],
                                "description": "Which vessel this action happens in.",
                            },
                            "glass": {"type": "string", "enum": _GLASSES},
                            "what": {
                                "type": "string",
                                "description": (
                                    "For a measure action: the id of the ingredient being "
                                    "poured. MUST match an ingredient id declared above exactly."
                                ),
                            },
                            "unit": {"type": "string", "enum": ["ml", "count", "dash"]},
                            "amount": {
                                "oneOf": [
                                    {"type": "number"},
                                    {"type": "string", "enum": ["top the cocktail"]},
                                ]
                            },
                            "ice_type": {
                                "type": "string",
                                "enum": ["cubed", "crushed", "large_rock", "sphere"],
                            },
                            "duration_sec": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "How long to stir, shake or muddle, in seconds.",
                            },
                            "style": {"type": "string", "enum": ["wet", "dry"]},
                            "technique": {"type": "string", "enum": ["single", "double"]},
                            "into": {"type": "string", "enum": ["serving_glass"]},
                            "item": {
                                "type": "string",
                                "description": "For a garnish action: what the garnish is, e.g. orange twist.",
                            },
                            "placement": {
                                "type": "string",
                                "enum": ["rim", "float", "side_of_ice"],
                                "description": "Where the garnish sits: on the rim, floating, or beside the ice.",
                            },
                            "color_hex": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                            "shape": {
                                "type": "string",
                                "enum": [
                                    "half circle", "leaf", "square",
                                    "triangle", "traingle", "foam", "dashes",
                                ],
                                "description": (
                                    "Garnish silhouette. half circle for a citrus wheel, "
                                    "leaf for mint or basil. Prefer triangle; traingle is a "
                                    "legacy spelling kept so older saved specs still validate."
                                ),
                            },
                        },
                    },
                },
            },
        },
    },
}


def input_schema() -> dict:
    schema = copy.deepcopy(SCHEMA)
    schema.pop("$schema", None)
    schema.pop("title", None)
    return schema


def build(handlers: Any):
    async def show_recipe(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.show_recipe")
        try:
            validate(instance=args, schema=SCHEMA)
        except ValidationError as exc:
            return {
                "content": [{"type": "text", "text": f"{ERROR_SCHEMA} {exc.message}"}],
                "is_error": True,
            }
        handlers.on_recipe(args)
        return {"content": [{"type": "text", "text": RESULT}]}

    return tool(NAME, DESCRIPTION, input_schema())(show_recipe)