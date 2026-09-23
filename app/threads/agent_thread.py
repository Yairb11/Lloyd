import asyncio
import itertools
import re
import threading
from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock
from claude_agent_sdk.types import StreamEvent
from PyQt6.QtCore import QThread, pyqtSignal

from app.agent import client
from app.agent.vision import analyze_bottle_photo
from app.config import (
    AGENT_ERROR_SPEECH, AGENT_NOT_READY_SPEECH, AGENT_SCAN_NO_RESULT,
    LOG_PREFIX_ERROR, SHUTDOWN_THREAD_TIMEOUT_MS, SPEECH_SENTENCE_SPLIT_PATTERN,
)
from app.core import perf
from app.core.connectivity import is_online
from app.core.offline_lines import pick_offline_line
from app.core.qthread_support import track
from app.core.text import clean_text_for_speech
from app.threads.cancellable_worker import CancellableWorker

_agent_sequence = itertools.count(1)
_SENTENCE_END = re.compile(SPEECH_SENTENCE_SPLIT_PATTERN)


def split_completed_sentences(buffer: str) -> tuple[list[str], str]:
    parts = _SENTENCE_END.split(buffer)
    if len(parts) == 1:
        return [], buffer
    completed = [part.strip() for part in parts[:-1] if part.strip()]
    return completed, parts[-1]


