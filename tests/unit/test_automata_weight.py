from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_new_automaton_weight_within_range():
    a = Automaton(letter="A", x=0.0, y=0.0)
    assert 20.0 <= a.weight <= 100.0


def test_seeded_automata_weights_within_range():
    sim = Simulation(width=20, height=10)
    sim.configure_surface_for_view(20, 10, sea_level_offset=4, amplitude=0, seed=42)
    sim.seed_population_balanced(25, seed=123)
    assert len(sim.automata) == 25
    assert all(20.0 <= a.weight <= 100.0 for a in sim.automata)


def test_reproduction_newborn_weight_within_range():
    sim = Simulation(width=10, height=20)
    # Place C/D pair to reproduce
    c = Automaton(letter="C", x=5.0, y=10.0, energy=70.0)
    d = Automaton(letter="D", x=5.0, y=10.0, energy=70.0)
    sim.add(c)
    sim.add(d)
    sim.step(0.0)
    newborns = [a for a in sim.automata if a is not c and a is not d]
    assert len(newborns) >= 1
    assert 20.0 <= newborns[0].weight <= 100.0


def test_z_asexual_newborn_weight_within_range():
    sim = Simulation(width=10, height=50)
    x = 3
    gy = int(round(sim.ground_y_at(x)))
    z = Automaton(letter="Z", x=float(x), y=float(max(0, gy - 25)), energy=95.0)
    sim.add(z)
    sim.step(0.0)
    children = [a for a in sim.automata if a is not z and a.letter == "Z"]
    assert len(children) >= 1
    assert 20.0 <= children[0].weight <= 100.0
