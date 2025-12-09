from conways_physics.world import World
from conways_physics.config import DAY_LENGTH_S, DAYLIGHT_S, E_MEAL


def test_world_ticks_and_day_night_cycle():
    w = World()
    assert w.t_abs == 0.0
    assert w.is_day is True

    # Advance to just before night
    w.tick(DAYLIGHT_S - 0.1)
    assert w.is_day is True

    # Cross into night
    w.tick(0.2)
    assert w.is_day is False

    # Wrap around into the next day
    w.tick(DAY_LENGTH_S - DAYLIGHT_S)
    assert w.is_day is True


def test_sunlight_energy_rate_is_consistent():
    w = World()
    per_sec = w.sunlight_energy_gain(E_MEAL)
    # Over the daylight window, total energy equals one quarter of a meal
    total_gain = per_sec * DAYLIGHT_S
    assert abs(total_gain - (0.25 * E_MEAL)) < 1e-6


def test_tick_ignores_negative_dt():
    w = World()
    w.tick(-10.0)
    assert w.t_abs == 0.0


def test_sunlight_energy_rate_with_zero_daylight(monkeypatch):
    import conways_physics.world as world

    w = World()
    old = world.DAYLIGHT_S
    try:
        world.DAYLIGHT_S = 0.0
        assert w.sunlight_energy_gain(E_MEAL) == 0.0
    finally:
        world.DAYLIGHT_S = old


def test_sunlight_energy_rate_clamped_to_max():
    # Choose an unrealistic meal energy to force clamping above ENERGY_MAX
    w = World()
    huge_meal = 1e9
    per_sec = w.sunlight_energy_gain(huge_meal)
    # per-second value should not exceed ENERGY_MAX when clamped
    from conways_physics.config import ENERGY_MAX

    assert per_sec == ENERGY_MAX
