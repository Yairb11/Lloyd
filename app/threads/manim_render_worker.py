import json
import os
import shutil
from pathlib import Path
from manim import config as manim_config
from PyQt6.QtCore import QThread, pyqtSignal

from app.config import MANIM_OUTPUT_DIR, MANIM_QUALITY, MANIM_TEMP_DIR_PREFIX, MANIM_VERBOSITY, MANIM_VIDEO_EXTENSION
from app.helpers.cocktail_animation_scene import CocktailAnimationScene
from app.helpers.text import sanitize_cocktail_filename
from app.threads.cancellable_worker import CancellableWorker
from app.helpers import perf

class ManimRenderWorker(CancellableWorker):
    rendering_finished = pyqtSignal(str)
    rendering_failed = pyqtSignal(str)

    def __init__(self, recipe_str: str, parent=None):
        super().__init__(parent)
        self.recipe_str = recipe_str
        self._temp_media_dir: Path | None = None

    def do_work(self):
        try:
            parsed_data = json.loads(self.recipe_str.strip())
        except Exception as exc:
            self.rendering_failed.emit(f"Invalid JSON recipe string: {exc}")
            return

        if self.is_cancelled():
            return

        cocktail_name = parsed_data.get("name", "Cocktail")
        base_filename = sanitize_cocktail_filename(cocktail_name)

        output_dir = Path(MANIM_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        final_mp4 = (output_dir / f"{base_filename}{MANIM_VIDEO_EXTENSION}").resolve()

        self._temp_media_dir = Path(f"{MANIM_TEMP_DIR_PREFIX}{base_filename}")
        self._temp_media_dir.mkdir(parents=True, exist_ok=True)

        manim_config.media_dir = str(self._temp_media_dir)
        manim_config.output_file = base_filename
        manim_config.preview = False
        manim_config.quality = MANIM_QUALITY
        manim_config.verbosity = MANIM_VERBOSITY

        try:
            scene = CocktailAnimationScene(parsed_data)
            perf.mark("render.start")
            scene.render()

            if self.is_cancelled():
                return

            generated_files = list(self._temp_media_dir.rglob(f"{base_filename}{MANIM_VIDEO_EXTENSION}"))
            if not generated_files:
                self.rendering_failed.emit(f"Render failed: Output file {base_filename}{MANIM_VIDEO_EXTENSION} not found.")
                return

            tmp_final = final_mp4.with_name(f"{final_mp4.stem}.tmp{final_mp4.suffix}")
            try:
                shutil.copy2(generated_files[0], tmp_final)
                os.replace(tmp_final, final_mp4)
            finally:
                tmp_final.unlink(missing_ok=True)

            perf.mark("render.done")
            self.rendering_finished.emit(str(final_mp4))

        except Exception as exc:
            self.rendering_failed.emit(str(exc))

    def cleanup(self) -> None:
        if self._temp_media_dir is not None and self._temp_media_dir.exists():
            shutil.rmtree(self._temp_media_dir, ignore_errors=True)