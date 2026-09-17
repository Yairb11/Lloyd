import json
import subprocess
from pathlib import Path
from typing import Callable

from app.config import (
    AGENT_CLI_COMMAND,
    AGENT_CLI_TIMEOUT_S,
    AGENT_MCP_TOOL_NAMES,
    AGENT_OUTPUT_FORMAT,
    AGENT_SYSTEM_PROMPT_PATH,
    MCP_CONFIG_PATH,
    MCP_SERVER_NAME,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

with open(_PROJECT_ROOT / AGENT_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
    _SYSTEM_PROMPT = f.read().strip()

_ALLOWED_TOOLS = ",".join(f"mcp__{MCP_SERVER_NAME}__{name}" for name in AGENT_MCP_TOOL_NAMES)


def _strip_json_fences(raw: str) -> str:
    raw = (raw or "").strip()
    for fence in ("```json", "```"):
        if raw.startswith(fence):
            raw = raw[len(fence):]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def ask_bartender(
    message: str,
    session_id: str | None = None,
    on_process_started: Callable[[subprocess.Popen], None] | None = None,
) -> dict:
    cmd = [
        AGENT_CLI_COMMAND, "-p", message,
        "--append-system-prompt", _SYSTEM_PROMPT,
        "--output-format", AGENT_OUTPUT_FORMAT,
        "--mcp-config", str(_PROJECT_ROOT / MCP_CONFIG_PATH),
        "--allowedTools", _ALLOWED_TOOLS,
    ]
    if session_id:
        cmd += ["--resume", session_id]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if on_process_started is not None:
        on_process_started(proc)

    try:
        stdout, stderr = proc.communicate(timeout=AGENT_CLI_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise RuntimeError("claude CLI timed out")

    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed:\n{stderr}")

    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"claude CLI returned invalid JSON: {exc}\n{stdout}") from exc

    raw = _strip_json_fences(outer.get("result", ""))
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        envelope = {"operation": "basic_question", "speech": raw, "data": None}

    envelope["session_id"] = outer.get("session_id")
    return envelope
