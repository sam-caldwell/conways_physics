from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import DAY_LENGTH_S
from conways_physics.species import is_flyer_letter


def test_lander_transforms_after_30_days():
    sim = Simulation(width=10, height=10)
    # Flat terrain; place an A on the ground
    x = 5
    gy = sim.terrain[x]
    a = Automaton(letter="A", x=float(x), y=float(gy - 1), energy=100.0)
    sim.add(a)
    # Advance time by just over 30 days
    sim.step(30.0 * DAY_LENGTH_S + 0.1)
    assert a.letter.upper() == "C"
    assert is_flyer_letter(a.letter) is False


def test_lander_may_become_flyer_after_transform():
    sim = Simulation(width=10, height=10)
    x = 2
    gy = sim.terrain[x]
    m = Automaton(letter="M", x=float(x), y=float(gy - 1), energy=100.0)
    sim.add(m)
    # After 30 days, M should become O (a flyer)
    sim.step(30.0 * DAY_LENGTH_S + 0.1)
    assert m.letter.upper() == "O"
    assert is_flyer_letter(m.letter) is True

