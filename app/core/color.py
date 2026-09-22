import numpy as np


def hex_to_rgb(hex_str: str) -> np.ndarray:
    h = hex_str.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])


def rgb_to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        int(np.clip(rgb[0] * 255, 0, 255)),
        int(np.clip(rgb[1] * 255, 0, 255)),
        int(np.clip(rgb[2] * 255, 0, 255)),
    )
