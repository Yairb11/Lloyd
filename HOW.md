# Lloyd

====================================================================

## Features

1. Application Startup
2. Central Configuration
3. Environment Settings (.env)
4. Main Window and Splitter Layout
5. Dark Theme Stylesheet
6. Custom Scrollbars
7. Dark Title Bar
8. Window Placement Memory
9. Saved Splitter and Volume
10. Fullscreen and Keyboard Shortcuts
11. Animated Status Sphere
12. Chat Panel
13. Chat Bubbles
14. Typing Indicator
15. Send / Stop Button
16. Mic Toggle Button
17. Mute Button and Volume Popup
18. Floating Resizable Panels
19. Wake Word Detection
20. Stop Word Detection
21. Command Recording and End-of-Speech Detection
22. Speech-to-Text Transcription
23. Voice Clear-Chat Command
24. Claude Connection
25. System Prompt and Persona
26. Custom Agent Tools
27. Tool Argument Validation (JSON Schema)
28. Prompt Behaviours
29. Streaming Replies Spoken Sentence by Sentence
30. Text Cleanup for Speech
31. Text-to-Speech Engines
32. Swappable Voice Catalog
33. Audio Playback with Live Amplitude
34. Volume Curve
35. Interrupt Everything
36. Conversation Memory and Reset
37. Offline Detection and In-Character Replies
38. Recipe Card
39. Live Cocktail Build Animation
40. MP4 Export with Manim
41. Render Cache
42. Video Preview Player
43. Phone Upload Server and QR Code
44. Bottle Recognition with Claude Vision
45. Web Search Tool
46. Background Threads and Signals
47. Thread Diagnostics and Crash Handling
48. Performance Tracing
49. Model Installer
50. Desktop Launcher (EXE)

====================================================================

## Features Explained

### 1. Application Startup

**How it is implemented in Lloyd**

- `run.py` only calls `run()` from `app/app.py`.
- `run()` does the following, in order:
  - Installs the thread diagnostics (see feature 47) and replaces `sys.excepthook` with a crash hook.
  - Loads the voice catalog (`load_catalog()`) before Qt starts, so voice errors show up early in the log.
  - Creates a `QApplication`, sets the `"Fusion"` style, and sets the organization and application names. `QSettings` needs these names to know where to save.
  - Creates `MainWindow`, shows it, and hands control to `app.exec()`.

**How to implement it in another project**

1. Keep the entry script tiny and put the real startup in a package module.
2. Use the `Fusion` style to get the same look on every OS.
3. Set the organization and application names before you create any `QSettings`.

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow


def run() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setOrganizationName("MyOrg")
    app.setApplicationName("MyApp")
    window = QMainWindow()
    window.show()
    sys.exit(app.exec())
```

### 2. Central Configuration

**How it is implemented in Lloyd**

- Every number, color, text string, path, and threshold lives in `app/config/`, with one module per area: `agent.py`, `voice.py`, `speech.py`, `theme.py`, `sphere.py`, `animation.py`, `chat.py`, `panels.py`, `render.py`, `offline.py`, `install.py`, and more.
- Constants are typed, module-level, and named in `UPPER_CASE`.
- `app/config/__init__.py` re-exports all of them, so any file can write `from app.config import COLOR_ACCENT`.
- The code itself has no magic numbers. Tuning the app means editing config only.

**How to implement it in another project**

1. Create a `config` package with one module per area.
2. Declare typed constants such as `WINDOW_MIN_WIDTH: int = 1024`.
3. Re-export them in the package `__init__.py` and import only from the package.
4. When you catch yourself typing a literal in logic code, move it to config.

### 3. Environment Settings (.env)

**How it is implemented in Lloyd**

- `app/core/paths.py` computes `PROJECT_ROOT` from `__file__`, so paths work from any working directory.
- `app/config/env.py` calls `load_dotenv(PROJECT_ROOT / ".env")` from **python-dotenv**. It defines three helpers:
  - `env_value(key, default)` returns the value, or the default when it is empty.
  - `env_float(key, default)` falls back to the default and prints a warning when the value is not a number.
  - `env_int(key)` returns `None` when the value is empty or invalid.
- `app/config/speech.py` builds the voice settings (`TTS_VOICE_ID`, pace, noise, volume, speaker, Edge voice) from these helpers.
- `.env.example` is the template that users copy.

**How to implement it in another project**

1. `pip install python-dotenv`, and call `load_dotenv(project_root / ".env")` once, inside a config module.
2. Wrap `os.getenv` in typed helpers that never crash on bad input.
3. Commit a `.env.example` file and add `.env` to `.gitignore`.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def env_float(key: str, default: float) -> float:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default
```

### 4. Main Window and Splitter Layout

**How it is implemented in Lloyd**

- `app/widgets/main_window.py`: `MainWindow(QMainWindow)` has a central `QWidget` with a zero-margin `QHBoxLayout`. The layout holds a horizontal `QSplitter` with two sides:
  - Left: `CanvasPanel`, which holds the sphere, the mic button, and the mute button.
  - Right: `ChatPanel`.
- The stretch factors are 3:1. The default sizes are 75% and 25% of the window width. The minimum window size is 1024×640.
- The floating panels (video, cocktail build, recipe card) are children of the main window, not separate windows. `_reposition_hud_widgets()` places them over the canvas with `canvas.mapTo(self, QPoint(...))`. `_raise_hud_widgets()` keeps them on top.
- Both methods run on resize and whenever the splitter moves.

**How to implement it in another project**

1. Use a `QSplitter` inside the central widget for resizable columns, and set stretch factors and initial sizes.
2. For overlays, make the overlay a child of the main window, not of a layout.
3. Position it with `mapTo()` and call `raise_()` after every resize.

### 5. Dark Theme Stylesheet

**How it is implemented in Lloyd**

- `app/config/theme.py` holds the palette (`COLOR_BG`, `COLOR_ACCENT`, the bubble colors, and so on), the fonts, the paddings, and the object names.
- `app/widget_helpers/stylesheet.py`: `build_stylesheet()` returns one QSS f-string built from those constants. It is applied once with `setStyleSheet` on the main window, and child widgets inherit it.
- Widgets are targeted by object name (`setObjectName("sendButton")` → `QPushButton#sendButton`) or by state (`:checked`, `:hover`, `:focus`).
- Dynamic look changes use custom properties. For example, `QPushButton#sendButton[busy="true"]` turns red. After changing the property, the code calls `style().unpolish()` and then `style().polish()` so Qt applies the new style.

**How to implement it in another project**

1. Put colors in constants and build the QSS in one function.
2. Give each styled widget an object name.
3. For state-based styling, use `widget.setProperty("busy", True)` together with a `[busy="true"]` selector, then re-polish the widget.

```python
button.setProperty("busy", True)
button.style().unpolish(button)
button.style().polish(button)
```

### 6. Custom Scrollbars

**How it is implemented in Lloyd**

- `app/widget_helpers/scrollbar_style.py` returns QSS for `QScrollBar`:
  - A 10 px dark track.
  - A rounded handle that changes color on hover.
  - A minimum handle length.
  - Zero-size arrow buttons (`add-line` and `sub-line`), so the arrows disappear.
  - Transparent page areas.
