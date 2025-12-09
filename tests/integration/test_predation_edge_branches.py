from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_predation_skips_dead_in_build_and_scan():
    sim = Simulation(width=10, height=10)
    alive = Automaton(letter="N", x=1, y=1, energy=50.0)
    dead = Automaton(letter="A", x=1, y=1, energy=0.0, alive=False)
    sim.add(alive)
    sim.add(dead)
    # Should not raise and should skip dead entries in maps and scans
    sim.step(0.1)
    assert alive.alive is True and dead.alive is False

