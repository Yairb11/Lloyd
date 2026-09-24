import os
import shutil
import string
import subprocess
import sys
import tempfile
import urllib.request
import winreg
import zipfile
from collections.abc import Callable
from pathlib import Path

from huggingface_hub import snapshot_download

from app.config.install import (
    INSTALL_APP_NAME, INSTALL_ARCHIVE_SUFFIX, INSTALL_BUILD_DIR_PREFIX,
    INSTALL_BYTES_PER_MB, INSTALL_DESKTOP_FALLBACK, INSTALL_DESKTOP_VALUE,
    INSTALL_DETAIL_INDENT, INSTALL_DOWNLOAD_CHUNK_BYTES, INSTALL_DOWNLOAD_TIMEOUT_S,
    INSTALL_DOWNLOAD_USER_AGENT, INSTALL_ENTRY_SCRIPT, INSTALL_EXECUTABLE_SUFFIX,
    INSTALL_ICON_PATH, INSTALL_LOG_FILE, INSTALL_PARTIAL_SUFFIX,
    INSTALL_PIPER_VOICE_BASE_URL, INSTALL_PYINSTALLER_COMMAND, INSTALL_PYINSTALLER_LOG_LEVEL,
    INSTALL_PYINSTALLER_PACKAGE, INSTALL_SECTION_DONE, INSTALL_SECTION_EXE,
    INSTALL_SECTION_FAILED, INSTALL_SECTION_FILL, INSTALL_SECTION_LEAD,
    INSTALL_SECTION_OUTPUT, INSTALL_SECTION_VOICE, INSTALL_SECTION_VOSK,
    INSTALL_SECTION_WHISPER, INSTALL_SECTION_WIDTH, INSTALL_SHELL_FOLDERS_KEY,
    INSTALL_STAGING_SUFFIX, INSTALL_UV_COMMAND, INSTALL_VENV_PYTHON,
    INSTALL_VOSK_BASE_URL, INSTALL_WHISPER_FILE_PATTERNS, INSTALL_WHISPER_REPO_ID,
)
from app.config.render import MANIM_OUTPUT_DIR
from app.config.speech import (
    TTS_VOICES_DIR, TTS_VOICE_CONFIG_SUFFIX, TTS_VOICE_DEFAULT_MODEL, TTS_VOICE_MODEL_EXTENSION,
)
from app.config.voice import VOICE_VOSK_WAKE_MODEL_DIR, VOICE_WHISPER_DOWNLOAD_ROOT
from app.core.paths import PROJECT_ROOT

