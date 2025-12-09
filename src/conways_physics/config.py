"""Configuration constants for the simulation.

These defaults are tuned for a stable, readable terminal simulation and may be
adjusted as needed for different performance envelopes.
"""

from __future__ import annotations

# Time
DAY_LENGTH_S: float = 30.0
DAYLIGHT_S: float = 15.0

# Energy economy
E_MEAL: float = 25.0
ENERGY_MIN_MOVE: float = 10.0
ENERGY_MIN_FLY: float = 20.0
ENERGY_MAX: float = 100.0

# Physics (simple, stable constants)
GRAVITY: float = 9.81
AIR_DRAG: float = 0.02
GROUND_FRICTION: float = 0.1
RESTITUTION: float = 0.2

# Rock behavior
ROCK_MASS: float = 20.0
ROCK_DROP_THRESHOLD: float = 70.0

# Simulation defaults
DEFAULT_WIDTH: int = 40
DEFAULT_HEIGHT: int = 24

# Reproduction rules
REPRO_ENERGY_THRESHOLD: float = 60.0
FLYER_MIN_ALTITUDE_REPRO: float = 20.0

# Flight behavior
FLYER_CLIMB_ACCEL: float = 12.0

# Corpses
# Time for a corpse to be absorbed into terrain: 5 in-game days.
CORPSE_DECAY_SECONDS: float = 5.0 * DAY_LENGTH_S

# Rocks
# Time for a landed rock to be absorbed into terrain: 10 in-game days.
ROCK_DECAY_SECONDS: float = 10.0 * DAY_LENGTH_S

# Lander jump capability
LANDER_JUMP_COOLDOWN_DAYS: float = 7.0
LANDER_JUMP_ASCENT_MAX_CELLS: int = 3
LANDER_JUMP_DISTANCE_CELLS: int = 2
LANDER_JUMP_CHANCE: float = 0.5  # probability to attempt a jump when eligible
