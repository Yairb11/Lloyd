"""Strict JSON Schema (draft-07) for the step_by_step tool's animation recipe data.

This mirrors test/cocktails/format.json exactly. It is embedded here (rather than
read from the test/ folder) so the shipped app has no runtime dependency on test/.
"""

STEP_BY_STEP_SCHEMA: dict = {
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
        "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
        "name": {"type": "string"},
        "build_in_serving_glass": {"type": "boolean"},
        "glass_type": {
            "type": "string",
            "enum": ["coupe", "rocks", "highball", "martini", "nick_and_nora"],
        },
        "has_foam": {"type": "boolean"},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "name", "type", "amount", "color_hex"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["liquid", "solid", "bitters"]},
                    "amount": {
                        "oneOf": [
                            {"type": "number", "minimum": 0},
                            {"type": "string", "enum": ["top the cocktail"]},
                        ]
                    },
                    "unit": {"type": "string", "enum": ["ml", "count", "dash"]},
                    "color_hex": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                },
            },
        },
        "steps": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "instruction", "action"],
                "properties": {
                    "title": {"type": "string"},
                    "instruction": {"type": "string"},
                    "action": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "enum": [
                                    "chill", "measure", "ice", "muddle",
                                    "stir", "shake", "strain", "garnish",
                                ],
                            },
                            "target": {"type": "string", "enum": ["shaker", "mixing_glass", "serving_glass"]},
                            "glass": {"type": "string", "enum": ["coupe", "rocks", "highball", "martini", "nick_and_nora"]},
                            "what": {"type": "string"},
                            "unit": {"type": "string", "enum": ["ml", "count", "dash"]},
                            "amount": {
                                "oneOf": [
                                    {"type": "number"},
                                    {"type": "string", "enum": ["top the cocktail"]},
                                ]
                            },
                            "ice_type": {"type": "string", "enum": ["cubed", "crushed", "large_rock", "sphere"]},
                            "duration_sec": {"type": "integer"},
                            "style": {"type": "string", "enum": ["wet", "dry"]},
                            "technique": {"type": "string", "enum": ["single", "double"]},
                            "into": {"type": "string", "enum": ["serving_glass"]},
                            "item": {"type": "string"},
                            "placement": {"type": "string", "enum": ["rim", "float", "side_of_ice"]},
                            "color_hex": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                            "shape": {"type": "string", "enum": ["half circle", "leaf", "square", "traingle", "foam", "dashes"]},
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