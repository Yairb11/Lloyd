import os
import sys
import traceback

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME, LOG_PREFIX_ERROR, MCP_WATCHDOG_POLL_INTERVAL_S, ORG_NAME
from app.setup import is_mcp_server_alive, shutdown_mcp_server
from app.widgets import MainWindow

_window: MainWindow | None = None
_mcp_watchdog: QTimer | None = None


def _crash_excepthook(exc_type, exc_value, exc_tb) -> None:
    traceback.print_exception(exc_type, exc_value, exc_tb)

    if _window is not None:
        try:
            _window.close()
        except Exception:
            pass

    try:
        shutdown_mcp_server()
    except Exception:
        pass

    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)


def _on_mcp_watchdog_tick() -> None:
    if is_mcp_server_alive():
        return

    print(f"{LOG_PREFIX_ERROR} MCP server terminal is no longer running — shutting down.")

    if _mcp_watchdog is not None:
        _mcp_watchdog.stop()

    if _window is not None:
        try:
            _window.close()
        except Exception:
            pass

    try:
        shutdown_mcp_server()
    except Exception:
        pass

    QApplication.quit()


def run() -> None:
    global _window, _mcp_watchdog
    sys.excepthook = _crash_excepthook

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)
    app.aboutToQuit.connect(shutdown_mcp_server)

    _window = MainWindow()
    _window.show()

    _mcp_watchdog = QTimer()
    _mcp_watchdog.setInterval(int(MCP_WATCHDOG_POLL_INTERVAL_S * 1000))
    _mcp_watchdog.timeout.connect(_on_mcp_watchdog_tick)
    _mcp_watchdog.start()

    sys.exit(app.exec())
