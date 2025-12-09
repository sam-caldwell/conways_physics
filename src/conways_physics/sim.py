from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .automata import Automaton, Rock
from .config import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    ROCK_MASS,
    ROCK_DROP_THRESHOLD,
    E_MEAL,
    ENERGY_MAX,
)
from .species import Species, is_flyer_letter, pair_index, letter_order
from .terrain import flat_terrain, generate_surface
from .life import step_life
from .world import World
from .utils import clamp
import random


def same_cell(a: Automaton, b: Automaton) -> bool:
    return int(round(a.x)) == int(round(b.x)) and int(round(a.y)) == int(round(b.y))


def adjacent_positions(ax: int, ay: int) -> List[Tuple[int, int]]:
    return [
        (ax, ay - 1),  # above
        (ax - 1, ay),  # left
        (ax + 1, ay),  # right
        (ax, ay + 1),  # below
    ]


@dataclass
class Simulation:
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    world: World = field(default_factory=World)
    terrain: List[int] = field(default_factory=list)
    automata: List[Automaton] = field(default_factory=list)
    rocks: List[Rock] = field(default_factory=list)
    life_grid: List[List[int]] = field(default_factory=list)
    auto_rocks: bool = False

    def configure_surface_for_view(
        self,
        width: int,
        height: int,
        *,
        sea_level_offset: int = 4,
        amplitude: int = 3,
        seed: int | None = None,
    ) -> None:
        """Resize the simulation to the view and regenerate the surface.

        The resulting surface spans the full width with a baseline 4 rows above the bottom
        by default, varying ±3 rows.
        """
        old_w, old_h = self.width, self.height
        old_terrain = self.terrain[:] if self.terrain else []
        self.width = max(0, int(width))
        self.height = max(1, int(height))
        self.terrain = generate_surface(self.width, self.height, sea_level_offset=sea_level_offset, amplitude=amplitude, seed=seed)
        # Resize life grid to match new view (clear)
        self.life_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        # Reposition existing automata to span new width/height
        if old_w and self.width and self.automata:
            scale_x = self.width / float(old_w)
            for a in self.automata:
                # Compute new x by scaling
                new_x = float(a.x) * scale_x
                # Compute surface-aligned y
                new_ix = int(round(new_x)) % self.width
                new_gy = int(round(self.terrain[new_ix])) if self.terrain else self.height - 1
                if is_flyer_letter(a.letter):
                    # Preserve height above ground
                    old_ix = int(round(a.x)) % max(1, old_w)
                    old_gy = int(round(old_terrain[old_ix])) if old_terrain else (old_h - 1)
                    above = max(0, old_gy - int(round(a.y)))
                    new_y = max(0, new_gy - above)
                else:
                    new_y = new_gy
                a.x = max(0.0, min(float(self.width - 1), new_x))
                a.y = float(max(0, min(self.height - 1, new_y)))

    def seed_population(self, count: int, *, seed: int | None = None) -> None:
        """Seed the world with a number of automata across random species and genders.

        - For paired species (A..Y), pick a species pair uniformly and then a gender (first/second letter) at random.
        - Include Z occasionally; Z has no gender and is a flyer.
        - Landers spawn on terrain at their column; flyers spawn a few rows above the terrain.
        - Energy is initialized in a moderate range to allow motion from the start.
        """
        if self.width <= 0:
            return
        rng = random.Random(seed)
        n = max(0, int(count))
        for _ in range(n):
            # 10% chance of Z (genderless flyer)
            if rng.random() < 0.1:
                letter = 'Z'
            else:
                pair = rng.randint(0, 12)  # 0..12 -> A/B .. Y
                base = ord('A') + 2 * pair
                letter = chr(base + rng.randint(0, 1))

            x = rng.randrange(self.width)
            gy = int(round(self.terrain[x])) if self.terrain else self.height - 1
            if is_flyer_letter(letter):
                y = max(0, gy - rng.randint(2, 5))
                vx = rng.uniform(-0.5, 0.5)
                vy = 0.0
            else:
                y = gy
                vx = rng.uniform(-0.5, 0.5)
                vy = 0.0
            energy = rng.uniform(30.0, 80.0)
            self.add(Automaton(letter=letter, x=float(x), y=float(y), energy=energy, vx=vx, vy=vy))

    def __post_init__(self) -> None:
        if not self.terrain:
            self.terrain = flat_terrain(self.width, self.height)
        if not self.life_grid:
            self.life_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def ground_y_at(self, x: float) -> float:
        if self.width == 0:
            return float(self.height - 1)
        idx = int(round(x)) % self.width
        return float(self.terrain[idx])

    def add(self, a: Automaton) -> None:
        self.automata.append(a)

    def drop_rock_from(self, a: Automaton) -> bool:
        if not a.alive:
            return False
        c = a.letter.upper()
        if c not in ("X", "Y", "Z"):
            return False
        if a.energy <= ROCK_DROP_THRESHOLD:
            return False
        r = Rock(x=a.x, y=a.y - 1.0, vy=0.0, active=True)
        self.rocks.append(r)
        return True

    def step(self, dt: float) -> None:
        # Advance world clock
        self.world.tick(dt)

        # Sunlight for A/B during daylight
        if self.world.is_day:
            per_sec = self.world.sunlight_energy_gain(E_MEAL)
            for a in self.automata:
                if a.letter.upper() in ("A", "B"):
                    a.apply_sunlight(per_sec, dt)

        # Motion update
        for a in self.automata:
            gy = self.ground_y_at(a.x)
            a.tick_motion(dt, gy, self.width)
            a.tick_flashes()
            # Apply GoL bias after motion so cost applies next step
            if self.width > 0 and self.height > 0:
                ax = int(round(a.x)) % self.width
                ay = int(round(a.y))
                if 0 <= ay < self.height:
                    cnt = 0
                    for dr in (-1, 0, 1):
                        rr = ay + dr
                        if rr < 0 or rr >= self.height:
                            continue
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            cc = (ax + dc) % self.width
                            cnt += 1 if self.life_grid[rr][cc] else 0
                    if cnt >= 5:
                        a.vx += 0.2
                    elif cnt <= 2:
                        a.vx -= 0.2

        # Reproduction before predation to favor population growth
        self._resolve_reproduction()

        # Predation rules
        self._resolve_predation()

        # Auto rock dropping for X/Y/Z when enabled and energetic
        if self.auto_rocks:
            for a in self.automata:
                c = a.letter.upper()
                if c in ("X", "Y", "Z") and a.energy > ROCK_DROP_THRESHOLD:
                    # light stochasticity
                    import random

                    if random.random() < 0.1:
                        self.drop_rock_from(a)

        # Rocks update and impacts
        self._update_rocks(dt)

        # Step GoL field for the next update
        if self.width > 0 and self.height > 0:
            self.life_grid = step_life(self.life_grid)

        # Cull dead automata list to keep things tidy (we retain entries but mark dead)

    def _update_rocks(self, dt: float) -> None:
        for r in self.rocks:
            if not r.active:
                continue
            gy = self.ground_y_at(r.x)
            prev_y = r.y
            r.step(dt, gy)
            rx = int(round(r.x))
            # Check along path for same-column impacts
            for a in self.automata:
                if not a.alive:
                    continue
                ax, ay = int(round(a.x)), int(round(a.y))
                if ax == rx and min(prev_y, r.y) <= ay <= max(prev_y, r.y):
                    impact = r.impact_energy() * ROCK_MASS
                    a.energy = clamp(a.energy - impact, 0.0, ENERGY_MAX)
                    if a.energy <= 0.0:
                        self._bury(a)
                    r.active = False
                    break
            # Absorb into ground after potential impact
            if r.active and r.y >= gy:
                r.y = gy
                r.active = False
                self._bury_at_x(rx)
                # Align rock to new surface height after stacking
                r.y = self.ground_y_at(r.x)

    def _resolve_predation(self) -> None:
        # Build cell map for speed
        cell_map: dict[Tuple[int, int], List[int]] = {}
        for idx, a in enumerate(self.automata):
            if not a.alive:
                continue
            key = (int(round(a.x)), int(round(a.y)))
            cell_map.setdefault(key, []).append(idx)

        # Same-cell interactions: check both directions to allow cannibalism by starved lower letters
        for key, indices in cell_map.items():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                ai = self.automata[indices[i]]
                if not ai.alive:
                    continue
                for j in range(i + 1, len(indices)):
                    aj = self.automata[indices[j]]
                    if not aj.alive:
                        continue
                    if self._can_eat(ai, aj, same_cell=True, vertical_relation=0):
                        self._bury(aj)
                        ai.eat_gain(1.0)
                    elif self._can_eat(aj, ai, same_cell=True, vertical_relation=0):
                        self._bury(ai)
                        aj.eat_gain(1.0)

        # Flyers attack landers from above; landers can eat flyers above/left/right
        # Interactions are limited to visibility within two cells; at distance==2, a random
        # coin toss (50%) determines if vision occurs.
        for idx, attacker in enumerate(self.automata):
            if not attacker.alive:
                continue
            ax, ay = int(round(attacker.x)), int(round(attacker.y))
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    # limit to chebyshev distance <= 2
                    if max(abs(dx), abs(dy)) > 2:
                        continue
                    key = (ax + dx, ay + dy)
                    neighbor_indices = cell_map.get(key, [])
                    for j in neighbor_indices:
                        if j == idx:
                            continue
                        prey = self.automata[j]
                        if not prey.alive:
                            continue
                        # At distance 2, roll a coin toss for visibility
                        if max(abs(dx), abs(dy)) == 2 and random.random() >= 0.5:
                            continue
                        vertical = -1 if (ay > int(round(prey.y))) else (1 if (ay < int(round(prey.y))) else 0)
                        if self._can_eat(attacker, prey, same_cell=False, vertical_relation=vertical):
                            self._bury(prey)
                            attacker.eat_gain(1.0)

    def _can_eat(self, attacker: Automaton, prey: Automaton, *, same_cell: bool, vertical_relation: int) -> bool:
        if not attacker.alive or not prey.alive:
            return False
        att_is_fly = is_flyer_letter(attacker.letter)
        prey_is_fly = is_flyer_letter(prey.letter)

        if same_cell:
            # Land vs land: allowed by letter order or cannibalism rule
            if not att_is_fly and not prey_is_fly:
                if letter_order(attacker.letter) > letter_order(prey.letter):
                    return True
                # Cannibalism allowed only if same pair and starved
                same_species = pair_index(attacker.letter) == pair_index(prey.letter)
                return same_species and attacker.energy <= 10.0
            # Flyer vs anything in same cell not allowed per spec
            return False

        # Adjacent rules
        if att_is_fly and not prey_is_fly:
            # Flyers attack landers located below the flyer (attacking from above)
            return vertical_relation == 1
        if not att_is_fly and prey_is_fly:
            # Landers can eat adjacent flyers (above/left/right)
            return vertical_relation in (-1, 0)
        # Otherwise defer to letter-order rule with cannibal exception
        if letter_order(attacker.letter) <= letter_order(prey.letter):
            same_species = pair_index(attacker.letter) == pair_index(prey.letter)
            return same_species and attacker.energy <= 10.0
        return True

    def _resolve_reproduction(self) -> None:
        # Map cell occupancy
        cell_map: dict[Tuple[int, int], List[int]] = {}
        for idx, a in enumerate(self.automata):
            if not a.alive:
                continue
            key = (int(round(a.x)), int(round(a.y)))
            cell_map.setdefault(key, []).append(idx)

        newborns: List[Automaton] = []
        for key, indices in cell_map.items():
            if len(indices) < 1:
                continue
            # Z asexual reproduction
            for i in indices:
                a = self.automata[i]
                if a.letter.upper() == "Z" and is_flyer_letter("Z") and a.energy > 90.0 and a.can_fly():
                    # Spawn near parent (same x, above if free)
                    child = Automaton(letter="Z", x=a.x, y=max(0.0, a.y - 1.0), energy=50.0)
                    newborns.append(child)
                    a.repro_flash = max(a.repro_flash, 1)

            # Pair reproduction: look for opposite genders in same species pair
            # Minimal gating: both have enough energy to move
            for i in range(len(indices)):
                ai = self.automata[indices[i]]
                for j in range(i + 1, len(indices)):
                    aj = self.automata[indices[j]]
                    if pair_index(ai.letter) == pair_index(aj.letter):
                        # Opposite genders for A..Y; ignore Z here
                        if ai.letter.upper() != "Z" and aj.letter.upper() != "Z":
                            genders_different = ((ord(ai.letter.upper()) - ord("A")) % 2) != (
                                (ord(aj.letter.upper()) - ord("A")) % 2
                            )
                            if genders_different and ai.energy > 10.0 and aj.energy > 10.0:
                                # Spawn child of same species pair, choose lower letter visually
                                base_letter_ord = 2 * pair_index(ai.letter) + ord("A")
                                child_letter = chr(base_letter_ord)
                                newborns.append(
                                    Automaton(letter=child_letter, x=ai.x, y=ai.y, energy=50.0)
                                )
                                ai.repro_flash = max(ai.repro_flash, 1)
                                aj.repro_flash = max(aj.repro_flash, 1)

        # Add newborns
        self.automata.extend(newborns)

    # Surface absorption helpers
    def _bury(self, a: Automaton) -> None:
        a.kill()
        self._bury_at_x(int(round(a.x)))

    def _bury_at_x(self, x: int) -> None:
        if self.width <= 0:
            return
        idx = x % self.width
        self.terrain[idx] = max(0, self.terrain[idx] - 1)
