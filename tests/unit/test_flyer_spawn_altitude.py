from conways_physics.sim import Simulation
from conways_physics.species import is_flyer_letter
from conways_physics.config import FLYER_MIN_ALTITUDE_REPRO


def _assert_flyer_altitudes(sim: Simulation) -> None:
    for a in sim.automata:
        if not is_flyer_letter(a.letter):
            continue
        x = int(round(a.x))
        gy = int(round(sim.terrain[x]))
        min_alt = int(round(FLYER_MIN_ALTITUDE_REPRO))
        # y must be within top third and also at least min_alt above terrain when possible
        top_third_cap = sim.height // 3
        terrain_cap = max(0, gy - min_alt)
        y_max = min(top_third_cap, terrain_cap)
        assert int(round(a.y)) <= y_max


def test_seed_population_flyers_spawn_high_top_third_and_altitude():
    # Choose a height where gy - min_alt < height//3 so altitude gating is binding
    sim = Simulation(width=80, height=30)
    sim.configure_surface_for_view(80, 30, sea_level_offset=4, amplitude=2, seed=7)
    sim.seed_population(120, seed=9)
    _assert_flyer_altitudes(sim)


def test_seed_population_balanced_flyers_spawn_high_top_third_and_altitude():
    # Choose a height where top-third gating is binding
    sim = Simulation(width=120, height=60)
    sim.configure_surface_for_view(120, 60, sea_level_offset=4, amplitude=3, seed=11)
    sim.seed_population_balanced(100, seed=13)
    _assert_flyer_altitudes(sim)

