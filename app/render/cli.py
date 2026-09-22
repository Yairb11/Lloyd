import json
import os
import shutil
import sys
import time
from pathlib import Path

from app.config import (
    ANIM_DEFAULT_COCKTAIL_NAME, MANIM_DISABLE_CACHING, MANIM_OUTPUT_DIR,
    MANIM_PROGRESS_BAR, MANIM_QUALITY, MANIM_RENDERER,
    MANIM_RENDER_FAILED_MARKER, MANIM_RENDER_OK_MARKER, MANIM_SPEC_SIDECAR_EXTENSION,
    MANIM_TEMP_DIR_PREFIX, MANIM_VERBOSITY, MANIM_VIDEO_EXTENSION,
)
from app.core.text import sanitize_cocktail_filename


def spec_fingerprint(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"))


def sidecar_path(output_dir: Path, base: str) -> Path:
    return output_dir / f"{base}{MANIM_SPEC_SIDECAR_EXTENSION}"


def render(spec_path: str) -> int:
    from manim import config as manim_config

    from app.animation.scene import CocktailAnimationScene

    try:
        data = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{MANIM_RENDER_FAILED_MARKER}{exc}", file=sys.stderr, flush=True)
        return 1

    base = sanitize_cocktail_filename(data.get("name", ANIM_DEFAULT_COCKTAIL_NAME))
    temp_dir = Path(f"{MANIM_TEMP_DIR_PREFIX}{base}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    manim_config.media_dir = str(temp_dir)
    manim_config.output_file = base
    manim_config.preview = False
    manim_config.quality = MANIM_QUALITY
    manim_config.verbosity = MANIM_VERBOSITY
    manim_config.renderer = MANIM_RENDERER
    manim_config.progress_bar = MANIM_PROGRESS_BAR
    manim_config.disable_caching = MANIM_DISABLE_CACHING
    manim_config.flush_cache = MANIM_DISABLE_CACHING

    started = time.perf_counter()
    try:
        CocktailAnimationScene(data).render()

        produced = next(temp_dir.rglob(f"{base}{MANIM_VIDEO_EXTENSION}"), None)
        if produced is None:
            print(
                f"{MANIM_RENDER_FAILED_MARKER}no output file for {base}",
                file=sys.stderr,
                flush=True,
            )
            return 1

        output_dir = Path(MANIM_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        final = (output_dir / f"{base}{MANIM_VIDEO_EXTENSION}").resolve()
        staged = final.with_name(f"{final.stem}.tmp{final.suffix}")
        shutil.copy2(produced, staged)
        os.replace(staged, final)

        try:
            sidecar_path(output_dir, base).write_text(
                spec_fingerprint(data), encoding="utf-8"
            )
        except OSError as exc:
            print(f"sidecar_write_failed={exc}", file=sys.stderr, flush=True)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        print(f"render_ms={elapsed_ms:.0f}", file=sys.stderr, flush=True)
        print(f"{MANIM_RENDER_OK_MARKER}{final}", flush=True)
        return 0

    except Exception as exc:
        print(f"{MANIM_RENDER_FAILED_MARKER}{exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            f"{MANIM_RENDER_FAILED_MARKER}usage: python -m app.render.cli <spec.json>",
            file=sys.stderr,
            flush=True,
        )
        return 2
    return render(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
