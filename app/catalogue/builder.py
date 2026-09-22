import asyncio
import json
import subprocess
import sys
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock

from app.agent import client
from app.config import (
    ANIM_BACKEND_CANVAS, CATALOGUE_DIR, CATALOGUE_SOURCES_FILE,
    MANIM_RENDER_MODULE,
)
from app.core.paths import PROJECT_ROOT

BUILDER_INSTRUCTION = (
    "OVERRIDE for this offline catalogue build only. Ignore the one-tool-per-turn rule. "
    "For the cocktail named below: first write the spoken reply you would give a guest who "
    "just asked you to make it -- 2 to 4 sentences covering only the first checkpoint, "
    "exactly as you normally would. Then call show_recipe with the complete recipe card. "
    "Then call render_animation with the complete build spec for the whole drink. "
    "Call BOTH tools, in that order, every time. Ask no questions."
)


class CaptureHandlers:
    def __init__(self) -> None:
        self.recipe: dict | None = None
        self.animation: dict | None = None

    def on_recipe(self, data: dict) -> None:
        self.recipe = dict(data)

    def on_animation(self, data: dict) -> None:
        self.animation = dict(data)

    async def on_scan(self) -> list:
        return []


def slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


async def generate(name: str) -> tuple[str, dict | None, dict | None]:
    handlers = CaptureHandlers()
    options = client.build_options(handlers)
    options.system_prompt = f"{options.system_prompt}\n\n{BUILDER_INSTRUCTION}"

    speech = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Make me a {name}.")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        speech += block.text
            elif isinstance(message, ResultMessage):
                if isinstance(message.result, str) and message.result.strip():
                    speech = message.result

    return speech.strip(), handlers.recipe, handlers.animation


def bake_video(entry_path: Path, animation: dict) -> bool:
    spec_path = entry_path.with_suffix(".spec.json")
    spec_path.write_text(json.dumps(animation), encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, "-m", MANIM_RENDER_MODULE, str(spec_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  render failed: {result.stderr.strip().splitlines()[-1:]}")
            return False
        return True
    finally:
        spec_path.unlink(missing_ok=True)


async def build(names: list[dict], render_videos: bool) -> None:
    out_dir = PROJECT_ROOT / CATALOGUE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    for index, item in enumerate(names, start=1):
        name = item["name"]
        aliases = item.get("aliases", [])
        target = out_dir / f"{slug(name)}.json"

        if target.is_file():
            print(f"[{index}/{len(names)}] {name}: already built, skipping")
            continue

        print(f"[{index}/{len(names)}] {name}: generating")
        try:
            speech, recipe, animation = await generate(name)
        except Exception as exc:
            print(f"  generation failed: {exc}")
            continue

        if recipe is None or animation is None:
            print(f"  incomplete (recipe={recipe is not None}, animation={animation is not None})")
            continue

        entry = {
            "name": name,
            "aliases": aliases,
            "speech": speech,
            "recipe": recipe,
            "animation": animation,
        }
        target.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        print(f"  wrote {target.name}")

        if render_videos:
            print("  baking video")
            bake_video(target, animation)


def main(argv: list[str]) -> int:
    source = PROJECT_ROOT / CATALOGUE_DIR / CATALOGUE_SOURCES_FILE
    if not source.is_file():
        print(f"missing source list: {source}")
        return 2

    names = json.loads(source.read_text(encoding="utf-8"))

    render_videos = "--render" in argv
    if not render_videos:
        print(f"spec only (ANIM_BACKEND={ANIM_BACKEND_CANVAS} needs no mp4); pass --render to bake videos")

    asyncio.run(build(names, render_videos))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
