from unittest.mock import patch

from conways_physics.app import ConwaysPhysics
from conways_physics.sim import Simulation


def _build_app() -> ConwaysPhysics:
    """Create an app instance and compose widgets without mounting the UI."""
    app = ConwaysPhysics()
    # Compose initializes `sim`, `gameplay`, and `status` but does not start timers
    _ = list(app.compose())
    return app


def test_app_starts_paused():
    app = _build_app()
    assert app.running is False


def test_bindings_include_spawn_range():
    keys = [b[0] for b in ConwaysPhysics.BINDINGS]
    actions = [b[1] for b in ConwaysPhysics.BINDINGS]
    assert "n" in keys
    assert "set_spawn_range" in actions


def test_on_spawn_range_set_sanitizes_values():
    app = _build_app()
    # Negative and inverted values get clamped and ordered
    app._on_spawn_range_set((0, -5))
    assert app.spawn_min == 1
    assert app.spawn_max == 1


def test_choose_spawn_total_with_range_inclusive():
    app = _build_app()
    app.spawn_min = 50
    app.spawn_max = 60
    # Repeat to exercise randomness bounds while keeping property-based assertion
    for _ in range(20):
        n = app._choose_spawn_total()
        assert 50 <= n <= 60


def test_choose_spawn_total_default_range_scaled_by_width():
    app = _build_app()
    # Default randomized range should be within 50..800 inclusive
    values = [app._choose_spawn_total() for _ in range(20)]
    assert all(50 <= v <= 800 for v in values)


def test_recycle_pauses_and_uses_spawn_range():
    app = _build_app()
    app.spawn_min = 90
    app.spawn_max = 110

    captured = {"called": False, "totals": []}

    def spy_seed(self: Simulation, total: int = 100, *, seed=None):  # type: ignore[override]
        captured["called"] = True
        captured["totals"].append(int(total))

    # Patch the class method before recycle creates a new Simulation instance
    with patch.object(Simulation, "seed_population_balanced", new=spy_seed):
        app.action_recycle()

    assert captured["called"] is True
    assert all(90 <= t <= 110 for t in captured["totals"])  # inclusive range
    # Ensure the app remains paused after recycle
    assert app.running is False
