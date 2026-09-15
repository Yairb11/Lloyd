# Lloyd

## Voice input setup: Vosk speech models

Lloyd's wake-word listener (`app/threads/voice_listener.py`) needs **two** Vosk speech recognition models on disk before voice input will work — one small model for always-on wake-word listening, one much larger/more accurate model used briefly for transcribing your actual command after the wake word fires. Both are one-time manual downloads — they're data models, not Python packages, so `uv sync`/`pip` can't install them for you.

| Purpose | Model | Size | Used by |
|---|---|---|---|
| Wake-word (always listening) | `vosk-model-small-en-us-0.15` | ~40MB | `VOICE_VOSK_WAKE_MODEL_DIR` |
| Command transcription (brief, after wake word) | `vosk-model-en-us-0.22` | ~1.8GB | `VOICE_VOSK_COMMAND_MODEL_DIR` |

The command model is the full accurate model, not the smaller `-lgraph` middle-ground variant — chosen deliberately for maximum transcription accuracy, at the cost of a much bigger download and a noticeably larger memory footprint while the app is running (it's loaded once and stays resident, not reloaded per command). If that tradeoff turns out to be too much, the `-lgraph` variant (128MB, still meaningfully better than the small model) is a straightforward one-line swap of `VOICE_VOSK_COMMAND_MODEL_DIR`.

Both come from the official model list: https://alphacephei.com/vosk/models

### 1. Download both models

From the repo root, in PowerShell. **The command model is a ~1.8GB download — this will take a while on most connections.**

```powershell
New-Item -ItemType Directory -Force -Path models
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "models\vosk-model-small-en-us-0.15.zip"
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip" -OutFile "models\vosk-model-en-us-0.22.zip"