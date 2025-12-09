"""Small utility helpers used across the simulation."""

from __future__ import annotations

from .config import DAY_LENGTH_S, DAYLIGHT_S


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a numeric value to the closed interval [lo, hi]."""
    if lo > hi:
        lo, hi = hi, lo
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def is_day(t_seconds: float) -> bool:
    """Return True if the given absolute time (in seconds) falls within daylight."""
    if DAY_LENGTH_S <= 0:
        return False
    phase = t_seconds % DAY_LENGTH_S
    return phase < DAYLIGHT_S
