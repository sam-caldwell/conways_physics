from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import ROCK_DECAY_SECONDS


def test_static_rock_blocks_and_decays_into_terrain():
    sim = Simulation(width=5, height=12)
    # Put a static rock at column 1 on the air boundary
    x = 1
    gy = int(round(sim.terrain[x]))
    ry = max(0, gy - 1)
    sim.rocks_static.add((ry, x))
    sim.rocks_age[(ry, x)] = ROCK_DECAY_SECONDS - 0.5
    # Lander at x=0 moving right should be blocked by rock at (ry,1)
    a = Automaton(letter="E", x=0.0, y=float(ry), energy=100.0, vx=3.0)
    sim.add(a)
    sim.step(0.2)
    # Should not have entered the rock cell
    assert int(round(a.x)) == 0
    # Advance time to trigger rock decay
    sim._decay_rocks(1.0)
    # Rock marker removed and terrain increased stack (y decreases by one)
    assert (ry, x) not in sim.rocks_static
    assert (ry, x) not in sim.rocks_age
    assert sim.terrain[x] == max(0, gy - 1)
