import threading
import time
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from app.config import LOG_PREFIX_ERROR
from app.threads.bottle_scan_worker import BottleScanWorker
from app.threads.cancellable_worker import CancellableWorker
from app.threads.manim_render_worker import ManimRenderWorker


class Agent(QThread):
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    show_reply = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    render_succeeded = pyqtSignal(str)

    _popup_requested = pyqtSignal(object)

    def __init__(self, message: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.message = message
        self._paused = threading.Event()
        self._child_workers: list[CancellableWorker] = []
        self.manim_worker = None
        self.bottle_worker = None
        self._scan_popup = None
        self._scan_result_path: str | None = None
        self._active_scan_path: str | None = None

        self._popup_requested.connect(self._create_scan_popup)

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
            self.scan_image()
        else:
            time.sleep(1)
            output_messgae = "For a classic Daiquiri."
            self.thinking_ended.emit()
            self.show_reply.emit(output_messgae)
        #===========================================================================================================================================================

    def _spawn_child(self, worker: CancellableWorker) -> None:
        self._child_workers.append(worker)

    def stop_active_worker(self) -> None:
        for worker in self._child_workers:
            worker.request_stop()

    def scan_image(self) -> None:
        done_event = threading.Event()
        self._scan_result_path = None
        self._popup_requested.emit(done_event)
        done_event.wait()

        if self._scan_result_path is not None:
            self.scan_from_image_path(self._scan_result_path)

    def _create_scan_popup(self, done_event: threading.Event) -> None:
        from app.widgets.scan_receiver_popup import ScanReceiverPopup

        try:
            self._scan_popup = ScanReceiverPopup(agent=self, done_event=done_event)
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: failed to start phone scan server: {exc}")
            self._on_scan_failure(f"Could not start the phone scan server: {exc}")
            done_event.set()
            return
        self._scan_popup.show()

    def scan_from_image_path(self, path: str):
        self._active_scan_path = path
        self.bottle_worker = BottleScanWorker(
            image_input=path,
            gpu=False,
        )
        self._spawn_child(self.bottle_worker)
        self.bottle_worker.scan_finished.connect(self._on_scan_success)
        self.bottle_worker.scan_failed.connect(self._on_scan_failure)
        self.bottle_worker.finished.connect(self._cleanup_scan_file)

        self.bottle_worker.start()

    def _cleanup_scan_file(self) -> None:
        path = self._active_scan_path
        self._active_scan_path = None
        if path is None:
            return
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as exc:
            print(f"{LOG_PREFIX_ERROR}: could not delete uploaded scan {path}: {exc}")

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
        self._spawn_child(self.manim_worker)
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