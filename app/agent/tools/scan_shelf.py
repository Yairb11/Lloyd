import json
from typing import Any
from claude_agent_sdk import tool

from app.core import perf

NAME: str = "scan_shelf"

ROUTING: str = (
    "the user explicitly asks you to scan, look at, or check the bar shelf or the "
    "counter -> scan_shelf"
)

DESCRIPTION: str = (
    "Open the phone camera popup, wait for the user to photograph their bar shelf, "
    "and return the list of bottles identified in the photo. Call this ONLY when the "
    "user explicitly asks you to scan, look at or check the shelf or the counter. "
    "Never call it for a vague or general question -- it costs the user several "
    "seconds and a photo. Once the list comes back, suggest drinks from it directly; "
    "do not call another tool to do that."
)

VISION_PROMPT: str = (
    "Look at this photo of a bar shelf and identify every distinct alcoholic "
    "beverage bottle you can see (spirits, wine, liqueurs -- not mixers, glassware, "
    "or garnishes). Respond with ONLY a JSON array of lowercase beverage names, "
    "nothing else, no markdown fences.\n"
    'Example: ["bourbon", "gin", "sweet vermouth"]\n'
    "If you can't identify any bottles, respond with []."
)

SCHEMA: dict = {"type": "object", "properties": {}, "required": []}

ERROR_FAILED: str = "The shelf scan failed:"
ERROR_EMPTY: str = "The photo arrived but no bottles could be identified in it."


def build(handlers: Any):
    async def scan_shelf(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.scan_shelf")
        try:
            beverages = await handlers.on_scan()
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"{ERROR_FAILED} {exc}"}],
                "is_error": True,
            }
        if not beverages:
            return {
                "content": [{"type": "text", "text": ERROR_EMPTY}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": json.dumps(beverages)}]}

    return tool(NAME, DESCRIPTION, SCHEMA)(scan_shelf)
