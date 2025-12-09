from conways_physics.automata import Automaton


def test_weight_influences_flyer_vertical_response():
    ground_y = 10.0
    # Two flyers mid-air with same energy and vy; heavier should have higher (less negative) vy after step
    light = Automaton(letter="N", x=0.0, y=ground_y - 2.0, energy=50.0, vx=0.0, vy=-1.0)
    heavy = Automaton(letter="N", x=0.0, y=ground_y - 2.0, energy=50.0, vx=0.0, vy=-1.0)
    light.weight = 20.0
    heavy.weight = 100.0
    dt = 0.1
    # Avoid wrap, width irrelevant here
    light.tick_motion(dt, ground_y=ground_y, width=10)
    heavy.tick_motion(dt, ground_y=ground_y, width=10)
    assert heavy.vy > light.vy  # heavier is pulled down more (less negative vy)


def test_weight_influences_lander_friction():
    ground_y = 10.0
    # Two landers on ground; heavier should slow more due to added friction term
    light = Automaton(letter="A", x=0.0, y=ground_y - 1.0, energy=50.0, vx=1.0, vy=0.0)
    heavy = Automaton(letter="A", x=0.0, y=ground_y - 1.0, energy=50.0, vx=1.0, vy=0.0)
    light.weight = 20.0
    heavy.weight = 100.0
    dt = 1.0
    light.tick_motion(dt, ground_y=ground_y, width=10)
    heavy.tick_motion(dt, ground_y=ground_y, width=10)
    assert abs(heavy.vx) < abs(light.vx)
