import io
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf

def decode_audio_to_pcm(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    data, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="int16", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1).astype(np.int16)
    return data, sample_rate


def silence_pcm(duration_ms: int, sample_rate: int) -> np.ndarray:
    frame_count = int(sample_rate * duration_ms / 1000)
    return np.zeros(frame_count, dtype=np.int16)


class AmplitudePlayer:
    """Continuous, gapless mono PCM playback with per-block loudness reporting.

    Sentences are fed in as they're synthesized; the output stream keeps
    running (emitting silence if the buffer runs dry) instead of being
    stopped and restarted per sentence, which is what made the old
    per-sentence pygame playback sound choppy between sentences.
    """

    def __init__(
        self,
        block_frames: int,
        amplitude_peak: float,
        on_amplitude=None,
    ) -> None:
        self._block_frames = block_frames
        self._amplitude_peak = amplitude_peak
        self._on_amplitude = on_amplitude

        self._lock = threading.Lock()
        self._buffer: np.ndarray = np.empty(0, dtype=np.int16)
        self._input_finished = True
        self._drained_event = threading.Event()
        self._drained_event.set()
        self._stream: sd.OutputStream | None = None

    def start(self, sample_rate: int) -> None:
        self._teardown_stream()
        with self._lock:
            self._buffer = np.empty(0, dtype=np.int16)
            self._input_finished = False
        self._drained_event.clear()
        self._stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self._block_frames,
            callback=self._callback,
        )
        self._stream.start()

    def feed(self, pcm: np.ndarray) -> None:
        if pcm.size == 0:
            return
        with self._lock:
            self._buffer = np.concatenate([self._buffer, pcm])

    def mark_end_of_input(self) -> None:
        with self._lock:
            self._input_finished = True

    def wait_until_drained(self, poll_interval_s: float, is_cancelled) -> None:
        while not self._drained_event.is_set():
            if is_cancelled():
                return
            self._drained_event.wait(timeout=poll_interval_s)

    def stop(self) -> None:
        self._teardown_stream()
        with self._lock:
            self._buffer = np.empty(0, dtype=np.int16)
            self._input_finished = True
        self._drained_event.set()
        if self._on_amplitude is not None:
            self._on_amplitude(0.0)

    def _teardown_stream(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        self._stream = None

    def _callback(self, outdata: np.ndarray, frames: int, time_info, status) -> None:
        with self._lock:
            take = min(len(self._buffer), frames)
            chunk = self._buffer[:take]
            self._buffer = self._buffer[take:]
            drained = self._input_finished and len(self._buffer) == 0

        if take < frames:
            chunk = np.concatenate([chunk, np.zeros(frames - take, dtype=np.int16)])
        outdata[:, 0] = chunk

        if self._on_amplitude is not None:
            self._on_amplitude(self._compute_amplitude(chunk[:take]))

        if drained:
            self._drained_event.set()

    def _compute_amplitude(self, samples: np.ndarray) -> float:
        if samples.size == 0:
            return 0.0
        rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
        return max(0.0, min(1.0, rms / self._amplitude_peak))