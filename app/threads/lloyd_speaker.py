import asyncio
import io
from PyQt6.QtCore import QThread, pyqtSignal
import edge_tts
import pygame

class LloydSpeaker(QThread):
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()

    VOICE = "en-GB-RyanNeural"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._text: str = ""
        pygame.mixer.init()

    def speak(self, text: str) -> None:
        if self.isRunning():
            self.stop()
        self._text = text
        self.start()

    def run(self) -> None:
        if not self._text:
            return

        self.speech_started.emit()
        try:
            asyncio.run(self._synthesize_and_play(self._text))
        except Exception as exc:
            print(f"[Lloyd Error]: {exc}")
        finally:
            self.speech_finished.emit()

    async def _synthesize_and_play(self, text: str) -> None:
        communicate = edge_tts.Communicate(text, self.VOICE)
        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

        audio_stream.seek(0)
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy() and not self.isInterruptionRequested():
            self.msleep(50)

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.requestInterruption()
        self.wait()  