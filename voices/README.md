# How To Add Voices

Lloyd speaks with [Piper](https://github.com/rhasspy/piper) neural voices, which run entirely
on your machine. `en_GB-alan-medium` is installed by `install.py` and is the default. You can
add any other Piper voice and switch to it in `.env`.

## 1. What to download, and from where

All Piper voices are hosted on Hugging Face:

**https://huggingface.co/rhasspy/piper-voices/tree/main/en**

A voice is always a **pair of files**, and you need both:

| File | Purpose |
|---|---|
| `<voice>.onnx` | The voice model (about 60 to 115 MB) |
| `<voice>.onnx.json` | Its configuration: sample rate, speakers, default pacing |

Keep the two file names identical apart from the extra `.json`. Lloyd finds the config by
appending `.json` to the model path.

### Recommended voices

| Voice | Size | Character | Download |
|---|---|---|---|
| `en_GB-alan-medium` | 60 MB | Crisp British, butler-like. **Default** | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json) |
| `en_GB-northern_english_male-medium` | 60 MB | Warm Northern English pub landlord | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json) |
| `en_US-joe-medium` | 60 MB | Deep, calm American | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json) |
| `en_US-norman-medium` | 61 MB | Older and grainier, lots of character | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/norman/medium/en_US-norman-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/norman/medium/en_US-norman-medium.onnx.json) |
| `en_US-hfc_male-medium` | 60 MB | Neutral and warm, very clean | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/hfc_male/medium/en_US-hfc_male-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/hfc_male/medium/en_US-hfc_male-medium.onnx.json) |
| `en_US-ryan-high` | 115 MB | Friendly, higher-quality model | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json) |
| `en_GB-vctk-medium` | 73 MB | 109 speakers in one model | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx.json) |

### Any other voice

Direct download links follow this pattern:

```text
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/{lang}/{name}/{quality}/{lang}-{name}-{quality}.onnx
```

For example, `en_US-joe-medium` has `lang` = `en_US`, `name` = `joe`, and `quality` = `medium`.
Add `.json` to the end of the URL for the config file.

Piper can also download voices for you. Run this from the project root:

```powershell
uv run python -m piper.download_voices en_US-joe-medium --download-dir voices
```

Run it with no voice name to list every available voice.

## 2. Where to put them

Place both files directly in the `voices/` folder at the project root. Subfolders are not
scanned.

```text
lloyd/
└── voices/
    ├── en_GB-alan-medium.onnx
    ├── en_GB-alan-medium.onnx.json
    ├── en_US-joe-medium.onnx            <- new voice
    └── en_US-joe-medium.onnx.json       <- and its config
```

Voice files are gitignored, so each machine keeps its own set.

## 3. Point `.env` at the voice

`.env` is in the project root. If you don't have one yet, copy the template:

```powershell
Copy-Item .env.example .env
```

Set `LLOYD_VOICE` to the voice's file name **without** `.onnx`:

```dotenv
LLOYD_VOICE=en_US-joe-medium
```

That is the only line you need. Restart Lloyd, because `.env` is read once at startup.

If the value is empty, or no voice with that name is in `voices/`, Lloyd falls back to `alan`
(the default voice). If no Piper voice loads at all, it falls back to Microsoft Edge's online
voice.

### Optional tuning

| Key | Default | Meaning |
|---|---|---|
| `LLOYD_VOICE` | `alan` | `alan`, a file name from `voices/` without `.onnx`, or `edge` |
| `LLOYD_VOICE_LENGTH` | `1.0` | Pace. `1.05` is 5% slower. `1.04` to `1.08` suits a bartender |
| `LLOYD_VOICE_NOISE` | `1.0` | Voice variation |
| `LLOYD_VOICE_NOISE_W` | `1.0` | Timing variation. Above `1.0` sounds less robotic |
| `LLOYD_VOICE_VOLUME` | `1.0` | Output gain |
| `LLOYD_VOICE_SPEAKER` | empty | Speaker number, for multi-speaker models only |
| `LLOYD_EDGE_VOICE` | `en-GB-RyanNeural` | Online fallback voice |
| `LLOYD_EDGE_RATE` | `-4%` | Online fallback speaking rate |
| `LLOYD_EDGE_PITCH` | `-2Hz` | Online fallback pitch |

`LENGTH`, `NOISE`, and `NOISE_W` **multiply** the model's own values from its `.onnx.json`, so
`1.0` always means "as the model was trained". Models differ a lot, so start at `1.0` and adjust
in small steps. These values apply only to the selected voice.

For a multi-speaker model, pick a speaker. An out-of-range number falls back to speaker `0`.

```dotenv
LLOYD_VOICE=en_GB-vctk-medium
LLOYD_VOICE_SPEAKER=42
```

To try a voice without editing `.env`, set it for one run from the shell:

```powershell
$env:LLOYD_VOICE = "en_US-norman-medium"; uv run run.py
```

## 4. Full example: switching to `en_US-joe-medium`

**Step 1: Download both files into `voices/`.** From the project root in PowerShell:

```powershell
$base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium"
Invoke-WebRequest -Uri "$base/en_US-joe-medium.onnx"      -OutFile "voices\en_US-joe-medium.onnx"
Invoke-WebRequest -Uri "$base/en_US-joe-medium.onnx.json" -OutFile "voices\en_US-joe-medium.onnx.json"
```

**Step 2: Check that both files arrived.**

```powershell
Get-ChildItem voices
```

```text
en_GB-alan-medium.onnx
en_GB-alan-medium.onnx.json
en_US-joe-medium.onnx
en_US-joe-medium.onnx.json
```

**Step 3: Edit `.env`.** Select the voice and slow it down slightly:

```dotenv
LLOYD_VOICE=en_US-joe-medium
LLOYD_VOICE_LENGTH=1.05
LLOYD_VOICE_NOISE=1.0
LLOYD_VOICE_NOISE_W=1.0
LLOYD_VOICE_VOLUME=1.0
LLOYD_VOICE_SPEAKER=
LLOYD_EDGE_VOICE=en-GB-RyanNeural
LLOYD_EDGE_RATE=-4%
LLOYD_EDGE_PITCH=-2Hz
```

**Step 4: Restart Lloyd and check the log.**

```powershell
uv run run.py
```

The console (or `runtime/lloyd.log` when started from the desktop launcher) shows:

```text
[Lloyd voice]: 2 voice(s) in voices: alan, en_US-joe-medium
[Lloyd voice]: speaking with en_US-joe-medium [piper: en_US-joe-medium.onnx, 22050 Hz, pace 1.05]
```

If you see `voice 'en_US-joe-medium' is not available, using 'alan' instead`, check the
spelling in `.env` against the file name. If you see `missing its config file`, the
`.onnx.json` file is missing or misnamed.

**Tip:** Download two or three candidates and compare them by switching `LLOYD_VOICE` and
restarting. Voices rarely sound the way their names suggest.