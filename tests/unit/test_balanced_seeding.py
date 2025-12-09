from conways_physics.sim import Simulation
from conways_physics.species import is_flyer_letter


def test_seed_population_balanced_10_percent_flyers():
    sim = Simulation(width=80, height=30)
    sim.configure_surface_for_view(80, 30, sea_level_offset=4, amplitude=2, seed=42)
    sim.seed_population_balanced(100, seed=123)
    n = len(sim.automata)
    assert n == 100
    flyers = sum(1 for a in sim.automata if is_flyer_letter(a.letter))
    landers = n - flyers
    assert flyers == 10 and landers == 90
