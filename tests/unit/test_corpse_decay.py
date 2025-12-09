from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import CORPSE_DECAY_SECONDS


def test_corpse_decays_into_terrain():
    sim = Simulation(width=10, height=20)
    x = 3
    base = sim.terrain[x]
    # Create a corpse at (terrain-1, x)
    a = Automaton(letter="A", x=float(x), y=float(sim.terrain[x]-1), energy=0.0)
    sim._bury(a)
    assert (sim.terrain[x] - 1, x) in sim.corpses
    sim.step(CORPSE_DECAY_SECONDS + 0.1)
    # Terrain should have increased stack (y decreases by 1)
    assert sim.terrain[x] == max(0, base - 1)
    # Corpse marker cleared
    assert (sim.terrain[x] - 1, x) not in sim.corpses
