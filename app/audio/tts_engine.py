import asyncio
import io
import threading

import numpy as np

from app.config import (
    LOG_PREFIX_ERROR, TTS_ENGINE, TTS_ENGINE_EDGE,
    TTS_ENGINE_PIPER, TTS_PIPER_FALLBACK_SAMPLE_RATE, TTS_PIPER_MODEL_PATH,
    TTS_PITCH, TTS_RATE, TTS_VOICE,
    TTS_WARMUP_TEXT,
)
from app.core.paths import PROJECT_ROOT


class EdgeEngine:
    def __init__(self) -> None:
        self.name = TTS_ENGINE_EDGE

    def load(self) -> bool:
        return True

    async def warmup(self) -> None:
        await self.synthesize(TTS_WARMUP_TEXT, _never_cancelled)

    async def synthesize(self, sentence, is_cancelled):
        import edge_tts

        from app.audio.playback import decode_audio_to_pcm

        stream = io.BytesIO()
        try:
            communicate = edge_tts.Communicate(
                sentence, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH
            )
            async for chunk in communicate.stream():
                if is_cancelled():
                    return None
                if chunk["type"] == "audio":
                    stream.write(chunk["data"])
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: edge tts failed: {exc}")
            return None

        if stream.tell() == 0:
            return None

        stream.seek(0)
        return await asyncio.to_thread(decode_audio_to_pcm, stream.read())


class PiperEngine:
    def __init__(self) -> None:
        self.name = TTS_ENGINE_PIPER
        self._voice = None
        self._lock = threading.Lock()

    def load(self) -> bool:
        try:
            from piper import PiperVoice
        except ImportError as exc:
            print(f"{LOG_PREFIX_ERROR}: piper-tts is not installed: {exc}")
            return False

        model_path = PROJECT_ROOT / TTS_PIPER_MODEL_PATH
        if not model_path.is_file():
            print(f"{LOG_PREFIX_ERROR}: piper voice not found at {model_path}")
            return False

        try:
            self._voice = PiperVoice.load(str(model_path), use_cuda=False)
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: piper voice failed to load: {exc}")
            return False
        return True

    async def warmup(self) -> None:
        await self.synthesize(TTS_WARMUP_TEXT, _never_cancelled)

    async def synthesize(self, sentence, is_cancelled):
        if is_cancelled():
            return None
        return await asyncio.to_thread(self._render, sentence)

    def _render(self, sentence):
        buffer = bytearray()
        sample_rate = TTS_PIPER_FALLBACK_SAMPLE_RATE
        try:
            with self._lock:
                for chunk in self._voice.synthesize(sentence):
                    buffer.extend(chunk.audio_int16_bytes)
                    sample_rate = chunk.sample_rate
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: piper synthesis failed: {exc}")
            return None

        if not buffer:
            return None
        return np.frombuffer(bytes(buffer), dtype=np.int16), sample_rate


def _never_cancelled() -> bool:
    return False


def create_engine():
    if TTS_ENGINE == TTS_ENGINE_PIPER:
        piper = PiperEngine()
        if piper.load():
            return piper
        print(f"{LOG_PREFIX_ERROR}: falling back to {TTS_ENGINE_EDGE} tts")

    edge = EdgeEngine()
    edge.load()
    return edge
