import asyncio
import json
from collections import OrderedDict
from typing import Any

from claude_agent_sdk import ToolAnnotations, tool

from app.core import perf

NAME: str = "web_search"

ROUTING: str = (
    "you genuinely need current or obscure information you do not already know -> "
    "web_search, then keep speaking with what it returns"
)

DESCRIPTION: str = (
    "Search the web and return raw results. Use this ONLY for genuinely current or "
    "obscure information you do not already know, such as a bar that opened this "
    "year or a product that may have been discontinued. Do NOT use it for classic "
    "cocktails, standard technique, bar terminology, cocktail history, or suggesting "
    "drinks from a list of bottles -- answer those directly from what you know."
)

SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["query"],
    "properties": {
        "query": {
            "type": "string",
            "description": "A short search query, not a sentence addressed to the user.",
        }
    },
}

ERROR_FAILED: str = "The web search failed:"

MAX_RESULTS: int = 5
CACHE_SIZE: int = 32

_cache: "OrderedDict[str, list]" = OrderedDict()


def _search(query: str) -> list:
    cached = _cache.get(query)
    if cached is not None:
        _cache.move_to_end(query)
        return cached

    from ddgs import DDGS

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=MAX_RESULTS))

    _cache[query] = results
    while len(_cache) > CACHE_SIZE:
        _cache.popitem(last=False)
    return results


def build(handlers: Any):
    async def web_search(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.web_search")
        try:
            results = await asyncio.to_thread(_search, args["query"])
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"{ERROR_FAILED} {exc}"}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": json.dumps(results)}]}

    return tool(
        NAME, DESCRIPTION, SCHEMA,
        annotations=ToolAnnotations(readOnlyHint=True),
    )(web_search)
