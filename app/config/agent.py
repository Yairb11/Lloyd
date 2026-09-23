MCP_SERVER_NAME: str = "bartender"
AGENT_MCP_SERVER_VERSION: str = "1.0.0"
AGENT_MODEL: str = "claude-opus-5"
AGENT_PERMISSION_MODE: str = "bypassPermissions"
AGENT_SCAN_DEFAULT_MEDIA_TYPE: str = "image/jpeg"
AGENT_ENV: dict[str, str] = {"ENABLE_TOOL_SEARCH": "false"}

AGENT_SCAN_NO_RESULT: str = "No photo was received."

AGENT_ERROR_SPEECH: str = "Something broke on my end. Give it another go and I'll pick it back up."
AGENT_NOT_READY_SPEECH: str = "Give me a second, I'm still setting up behind the bar."
AGENT_RENDER_STATUS_TEXT: str = "Render completed"
AGENT_RENDER_STARTED_TEXT: str = "Creating your cocktail video..."
AGENT_RENDER_FAILED_PREFIX: str = "Rendering failed:"



STEP_BY_STEP_DEBUG_DIR: str = "runtime/step_by_step_debug"
STEP_BY_STEP_RERENDER_KEYWORDS: tuple[str, ...] = (
    "rerender", "re-render", "renew", "regenerate", "redo", "recreate",
)
