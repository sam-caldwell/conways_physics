from conways_physics.automata import Automaton


def test_tick_flashes_decrements_when_positive():
    a = Automaton(letter="A", x=0.0, y=0.0, energy=50.0)
    a.eat_flash = 2
    a.repro_flash = 1
    a.tick_flashes()
    assert a.eat_flash == 1
    assert a.repro_flash == 0