LAUNCHER_TEMPLATE = string.Template('''import ctypes
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(${project_root})
PYTHON = PROJECT_ROOT / ${venv_python}
ENTRY = PROJECT_ROOT / ${entry_script}
LOG_FILE = PROJECT_ROOT / ${log_file}
TITLE = ${title}
MISSING_MESSAGE = ${missing_message}
MB_ICONERROR = 0x10
FROZEN_ENV_PREFIXES = ("_PYI", "_MEI")
CREATION_FLAGS = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP


def child_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(FROZEN_ENV_PREFIXES)
    }
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def main() -> int:
    if not PYTHON.is_file() or not ENTRY.is_file():
        ctypes.windll.user32.MessageBoxW(None, MISSING_MESSAGE, TITLE, MB_ICONERROR)
        return 1

    ctypes.windll.kernel32.SetDllDirectoryW(None)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("w", encoding="utf-8") as log:
        subprocess.Popen(
            [str(PYTHON), str(ENTRY)],
            cwd=PROJECT_ROOT,
            env=child_environment(),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=CREATION_FLAGS,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')


class InstallError(Exception):
    pass


def section(title: str) -> None:
    banner = f"{INSTALL_SECTION_FILL * INSTALL_SECTION_LEAD}{title}"
    print(f"\n{banner.ljust(INSTALL_SECTION_WIDTH, INSTALL_SECTION_FILL)}", flush=True)


def log(message: str) -> None:
    print(f"{INSTALL_DETAIL_INDENT}{message}", flush=True)


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def report_progress(received: int, total: int) -> None:
    received_mb = received / INSTALL_BYTES_PER_MB
    if total > 0:
        percent = received * 100 // total
        line = f"{received_mb:.1f} / {total / INSTALL_BYTES_PER_MB:.1f} MB ({percent}%)"
    else:
        line = f"{received_mb:.1f} MB"
    print(f"\r{INSTALL_DETAIL_INDENT}{line}", end="", flush=True)


def download(url: str, target: Path) -> None:
    if target.is_file():
        log(f"found {relative(target)}, skipping")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + INSTALL_PARTIAL_SUFFIX)
    request = urllib.request.Request(url, headers={"User-Agent": INSTALL_DOWNLOAD_USER_AGENT})

    log(f"downloading {url}")
    with urllib.request.urlopen(request, timeout=INSTALL_DOWNLOAD_TIMEOUT_S) as response:
        total = int(response.headers.get("Content-Length") or 0)
        received = 0
        with partial.open("wb") as sink:
            while chunk := response.read(INSTALL_DOWNLOAD_CHUNK_BYTES):
                sink.write(chunk)
                received += len(chunk)
                report_progress(received, total)
    print()

    partial.replace(target)
    log(f"saved {relative(target)}")


def install_voice() -> None:
    voices = PROJECT_ROOT / TTS_VOICES_DIR
    model_name = f"{TTS_VOICE_DEFAULT_MODEL}{TTS_VOICE_MODEL_EXTENSION}"
    config_name = f"{model_name}{TTS_VOICE_CONFIG_SUFFIX}"

    for filename in (model_name, config_name):
        download(f"{INSTALL_PIPER_VOICE_BASE_URL}/{filename}", voices / filename)


def install_vosk_model() -> None:
    model_dir = PROJECT_ROOT / VOICE_VOSK_WAKE_MODEL_DIR
    if model_dir.is_dir():
        log(f"found {relative(model_dir)}, skipping")
        return

    archive = model_dir.with_name(model_dir.name + INSTALL_ARCHIVE_SUFFIX)
    staging = model_dir.with_name(model_dir.name + INSTALL_STAGING_SUFFIX)
    download(f"{INSTALL_VOSK_BASE_URL}/{archive.name}", archive)

    shutil.rmtree(staging, ignore_errors=True)
    log(f"extracting {relative(archive)}")
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(staging)

    extracted = staging / model_dir.name
    if not extracted.is_dir():
        raise InstallError(f"{archive.name} does not contain {model_dir.name}")

    extracted.replace(model_dir)
    shutil.rmtree(staging, ignore_errors=True)
    archive.unlink()
    log(f"installed {relative(model_dir)}")


def install_whisper_model() -> None:
    cache = PROJECT_ROOT / VOICE_WHISPER_DOWNLOAD_ROOT
    cache.mkdir(parents=True, exist_ok=True)
    log(f"fetching {INSTALL_WHISPER_REPO_ID} into {relative(cache)}")
    location = snapshot_download(
        INSTALL_WHISPER_REPO_ID,
        cache_dir=str(cache),
        allow_patterns=list(INSTALL_WHISPER_FILE_PATTERNS),
    )
    log(f"whisper ready at {relative(Path(location))}")


def create_output_dir() -> None:
    output = PROJECT_ROOT / MANIM_OUTPUT_DIR
    output.mkdir(parents=True, exist_ok=True)
    log(f"ready {relative(output)}")


def desktop_dir() -> Path:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INSTALL_SHELL_FOLDERS_KEY) as key:
            raw, _ = winreg.QueryValueEx(key, INSTALL_DESKTOP_VALUE)
    except OSError:
        return Path.home() / INSTALL_DESKTOP_FALLBACK
    return Path(os.path.expandvars(raw))


def uv_executable() -> str:
    executable = shutil.which(INSTALL_UV_COMMAND)
    if executable is None:
        raise InstallError(f"'{INSTALL_UV_COMMAND}' was not found on PATH")
    return executable


def render_launcher() -> str:
    missing_message = (
        f"{INSTALL_APP_NAME} could not find its Python environment in:\n"
        f"{PROJECT_ROOT}\n\n"
        f"Open that folder and run 'uv run install.py'."
    )
    return LAUNCHER_TEMPLATE.substitute(
        project_root=repr(str(PROJECT_ROOT)),
        venv_python=repr(INSTALL_VENV_PYTHON),
        entry_script=repr(INSTALL_ENTRY_SCRIPT),
        log_file=repr(INSTALL_LOG_FILE),
        title=repr(INSTALL_APP_NAME),
        missing_message=repr(missing_message),
    )


def build_launcher(workspace: Path, icon: Path) -> Path:
    source = workspace / f"{INSTALL_APP_NAME}.py"
    source.write_text(render_launcher(), encoding="utf-8")
    dist = workspace / "dist"

    command = [
        uv_executable(), "tool", "run",
        "--from", INSTALL_PYINSTALLER_PACKAGE, INSTALL_PYINSTALLER_COMMAND,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--log-level", INSTALL_PYINSTALLER_LOG_LEVEL,
        "--name", INSTALL_APP_NAME,
        "--icon", str(icon),
        "--distpath", str(dist),
        "--workpath", str(workspace / "build"),
        "--specpath", str(workspace),
        str(source),
    ]
    log(f"building {INSTALL_APP_NAME}{INSTALL_EXECUTABLE_SUFFIX}")
    subprocess.run(command, check=True)

    executable = dist / f"{INSTALL_APP_NAME}{INSTALL_EXECUTABLE_SUFFIX}"
    if not executable.is_file():
        raise InstallError(f"PyInstaller did not produce {executable.name}")
    return executable


def install_launcher() -> None:
    icon = PROJECT_ROOT / INSTALL_ICON_PATH
    if not icon.is_file():
        raise InstallError(f"icon not found: {relative(icon)}")

    desktop = desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=INSTALL_BUILD_DIR_PREFIX) as workspace:
        executable = build_launcher(Path(workspace), icon)
        target = desktop / executable.name
        try:
            shutil.copy2(executable, target)
        except PermissionError as exc:
            raise InstallError(
                f"cannot replace {target}; close {INSTALL_APP_NAME} and run the installer again"
            ) from exc

    log(f"placed {target}")


def main() -> int:
    if sys.platform != "win32":
        section(INSTALL_SECTION_FAILED)
        log("the installer supports Windows only")
        return 1

    steps: tuple[tuple[str, Callable[[], None]], ...] = (
        (INSTALL_SECTION_VOICE, install_voice),
        (INSTALL_SECTION_VOSK, install_vosk_model),
        (INSTALL_SECTION_WHISPER, install_whisper_model),
        (INSTALL_SECTION_OUTPUT, create_output_dir),
        (INSTALL_SECTION_EXE, install_launcher),
    )

    try:
        for title, step in steps:
            section(title)
            step()
    except (InstallError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        section(INSTALL_SECTION_FAILED)
        log(str(exc))
        return 1

    section(INSTALL_SECTION_DONE)
    log(f"double-click {INSTALL_APP_NAME}{INSTALL_EXECUTABLE_SUFFIX} on your desktop to start {INSTALL_APP_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())