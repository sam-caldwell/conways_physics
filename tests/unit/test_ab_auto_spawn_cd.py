from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import DAY_LENGTH_S


def test_ab_autospawn_cd_after_30_days_adjacent():
    sim = Simulation(width=10, height=10)
    x = 5
    gy = sim.terrain[x]
    a = Automaton(letter="A", x=float(x), y=float(gy - 2), energy=100.0)
    sim.add(a)
    # Ensure one adjacent cell is free and non-terrain: up from current
    # Advance just over 30 days
    sim.step(30.0 * DAY_LENGTH_S + 0.1)
    # Should have spawned one C/D in an adjacent cell
    cds = [b for b in sim.automata if b is not a and b.letter.upper() in ("C", "D")]
    assert len(cds) >= 1
    child = cds[0]
    ax, ay = int(round(a.x)), int(round(a.y))
    cx, cy = int(round(child.x)), int(round(child.y))
    assert (abs(ax - cx) + abs(ay - cy)) == 1  # 4-neighborhood


def test_ab_no_autospawn_when_surrounded():
    sim = Simulation(width=10, height=10)
    x = 5
    gy = sim.terrain[x]
    a = Automaton(letter="A", x=float(x), y=float(gy - 2), energy=100.0)
    sim.add(a)
    # Surround with blockers in the four adjacent cells
    up = Automaton(letter="E", x=float(x), y=float(gy - 3), energy=100.0)
    left = Automaton(letter="E", x=float(x - 1), y=float(gy - 2), energy=100.0)
    right = Automaton(letter="E", x=float(x + 1), y=float(gy - 2), energy=100.0)
    down = Automaton(letter="E", x=float(x), y=float(gy - 1), energy=100.0)
    for b in (up, left, right, down):
        sim.add(b)
    # Advance time
    sim.step(30.0 * DAY_LENGTH_S + 0.1)
    # No new C/D spawned
    cds = [b for b in sim.automata if b.letter.upper() in ("C", "D") and b is not a]
    assert len(cds) == 0
