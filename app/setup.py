import itertools
import json
import socket
import subprocess
import sys
import threading
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
    STARTUP_LOADING_INTERVAL_S,
    STARTUP_LOADING_TEXT,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_mcp_process: subprocess.Popen | None = None


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
    global _mcp_process
    _mcp_process = subprocess.Popen(
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


def shutdown_mcp_server() -> None:
    """Terminate the MCP server subprocess if this process launched it."""
    global _mcp_process
    if _mcp_process is not None and _mcp_process.poll() is None:
        _mcp_process.terminate()
        try:
            _mcp_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _mcp_process.kill()
    _mcp_process = None


class _LoadingIndicator:
    def __init__(self, text: str = STARTUP_LOADING_TEXT, interval_s: float = STARTUP_LOADING_INTERVAL_S) -> None:
        self._text = text
        self._interval_s = interval_s
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join()
        sys.stdout.write("\r" + " " * (len(self._text) + 4) + "\r")
        sys.stdout.flush()

    def _run(self) -> None:
        for dots in itertools.cycle(["", ".", "..", "..."]):
            if self._stop_event.is_set():
                return
            sys.stdout.write(f"\r{self._text}{dots}   ")
            sys.stdout.flush()
            self._stop_event.wait(self._interval_s)


def setup() -> None:
    indicator = _LoadingIndicator()
    indicator.start()
    try:
        _write_mcp_config()

        if not _is_mcp_server_reachable():
            _launch_mcp_server()

        server_ready = _wait_for_mcp_server()
    finally:
        indicator.stop()

    if not server_ready:
        print(f"{LOG_PREFIX_ERROR} MCP server did not come up within {MCP_HEALTHCHECK_TIMEOUT_S}s on {MCP_HOST}:{MCP_PORT}")
        raise RuntimeError(f"MCP server did not start on {MCP_HOST}:{MCP_PORT}")

    print(f"{LOG_PREFIX_MCP} server is up on {MCP_HOST}:{MCP_PORT}")