from app.config import TTS_VOLUME_MIN_DB, TTS_VOLUME_PERCENT_MAX, TTS_VOLUME_PERCENT_MIN

_AMPLITUDE_DECIBEL_FACTOR: float = 20.0


def percent_to_gain(percent: int) -> float:
    if percent <= TTS_VOLUME_PERCENT_MIN:
        return 0.0
    span = TTS_VOLUME_PERCENT_MAX - TTS_VOLUME_PERCENT_MIN
    fraction = min(percent - TTS_VOLUME_PERCENT_MIN, span) / span
    decibels = TTS_VOLUME_MIN_DB * (1.0 - fraction)
    return 10.0 ** (decibels / _AMPLITUDE_DECIBEL_FACTOR)