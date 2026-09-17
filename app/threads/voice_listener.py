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

from app.config import (
    VOICE_AUDIO_DTYPE,
    VOICE_BLOCK_SIZE_FRAMES,
    VOICE_COMMAND_MAX_DURATION_S,
    VOICE_COMMAND_MODEL_WARMUP_SECONDS,
    VOICE_COMMAND_SILENCE_TIMEOUT_S,
    VOICE_COMMAND_START_TIMEOUT_S,
    VOICE_MSG_MODEL_MISSING,
    VOICE_MSG_NO_COMMAND_HEARD,
    VOICE_PAUSED_POLL_INTERVAL_MS,
    VOICE_QUEUE_POLL_TIMEOUT_S,
    VOICE_SAMPLE_RATE_HZ,
    VOICE_SILENCE_RMS_THRESHOLD,
    VOICE_STOP_PHRASE,
    VOICE_STOP_PHRASE_MATCH_THRESHOLD,
    VOICE_STOP_KEYWORD_MAX_WORDS,
    VOICE_VOSK_WAKE_MODEL_DIR,
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

class VoiceListener(QThread):
    wake_word_detected = pyqtSignal(str)
    stop_word_detected = pyqtSignal()
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    error_occurred = pyqtSignal(str)
    partial_transcript = pyqtSignal(str)
    listener_ready = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._paused = threading.Event()
        self._suspended = threading.Event()

        self._audio_queue: "queue.Queue[bytes]" = queue.Queue()
        self._stream: sd.RawInputStream | None = None

    def run(self) -> None:
        if not os.path.isdir(VOICE_VOSK_WAKE_MODEL_DIR):
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} (wake model: {VOICE_VOSK_WAKE_MODEL_DIR})")
            return

        vosk.SetLogLevel(-1)

        # Open the microphone immediately so audio starts buffering right
        # away, before either model has loaded.
        try:
            self._ensure_stream_open()
        except Exception as exc:
            self.error_occurred.emit(f"Microphone error: {exc}")
            return

        try:
            device_info = sd.query_devices(kind="input")
            self.error_occurred.emit(f"Using input device: {device_info.get('name')!r}")
        except Exception as exc:
            self.error_occurred.emit(f"Could not query input device: {exc}")

        # Load both models in parallel to minimize total setup time, but
        # do NOT start listening for the wake word until both are fully
        # ready - including paying the command model's one-time first-
        # decode warm-up cost here, not on the user's first real command.
        wake_result: dict[str, object] = {}
        command_result: dict[str, object] = {}

        def _load_wake_model() -> None:
            try:
                wake_result["model"] = vosk.Model(VOICE_VOSK_WAKE_MODEL_DIR)
            except Exception as exc:
                wake_result["error"] = exc

        def _load_and_warm_command_model() -> None:
            try:
                model = WhisperModel(
                    VOICE_WHISPER_MODEL_SIZE,
                    device=VOICE_WHISPER_DEVICE,
                    compute_type=VOICE_WHISPER_COMPUTE_TYPE,
                    cpu_threads=VOICE_WHISPER_CPU_THREADS,
                    download_root=VOICE_WHISPER_DOWNLOAD_ROOT,
                )
                silence = np.zeros(
                    int(VOICE_SAMPLE_RATE_HZ * VOICE_COMMAND_MODEL_WARMUP_SECONDS), dtype=np.float32
                )
                segments, _ = model.transcribe(silence, language=VOICE_WHISPER_LANGUAGE)
                list(segments)  # force decode now, not on first real command
                command_result["model"] = model
            except Exception as exc:
                command_result["error"] = exc

        wake_thread = threading.Thread(target=_load_wake_model, daemon=True)
        command_thread = threading.Thread(target=_load_and_warm_command_model, daemon=True)
        wake_thread.start()
        command_thread.start()
        wake_thread.join()
        command_thread.join()

        wake_model = wake_result.get("model")
        if wake_model is None:
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} ({wake_result.get('error')})")
            return

        command_model = command_result.get("model")
        if command_model is None:
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} ({command_result.get('error')})")
            return

        self.listener_ready.emit()

        try:
            self._run_loop(wake_model, command_model)
        finally:
            self._close_stream()

    def _run_loop(self, wake_model: vosk.Model, command_model: WhisperModel) -> None:
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

            try:
                if wake_rec.AcceptWaveform(chunk):
                    text = json.loads(wake_rec.Result()).get("text", "")
                else:
                    text = json.loads(wake_rec.PartialResult()).get("partial", "")
            except Exception as exc:
                self.error_occurred.emit(f"Wake-word engine error: {exc}")
                continue

            # While suspended (Lloyd is thinking/speaking/rendering), don't
            # run full wake-word detection - just listen for the bare word
            # "stop" so the user can barge in without saying "hey lloyd"
            # first. This is the only audio processing that happens while
            # suspended.
            if self._suspended.is_set():
                if self._matches_stop_word(text):
                    self.stop_word_detected.emit()
                    wake_rec = self._new_wake_recognizer(wake_model)
                continue

            if text.strip():
                self.partial_transcript.emit(text)

            if not self._matches_wake_word(text):
                continue

            self._drain_queue()

            self.speech_started.emit()
            try:
                command_text = self._capture_command(command_model)
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
        rec = vosk.KaldiRecognizer(wake_model, VOICE_SAMPLE_RATE_HZ)
        rec.SetWords(False)
        return rec

    def _matches_wake_word(self, text: str) -> bool:
        normalized = text.strip().lower()
        if not normalized:
            return False

        words = normalized.split()

        # Full-phrase match against every configured wake phrase, including
        # known phonetic-mishear variants (e.g. "hey floyd", "hey boyd").
        for phrase in VOICE_WAKE_WORDS:
            if len(words) < len(phrase.split()):
                continue
            if fuzz.partial_ratio(phrase, normalized) >= VOICE_WAKE_PHRASE_MATCH_THRESHOLD:
                return True

        # Bare-keyword fallback: the small wake model frequently drops or
        # clips the short, low-energy "hey" and only ever transcribes
        # "lloyd" (optionally preceded by a filler word). A phrase-level
        # check can never see these, so fuzzy-match each word of a short
        # utterance directly against the keyword using whole-string ratio
        # (not partial_ratio, which over-matches short strings — e.g. bare
        # "hey" scores 100 against "hey lloyd" via partial_ratio) at a
        # stricter, separately tuned bar.
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

    def _capture_command(self, command_model: WhisperModel) -> str:
        audio_buffer = bytearray()

        start_time = time.monotonic()
        started_talking = False
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

            samples = np.frombuffer(chunk, dtype=np.int16)
            rms = (
                float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
                if samples.size
                else 0.0
            )

            if rms >= VOICE_SILENCE_RMS_THRESHOLD:
                started_talking = True
                silence_started_at = None
            elif started_talking:
                if silence_started_at is None:
                    silence_started_at = time.monotonic()
                elif time.monotonic() - silence_started_at >= VOICE_COMMAND_SILENCE_TIMEOUT_S:
                    break

        if not audio_buffer:
            return ""

        audio_np = np.frombuffer(bytes(audio_buffer), dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = command_model.transcribe(audio_np, language=VOICE_WHISPER_LANGUAGE)
        return " ".join(segment.text.strip() for segment in segments).strip()

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
        self._audio_queue.put(bytes(indata))

    def _drain_queue(self) -> None:
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def suspend(self) -> None:
        self._suspended.set()

    def unsuspend(self) -> None:
        self._suspended.clear()

    def stop(self) -> None:
        self.requestInterruption()
        self.wait()