- It is appended to the main stylesheet and to every floating panel's stylesheet.

**How to implement it in another project**

- Write the same QSS block once and append it wherever a scroll area lives.
- The key parts are `QScrollBar::handle` (color, radius, min-height) and `QScrollBar::add-line` / `sub-line` with `height: 0px; width: 0px;` to hide the arrows.

### 7. Dark Title Bar

**How it is implemented in Lloyd**

- `app/widget_helpers/win_dark_mode.py` calls the Windows DWM API through `ctypes`: `DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), sizeof(...))`. Attribute 20 is `DWMWA_USE_IMMERSIVE_DARK_MODE`.
- It runs once, in the first `showEvent`, with `int(self.winId())`.
- It does nothing on other platforms and ignores errors on older Windows versions.

**How to implement it in another project**

- Copy the function and call it with the window handle after the window has been shown.
- Guard it with `sys.platform == "win32"` and a `try` block around the call.

```python
import ctypes
import sys
from ctypes import wintypes


def enable_dark_titlebar(window_handle: int) -> None:
    if sys.platform != "win32":
        return
    value = ctypes.c_int(1)
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(window_handle), 20, ctypes.byref(value), ctypes.sizeof(value)
        )
    except (AttributeError, OSError):
        pass
```

### 8. Window Placement Memory

**How it is implemented in Lloyd**

- `app/widget_helpers/window_placement.py` (`WindowPlacementManager`) and `app/widget_helpers/monitors.py`.
- **What it saves:** `saveGeometry()`, the window state (normal, maximized, or fullscreen), the monitor name, the monitor rectangle, and the normal rectangle. They go into `QSettings` under a key that depends on the current monitor layout. The layout signature is one letter per screen, `L` or `P`, so "laptop only" and "laptop + portrait monitor" each remember their own position.
- **When it saves:**
  - On move, resize, or state change, after a single-shot 400 ms `QTimer` (debounce).
  - Immediately in `closeEvent`.
- **How it restores:**
  - It finds the saved monitor by name and rectangle, then by the window's center point, then falls back to the primary screen.
  - It clamps the rectangle inside the monitor's available area (`fit`) and checks that the title bar is still reachable (`is_reachable`).
  - After `show()`, `confirm_placement()` moves the window back if Windows placed it on a different monitor.

**How to implement it in another project**

1. The simple version: `settings.setValue("geometry", window.saveGeometry())` on close, and `window.restoreGeometry(...)` on start.
2. For multi-monitor setups, add three things:
   - A layout signature in the settings key.
   - Clamping to `screen.availableGeometry()`.
   - A debounce timer, so dragging does not write to settings on every pixel.

### 9. Saved Splitter and Volume

**How it is implemented in Lloyd**

- In `MainWindow.closeEvent`, `QSettings(ORG_NAME, APP_NAME)` stores `splitter.saveState()` and the volume percent.
- On startup, `_restore_settings()` restores the splitter, or uses the 75/25 default. `_restore_volume()` reads the volume with `type=int`.
- On Windows, `QSettings` saves to the registry automatically.

**How to implement it in another project**

- Save `saveState()` or any plain value with `QSettings`, and read it back with a default and an explicit `type=`.

### 10. Fullscreen and Keyboard Shortcuts

**How it is implemented in Lloyd**

- `QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)`.
- `Esc` first closes the topmost visible panel (recipe card, then cocktail build, then video). If no panel is open, it toggles fullscreen.
- Toggling uses `showFullScreen()` and `showNormal()`.

**How to implement it in another project**

- Create `QShortcut` objects bound to the window.
- Give `Esc` a priority chain: close the innermost thing first, then exit fullscreen.

### 11. Animated Status Sphere

**How it is implemented in Lloyd**

- `app/widgets/sphere_widget.py` (`SphereWidget`) is fully custom-painted with `QPainter`. All of its parameters are in `app/config/sphere.py`.
- **Frame loop:** a `QTimer` in `PreciseTimer` mode fires every 16 ms (about 60 fps). A `QElapsedTimer` measures the real time between frames, capped at 50 ms, so the animation speed does not depend on the frame rate.
- **Five modes:** default, listening, thinking, rendering, and speaking. Each mode is a "look" dictionary that sets colors, size range, breathing period, swirl, orbiting nodes, particles, and how strongly the sphere reacts to voice.
- **Smooth transitions:** `SphereLook.approach()` moves every float and every `QColor` of the current look toward the target look with exponential smoothing, `1 - exp(-dt / transition_s)`. Mode changes therefore blend and never jump.
- **Breathing:** an eased inhale/exhale wave scales the radius.
- **Voice reaction:**
  - Amplitude comes from the microphone while listening and from the TTS player while speaking.
  - It feeds a fast envelope (attack/release) and a slow envelope.
  - The outline is a 180-point `QPainterPath`, deformed by sums of sine waves scaled by those envelopes. The sphere wobbles with the voice.
- **Paint layers, in order:**
  1. Halo (`QRadialGradient`).
  2. Rotating chromatic ring (`QConicalGradient`).
  3. Body gradient with an off-center focal point.
  4. Clipped to the outline: swirl blobs, core glow, smoke.
  5. Orbiting nodes with trails and inward-spiraling particles, drawn with additive blending (`CompositionMode_Plus`).
  6. Rim light and specular highlight.
- **Mode selection:** `MainWindow._refresh_busy_visuals()` picks the mode by priority:
  1. Models still loading → thinking.
  2. Rendering → rendering.
  3. Agent busy or transcribing → thinking.
  4. Speaking → speaking.
  5. Otherwise → default.

**How to implement it in another project**

1. Subclass `QWidget`, start a `QTimer` that updates the state and calls `update()`, and draw in `paintEvent`.
2. Keep a "current" and a "target" value for everything that animates, and move current toward target every frame.
3. Build complex looks from layered gradients, and use a clip path for inner effects.

```python
import math
from PyQt6.QtCore import QElapsedTimer, QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget


class PulseOrb(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._level = 0.0
        self._target = 0.0
        self._time_s = 0.0
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_level(self, level: float) -> None:
        self._target = max(0.0, min(1.0, level))

    def _tick(self) -> None:
        delta_s = min(self._clock.restart() / 1000.0, 0.05)
        self._time_s += delta_s
        self._level += (self._target - self._level) * (1.0 - math.exp(-delta_s / 0.12))
        self.update()

    def paintEvent(self, event) -> None:
        breath = 1.0 + 0.03 * math.sin(self._time_s * 2.0)
        radius = min(self.width(), self.height()) * 0.3 * (breath + 0.3 * self._level)
        center = QPointF(self.width() / 2, self.height() / 2)
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor("#ffd08a"))
        gradient.setColorAt(1.0, QColor("#5a300e"))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(center, radius, radius)
```

### 12. Chat Panel

**How it is implemented in Lloyd**

