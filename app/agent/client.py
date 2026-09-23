from typing import Any
from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server

from app.agent.prompt import build_system_prompt
from app.agent.tools import ALLOWED_TOOLS, build_all
from app.config import (
    AGENT_ENV, AGENT_MCP_SERVER_VERSION, AGENT_MODEL,
    AGENT_PERMISSION_MODE, MCP_SERVER_NAME,
)
from app.core.paths import PROJECT_ROOT


def build_server(handlers: Any):
    return create_sdk_mcp_server(
        name=MCP_SERVER_NAME,
        version=AGENT_MCP_SERVER_VERSION,
        tools=build_all(handlers),
    )


def build_options(handlers: Any) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=build_system_prompt(),
        model=AGENT_MODEL,
        mcp_servers={MCP_SERVER_NAME: build_server(handlers)},
        allowed_tools=list(ALLOWED_TOOLS),
        tools=[],
        setting_sources=[],
        permission_mode=AGENT_PERMISSION_MODE,
        include_partial_messages=True,
        env=dict(AGENT_ENV),
        cwd=str(PROJECT_ROOT),
    )
