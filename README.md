# Lloyd

## Voice input setup: Vosk speech model

Lloyd's wake-word listener (`app/threads/voice_listener.py`) needs a Vosk speech recognition model on disk before voice input will work. This is a one-time manual step — it's a data model, not a Python package, so `uv sync`/`pip` can't install it for you.

### 1. Download the model

Get `vosk-model-small-en-us-0.15.zip` (~40MB, Apache 2.0 licensed) from the official model list:

https://alphacephei.com/vosk/models

Or download it directly from the repo root in PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path models
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "models\vosk-model-small-en-us-0.15.zip"