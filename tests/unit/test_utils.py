from conways_physics import get_version
from conways_physics.utils import clamp, is_day
from conways_physics.config import DAY_LENGTH_S, DAYLIGHT_S


def test_get_version_string():
    v = get_version()
    assert isinstance(v, str)
    assert v.count(".") >= 1


def test_clamp_basic():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_clamp_swapped_bounds():
    # Should be resilient to inverted bounds
    assert clamp(5, 10, 0) == 5
    assert clamp(-100, 10, 0) == 0
    assert clamp(100, 10, 0) == 10


def test_is_day_phase_boundaries():
    # Beginning of day is daylight
    assert is_day(0.0) is True
    # Just before the end of daylight
    assert is_day(DAYLIGHT_S - 1e-9) is True
    # At the exact boundary and beyond is night
    assert is_day(DAYLIGHT_S) is False
    # Wrap around day length
    t = DAY_LENGTH_S + (DAYLIGHT_S / 2.0)
    assert is_day(t) is True


def test_is_day_handles_zero_day_length(monkeypatch):
    import conways_physics.utils as utils

    # Temporarily force invalid day length to exercise the guard branch
    old = utils.DAY_LENGTH_S
    try:
        utils.DAY_LENGTH_S = 0.0
        assert is_day(123.45) is False
    finally:
        utils.DAY_LENGTH_S = old
