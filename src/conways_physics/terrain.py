"""Terrain helpers to generate surface height maps."""

from __future__ import annotations

from typing import List
import random


def flat_terrain(width: int, height: int, margin_from_bottom: int = 5) -> List[int]:
    """Return a simple flat terrain height map (y values) per column.

    The terrain baseline is `height - margin_from_bottom`.
    """
    baseline = max(0, height - max(1, margin_from_bottom))
    return [baseline for _ in range(max(0, width))]


def generate_random_terrain(width: int, height: int, low_margin: int = 3, high_margin: int = 6, seed: int | None = None) -> List[int]:
    """Generate a simple random-walk terrain with the surface 3–6 rows above bottom.

    Returns a list of y positions representing the top surface per column.
    """
    rng = random.Random(seed)
    base = height - rng.randint(low_margin, high_margin)
    y = max(0, base)
    out: List[int] = []
    for _ in range(max(0, width)):
        dy = rng.choice([-1, 0, 1])
        y = max(0, min(height - 1, y + dy))
        out.append(y)
    return out


def generate_surface(
    width: int,
    height: int,
    *,
    sea_level_offset: int = 4,
    amplitude: int = 3,
    seed: int | None = None,
) -> List[int]:
    """Generate a constrained random-walk surface.

    - Baseline is exactly `sea_level_offset` rows above the bottom (y increases downward).
    - Surface varies within ±`amplitude` rows of baseline.
    - Returned list contains y (row) per column 0..width-1.
    """
    rng = random.Random(seed)
    width = max(0, int(width))
    height = max(1, int(height))
    baseline = height - max(0, int(sea_level_offset))
    lo = max(0, baseline - max(0, int(amplitude)))
    hi = min(height - 1, baseline + max(0, int(amplitude)))
    y = min(max(lo, baseline), hi)
    out: List[int] = []
    for _ in range(width):
        dy = rng.choice([-1, 0, 1])
        y = max(lo, min(hi, y + dy))
        out.append(y)
    return out
