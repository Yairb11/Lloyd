import sys

from PyQt6.QtWidgets import QApplication

from app import config
from app.widgets import MainWindow


def run() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName(config.ORG_NAME)
    app.setApplicationName(config.APP_NAME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())