import threading
from PyQt6.QtCore import QThread, pyqtSignal
import time

from app.config import *

class Agent(QThread):
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    show_reply = pyqtSignal(str)
    error_occurred = pyqtSignal(str)


    def __init__(self, message: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.message = message
        self._paused = threading.Event()

    def run(self) -> None:
        self.thinking_started.emit()
        time.sleep(1)
        output_messgae = "For a classic Daiquiri, measure 60ml of white rum, 30ml fresh lime juice, and 1/2 oz of 2:1 rich simple syrup."
        self.thinking_ended.emit()
        self.show_reply.emit(output_messgae)

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self.requestInterruption()
        self.wait()
