import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from jsonschema import ValidationError, validate
import itertools

from app.helpers.qthread_support import track
from app.agent import ask_bartender
from app.agent.step_by_step_schema import STEP_BY_STEP_SCHEMA
from app.config import (
    AGENT_CLARIFY_OPERATION,
    AGENT_ERROR_SPEECH,
    AGENT_INVALID_RECIPE_SPEECH,
    AGENT_INVALID_STEP_BY_STEP_SPEECH,
    AGENT_RECIPE_OPERATION,
    AGENT_RECIPE_REQUIRED_KEYS,
    AGENT_RENDER_STARTED_TEXT,
    AGENT_RENDER_STATUS_TEXT,
    AGENT_STEP_BY_STEP_OPERATION,
    LOG_PREFIX_ERROR,
    MANIM_OUTPUT_DIR,
    MANIM_VIDEO_EXTENSION,
    STEP_BY_STEP_RERENDER_KEYWORDS,
    STEP_BY_STEP_DEBUG_DIR,
)
from app.helpers.text import sanitize_cocktail_filename
from app.threads.cancellable_worker import CancellableWorker
from app.threads.manim_render_worker import ManimRenderWorker
from app.helpers import perf

_agent_sequence = itertools.count(1)

class Agent(QThread):
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    show_reply = pyqtSignal(str)
    show_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    render_succeeded = pyqtSignal(str)
    video_render_started = pyqtSignal(str)
    recipe_ready = pyqtSignal(dict)
    session_id_updated = pyqtSignal(str)

    _popup_requested = pyqtSignal(object)

    def __init__(self, message: str, session_id: str | None = None, parent=None) -> None:
        super().__init__(parent=parent)
        track(self, f"Agent-{next(_agent_sequence)}")
        self.message = message
        self.session_id = session_id
        self._paused = threading.Event()
        self._interrupted = threading.Event()
        self._cli_process: subprocess.Popen | None = None
        self._child_workers: list[CancellableWorker] = []
        self.manim_worker = None
        self._scan_popup = None
        self._scan_result_path: str | None = None
        self._active_scan_path: str | None = None

        self._popup_requested.connect(self._create_scan_popup)

    def run(self) -> None:
        self.thinking_started.emit()

        perf.mark("agent.query_sent")
        try:
            envelope = ask_bartender(
                self.message, self.session_id, on_process_started=self._on_cli_process_started
            )
        except Exception as exc:
            if self._interrupted.is_set():
                return
            self.error_occurred.emit(str(exc))
            self.show_reply.emit(AGENT_ERROR_SPEECH)
            self.thinking_ended.emit()
            return
        perf.mark("agent.reply_ready")

        if self._interrupted.is_set():
            return

        current_session_id = envelope.get("session_id") or self.session_id

        if envelope.get("operation") == AGENT_CLARIFY_OPERATION:
            self.scan_image()

            if self._interrupted.is_set() or self._scan_result_path is None:
                return

            self._active_scan_path = self._scan_result_path
            perf.mark("agent.scan_query_sent")
            try:
                envelope = ask_bartender(
                    self._scan_result_path,
                    current_session_id,
                    on_process_started=self._on_cli_process_started,
                )
            except Exception as exc:
                if self._interrupted.is_set():
                    return
                self.error_occurred.emit(str(exc))
                self.show_reply.emit(AGENT_ERROR_SPEECH)
                self.thinking_ended.emit()
                return
            finally:
                self._cleanup_scan_file()
            perf.mark("agent.scan_reply_ready")

            if self._interrupted.is_set():
                return

            current_session_id = envelope.get("session_id") or current_session_id

            if envelope.get("operation") == AGENT_CLARIFY_OPERATION:
                self.error_occurred.emit("scan still needs a path after auto-fulfillment")
                self.show_reply.emit(AGENT_ERROR_SPEECH)
                self.thinking_ended.emit()
                if current_session_id:
                    self.session_id_updated.emit(current_session_id)
                return

        operation = envelope.get("operation")

        if operation == AGENT_RECIPE_OPERATION:
            data = envelope.get("data")
            if not isinstance(data, dict) or not all(k in data for k in AGENT_RECIPE_REQUIRED_KEYS):
                self.thinking_ended.emit()
                self.show_reply.emit(envelope.get("speech") or AGENT_INVALID_RECIPE_SPEECH)
            else:
                self.thinking_ended.emit()
                self.show_reply.emit(envelope.get("speech", ""))
                self.recipe_ready.emit(data)
        elif operation == AGENT_STEP_BY_STEP_OPERATION:
            data = envelope.get("data")
            if not isinstance(data, dict) or not self._is_valid_step_by_step(data):
                self.thinking_ended.emit()
                self.show_reply.emit(envelope.get("speech") or AGENT_INVALID_STEP_BY_STEP_SPEECH)
            else:
                self.show_reply.emit(envelope.get("speech", ""))
                existing_path = self._existing_render_path(data.get("name", "Cocktail"))
                if existing_path is not None and not self._wants_rerender(self.message):
                    self.thinking_ended.emit()
                    self.show_status.emit(AGENT_RENDER_STATUS_TEXT)
                    perf.mark("render.cached")
                    self.render_succeeded.emit(str(existing_path))
                else:
                    self._dump_step_by_step_debug(data)
                    cocktail_name = data.get("name", "Cocktail")
                    self.video_render_started.emit(cocktail_name)
                    self.show_status.emit(AGENT_RENDER_STARTED_TEXT)
                    self.generate_and_show_from_string(json.dumps(data))
        else:
            self.thinking_ended.emit()
            self.show_reply.emit(envelope.get("speech", ""))

        if current_session_id:
            self.session_id_updated.emit(current_session_id)

    def _is_valid_step_by_step(self, data: dict) -> bool:
        try:
            validate(instance=data, schema=STEP_BY_STEP_SCHEMA)
        except ValidationError:
            return False
        return True

    def _on_cli_process_started(self, proc: subprocess.Popen) -> None:
        self._cli_process = proc

    def interrupt(self) -> None:
        self._interrupted.set()
        self.stop_active_worker()
        proc = self._cli_process
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass

    def _existing_render_path(self, cocktail_name: str) -> Path | None:
        filename = sanitize_cocktail_filename(cocktail_name)
        path = (Path(MANIM_OUTPUT_DIR) / f"{filename}{MANIM_VIDEO_EXTENSION}").resolve()
        return path if path.is_file() else None

    def _wants_rerender(self, message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in STEP_BY_STEP_RERENDER_KEYWORDS)

    def _spawn_child(self, worker: CancellableWorker) -> None:
        self._child_workers.append(worker)

    def stop_active_worker(self) -> None:
        for worker in self._child_workers:
            worker.request_stop()

    def shutdown(self) -> None:
        self._interrupted.set()
        self.stop_active_worker()
        proc = self._cli_process
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
        if self._scan_popup is not None:
            self._scan_popup.close()
        for worker in self._child_workers:
            worker.wait()
        self.wait()

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

    def _cleanup_scan_file(self) -> None:
        path = self._active_scan_path
        self._active_scan_path = None
        if path is None:
            return
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as exc:
            print(f"{LOG_PREFIX_ERROR}: could not delete uploaded scan {path}: {exc}")

    def _dump_step_by_step_debug(self, data: dict) -> None:
        debug_dir = Path(STEP_BY_STEP_DEBUG_DIR)
        filename = sanitize_cocktail_filename(data.get("name", "Cocktail"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = debug_dir / f"{filename}_{timestamp}.json"
        try:
            debug_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            print(f"{LOG_PREFIX_ERROR}: could not write step-by-step debug json {path}: {exc}")

    def _on_scan_failure(self, error_msg: str):
        output_messgae = f"Scanning failed: {error_msg}"
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)

    def generate_and_show_from_string(self, recipe_json_string: str):
        self.manim_worker = ManimRenderWorker(recipe_json_string)
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