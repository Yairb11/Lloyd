SPEECH_STRIP_MARKDOWN_PATTERN: str = r"[\*#_`~]"
SPEECH_STRIP_EMOJI_PATTERN: str = r"[\U00010000-\U0010ffff]"
SPEECH_FRACTION_REPLACEMENTS: dict[str, str] = {
    "1/2": "half",
    "1/4": "quarter",
    "3/4": "three quarters",
    "1/3": "one third",
    "2/3": "two thirds",
}
SPEECH_ML_PATTERN: str = r"(\d+(?:\.\d+)?)\s*ml\b"
SPEECH_ML_REPLACEMENT: str = r"\1 milliliters"
SPEECH_CL_PATTERN: str = r"(\d+(?:\.\d+)?)\s*cl\b"
SPEECH_CL_REPLACEMENT: str = r"\1 centiliters"
SPEECH_OZ_PATTERN: str = r"(\d+(?:\.\d+)?)\s*oz\b"
SPEECH_OZ_REPLACEMENT: str = r"\1 ounces"
SPEECH_NUMBER_RANGE_PATTERN: str = r"(\d+)\s*-\s*(\d+)"
SPEECH_NUMBER_RANGE_REPLACEMENT: str = r"\1 to \2"
SPEECH_CELSIUS_PATTERN: str = r"(\d+)\s*°\s*C"
SPEECH_CELSIUS_REPLACEMENT: str = r"\1 degrees Celsius"
SPEECH_SENTENCE_SPLIT_PATTERN: str = r"(?<=[.!?])\s+"

TTS_ENGINE_PIPER: str = "piper"
TTS_ENGINE_EDGE: str = "edge"
TTS_ENGINE: str = TTS_ENGINE_PIPER

TTS_PIPER_MODEL_PATH: str = "models/piper/en_GB-alan-medium.onnx"
TTS_PIPER_FALLBACK_SAMPLE_RATE: int = 22050

TTS_VOICE: str = "en-GB-RyanNeural"
TTS_RATE: str = "-4%"
TTS_PITCH: str = "-2Hz"

TTS_WARMUP_TEXT: str = "Ready."
TTS_POLL_INTERVAL_MS: int = 50
TTS_INTER_SENTENCE_SILENCE_MS: int = 120
TTS_AUDIO_BLOCK_FRAMES: int = 512
TTS_AMPLITUDE_NORMALIZATION_PEAK: float = 6000.0
