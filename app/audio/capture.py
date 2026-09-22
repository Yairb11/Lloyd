import math
import numpy as np

from app.config import (
    VOICE_AUDIO_DTYPE, VOICE_BLOCK_SIZE_FRAMES, VOICE_COMMAND_SILENCE_TIMEOUT_FALLBACK_S,
    VOICE_COMMAND_SILENCE_TIMEOUT_S, VOICE_PREROLL_SPEECH_PROBE_S, VOICE_SAMPLE_RATE_HZ,
    VOICE_SILENCE_RMS_THRESHOLD, VOICE_VAD_CONTEXT_SAMPLES, VOICE_VAD_ENABLED,
    VOICE_VAD_FRAME_SAMPLES, VOICE_VAD_SILENCE_THRESHOLD, VOICE_VAD_SPEECH_THRESHOLD,
    VOICE_VAD_STATE_SIZE,
)

BYTES_PER_SAMPLE: int = np.dtype(VOICE_AUDIO_DTYPE).itemsize
CHUNK_DURATION_S: float = VOICE_BLOCK_SIZE_FRAMES / VOICE_SAMPLE_RATE_HZ


def chunks_for(seconds: float) -> int:
    return max(1, math.ceil(seconds / CHUNK_DURATION_S))


def to_float32(audio: bytes) -> np.ndarray:
    return np.frombuffer(audio, dtype=VOICE_AUDIO_DTYPE).astype(np.float32) / 32768.0


_PROBE_BYTES: int = (
    chunks_for(VOICE_PREROLL_SPEECH_PROBE_S) * VOICE_BLOCK_SIZE_FRAMES * BYTES_PER_SAMPLE
)
_SILENT_FRAME: bytes = bytes(VOICE_VAD_FRAME_SAMPLES * BYTES_PER_SAMPLE)


class RmsSpeechDetector:
    silence_timeout_s: float = VOICE_COMMAND_SILENCE_TIMEOUT_FALLBACK_S

    def prime(self, audio: bytes) -> bool:
        return bool(audio) and self.is_speaking(audio[-_PROBE_BYTES:])

    def is_speaking(self, audio: bytes) -> bool:
        samples = np.frombuffer(audio, dtype=VOICE_AUDIO_DTYPE)
        if samples.size == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
        return rms >= VOICE_SILENCE_RMS_THRESHOLD


class SileroSpeechDetector:
    silence_timeout_s: float = VOICE_COMMAND_SILENCE_TIMEOUT_S

    def __init__(self, session) -> None:
        self._session = session
        self._state_h = np.zeros((1, 1, VOICE_VAD_STATE_SIZE), dtype=np.float32)
        self._state_c = np.zeros((1, 1, VOICE_VAD_STATE_SIZE), dtype=np.float32)
        self._context = np.zeros((1, VOICE_VAD_CONTEXT_SAMPLES), dtype=np.float32)
        self._speaking = False

    def prime(self, audio: bytes) -> bool:
        return self.is_speaking(audio)

    def is_speaking(self, audio: bytes) -> bool:
        samples = to_float32(audio)
        usable = samples.size - (samples.size % VOICE_VAD_FRAME_SAMPLES)
        for start in range(0, usable, VOICE_VAD_FRAME_SAMPLES):
            self._advance(samples[start:start + VOICE_VAD_FRAME_SAMPLES])
        return self._speaking

    def _advance(self, frame: np.ndarray) -> None:
        frame = frame.reshape(1, -1)
        window = np.concatenate([self._context, frame], axis=1)
        probabilities, self._state_h, self._state_c = self._session.run(
            None, {"input": window, "h": self._state_h, "c": self._state_c}
        )
        self._context = frame[:, -VOICE_VAD_CONTEXT_SAMPLES:]

        probability = float(probabilities[0][0])
        if probability >= VOICE_VAD_SPEECH_THRESHOLD:
            self._speaking = True
        elif probability < VOICE_VAD_SILENCE_THRESHOLD:
            self._speaking = False


def load_silero_session():
    from faster_whisper.vad import get_vad_model

    session = get_vad_model().session
    SileroSpeechDetector(session).is_speaking(_SILENT_FRAME)
    return session


def create_speech_detector(silero_session):
    if VOICE_VAD_ENABLED and silero_session is not None:
        return SileroSpeechDetector(silero_session)
    return RmsSpeechDetector()
