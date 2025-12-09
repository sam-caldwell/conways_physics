from conways_physics.sim import Simulation
from conways_physics.species import is_flyer_letter, is_lander_letter


def test_seed_population_spawns_expected_number_and_positions():
    sim = Simulation(width=50, height=20)
    sim.configure_surface_for_view(50, 20, sea_level_offset=4, amplitude=3, seed=123)
    sim.seed_population(50, seed=1234)
    assert len(sim.automata) == 50
    # Validate positions/letters
    flyers = 0
    landers = 0
    for a in sim.automata:
        assert 0 <= a.x < sim.width
        assert 0 <= a.y < sim.height
        x = int(round(a.x))
        gy = sim.terrain[x]
        if is_lander_letter(a.letter):
            landers += 1
            assert int(round(a.y)) == int(round(gy))
        else:
            flyers += 1
            assert int(round(a.y)) <= int(round(gy))
        assert 0.0 <= a.energy <= 100.0
    assert flyers > 0 and landers > 0
