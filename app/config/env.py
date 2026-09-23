import os

from dotenv import load_dotenv

from app.config.application import LOG_PREFIX_ERROR
from app.core.paths import PROJECT_ROOT

ENV_FILENAME: str = ".env"

ENV_VOICE_KEY: str = "LLOYD_VOICE"
ENV_VOICE_LENGTH_KEY: str = "LLOYD_VOICE_LENGTH"
ENV_VOICE_NOISE_KEY: str = "LLOYD_VOICE_NOISE"
ENV_VOICE_NOISE_W_KEY: str = "LLOYD_VOICE_NOISE_W"
ENV_VOICE_VOLUME_KEY: str = "LLOYD_VOICE_VOLUME"
ENV_VOICE_SPEAKER_KEY: str = "LLOYD_VOICE_SPEAKER"
ENV_EDGE_VOICE_KEY: str = "LLOYD_EDGE_VOICE"
ENV_EDGE_RATE_KEY: str = "LLOYD_EDGE_RATE"
ENV_EDGE_PITCH_KEY: str = "LLOYD_EDGE_PITCH"

load_dotenv(PROJECT_ROOT / ENV_FILENAME)


def env_value(key: str, default: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        return default
    return value


def env_float(key: str, default: float) -> float:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default

    try:
        return float(raw)
    except ValueError:
        print(f"{LOG_PREFIX_ERROR}: {key}='{raw}' is not a number, using {default}")
        return default


def env_int(key: str) -> int | None:
    raw = os.getenv(key, "").strip()
    if not raw:
        return None

    try:
        return int(raw)
    except ValueError:
        print(f"{LOG_PREFIX_ERROR}: {key}='{raw}' is not a whole number, ignoring")
        return None