- `app/widgets/chat_panel.py` (`ChatPanel`).
- **History:** a `QScrollArea` with `setWidgetResizable(True)` wraps a `QVBoxLayout` that ends in a stretch. New bubbles are inserted at `count() - 1`, just before the stretch, so messages stack from the top.
- **Auto-scroll:** the vertical scrollbar's `rangeChanged` signal jumps to the maximum, and each append also calls `QTimer.singleShot(0, scroll_to_bottom)`.
- **Input row:** a `QLineEdit` (Enter sends) and the Send/Stop button.
- The panel owns the three workers, `Agent`, `LloydSpeaker`, and `RenderController`, and connects all of their signals.
- `MainWindow` passes its handlers as constructor callbacks (`on_thinking_started=...`). The panel reports state changes upward without importing the window.
- Input is disabled while Lloyd is busy or speaking.

**How to implement it in another project**

- Use a scroll area, an inner `QVBoxLayout`, and a trailing stretch. Insert new messages before the stretch and scroll to the bottom on `rangeChanged`.

### 13. Chat Bubbles

**How it is implemented in Lloyd**

- `app/widgets/chat_bubble.py`: a `QWidget` that holds one `QLabel` with word wrap and a maximum width of 220 px.
- The label's object name is `userBubble` or `agentBubble`. The QSS gives each its own background color, a 14 px radius, and padding.
- The alignment comes from the layout:
  - User bubble: a stretch on the left, so it sits on the right.
  - Agent bubble: a stretch on the right, so it sits on the left.

**How to implement it in another project**

```python
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ChatBubble(QWidget):
    def __init__(self, text: str, is_user: bool, parent=None) -> None:
        super().__init__(parent)
        label = QLabel(text, self)
        label.setObjectName("userBubble" if is_user else "agentBubble")
        label.setWordWrap(True)
        label.setMaximumWidth(220)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if is_user:
            layout.addStretch(1)
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch(1)
```

Then style `QLabel#userBubble` and `QLabel#agentBubble` with `background-color`, `border-radius`, and `padding`.

### 14. Typing Indicator

**How it is implemented in Lloyd**

- `app/widgets/typing_indicator.py`: `_TypingBubble` paints a rounded rectangle and three dots.
- Each dot's height is `sin(phase - i * 0.9) * 5 px`, so the dots bounce one after another. A 16 ms `QTimer` advances the phase.
- `TypingIndicator` aligns the bubble on either side:
  - Left, in the agent's color, while Claude is thinking.
  - Right, in the user's color, while your voice is being transcribed.
- When the wait ends, the timer is stopped and the widget is removed and deleted with `deleteLater()`.

**How to implement it in another project**

- Use a small fixed-size widget with a `QTimer` and a `paintEvent` that offsets each dot with a phase-shifted sine.
- Always stop the timer before you delete the widget.

### 15. Send / Stop Button

**How it is implemented in Lloyd**

- It is one button. `_set_busy(True)` changes its text to "Stop" and sets the `busy` property, and the stylesheet turns it red.
- Clicking it while busy calls `interrupt()` (see feature 35). Clicking it while idle sends the message.

**How to implement it in another project**

- Reuse one button with a busy flag. Choose the action in the click handler, and restyle with a dynamic property.

### 16. Mic Toggle Button

**How it is implemented in Lloyd**

- It is a checkable `QPushButton` in `CanvasPanel`. It starts disabled with the text "Speech model is loading" and becomes enabled when `VoiceListener.listener_ready` fires.
- Checked means muted:
  - `voice_listener.pause()` closes the microphone stream completely.
  - `resume()` reopens it.
- The `:checked` state is styled red.

**How to implement it in another project**

- Use `setCheckable(True)` with the `toggled(bool)` signal. Keep it disabled until the backend reports ready.
- To mute, actually release the device instead of only ignoring the audio.

### 17. Mute Button and Volume Popup

**How it is implemented in Lloyd**

- `app/widgets/canvas_panel.py` and `app/widgets/volume_popup.py`.
- **The mute button:** a round, checkable button. It is not in a layout; `resizeEvent` positions it at the bottom-right corner of the sphere.
- **Opening the popup:** an `eventFilter` on the button catches `Enter` and `Leave`. On hover it shows `VolumePopup` above the button: a `QFrame` with a percent label and a vertical `QSlider` from 0 to 100.
- **Closing the popup:**
  - A 300 ms single-shot timer hides it after the mouse leaves.
  - The timer is cancelled if the mouse enters the popup, which reports this through the `hover_entered` and `hover_left` signals from `enterEvent` and `leaveEvent`.
  - It never hides while the slider is being dragged (`isSliderDown()`).
- **How mute and volume interact:**
  - Volume 0 checks the mute button.
  - Unmuting at 0 restores the last audible volume.
  - `set_value` uses `blockSignals` so programmatic changes do not loop back.

**How to implement it in another project**

1. Show the popup from an event filter on hover.
2. Hide it with a delay timer that the popup itself can cancel.
3. Remember the last non-zero value so unmute can restore it.

### 18. Floating Resizable Panels

**How it is implemented in Lloyd**

- `app/widgets/floating_panel.py` (`FloatingPanel(QFrame)`) is the base class for the video player, the cocktail build, and the recipe card.
- **Look:** a colored border and a header with an uppercase title (trimmed to 30 characters), optional action buttons (`make_action_button`), and a red close button.
- **Resizing:**
  - `setMouseTracking(True)` gives mouse moves without a pressed button. Within 8 px of the side or bottom edge, the cursor changes to a resize shape.
  - On press, the panel stores the global mouse position and its geometry. On move, it computes the new size and never goes below the minimum.
  - `resize_side="left"` makes the right-anchored recipe card grow to the left.
- Subclasses override `on_body_clicked()` and `close_panel()`.

**How to implement it in another project**

- Subclass `QFrame` and turn on mouse tracking.
- In `mousePressEvent`, record the press point and geometry. In `mouseMoveEvent`, apply the delta to width and height, clamped to minimums. In `mouseReleaseEvent`, reset.

### 19. Wake Word Detection

**How it is implemented in Lloyd**

- `app/threads/voice_listener.py` (`VoiceListener(QThread)`).
- **Microphone:** `sounddevice.RawInputStream` records 16 kHz mono int16 audio in 2048-frame blocks.
- **Audio callback:** it pushes bytes into a bounded `queue.Queue` that holds 1 second of audio. When the queue is full, it drops the oldest chunk and never blocks the audio thread.
- **Recognition:**
  - A **Vosk** small English model (`KaldiRecognizer`) reads every chunk with `AcceptWaveform`, `Result`, and `PartialResult`, fully offline.
  - `_matches_wake_word` fuzzy-matches the last word against "lloyd", "loyd", "floyd", and "boyd" using `thefuzz.fuzz.ratio >= 88`.
  - The match must follow a greeting ("hey", "hi", "hay", "ay", ratio >= 80), or the whole utterance must be at most 2 words.
  - A 1.5-second refractory period prevents double triggers.
- **Preroll:** a `deque` keeps the last 1.5 seconds of audio, so words said right after "Hey Lloyd" are not lost.
- A grammar-restricted recognizer is supported but off by default, with an automatic fallback.

**How to implement it in another project**

1. Download a Vosk model and `pip install vosk sounddevice thefuzz`.
2. Record in a background thread, move audio through a bounded queue, and run a `KaldiRecognizer`.
3. Fuzzy-match the recognized words against your wake word and its common misrecognitions.

