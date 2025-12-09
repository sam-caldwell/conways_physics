from conways_physics.sim import Simulation
from conways_physics.automata import Automaton
from conways_physics.config import E_MEAL


def test_ab_sunlight_gain_during_day():
    sim = Simulation(width=10, height=10)
    a = Automaton(letter="A", x=5, y=5, energy=10.0)
    sim.add(a)
    # At t=0 it's day
    per_sec = sim.world.sunlight_energy_gain(E_MEAL)
    sim.step(1.0)
    assert a.energy >= 10.0 + per_sec - 1e-6


def test_predation_land_same_cell_order_and_cannibal_only_when_starved():
    sim = Simulation(width=10, height=10)
    # Higher letter eats lower letter in same cell
    attacker = Automaton(letter="D", x=1, y=5, energy=50.0)
    prey = Automaton(letter="B", x=1, y=5, energy=50.0)
    sim.add(attacker)
    sim.add(prey)
    sim.step(0.0)
    assert prey.alive is False
    assert attacker.energy > 50.0

    # Cannibalism only if starved (<=10)
    sim = Simulation(width=10, height=10)
    eater = Automaton(letter="C", x=2, y=5, energy=10.0)
    same_species = Automaton(letter="D", x=2, y=5, energy=50.0)
    sim.add(eater)
    sim.add(same_species)
    sim.step(0.0)
    assert same_species.alive is False


def test_flyer_attacks_lander_from_above_and_lander_eats_adjacent_flyer(monkeypatch):
    sim = Simulation(width=10, height=10)
    flyer = Automaton(letter="N", x=5, y=3, energy=50.0)
    lander = Automaton(letter="A", x=5, y=5, energy=50.0)
    sim.add(flyer)
    sim.add(lander)
    # ensure visibility at distance 2
    import conways_physics.sim as sim_mod
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.0)
    sim.step(0.0)
    # Flyer is above lander at start, should attack
    assert lander.alive is False

    # Landers can eat adjacent flyers above/left/right
    sim = Simulation(width=10, height=10)
    lander = Automaton(letter="A", x=5, y=5, energy=50.0)
    flyer = Automaton(letter="N", x=5, y=3, energy=50.0)
    sim.add(lander)
    sim.add(flyer)
    sim.step(0.0)
    assert flyer.alive is False


def test_z_asexual_reproduction_when_flying_and_high_altitude():
    sim = Simulation(width=10, height=40)
    # Place Z at altitude >= 20 above ground
    x = 5
    gy = int(round(sim.ground_y_at(x)))
    z = Automaton(letter="Z", x=float(x), y=float(max(0, gy - 25)), energy=95.0)
    sim.add(z)
    sim.step(0.0)
    assert any(a is not z and a.letter == "Z" for a in sim.automata)


def test_rock_drops_and_damages_target():
    sim = Simulation(width=10, height=10)
    x = Automaton(letter="X", x=5, y=3, energy=80.0)
    target = Automaton(letter="A", x=5, y=6, energy=50.0)
    sim.add(x)
    sim.add(target)
    did_drop = sim.drop_rock_from(x)
    assert did_drop is True
    # Step until rock falls onto target (a few seconds is plenty)
    for _ in range(30):
        sim.step(0.1)
        if not target.alive:
            break
    assert target.energy < 50.0 or target.alive is False


def test_explicit_rock_collision_with_flyer():
    sim = Simulation(width=10, height=10)
    flyer = Automaton(letter="N", x=5, y=3, energy=50.0, vx=0.0, vy=0.0)
    sim.add(flyer)
    # Place a rock above, falling fast to ensure collision in a couple steps
    from conways_physics.automata import Rock

    sim.rocks.append(Rock(x=5.0, y=1.0, vy=10.0, active=True))
    pre = flyer.energy
    for _ in range(10):
        sim.step(0.1)
        if not sim.rocks[-1].active:
            break
    assert flyer.energy < pre


def test_movement_gating_and_world_wrap():
    sim = Simulation(width=8, height=10)
    slow = Automaton(letter="A", x=0, y=5, energy=5.0, vx=5.0)
    sim.add(slow)
    sim.step(1.0)
    # No movement when energy too low
    assert int(round(slow.x)) == 0

    # Movement and wrap
    fast = Automaton(letter="A", x=7.5, y=5, energy=50.0, vx=5.0)
    sim.add(fast)
    sim.step(1.0)
    assert 0 <= fast.x < sim.width


def test_flyer_distance_attack_within_two_cells(monkeypatch):
    sim = Simulation(width=10, height=10)
    # Landers can eat flyers within two cells horizontally (left/right)
    lander = Automaton(letter="A", x=5, y=5, energy=50.0)
    flyer = Automaton(letter="N", x=7, y=5, energy=50.0)
    sim.add(flyer)
    sim.add(lander)
    # ensure detection at distance 2 passes the coin toss
    # Patch the sim module's RNG to ensure visibility at distance=2
    import conways_physics.sim as sim_mod
    monkeypatch.setattr(sim_mod.random, "random", lambda: 0.0)
    sim.step(0.0)
    assert flyer.alive is False
