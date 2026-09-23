import re
from thefuzz import fuzz

from app.config import (
    SPEECH_CELSIUS_PATTERN, SPEECH_CELSIUS_REPLACEMENT, SPEECH_CL_PATTERN,
    SPEECH_CL_REPLACEMENT, SPEECH_FRACTION_REPLACEMENTS, SPEECH_ML_PATTERN,
    SPEECH_ML_REPLACEMENT, SPEECH_NUMBER_RANGE_PATTERN, SPEECH_NUMBER_RANGE_REPLACEMENT,
    SPEECH_OZ_PATTERN, SPEECH_OZ_REPLACEMENT, SPEECH_SENTENCE_SPLIT_PATTERN,
    SPEECH_STRIP_EMOJI_PATTERN, SPEECH_STRIP_MARKDOWN_PATTERN, VOICE_COMMAND_PUNCTUATION_PATTERN,
    VOICE_WAKE_GREETINGS, VOICE_WAKE_GREETING_MATCH_THRESHOLD, VOICE_WAKE_KEYWORD_MATCH_THRESHOLD,
    VOICE_WAKE_KEYWORD_VARIANTS,
)


def clean_text_for_speech(text: str) -> str:
    text = re.sub(SPEECH_STRIP_MARKDOWN_PATTERN, "", text)
    text = re.sub(SPEECH_STRIP_EMOJI_PATTERN, "", text)

    for frac, replacement in SPEECH_FRACTION_REPLACEMENTS.items():
        text = re.sub(rf"\b{re.escape(frac)}\b", replacement, text)

    text = re.sub(SPEECH_ML_PATTERN, SPEECH_ML_REPLACEMENT, text, flags=re.IGNORECASE)
    text = re.sub(SPEECH_CL_PATTERN, SPEECH_CL_REPLACEMENT, text, flags=re.IGNORECASE)
    text = re.sub(SPEECH_OZ_PATTERN, SPEECH_OZ_REPLACEMENT, text, flags=re.IGNORECASE)

    text = re.sub(SPEECH_NUMBER_RANGE_PATTERN, SPEECH_NUMBER_RANGE_REPLACEMENT, text)
    text = re.sub(SPEECH_CELSIUS_PATTERN, SPEECH_CELSIUS_REPLACEMENT, text)

    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    sentences = re.split(SPEECH_SENTENCE_SPLIT_PATTERN, text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def sanitize_cocktail_filename(name: str) -> str:
    clean_name = re.sub(r"[^\w\s]", "", name)
    return "".join(word.capitalize() for word in clean_name.split())


def best_match_score(word: str, candidates: tuple[str, ...]) -> int:
    return max(fuzz.ratio(candidate, word) for candidate in candidates)


def is_wake_keyword(word: str) -> bool:
    return best_match_score(word, VOICE_WAKE_KEYWORD_VARIANTS) >= VOICE_WAKE_KEYWORD_MATCH_THRESHOLD


def is_wake_greeting(word: str) -> bool:
    return best_match_score(word, VOICE_WAKE_GREETINGS) >= VOICE_WAKE_GREETING_MATCH_THRESHOLD


def strip_wake_prefix(words: list[str]) -> list[str]:
    index = 0
    while index < len(words) and (is_wake_greeting(words[index]) or is_wake_keyword(words[index])):
        index += 1
    return words[index:]


def normalize_voice_command(text: str) -> str:
    words = re.sub(VOICE_COMMAND_PUNCTUATION_PATTERN, " ", text.lower()).split()
    return " ".join(strip_wake_prefix(words))