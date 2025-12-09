from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_lander_blocked_by_terrain_step():
    sim = Simulation(width=5, height=10)
    # Create a terrain step higher at x=1
    sim.terrain = [8, 5, 8, 8, 8]
    # Place a lander at x=0 on air boundary (y=terrain-1)
    a = Automaton(letter="A", x=0.0, y=sim.terrain[0] - 1, energy=100.0, vx=5.0)
    sim.add(a)
    # One second step would move into x ≈ 5 (wrapped), but collision with x=1 blocks immediately
    sim.step(0.2)
    # Should not have moved into column 1 because y would collide (>= terrain[1])
    assert int(round(a.x)) == 0


def test_flyer_may_pass_over_terrain_if_above_blocks():
    sim = Simulation(width=5, height=10)
    sim.terrain = [8, 6, 4, 4, 4]
    # Flyer near ground at x=1, moving left into higher terrain at x=0
    f = Automaton(letter="N", x=1.0, y=6 - 1, energy=100.0, vx=-10.0, vy=0.0)
    sim.add(f)
    sim.step(0.1)
    # Allowed to move over columns as long as not entering block cells
    assert int(round(f.x)) == 0
    assert int(round(f.y)) < sim.terrain[0]
