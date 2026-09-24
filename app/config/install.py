INSTALL_APP_NAME: str = "Lloyd"
INSTALL_ICON_PATH: str = "icon/Lloyd.ico"
INSTALL_ENTRY_SCRIPT: str = "run.py"
INSTALL_VENV_PYTHON: str = ".venv/Scripts/python.exe"
INSTALL_LOG_FILE: str = "runtime/lloyd.log"

INSTALL_PIPER_VOICE_BASE_URL: str = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium"
)
INSTALL_VOSK_BASE_URL: str = "https://alphacephei.com/vosk/models"

INSTALL_WHISPER_REPO_ID: str = "Systran/faster-distil-whisper-small.en"
INSTALL_WHISPER_FILE_PATTERNS: tuple[str, ...] = (
    "config.json",
    "preprocessor_config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.*",
)

INSTALL_DOWNLOAD_CHUNK_BYTES: int = 1024 * 1024
INSTALL_DOWNLOAD_TIMEOUT_S: float = 60.0
INSTALL_DOWNLOAD_USER_AGENT: str = "Lloyd-Installer"
INSTALL_PARTIAL_SUFFIX: str = ".part"
INSTALL_STAGING_SUFFIX: str = ".extracting"
INSTALL_ARCHIVE_SUFFIX: str = ".zip"
INSTALL_BYTES_PER_MB: float = 1024.0 * 1024.0

INSTALL_PYINSTALLER_PACKAGE: str = "pyinstaller"
INSTALL_PYINSTALLER_COMMAND: str = "pyinstaller"
INSTALL_PYINSTALLER_LOG_LEVEL: str = "WARN"
INSTALL_UV_COMMAND: str = "uv"
INSTALL_BUILD_DIR_PREFIX: str = "lloyd_build_"
INSTALL_EXECUTABLE_SUFFIX: str = ".exe"

INSTALL_SHELL_FOLDERS_KEY: str = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
)
INSTALL_DESKTOP_VALUE: str = "Desktop"
INSTALL_DESKTOP_FALLBACK: str = "Desktop"

INSTALL_SECTION_VOICE: str = "DOWNLOAD VOICE"
INSTALL_SECTION_VOSK: str = "DOWNLOAD VOSK MODEL"
INSTALL_SECTION_WHISPER: str = "DOWNLOAD WHISPER MODEL"
INSTALL_SECTION_OUTPUT: str = "CREATING OUTPUT FOLDER"
INSTALL_SECTION_EXE: str = "CREATING EXE"
INSTALL_SECTION_DONE: str = "DONE"
INSTALL_SECTION_FAILED: str = "FAILED"

INSTALL_SECTION_FILL: str = "-"
INSTALL_SECTION_LEAD: int = 10
INSTALL_SECTION_WIDTH: int = 60
INSTALL_DETAIL_INDENT: str = "  "