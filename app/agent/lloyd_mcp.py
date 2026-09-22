import sys
import os
import json
import base64
import mimetypes
import subprocess
import textwrap
from pathlib import Path

from app.config import MCP_HOST, MCP_PORT, MCP_SERVER_NAME, MCP_TRANSPORT
from app.helpers import perf

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"


def _load_prompt(filename: str) -> str:
    with open(_PROMPTS_DIR / filename, encoding="utf-8") as f:
        return textwrap.dedent(f.read()).strip()


SCAN_PROMPT = _load_prompt("SCAN_PROMPT.md")
RECIPE_PROMPT = _load_prompt("RECIPE_PROMPT.md")
STEP_BY_STEP_PROMPT = _load_prompt("STEP_BY_STEP_PROMPT.md")
SUGGESTIONS_PROMPT = _load_prompt("SUGGESTIONS_PROMPT.md")
BASIC_QUESTION_PROMPT = _load_prompt("BASIC_QUESTION_PROMPT.md")
STORY_PROMPT = _load_prompt("STORY_PROMPT.md")


def _parse_beverage_list(raw: str) -> list:
    raw = (raw or "").strip()
    for fence in ("```json", "```"):
        if raw.startswith(fence):
            raw = raw[len(fence):]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except json.JSONDecodeError:
        pass
    return []


def _extract_result_from_stream_json(stdout: str) -> str:
    """--output-format stream-json emits one JSON object per line (NDJSON) --
    system/assistant/etc. events, then a final line with "type": "result"
    holding the actual text."""
    result_text = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "result":
            result_text = obj.get("result")
    return result_text


def analyze_image_base64(image_path: str) -> list:
    """Spawns a separate, one-off `claude -p` process and sends the photo as
    inline base64 via --input-format stream-json.

    Note: --input-format stream-json requires --output-format stream-json
    (the CLI enforces this pairing), so output here is NDJSON parsed
    line-by-line via _extract_result_from_stream_json, not a single JSON
    object. If this ever errors, analyze_image_file_ref() below is a
    simpler fallback.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"No such file: {image_path}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    b64_data = base64.b64encode(image_bytes).decode("ascii")
    media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    turn = {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64_data},
                },
                {"type": "text", "text": SCAN_PROMPT},
            ],
        },
    }
    stdin_payload = json.dumps(turn) + "\n"

    cmd = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--input-format", "stream-json",
        "--verbose",
    ]
    proc = subprocess.run(
        cmd, input=stdin_payload, capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI (image analysis, base64) failed:\n{proc.stderr}")

    result_text = _extract_result_from_stream_json(proc.stdout)
    if result_text is None:
        raise RuntimeError("No 'result' line found in stream-json output.")

    return _parse_beverage_list(result_text)


def run_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:
            from fastmcp import FastMCP
        except ImportError as e:
            print(f"FATAL: could not import FastMCP from either 'mcp' or 'fastmcp': {e}",
                  file=sys.stderr)
            print("Fix: pip install \"mcp<2\"   (or: pip install fastmcp)", file=sys.stderr)
            sys.exit(1)

    mcp = FastMCP(MCP_SERVER_NAME, host=MCP_HOST, port=MCP_PORT)

    def web_search(query: str, max_results: int = 5):
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def scan(image_path: str) -> dict:
        """Identify which beverages are visible in a photo of the bar shelf.
        Only use this when the user EXPLICITLY asks to scan, look at, or
        check the bar shelf/counter (e.g. 'scan the bar', 'what's on the
        counter?'). Do not use it for general or ambiguous questions --
        those go to basic_question instead. Requires image_path: the
        absolute path to the photo -- this will already be present in the
        user's own message when scan is the right tool to call (e.g. 'scan
        the shelf, photo's at /home/me/bar.jpg'). Never invent or guess a
        path; if the message doesn't contain one, don't call this tool --
        explain in your reply that you need an image path instead."""
        perf.start("mcp.scan")
        try:
            beverages = analyze_image_base64(image_path)
        except Exception as e:
            return {"beverages": [], "error": f"{type(e).__name__}: {e}"}
        finally:
            perf.mark("mcp.tool_done")
        return {"beverages": beverages}

    @mcp.tool(description=RECIPE_PROMPT)
    def recipe(drink_name: str) -> dict:
        perf.start("mcp.recipe")
        results = web_search(f"{drink_name} cocktail recipe")
        perf.mark("mcp.tool_done")
        return {"drink": drink_name, "results": results}

    @mcp.tool(description=STEP_BY_STEP_PROMPT)
    def step_by_step(drink_name: str) -> dict:
        perf.start("mcp.step_by_step")
        results = web_search(f"{drink_name} cocktail exact measurements method steps")
        perf.mark("mcp.tool_done")
        return {"drink": drink_name, "results": results}

    @mcp.tool(description=SUGGESTIONS_PROMPT)
    def suggestions(available_drinks: list) -> dict:
        perf.start("mcp.suggestions")
        q = " ".join(available_drinks)
        results = web_search(f"cocktails to make with {q}")
        perf.mark("mcp.tool_done")
        return {"available": available_drinks, "results": results}

    @mcp.tool(description=BASIC_QUESTION_PROMPT)
    def basic_question(question: str) -> dict:
        perf.start("mcp.basic_question")
        results = web_search(question)
        perf.mark("mcp.tool_done")
        return {"question": question, "results": results}

    @mcp.tool(description=STORY_PROMPT)
    def story(drink_name: str) -> dict:
        perf.start("mcp.story")
        results = web_search(f"{drink_name} cocktail history origin story")
        perf.mark("mcp.tool_done")
        return {"drink": drink_name, "results": results}

    mcp.run(transport=MCP_TRANSPORT)


if __name__ == "__main__":
    run_mcp_server()