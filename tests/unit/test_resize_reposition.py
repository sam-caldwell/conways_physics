from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_configure_surface_rescales_automata_positions():
    sim = Simulation(width=10, height=12)
    sim.configure_surface_for_view(10, 12, sea_level_offset=4, amplitude=1, seed=1)
    # Place a lander at left edge on surface
    x0 = 0
    gy0 = sim.terrain[x0]
    lander = Automaton(letter="A", x=float(x0), y=float(gy0), energy=50.0)
    # Place a flyer near right edge two above surface
    x1 = 9
    gy1 = sim.terrain[x1]
    flyer = Automaton(letter="N", x=float(x1), y=float(max(0, gy1 - 2)), energy=50.0)
    sim.add(lander)
    sim.add(flyer)

    # Resize width to 20; positions should scale
    sim.configure_surface_for_view(20, 12, sea_level_offset=4, amplitude=1, seed=1)

    # Landers remain on surface at their scaled column
    new_ix0 = int(round(lander.x))
    assert 0 <= new_ix0 < sim.width
    assert int(round(lander.y)) == int(round(sim.terrain[new_ix0])) - 1

    # Flyers preserve height above ground (approx two rows)
    new_ix1 = int(round(flyer.x))
    new_gy1 = int(round(sim.terrain[new_ix1]))
    assert int(round(new_gy1 - flyer.y)) >= 2  # at least as high above
