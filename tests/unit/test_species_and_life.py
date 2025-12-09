from conways_physics.species import (
    is_flyer_letter,
    is_lander_letter,
    pair_index,
    gender,
    letter_order,
    Species,
)
from conways_physics.life import step_life
from conways_physics.terrain import generate_random_terrain


def test_species_helpers():
    assert is_lander_letter("A") and not is_flyer_letter("A")
    assert is_flyer_letter("N") and not is_lander_letter("N")
    assert pair_index("A") == 0
    assert pair_index("B") == 0
    assert pair_index("C") == 1
    assert gender("A") == "male"
    assert gender("B") == "female"
    assert gender("Z") == "none"
    assert letter_order("A") < letter_order("B") < letter_order("Z")

    s = Species("Q")
    assert s.is_flyer and not s.is_lander
    assert s.pair == pair_index("Q")
    assert s.gender in ("male", "female")


def test_life_step_blinker_and_block():
    # Blinker toggles
    blinker = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]
    next_gen = step_life(blinker)
    assert next_gen == [
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]

    # Block stays stable
    block = [
        [1, 1],
        [1, 1],
    ]
    assert step_life(block) == block


def test_life_empty_grid_returns_empty():
    assert step_life([]) == []


def test_generate_random_terrain_seed_and_bounds():
    w, h = 20, 15
    t1 = generate_random_terrain(w, h, seed=123)
    t2 = generate_random_terrain(w, h, seed=123)
    assert t1 == t2
    assert len(t1) == w
    assert all(0 <= y < h for y in t1)
