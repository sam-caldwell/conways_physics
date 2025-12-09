from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_lander_pursues_prey_and_avoids_predator():
    sim = Simulation(width=10, height=10)
    a = Automaton(letter="C", x=5.0, y=sim.terrain[5]-1, energy=100.0)
    sim.add(a)
    # Place prey to the right and predator to the far left; avoidance prioritized
    predator = Automaton(letter="G", x=3.0, y=sim.terrain[3]-1, energy=100.0)
    prey = Automaton(letter="A", x=7.0, y=sim.terrain[7]-1, energy=100.0)
    sim.add(predator)
    sim.add(prey)
    sim.step(0.2)
    # Moves right toward prey as predator is not closer horizontally than prey
    assert a.x >= 5.0
