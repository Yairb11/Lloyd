import collections
import json
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

from app.audio.capture import (
    chunks_for, create_speech_detector, load_silero_session,
    to_float32,
)
from app.config import (
    VOICE_AUDIO_DTYPE, VOICE_AUDIO_QUEUE_MAX_S, VOICE_BLOCK_SIZE_FRAMES,
    VOICE_COMMAND_MAX_DURATION_S, VOICE_COMMAND_MODEL_WARMUP_SECONDS, VOICE_COMMAND_START_TIMEOUT_S,
    VOICE_LOG_TRANSCRIPT_COMPARISON, VOICE_LOG_WAKE_MATCH, VOICE_MSG_MODEL_MISSING,
    VOICE_MSG_NO_COMMAND_HEARD, VOICE_MSG_VAD_UNAVAILABLE, VOICE_MSG_WAKE_GRAMMAR_UNSUPPORTED,
    VOICE_PAUSED_POLL_INTERVAL_MS, VOICE_PREROLL_S, VOICE_QUEUE_POLL_TIMEOUT_S,
    VOICE_SAMPLE_RATE_HZ, VOICE_STOP_KEYWORD, VOICE_STOP_KEYWORD_MATCH_THRESHOLD,
    VOICE_STOP_PHRASE, VOICE_STREAM_TRANSCRIPT_ENABLED, VOICE_VAD_ENABLED,
    VOICE_VOSK_WAKE_MODEL_DIR, VOICE_WAKE_GRAMMAR_ENABLED, VOICE_WAKE_GRAMMAR_UNKNOWN_TOKEN,
    VOICE_WAKE_GREETINGS, VOICE_WAKE_KEYWORD, VOICE_WAKE_KEYWORD_MAX_WORDS,
    VOICE_WAKE_KEYWORD_VARIANTS, VOICE_WAKE_REFRACTORY_S, VOICE_WHISPER_BEAM_SIZE,
    VOICE_WHISPER_BEST_OF, VOICE_WHISPER_COMPUTE_TYPE, VOICE_WHISPER_CONDITION_ON_PREVIOUS_TEXT,
    VOICE_WHISPER_CPU_THREADS, VOICE_WHISPER_DEVICE, VOICE_WHISPER_DOWNLOAD_ROOT,
    VOICE_WHISPER_LANGUAGE, VOICE_WHISPER_MODEL_SIZE, VOICE_WHISPER_TEMPERATURE,
    VOICE_WHISPER_VAD_FILTER, VOICE_WHISPER_WITHOUT_TIMESTAMPS,
)
from app.core import perf
from app.core.qthread_support import track
from app.core.text import is_wake_greeting, is_wake_keyword


def _build_wake_grammar() -> str:
    phrases = {VOICE_WAKE_KEYWORD, VOICE_STOP_PHRASE}
    for variant in VOICE_WAKE_KEYWORD_VARIANTS:
        phrases.add(variant)
        for greeting in VOICE_WAKE_GREETINGS:
            phrases.add(f"{greeting} {variant}")
    return json.dumps(sorted(phrases) + [VOICE_WAKE_GRAMMAR_UNKNOWN_TOKEN])


def _is_stop_keyword(word: str) -> bool:
    return fuzz.ratio(VOICE_STOP_KEYWORD, word) >= VOICE_STOP_KEYWORD_MATCH_THRESHOLD


