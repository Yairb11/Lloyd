import json
import threading
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from app.agent import ask_bartender
from app.config import (
    AGENT_CLARIFY_OPERATION,
    AGENT_ERROR_SPEECH,
    AGENT_INVALID_RECIPE_SPEECH,
    AGENT_RENDER_STATUS_TEXT,
    AGENT_STEP_BY_STEP_OPERATION,
    LOG_PREFIX_ERROR,
)
from app.threads.bottle_scan_worker import BottleScanWorker
from app.threads.cancellable_worker import CancellableWorker
from app.threads.manim_render_worker import ManimRenderWorker


class Agent(QThread):
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    show_reply = pyqtSignal(str)
    show_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    render_succeeded = pyqtSignal(str)
    session_id_updated = pyqtSignal(str)

    _popup_requested = pyqtSignal(object)

    def __init__(self, message: str, session_id: str | None = None, parent=None) -> None:
        super().__init__(parent=parent)
        self.message = message
        self.session_id = session_id
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

        try:
            envelope = ask_bartender(self.message, self.session_id)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            self.show_reply.emit(AGENT_ERROR_SPEECH)
            self.thinking_ended.emit()
            return

        current_session_id = envelope.get("session_id") or self.session_id

        if envelope.get("operation") == AGENT_CLARIFY_OPERATION:
            self.scan_image()

            if self._scan_result_path is None:
                return

            self._active_scan_path = self._scan_result_path
            try:
                envelope = ask_bartender(self._scan_result_path, current_session_id)
            except Exception as exc:
                self.error_occurred.emit(str(exc))
                self.show_reply.emit(AGENT_ERROR_SPEECH)
                self.thinking_ended.emit()
                return
            finally:
                self._cleanup_scan_file()

            current_session_id = envelope.get("session_id") or current_session_id

            if envelope.get("operation") == AGENT_CLARIFY_OPERATION:
                self.error_occurred.emit("scan still needs a path after auto-fulfillment")
                self.show_reply.emit(AGENT_ERROR_SPEECH)
                self.thinking_ended.emit()
                if current_session_id:
                    self.session_id_updated.emit(current_session_id)
                return

        operation = envelope.get("operation")

        if operation == AGENT_STEP_BY_STEP_OPERATION:
            data = envelope.get("data")
            if not isinstance(data, dict) or not all(k in data for k in ("name", "glass_type", "ingredients", "steps")):
                self.thinking_ended.emit()
                self.show_reply.emit(envelope.get("speech") or AGENT_INVALID_RECIPE_SPEECH)
            else:
                self.show_reply.emit(envelope.get("speech", ""))
                self.generate_and_show_from_string(json.dumps(data))
        else:
            self.thinking_ended.emit()
            self.show_reply.emit(envelope.get("speech", ""))

        if current_session_id:
            self.session_id_updated.emit(current_session_id)

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
        output_messgae = f"Bottles: {','.join(output)}"
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
        self.thinking_ended.emit()
        self.show_status.emit(AGENT_RENDER_STATUS_TEXT)
        self.render_succeeded.emit(output_mp4_path)

    def _on_render_failure(self, error_msg: str):
        self.thinking_ended.emit()
        self.show_reply.emit(f"Rendering failed: {error_msg}")

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()
