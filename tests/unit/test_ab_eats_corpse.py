from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import E_MEAL


def test_a_b_species_can_eat_corpse_same_cell():
    sim = Simulation(width=20, height=20)
    x = 10
    gy = int(round(sim.ground_y_at(x)))
    y = max(0, gy - 1)
    # Place corpse at air boundary
    sim.corpses.add((y, x))
    # Place an A at same cell with known energy
    a = Automaton(letter="A", x=float(x), y=float(y), energy=10.0)
    sim.add(a)
    sim.step(0.0)
    # Corpse removed and energy increased by one meal (within clamp)
    assert (y, x) not in sim.corpses
    assert a.energy >= min(10.0 + E_MEAL, 100.0) - 1e-6


def test_non_ab_cannot_eat_corpse():
    sim = Simulation(width=20, height=20)
    x = 5
    gy = int(round(sim.ground_y_at(x)))
    y = max(0, gy - 1)
    sim.corpses.add((y, x))
    c = Automaton(letter="C", x=float(x), y=float(y), energy=10.0)
    sim.add(c)
    sim.step(0.0)
    assert (y, x) in sim.corpses
    assert c.energy == 10.0


def test_consume_corpses_no_corpses_noop():
    sim = Simulation(width=10, height=10)
    a = Automaton(letter="A", x=1.0, y=1.0, energy=10.0)
    sim.add(a)
    # Should not error or change state
    sim._consume_corpses()
    assert len(sim.corpses) == 0
