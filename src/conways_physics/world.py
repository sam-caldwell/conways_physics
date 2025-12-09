from __future__ import annotations

from dataclasses import dataclass

from .utils import is_day as util_is_day, clamp
from .config import DAYLIGHT_S, ENERGY_MAX


@dataclass
class World:
    t_abs: float = 0.0

    def tick(self, dt: float) -> None:
        if dt < 0:
            return
        self.t_abs += dt

    @property
    def is_day(self) -> bool:
        return util_is_day(self.t_abs)

    def sunlight_energy_gain(self, e_meal: float) -> float:
        if DAYLIGHT_S <= 0:
            return 0.0
        per_second = (2.0 * e_meal) / DAYLIGHT_S
        return clamp(per_second, 0.0, ENERGY_MAX)

