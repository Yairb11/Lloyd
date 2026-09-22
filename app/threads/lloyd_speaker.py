import asyncio
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from app.config import (
    SHUTDOWN_THREAD_TIMEOUT_MS,
    TTS_AMPLITUDE_NORMALIZATION_PEAK,
    TTS_AUDIO_BLOCK_FRAMES,
    TTS_INTER_SENTENCE_SILENCE_MS,
    TTS_POLL_INTERVAL_MS,
)
from app.helpers import perf
from app.helpers.audio_playback import AmplitudePlayer, silence_pcm
from app.helpers.qthread_support import track
from app.helpers.text import split_into_sentences
from app.helpers.tts_engine import create_engine

_TURN_END = object()
_THREAD_END = object()


class LloydSpeaker(QThread):
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    amplitude_changed = pyqtSignal(float)
    engine_ready = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        track(self, "LloydSpeaker")
        self._player = AmplitudePlayer(
            block_frames=TTS_AUDIO_BLOCK_FRAMES,
            amplitude_peak=TTS_AMPLITUDE_NORMALIZATION_PEAK,
            on_amplitude=self.amplitude_changed.emit,
        )
        self._engine = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue | None = None
        self._ready = threading.Event()
        self._generation: int = 0
        self._speaking: bool = False
        self._sample_rate: int | None = None

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()
            self._loop = None

    async def _serve(self) -> None:
        self._queue = asyncio.Queue()
        self._ready.set()

        self._engine = create_engine()
        await self._engine.warmup()
        perf.mark("tts.engine_ready")
        self.engine_ready.emit(self._engine.name)

        while True:
            generation, payload = await self._queue.get()
            if payload is _THREAD_END:
                break
            if generation != self._generation:
                continue
            if payload is _TURN_END:
                await self._finish_turn(generation)
                continue
            await self._speak_one(generation, payload)

        self._player.stop()

    async def _speak_one(self, generation: int, sentence: str) -> None:
        item = await self._synthesize(generation, sentence)
        if item is None or generation != self._generation:
            return

        pcm, sample_rate = item
        if not self._speaking:
            self._sample_rate = sample_rate
            perf.mark("tts.first_audio")
            self._player.start(sample_rate)
            self._speaking = True
            self.speech_started.emit()

        self._player.feed(pcm)
        self._player.feed(silence_pcm(TTS_INTER_SENTENCE_SILENCE_MS, self._sample_rate))

    async def _finish_turn(self, generation: int) -> None:
        if not self._speaking or generation != self._generation:
            return

        self._player.mark_end_of_input()
        await asyncio.to_thread(
            self._player.wait_until_drained,
            TTS_POLL_INTERVAL_MS / 1000,
            lambda: generation != self._generation,
        )

        if generation != self._generation:
            return

        self._player.stop()
        self._speaking = False
        self.speech_finished.emit()

    async def _synthesize(self, generation: int, sentence: str):
        if self._engine is None:
            return None
        return await self._engine.synthesize(
            sentence, lambda: generation != self._generation
        )

    def enqueue(self, sentence: str) -> None:
        if sentence.strip():
            self._put(sentence)

    def finish(self) -> None:
        self._put(_TURN_END)

    def speak(self, text: str) -> None:
        self.stop()
        for sentence in split_into_sentences(text):
            self.enqueue(sentence)
        self.finish()

    def stop(self) -> None:
        self._generation += 1
        self._player.stop()
        if self._speaking:
            self._speaking = False
            self.speech_finished.emit()

    def shutdown(self) -> None:
        self.stop()
        loop = self._loop
        queue = self._queue
        if loop is not None and queue is not None:
            loop.call_soon_threadsafe(queue.put_nowait, (self._generation, _THREAD_END))
        self.wait(SHUTDOWN_THREAD_TIMEOUT_MS)

    def _put(self, payload) -> None:
        loop = self._loop
        queue = self._queue
        if loop is None or queue is None:
            return
        loop.call_soon_threadsafe(queue.put_nowait, (self._generation, payload))