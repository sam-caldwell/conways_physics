from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_lander_tries_right_when_left_blocked():
    sim = Simulation(width=5, height=20)
    # Terrain with a sharp uphill to the left of x=2
    # y increases downward; smaller y is higher ground. Moving from 2->1 is an ascent of 3 rows.
    sim.terrain = [6, 6, 9, 9, 9]
    # Place lander at x=2 on air boundary, with a prey to the left to bias leftward intent
    a = Automaton(letter="E", x=2.0, y=sim.terrain[2] - 1, energy=100.0)
    prey = Automaton(letter="C", x=1.0, y=sim.terrain[1] - 1, energy=100.0)
    sim.add(a)
    sim.add(prey)
    # Step enough to move one column if allowed
    sim.step(0.5)
    # Left is blocked by terrain; should try right instead
    assert int(round(a.x)) in (2, 3)
    assert int(round(a.x)) != 1


def test_lander_tries_left_when_right_blocked():
    sim = Simulation(width=5, height=20)
    # Terrain with a sharp uphill to the right of x=2
    sim.terrain = [9, 9, 9, 6, 6]
    # Place lander at x=2 on air boundary, with a prey to the right to bias rightward intent
    a = Automaton(letter="E", x=2.0, y=sim.terrain[2] - 1, energy=100.0)
    prey = Automaton(letter="C", x=3.0, y=sim.terrain[3] - 1, energy=100.0)
    sim.add(a)
    sim.add(prey)
    sim.step(0.5)
    # Right is blocked by terrain; should try left instead
    assert int(round(a.x)) in (1, 2)
    assert int(round(a.x)) != 3
