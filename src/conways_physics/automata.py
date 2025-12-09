from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .config import (
    ENERGY_MAX,
    ENERGY_MIN_FLY,
    ENERGY_MIN_MOVE,
    GRAVITY,
    AIR_DRAG,
    GROUND_FRICTION,
    RESTITUTION,
    E_MEAL,
)
from .species import is_flyer_letter
from .utils import clamp


@dataclass
class Automaton:
    letter: str
    x: float
    y: float
    energy: float = 50.0
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True
    eat_flash: int = 0  # red for 2 cycles after eating
    repro_flash: int = 0  # green for 1 cycle before/after reproduction

    def can_move(self) -> bool:
        return self.energy > ENERGY_MIN_MOVE and self.alive

    def can_fly(self) -> bool:
        return is_flyer_letter(self.letter) and self.energy > ENERGY_MIN_FLY and self.alive

    def apply_sunlight(self, per_second: float, dt: float) -> None:
        if not self.alive:
            return
        self.energy = clamp(self.energy + per_second * dt, 0.0, ENERGY_MAX)

    def eat_gain(self, meals: float = 1.0) -> None:
        if not self.alive:
            return
        self.energy = clamp(self.energy + meals * E_MEAL, 0.0, ENERGY_MAX)
        # Trigger eat flash for 2 cycles
        self.eat_flash = max(self.eat_flash, 2)

    def kill(self) -> None:
        self.alive = False

    def tick_motion(self, dt: float, ground_y: float, width: int) -> None:
        if not self.alive:
            return

        if not self.can_move():
            # Mild passive energy drain
            self.energy = clamp(self.energy - 0.1 * dt, 0.0, ENERGY_MAX)
            return

        ground_air = max(0.0, ground_y - 1.0)
        if self.can_fly():
            # Prefer flight: if on/at ground and not already ascending, kick upward
            if self.y >= ground_air - 1e-6 and self.vy >= 0.0:
                self.vy = -3.0
            # Simple vertical dynamics with drag; horizontal conserved
            weight_factor = 1.0 + 0.5 * (self.energy / ENERGY_MAX)
            self.vy += (GRAVITY * weight_factor) * dt
            self.vy *= max(0.0, 1.0 - AIR_DRAG)
            self.y += self.vy * dt
            self.x += self.vx * dt
            # Bounce against air/ground boundary (one above surface)
            if self.y >= ground_air:
                self.y = ground_air
                self.vy = -self.vy * RESTITUTION
            # Flight cost only if actually moving
            if abs(self.vx) > 1e-9 or abs(self.vy) > 1e-9:
                self.energy = clamp(self.energy - (0.5 * dt), 0.0, ENERGY_MAX)
        else:
            # On ground: stick to one-above-surface and apply friction
            self.y = ground_air
            self.x += self.vx * dt
            # Energy increases effective mass: heavier means more frictional slowdown
            mass_factor = 1.0 - 0.5 * (self.energy / ENERGY_MAX)
            self.vx *= max(0.0, 1.0 - (GROUND_FRICTION + 0.2 * (1.0 - mass_factor)))
            # Walking cost only if moving horizontally
            if abs(self.vx) > 1e-9:
                self.energy = clamp(self.energy - (0.2 * dt), 0.0, ENERGY_MAX)

        # Wrap horizontally
        if width > 0:
            while self.x < 0:
                self.x += width
            while self.x >= width:
                self.x -= width

    @property
    def starving(self) -> bool:
        return self.energy < ENERGY_MIN_MOVE

    def tick_flashes(self) -> None:
        if self.eat_flash > 0:
            self.eat_flash -= 1
        if self.repro_flash > 0:
            self.repro_flash -= 1


@dataclass
class Rock:
    x: float
    y: float
    vy: float = 0.0
    active: bool = True

    def step(self, dt: float, ground_y: float) -> None:
        if not self.active:
            return
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        # Ground absorption handled by Simulation to allow impact checks first

    def impact_energy(self) -> float:
        # Kinetic energy before deactivation
        return 0.5 * (self.vy * self.vy)
