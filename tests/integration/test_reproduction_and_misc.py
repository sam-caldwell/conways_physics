from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_pair_reproduction_same_cell():
    sim = Simulation(width=10, height=10)
    # C/D pair, opposite genders; energies high enough to desire reproduction
    c = Automaton(letter="C", x=2, y=5, energy=70.0)
    d = Automaton(letter="D", x=2, y=5, energy=70.0)
    sim.add(c)
    sim.add(d)
    sim.step(0.1)
    # Expect a newborn of same pair (lower letter of the pair)
    assert any(a.letter == "C" and a is not c and a is not d for a in sim.automata)


def test_drop_rock_conditions():
    sim = Simulation(width=10, height=10)
    a = Automaton(letter="A", x=1, y=1, energy=100.0)
    z_low = Automaton(letter="Z", x=2, y=1, energy=50.0)
    z_ok = Automaton(letter="Z", x=3, y=1, energy=95.0)
    z_dead = Automaton(letter="Z", x=4, y=1, energy=95.0, alive=False)
    sim.add(a)
    sim.add(z_low)
    sim.add(z_ok)
    sim.add(z_dead)
    assert sim.drop_rock_from(a) is False  # wrong species
    assert sim.drop_rock_from(z_low) is False  # energy too low
    assert sim.drop_rock_from(z_dead) is False  # not alive
    assert sim.drop_rock_from(z_ok) is True


def test_ground_y_at_when_width_zero():
    sim = Simulation(width=0, height=10)
    # With width zero, use last row as ground
    assert sim.ground_y_at(123.4) == float(9)


def test_auto_rocks_drop_with_monkeypatch(monkeypatch):
    sim = Simulation(width=10, height=10)
    sim.auto_rocks = True
    z = Automaton(letter="Z", x=5, y=3, energy=95.0)
    sim.add(z)
    import random

    monkeypatch.setattr(random, "random", lambda: 0.0)
    rocks_before = len(sim.rocks)
    sim.step(0.1)
    assert len(sim.rocks) >= rocks_before + 1
