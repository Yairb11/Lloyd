import copy
from typing import Any

from claude_agent_sdk import tool
from jsonschema import ValidationError, validate

from app.core import perf

NAME: str = "render_animation"

ROUTING: str = (
    "the user wants a step-by-step build to follow along with -> render_animation"
)

DESCRIPTION: str = (
    "Play the step-by-step build animation for one cocktail on the user's screen. "
    "Call this AFTER you have already written your spoken reply as plain text, and "
    "only once per named cocktail. The spec is the COMPLETE build for the whole "
    "drink, not just the checkpoint you are currently narrating -- it drives a "
    "one-time render, not the conversation. Ground the method in IBA Official "
    "Cocktails, Difford's Guide or the Cocktail Codex root templates, use metric "
    "units only, and shake drinks containing citrus, egg white or dairy while "
    "stirring all-spirit drinks. The spec is validated against this schema before "
    "anything is drawn: a missing field, a misspelled enum value or an extra "
    "property rejects the whole call."
)

RESULT: str = "Animation started."
ERROR_SCHEMA: str = "The animation spec was rejected by the schema:"

_GLASSES: list[str] = ["coupe", "rocks", "highball", "martini", "nick_and_nora"]

SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "StrictCocktailRecipe",
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
        "name": {"type": "string", "description": "Display name, e.g. Old Fashioned."},
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
            "description": "Every ingredient in the drink. Step actions reference these by id.",
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
                    "name": {"type": "string", "description": "Display name of the ingredient."},
                    "type": {
                        "type": "string",
                        "enum": ["liquid", "solid", "bitters"],
                        "description": (
                            "liquid pours as a layer, solid drops in as an object "
                            "such as a sugar cube or mint leaves, bitters dashes in."
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
                        "description": "ml for liquids, count for solids, dash for bitters. Never oz.",
                    },
                    "color_hex": {
                        "type": "string",
                        "pattern": "^#[0-9A-Fa-f]{6}$",
                        "description": (
                            "The ingredient's real colour in the glass, used to paint the "
                            "liquid layer. Campari #C81A17, bourbon #B85A1E, gin #F2F2F0, "
                            "sweet vermouth #6E1A11, lime juice #D4E157."
                        ),
                    },
                },
            },
        },
        "steps": {
            "type": "array",
            "minItems": 2,
            "description": (
                "The build in order. The FIRST step must always be a chill action "
                "targeting serving_glass with a glass matching glass_type."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "instruction", "action"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Two to four words naming the step, e.g. Muddle the sugar.",
                    },
                    "instruction": {
                        "type": "string",
                        "description": "One short sentence shown under the title while this step plays.",
                    },
                    "action": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name"],
                        "description": "What is drawn. Only the fields relevant to this action name.",
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
                            "duration_sec": {"type": "integer"},
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
                                    "Garnish silhouette. half circle for a citrus wheel, leaf "
                                    "for mint or basil. Prefer triangle; traingle is a legacy "
                                    "spelling kept so older saved specs still validate."
                                ),
                            },
                        },
                    },
                },
            },
            "allOf": [
                {
                    "properties": {
                        "steps": {
                            "items": [
                                {
                                    "properties": {
                                        "action": {
                                            "properties": {"name": {"const": "chill"}},
                                            "required": ["name", "target", "glass"],
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            ],
        },
    },
}


def input_schema() -> dict:
    schema = copy.deepcopy(SCHEMA)
    schema.pop("$schema", None)
    schema.pop("title", None)
    steps = schema.get("properties", {}).get("steps")
    if isinstance(steps, dict):
        steps.pop("allOf", None)
    return schema


def build(handlers: Any):
    async def render_animation(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.render_animation")
        try:
            validate(instance=args, schema=SCHEMA)
        except ValidationError as exc:
            return {
                "content": [{"type": "text", "text": f"{ERROR_SCHEMA} {exc.message}"}],
                "is_error": True,
            }
        handlers.on_animation(args)
        return {"content": [{"type": "text", "text": RESULT}]}

    return tool(NAME, DESCRIPTION, input_schema())(render_animation)
