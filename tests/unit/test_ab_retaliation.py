from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_ab_retaliation_triggers_on_coin_toss(monkeypatch):
    sim = Simulation(width=10, height=10)
    predator = Automaton(letter="C", x=2.0, y=5.0, energy=5.0)
    prey_ab = Automaton(letter="A", x=2.0, y=5.0, energy=50.0)
    sim.add(predator)
    sim.add(prey_ab)
    # Force coin toss to succeed, prey eats attacker instead
    import conways_physics.sim as sim_mod
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.0)
    sim.step(0.0)
    assert predator.alive is False
    assert prey_ab.alive is True
    assert prey_ab.energy > 50.0


def test_ab_retaliation_does_not_trigger_on_coin_fail(monkeypatch):
    sim = Simulation(width=10, height=10)
    predator = Automaton(letter="C", x=2.0, y=5.0, energy=5.0)
    prey_ab = Automaton(letter="A", x=2.0, y=5.0, energy=50.0)
    sim.add(predator)
    sim.add(prey_ab)
    # Force coin toss to fail, predator eats prey
    import conways_physics.sim as sim_mod
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.9)
    sim.step(0.0)
    assert predator.alive is True
    assert prey_ab.alive is False
    assert predator.energy > 5.0
