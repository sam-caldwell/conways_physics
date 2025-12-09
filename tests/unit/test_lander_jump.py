from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import DAY_LENGTH_S, LANDER_JUMP_DISTANCE_CELLS
from unittest.mock import patch


def test_lander_can_jump_over_two_columns_up_three():
    sim = Simulation(width=10, height=20)
    # Create a 3-cell higher plateau starting at x=1 and x=2
    # base ground at x=0 is 12, higher ground at x=1 is 9, x=2 is 9
    sim.terrain = [12, 9, 9, 12, 12, 12, 12, 12, 12, 12]
    # Place lander at x=0 on air boundary, energetic
    a = Automaton(letter="E", x=0.0, y=sim.terrain[0] - 1, energy=100.0)
    sim.add(a)
    # Put prey toward the right to bias motion right
    prey = Automaton(letter="C", x=5.0, y=sim.terrain[5] - 1, energy=100.0)
    sim.add(prey)
    with patch('conways_physics.sim.random.random', return_value=0.0):
        sim.step(0.4)
    # Should have jumped to x=0 + 2
    assert int(round(a.x)) == (0 + LANDER_JUMP_DISTANCE_CELLS)
    # Landed on the target air boundary
    tx = int(round(a.x))
    assert int(round(a.y)) == sim.terrain[tx] - 1
    # Energy decreased by about two (plus small walking cost)
    assert a.energy <= 98.0 and a.energy >= 97.5


def test_lander_jump_has_seven_day_cooldown():
    sim = Simulation(width=10, height=20)
    sim.terrain = [12, 9, 9, 12, 12, 12, 12, 12, 12, 12]
    a = Automaton(letter="E", x=0.0, y=sim.terrain[0] - 1, energy=100.0)
    prey = Automaton(letter="C", x=5.0, y=sim.terrain[5] - 1, energy=100.0)
    sim.add(a)
    sim.add(prey)
    with patch('conways_physics.sim.random.random', return_value=0.0):
        sim.step(0.4)
    first_x = int(round(a.x))
    # Reset position back to 0 to test that second immediate jump does not occur
    a.x = 0.0
    a.y = sim.terrain[0] - 1
    with patch('conways_physics.sim.random.random', return_value=0.0):
        sim.step(0.4)
    # Should not have jumped again; position remains 0 or moves at most 1 due to regular movement/collision
    assert int(round(a.x)) in (0, 1)
    # Advance world time by 7 days without moving
    sim.world.t_abs += 7.0 * DAY_LENGTH_S + 0.1
    # Next step should allow another jump
    a.x = 0.0
    a.y = sim.terrain[0] - 1
    with patch('conways_physics.sim.random.random', return_value=0.0):
        sim.step(0.4)
    assert int(round(a.x)) == first_x
