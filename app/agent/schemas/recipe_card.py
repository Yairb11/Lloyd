RECIPE_CARD_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "glass_type", "ice", "technique", "ingredients", "steps"],
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"},
        "glass_type": {
            "type": "string",
            "enum": ["rocks", "coupe", "highball", "martini", "flute", "nick_and_nora"],
        },
        "ice": {"type": "string"},
        "technique": {
            "type": "string",
            "enum": ["Stirred", "Shaken", "Built", "Blended", "Muddled"],
        },
        "ingredients": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "display"],
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": ["number", "null"]},
                    "unit": {
                        "type": "string",
                        "enum": [
                            "ml", "cl", "g", "dashes", "drops",
                            "barspoons", "leaves", "cube", "top-up", "",
                        ],
                    },
                    "display": {"type": "string"},
                },
            },
        },
        "garnish": {"type": "string"},
        "steps": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    },
}
