import threading
import time
from PyQt6.QtCore import QThread, pyqtSignal

from app.threads.bottle_scan_worker import BottleScanWorker
from app.threads.manim_render_worker import ManimRenderWorker


class Agent(QThread):
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    show_reply = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    render_succeeded = pyqtSignal(str)


    def __init__(self, message: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.message = message
        self._paused = threading.Event()
        self.manim_worker = None
        self.bottle_worker = None

    def run(self) -> None:
        self.thinking_started.emit()

        #===========================================================================================================================================================
        # TESTING THE AGENT
        if self.message.startswith("json"):
            path = self.message[4:]
            with open(path, "r", encoding="utf-8") as file:
                raw_agent_output = file.read()
            self.generate_and_show_from_string(raw_agent_output)
        elif self.message.startswith("img"):
            path = self.message[3:]
            self.scan_from_image_path(path)
        else:
            time.sleep(1)
            output_messgae = "For a classic Daiquiri, measure 60ml of white rum, 30ml fresh lime juice, and 1/2 oz of 2:1 rich simple syrup."
            self.thinking_ended.emit()
            self.show_reply.emit(output_messgae)
        #===========================================================================================================================================================

    def scan_from_image_path(self, path: str):
        self.bottle_worker = BottleScanWorker(
            image_input=path,
            gpu=False,
        )
        self.bottle_worker.scan_finished.connect(self._on_scan_success)
        self.bottle_worker.scan_failed.connect(self._on_scan_failure)

        self.bottle_worker.start()

    def _on_scan_success(self, output: list):
        output_messgae = f"Bottles: {",".join(output)}"
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)

    def _on_scan_failure(self, error_msg: str):
        output_messgae = f"Scanning failed: {error_msg}"
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)


    def generate_and_show_from_string(self, recipe_json_string: str):
        self.manim_worker = ManimRenderWorker(recipe_json_string, self)
        self.manim_worker.rendering_finished.connect(self._on_render_success)
        self.manim_worker.rendering_failed.connect(self._on_render_failure)

        self.manim_worker.start()

    def _on_render_success(self, output_mp4_path: str):
        output_messgae = "Render completed"
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)
        self.render_succeeded.emit(output_mp4_path)

    def _on_render_failure(self, error_msg: str):
        output_messgae = f"Rendering failed: {error_msg}"
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)


    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self.requestInterruption()
        self.wait()