import asyncio
import io
import edge_tts
import pygame
from PyQt6.QtCore import QThread, pyqtSignal

from app.config import LOG_PREFIX_ERROR, TTS_PIPELINE_QUEUE_SIZE, TTS_POLL_INTERVAL_MS, TTS_VOICE
from app.helpers.text import split_into_sentences


class LloydSpeaker(QThread):
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()

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
            asyncio.run(self._speak_pipelined(self._text))
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: {exc}")
        finally:
            self.speech_finished.emit()

    async def _speak_pipelined(self, text: str) -> None:
        sentences = split_into_sentences(text)
        if not sentences:
            return

        queue: asyncio.Queue = asyncio.Queue(maxsize=TTS_PIPELINE_QUEUE_SIZE)
        producer = asyncio.create_task(self._produce_audio(sentences, queue))

        try:
            while True:
                audio_stream = await queue.get()
                if audio_stream is None or self.isInterruptionRequested():
                    break

                audio_stream.seek(0)
                pygame.mixer.music.load(audio_stream)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() and not self.isInterruptionRequested():
                    await asyncio.sleep(TTS_POLL_INTERVAL_MS / 1000)
        finally:
            producer.cancel()
            try:
                await producer
            except asyncio.CancelledError:
                pass

    async def _produce_audio(self, sentences: list[str], queue: asyncio.Queue) -> None:
        try:
            for sentence in sentences:
                if self.isInterruptionRequested():
                    return
                audio_stream = await self._synthesize_sentence(sentence)
                if audio_stream is not None:
                    await queue.put(audio_stream)
        finally:
            await queue.put(None)

    async def _synthesize_sentence(self, sentence: str) -> io.BytesIO | None:
        communicate = edge_tts.Communicate(sentence, TTS_VOICE)
        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if self.isInterruptionRequested():
                return None
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

        if audio_stream.tell() == 0:
            return None

        audio_stream.seek(0)
        return audio_stream

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.requestInterruption()
        self.wait()
