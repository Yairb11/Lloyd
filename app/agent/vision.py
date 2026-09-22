import base64
import json
import mimetypes
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient,
    ResultMessage, TextBlock,
)

from app.config import (
    AGENT_ENV, AGENT_MODEL, AGENT_PERMISSION_MODE,
    AGENT_SCAN_DEFAULT_MEDIA_TYPE, AGENT_SCAN_PROMPT_PATH,
)
from app.core.paths import PROJECT_ROOT

SCAN_PROMPT: str = (
    (PROJECT_ROOT / AGENT_SCAN_PROMPT_PATH).read_text(encoding="utf-8").strip()
)


def parse_beverage_list(raw: str) -> list:
    raw = (raw or "").strip()
    for fence in ("```json", "```"):
        if raw.startswith(fence):
            raw = raw[len(fence):]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def _vision_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SCAN_PROMPT,
        model=AGENT_MODEL,
        tools=[],
        setting_sources=[],
        permission_mode=AGENT_PERMISSION_MODE,
        env=dict(AGENT_ENV),
        cwd=str(PROJECT_ROOT),
    )


async def analyze_bottle_photo(image_path: str) -> list:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {image_path}")

    media_type = mimetypes.guess_type(str(path))[0] or AGENT_SCAN_DEFAULT_MEDIA_TYPE
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")

    async def photo_turn():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded,
                        },
                    },
                    {"type": "text", "text": SCAN_PROMPT},
                ],
            },
        }

    collected = ""
    final = ""
    async with ClaudeSDKClient(options=_vision_options()) as client:
        await client.query(photo_turn())
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        collected += block.text
            elif isinstance(message, ResultMessage):
                if isinstance(message.result, str):
                    final = message.result

    return parse_beverage_list(final or collected)
