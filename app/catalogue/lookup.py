import json
import re

from thefuzz import process as fuzzy_process

from app.config import (
    CATALOGUE_DIR, CATALOGUE_ENABLED, CATALOGUE_INTENT_PATTERN,
    CATALOGUE_MATCH_THRESHOLD, CATALOGUE_MAX_MESSAGE_WORDS, CATALOGUE_SKIP_PATTERN,
    CATALOGUE_SOURCES_FILE, LOG_PREFIX_ERROR,
)
from app.core.paths import PROJECT_ROOT

_entries: dict[str, dict] = {}
_names: list[str] = []
_loaded: bool = False

_INTENT = re.compile(CATALOGUE_INTENT_PATTERN, re.IGNORECASE)
_SKIP = re.compile(CATALOGUE_SKIP_PATTERN, re.IGNORECASE)


def entry_keys(entry: dict) -> list[str]:
    keys = [str(entry.get("name", ""))]
    keys.extend(str(alias) for alias in entry.get("aliases", []) or [])
    return [key.strip().lower() for key in keys if key and key.strip()]


def load_entries() -> int:
    global _loaded

    _entries.clear()
    _names.clear()

    directory = PROJECT_ROOT / CATALOGUE_DIR
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            if path.name == CATALOGUE_SOURCES_FILE:
                continue
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"{LOG_PREFIX_ERROR}: bad catalogue entry {path}: {exc}")
                continue
            if not isinstance(entry, dict):
                continue
            for key in entry_keys(entry):
                _entries[key] = entry

    _names.extend(sorted(_entries))
    _loaded = True
    return len(_names)


def strip_intent(text: str) -> str:
    return _INTENT.sub(" ", text).strip(" ?.!,")


def find_entry(message: str) -> dict | None:
    if not CATALOGUE_ENABLED:
        return None
    if not _loaded:
        load_entries()
    if not _names:
        return None

    text = message.strip().lower()
    if not text:
        return None
    if len(text.split()) > CATALOGUE_MAX_MESSAGE_WORDS:
        return None
    if _SKIP.search(text):
        return None
    if not _INTENT.search(text):
        return None

    probe = strip_intent(text)
    if not probe:
        return None

    match = fuzzy_process.extractOne(probe, _names)
    if match is None:
        return None
    if match[1] < CATALOGUE_MATCH_THRESHOLD:
        return None

    return _entries.get(match[0])