```python
import json
import queue
import sounddevice as sd
import vosk
from thefuzz import fuzz

audio: "queue.Queue[bytes]" = queue.Queue(maxsize=8)


def on_audio(indata, frames, time_info, status) -> None:
    try:
        audio.put_nowait(bytes(indata))
    except queue.Full:
        pass


model = vosk.Model("models/vosk-model-small-en-us-0.15")
recognizer = vosk.KaldiRecognizer(model, 16000)
with sd.RawInputStream(samplerate=16000, blocksize=2048, dtype="int16", channels=1, callback=on_audio):
    while True:
        chunk = audio.get()
        if recognizer.AcceptWaveform(chunk):
            text = json.loads(recognizer.Result()).get("text", "")
        else:
            text = json.loads(recognizer.PartialResult()).get("partial", "")
        words = text.split()
        if words and fuzz.ratio("jarvis", words[-1]) >= 88:
            print("wake word heard")
            recognizer = vosk.KaldiRecognizer(model, 16000)
```

### 20. Stop Word Detection

**How it is implemented in Lloyd**

- While Lloyd is thinking, speaking, or transcribing, `MainWindow` calls `voice_listener.suspend()`.
- In suspended mode the wake word is ignored and the preroll is cleared. The listener checks only whether the last two words are the wake keyword followed by a fuzzy "stop".
- A match emits `stop_word_detected`, and the main window calls `chat_panel.interrupt()`.

**How to implement it in another project**

- Keep the wake-word recognizer running during playback, but switch it to a "commands only" mode that listens for a short phrase such as "<name> stop" and cancels the current work.

### 21. Command Recording and End-of-Speech Detection

**How it is implemented in Lloyd**

- `_capture_command()` in `voice_listener.py`, and `app/audio/capture.py`.
- Recording starts with the preroll and keeps collecting chunks until one of three things happens:
  - No speech started within 5 seconds.
  - 12 seconds have passed.
  - Silence has lasted long enough after speech: 0.4 s with Silero, or 1.2 s with the RMS fallback.
- **Silero VAD:**
  - The ONNX session is reused from `faster_whisper.vad.get_vad_model()`, so there is no extra download.
  - It runs on 512-sample frames, keeps its LSTM state (`h`, `c`) and a 64-sample context between frames, and uses hysteresis: speech starts at probability ≥ 0.5 and ends below 0.35.
- **Fallback:** `RmsSpeechDetector` treats a chunk as speech when its RMS is ≥ 300.
- Each chunk's normalized RMS is emitted as `listening_amplitude`, which drives the sphere.
- The same audio also goes to a second Vosk recognizer, which gives an instant rough transcript as a backup.

**How to implement it in another project**

- Use a VAD (Silero, WebRTC VAD, or simple RMS) to detect the end of speech. Stop after a short silence, and also enforce a start timeout and a maximum length.
- Keep a preroll buffer so the first word is not cut off.

### 22. Speech-to-Text Transcription

**How it is implemented in Lloyd**

- **Loading:** **faster-whisper** `WhisperModel("distil-small.en", device="cpu", compute_type="int8", cpu_threads=8, download_root="models/whisper")`.
  - It loads in a separate `threading.Thread` at startup, so the wake word works while Whisper is still loading.
  - It is warmed up by transcribing 1 second of silence, so the first real request is fast.
- **Decoding:** `beam_size=1`, `temperature=0`, `without_timestamps=True`, `condition_on_previous_text=False`, `vad_filter=True`. The audio bytes are converted with `int16 → float32 / 32768`.
- If Whisper failed to load, the Vosk rough transcript is used.
- The result is emitted as `wake_word_detected(text)`. It then goes through `ChatPanel.finish_voice_transcription()` to `submit_message(via_voice=True)`.

**How to implement it in another project**

```python
import numpy as np
from faster_whisper import WhisperModel

model = WhisperModel("distil-small.en", device="cpu", compute_type="int8")


def transcribe(pcm_int16: bytes) -> str:
    audio = np.frombuffer(pcm_int16, dtype=np.int16).astype(np.float32) / 32768.0
    segments, _ = model.transcribe(audio, language="en", beam_size=1, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()
```

Load the model in the background at startup and warm it up once.

### 23. Voice Clear-Chat Command

**How it is implemented in Lloyd**

- Typed: the text must be exactly `/clear`.
- Spoken:
  - `normalize_voice_command()` in `app/core/text.py` lowercases the text, removes punctuation, and strips leading "hey" and "lloyd" words.
  - The result is fuzzy-matched against "clear the chat", "clean the chat", "clear chat", and "clean chat" (ratio ≥ 85).
- `_clear_chat()` deletes every bubble widget and calls `agent.reset_session()` (see feature 36).

**How to implement it in another project**

- Intercept local commands before sending text to the LLM: exact matching for typed commands, fuzzy matching for spoken ones.

### 24. Claude Connection

**How it is implemented in Lloyd**

- It uses the **Claude Agent SDK** (`claude-agent-sdk`).
- `app/agent/client.py`: `build_options(handlers)` returns `ClaudeAgentOptions` with these settings:
  - `system_prompt`: the bartender prompt (see feature 25).
  - `model=AGENT_MODEL`.
  - `mcp_servers={"bartender": create_sdk_mcp_server(...)}` and `allowed_tools=["mcp__bartender__render_animation", ...]`.
  - `tools=[]` turns off the built-in Claude Code tools (Bash, Read, and so on). `setting_sources=[]` ignores user and project settings files.
  - `permission_mode="bypassPermissions"`, so tools run without prompts.
  - `include_partial_messages=True`, for token streaming.
  - `env={"ENABLE_TOOL_SEARCH": "false"}` and `cwd=PROJECT_ROOT`.
- `app/threads/agent_thread.py` (`Agent(QThread)`):
  - The thread runs its own `asyncio` event loop. At startup it connects one long-lived `ClaudeSDKClient` (`await client.connect()`).
  - `submit(message)` is called from the GUI thread and schedules `_process_message` with `asyncio.run_coroutine_threadsafe`.
  - Each turn runs `await client.query(message)` and then `async for item in client.receive_response()`.
  - An `asyncio.Lock` makes sure only one turn runs at a time.
- Authentication comes from the Claude Code login or `ANTHROPIC_API_KEY`.

**How to implement it in another project**

```python
import asyncio
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock


async def ask(prompt: str) -> str:
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant.",
        tools=[],
        setting_sources=[],
    )
    reply = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        reply += block.text
    return reply


print(asyncio.run(ask("Name one classic gin cocktail.")))
```

In a GUI app, keep one client connected in a worker thread's event loop, not one `async with` per message.

### 25. System Prompt and Persona

**How it is implemented in Lloyd**

- `app/agent/prompt.py`: `build_system_prompt()` joins separate sections with blank lines:
  - `VOICE`: the input is speech and the reply is read aloud.
  - `PERSONA`: a calm bartender with twenty years behind the bar, American idiom, one sensory detail, no exclamation marks.
  - `RESPONSE_SHAPE`: speak first in 2 to 4 plain sentences, then call at most one tool. The routing lines are listed here.
  - `SOURCING`: IBA, Difford's Guide, and the Cocktail Codex; metric units only; shake versus stir rules.
  - `PACING`: walk through a build one step at a time.
  - `Answering without a tool`: the behaviour blocks (see feature 28).
  - `TOOL_FAILURES`: say what went wrong, and fix the spec and retry once.
