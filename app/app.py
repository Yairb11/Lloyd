import sys
from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.widgets import MainWindow


def run() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())