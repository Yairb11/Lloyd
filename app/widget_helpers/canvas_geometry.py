from PyQt6.QtCore import QPointF

from app.config import (
    ANIM_CONTAINER_MIXING_HEIGHT, ANIM_CONTAINER_MIXING_W_BOT, ANIM_CONTAINER_MIXING_W_TOP,
    ANIM_CONTAINER_ROCKS_HEIGHT, ANIM_CONTAINER_ROCKS_W_BOT, ANIM_CONTAINER_ROCKS_W_TOP,
    ANIM_CONTAINER_SHAKER_HEIGHT, ANIM_CONTAINER_SHAKER_W_BOT, ANIM_CONTAINER_SHAKER_W_TOP,
    ANIM_CONTAINER_STEMMED_HEIGHT, ANIM_CONTAINER_STEMMED_W_BOT, ANIM_CONTAINER_STEMMED_W_TOP,
    ANIM_CONTAINER_TALL_HEIGHT, ANIM_CONTAINER_TALL_W_BOT, ANIM_CONTAINER_TALL_W_TOP,
)


def qp(x: float, y: float) -> QPointF:
    return QPointF(float(x), float(-y))


class VesselShape:
    def __init__(self, w_top: float, w_bot: float, height: float, stemmed: bool) -> None:
        self.w_top = w_top
        self.w_bot = w_bot
        self.h = height
        self.stemmed = stemmed

    def width_at(self, y_rel: float) -> float:
        if self.h <= 0:
            return self.w_bot
        ratio = max(0.0, min(1.0, y_rel / self.h))
        return self.w_bot + (self.w_top - self.w_bot) * ratio


def vessel_shape(c_type: str) -> VesselShape:
    name = str(c_type).lower()
    if "shaker" in name:
        return VesselShape(
            ANIM_CONTAINER_SHAKER_W_TOP, ANIM_CONTAINER_SHAKER_W_BOT,
            ANIM_CONTAINER_SHAKER_HEIGHT, False,
        )
    if "mixing" in name:
        return VesselShape(
            ANIM_CONTAINER_MIXING_W_TOP, ANIM_CONTAINER_MIXING_W_BOT,
            ANIM_CONTAINER_MIXING_HEIGHT, False,
        )
    if "coupe" in name or "martini" in name or "nick" in name:
        return VesselShape(
            ANIM_CONTAINER_STEMMED_W_TOP, ANIM_CONTAINER_STEMMED_W_BOT,
            ANIM_CONTAINER_STEMMED_HEIGHT, True,
        )
    if "highball" in name or "collins" in name:
        return VesselShape(
            ANIM_CONTAINER_TALL_W_TOP, ANIM_CONTAINER_TALL_W_BOT,
            ANIM_CONTAINER_TALL_HEIGHT, False,
        )
    return VesselShape(
        ANIM_CONTAINER_ROCKS_W_TOP, ANIM_CONTAINER_ROCKS_W_BOT,
        ANIM_CONTAINER_ROCKS_HEIGHT, False,
    )