- The routing lines are not written by hand. Each tool module contributes its own `ROUTING` string, so the prompt always matches the registered tools.

**How to implement it in another project**

- Split the prompt into named constants, one concern each, and assemble them in a function.
- Generate the tool-routing part from your tool registry.
- For voice apps, forbid markdown and lists, because the text is read aloud.

### 26. Custom Agent Tools

**How it is implemented in Lloyd**

- `app/agent/tools/`: each tool is one module that exports `NAME`, `ROUTING`, `DESCRIPTION`, `SCHEMA`, and `build(handlers)`.
- `build()` wraps an `async` function with the SDK's `tool(NAME, DESCRIPTION, schema)(function)`, called as a normal function.
- `tools/__init__.py` holds the registry: `TOOL_MODULES`, `ALLOWED_TOOLS` (`mcp__bartender__<name>`), and `build_all()`.
- The tools run in an in-process MCP server (`create_sdk_mcp_server`), not a separate process.
- A handler returns `{"content": [{"type": "text", "text": ...}]}`, plus `"is_error": True` when it fails.
- `handlers` is the `Agent` thread itself:
  - `on_recipe` and `on_animation` emit Qt signals, which Qt delivers to the GUI thread.
  - `on_scan` is `async` and waits for the phone photo.
- `web_search` is marked read-only with `ToolAnnotations(readOnlyHint=True)`.

**How to implement it in another project**

```python
from typing import Any
from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, tool


async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": "It is 18:00."}]}


time_tool = tool("get_time", "Return the current local time.", {"type": "object", "properties": {}})(get_time)
server = create_sdk_mcp_server(name="helper", version="1.0.0", tools=[time_tool])
options = ClaudeAgentOptions(
    mcp_servers={"helper": server},
    allowed_tools=["mcp__helper__get_time"],
    tools=[],
)
```

To let a tool update a GUI, have it emit a Qt signal instead of touching widgets directly.

### 27. Tool Argument Validation (JSON Schema)

**How it is implemented in Lloyd**

- `render_animation.py` and `show_recipe.py` each define a strict draft-07 schema:
  - `additionalProperties: False` everywhere.
  - Enums for the glass, action, ice, strain, and garnish values.
  - Regex patterns for snake_case ids and `#RRGGBB` colors.
  - `amount` must be either a number or the string `"top the cocktail"` (`oneOf`).
  - `minItems` for steps.
  - An `allOf` rule that the first step must be a `chill` action.
- `input_schema()` deep-copies the schema and removes `$schema`, `title`, and `allOf`, which the tool definition does not accept. That trimmed copy is what Claude sees.
- The handler validates the arguments against the **full** schema with `jsonschema.validate`. On `ValidationError` it returns `is_error` with the message, and the prompt tells Claude to fix the spec and call once more.
- The schema descriptions double as instructions, for example "Campari #C81A17, bourbon #B85A1E".

**How to implement it in another project**

- Never trust tool arguments. Validate them with `jsonschema` inside the handler and return the error text to the model so it can correct itself. Write precise `description` fields, because the model reads them.

### 28. Prompt Behaviours

**How it is implemented in Lloyd**

- `app/agent/behaviours/` contains `story.py`, `top_shelf.py`, `bar_knowledge.py`, and `suggestions.py`. Each exports `NAME` and a `BLOCK` of prompt text.
- `BLOCKS` is added to the system prompt. No code runs for them; they only shape Claude's answers. For example:
  - A cocktail story is four spoken paragraphs: hook, chronicle, how the recipe came together, and legacy. There are variants for "quick version" and "is that true?".
  - A bottle presentation is an opening line and four movements, with a web search fallback for unknown bottles.
  - They are marked as long-form, which overrides the usual 2 to 4 sentence limit.

**How to implement it in another project**

- When a "feature" is only a way of answering, write it as a prompt module instead of a tool.
- Keep the modules in a tuple, so adding a behaviour means adding one file and one entry.

### 29. Streaming Replies Spoken Sentence by Sentence

**How it is implemented in Lloyd**

- `Agent._run_turn()` in `agent_thread.py`.
- With `include_partial_messages=True`, the SDK yields `StreamEvent`s. Each `content_block_delta` with a `text_delta` is added to a buffer.
- `split_completed_sentences(buffer)` splits on the regex `(?<=[.!?])\s+`. It returns the completed sentences and keeps the unfinished tail in the buffer.
- Each completed sentence is cleaned (see feature 30) and emitted as `speak_sentence`, which goes to `LloydSpeaker.enqueue()`. Lloyd starts talking while Claude is still writing.
- `content_block_stop` and `ResultMessage` flush the tail. If no deltas arrived at all, the full `AssistantMessage` text blocks are used.
- At the end of the turn, `format_reply_for_display()` turns the whole transcript into one chat bubble with its paragraphs kept, and `speech_complete` tells the speaker the turn is over.

**How to implement it in another project**

```python
import re

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_completed_sentences(buffer: str) -> tuple[list[str], str]:
    parts = SENTENCE_END.split(buffer)
    if len(parts) == 1:
        return [], buffer
    return [part.strip() for part in parts[:-1] if part.strip()], parts[-1]
```

Add every streamed chunk to the buffer, send the completed sentences to TTS, and keep the remainder for the next chunk.

### 30. Text Cleanup for Speech

**How it is implemented in Lloyd**

- `clean_text_for_speech()` in `app/core/text.py` changes the text in this order. All patterns are in `app/config/speech.py`.
  1. Removes the markdown characters `* # _ \` ~`.
  2. Removes emoji (the astral Unicode range).
  3. Turns `1/2` into "half" and `3/4` into "three quarters".
  4. Turns `45 ml` into "45 milliliters", and does the same for cl and oz.
  5. Turns `10-15` into "10 to 15".
  6. Turns `4°C` into "4 degrees Celsius".

**How to implement it in another project**

- Run every string through a regex normalization pass before TTS. Voices read symbols badly.

### 31. Text-to-Speech Engines

**How it is implemented in Lloyd**

- `app/audio/tts_engine.py` has two engines with the same interface: `name`, `warmup()`, and `synthesize(sentence, is_cancelled) -> (pcm_int16, sample_rate) | None`.
  - **`PiperEngine`**: **piper-tts**, a local ONNX neural voice.
    - It loads with `PiperVoice.load(model, use_cuda=False)` and a `SynthesisConfig` (speaker, length, noise, noise_w, volume).
    - It collects the `audio_int16_bytes` chunks and runs in `asyncio.to_thread` behind a lock.
  - **`EdgeEngine`**: **edge-tts**, an online Microsoft neural voice and the fallback. It streams MP3 chunks, which **soundfile** decodes to int16 PCM.
- `create_engine()` tries Piper first and falls back to Edge.
- `app/threads/speaker.py` (`LloydSpeaker(QThread)`) owns an asyncio loop and an `asyncio.Queue` of `(generation, payload)` items:
  - Sentences are synthesized in order and fed to the player, with 120 ms of silence between them.
  - The `_TURN_END` marker waits until playback has drained, then emits `speech_finished`.
  - The engine speaks "Ready." once at startup to warm up.

**How to implement it in another project**

