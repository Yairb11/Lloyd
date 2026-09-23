import json
from pathlib import Path

from app.config import (
    LOG_PREFIX_ERROR, LOG_PREFIX_VOICE, TTS_EDGE_PITCH,
    TTS_EDGE_RATE, TTS_EDGE_VOICE, TTS_ENGINE_EDGE,
    TTS_ENGINE_PIPER, TTS_PIPER_DEFAULT_LENGTH_SCALE, TTS_PIPER_DEFAULT_NOISE_SCALE,
    TTS_PIPER_DEFAULT_NOISE_W, TTS_PIPER_FALLBACK_SAMPLE_RATE, TTS_VOICE_CONFIG_SUFFIX,
    TTS_VOICE_DEFAULT_ID, TTS_VOICE_DEFAULT_MODEL, TTS_VOICE_DEFAULT_VOLUME,
    TTS_VOICE_ID, TTS_VOICE_LENGTH_MULTIPLIER, TTS_VOICE_MODEL_EXTENSION,
    TTS_VOICE_NEUTRAL_MULTIPLIER, TTS_VOICE_NOISE_MULTIPLIER, TTS_VOICE_NOISE_W_MULTIPLIER,
    TTS_VOICE_SPEAKER, TTS_VOICE_VOLUME, TTS_VOICES_DIR,
)
from app.core.paths import PROJECT_ROOT


class VoiceSpec:
    def __init__(
        self,
        voice_id: str,
        engine: str,
        model_path: Path | None = None,
        config_path: Path | None = None,
        speaker_id: int | None = None,
        length_scale: float | None = None,
        noise_scale: float | None = None,
        noise_w_scale: float | None = None,
        volume: float = TTS_VOICE_DEFAULT_VOLUME,
        sample_rate: int = TTS_PIPER_FALLBACK_SAMPLE_RATE,
        num_speakers: int = 1,
        language: str = "",
        quality: str = "",
        edge_voice: str = TTS_EDGE_VOICE,
        edge_rate: str = TTS_EDGE_RATE,
        edge_pitch: str = TTS_EDGE_PITCH,
    ) -> None:
        self.voice_id = voice_id
        self.engine = engine
        self.model_path = model_path
        self.config_path = config_path
        self.speaker_id = speaker_id
        self.length_scale = length_scale
        self.noise_scale = noise_scale
        self.noise_w_scale = noise_w_scale
        self.volume = volume
        self.sample_rate = sample_rate
        self.num_speakers = num_speakers
        self.language = language
        self.quality = quality
        self.edge_voice = edge_voice
        self.edge_rate = edge_rate
        self.edge_pitch = edge_pitch


class VoiceCatalog:
    def __init__(self, voices: dict[str, VoiceSpec], directory: Path) -> None:
        self.voices = voices
        self.directory = directory

    def get(self, voice_id: str) -> VoiceSpec | None:
        return self.voices.get(voice_id)

    def ids(self) -> list[str]:
        return sorted({spec.voice_id for spec in self.voices.values()})

    def piper_ids(self) -> list[str]:
        return sorted(
            {
                spec.voice_id
                for spec in self.voices.values()
                if spec.engine == TTS_ENGINE_PIPER
            }
        )

    def summary(self) -> str:
        found = self.piper_ids()
        if not found:
            return f"no voice models found in {self.directory}"
        return f"{len(found)} voice(s) in {self.directory.name}: {', '.join(found)}"


_catalog: VoiceCatalog | None = None


def voices_dir() -> Path:
    return PROJECT_ROOT / TTS_VOICES_DIR


def discover_voice_files() -> dict[str, Path]:
    directory = voices_dir()
    if not directory.is_dir():
        return {}

    found: dict[str, Path] = {}
    for path in sorted(directory.glob(f"*{TTS_VOICE_MODEL_EXTENSION}")):
        found[path.name[: -len(TTS_VOICE_MODEL_EXTENSION)]] = path
    return found


def build_catalog() -> VoiceCatalog:
    voices: dict[str, VoiceSpec] = {}

    for stem, model_path in discover_voice_files().items():
        voice_id = TTS_VOICE_DEFAULT_ID if stem == TTS_VOICE_DEFAULT_MODEL else stem
        spec = _piper_spec(voice_id, stem, model_path)
        if spec is None:
            continue
        voices[voice_id] = spec
        voices[stem] = spec

    if TTS_ENGINE_EDGE not in voices:
        voices[TTS_ENGINE_EDGE] = edge_fallback_voice()

    return VoiceCatalog(voices, voices_dir())


def load_catalog(refresh: bool = False) -> VoiceCatalog:
    global _catalog
    if _catalog is None or refresh:
        _catalog = build_catalog()
        print(f"{LOG_PREFIX_VOICE}: {_catalog.summary()}")
    return _catalog


def available_voice_ids() -> list[str]:
    return load_catalog().ids()


