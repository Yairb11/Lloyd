from typing import Any

from claude_agent_sdk import tool

from app.core import perf

NAME: str = "show_recipe"

ROUTING: str = (
    "the user asks what is in a named cocktail or asks for its recipe, rather than "
    "asking to be walked through building it -> show_recipe"
)

DESCRIPTION: str = (
    "Display the recipe card for one named cocktail on the user's screen. Call this "
    "AFTER you have already written your spoken reply as plain text. The card is "
    "shown in full all at once, so it carries the COMPLETE recipe -- unlike your "
    "spoken reply, which is paced one checkpoint at a time. Ground every "
    "measurement, glass, ice and technique in IBA Official Cocktails, Difford's "
    "Guide or the Cocktail Codex root templates. Never invent a novelty variation."
)

RESULT: str = "Recipe card shown."

SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "glass_type", "ice", "technique", "ingredients", "steps"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The cocktail's canonical name, title-cased, e.g. Old Fashioned.",
        },
        "category": {
            "type": "string",
            "description": (
                "Optional Cocktail Codex family this drink is a variation of: "
                "Old Fashioned, Martini, Manhattan, Sour, Highball or Sidecar."
            ),
        },
        "glass_type": {
            "type": "string",
            "enum": ["rocks", "coupe", "highball", "martini", "flute", "nick_and_nora"],
        },
        "ice": {
            "type": "string",
            "description": (
                "The ice in the glass as served, as a short phrase: Large cube, "
                "Cubed, Crushed, or None for a drink served up."
            ),
        },
        "technique": {
            "type": "string",
            "enum": ["Stirred", "Shaken", "Built", "Blended", "Muddled"],
            "description": (
                "Shaken for drinks containing citrus, egg white or dairy. Stirred for "
                "all-spirit drinks. Built for highballs assembled in the serving glass."
            ),
        },
        "ingredients": {
            "type": "array",
            "minItems": 1,
            "description": "Listed in the order they are added to the drink.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "display"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Ingredient name only, with no quantity in it.",
                    },
                    "amount": {
                        "type": ["number", "null"],
                        "description": "Numeric quantity, or null when the ingredient tops the drink.",
                    },
                    "unit": {
                        "type": "string",
                        "enum": [
                            "ml", "cl", "g", "dashes", "drops",
                            "barspoons", "leaves", "cube", "top-up", "",
                        ],
                        "description": "Metric only. Never oz, cups, tablespoons or teaspoons.",
                    },
                    "display": {
                        "type": "string",
                        "description": (
                            "The amount exactly as it should read on the card, "
                            "e.g. 60 ml, 2 dashes, Top up."
                        ),
                    },
                },
            },
        },
        "garnish": {
            "type": "string",
            "description": "The garnish as served, e.g. Orange twist. Omit the field entirely if there is none.",
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
            "description": "The complete method, one short imperative sentence per step.",
        },
    },
}


def build(handlers: Any):
    async def show_recipe(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.show_recipe")
        handlers.on_recipe(args)
        return {"content": [{"type": "text", "text": RESULT}]}

    return tool(NAME, DESCRIPTION, SCHEMA)(show_recipe)
