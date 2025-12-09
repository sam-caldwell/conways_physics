from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_lander_can_climb_one_cell_but_not_two():
    sim = Simulation(width=3, height=10)
    # Terrain: step up by 1 then by 2
    sim.terrain = [7, 8, 10]
    a = Automaton(letter="C", x=0.0, y=6.0, energy=100.0)
    sim.add(a)
    # Place prey one cell to the right to bias motion
    prey = Automaton(letter="A", x=1.0, y=7.0, energy=100.0)
    sim.add(prey)
    sim.step(0.5)
    # Should have moved to column 1 (climb 1)
    assert int(round(a.x)) == 1
    # Now bias toward column 2; a cannot climb +2
    prey.x = 2.0
    sim.step(0.5)
    # Should stay at column 1 due to climb restriction
    assert int(round(a.x)) == 1
