import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from app.config import (
    PERF_ENABLED,
    PERF_LOG_DIR,
    PERF_LOG_FILENAME_FORMAT,
    PERF_LOG_PREFIX,
    PERF_LOG_TO_FILE,
    PERF_STAGE_COLUMN_WIDTH,
)

_lock = threading.Lock()

_turn_label: str = ""
_turn_index: int = 0
_turn_started_at: float = 0.0
_last_mark_at: float = 0.0
_seen_stages: set[str] = set()

_log_file: TextIO | None = None
_log_unavailable: bool = False


def start(label: str = "turn") -> None:
    if not PERF_ENABLED:
        return
    with _lock:
        _begin_locked(label, time.perf_counter())


def mark(stage: str, once: bool = False) -> None:
    global _last_mark_at

    if not PERF_ENABLED:
        return

    now = time.perf_counter()
    with _lock:
        if not _turn_label:
            _begin_locked("untracked", now)
        if once and stage in _seen_stages:
            return
        _seen_stages.add(stage)

        delta_ms = (now - _last_mark_at) * 1000.0
        total_ms = (now - _turn_started_at) * 1000.0
        _last_mark_at = now

        _emit_locked(
            f"{stage:<{PERF_STAGE_COLUMN_WIDTH}} +{delta_ms:8.1f} ms   (total {total_ms:8.1f} ms)",
            {
                "event": "mark",
                "stage": stage,
                "delta_ms": round(delta_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        )


def end(stage: str = "turn.end") -> None:
    global _turn_label

    if not PERF_ENABLED:
        return
    mark(stage)
    with _lock:
        _turn_label = ""


def elapsed_ms() -> float:
    if not PERF_ENABLED or not _turn_label:
        return 0.0
    return (time.perf_counter() - _turn_started_at) * 1000.0


def _begin_locked(label: str, started_at: float) -> None:
    global _turn_label, _turn_index, _turn_started_at, _last_mark_at

    _turn_label = label
    _turn_index += 1
    _turn_started_at = started_at
    _last_mark_at = started_at
    _seen_stages.clear()

    _emit_locked(f"===== {label} #{_turn_index} =====", {"event": "start"})


def _emit_locked(line: str, record: dict[str, Any]) -> None:
    print(f"{PERF_LOG_PREFIX} {line}", flush=True)

    if not PERF_LOG_TO_FILE:
        return
    handle = _log_handle_locked()
    if handle is None:
        return

    entry = {
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "turn": _turn_label,
        "index": _turn_index,
        **record,
    }
    try:
        handle.write(json.dumps(entry) + "\n")
        handle.flush()
    except OSError:
        pass


def _log_handle_locked() -> TextIO | None:
    global _log_file, _log_unavailable

    if _log_file is not None or _log_unavailable:
        return _log_file

    try:
        directory = Path(PERF_LOG_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime(PERF_LOG_FILENAME_FORMAT)
        _log_file = (directory / filename).open("a", encoding="utf-8")
    except OSError:
        _log_unavailable = True
    return _log_file
