import json
import subprocess
from pathlib import Path

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


def ask_bartender(message: str, session_id: str | None = None) -> dict:
    cmd = [
        AGENT_CLI_COMMAND, "-p", message,
        "--append-system-prompt", _SYSTEM_PROMPT,
        "--output-format", AGENT_OUTPUT_FORMAT,
        "--mcp-config", str(_PROJECT_ROOT / MCP_CONFIG_PATH),
        "--allowedTools", _ALLOWED_TOOLS,
    ]
    if session_id:
        cmd += ["--resume", session_id]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=AGENT_CLI_TIMEOUT_S)
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed:\n{proc.stderr}")

    try:
        outer = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"claude CLI returned invalid JSON: {exc}\n{proc.stdout}") from exc

    raw = _strip_json_fences(outer.get("result", ""))
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        envelope = {"operation": "basic_question", "speech": raw, "data": None}

    envelope["session_id"] = outer.get("session_id")
    return envelope
