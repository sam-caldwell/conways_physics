from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_flyer_pair_reproduction_requires_altitude():
    sim = Simulation(width=20, height=50)
    # Choose a column, compute ground
    x = 10
    gy = int(round(sim.ground_y_at(x)))
    # N/O pair at same cell below altitude threshold
    n = Automaton(letter="N", x=float(x), y=float(max(0, gy - 5)), energy=80.0)
    o = Automaton(letter="O", x=float(x), y=float(max(0, gy - 5)), energy=80.0)
    sim.add(n)
    sim.add(o)
    sim.step(0.0)
    assert not any(a.letter in ("N", "O") and a is not n and a is not o for a in sim.automata)

    # Move pair high enough to reproduce
    n.y = float(max(0, gy - 25))
    o.y = float(max(0, gy - 25))
    sim.step(0.0)
    assert any(a.letter in ("N", "O") and a is not n and a is not o for a in sim.automata)
