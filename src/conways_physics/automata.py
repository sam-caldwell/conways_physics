"""Core entity types: Automaton and Rock.

This module defines the Automaton class (land and flying species) and the simple
Rock projectile used by X/Y/Z flyers. The motion integrator models a light
flight/ground system tuned for stability in a terminal simulation.

Docstrings follow PEP 257 conventions with concise summaries and details where
useful. Public attributes are documented via type hints; behavior is described
on classes and methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from .config import (
    ENERGY_MAX,
    ENERGY_MIN_FLY,
    ENERGY_MIN_MOVE,
    GRAVITY,
    AIR_DRAG,
    GROUND_FRICTION,
    RESTITUTION,
    E_MEAL,
    FLYER_MIN_ALTITUDE_REPRO,
    FLYER_CLIMB_ACCEL,
)
from .species import is_flyer_letter
from .utils import clamp


@dataclass
class Automaton:
    """A single automaton with simple Newtonian dynamics and energy.

    Automata may be landers (A..M) or flyers (N..Z). Flyers prefer flight when
    they have sufficient energy and will actively climb until they reach a
    preferred altitude above the local terrain.
    """
    letter: str
    x: float
    y: float
    energy: float = 50.0
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True
    age_s: float = 0.0  # accumulated lifetime in seconds
    transforms_done: int = 0  # number of 30-day transformations applied (landers only)
    last_jump_time_s: float = -1e18  # last absolute time a lander jump was used
    since_repro_s: float = 0.0  # time since last successful reproduction (A/B auto-spawn rule)
    ate_step: bool = False  # set True when eat_gain is called within a step
    repro_step: bool = False  # set True when reproduction occurs within a step
    stagnant_s: float = 0.0  # accumulated time spent in the same integer cell
    # Randomized body weight in [20..100]; reserved for physics tuning
    weight: float = field(default_factory=lambda: float(random.randint(20, 100)))

    def can_move(self) -> bool:
        """Return True if the automaton has enough energy to move."""
        return self.energy > ENERGY_MIN_MOVE and self.alive

    def can_fly(self) -> bool:
        """Return True if this automaton is a flyer with enough energy to fly."""
        return is_flyer_letter(self.letter) and self.energy > ENERGY_MIN_FLY and self.alive

    def apply_sunlight(self, per_second: float, dt: float) -> None:
        """Increase energy by the sunlit rate times ``dt``.

        Parameters:
            per_second: Energy gain per second.
            dt: Time delta in seconds.
        """
        if not self.alive:
            return
        self.energy = clamp(self.energy + per_second * dt, 0.0, ENERGY_MAX)

    def eat_gain(self, meals: float = 1.0) -> None:
        """Increase energy as if the automaton consumed ``meals`` meals."""
        if not self.alive:
            return
        self.energy = clamp(self.energy + meals * E_MEAL, 0.0, ENERGY_MAX)
        # mark this step as having eaten (used for idle drain logic)
        self.ate_step = True

    def kill(self) -> None:
        """Mark the automaton as no longer alive."""
        self.alive = False

    def tick_motion(self, dt: float, ground_y: float, width: int) -> None:
        """Advance position/velocity by ``dt`` seconds.

        Parameters:
            dt: Time step in seconds (non-negative).
            ground_y: The terrain surface row at the current ``x``.
            width: World width for wraparound.
        """
        if not self.alive:
            return
        # Do not change position/velocity when dt <= 0; allows tests to set
        # exact positions for reproduction/visibility without side effects.
        if dt <= 0.0:
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
            # Incorporate weight conservatively: heavier bodies increase effective gravity slightly.
            w_norm = max(0.0, min(1.0, (self.weight - 20.0) / 80.0))
            weight_factor = 1.0 + 0.5 * (self.energy / ENERGY_MAX) + 0.2 * w_norm
            # Add climb bias if below preferred altitude relative to surface
            altitude = max(0.0, ground_y - self.y)
            climb = 0.0
            if altitude < FLYER_MIN_ALTITUDE_REPRO:
                climb = FLYER_CLIMB_ACCEL * (1.0 - (altitude / max(1e-6, FLYER_MIN_ALTITUDE_REPRO)))
            self.vy += ((GRAVITY * weight_factor) - climb) * dt
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
            # On ground: flyers may rest but cannot translate along terrain; landers can walk
            self.y = ground_air
            if is_flyer_letter(self.letter):
                # immobilize along ground
                self.vx = 0.0
                # small passive drain
                self.energy = clamp(self.energy - (0.1 * dt), 0.0, ENERGY_MAX)
            else:
                # landers walk with friction
                self.x += self.vx * dt
                # Friction scaling: slightly higher with more energy and more weight
                e_term = 0.1 * (self.energy / ENERGY_MAX)
                w_norm = max(0.0, min(1.0, (self.weight - 20.0) / 80.0))
                w_term = 0.03 * w_norm
                self.vx *= max(0.0, 1.0 - (GROUND_FRICTION + e_term + w_term))
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
        """Return True if energy is below the move threshold."""
        return self.energy < ENERGY_MIN_MOVE


@dataclass
class Rock:
    """A simple falling rock with vertical velocity only."""
    x: float
    y: float
    vy: float = 0.0
    active: bool = True

    def step(self, dt: float, ground_y: float) -> None:
        """Integrate the rock for a single time step ``dt``."""
        if not self.active:
            return
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        # Ground absorption handled by Simulation to allow impact checks first

    def impact_energy(self) -> float:
        """Return the current kinetic energy for collision calculations."""
        return 0.5 * (self.vy * self.vy)
