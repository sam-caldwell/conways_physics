from conways_physics.app import ConwaysPhysics
from conways_physics.automata import Automaton
from conways_physics.sim import Simulation
from conways_physics.config import DAY_LENGTH_S


def test_status_shows_reproduction_count():
    app = ConwaysPhysics()
    _ = list(app.compose())
    # Ensure empty sim; add a reproducing pair (C/D) with enough energy
    app.sim.automata.clear()
    a = Automaton(letter="C", x=5.0, y=5.0, energy=70.0)
    b = Automaton(letter="D", x=5.0, y=5.0, energy=70.0)
    app.sim.add(a)
    app.sim.add(b)
    app.sim.step(0.0)
    app._update_status()
    # Expect reproduction count to be 1 in status text
    assert "repro=" in app.status.text
    # crude parse: find 'repro=1' substring
    assert "repro=1" in app.status.text


def test_autospawn_does_not_increment_reproduction_count():
    sim = Simulation(width=10, height=10)
    # Single A that hasn't reproduced in >=30 days should auto-spawn C/D
    a = Automaton(letter="A", x=2.0, y=5.0, energy=80.0)
    sim.add(a)
    a.since_repro_s = 30.0 * DAY_LENGTH_S
    before_spawned = sim.spawned_total
    sim.step(0.0)
    # Spawned increased but reproduction events remain unchanged
    assert sim.spawned_total > before_spawned
    assert sim.reproductions_total == 0
