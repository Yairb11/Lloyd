from app.config.env import ENV_VOICE_KEY, env_value

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

TTS_VOICES_DIR: str = "voices"
TTS_VOICE_MODEL_EXTENSION: str = ".onnx"
TTS_VOICE_CONFIG_SUFFIX: str = ".json"

TTS_VOICE_DEFAULT_ID: str = "alan"
TTS_VOICE_ID: str = env_value(ENV_VOICE_KEY, TTS_VOICE_DEFAULT_ID)
TTS_VOICE_FALLBACK_ID: str = TTS_VOICE_DEFAULT_ID

TTS_VOICE_ALIASES: dict[str, str] = {
    "alan": "en_GB-alan-medium",
    "barkeep": "en_GB-northern_english_male-medium",
    "hfc": "en_US-hfc_male-medium",
    "joe": "en_US-joe-medium",
    "norman": "en_US-norman-medium",
    "ryan_high": "en_US-ryan-high",
    "vctk": "en_GB-vctk-medium",
}

TTS_VOICE_TUNING: dict[str, dict] = {
    "en_GB-northern_english_male-medium": {
        "length_multiplier": 1.06,
        "noise_w_multiplier": 1.06,
    },
    "en_US-joe-medium": {
        "length_multiplier": 1.05,
    },
    "en_US-norman-medium": {
        "length_multiplier": 1.08,
        "noise_w_multiplier": 1.06,
    },
    "en_US-ryan-high": {
        "length_multiplier": 1.04,
    },
    "en_US-hfc_male-medium": {
        "length_multiplier": 1.05,
    },
    "en_GB-vctk-medium": {
        "speaker": 0,
    },
}

TTS_VOICE_DEFAULT_LENGTH_MULTIPLIER: float = 1.0
TTS_VOICE_DEFAULT_NOISE_MULTIPLIER: float = 1.0
TTS_VOICE_DEFAULT_NOISE_W_MULTIPLIER: float = 1.0
TTS_VOICE_DEFAULT_VOLUME: float = 1.0

TTS_EDGE_VOICES: dict[str, dict] = {
    "connor": {
        "voice": "en-IE-ConnorNeural",
        "rate": "-6%",
        "pitch": "-3Hz",
    },
    "ryan": {
        "voice": "en-GB-RyanNeural",
        "rate": "-4%",
        "pitch": "-2Hz",
    },
}

TTS_EDGE_DEFAULT_VOICE: str = "en-GB-RyanNeural"
TTS_EDGE_DEFAULT_RATE: str = "-4%"
TTS_EDGE_DEFAULT_PITCH: str = "-2Hz"

TTS_PIPER_FALLBACK_SAMPLE_RATE: int = 22050
TTS_PIPER_DEFAULT_LENGTH_SCALE: float = 1.0
TTS_PIPER_DEFAULT_NOISE_SCALE: float = 0.667
TTS_PIPER_DEFAULT_NOISE_W: float = 0.8

TTS_WARMUP_TEXT: str = "Ready."
TTS_POLL_INTERVAL_MS: int = 50
TTS_INTER_SENTENCE_SILENCE_MS: int = 120
TTS_AUDIO_BLOCK_FRAMES: int = 512
TTS_AMPLITUDE_NORMALIZATION_PEAK: float = 6000.0