```python
import numpy as np
import sounddevice as sd
from piper import PiperVoice

voice = PiperVoice.load("voices/en_GB-alan-medium.onnx")
pcm = bytearray()
rate = 22050
for chunk in voice.synthesize("Good evening. What are we drinking?"):
    pcm.extend(chunk.audio_int16_bytes)
    rate = chunk.sample_rate
sd.play(np.frombuffer(bytes(pcm), dtype=np.int16), rate)
sd.wait()
```

Give all engines one shared interface, so a fallback engine is a one-line swap.

### 32. Swappable Voice Catalog

**How it is implemented in Lloyd**

- `app/audio/voices.py` scans `voices/*.onnx`. Each voice needs a matching `.onnx.json`, which provides the sample rate, the number of speakers, and the default `length_scale`, `noise_scale`, and `noise_w`.
- Each voice becomes a `VoiceSpec`. The default model is also registered under the short name `alan`.
- The `.env` multipliers (`LLOYD_VOICE_LENGTH`, and so on) multiply the model's own values, and apply only to the selected voice. The speaker id is range-checked.
- `resolve_voice()` tries these in order: the requested voice, the default voice, any Piper voice, and Edge. It logs every fallback.
- `load_catalog()` is cached and runs once at startup.

**How to implement it in another project**

- Discover models by scanning a folder, pair each model with its config file, and select one by a name from `.env`, with a clear fallback chain and log messages.

### 33. Audio Playback with Live Amplitude

**How it is implemented in Lloyd**

- `app/audio/playback.py` (`AmplitudePlayer`) opens a `sounddevice.OutputStream` (int16, mono, 512-frame blocks).
- The callback takes samples from a numpy buffer under a lock, fills any gap with zeros, and applies the gain.
- It computes the RMS of the block, normalized to a peak of 6000, and passes it to `on_amplitude`. That is a Qt signal emit, which is safe from any thread, and it makes the sphere react to Lloyd's voice.
- `feed()` appends PCM while playback runs, so sentence 1 plays while sentence 2 is being synthesized.
- A `threading.Event` marks when all input has been played.

**How to implement it in another project**

- Use a callback-based output stream that reads from a growing buffer. Compute the RMS per block in the callback for visual meters. Pad with silence instead of stopping when the buffer runs dry.

### 34. Volume Curve

**How it is implemented in Lloyd**

- `app/audio/volume.py`: `percent_to_gain(percent)` maps 0 to 100% onto −40 dB to 0 dB, then converts to linear gain with `10 ** (dB / 20)`. 0% means silence.
- The gain is applied inside the audio callback, so changes are instant.
- Mute sets the gain to 0 without forgetting the slider value.

**How to implement it in another project**

- Never map a slider linearly to amplitude. Map it to decibels and then convert, so each slider step sounds equally loud.

### 35. Interrupt Everything

**How it is implemented in Lloyd**

- It is triggered by the Stop button or by saying "Lloyd stop".
- `ChatPanel.interrupt()` works like this:
  - If a voice command is still being transcribed, it only cancels that.
  - Otherwise it stops the agent:
    - `agent.interrupt()` sets a `threading.Event` that the stream loop checks.
    - It stops child workers such as the phone server.
    - It schedules `client.interrupt()` on the agent's event loop.
  - It stops the speech: `lloyd_speaker.stop()` increments a **generation counter**.
    - Queued sentences from the old generation are skipped.
    - Running synthesis sees `is_cancelled()` return `True`.
    - The player stops.
  - `render_controller.cancel()` kills the Manim process.
  - The UI returns to idle.

**How to implement it in another project**

- Use a generation (epoch) number. Every queued job carries the generation it was created in, and "stop" just increments the number, so stale jobs drop themselves. This beats trying to clear every queue by hand.

### 36. Conversation Memory and Reset

**How it is implemented in Lloyd**

- One `ClaudeSDKClient` stays connected for the whole session, so the SDK keeps the conversation history. Follow-ups such as "next step" and "repeat that measurement" work without repeating the drink's name.
- `reset_session()` closes the client and connects a new one under the turn lock, which starts a fresh conversation.
- If the client is missing (for example after going offline), the next message reconnects it.

**How to implement it in another project**

- Keep a persistent client for chat memory. To clear memory, disconnect and reconnect instead of trimming history by hand.

### 37. Offline Detection and In-Character Replies

**How it is implemented in Lloyd**

- `app/core/connectivity.py`: `is_online()` opens a TCP connection to `api.anthropic.com:443` with a 1.5-second timeout. The result is cached for 5 seconds, but every new message checks without the cache.
- `app/core/offline_lines.py` picks one of 14 in-character lines from `app/config/offline.py`, such as "Bar's dark tonight...". It never picks the same line twice in a row.
- `ChatPanel` holds the line until the TTS engine is ready, then shows and speaks it.
- If a turn fails, Lloyd checks the connection again:
  - Offline: close the client and say an offline line.
  - Online: say "Something broke on my end".
- A message sent before the agent is ready gets "Give me a second, I'm still setting up".

**How to implement it in another project**

- Probe the real API host with a short socket connect before each request. When it fails, show and speak a friendly message instead of a stack trace.

### 38. Recipe Card

**How it is implemented in Lloyd**

