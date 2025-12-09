from conways_physics.sim import Simulation
from conways_physics.automata import Automaton, Rock


def test_lander_blocked_by_corpse_cell():
    sim = Simulation(width=5, height=10)
    # Flat terrain
    sim.terrain = [7, 7, 7, 7, 7]
    # Corpse at (y=6, x=1)
    sim.corpses.add((6, 1))
    # Lander at x=0, y=6 moving right into corpse cell
    a = Automaton(letter="A", x=0.0, y=6.0, energy=100.0, vx=5.0)
    sim.add(a)
    sim.step(0.2)
    # Should not enter (6,1); remains at previous column
    assert int(round(a.x)) == 0


def test_lander_blocked_by_rock_cell():
    sim = Simulation(width=5, height=10)
    sim.terrain = [7, 7, 7, 7, 7]
    # Rock at (y=6, x=1)
    r = Rock(x=1.0, y=6.0, vy=0.0, active=True)
    sim.rocks.append(r)
    a = Automaton(letter="A", x=0.0, y=6.0, energy=100.0, vx=5.0)
    sim.add(a)
    sim.step(0.2)
    assert int(round(a.x)) == 0
