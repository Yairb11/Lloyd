import re

from app.config import (
    SPEECH_CELSIUS_PATTERN,
    SPEECH_CELSIUS_REPLACEMENT,
    SPEECH_CL_PATTERN,
    SPEECH_CL_REPLACEMENT,
    SPEECH_FRACTION_REPLACEMENTS,
    SPEECH_ML_PATTERN,
    SPEECH_ML_REPLACEMENT,
    SPEECH_NUMBER_RANGE_PATTERN,
    SPEECH_NUMBER_RANGE_REPLACEMENT,
    SPEECH_OZ_PATTERN,
    SPEECH_OZ_REPLACEMENT,
    SPEECH_SENTENCE_SPLIT_PATTERN,
    SPEECH_STRIP_EMOJI_PATTERN,
    SPEECH_STRIP_MARKDOWN_PATTERN,
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
