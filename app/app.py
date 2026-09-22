import os
import sys
import traceback

from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.core import qthread_support
from app.widgets.main_window import MainWindow

_window: MainWindow | None = None


def _crash_excepthook(exc_type, exc_value, exc_tb) -> None:
    traceback.print_exception(exc_type, exc_value, exc_tb)

    if _window is not None:
        try:
            _window.close()
        except Exception:
            pass

    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)


def run() -> None:
    global _window
    qthread_support.install_diagnostics()
    sys.excepthook = _crash_excepthook

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)

    _window = MainWindow()
    _window.show()

    sys.exit(app.exec())
