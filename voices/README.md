## Setting the voice

Lloyd scans this folder at startup and logs what it found:

    [Lloyd voice]: 7 voice(s) in voices: alan, barkeep, hfc, joe, norman, ryan_high, vctk

Pick one with `LLOYD_VOICE` in `.env`, which is gitignored and per-machine:

    LLOYD_VOICE=hfc

The value is a short alias from `TTS_VOICE_ALIASES`, or the bare filename stem of any `.onnx`
in this folder:

    LLOYD_VOICE=en_US-hfc_male-medium

With no `.env`, or an empty value, Lloyd uses `TTS_VOICE_DEFAULT_ID` (`alan`). A real shell
variable overrides `.env`, which is handy for one-off tests:

    $env:LLOYD_VOICE = "norman"; uv run python test.py

Restart Lloyd after editing `.env` — it is read once at import.

## Adding a voice

Drop the `.onnx` + `.onnx.json` pair into this folder. That is all that is required — it is
picked up at the next startup and selectable by its filename stem.

Optionally, in `app/config/speech.py`:

- `TTS_VOICE_ALIASES` gives it a short name: `"gruff": "en_US-norman-medium"`
- `TTS_VOICE_TUNING` adjusts delivery, keyed by filename stem

### Tuning keys

Tuning is **relative to the model's own values**, read from its `.onnx.json` at startup. This
matters because natives differ: `en_US-hfc_male-medium` ships at `length_scale 0.8` and
`en_GB-vctk-medium` at `1.4`, so an absolute number that suits one ruins the other.

| Key | Meaning |
|---|---|
| `length_multiplier`  | Pace. `1.06` is 6% slower than the model's natural pace. 1.04-1.08 suits a bartender |
| `noise_w_multiplier` | Phoneme-width jitter. Slightly above 1.0 sounds less robotic |
| `noise_multiplier`   | Generator noise |
| `volume`             | Absolute output multiplier, not relative |
| `speaker`            | Speaker index, multi-speaker models only. Validated against the model's real speaker count |

Omit a key and the model's own value is used unchanged.