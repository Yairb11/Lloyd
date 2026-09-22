import asyncio
import copy
import json
from collections import OrderedDict
from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions, ToolAnnotations, create_sdk_mcp_server,
    tool,
)
from jsonschema import ValidationError, validate

from app.agent.schemas.recipe_card import RECIPE_CARD_SCHEMA
from app.agent.schemas.step_by_step import STEP_BY_STEP_SCHEMA
from app.config import (
    AGENT_ALLOWED_TOOLS, AGENT_DESC_RENDER_ANIMATION, AGENT_DESC_SCAN_SHELF,
    AGENT_DESC_SHOW_RECIPE, AGENT_DESC_WEB_SEARCH, AGENT_ENV,
    AGENT_MCP_SERVER_VERSION, AGENT_MODEL, AGENT_PERMISSION_MODE,
    AGENT_SYSTEM_PROMPT_PATH, AGENT_TOOL_ERROR_ANIMATION_SCHEMA, AGENT_TOOL_ERROR_SCAN,
    AGENT_TOOL_ERROR_SCAN_EMPTY, AGENT_TOOL_ERROR_WEB_SEARCH, AGENT_TOOL_RENDER_ANIMATION,
    AGENT_TOOL_RESULT_ANIMATION, AGENT_TOOL_RESULT_RECIPE, AGENT_TOOL_SCAN_SHELF,
    AGENT_TOOL_SHOW_RECIPE, AGENT_TOOL_WEB_SEARCH, MCP_SERVER_NAME,
    WEB_SEARCH_CACHE_SIZE, WEB_SEARCH_MAX_RESULTS,
)
from app.core import perf
from app.core.paths import PROJECT_ROOT

_EMPTY_SCHEMA: dict = {"type": "object", "properties": {}, "required": []}
_QUERY_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["query"],
    "properties": {"query": {"type": "string"}},
}

_search_cache: "OrderedDict[str, list]" = OrderedDict()


def animation_input_schema() -> dict:
    schema = copy.deepcopy(STEP_BY_STEP_SCHEMA)
    schema.pop("$schema", None)
    schema.pop("title", None)
    steps = schema.get("properties", {}).get("steps")
    if isinstance(steps, dict):
        steps.pop("allOf", None)
    return schema


def _text_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _error_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


def _web_search(query: str) -> list:
    cached = _search_cache.get(query)
    if cached is not None:
        _search_cache.move_to_end(query)
        return cached

    from ddgs import DDGS

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=WEB_SEARCH_MAX_RESULTS))

    _search_cache[query] = results
    while len(_search_cache) > WEB_SEARCH_CACHE_SIZE:
        _search_cache.popitem(last=False)
    return results


def build_server(handlers: Any):
    async def render_animation(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.render_animation")
        try:
            validate(instance=args, schema=STEP_BY_STEP_SCHEMA)
        except ValidationError as exc:
            return _error_result(f"{AGENT_TOOL_ERROR_ANIMATION_SCHEMA} {exc.message}")
        handlers.on_animation(args)
        return _text_result(AGENT_TOOL_RESULT_ANIMATION)

    async def show_recipe(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.show_recipe")
        handlers.on_recipe(args)
        return _text_result(AGENT_TOOL_RESULT_RECIPE)

    async def scan_shelf(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.scan_shelf")
        try:
            beverages = await handlers.on_scan()
        except Exception as exc:
            return _error_result(f"{AGENT_TOOL_ERROR_SCAN} {exc}")
        if not beverages:
            return _error_result(AGENT_TOOL_ERROR_SCAN_EMPTY)
        return _text_result(json.dumps(beverages))

    async def web_search(args: dict[str, Any]) -> dict[str, Any]:
        perf.mark("agent.tool.web_search")
        try:
            results = await asyncio.to_thread(_web_search, args["query"])
        except Exception as exc:
            return _error_result(f"{AGENT_TOOL_ERROR_WEB_SEARCH} {exc}")
        return _text_result(json.dumps(results))

    tools = [
        tool(
            AGENT_TOOL_RENDER_ANIMATION,
            AGENT_DESC_RENDER_ANIMATION,
            animation_input_schema(),
        )(render_animation),
        tool(
            AGENT_TOOL_SHOW_RECIPE,
            AGENT_DESC_SHOW_RECIPE,
            RECIPE_CARD_SCHEMA,
        )(show_recipe),
        tool(
            AGENT_TOOL_SCAN_SHELF,
            AGENT_DESC_SCAN_SHELF,
            _EMPTY_SCHEMA,
        )(scan_shelf),
        tool(
            AGENT_TOOL_WEB_SEARCH,
            AGENT_DESC_WEB_SEARCH,
            _QUERY_SCHEMA,
            annotations=ToolAnnotations(readOnlyHint=True),
        )(web_search),
    ]

    return create_sdk_mcp_server(
        name=MCP_SERVER_NAME,
        version=AGENT_MCP_SERVER_VERSION,
        tools=tools,
    )


def build_options(handlers: Any) -> ClaudeAgentOptions:
    system_prompt = (
        (PROJECT_ROOT / AGENT_SYSTEM_PROMPT_PATH).read_text(encoding="utf-8").strip()
    )
    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=AGENT_MODEL,
        mcp_servers={MCP_SERVER_NAME: build_server(handlers)},
        allowed_tools=list(AGENT_ALLOWED_TOOLS),
        tools=[],
        setting_sources=[],
        permission_mode=AGENT_PERMISSION_MODE,
        include_partial_messages=True,
        env=dict(AGENT_ENV),
        cwd=str(PROJECT_ROOT),
    )
