from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_starvation_increments_counter_and_corpse_marked():
    sim = Simulation(width=10, height=10)
    # Lander with very low energy that cannot move; passive drain should starve
    a = Automaton(letter="E", x=3.0, y=sim.ground_y_at(3.0) - 1.0, energy=0.05, vx=0.0, vy=0.0)
    sim.add(a)
    sim.step(1.0)
    assert a.alive is False
    assert sim.starved_total >= 1
    # Corpse placed on surface at column
    gx = int(round(a.x)) % sim.width
    gy = int(round(sim.ground_y_at(a.x))) - 1
    assert (gy, gx) in sim.corpses


def test_non_starvation_deaths_do_not_increment_starved():
    sim = Simulation(width=10, height=10)
    # Predation: higher rank eats lower
    high = Automaton(letter="D", x=1.0, y=5.0, energy=50.0)
    low = Automaton(letter="B", x=1.0, y=5.0, energy=50.0)
    sim.add(high)
    sim.add(low)
    sim.step(0.0)
    assert sim.starved_total == 0
