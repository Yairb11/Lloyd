import json
from typing import Any
from claude_agent_sdk import tool

from app.core import perf

NAME: str = "scan_shelf"

ROUTING: str = (
    "the user explicitly asks you to scan, look at, or check the bar shelf or the "
    "counter -> scan_shelf"
)

REPORT_FORMAT: str = (
    "The result is JSON with three sections, \"spirits\", \"modifiers\" and "
    "\"other\". Each item has a name (null when unreadable), category, details, "
    "presentation, position, and a confident flag.\n"
    "\n"
    "When it comes back, keep speaking. Report the shelf as an observant bartender "
    "who reads a back bar at a glance -- interpret and group it, never rattle it off "
    "like a grocery list. This is a long-form format: it replaces the usual sentence "
    "limit and the one-detail rule. It must sound entirely spoken, with no lists, "
    "no markdown, and no colons inside sentences.\n"
    "\n"
    "Write four paragraphs separated by one blank line, and never number or label "
    "them:\n"
    "\n"
    "- The welcome assessment. One sentence judging the collection's overall "
    "character, such as a versatile cocktail station, a serious whiskey enthusiast "
    "corner, or a relaxed aperitif spread.\n"
    "- The primary spirits. Walk through every spirit, grouping like with like, such "
    "as the whiskies and dark spirits, then the clear spirits, or shelf by shelf. Name "
    "each bottle and its expression in full, with its region, age, cask or proof "
    "where the details give them, and weave in its presentation and position "
    "naturally, such as \"in its presentation box\", \"with its signature red wax "
    "seal\", or \"resting just behind the Absolut\".\n"
    "- The modifiers and secondary bottles. Cover the vermouths, aperitifs, "
    "liqueurs, bitters, wines, and mixers, and say what each one is useful for "
    "behind the bar. When the modifiers section and the other section are both "
    "empty, use this paragraph for the no-modifiers adaptation below instead.\n"
    "- The potential. Name the kinds of drinks or tasting flights this exact setup "
    "enables, and fold a warm invitation for the guest's next move into the closing "
    "sentence.\n"
    "\n"
    "When one section is much larger than another, the order of the middle two "
    "paragraphs may follow the shelf, as long as each stays grouped. Mention every "
    "item exactly once. Spell label abbreviations out as spoken, such as Very Special "
    "for VS and Very Superior Old Pale for VSOP, and never write dotted "
    "abbreviations, because every period ends a spoken sentence.\n"
    "\n"
    "Adapt to what the scan shows:\n"
    "\n"
    "- Mostly whiskey or neat spirits: focus on the tasting contrasts between "
    "regions, mash bills, and cask finishes, and suggest a side-by-side dram flight.\n"
    "- Base spirits but no modifiers such as vermouth or liqueurs: say what can be "
    "made right now with pantry staples, citrus, or highball mixers, then suggest "
    "one or two versatile modifier bottles to pick up next.\n"
    "- Any item with confident false: never assert a brand for it. Describe it by "
    "its color, shape, and position, such as \"a white bottle resting behind the "
    "vodka\", and in the closing sentence gently ask the guest to confirm what is in "
    "that spot if they want cocktails that use it."
)

DESCRIPTION: str = (
    "Open the phone camera popup, wait for the user to photograph their bar shelf or "
    "counter, and return an inventory of every bottle in the photo. Call this ONLY "
    "when the user explicitly asks you to scan, look at or check the shelf or the "
    "counter. Never call it for a vague or general question -- it costs the user "
    "several seconds and a photo.\n"
    "\n"
    f"{REPORT_FORMAT}"
)

