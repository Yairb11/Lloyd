import asyncio
import io
import threading
import numpy as np

from app.audio.voices import (
    VoiceSpec, describe_voice, edge_fallback_voice, resolve_voice,
)
from app.config import (
    LOG_PREFIX_ERROR, LOG_PREFIX_VOICE, TTS_ENGINE_EDGE,
    TTS_ENGINE_PIPER, TTS_PIPER_FALLBACK_SAMPLE_RATE, TTS_WARMUP_TEXT,
)


class EdgeEngine:
    def __init__(self, voice: VoiceSpec) -> None:
        self.name = TTS_ENGINE_EDGE
        self.voice = voice

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
                sentence,
                self.voice.edge_voice,
                rate=self.voice.edge_rate,
                pitch=self.voice.edge_pitch,
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
    def __init__(self, voice: VoiceSpec) -> None:
        self.name = TTS_ENGINE_PIPER
        self.voice = voice
        self._voice = None
        self._syn_config = None
        self._lock = threading.Lock()

    def load(self) -> bool:
        try:
            from piper import PiperVoice, SynthesisConfig
        except ImportError as exc:
            print(f"{LOG_PREFIX_ERROR}: piper-tts is unavailable: {exc}")
            return False

        model_path = self.voice.model_path
        if model_path is None or not model_path.is_file():
            print(f"{LOG_PREFIX_ERROR}: piper voice not found at {model_path}")
            return False

        try:
            self._voice = PiperVoice.load(str(model_path), use_cuda=False)
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: piper voice failed to load: {exc}")
            return False

        self._syn_config = SynthesisConfig(
            speaker_id=self.voice.speaker_id,
            length_scale=self.voice.length_scale,
            noise_scale=self.voice.noise_scale,
            noise_w_scale=self.voice.noise_w_scale,
            volume=self.voice.volume,
        )
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
                for chunk in self._voice.synthesize(sentence, syn_config=self._syn_config):
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


def create_engine(voice_id: str | None = None):
    voice = resolve_voice(voice_id)

    if voice.engine == TTS_ENGINE_PIPER:
        piper = PiperEngine(voice)
        if piper.load():
            print(f"{LOG_PREFIX_VOICE}: speaking with {describe_voice(voice)}")
            return piper
        print(f"{LOG_PREFIX_ERROR}: falling back to {TTS_ENGINE_EDGE} tts")
        voice = edge_fallback_voice()

    edge = EdgeEngine(voice)
    edge.load()
    print(f"{LOG_PREFIX_VOICE}: speaking with {describe_voice(voice)}")
    return edge