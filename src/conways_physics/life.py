"""Conway's Game of Life stepper (no wrapping)."""

from __future__ import annotations

from typing import List


def step_life(grid: List[List[int]]) -> List[List[int]]:
    """Advance Conway's Game of Life by one generation.

    - grid: list of rows; each cell is 0 (dead) or 1 (alive)
    - no wrap-around; edges see fewer neighbors
    """
    h = len(grid)
    if h == 0:
        return []
    w = len(grid[0])

    def neighbors(r: int, c: int) -> int:
        s = 0
        for dr in (-1, 0, 1):
            rr = r + dr
            if rr < 0 or rr >= h:
                continue
            for dc in (-1, 0, 1):
                cc = c + dc
                if dc == 0 and dr == 0:
                    continue
                if cc < 0 or cc >= w:
                    continue
                s += 1 if grid[rr][cc] else 0
        return s

    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            n = neighbors(r, c)
            if grid[r][c]:
                out[r][c] = 1 if n in (2, 3) else 0
            else:
                out[r][c] = 1 if n == 3 else 0
    return out