def _decode_command(model: WhisperModel, audio: np.ndarray, vad_filter: bool) -> str:
    segments, _ = model.transcribe(
        audio,
        language=VOICE_WHISPER_LANGUAGE,
        beam_size=VOICE_WHISPER_BEAM_SIZE,
        best_of=VOICE_WHISPER_BEST_OF,
        temperature=VOICE_WHISPER_TEMPERATURE,
        condition_on_previous_text=VOICE_WHISPER_CONDITION_ON_PREVIOUS_TEXT,
        without_timestamps=VOICE_WHISPER_WITHOUT_TIMESTAMPS,
        vad_filter=vad_filter,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


_WAKE_GRAMMAR: str = _build_wake_grammar()
_AUDIO_QUEUE_MAX_CHUNKS: int = chunks_for(VOICE_AUDIO_QUEUE_MAX_S)
_PREROLL_MAX_CHUNKS: int = chunks_for(VOICE_PREROLL_S)


class VoiceListener(QThread):
    wake_detected = pyqtSignal()
    wake_word_detected = pyqtSignal(str)
    stop_word_detected = pyqtSignal()
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    transcribing_started = pyqtSignal()
    transcribing_ended = pyqtSignal()
    error_occurred = pyqtSignal(str)
    listener_ready = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        track(self, "VoiceListener")
        self._paused = threading.Event()
        self._suspended = threading.Event()

        self._audio_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=_AUDIO_QUEUE_MAX_CHUNKS)
        self._preroll: "collections.deque[bytes]" = collections.deque(maxlen=_PREROLL_MAX_CHUNKS)
        self._stream: sd.RawInputStream | None = None

        self._grammar_supported: bool = VOICE_WAKE_GRAMMAR_ENABLED
        self._wake_model: vosk.Model | None = None
        self._vad_session: object | None = None
        self._last_wake_at: float = 0.0
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
            self._wake_model = vosk.Model(VOICE_VOSK_WAKE_MODEL_DIR)
        except Exception as exc:
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} ({exc})")
            return

        self._vad_session = self._load_vad_session()
        self.listener_ready.emit()

        try:
            self._run_loop()
        finally:
            self._close_stream()

    def _report_input_device(self) -> None:
        try:
            device_info = sd.query_devices(kind="input")
            self.error_occurred.emit(f"Using input device: {device_info.get('name')!r}")
        except Exception as exc:
            self.error_occurred.emit(f"Could not query input device: {exc}")

    def _load_vad_session(self) -> object | None:
        if not VOICE_VAD_ENABLED:
            return None
        try:
            return load_silero_session()
        except Exception as exc:
            self.error_occurred.emit(f"{VOICE_MSG_VAD_UNAVAILABLE} ({exc})")
            return None

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
                _decode_command(model, silence, False)
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

    def _run_loop(self) -> None:
        wake_rec = self._new_wake_recognizer()

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
                    wake_rec = self._new_wake_recognizer()
                continue

            if not self._matches_wake_word(text):
                continue

            if time.monotonic() - self._last_wake_at < VOICE_WAKE_REFRACTORY_S:
                continue

            self._last_wake_at = time.monotonic()
            self.error_occurred.emit(f"{VOICE_LOG_WAKE_MATCH} {text!r}")

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

            wake_rec = self._new_wake_recognizer()
            self._last_wake_at = time.monotonic()

    def _new_wake_recognizer(self) -> vosk.KaldiRecognizer:
        if self._grammar_supported:
            try:
                rec = vosk.KaldiRecognizer(self._wake_model, VOICE_SAMPLE_RATE_HZ, _WAKE_GRAMMAR)
                rec.SetWords(False)
                return rec
            except Exception as exc:
                self._grammar_supported = False
                self.error_occurred.emit(f"{VOICE_MSG_WAKE_GRAMMAR_UNSUPPORTED} ({exc})")

        rec = vosk.KaldiRecognizer(self._wake_model, VOICE_SAMPLE_RATE_HZ)
        rec.SetWords(False)
        return rec

    def _matches_wake_word(self, text: str) -> bool:
        words = text.strip().lower().split()
        if not words:
            return False

        if not is_wake_keyword(words[-1]):
            return False

        if len(words) >= 2 and is_wake_greeting(words[-2]):
            return True

        return len(words) <= VOICE_WAKE_KEYWORD_MAX_WORDS

    def _matches_stop_word(self, text: str) -> bool:
        words = text.strip().lower().split()
        if len(words) < 2:
            return False

        return is_wake_keyword(words[-2]) and _is_stop_keyword(words[-1])

    def _capture_command(self) -> str:
        preroll = self._take_preroll()
        audio_buffer = bytearray(preroll)

        detector = create_speech_detector(self._vad_session)
        stream_rec = self._new_stream_recognizer()
        if stream_rec is not None and preroll:
            stream_rec.AcceptWaveform(preroll)

        started_talking = detector.prime(preroll)

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
            if stream_rec is not None:
                stream_rec.AcceptWaveform(chunk)

            if detector.is_speaking(chunk):
                started_talking = True
                silence_started_at = None
            elif started_talking:
                if silence_started_at is None:
                    silence_started_at = time.monotonic()
                elif time.monotonic() - silence_started_at >= detector.silence_timeout_s:
                    break

        if not audio_buffer:
            return ""

        perf.mark("stt.capture_end")

        fast_text = self._stream_transcript(stream_rec)
        if fast_text:
            perf.mark("stt.vosk_instant")

        command_model = self._await_command_model()
        if command_model is None:
            self.error_occurred.emit(
                f"{VOICE_MSG_MODEL_MISSING} ({self._command_model_result.get('error')})"
            )
            return fast_text

        self.transcribing_started.emit()
        try:
            refined = _decode_command(
                command_model, to_float32(bytes(audio_buffer)), VOICE_WHISPER_VAD_FILTER
            )
            perf.mark("stt.decoded")
            self._log_transcript_comparison(fast_text, refined)
            return refined or fast_text
        finally:
            self.transcribing_ended.emit()

    def _new_stream_recognizer(self) -> vosk.KaldiRecognizer | None:
        if not VOICE_STREAM_TRANSCRIPT_ENABLED or self._wake_model is None:
            return None
        try:
            rec = vosk.KaldiRecognizer(self._wake_model, VOICE_SAMPLE_RATE_HZ)
            rec.SetWords(False)
            return rec
        except Exception as exc:
            self.error_occurred.emit(f"Streaming recognizer unavailable: {exc}")
            return None

    def _stream_transcript(self, stream_rec: vosk.KaldiRecognizer | None) -> str:
        if stream_rec is None:
            return ""
        try:
            return json.loads(stream_rec.FinalResult()).get("text", "").strip()
        except Exception as exc:
            self.error_occurred.emit(f"Streaming recognizer error: {exc}")
            return ""

    def _log_transcript_comparison(self, fast_text: str, refined: str) -> None:
        if not VOICE_STREAM_TRANSCRIPT_ENABLED:
            return
        agreement = fuzz.ratio(fast_text.lower(), refined.lower())
        self.error_occurred.emit(
            f"{VOICE_LOG_TRANSCRIPT_COMPARISON} vosk={fast_text!r} "
            f"whisper={refined!r} agreement={agreement}"
        )

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
