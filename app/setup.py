import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from app.config import (
    LOG_PREFIX_ERROR,
    LOG_PREFIX_MCP,
    MCP_CONFIG_PATH,
    MCP_HEALTHCHECK_CONNECT_TIMEOUT_S,
    MCP_HEALTHCHECK_POLL_INTERVAL_S,
    MCP_HEALTHCHECK_TIMEOUT_S,
    MCP_HOST,
    MCP_PORT,
    MCP_SERVER_MODULE,
    MCP_SERVER_NAME,
    MCP_SSE_PATH,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _is_mcp_server_reachable() -> bool:
    try:
        with socket.create_connection((MCP_HOST, MCP_PORT), timeout=MCP_HEALTHCHECK_CONNECT_TIMEOUT_S):
            return True
    except OSError:
        return False


def _write_mcp_config() -> None:
    config_path = _PROJECT_ROOT / MCP_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"http://{MCP_HOST}:{MCP_PORT}{MCP_SSE_PATH}"
    config_path.write_text(
        json.dumps({"mcpServers": {MCP_SERVER_NAME: {"type": "sse", "url": url}}}),
        encoding="utf-8",
    )


def _launch_mcp_server() -> None:
    subprocess.Popen(
        [sys.executable, "-m", MCP_SERVER_MODULE],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=str(_PROJECT_ROOT),
    )


def _wait_for_mcp_server() -> bool:
    deadline = time.monotonic() + MCP_HEALTHCHECK_TIMEOUT_S
    while time.monotonic() < deadline:
        if _is_mcp_server_reachable():
            return True
        time.sleep(MCP_HEALTHCHECK_POLL_INTERVAL_S)
    return False


def setup() -> None:
    _write_mcp_config()

    if not _is_mcp_server_reachable():
        _launch_mcp_server()

    if not _wait_for_mcp_server():
        print(f"{LOG_PREFIX_ERROR} MCP server did not come up within {MCP_HEALTHCHECK_TIMEOUT_S}s on {MCP_HOST}:{MCP_PORT}")
        raise RuntimeError(f"MCP server did not start on {MCP_HOST}:{MCP_PORT}")

    print(f"{LOG_PREFIX_MCP} server is up on {MCP_HOST}:{MCP_PORT}")