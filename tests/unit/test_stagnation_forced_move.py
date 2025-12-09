from unittest.mock import patch

from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def _flat_sim(w=10, h=10) -> Simulation:
    sim = Simulation(width=w, height=h)
    sim.configure_surface_for_view(w, h, sea_level_offset=4, amplitude=0, seed=1)
    return sim


def _set_mid_neighbors(sim: Simulation, ax: int, ay: int) -> None:
    """Configure Life grid so local neighbor count is between 3 and 4.

    Keeps GoL bias neutral so velocity isn't nudged by the field.
    """
    # Clear grid
    sim.life_grid = [[0 for _ in range(sim.width)] for _ in range(sim.height)]
    if sim.width <= 0 or sim.height <= 0:
        return
    # Place three live neighbors around (ax, ay)
    nx = ax % sim.width
    ny = max(0, min(sim.height - 1, ay))
    coords = [
        (max(0, ny - 1), nx),
        (ny, (nx - 1) % sim.width),
        (ny, (nx + 1) % sim.width),
    ]
    for ry, cx in coords:
        if 0 <= ry < sim.height and 0 <= cx < sim.width:
            sim.life_grid[ry][cx] = 1


def test_stagnation_counter_increases_when_not_moving_cells():
    sim = _flat_sim(20, 10)
    # Place an isolated lander with zero velocity at integer cell
    a = Automaton(letter="A", x=10.0, y=sim.ground_y_at(10.0) - 1.0, energy=100.0, vx=0.0, vy=0.0)
    sim.add(a)
    # Neutralize GoL bias near the automaton so it remains in place
    _set_mid_neighbors(sim, int(round(a.x)), int(round(a.y)))
    # Step once; since cell didn't change, stagnant_s should accumulate
    sim.step(1.0)
    assert a.stagnant_s >= 1.0


def test_stagnation_applies_nudge_after_threshold():
    sim = _flat_sim(20, 10)
    a = Automaton(letter="A", x=5.0, y=sim.ground_y_at(5.0) - 1.0, energy=100.0, vx=0.0, vy=0.0)
    sim.add(a)
    _set_mid_neighbors(sim, int(round(a.x)), int(round(a.y)))
    # Accumulate stagnant time beyond the threshold
    with patch("conways_physics.sim.random.random", return_value=0.0), \
         patch("conways_physics.sim.step_life", side_effect=lambda grid: grid):
        for _ in range(6):
            sim.step(1.0)
        # After threshold and with random=0, a nudge should be applied
        # Lander nudge is horizontal; due to friction it may be <1.0 by the end
        assert abs(a.vx) > 0.0 or a.vy < 0.0


def test_flyer_stagnation_grounded_upward_nudge():
    sim = _flat_sim(20, 10)
    # Flyer with low energy cannot fly; should get upward vy nudge when stagnant
    a = Automaton(letter="N", x=8.0, y=sim.ground_y_at(8.0) - 1.0, energy=10.0, vx=0.0, vy=0.0)
    sim.add(a)
    _set_mid_neighbors(sim, int(round(a.x)), int(round(a.y)))
    with patch("conways_physics.sim.random.random", return_value=0.0), \
         patch("conways_physics.sim.step_life", side_effect=lambda grid: grid):
        for _ in range(6):
            sim.step(1.0)
        assert a.vy < 0.0


def test_flyer_stagnation_flying_horizontal_nudge():
    sim = _flat_sim(20, 10)
    # Flyer with ample energy can fly; we freeze motion to accumulate stagnation
    a = Automaton(letter="N", x=12.0, y=sim.ground_y_at(12.0) - 10.0, energy=100.0, vx=0.0, vy=0.0)
    sim.add(a)
    _set_mid_neighbors(sim, int(round(a.x)), int(round(a.y)))

    def _noop_tick(self, dt, ground_y, width):  # type: ignore[no-redef]
        return None

    with patch("conways_physics.sim.random.random", return_value=0.0), \
         patch("conways_physics.automata.Automaton.tick_motion", new=_noop_tick), \
         patch("conways_physics.sim.step_life", side_effect=lambda grid: grid):
        for _ in range(6):
            sim.step(1.0)
        # For a flying flyer, the nudge should be horizontal
        assert abs(a.vx) > 0.0
        # vy remains unchanged by the horizontal nudge
        assert a.vy == 0.0
