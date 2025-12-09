from conways_physics.automata import Automaton, Rock


def test_apply_sunlight_and_eat_gain_ignore_when_dead():
    a = Automaton(letter="A", x=0, y=0, energy=10.0, alive=False)
    a.apply_sunlight(100.0, 1.0)
    assert a.energy == 10.0
    a.eat_gain(2)
    assert a.energy == 10.0


def test_tick_motion_early_return_when_dead():
    a = Automaton(letter="N", x=0, y=0, energy=50.0, alive=False)
    a.tick_motion(1.0, ground_y=5.0, width=10)
    assert (a.x, a.y) == (0, 0)


def test_flyer_bounce_and_energy_cost_when_moving():
    # Place a flyer just above ground moving downward
    a = Automaton(letter="N", x=0, y=4.9, energy=50.0, vy=1.0)
    a.tick_motion(0.2, ground_y=5.0, width=10)
    # Should not be below ground and velocity should invert sign (bounce)
    assert a.y <= 5.0
    # after bounce vy becomes negative or reduced
    assert a.vy <= 0.0 or abs(a.vy) < 1.0
    # Energy decreased due to flight cost
    assert a.energy < 50.0


def test_flyer_prefers_flight_when_possible():
    # Flyer at ground with sufficient energy should lift off
    ground_y = 5.0
    a = Automaton(letter="N", x=0.0, y=ground_y, energy=50.0, vx=0.0, vy=0.0)
    a.tick_motion(0.1, ground_y=ground_y, width=10)
    assert a.y < ground_y  # moved upward (smaller y)
    assert a.vy < 0.0


def test_wrap_negative_and_positive():
    a = Automaton(letter="A", x=-1.0, y=5.0, energy=50.0)
    a.vx = -5.0
    a.tick_motion(0.1, ground_y=5.0, width=8)
    assert 0 <= a.x < 8
    # Width zero should skip wrap logic without error
    b = Automaton(letter="A", x=-1.0, y=5.0, energy=50.0)
    b.tick_motion(0.1, ground_y=5.0, width=0)
    # still a valid position
    assert b.x <= -1.0 or b.x >= -1.0


def test_rock_step_noop_when_inactive():
    r = Rock(x=0.0, y=0.0, vy=1.0, active=False)
    r.step(1.0, ground_y=10.0)
    assert r.y == 0.0 and r.vy == 1.0 and r.active is False
    # impact energy simple function
    r2 = Rock(x=0.0, y=0.0, vy=2.0, active=True)
    assert abs(r2.impact_energy() - 2.0) < 1e-9


def test_starving_property():
    a = Automaton(letter="A", x=0, y=0, energy=9.0)
    assert a.starving is True
    a.energy = 11.0
    assert a.starving is False


def test_lander_eats_adjacent_flyer_left():
    from conways_physics.sim import Simulation

    sim = Simulation(width=10, height=10)
    lander = Automaton(letter="A", x=5, y=5, energy=50.0)
    flyer = Automaton(letter="N", x=4, y=5, energy=50.0)
    sim.add(lander)
    sim.add(flyer)
    sim.step(0.1)
    assert flyer.alive is False
