MCP_SERVER_NAME: str = "bartender"
AGENT_MCP_SERVER_VERSION: str = "1.0.0"
AGENT_MODEL: str = "claude-opus-5"
AGENT_PERMISSION_MODE: str = "bypassPermissions"
AGENT_SYSTEM_PROMPT_PATH: str = "prompts/SYSTEM_PROMPT.md"
AGENT_SCAN_PROMPT_PATH: str = "prompts/SCAN_PROMPT.md"
AGENT_SCAN_DEFAULT_MEDIA_TYPE: str = "image/jpeg"
AGENT_ENV: dict[str, str] = {"ENABLE_TOOL_SEARCH": "false"}

AGENT_TOOL_RENDER_ANIMATION: str = "render_animation"
AGENT_TOOL_SHOW_RECIPE: str = "show_recipe"
AGENT_TOOL_SCAN_SHELF: str = "scan_shelf"
AGENT_TOOL_WEB_SEARCH: str = "web_search"
AGENT_TOOL_NAMES: tuple[str, ...] = (
    AGENT_TOOL_RENDER_ANIMATION, AGENT_TOOL_SHOW_RECIPE, AGENT_TOOL_SCAN_SHELF,
    AGENT_TOOL_WEB_SEARCH,
)
AGENT_ALLOWED_TOOLS: tuple[str, ...] = tuple(
    f"mcp__{MCP_SERVER_NAME}__{name}" for name in AGENT_TOOL_NAMES
)

AGENT_DESC_RENDER_ANIMATION: str = (
    "Play the step-by-step build animation for one cocktail on the user's screen. "
    "Call this AFTER you have already written your spoken reply as plain text, and "
    "only once per named cocktail. The spec is the COMPLETE build for the whole "
    "drink, not just the step you are currently narrating. The first step must "
    "always be a chill action with target serving_glass and a glass matching "
    "glass_type."
)
AGENT_DESC_SHOW_RECIPE: str = (
    "Display the recipe card for one named cocktail. Call this AFTER you have "
    "already written your spoken reply as plain text. Use it when the user asks "
    "what is in a drink or asks for its recipe, rather than asking to be walked "
    "through building it."
)
AGENT_DESC_SCAN_SHELF: str = (
    "Open the phone camera popup, wait for the user to photograph their bar shelf, "
    "and return the list of bottles identified in the photo. Call this ONLY when "
    "the user explicitly asks you to scan, look at, or check the shelf or the "
    "counter. Never call it for a vague or general question -- it costs the user "
    "several seconds and a photo."
)
AGENT_DESC_WEB_SEARCH: str = (
    "Search the web and return raw results. Use this ONLY for genuinely current or "
    "obscure information you do not already know, such as a bar that opened this "
    "year or a product that may have been discontinued. Do NOT use it for classic "
    "cocktails, standard technique, bar terminology, cocktail history, or "
    "suggesting drinks from a list of bottles -- answer those directly."
)

AGENT_TOOL_RESULT_ANIMATION: str = "Animation started."
AGENT_TOOL_RESULT_RECIPE: str = "Recipe card shown."
AGENT_TOOL_ERROR_ANIMATION_SCHEMA: str = "The animation spec was rejected by the schema:"
AGENT_TOOL_ERROR_SCAN: str = "The shelf scan failed:"
AGENT_TOOL_ERROR_SCAN_EMPTY: str = "The photo arrived but no bottles could be identified in it."
AGENT_TOOL_ERROR_WEB_SEARCH: str = "The web search failed:"
AGENT_SCAN_NO_RESULT: str = "No photo was received."

AGENT_ERROR_SPEECH: str = "Something went wrong on my end -- would you like to try that again?"
AGENT_NOT_READY_SPEECH: str = "Give me a second -- I'm still waking up."
AGENT_RENDER_STATUS_TEXT: str = "Render completed"
AGENT_RENDER_STARTED_TEXT: str = "Creating your cocktail video..."
AGENT_RENDER_FAILED_PREFIX: str = "Rendering failed:"

STEP_BY_STEP_DEBUG_DIR: str = "runtime/step_by_step_debug"
STEP_BY_STEP_RERENDER_KEYWORDS: tuple[str, ...] = (
    "rerender", "re-render", "renew", "regenerate", "redo", "recreate",
)

WEB_SEARCH_MAX_RESULTS: int = 5
WEB_SEARCH_CACHE_SIZE: int = 32
