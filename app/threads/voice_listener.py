import collections
import json
import math
import os
import queue
import threading
import time
import numpy as np
import sounddevice as sd
import vosk
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal
from thefuzz import fuzz

from app.config import (
    VOICE_AUDIO_DTYPE,
    VOICE_AUDIO_QUEUE_MAX_S,
    VOICE_BLOCK_SIZE_FRAMES,
    VOICE_COMMAND_MAX_DURATION_S,
    VOICE_COMMAND_MODEL_WARMUP_SECONDS,
    VOICE_COMMAND_SILENCE_TIMEOUT_S,
    VOICE_COMMAND_START_TIMEOUT_S,
    VOICE_MSG_MODEL_MISSING,
    VOICE_MSG_NO_COMMAND_HEARD,
    VOICE_MSG_WAKE_GRAMMAR_UNSUPPORTED,
    VOICE_PAUSED_POLL_INTERVAL_MS,
    VOICE_PREROLL_S,
    VOICE_PREROLL_SPEECH_PROBE_S,
    VOICE_QUEUE_POLL_TIMEOUT_S,
    VOICE_SAMPLE_RATE_HZ,
    VOICE_SILENCE_RMS_THRESHOLD,
    VOICE_STOP_PHRASE,
    VOICE_STOP_PHRASE_MATCH_THRESHOLD,
    VOICE_VOSK_WAKE_MODEL_DIR,
    VOICE_WAKE_GRAMMAR_ENABLED,
    VOICE_WAKE_GRAMMAR_UNKNOWN_TOKEN,
    VOICE_WAKE_KEYWORD,
    VOICE_WAKE_KEYWORD_MATCH_THRESHOLD,
    VOICE_WAKE_KEYWORD_MAX_WORDS,
    VOICE_WAKE_PHRASE_MATCH_THRESHOLD,
    VOICE_WAKE_WORDS,
    VOICE_WHISPER_COMPUTE_TYPE,
    VOICE_WHISPER_CPU_THREADS,
    VOICE_WHISPER_DEVICE,
    VOICE_WHISPER_DOWNLOAD_ROOT,
    VOICE_WHISPER_LANGUAGE,
    VOICE_WHISPER_MODEL_SIZE,
)
from app.helpers import perf

_BYTES_PER_SAMPLE: int = np.dtype(VOICE_AUDIO_DTYPE).itemsize
_CHUNK_DURATION_S: float = VOICE_BLOCK_SIZE_FRAMES / VOICE_SAMPLE_RATE_HZ


def _chunks_for(seconds: float) -> int:
    return max(1, math.ceil(seconds / _CHUNK_DURATION_S))


def _build_wake_grammar() -> str:
    phrases = {phrase.strip().lower() for phrase in VOICE_WAKE_WORDS}
    phrases.add(VOICE_WAKE_KEYWORD)
    phrases.add(VOICE_STOP_PHRASE)
    return json.dumps(sorted(phrases) + [VOICE_WAKE_GRAMMAR_UNKNOWN_TOKEN])


def _is_speech(audio: bytes) -> bool:
    samples = np.frombuffer(audio, dtype=VOICE_AUDIO_DTYPE)
    if samples.size == 0:
        return False
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
    return rms >= VOICE_SILENCE_RMS_THRESHOLD


def _ends_in_speech(audio: bytes) -> bool:
    return bool(audio) and _is_speech(audio[-_PREROLL_PROBE_BYTES:])


_WAKE_GRAMMAR: str = _build_wake_grammar()
_AUDIO_QUEUE_MAX_CHUNKS: int = _chunks_for(VOICE_AUDIO_QUEUE_MAX_S)
_PREROLL_MAX_CHUNKS: int = _chunks_for(VOICE_PREROLL_S)
_PREROLL_PROBE_BYTES: int = (
    _chunks_for(VOICE_PREROLL_SPEECH_PROBE_S) * VOICE_BLOCK_SIZE_FRAMES * _BYTES_PER_SAMPLE
)


