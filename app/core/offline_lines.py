import random

from app.config import OFFLINE_LINES

_last_index: int = -1


def pick_offline_line() -> str:
    global _last_index

    if len(OFFLINE_LINES) < 2:
        return OFFLINE_LINES[0]

    _last_index = random.choice(
        [index for index in range(len(OFFLINE_LINES)) if index != _last_index]
    )
    return OFFLINE_LINES[_last_index]