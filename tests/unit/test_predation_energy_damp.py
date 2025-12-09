from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_high_energy_predator_eats_less(monkeypatch):
    sim = Simulation(width=10, height=10)
    # Predator higher rank with near-max energy
    predator = Automaton(letter="F", x=2, y=5, energy=100.0)
    prey = Automaton(letter="E", x=2, y=5, energy=50.0)
    sim.add(predator)
    sim.add(prey)
    import conways_physics.sim as sim_mod
    # With high random value and damped appetite, predator should abstain
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.95)
    sim.step(0.0)
    assert prey.alive is True


def test_normal_energy_predator_still_eats(monkeypatch):
    sim = Simulation(width=10, height=10)
    predator = Automaton(letter="F", x=3, y=5, energy=50.0)
    prey = Automaton(letter="E", x=3, y=5, energy=50.0)
    sim.add(predator)
    sim.add(prey)
    import conways_physics.sim as sim_mod
    # Even with high random draw, below damp threshold should eat
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.95)
    sim.step(0.0)
    assert prey.alive is False
