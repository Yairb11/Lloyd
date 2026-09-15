import json
import os
import queue
import threading
import time
import numpy as np
import sounddevice as sd
import vosk
from PyQt6.QtCore import QThread, pyqtSignal
from thefuzz import fuzz

from app.config import (
    VOICE_AUDIO_DTYPE,
    VOICE_BLOCK_SIZE_FRAMES,
    VOICE_COMMAND_MAX_DURATION_S,
    VOICE_COMMAND_SILENCE_TIMEOUT_S,
    VOICE_COMMAND_START_TIMEOUT_S,
    VOICE_MSG_MODEL_MISSING,
    VOICE_MSG_NO_COMMAND_HEARD,
    VOICE_PAUSED_POLL_INTERVAL_MS,
    VOICE_QUEUE_POLL_TIMEOUT_S,
    VOICE_SAMPLE_RATE_HZ,
    VOICE_SILENCE_RMS_THRESHOLD,
    VOICE_VOSK_COMMAND_MODEL_DIR,
    VOICE_VOSK_WAKE_MODEL_DIR,
    VOICE_WAKE_MATCH_THRESHOLD,
    VOICE_WAKE_WORDS,
)

class VoiceListener(QThread):

    wake_word_detected = pyqtSignal(str)
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    error_occurred = pyqtSignal(str)

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
        if not os.path.isdir(VOICE_VOSK_COMMAND_MODEL_DIR):
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} (command model: {VOICE_VOSK_COMMAND_MODEL_DIR})")
            return

        vosk.SetLogLevel(-1)
        try:
            wake_model = vosk.Model(VOICE_VOSK_WAKE_MODEL_DIR)
            command_model = vosk.Model(VOICE_VOSK_COMMAND_MODEL_DIR)
        except Exception as exc:
            self.error_occurred.emit(f"{VOICE_MSG_MODEL_MISSING} ({exc})")
            return

        try:
            self._run_loop(wake_model, command_model)
        finally:
            self._close_stream()

    def _run_loop(self, wake_model: vosk.Model, command_model: vosk.Model) -> None:
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

            if self._suspended.is_set():
                continue

            try:
                if wake_rec.AcceptWaveform(chunk):
                    text = json.loads(wake_rec.Result()).get("text", "")
                else:
                    text = json.loads(wake_rec.PartialResult()).get("partial", "")
            except Exception as exc:
                self.error_occurred.emit(f"Wake-word engine error: {exc}")
                continue

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

        for phrase in VOICE_WAKE_WORDS:
            if len(normalized.split()) < len(phrase.split()):
                continue
            if fuzz.partial_ratio(phrase, normalized) >= VOICE_WAKE_MATCH_THRESHOLD:
                return True
        return False

    def _capture_command(self, command_model: vosk.Model) -> str:
        recognizer = vosk.KaldiRecognizer(command_model, VOICE_SAMPLE_RATE_HZ)
        recognizer.SetWords(False)

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

            recognizer.AcceptWaveform(chunk)

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

        try:
            result = json.loads(recognizer.FinalResult())
        except json.JSONDecodeError:
            return ""
        return result.get("text", "").strip()

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