import socket
import time

from app.config import (
    OFFLINE_PROBE_CACHE_S, OFFLINE_PROBE_HOST,
    OFFLINE_PROBE_PORT, OFFLINE_PROBE_TIMEOUT_S,
)

_last_result: bool | None = None
_last_checked: float = 0.0


def probe() -> bool:
    try:
        with socket.create_connection(
            (OFFLINE_PROBE_HOST, OFFLINE_PROBE_PORT),
            timeout=OFFLINE_PROBE_TIMEOUT_S,
        ):
            return True
    except OSError:
        return False


def is_online(use_cache: bool = True) -> bool:
    global _last_result, _last_checked

    now = time.monotonic()
    if use_cache and _last_result is not None and now - _last_checked < OFFLINE_PROBE_CACHE_S:
        return _last_result

    _last_result = probe()
    _last_checked = now
    return _last_result