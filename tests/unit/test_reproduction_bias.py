from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_lander_bias_toward_mate_over_prey():
    sim = Simulation(width=20, height=20)
    # Terrain flat
    sim.terrain = [15] * 20
    # Lander C at x=10
    c = Automaton(letter="C", x=10.0, y=14.0, energy=100.0)
    sim.add(c)
    # Mate D to the right, prey A to the left; should move toward mate
    mate = Automaton(letter="D", x=12.0, y=14.0, energy=100.0)
    prey = Automaton(letter="A", x=8.0, y=14.0, energy=100.0)
    sim.add(mate)
    sim.add(prey)
    sim.step(0.5)
    assert c.x > 10.0


def test_flyer_bias_toward_mate():
    sim = Simulation(width=20, height=30)
    # Terrain flat and low
    sim.terrain = [25] * 20
    n = Automaton(letter="N", x=10.0, y=5.0, energy=100.0, vx=0.0)
    o = Automaton(letter="O", x=12.0, y=5.0, energy=100.0)
    sim.add(n)
    sim.add(o)
    sim.step(0.5)
    # Should have moved toward mate (to the right)
    assert n.x > 10.0
