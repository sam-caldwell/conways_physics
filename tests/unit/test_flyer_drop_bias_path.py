from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import ROCK_DROP_THRESHOLD


def test_flyer_drop_action_path_monkeypatched(monkeypatch):
    sim = Simulation(width=10, height=10)
    # Flat terrain high enough
    sim.terrain = [8] * 10
    # X flyer with enough energy to drop rocks
    xfly = Automaton(letter="X", x=5.0, y=4.0, energy=ROCK_DROP_THRESHOLD + 10.0)
    sim.add(xfly)
    # Place a prey nearby to ensure had_signal path
    prey = Automaton(letter="A", x=7.0, y=4.0, energy=50.0)
    sim.add(prey)

    calls = {"n": 0}

    def fake_choices(seq, weights=None, k=1):  # noqa: ARG001
        calls["n"] += 1
        # First call selects 'drop', second call picks 'right'
        return [4] if calls["n"] == 1 else [1]

    import conways_physics.sim as sim_mod

    monkeypatch.setattr(sim_mod.random, "choices", fake_choices)
    # Ensure visibility
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.0)

    rocks_before = len(sim.rocks)
    sim.step(0.1)
    assert len(sim.rocks) >= rocks_before + 1
