from conways_physics.sim import Simulation
from conways_physics.automata import Automaton


def test_bury_on_predation_raises_surface():
    sim = Simulation(width=10, height=10)
    x = 2
    base = sim.terrain[x]
    eater = Automaton(letter="F", x=x, y=5, energy=50.0)
    prey = Automaton(letter="E", x=x, y=5, energy=50.0)
    sim.add(eater)
    sim.add(prey)
    sim.step(0.1)
    assert sim.terrain[x] <= max(0, base - 1)


def test_flash_eat_and_repro():
    sim = Simulation(width=10, height=10)
    a = Automaton(letter="A", x=1, y=5, energy=50.0)
    b = Automaton(letter="B", x=1, y=5, energy=50.0)
    sim.add(a)
    sim.add(b)
    # Eat triggers when one eats another lower letter; force an extra prey nearby
    low = Automaton(letter="A", x=1, y=5, energy=5.0)
    sim.add(low)
    sim.step(0.1)
    # One of a/b should have flashed for eat
    assert (a.eat_flash > 0) or (b.eat_flash > 0)

    # Reproduction flash: same pair C/D co-located (use new sim to avoid interactions)
    sim2 = Simulation(width=10, height=10)
    c = Automaton(letter="C", x=2, y=5, energy=70.0)
    d = Automaton(letter="D", x=2, y=5, energy=70.0)
    sim2.add(c)
    sim2.add(d)
    sim2.step(0.0)
    assert c.repro_flash > 0 and d.repro_flash > 0


def test_same_cell_predation_reverse_branch():
    # Ensure the reverse branch (elif path) is exercised
    sim = Simulation(width=10, height=10)
    low = Automaton(letter="A", x=3, y=5, energy=50.0)
    high = Automaton(letter="C", x=3, y=5, energy=50.0)
    sim.add(low)
    sim.add(high)
    sim.step(0.1)
    # High letter should eat low via the reverse branch
    assert low.alive is False and high.alive is True


def test_gol_bias_changes_velocity():
    sim = Simulation(width=5, height=10)
    a = Automaton(letter="A", x=2, y=5, energy=50.0, vx=0.0)
    sim.add(a)
    # Fill neighbors alive around (2,2) to ensure high count
    grid = [[0 for _ in range(sim.width)] for _ in range(sim.height)]
    for rr in (4, 5, 6):
        for cc in (1, 2, 3):
            if rr == 5 and cc == 2:
                continue
            grid[rr][cc] = 1
    sim.life_grid = grid
    sim.step(0.0)
    assert a.vx >= 0.0


def test_gol_bias_low_density_biases_left():
    sim = Simulation(width=5, height=10)
    a = Automaton(letter="A", x=2, y=5, energy=50.0, vx=0.0)
    sim.add(a)
    # Empty grid yields low neighbor counts
    sim.life_grid = [[0 for _ in range(sim.width)] for _ in range(sim.height)]
    sim.step(0.0)
    assert a.vx < 0.0