- **Flow:** the `show_recipe` tool calls `Agent.on_recipe`, which emits `recipe_ready(dict)`. `MainWindow` then calls `TopRightRecipyWidget.show_recipe()` in `app/widgets/recipe_panel.py`.
- **Layout:**
  - A rich-text title.
  - Pill badges: the glass, the method (Built, Shaker, or Mixing glass), and Foam.
  - A `QGridLayout` ingredient table. Each row has a color pip (a round `QLabel` in the ingredient's `color_hex`), the name, and a right-aligned amount ("Top up" in italics), with thin dividers between rows.
  - Numbered steps with rich-text bodies.
- **Formatting:** `app/widgets/recipe_content.py` holds pure formatting functions with no Qt dependency: `glass_label`, `method_label`, `amount_label`, and `instruction_text`, which strips durations with a regex.
- **Sizing:** `_fit_to_content()` measures `heightForWidth` of the content. It caps the height to a share of the screen and of the parent window, and measures again with room for the scrollbar if the content does not fit.
- **Styling:** `app/widget_helpers/recipe_style.py`.

**How to implement it in another project**

- Keep data-to-text formatting in plain functions and widget building in the panel class.
- To auto-size a scrollable card, use `layout.heightForWidth(viewport_width)`, then clamp the result.

### 39. Live Cocktail Build Animation

**How it is implemented in Lloyd**

- **Flow:** the `render_animation` tool emits `animation_ready`, which reaches `CocktailCanvasPopup.play(spec)` and then `CocktailCanvas(QGraphicsView)` in `app/widgets/cocktail_canvas.py`.
- **Scene:** a `QGraphicsScene` in scene units (14.2 × 8, the same as a Manim frame). `qp(x, y)` flips the y-axis, so the math matches Manim. `fitInView(..., KeepAspectRatio)` on resize makes it scale to any panel size.
- **Items:** `ShapeItem(QGraphicsObject)`, which paints a `QPainterPath` (`app/widget_helpers/canvas_items.py`). Because it is a `QGraphicsObject`, `opacity`, `pos`, and `rotation` can be animated with `QPropertyAnimation`.
- **Building the sequence:** the whole build is prepared in advance as one `QSequentialAnimationGroup`: the title, the ingredient list, and then, for each step, the step text swap, the vessel reveal, and an action builder picked from a dictionary. The actions work like this:
  - `measure`: a pour stream line, then a trapezoid liquid layer whose width follows the glass taper (`VesselShape.width_at`) and whose height is proportional to the ml.
  - `shake`: rotation wiggles, then all layers merge into one layer with the average color.
  - `stir`: a bar spoon moving along an elliptical orbit (`QVariantAnimation`).
  - `strain`: a tilt, a cubic pour curve, and the transfer into the serving glass.
  - `ice`, `muddle`, `chill`, and `garnish` use their own shapes.
- The sequence loops forever and resets opacities at the start of each loop.
- `app/animation/recipe.py` (`Recipe`, `needs_shaker`, `ingredient_color`) is shared with Manim and the recipe card.

**How to implement it in another project**

- Use `QGraphicsView`/`QGraphicsScene`. Subclass `QGraphicsObject` (not `QGraphicsItem`) so you can animate its properties.
- Compose `QPropertyAnimation`s into sequential and parallel groups, and give each animation a parent or add it to a group, so it is not garbage-collected.

```python
from PyQt6.QtCore import QPropertyAnimation, QRectF
from PyQt6.QtGui import QBrush, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsObject


class PathItem(QGraphicsObject):
    def __init__(self, path: QPainterPath, color: str) -> None:
        super().__init__()
        self._path = path
        self._brush = QBrush(QColor(color))

    def boundingRect(self) -> QRectF:
        return self._path.boundingRect()

    def paint(self, painter, option, widget=None) -> None:
        painter.setBrush(self._brush)
        painter.drawPath(self._path)


def fade_in(item: QGraphicsObject, duration_ms: int, parent) -> QPropertyAnimation:
    animation = QPropertyAnimation(item, b"opacity", parent)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    return animation
```

### 40. MP4 Export with Manim

**How it is implemented in Lloyd**

- **Flow:** the **MP4** button on the build panel emits `export_requested(spec)`. It goes to `ChatPanel.request_render` and then to `RenderController.request` in `app/render/controller.py`.
- **The controller:**
  - Writes the spec to a temporary JSON file.
  - Starts `python -m app.render.cli <spec.json>` with **`QProcess`**. A separate process keeps the UI responsive and isolates Manim's global config.
  - Reads stdout and stderr asynchronously and parses the `RENDER_OK:<path>` and `RENDER_FAILED:<msg>` markers into the `render_finished` and `render_failed` signals.
  - Deletes the temporary spec file.
- **`app/render/cli.py`:**
  - Configures `manim.config` (low quality, cairo renderer, no caching, temporary media directory) and runs `CocktailAnimationScene(data).render()` from `app/animation/scene.py`.
  - The scene is a Manim `Scene` with `Container` vessels (`vessel.py`) and props (`props.py`). It uses the same step handlers as the live canvas, drawn with Manim animations (`FadeIn`, `Create`, `ReplacementTransform`, ...).
  - The file is copied to `output/<Name>.mp4` atomically: first to a `.tmp` file, then moved with `os.replace`.
- While rendering, the sphere is in rendering mode, and Stop kills the process.
- `ANIM_BACKEND` in config chooses canvas, manim, or both for tool calls. The default is the canvas, with MP4 on demand.

**How to implement it in another project**

- Run heavy renderers in a child process with `QProcess` and talk to it through simple stdout markers. Write outputs atomically, with a temporary file plus `os.replace`.

### 41. Render Cache

**How it is implemented in Lloyd**

- After a successful render, `cli.py` writes a sidecar file, `output/<Name>.json`. It holds a canonical fingerprint: `json.dumps(spec, sort_keys=True, separators=(",", ":"))`.
- Before rendering, `cached_render_path()` checks that the video exists and that the sidecar matches the fingerprint. If both are true, it emits `render_cached` immediately.
- Words such as "rerender", "redo", or "regenerate" in the last user message skip the cache.

**How to implement it in another project**

- Cache expensive outputs by a canonical JSON fingerprint of their inputs (sorted keys) and store it next to the output file.

### 42. Video Preview Player

**How it is implemented in Lloyd**

- `app/widgets/video_panel.py` (`TopLeftVideoWidget(FloatingPanel)`) uses `QMediaPlayer`, `QAudioOutput`, and `QVideoWidget` from **PyQt6.QtMultimedia**, with looping set to `Infinite`.
- `show_preparing()` shows "Creating ..." while the render runs. On success, the player takes the build panel's exact geometry.
- Clicking the video opens it in the system player: `os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux.

**How to implement it in another project**

```python
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

video = QVideoWidget()
player = QMediaPlayer()
audio = QAudioOutput()
player.setAudioOutput(audio)
player.setVideoOutput(video)
player.setLoops(QMediaPlayer.Loops.Infinite)
player.setSource(QUrl.fromLocalFile("output/Negroni.mp4"))
video.show()
player.play()
```

### 43. Phone Upload Server and QR Code

**How it is implemented in Lloyd**

- **Flow:** the `scan_shelf` tool calls `Agent.on_scan()`, which creates a `threading.Event` and emits `_popup_requested`. Because of the signal, the window is created on the GUI thread. The agent then waits with `await asyncio.to_thread(done_event.wait)`.
- **`ScanReceiverPopup`** in `app/widgets/scan_receiver_popup.py`:
  - `get_local_ip()` connects a UDP socket to `10.255.255.255` and reads `getsockname()`. No packet is sent; the OS just picks the Wi-Fi IP.
  - It starts a `ThreadingHTTPServer` on `0.0.0.0:8080` inside `PhoneServerWorker`, a `QThread` that runs `serve_forever`. Stopping calls `httpd.shutdown()`.
  - It builds a QR code with the **qrcode** library, saves it as PNG into a `BytesIO`, and shows it with `QPixmap.loadFromData` in a `QLabel`.
- **`PhoneUploadHandler`** in `app/network/phone_upload.py`:
  - `GET` serves a mobile page embedded in `app/network/html.py`. Its `<input type="file" accept="image/*" capture="environment">` opens the phone's rear camera, and `fetch('/upload', {method: 'POST', body: file})` sends the photo.
  - `POST /upload` saves `output/scan_<ms>.jpg` and emits `ServerBridge.image_received(path)`. `ServerBridge` is a `QObject` signal that carries the event safely from the server thread to Qt.
- On the first image: store the path, stop the server, set the event, and close the window. Closing the window without a photo reports "Scan cancelled".
- The phone must be on the same Wi-Fi network, and Windows may ask to allow Python through the firewall.

**How to implement it in another project**

- Serve a one-page HTML uploader from `http.server` in a background thread, show its LAN URL as a QR code, and pass the uploaded file path back to the GUI through a `QObject` signal.

### 44. Bottle Recognition with Claude Vision

**How it is implemented in Lloyd**

- `app/agent/vision.py` (`analyze_bottle_photo`) opens a separate one-shot `ClaudeSDKClient`. It has no tools, and its system prompt is `VISION_PROMPT` from `scan_shelf.py`, which asks for three passes and a strict JSON array.
- The photo is sent as an async generator that yields one user message. Its content is an `image` block (base64, media type from `mimetypes`) plus a text block.
- `parse_json_list()` strips ```` ``` ```` fences, runs `json.loads`, and accepts only a list.
- `scan_shelf._build_inventory()` normalizes each item:
  - Trims the text fields.
  - Puts each item into `spirits`, `modifiers`, or `other`.
  - Sets `confident` only when a name was read.
- It returns JSON to the main agent, which speaks a four-paragraph shelf report. Brands it is unsure of are described by color and position.
- The photo is deleted after analysis.

**How to implement it in another project**

```python
import base64
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage


async def describe_image(path: str) -> str:
    data = base64.b64encode(open(path, "rb").read()).decode("ascii")

    async def turn():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
                    {"type": "text", "text": "List every bottle as a JSON array."},
                ],
            },
        }

    result = ""
    async with ClaudeSDKClient(options=ClaudeAgentOptions(tools=[], setting_sources=[])) as client:
        await client.query(turn())
        async for message in client.receive_response():
            if isinstance(message, ResultMessage) and isinstance(message.result, str):
                result = message.result
    return result
```

### 45. Web Search Tool

**How it is implemented in Lloyd**

- `app/agent/tools/web_search.py` uses **ddgs** (DuckDuckGo): `DDGS().text(query, max_results=5)`.
- The library is imported lazily and runs in `asyncio.to_thread`, so the blocking HTTP call never stalls the event loop.
- An `OrderedDict` LRU cache holds 32 queries: `move_to_end` on a hit and `popitem(last=False)` on overflow.
- The tool description limits its use to current or obscure facts, never classic recipes.

**How to implement it in another project**

- Wrap any blocking search API in `asyncio.to_thread`, add a small LRU cache, and return the raw results as JSON text for the model to read.

### 46. Background Threads and Signals

**How it is implemented in Lloyd**

- Only the GUI thread touches widgets. The work runs in these places:
  - `VoiceListener`: a `QThread` loop.
  - `Agent` and `LloydSpeaker`: `QThread`s that each host their own `asyncio` loop.
  - `PhoneServerWorker`: a `CancellableWorker`.
  - The Whisper loader: a `threading.Thread`.
  - The Manim render: a separate process through `QProcess`.
- Workers talk to the GUI with `pyqtSignal`. Qt automatically queues signals across threads.
- The GUI calls into worker loops with `asyncio.run_coroutine_threadsafe` and `loop.call_soon_threadsafe`, and shares flags through `threading.Event`.
- `app/threads/cancellable_worker.py`: `run()` calls `do_work()` and always runs `cleanup()` in a `finally` block. `request_stop()` calls `requestInterruption()`.
- `closeEvent` shuts down in a fixed order (listener, canvas, render, agent, speaker), and each worker is joined with a 3-second timeout.

**How to implement it in another project**

```python
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal


class AsyncWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop: asyncio.Event | None = None

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())
        self._loop.close()

    async def _serve(self) -> None:
        self._stop = asyncio.Event()
        await self._stop.wait()

    def submit(self, text: str) -> None:
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._handle(text), self._loop)

    async def _handle(self, text: str) -> None:
        await asyncio.sleep(0.1)
        self.result_ready.emit(text.upper())

    def shutdown(self) -> None:
        if self._loop is not None and self._stop is not None:
            self._loop.call_soon_threadsafe(self._stop.set)
        self.wait(3000)
```

`submit()` works only after the loop has started. Lloyd uses a `threading.Event` ready flag for this.

### 47. Thread Diagnostics and Crash Handling

**How it is implemented in Lloyd**

- `app/core/qthread_support.py`:
  - `install_diagnostics()` turns on `faulthandler` and installs a Qt message handler with `qInstallMessageHandler`. When Qt reports a fatal "QThread destroyed while still running", the handler prints which threads are still running and every stack trace.
  - `track(thread, name)` sets the thread's object name and logs when it is created, started, and finished. Threads are kept in a `WeakSet`.
  - `log_running("closeEvent")` lists the live threads during shutdown.
- In `app/app.py`, the crash hook prints the traceback, closes the window, and calls `os._exit(1)`, so an exception in a slot never leaves zombie threads.

**How to implement it in another project**

- Name every `QThread`, keep a weak registry of them, and install a Qt message handler plus `faulthandler`. Shutdown bugs then become readable logs instead of silent crashes.

### 48. Performance Tracing

**How it is implemented in Lloyd**

- `app/core/perf.py`:
  - `start(label)` begins a traced turn.
  - `mark(stage, once=False)` prints the time since the last mark and since the start, in ms. It also appends a JSON line to `runtime/perf/YYYYMMDD.jsonl`, and a lock keeps it thread-safe.
- Marks are placed across the whole pipeline: `wake.matched`, `stt.decoded`, `agent.query_sent`, `agent.first_text_delta`, `agent.first_sentence`, `tts.first_audio`, `render.start`, `render.done`, `canvas.build_done`, and more.

**How to implement it in another project**

- Add a tiny tracer with `start()` and `mark()` based on `time.perf_counter()`, writing JSON lines. Put marks at each stage boundary to find where latency is spent.

### 49. Model Installer

**How it is implemented in Lloyd**

- `install.py` runs a tuple of `(section title, function)` steps: download the voice, download the Vosk model, download the Whisper model, create the output folder, and create the EXE.
- **Direct downloads:** `download()` streams `urllib` responses in 1 MB chunks into a `.part` file, shows progress, and renames the file only when it is complete. Existing files are skipped, so the installer can be run again safely.
- **Vosk:** the zip is extracted into a staging folder, checked, and then moved into place.
- **Whisper:** `huggingface_hub.snapshot_download(repo, cache_dir="models/whisper", allow_patterns=[...])` downloads only the needed files, into the same cache folder that faster-whisper reads.
- The installer runs on Windows only. Errors print a FAILED section and exit with code 1.

**How to implement it in another project**

- Keep large models out of git. Ship an installer that downloads to `.part` files, renames them when done, skips what already exists, and extracts archives through a staging folder.

### 50. Desktop Launcher (EXE)

**How it is implemented in Lloyd**

- `install_launcher()` in `install.py` fills a small launcher script from a `string.Template`, inserting the paths with `repr()`.
- It builds the script with `uv tool run --from pyinstaller pyinstaller --onefile --windowed --icon icon/Lloyd.ico` in a temporary folder, then copies `Lloyd.exe` to the Desktop. The Desktop path is read from the `User Shell Folders` registry key.
- **The launcher at runtime:**
  - It checks that `.venv\Scripts\python.exe` exists. If it doesn't, it shows a `MessageBoxW` error.
  - It starts `run.py` with `subprocess.Popen` and `CREATE_NO_WINDOW`, and sends the output to `runtime/lloyd.log`.
  - It removes the PyInstaller environment variables (`_MEI*`, `_PYI*`) and calls `SetDllDirectoryW(None)`, so the child Python does not load the bundled DLLs.
- The EXE stays tiny, and the real app stays editable source code.

**How to implement it in another project**

- Instead of freezing the whole app, freeze a small launcher that starts your virtualenv's Python on your entry script without a console window and redirects its output to a log file.