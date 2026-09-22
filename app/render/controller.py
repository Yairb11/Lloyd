import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

from app.config import (
    ANIM_DEFAULT_COCKTAIL_NAME, LOG_PREFIX_ERROR, LOG_PREFIX_RENDER,
    MANIM_OUTPUT_DIR, MANIM_RENDER_FAILED_MARKER, MANIM_RENDER_MODULE,
    MANIM_RENDER_OK_MARKER, MANIM_SPEC_FILE_PREFIX, MANIM_SPEC_SIDECAR_EXTENSION,
    MANIM_VIDEO_EXTENSION, RENDER_KILL_TIMEOUT_MS, STEP_BY_STEP_DEBUG_DIR,
    STEP_BY_STEP_RERENDER_KEYWORDS,
)
from app.core import perf
from app.core.paths import PROJECT_ROOT
from app.core.text import sanitize_cocktail_filename


def spec_fingerprint(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"))


def cached_render_path(cocktail_name: str, spec: dict) -> Path | None:
    base = sanitize_cocktail_filename(cocktail_name)
    output_dir = Path(MANIM_OUTPUT_DIR)
    video = (output_dir / f"{base}{MANIM_VIDEO_EXTENSION}").resolve()
    if not video.is_file():
        return None

    sidecar = output_dir / f"{base}{MANIM_SPEC_SIDECAR_EXTENSION}"
    try:
        recorded = sidecar.read_text(encoding="utf-8")
    except OSError:
        return None

    return video if recorded == spec_fingerprint(spec) else None


def wants_rerender(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in STEP_BY_STEP_RERENDER_KEYWORDS)


def write_spec(spec: dict) -> Path:
    path = Path(tempfile.gettempdir()) / f"{MANIM_SPEC_FILE_PREFIX}{uuid4().hex}.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def parse_render_ok(stdout: str) -> str | None:
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(MANIM_RENDER_OK_MARKER):
            return line[len(MANIM_RENDER_OK_MARKER):]
    return None


def parse_render_error(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith(MANIM_RENDER_FAILED_MARKER):
            return line[len(MANIM_RENDER_FAILED_MARKER):]
    return lines[-1] if lines else ""


def dump_spec_debug(spec: dict) -> None:
    debug_dir = Path(STEP_BY_STEP_DEBUG_DIR)
    filename = sanitize_cocktail_filename(spec.get("name", ANIM_DEFAULT_COCKTAIL_NAME))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = debug_dir / f"{filename}_{timestamp}.json"
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"{LOG_PREFIX_ERROR}: could not write spec debug json {path}: {exc}")


class RenderController(QObject):
    render_started = pyqtSignal(str)
    render_finished = pyqtSignal(str)
    render_failed = pyqtSignal(str)
    render_cached = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._process: QProcess | None = None
        self._spec_path: Path | None = None
        self._stdout: str = ""
        self._stderr: str = ""
        self._last_message: str = ""

    def set_last_message(self, message: str) -> None:
        self._last_message = message

    def request(self, spec: dict) -> None:
        name = spec.get("name", ANIM_DEFAULT_COCKTAIL_NAME)

        if not wants_rerender(self._last_message):
            cached = cached_render_path(name, spec)
            if cached is not None:
                perf.mark("render.cached")
                print(f"{LOG_PREFIX_RENDER} cached {cached}")
                self.render_cached.emit(str(cached))
                return

        dump_spec_debug(spec)
        self._start(spec, name)

    def _start(self, spec: dict, name: str) -> None:
        self.cancel()

        try:
            self._spec_path = write_spec(spec)
        except OSError as exc:
            self.render_failed.emit(str(exc))
            return

        self._stdout = ""
        self._stderr = ""

        process = QProcess(self)
        process.setProgram(sys.executable)
        process.setArguments(["-m", MANIM_RENDER_MODULE, str(self._spec_path)])
        process.setWorkingDirectory(str(PROJECT_ROOT))
        process.readyReadStandardOutput.connect(self._on_stdout)
        process.readyReadStandardError.connect(self._on_stderr)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_process_error)
        self._process = process

        perf.mark("render.start")
        print(f"{LOG_PREFIX_RENDER} start {name} -> {sys.executable} -m {MANIM_RENDER_MODULE}")
        self.render_started.emit(name)
        process.start()

    def cancel(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return

        try:
            process.finished.disconnect(self._on_finished)
        except TypeError:
            pass

        if process.state() != QProcess.ProcessState.NotRunning:
            process.kill()
            process.waitForFinished(RENDER_KILL_TIMEOUT_MS)

        process.deleteLater()
        self._cleanup_spec()

    def shutdown(self) -> None:
        self.cancel()

    def _on_stdout(self) -> None:
        process = self._process
        if process is None:
            return
        self._stdout += bytes(process.readAllStandardOutput()).decode("utf-8", "replace")

    def _on_stderr(self) -> None:
        process = self._process
        if process is None:
            return
        self._stderr += bytes(process.readAllStandardError()).decode("utf-8", "replace")

    def _on_process_error(self, error) -> None:
        print(f"{LOG_PREFIX_RENDER} process error: {error}")

    def _on_finished(self, exit_code: int, exit_status) -> None:
        process = self._process
        if process is not None:
            self._stdout += bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            self._stderr += bytes(process.readAllStandardError()).decode("utf-8", "replace")

        self._process = None
        if process is not None:
            process.deleteLater()

        self._cleanup_spec()
        perf.mark("render.done")

        path = parse_render_ok(self._stdout)
        print(f"{LOG_PREFIX_RENDER} finished exit={exit_code} path={path}")

        if exit_code == 0 and path is not None:
            self.render_finished.emit(path)
            return

        detail = parse_render_error(self._stderr) or f"render exited with code {exit_code}"
        self.render_failed.emit(detail)

    def _cleanup_spec(self) -> None:
        path = self._spec_path
        self._spec_path = None
        if path is None:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            print(f"{LOG_PREFIX_ERROR}: could not delete render spec {path}: {exc}")