class VoiceListener(QThread):
    wake_detected = pyqtSignal()
    wake_word_detected = pyqtSignal(str)
    stop_word_detected = pyqtSignal()
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    transcribing_started = pyqtSignal()
    transcribing_ended = pyqtSignal()
    error_occurred = pyqtSignal(str)
    partial_transcript = pyqtSignal(str)
    listener_ready = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._paused = threading.Event()
        self._suspended = threading.Event()

        self._audio_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=_AUDIO_QUEUE_MAX_CHUNKS)
        self._preroll: "collections.deque[bytes]" = collections.deque(maxlen=_PREROLL_MAX_CHUNKS)
        self._stream: sd.RawInputStream | None = None

        self._grammar_supported: bool = VOICE_WAKE_GRAMMAR_ENABLED
        self._command_model_thread: threading.Thread | None = None
        self._command_model_result: dict[str, object] = {}

    def run(self) -> None:
        if not os.path.isdir(VOICE_VOSK_WAKE_MODEL_DIR):
            self.error_occurred.emit(
                f"{VOICE_MSG_MODEL_MISSING} (wake model: {VOICE_VOSK_WAKE_MODEL_DIR})"
            )
            return

        vosk.SetLogLevel(-1)

        try:
            self._ensure_stream_open()
        except Exception as exc:
            self.error_occurred.emit(f"Microphone error: {exc}")
            return

        self._report_input_device()
        self._start_command_model_loader()

        try:
            wake_model = vosk.Model(VOICE_VOSK_WAKE_MODEL_DIR)
        except Exception as exc:
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} ({exc})")
            return

        self.listener_ready.emit()

        try:
            self._run_loop(wake_model)
        finally:
            self._close_stream()

    def _report_input_device(self) -> None:
        try:
            device_info = sd.query_devices(kind="input")
            self.error_occurred.emit(f"Using input device: {device_info.get('name')!r}")
        except Exception as exc:
            self.error_occurred.emit(f"Could not query input device: {exc}")

    def _start_command_model_loader(self) -> None:
        def load_and_warm() -> None:
            try:
                model = WhisperModel(
                    VOICE_WHISPER_MODEL_SIZE,
                    device=VOICE_WHISPER_DEVICE,
                    compute_type=VOICE_WHISPER_COMPUTE_TYPE,
                    cpu_threads=VOICE_WHISPER_CPU_THREADS,
                    download_root=VOICE_WHISPER_DOWNLOAD_ROOT,
                )
                silence = np.zeros(
                    int(VOICE_SAMPLE_RATE_HZ * VOICE_COMMAND_MODEL_WARMUP_SECONDS),
                    dtype=np.float32,
                )
                segments, _ = model.transcribe(silence, language=VOICE_WHISPER_LANGUAGE)
                list(segments)
                self._command_model_result["model"] = model
            except Exception as exc:
                self._command_model_result["error"] = exc

        self._command_model_thread = threading.Thread(
            target=load_and_warm, name="whisper-loader", daemon=True
        )
        self._command_model_thread.start()

    def _await_command_model(self) -> WhisperModel | None:
        thread = self._command_model_thread
        if thread is not None and thread.is_alive():
            thread.join()
            perf.mark("stt.model_wait")
        return self._command_model_result.get("model")

    def _run_loop(self, wake_model: vosk.Model) -> None:
        wake_rec = self._new_wake_recognizer(wake_model)

        while not self.isInterruptionRequested():
            if self._paused.is_set():
                self._close_stream()
                self.msleep(VOICE_PAUSED_POLL_INTERVAL_MS)
                continue

            self._ensure_stream_open()

            try:
                chunk = self._audio_queue.get(timeout=VOICE_QUEUE_POLL_TIMEOUT_S)
            except queue.Empty:
                continue

            if not self._suspended.is_set():
                self._preroll.append(chunk)

            try:
                if wake_rec.AcceptWaveform(chunk):
                    text = json.loads(wake_rec.Result()).get("text", "")
                else:
                    text = json.loads(wake_rec.PartialResult()).get("partial", "")
            except Exception as exc:
                self.error_occurred.emit(f"Wake-word engine error: {exc}")
                continue

            if self._suspended.is_set():
                if self._matches_stop_word(text):
                    self.stop_word_detected.emit()
                    wake_rec = self._new_wake_recognizer(wake_model)
                continue

            if text.strip():
                self.partial_transcript.emit(text)

            if not self._matches_wake_word(text):
                continue

            perf.start("wake")
            self.wake_detected.emit()
            perf.mark("wake.matched")

            self.speech_started.emit()
            try:
                command_text = self._capture_command()
            except Exception as exc:
                command_text = ""
                self.error_occurred.emit(f"Speech recognition error: {exc}")
            self.speech_ended.emit()

            if command_text:
                self.wake_word_detected.emit(command_text)
            else:
                self.error_occurred.emit(VOICE_MSG_NO_COMMAND_HEARD)

            wake_rec = self._new_wake_recognizer(wake_model)

    def _new_wake_recognizer(self, wake_model: vosk.Model) -> vosk.KaldiRecognizer:
        if self._grammar_supported:
            try:
                rec = vosk.KaldiRecognizer(wake_model, VOICE_SAMPLE_RATE_HZ, _WAKE_GRAMMAR)
                rec.SetWords(False)
                return rec
            except Exception as exc:
                self._grammar_supported = False
                self.error_occurred.emit(f"{VOICE_MSG_WAKE_GRAMMAR_UNSUPPORTED} ({exc})")

        rec = vosk.KaldiRecognizer(wake_model, VOICE_SAMPLE_RATE_HZ)
        rec.SetWords(False)
        return rec

    def _matches_wake_word(self, text: str) -> bool:
        normalized = text.strip().lower()
        if not normalized:
            return False

        words = normalized.split()

        for phrase in VOICE_WAKE_WORDS:
            if len(words) < len(phrase.split()):
                continue
            if fuzz.partial_ratio(phrase, normalized) >= VOICE_WAKE_PHRASE_MATCH_THRESHOLD:
                return True

        if 0 < len(words) <= VOICE_WAKE_KEYWORD_MAX_WORDS:
            for word in words:
                if fuzz.ratio(VOICE_WAKE_KEYWORD, word) >= VOICE_WAKE_KEYWORD_MATCH_THRESHOLD:
                    return True

        return False

    def _matches_stop_word(self, text: str) -> bool:
        normalized = text.strip().lower()
        if not normalized:
            return False

        if len(normalized.split()) < len(VOICE_STOP_PHRASE.split()):
            return False

        return fuzz.partial_ratio(VOICE_STOP_PHRASE, normalized) >= VOICE_STOP_PHRASE_MATCH_THRESHOLD

    def _capture_command(self) -> str:
        preroll = self._take_preroll()
        audio_buffer = bytearray(preroll)
        started_talking = _ends_in_speech(preroll)

        start_time = time.monotonic()
        silence_started_at: float | None = None

        while True:
            if self.isInterruptionRequested() or self._paused.is_set():
                break

            elapsed_s = time.monotonic() - start_time
            if not started_talking and elapsed_s >= VOICE_COMMAND_START_TIMEOUT_S:
                break
            if elapsed_s >= VOICE_COMMAND_MAX_DURATION_S:
                break

            try:
                chunk = self._audio_queue.get(timeout=VOICE_QUEUE_POLL_TIMEOUT_S)
            except queue.Empty:
                continue

            audio_buffer.extend(chunk)

            if _is_speech(chunk):
                started_talking = True
                silence_started_at = None
            elif started_talking:
                if silence_started_at is None:
                    silence_started_at = time.monotonic()
                elif time.monotonic() - silence_started_at >= VOICE_COMMAND_SILENCE_TIMEOUT_S:
                    break

        if not audio_buffer:
            return ""

        perf.mark("stt.capture_end")

        command_model = self._await_command_model()
        if command_model is None:
            self.error_occurred.emit(
                f"{VOICE_MSG_MODEL_MISSING} ({self._command_model_result.get('error')})"
            )
            return ""

        audio_np = np.frombuffer(bytes(audio_buffer), dtype=np.int16).astype(np.float32) / 32768.0
        self.transcribing_started.emit()
        try:
            segments, _ = command_model.transcribe(audio_np, language=VOICE_WHISPER_LANGUAGE)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            perf.mark("stt.decoded")
            return text
        finally:
            self.transcribing_ended.emit()

    def _take_preroll(self) -> bytes:
        chunks = list(self._preroll)
        self._preroll.clear()
        return b"".join(chunks)

    def _ensure_stream_open(self) -> None:
        if self._stream is not None:
            return
        self._stream = sd.RawInputStream(
            samplerate=VOICE_SAMPLE_RATE_HZ,
            blocksize=VOICE_BLOCK_SIZE_FRAMES,
            dtype=VOICE_AUDIO_DTYPE,
            channels=1,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _close_stream(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._drain_queue()

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        chunk = bytes(indata)
        if self._try_enqueue(chunk):
            return
        self._discard_oldest_chunk()
        self._try_enqueue(chunk)

    def _try_enqueue(self, chunk: bytes) -> bool:
        try:
            self._audio_queue.put_nowait(chunk)
            return True
        except queue.Full:
            return False

    def _discard_oldest_chunk(self) -> None:
        try:
            self._audio_queue.get_nowait()
        except queue.Empty:
            pass

    def _drain_queue(self) -> None:
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        self._preroll.clear()

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def suspend(self) -> None:
        self._suspended.set()
        self._preroll.clear()

    def unsuspend(self) -> None:
        self._suspended.clear()

    def stop(self) -> None:
        self.requestInterruption()
        self.wait()
