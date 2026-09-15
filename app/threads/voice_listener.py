import threading
from PyQt6.QtCore import QThread, pyqtSignal


class VoiceListener(QThread):

    wake_word_detected = pyqtSignal(str)
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._paused = threading.Event()

        # TRIGGER LIKE SIRI OR ALEXSA -> speech_started()
        # GET THE USERS VOICE AND COMMENDS -> wake_word_detected()
        # ON ERROR RUN -> error_occurred() 
        # SEND THE COMMEND -> speech_ended()



    def run(self) -> None:
        # RUNS THE LISTENER IN THE BACKGROUND
        pass

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self.requestInterruption()
        self.wait()