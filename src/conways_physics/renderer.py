"""Text rendering for the world using Rich/Textual.

The renderer produces a Text object with terrain, corpse overlays, and automata
glyphs colored by energy. Terrain uses block characters and corpses use '#'.
"""

from __future__ import annotations

from typing import List
from rich.text import Text

from .sim import Simulation


def slope_char(prev_y: int, y: int, next_y: int) -> str:
    """Return the terrain glyph (full block)."""
    return "\u2588"


COLOR_TABLE = [
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
]


def _energy_style(energy: float) -> str:
    """Map energy [1..100] to a 0..15 color index, clamped.

    - Energies <=1 map to index 0; 100 maps to 15.
    - Energies outside [0,100] are clamped before mapping.
    """
    e = 0.0 if energy is None else float(energy)
    if e < 0.0:
        e = 0.0
    if e > 100.0:
        e = 100.0
    # Treat the visible scale as 1..100 so that 100 -> 15 exactly
    e1 = max(1.0, e)
    ratio = (e1 - 1.0) / 99.0  # 0.0 at 1, 1.0 at 100
    idx = int(ratio * 15.0)
    idx = max(0, min(15, idx))
    return COLOR_TABLE[idx]


def render_sim(sim: Simulation, width: int, height: int) -> Text:
    """Render the world state to a Rich Text object of given size."""
    # Build a character grid
    w, h = width, height
    grid = [[" "] * w for _ in range(h)]

    # Terrain and fill below
    t = sim.terrain
    span = min(w, sim.width)
    terrain_cells = set()
    for x in range(span):
        y = int(round(t[x]))
        prev_y = t[(x - 1) % span] if span > 0 else y
        next_y = t[(x + 1) % span] if span > 0 else y
        # Draw block at surface and fill below
        if 0 <= y < h:
            grid[y][x] = slope_char(int(prev_y), int(y), int(next_y))
            terrain_cells.add((y, x))
            for yy in range(y + 1, h):
                grid[yy][x] = slope_char(int(y), int(yy), int(y))
                terrain_cells.add((yy, x))
        # Draw stacked '#': represent buried items above the surface (one cell per bury)
        # We infer stacks by how far surface has moved from a nominal baseline; skip for simplicity here.

    # Automata letters (overlay)
    for a in sim.automata:
        if not a.alive:
            continue
        x = int(round(a.x)) % max(1, span)
        y = int(round(a.y))
        if 0 <= y < h:
            ch = a.letter.upper()
            if 0 <= x < w:
                grid[y][x] = ch

    # Overlay corpses and static rocks as '#'
    corpse_cells = set()
    for (ry, cx) in getattr(sim, "corpses", set()):
        if 0 <= cx < w and 0 <= ry < h:
            grid[ry][cx] = "#"
            corpse_cells.add((ry, cx))
    rock_static_cells = set()
    for (ry, cx) in getattr(sim, "rocks_static", set()):
        if 0 <= cx < w and 0 <= ry < h:
            grid[ry][cx] = "#"
            rock_static_cells.add((ry, cx))

    # Build Rich Text with color states
    lines: List[Text] = []
    for r in range(h):
        row = Text()
        for c in range(w):
            ch = grid[r][c]
            style = None
            # Color based on automaton energy mapped to 0..15 palette,
            # or grey for terrain/corpses where no automata present
            for a in sim.automata:
                if not a.alive:
                    continue
                if int(round(a.x)) % max(1, w) == c and int(round(a.y)) == r:
                    style = _energy_style(a.energy)
                    break
            else:
                if (r, c) in corpse_cells or (r, c) in rock_static_cells:
                    style = "grey70"
                elif (r, c) in terrain_cells:
                    style = "grey50"
            row.append(ch, style=style)
        lines.append(row)
    # Join lines with newlines
    out = Text()
    for i, line in enumerate(lines):
        if i:
            out.append("\n")
        out.append(line)
    return out
