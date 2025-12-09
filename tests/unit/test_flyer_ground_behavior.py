from conways_physics.automata import Automaton


def test_flyer_grounded_cannot_translate():
    ground_y = 10.0
    # Energy below flying threshold; on boundary; non-zero vx should be zeroed
    f = Automaton(letter="N", x=5.0, y=ground_y - 1.0, energy=15.0, vx=2.0, vy=0.0)
    f.tick_motion(0.5, ground_y=ground_y, width=100)
    assert f.y == ground_y - 1.0
    assert f.vx == 0.0
    # x should not change when immobilized
    assert f.x == 5.0
