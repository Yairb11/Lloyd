# Lloyd's voices

Every voice Lloyd can speak with lives in this folder. `en_GB-alan-medium` is the one the
application ships with: it is the default and the fallback whenever anything else is
unavailable. Every other voice is a per-machine choice made in `.env` — nothing about it is
written into the application's code or config.

Model files are gitignored. A voice is always a **pair**, and both files are required:

    en_US-hfc_male-medium.onnx
    en_US-hfc_male-medium.onnx.json

The names must match, because Piper finds the config by appending `.json` to the model path.

## 1. Download a voice

Browse every English voice: https://huggingface.co/rhasspy/piper-voices/tree/main/en

Download both files of a pair into this folder. These are good bartender candidates:

| Voice | Size | Character | Links |
|---|---|---|---|
| `en_GB-northern_english_male-medium` | 60 MB | Northern English pub-landlord warmth. The pick. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json) |
| `en_US-joe-medium` | 60 MB | Deep, calm American male. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json) |
| `en_US-norman-medium` | 61 MB | Older and grainier, lots of character. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/norman/medium/en_US-norman-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/norman/medium/en_US-norman-medium.onnx.json) |
| `en_US-ryan-high` | 115 MB | Cleaner `high` quality, friendly mid-range. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json) |
| `en_US-hfc_male-medium` | 60 MB | Neutral and warm, very clean. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/hfc_male/medium/en_US-hfc_male-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/hfc_male/medium/en_US-hfc_male-medium.onnx.json) |
| `en_GB-vctk-medium` | 73 MB | Multi-speaker, 109 voices in one file. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx.json) |
| `en_GB-alan-medium` | 60 MB | Ships with the app. Crisp RP, reads as butler. | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx) · [.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json) |

For any other voice, the URL pattern is:

    .../resolve/main/{family}/{lang}/{name}/{quality}/{lang}-{name}-{quality}.onnx

so `en_US-joe-medium` becomes `.../main/en/en_US/joe/medium/en_US-joe-medium.onnx`.

Piper can also fetch them for you, and lists every voice it knows when given no arguments:

    uv run python -m piper.download_voices en_US-joe-medium --download-dir voices
    uv run python -m piper.download_voices

## 2. Point `.env` at it

`.env` sits in the project root and is gitignored, so your choice stays on your machine.
Set `LLOYD_VOICE` to the **filename stem** — the name without `.onnx`:

    LLOYD_VOICE=en_US-joe-medium

That is the only required line. Restart Lloyd and it will speak with that voice.

On startup Lloyd scans this folder and logs what it found, so you can check the name:

    [Lloyd voice]: 7 voice(s) in voices: alan, en_GB-northern_english_male-medium, ...
    [Lloyd voice]: speaking with en_US-joe-medium [piper: en_US-joe-medium.onnx, 22050 Hz, pace 1.05]

With no `.env`, an empty value, or a name that is not there, Lloyd uses `alan`.

## 3. Adjust the timing

A bartender talking you through a build is unhurried, so most voices want slowing down a
little:

    LLOYD_VOICE=en_US-joe-medium
    LLOYD_VOICE_LENGTH=1.05

`1.04`-`1.08` suits a bartender. Above about `1.15` it starts to sound drugged.

### All keys

| Key | Default | Meaning |
|---|---|---|
| `LLOYD_VOICE`         | `alan`             | `alan`, a filename stem from this folder, or `edge` |
| `LLOYD_VOICE_LENGTH`  | `1.0`              | Pace. `1.05` is 5% slower than the model's natural pace |
| `LLOYD_VOICE_NOISE`   | `1.0`              | Generator noise |
| `LLOYD_VOICE_NOISE_W` | `1.0`              | Phoneme-width jitter; above 1.0 sounds less robotic |
| `LLOYD_VOICE_VOLUME`  | `1.0`              | Output gain. Absolute, not a multiplier |
| `LLOYD_VOICE_SPEAKER` | unset              | Speaker index, multi-speaker models only |
| `LLOYD_EDGE_VOICE`    | `en-GB-RyanNeural` | Cloud voice, used when Piper cannot load |
| `LLOYD_EDGE_RATE`     | `-4%`              | |
| `LLOYD_EDGE_PITCH`    | `-2Hz`             | |

The four timing keys are **multipliers of the model's own values**, read from its
`.onnx.json` at startup. That matters because natives differ a lot —
`en_US-hfc_male-medium` ships at `length_scale 0.8` and `en_GB-vctk-medium` at `1.4` — so an
absolute number that suits one model ruins another. `1.0` always means "leave this model
alone". They apply only to the voice you selected.

A multi-speaker model needs a speaker index:

    LLOYD_VOICE=en_GB-vctk-medium
    LLOYD_VOICE_SPEAKER=42

Out-of-range values are reported and fall back to speaker 0.

A real shell variable overrides `.env`, which is handy for trying one without editing the
file:

    $env:LLOYD_VOICE = "en_US-norman-medium"; uv run python run.py

Restart Lloyd after editing `.env` — it is read once at import.

## Auditioning

Download two or three candidates, then try each by changing `LLOYD_VOICE` and restarting.
Picking by description is a waste of time — they sound quite different from what the name
suggests.