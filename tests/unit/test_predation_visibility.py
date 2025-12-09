from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_predation_visibility_coin_toss(monkeypatch):
    sim = Simulation(width=10, height=10)
    # Lander at ground, flyer two cells to the right (same row)
    lander = Automaton(letter="A", x=5, y=5, energy=50.0)
    flyer = Automaton(letter="N", x=7, y=5, energy=50.0)
    sim.add(lander)
    sim.add(flyer)

    import conways_physics.sim as sim_mod

    # First: coin toss fails visibility -> no predation
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.9)
    sim.step(0.0)
    assert flyer.alive is True

    # Second: coin toss sees -> lander eats flyer
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.0)
    sim.step(0.0)
    assert flyer.alive is False

