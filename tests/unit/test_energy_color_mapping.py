from conways_physics.renderer import _energy_style, COLOR_TABLE


def test_energy_color_scale_mapping_edges():
    # Energy 1 -> idx 0
    assert _energy_style(1.0) == COLOR_TABLE[0]
    # Energy 100 -> idx 15
    assert _energy_style(100.0) == COLOR_TABLE[15]


def test_energy_color_scale_mapping_midpoints():
    # Energy 50 -> floor((49/99)*15) == 7
    assert _energy_style(50.0) == COLOR_TABLE[7]
    # Energy below 1 still maps to lowest color
    assert _energy_style(0.0) == COLOR_TABLE[0]
