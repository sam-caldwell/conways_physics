from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_c_d_digs_when_moving_horizontally_into_terrain():
    sim = Simulation(width=3, height=20)
    # Set a small step up at x=1 to block at y
    sim.terrain = [10, 9, 10]
    # Place C at x=0 on air boundary, energetic
    c = Automaton(letter="C", x=0.0, y=sim.terrain[0] - 1, energy=100.0)
    sim.add(c)
    # Place a prey to the right to bias motion toward +x
    prey = Automaton(letter="A", x=2.0, y=sim.terrain[2] - 1, energy=100.0)
    sim.add(prey)
    # Step half a second so C moves roughly one column right
    sim.step(0.5)
    # C should have dug the blocking cell at x=1, raising surface to at least y+1
    xi = 1
    assert sim.terrain[xi] >= int(round(c.y)) + 1
    # And C occupies the carved cell
    assert int(round(c.x)) == 1


def test_non_cd_does_not_dig_and_is_blocked():
    sim = Simulation(width=3, height=20)
    sim.terrain = [10, 9, 10]
    a = Automaton(letter="E", x=0.0, y=sim.terrain[0] - 1, energy=100.0)
    sim.add(a)
    # Place prey to the right, but climb and collision should block
    prey = Automaton(letter="A", x=2.0, y=sim.terrain[2] - 1, energy=100.0)
    sim.add(prey)
    sim.step(0.5)
    # Should not have moved into column 1 due to collision
    assert int(round(a.x)) == 0
    # Terrain unchanged at x=1
    assert sim.terrain[1] == 9

