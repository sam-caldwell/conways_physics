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

    @staticmethod
    def sunlight_energy_gain(e_meal: float) -> float:
        """Return A/B sunlight energy gain per second during daylight.

        Over the daylight window (the sunlit portion of a day), the integral of
        this rate equals one quarter of a single meal's energy.
        """
        if DAYLIGHT_S <= 0:
            return 0.0
        per_second = (0.25 * e_meal) / DAYLIGHT_S
        return clamp(per_second, 0.0, ENERGY_MAX)
