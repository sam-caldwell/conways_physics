from conways_physics.sim import Simulation, same_cell, adjacent_positions
from conways_physics.automata import Automaton, Rock


def test_same_cell_and_adjacent_positions():
    a = Automaton(letter="A", x=1.2, y=3.6)
    b = Automaton(letter="B", x=1.49, y=3.51)
    assert same_cell(a, b) is True
    adj = set(adjacent_positions(2, 2))
    assert adj == {(2, 1), (1, 2), (3, 2), (2, 3)}


def test_sim_uses_custom_terrain_and_width_zero_behavior():
    terrain = [7] * 5
    sim = Simulation(width=5, height=10, terrain=terrain.copy())
    # __post_init__ should not override provided terrain
    assert sim.terrain == terrain

    sim_zero = Simulation(width=0, height=10)
    assert sim_zero.ground_y_at(123.4) == 9.0


def test_no_sunlight_at_night():
    sim = Simulation(width=10, height=10)
    # Force night by advancing to just past daylight
    from conways_physics.config import DAYLIGHT_S

    sim.world.t_abs = DAYLIGHT_S + 0.1
    a = Automaton(letter="A", x=0, y=0, energy=50.0)
    sim.add(a)
    sim.step(1.0)
    # No sunlight gain expected; with no movement, energy unchanged
    assert a.energy == 50.0


def test_rocks_inactive_ignored_and_absorb_to_ground():
    sim = Simulation(width=10, height=10)
    # Inactive rock ignored
    sim.rocks.append(Rock(x=0.0, y=0.0, vy=1.0, active=False))
    sim.step(0.1)
    assert sim.rocks[0].active is False

    # Active rock with no automata gets absorbed into ground
    r = Rock(x=4.0, y=0.0, vy=0.0, active=True)
    sim.rocks.append(r)
    sim.step(1.0)
    gy = sim.ground_y_at(r.x)
    assert r.active is False and r.y == gy


def test_bury_at_x_noop_when_width_zero():
    # With width=0, bury_at_x should be a no-op; ensure rock absorption doesn't crash
    sim = Simulation(width=0, height=10)
    from conways_physics.automata import Rock

    sim.rocks.append(Rock(x=0.0, y=0.0, vy=0.0, active=True))
    sim.step(1.0)
    # Should not raise and rock becomes inactive
    assert sim.rocks[0].active is False
