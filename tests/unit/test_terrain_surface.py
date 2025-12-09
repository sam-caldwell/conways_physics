from conways_physics.terrain import generate_surface


def test_generate_surface_baseline_and_bounds():
    w, h = 80, 30
    surf = generate_surface(w, h, sea_level_offset=4, amplitude=3, seed=42)
    assert len(surf) == w
    baseline = h - 4
    lo, hi = baseline - 3, baseline + 3
    assert all(lo <= y <= hi for y in surf)
    assert any(y != baseline for y in surf)  # has variation
