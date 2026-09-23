import os

from dotenv import load_dotenv

from app.core.paths import PROJECT_ROOT

ENV_FILENAME: str = ".env"
ENV_VOICE_KEY: str = "LLOYD_VOICE"

load_dotenv(PROJECT_ROOT / ENV_FILENAME)


def env_value(key: str, default: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        return default
    return value