class Agent(QThread):
    agent_ready = pyqtSignal()
    thinking_started = pyqtSignal()
    thinking_ended = pyqtSignal()
    speak_sentence = pyqtSignal(str)
    speech_complete = pyqtSignal()
    show_reply = pyqtSignal(str)
    show_status = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    offline_detected = pyqtSignal(str)
    recipe_ready = pyqtSignal(dict)
    animation_ready = pyqtSignal(dict)

    _popup_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        track(self, f"Agent-{next(_agent_sequence)}")

        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: ClaudeSDKClient | None = None
        self._options = None
        self._shutdown_event: asyncio.Event | None = None
        self._turn_lock: asyncio.Lock | None = None
        self._ready = threading.Event()
        self._interrupted = threading.Event()
        self._offline = False

        self._child_workers: list[CancellableWorker] = []

        self._scan_popup = None
        self._scan_result_path: str | None = None
        self._scan_error: str | None = None
        self._active_scan_path: str | None = None

        self._popup_requested.connect(self._create_scan_popup)

    def is_ready(self) -> bool:
        return self._ready.is_set() and self._client is not None

    def is_offline(self) -> bool:
        return self._offline

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()
            self._loop = None

    async def _serve(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._turn_lock = asyncio.Lock()
        self._options = client.build_options(self)

        await self._connect_or_deflect(announce_offline=True)
        self._ready.set()

        await self._shutdown_event.wait()
        await self._close_client()

    async def _connect_or_deflect(self, announce_offline: bool) -> bool:
        if not await asyncio.to_thread(is_online):
            self._offline = True
            if announce_offline:
                self.offline_detected.emit(pick_offline_line())
            return False

        try:
            await self._open_client()
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return False

        self._offline = False
        perf.mark("agent.client_ready")
        self.agent_ready.emit()
        return True

    async def _open_client(self) -> None:
        client = ClaudeSDKClient(options=self._options)
        await client.connect()
        self._client = client

    async def _close_client(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        try:
            await client.disconnect()
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: agent client disconnect failed: {exc}")

    def submit(self, message: str) -> None:
        loop = self._loop
        if loop is None or not self._ready.is_set():
            self._deliver_speech(AGENT_NOT_READY_SPEECH)
            return

        if self._client is None:
            asyncio.run_coroutine_threadsafe(self._recover_then_run(message), loop)
            return

        asyncio.run_coroutine_threadsafe(self._run_turn(message), loop)

    def _deliver_speech(self, text: str) -> None:
        self.show_reply.emit(text)
        self.speak_sentence.emit(text)
        self.speech_complete.emit()
        self.thinking_ended.emit()

    async def _recover_then_run(self, message: str) -> None:
        async with self._turn_lock:
            connected = await self._connect_or_deflect(announce_offline=False)

        if connected:
            await self._run_turn(message)
            return

        if self._offline:
            self.offline_detected.emit(pick_offline_line())
            self.thinking_ended.emit()
        else:
            self._deliver_speech(AGENT_ERROR_SPEECH)

    def reset_session(self) -> None:
        loop = self._loop
        if loop is None or not self._ready.is_set():
            return
        asyncio.run_coroutine_threadsafe(self._reset_session(), loop)

    async def _reset_session(self) -> None:
        async with self._turn_lock:
            await self._close_client()
            await self._connect_or_deflect(announce_offline=True)

    async def _run_turn(self, message: str) -> None:
        async with self._turn_lock:
            self._interrupted.clear()

            perf.mark("agent.query_sent")
            self.thinking_started.emit()

            buffer = ""
            reply = ""
            saw_delta = False
            spoke = False
            offline_line: str | None = None

            try:
                await self._client.query(message)
                async for item in self._client.receive_response():
                    if self._interrupted.is_set():
                        break

                    if isinstance(item, StreamEvent):
                        event = item.event
                        if event.get("type") != "content_block_delta":
                            continue
                        delta = event.get("delta") or {}
                        if delta.get("type") != "text_delta":
                            continue
                        if not saw_delta:
                            perf.mark("agent.first_text_delta")
                            saw_delta = True
                        buffer += delta.get("text", "")
                        completed, buffer = split_completed_sentences(buffer)
                        for sentence in completed:
                            reply = f"{reply} {sentence}".strip()
                            spoke = self._speak(sentence, spoke)

                    elif isinstance(item, AssistantMessage) and not saw_delta:
                        for block in item.content:
                            if not isinstance(block, TextBlock):
                                continue
                            buffer += block.text
                            completed, buffer = split_completed_sentences(buffer)
                            for sentence in completed:
                                reply = f"{reply} {sentence}".strip()
                                spoke = self._speak(sentence, spoke)

                    elif isinstance(item, ResultMessage):
                        tail = buffer.strip()
                        buffer = ""
                        if tail:
                            reply = f"{reply} {tail}".strip()
                            spoke = self._speak(tail, spoke)

            except Exception as exc:
                if not self._interrupted.is_set():
                    if await asyncio.to_thread(is_online):
                        self.error_occurred.emit(str(exc))
                        if not spoke:
                            reply = AGENT_ERROR_SPEECH
                            spoke = self._speak(AGENT_ERROR_SPEECH, spoke)
                    else:
                        self._offline = True
                        await self._close_client()
                        offline_line = pick_offline_line()

            finally:
                if reply:
                    self.show_reply.emit(reply)
                if offline_line is not None:
                    self.offline_detected.emit(offline_line)
                else:
                    self.speech_complete.emit()
                self.thinking_ended.emit()

    def _speak(self, sentence: str, already_spoke: bool) -> bool:
        cleaned = clean_text_for_speech(sentence)
        if not cleaned:
            return already_spoke
        if not already_spoke:
            perf.mark("agent.first_sentence")
        self.speak_sentence.emit(cleaned)
        return True

    def on_recipe(self, data: dict) -> None:
        self.recipe_ready.emit(dict(data))

    def on_animation(self, data: dict) -> None:
        self.animation_ready.emit(dict(data))

    async def on_scan(self) -> list:
        done_event = threading.Event()
        self._scan_result_path = None
        self._scan_error = None
        self._popup_requested.emit(done_event)

        await asyncio.to_thread(done_event.wait)

        path = self._scan_result_path
        self._scan_result_path = None
        if path is None:
            raise RuntimeError(self._scan_error or AGENT_SCAN_NO_RESULT)

        self._active_scan_path = path
        try:
            return await analyze_bottle_photo(path)
        finally:
            self._cleanup_scan_file()

    def interrupt(self) -> None:
        self._interrupted.set()
        self.stop_active_worker()
        loop = self._loop
        client = self._client
        if loop is None or client is None:
            return
        asyncio.run_coroutine_threadsafe(self._interrupt_client(client), loop)

    async def _interrupt_client(self, client: ClaudeSDKClient) -> None:
        try:
            await client.interrupt()
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: agent interrupt failed: {exc}")

    def shutdown(self) -> None:
        self._interrupted.set()
        self.stop_active_worker()

        if self._scan_popup is not None:
            self._scan_popup.close()
            self._scan_popup = None

        loop = self._loop
        event = self._shutdown_event
        if loop is not None and event is not None:
            loop.call_soon_threadsafe(event.set)

        for worker in self._child_workers:
            worker.wait(SHUTDOWN_THREAD_TIMEOUT_MS)
        self.wait(SHUTDOWN_THREAD_TIMEOUT_MS)

    def _spawn_child(self, worker: CancellableWorker) -> None:
        self._child_workers.append(worker)

    def stop_active_worker(self) -> None:
        for worker in self._child_workers:
            worker.request_stop()

    def _create_scan_popup(self, done_event: threading.Event) -> None:
        from app.widgets.scan_receiver_popup import ScanReceiverPopup

        try:
            self._scan_popup = ScanReceiverPopup(agent=self, done_event=done_event)
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: failed to start phone scan server: {exc}")
            self._on_scan_failure(f"Could not start the phone scan server: {exc}")
            done_event.set()
            return
        self._scan_popup.show()

    def _on_scan_failure(self, error_msg: str) -> None:
        self._scan_error = error_msg
        self.show_status.emit(f"Scanning failed: {error_msg}")

    def _cleanup_scan_file(self) -> None:
        path = self._active_scan_path
        self._active_scan_path = None
        if path is None:
            return
        try:
            from pathlib import Path

            Path(path).unlink(missing_ok=True)
        except OSError as exc:
            print(f"{LOG_PREFIX_ERROR}: could not delete uploaded scan {path}: {exc}")