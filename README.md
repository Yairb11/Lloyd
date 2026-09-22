# Lloyd

A fully local-first, voice-activated mixology assistant.

## Voice input setup

Lloyd needs **one** model on disk before voice input works: the small Vosk model
used for always-on wake-word listening. It is a data model, not a Python
package, so `uv sync` cannot install it.

| Purpose | Model | Size | Config |
|---|---|---|---|
| Wake word (always listening) | `vosk-model-small-en-us-0.15` | ~40 MB | `VOICE_VOSK_WAKE_MODEL_DIR` |

From the repo root, in PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path models
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "models\vosk-model-small-en-us-0.15.zip"
Expand-Archive -Path "models\vosk-model-small-en-us-0.15.zip" -DestinationPath "models"
Remove-Item "models\vosk-model-small-en-us-0.15.zip"
