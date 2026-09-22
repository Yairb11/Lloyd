import asyncio
import io
import itertools
import edge_tts
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from app.config import (
    LOG_PREFIX_ERROR,
    TTS_AMPLITUDE_NORMALIZATION_PEAK,
    TTS_AUDIO_BLOCK_FRAMES,
    TTS_INTER_SENTENCE_SILENCE_MS,
    TTS_PIPELINE_QUEUE_SIZE,
    TTS_PITCH,
    TTS_POLL_INTERVAL_MS,
    TTS_RATE,
    TTS_VOICE,
)
from app.helpers.audio_playback import AmplitudePlayer, decode_audio_to_pcm, silence_pcm
from app.helpers.text import split_into_sentences
from app.helpers import perf
from app.helpers.qthread_support import track


class LloydSpeaker(QThread):
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    amplitude_changed = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        track(self, "LloydSpeaker")
        self._text: str = ""
        self._player = AmplitudePlayer(
            block_frames=TTS_AUDIO_BLOCK_FRAMES,
            amplitude_peak=TTS_AMPLITUDE_NORMALIZATION_PEAK,
            on_amplitude=self.amplitude_changed.emit,
        )

    def speak(self, text: str) -> None:
        if self.isRunning():
            self.stop()
        self._text = text
        self.start()

    def run(self) -> None:
        if not self._text:
            return

        try:
            asyncio.run(self._speak_pipelined(self._text))
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: {exc}")
        finally:
            self._player.stop()
            self.speech_finished.emit()

    async def _speak_pipelined(self, text: str) -> None:
        sentences = split_into_sentences(text)
        if not sentences:
            return

        queue: asyncio.Queue = asyncio.Queue(maxsize=TTS_PIPELINE_QUEUE_SIZE)
        producer = asyncio.create_task(self._produce_audio(sentences, queue))

        sample_rate: int | None = None
        try:
            while True:
                item = await queue.get()
                if item is None or self.isInterruptionRequested():
                    break

                pcm, pcm_sample_rate = item
                if sample_rate is None:
                    sample_rate = pcm_sample_rate
                    perf.mark("tts.first_audio")
                    self._player.start(sample_rate)
                    self.speech_started.emit()

                self._player.feed(pcm)
                self._player.feed(silence_pcm(TTS_INTER_SENTENCE_SILENCE_MS, sample_rate))
        finally:
            producer.cancel()
            try:
                await producer
            except asyncio.CancelledError:
                pass

            self._player.mark_end_of_input()
            await asyncio.to_thread(
                self._player.wait_until_drained,
                TTS_POLL_INTERVAL_MS / 1000,
                self.isInterruptionRequested,
            )

    async def _produce_audio(self, sentences: list[str], queue: asyncio.Queue) -> None:
        try:
            for sentence in sentences:
                if self.isInterruptionRequested():
                    return
                item = await self._synthesize_sentence(sentence)
                if item is not None:
                    await queue.put(item)
        finally:
            await queue.put(None)

    async def _synthesize_sentence(self, sentence: str) -> tuple[np.ndarray, int] | None:
        communicate = edge_tts.Communicate(sentence, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if self.isInterruptionRequested():
                return None
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

        if audio_stream.tell() == 0:
            return None

        audio_stream.seek(0)
        return await asyncio.to_thread(decode_audio_to_pcm, audio_stream.read())

    def stop(self) -> None:
        self._player.stop()
        self.requestInterruption()
        self.wait()
