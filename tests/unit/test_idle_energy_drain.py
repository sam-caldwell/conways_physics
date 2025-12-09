from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from unittest.mock import patch


def test_idle_lander_loses_energy_when_blocked_no_eat_no_repro():
    sim = Simulation(width=4, height=10)
    # Make a high step at x=1 to block movement from x=0 to x=1
    sim.terrain = [8, 4, 8, 8]
    a = Automaton(letter="E", x=0.0, y=sim.terrain[0] - 1, energy=50.0)
    sim.add(a)
    # Put a non-prey ahead to avoid predation; ensure no reproduction; prevent jumping
    b = Automaton(letter="E", x=2.0, y=sim.terrain[2] - 1, energy=50.0)
    sim.add(b)
    e0 = a.energy
    with patch('conways_physics.sim.random.random', return_value=1.0):  # avoid jump chance
        sim.step(0.5)
    assert a.energy < e0

