import faulthandler
import sys
import traceback
import weakref
from PyQt6.QtCore import QThread, QtMsgType, qInstallMessageHandler

from app.config import LOG_PREFIX_ERROR, QTHREAD_DIAGNOSTICS_ENABLED, QTHREAD_LOG_PREFIX

_tracked: "weakref.WeakSet[QThread]" = weakref.WeakSet()
_previous_handler = None


def install_diagnostics() -> None:
    global _previous_handler

    if not QTHREAD_DIAGNOSTICS_ENABLED:
        return
    faulthandler.enable()
    _previous_handler = qInstallMessageHandler(_on_qt_message)


def track(thread: QThread, name: str) -> QThread:
    thread.setObjectName(name)
    if not QTHREAD_DIAGNOSTICS_ENABLED:
        return thread

    _tracked.add(thread)
    thread.started.connect(lambda: _log(f"started    {name}"))
    thread.finished.connect(lambda: _log(f"finished   {name}"))
    _log(f"created    {name}")
    return thread


def running_names() -> list[str]:
    return sorted(t.objectName() or repr(t) for t in _tracked if t.isRunning())


def log_running(label: str) -> None:
    if not QTHREAD_DIAGNOSTICS_ENABLED:
        return
    _log(f"{label}: running={running_names() or ['none']}")


def _on_qt_message(mode, context, message) -> None:
    if mode == QtMsgType.QtFatalMsg and "still running" in message:
        _dump_crash_context(message)

    if _previous_handler is not None:
        _previous_handler(mode, context, message)
    else:
        print(message, file=sys.stderr, flush=True)


def _dump_crash_context(message: str) -> None:
    print(f"{LOG_PREFIX_ERROR} {message}", file=sys.stderr)
    print(f"{LOG_PREFIX_ERROR} still running: {running_names()}", file=sys.stderr)
    print(f"{LOG_PREFIX_ERROR} destroyed from:", file=sys.stderr)
    traceback.print_stack(file=sys.stderr)
    sys.stderr.flush()
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()


def _log(text: str) -> None:
    print(f"{QTHREAD_LOG_PREFIX} {text}", flush=True)
