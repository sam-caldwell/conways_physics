from __future__ import annotations

from typing import List
from rich.text import Text

from .sim import Simulation
from .automata import Automaton


def slope_char(prev_y: int, y: int, next_y: int) -> str:
    # Choose '/', '\\', or '_' based on local slope
    left = prev_y - y
    right = next_y - y
    if left < 0 or right < 0:
        return "/"
    if left > 0 or right > 0:
        return "\\"
    return "_"


def render_sim(sim: Simulation, width: int, height: int) -> Text:
    # Build a character grid
    w, h = width, height
    grid = [[" "] * w for _ in range(h)]

    # Terrain baseline and stacks
    t = sim.terrain
    span = min(w, sim.width)
    for x in range(span):
        y = int(round(t[x]))
        prev_y = t[(x - 1) % span] if span > 0 else y
        next_y = t[(x + 1) % span] if span > 0 else y
        # Draw slope char at surface
        if 0 <= y < h:
            grid[y][x] = slope_char(int(prev_y), int(y), int(next_y))
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

    # Build Rich Text with color states
    lines: List[Text] = []
    for r in range(h):
        row = Text()
        for c in range(w):
            ch = grid[r][c]
            style = None
            # Color cues: match automata at this cell
            for a in sim.automata:
                if not a.alive:
                    continue
                if int(round(a.x)) % max(1, w) == c and int(round(a.y)) == r:
                    if a.eat_flash > 0:
                        style = "red"
                    elif a.repro_flash > 0:
                        style = "green"
                    elif a.starving:
                        style = "blue"
                    break
            row.append(ch, style=style)
        lines.append(row)
    # Join lines with newlines
    out = Text()
    for i, line in enumerate(lines):
        if i:
            out.append("\n")
        out.append(line)
    return out
