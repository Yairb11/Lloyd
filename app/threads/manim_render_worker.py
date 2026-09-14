import re
import json
import shutil
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from manim import config

from app.helpers.cocktail_animation_scene import CocktailAnimationScene



class ManimRenderWorker(QThread):
    rendering_finished = pyqtSignal(str)
    rendering_failed = pyqtSignal(str)

    def __init__(self, recipe_str: str, parent=None):
        super().__init__(parent)
        self.recipe_str = recipe_str

    def run(self):
        try:
            parsed_data = json.loads(self.recipe_str.strip())
        except Exception as exc:
            self.rendering_failed.emit(f"Invalid JSON recipe string: {exc}")
            return

        cocktail_name = parsed_data.get("name", "Cocktail")
        base_filename = self.sanitize_filename(cocktail_name)

        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_mp4 = (output_dir / f"{base_filename}.mp4").resolve()

        temp_media_dir = Path(f"media_temp_{base_filename}")
        temp_media_dir.mkdir(parents=True, exist_ok=True)

        config.media_dir = str(temp_media_dir)
        config.output_file = base_filename
        config.preview = False
        config.quality = "low_quality"
        config.verbosity = "ERROR"

        try:
            scene = CocktailAnimationScene(parsed_data)
            scene.render()


            generated_files = list(temp_media_dir.rglob(f"{base_filename}.mp4"))
            if not generated_files:
                self.rendering_failed.emit(f"Render failed: Output file {base_filename}.mp4 not found.")
                return

            shutil.copy2(generated_files[0], final_mp4)
            self.rendering_finished.emit(str(final_mp4))

        except Exception as exc:
            self.rendering_failed.emit(str(exc))
        finally:
            if temp_media_dir.exists():
                shutil.rmtree(temp_media_dir, ignore_errors=True)

    def sanitize_filename(self, name: str) -> str:
        clean_name = re.sub(r"[^\w\s]", "", name)
        return "".join(word.capitalize() for word in clean_name.split())
