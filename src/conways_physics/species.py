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
    """Return a pair index grouping letters into male/female pairs.

    Landers (A..M): A/B->0, C/D->1, ..., M/N->6.
    Flyers (N..Z):  N/O->100, P/Q->101, R/S->102, T/U->103, V/W->104, X/Y->105.
    Z does not have a gender; return a distinct index (999) but pair reproduction excludes Z.
    """
    c = letter.upper()
    if c == "Z":
        return 999
    if c < "N":  # A..M landers, simple adjacent pairs
        i = ord(c) - LAND_START
        return i // 2
    # Flyers use explicit adjacent pairs starting at N/O
    flyer_pairs = [
        ("N", "O"),
        ("P", "Q"),
        ("R", "S"),
        ("T", "U"),
        ("V", "W"),
        ("X", "Y"),
    ]
    for idx, (a, b) in enumerate(flyer_pairs):
        if c == a or c == b:
            return 100 + idx
    # Default fallback
    return 1000


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
