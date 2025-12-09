from __future__ import annotations

from dataclasses import dataclass

LAND_START = ord("A")
FLY_START = ord("N")


def is_flyer_letter(letter: str) -> bool:
    c = letter.upper()
    return ord(c) >= FLY_START and ord(c) <= ord("Z")


def is_lander_letter(letter: str) -> bool:
    c = letter.upper()
    return ord("A") <= ord(c) <= ord("M")


def pair_index(letter: str) -> int:
    """Return the 0-based species pair index for letters A..Y.

    A/B -> 0, C/D -> 1, ... Y (with X/Y as 11). Z returns 12.
    """
    c = letter.upper()
    i = max(0, min(25, ord(c) - LAND_START))
    return i // 2


def gender(letter: str) -> str:
    """Return 'male' or 'female' for A..Y pairs; 'none' for Z."""
    c = letter.upper()
    if c == "Z":
        return "none"
    return "male" if ((ord(c) - LAND_START) % 2 == 0) else "female"


def letter_order(letter: str) -> int:
    return ord(letter.upper())


@dataclass(frozen=True)
class Species:
    letter: str

    @property
    def is_flyer(self) -> bool:
        return is_flyer_letter(self.letter)

    @property
    def is_lander(self) -> bool:
        return is_lander_letter(self.letter)

    @property
    def pair(self) -> int:
        return pair_index(self.letter)

    @property
    def gender(self) -> str:
        return gender(self.letter)