def resolve_voice(voice_id: str | None = None) -> VoiceSpec:
    catalog = load_catalog()
    requested = (voice_id or TTS_VOICE_ID).strip()

    for candidate in _candidate_ids(requested, catalog):
        spec = catalog.get(candidate)
        if spec is None:
            continue
        if candidate != requested:
            print(
                f"{LOG_PREFIX_ERROR}: voice '{requested}' is not available, "
                f"using '{spec.voice_id}' instead"
            )
        return spec

    print(
        f"{LOG_PREFIX_ERROR}: no voice models found in {catalog.directory}, "
        f"falling back to {TTS_ENGINE_EDGE} tts"
    )
    return edge_fallback_voice()


def edge_fallback_voice() -> VoiceSpec:
    return VoiceSpec(
        voice_id=TTS_ENGINE_EDGE,
        engine=TTS_ENGINE_EDGE,
        edge_voice=TTS_EDGE_VOICE,
        edge_rate=TTS_EDGE_RATE,
        edge_pitch=TTS_EDGE_PITCH,
    )


def describe_voice(voice: VoiceSpec) -> str:
    if voice.engine == TTS_ENGINE_EDGE:
        return f"{voice.voice_id} [{TTS_ENGINE_EDGE}: {voice.edge_voice}]"

    name = voice.model_path.name if voice.model_path is not None else "?"
    details = [f"{voice.sample_rate} Hz"]
    if voice.length_scale is not None:
        details.append(f"pace {voice.length_scale:.2f}")
    if voice.speaker_id is not None:
        details.append(f"speaker {voice.speaker_id} of {voice.num_speakers}")
    return f"{voice.voice_id} [{TTS_ENGINE_PIPER}: {name}, {', '.join(details)}]"


def _candidate_ids(requested: str, catalog: VoiceCatalog):
    seen: set[str] = set()
    ordered = (requested, TTS_VOICE_DEFAULT_ID, *catalog.piper_ids(), TTS_ENGINE_EDGE)
    for candidate in ordered:
        if candidate and candidate not in seen:
            seen.add(candidate)
            yield candidate


def _piper_spec(voice_id: str, stem: str, model_path: Path) -> VoiceSpec | None:
    config_path = Path(f"{model_path}{TTS_VOICE_CONFIG_SUFFIX}")
    if not config_path.is_file():
        print(
            f"{LOG_PREFIX_ERROR}: voice '{stem}' is missing its config file "
            f"{config_path.name}, skipping"
        )
        return None

    metadata = _read_metadata(config_path)
    selected = TTS_VOICE_ID in (voice_id, stem)

    length = metadata["length_scale"] * _multiplier(selected, TTS_VOICE_LENGTH_MULTIPLIER)
    noise = metadata["noise_scale"] * _multiplier(selected, TTS_VOICE_NOISE_MULTIPLIER)
    noise_w = metadata["noise_w"] * _multiplier(selected, TTS_VOICE_NOISE_W_MULTIPLIER)
    volume = TTS_VOICE_VOLUME if selected else TTS_VOICE_DEFAULT_VOLUME

    return VoiceSpec(
        voice_id=voice_id,
        engine=TTS_ENGINE_PIPER,
        model_path=model_path,
        config_path=config_path,
        speaker_id=_speaker_id(stem, selected, metadata["num_speakers"]),
        length_scale=length,
        noise_scale=noise,
        noise_w_scale=noise_w,
        volume=volume,
        sample_rate=metadata["sample_rate"],
        num_speakers=metadata["num_speakers"],
        language=metadata["language"],
        quality=metadata["quality"],
    )


def _multiplier(selected: bool, value: float) -> float:
    if selected:
        return value
    return TTS_VOICE_NEUTRAL_MULTIPLIER


def _read_metadata(config_path: Path) -> dict:
    data: dict = {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"{LOG_PREFIX_ERROR}: could not read {config_path.name}: {exc}")

    audio = data.get("audio", {})
    inference = data.get("inference", {})
    language = data.get("language", {})

    return {
        "sample_rate": audio.get("sample_rate", TTS_PIPER_FALLBACK_SAMPLE_RATE),
        "quality": audio.get("quality", ""),
        "num_speakers": data.get("num_speakers", 1),
        "language": language.get("code", ""),
        "length_scale": inference.get("length_scale", TTS_PIPER_DEFAULT_LENGTH_SCALE),
        "noise_scale": inference.get("noise_scale", TTS_PIPER_DEFAULT_NOISE_SCALE),
        "noise_w": inference.get("noise_w", TTS_PIPER_DEFAULT_NOISE_W),
    }


def _speaker_id(stem: str, selected: bool, num_speakers: int) -> int | None:
    if num_speakers < 2:
        return None

    speaker = TTS_VOICE_SPEAKER if selected else None
    if speaker is None:
        return 0

    if 0 <= speaker < num_speakers:
        return speaker

    print(
        f"{LOG_PREFIX_ERROR}: voice '{stem}' has {num_speakers} speakers, "
        f"speaker {speaker} is out of range, using 0"
    )
    return 0