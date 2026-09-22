from app.agent.tools import (
    render_animation, scan_shelf, show_recipe,
    web_search,
)
from app.config import MCP_SERVER_NAME

TOOL_MODULES = (render_animation, show_recipe, scan_shelf, web_search)

ALLOWED_TOOLS: tuple[str, ...] = tuple(
    f"mcp__{MCP_SERVER_NAME}__{module.NAME}" for module in TOOL_MODULES
)

ROUTING_LINES: tuple[str, ...] = tuple(module.ROUTING for module in TOOL_MODULES)


def build_all(handlers):
    return [module.build(handlers) for module in TOOL_MODULES]
