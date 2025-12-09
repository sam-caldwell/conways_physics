"""Minimal world clock and day/night helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .utils import is_day as util_is_day, clamp
from .config import DAYLIGHT_S, ENERGY_MAX


@dataclass
class World:
    """Global timekeeper with day/night calculation."""

    t_abs: float = 0.0

    def tick(self, dt: float) -> None:
        """Advance absolute time by ``dt`` seconds (non-negative)."""
        if dt < 0:
            return
        self.t_abs += dt

    @property
    def is_day(self) -> bool:
        """True if the current phase is daylight."""
        return util_is_day(self.t_abs)

    def sunlight_energy_gain(self, e_meal: float) -> float:
        """Return A/B sunlight energy gain per second during daylight.

        Over the daylight window the integral of this rate equals two meals.
        """
        if DAYLIGHT_S <= 0:
            return 0.0
        per_second = (2.0 * e_meal) / DAYLIGHT_S
        return clamp(per_second, 0.0, ENERGY_MAX)
