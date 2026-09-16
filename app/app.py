import sys
from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.setup import shutdown_mcp_server
from app.widgets import MainWindow


def run() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)
    app.aboutToQuit.connect(shutdown_mcp_server)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())