VISION_PROMPT: str = (
    "You are auditing a photo of a bar shelf or counter for a bartender. Work "
    "through it in three passes.\n"
    "\n"
    "First, recognition. Read every label, crest, wax dip, bottle silhouette, and "
    "presentation box or gift tube. Make one entry per physical item -- a boxed or "
    "tubed bottle is one entry, and two identical bottles are two entries. Include "
    "spirits, wines, fortified wines, liqueurs, bitters, and non-alcoholic mixers or "
    "cans. Ignore glassware, barware, and garnishes.\n"
    "\n"
    "Second, grouping. Put each item in exactly one group. \"spirit\" is a base "
    "spirit such as whiskey, gin, vodka, rum, tequila, mezcal, brandy, or cognac. "
    "\"modifier\" is a fortified wine, aperitif, vermouth, liqueur, triple sec, amaro, "
    "or bitters. \"other\" is a wine, beer, or non-alcoholic mixer.\n"
    "\n"
    "Third, confidence. For a bottle that is partly hidden, blurry, or turned away, "
    "never guess a specific brand. Set confident to false and describe it only "
    "through its presentation and position.\n"
    "\n"
    "Respond with ONLY a JSON array, no markdown fences and no commentary. Order the "
    "items left to right, top shelf first. Each item is an object with these keys:\n"
    '- "name": the brand and expression as the label reads, with abbreviations '
    'written without periods, such as "Hennessy VS" or "Maker\'s Mark 101". null '
    "when you cannot read it.\n"
    '- "category": the specific style in lowercase, such as "blended malt scotch '
    'whisky", "kentucky straight bourbon", "london dry gin", "extra dry vermouth", '
    'or "white wine".\n'
    '- "group": "spirit", "modifier", or "other".\n'
    '- "details": region, age statement, cask, proof or ABV, and batch -- only what '
    'is printed or unmistakable, such as "Speyside, 12 year old, double cask '
    'matured". null when there is nothing to add.\n'
    '- "presentation": how it is presented, such as "open bottle", "sealed bottle", '
    '"wax-sealed bottle", "in its presentation box", or "in a presentation tube".\n'
    '- "position": where it sits relative to the shelf and its neighbors, such as '
    '"upper shelf, far left" or "behind the Absolut vodka".\n'
    '- "confident": true only when the label is legible enough to be certain of the '
    "name.\n"
    "\n"
    'Example: [{"name": "Monkey Shoulder The Original", "category": "blended malt '
    'scotch whisky", "group": "spirit", "details": "Speyside malts, batch 27", '
    '"presentation": "open bottle", "position": "front row, center", "confident": '
    'true}, {"name": null, "category": "vodka", "group": "spirit", "details": null, '
    '"presentation": "sealed white bottle", "position": "behind the Absolut vodka", '
    '"confident": false}]\n'
    "If you can't identify any bottles, respond with []."
)

SCHEMA: dict = {"type": "object", "properties": {}, "required": []}

FIELD_NAME: str = "name"
FIELD_CATEGORY: str = "category"
FIELD_GROUP: str = "group"
FIELD_DETAILS: str = "details"
FIELD_PRESENTATION: str = "presentation"
FIELD_POSITION: str = "position"
FIELD_CONFIDENT: str = "confident"

TEXT_FIELDS: tuple[str, ...] = (
    FIELD_NAME, FIELD_CATEGORY, FIELD_DETAILS, FIELD_PRESENTATION, FIELD_POSITION,
)

GROUP_SPIRIT: str = "spirit"
GROUP_MODIFIER: str = "modifier"
GROUP_OTHER: str = "other"

INVENTORY_SECTIONS: dict[str, str] = {
    GROUP_SPIRIT: "spirits",
    GROUP_MODIFIER: "modifiers",
    GROUP_OTHER: "other",
}

ERROR_FAILED: str = "The shelf scan failed:"
ERROR_EMPTY: str = "The photo arrived but no bottles could be identified in it."


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_item(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    item: dict[str, Any] = {field: _text(raw.get(field)) for field in TEXT_FIELDS}
    if item[FIELD_NAME] is None and item[FIELD_CATEGORY] is None:
        return None
    group = (_text(raw.get(FIELD_GROUP)) or "").lower()
    item[FIELD_GROUP] = group if group in INVENTORY_SECTIONS else GROUP_OTHER
    item[FIELD_CONFIDENT] = raw.get(FIELD_CONFIDENT) is True and item[FIELD_NAME] is not None
    return item


def _build_inventory(detected: list) -> dict[str, list[dict[str, Any]]]:
    inventory: dict[str, list[dict[str, Any]]] = {
        section: [] for section in INVENTORY_SECTIONS.values()
    }
    for raw in detected:
        item = _normalize_item(raw)
        if item is None:
            continue
        section = INVENTORY_SECTIONS[item.pop(FIELD_GROUP)]
        inventory[section].append(item)
    return inventory


def build(handlers: Any):
    async def scan_shelf(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.scan_shelf")
        try:
            detected = await handlers.on_scan()
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"{ERROR_FAILED} {exc}"}],
                "is_error": True,
            }
        inventory = _build_inventory(detected)
        if not any(inventory.values()):
            return {
                "content": [{"type": "text", "text": ERROR_EMPTY}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": json.dumps(inventory, ensure_ascii=False)}]}

    return tool(NAME, DESCRIPTION, SCHEMA)(scan_shelf)
