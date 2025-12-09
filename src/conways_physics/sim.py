"""World simulation orchestration.

This module implements the main simulation loop and systems for predation,
reproduction, rock updates, corpse handling, and terrain sizing. It coordinates
with Automaton physics and the renderer.
"""

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
    REPRO_ENERGY_THRESHOLD,
    FLYER_MIN_ALTITUDE_REPRO,
    CORPSE_DECAY_SECONDS,
    DAY_LENGTH_S,
    LANDER_JUMP_COOLDOWN_DAYS,
    LANDER_JUMP_ASCENT_MAX_CELLS,
    LANDER_JUMP_DISTANCE_CELLS,
    LANDER_JUMP_CHANCE,
    ROCK_DECAY_SECONDS,
)
from .species import is_flyer_letter, pair_index, relative_rank
from .terrain import flat_terrain, generate_surface
from .life import step_life
from .world import World
from .utils import clamp
import random


def same_cell(a: Automaton, b: Automaton) -> bool:
    """Return True if two automata occupy the same integer cell."""
    return int(round(a.x)) == int(round(b.x)) and int(round(a.y)) == int(round(b.y))


def adjacent_positions(ax: int, ay: int) -> List[Tuple[int, int]]:
    """Return the 4-neighborhood positions around (ax, ay)."""
    return [
        (ax, ay - 1),  # above
        (ax - 1, ay),  # left
        (ax + 1, ay),  # right
        (ax, ay + 1),  # below
    ]


@dataclass
class Simulation:
    """Top-level world state and stepping logic."""
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    world: World = field(default_factory=World)
    terrain: List[int] = field(default_factory=list)
    automata: List[Automaton] = field(default_factory=list)
    rocks: List[Rock] = field(default_factory=list)
    life_grid: List[List[int]] = field(default_factory=list)
    auto_rocks: bool = False
    corpses: set[tuple[int, int]] = field(default_factory=set)
    corpse_age: dict[tuple[int, int], float] = field(default_factory=dict)
    rocks_static: set[tuple[int, int]] = field(default_factory=set)
    rocks_age: dict[tuple[int, int], float] = field(default_factory=dict)

    # -----------------------------
    # Small internal helpers (no behavioral changes; reduce duplication)
    # -----------------------------
    def _age_and_collect(
        self,
        ages: dict[tuple[int, int], float],
        dt: float,
        threshold: float,
    ) -> list[tuple[int, int]]:
        """Increment ages by dt and return positions whose age crosses ``threshold``.

        This utility reduces duplication between corpse and rock decay logic.
        """
        if not ages:
            return []
        decayed: list[tuple[int, int]] = []
        delta = max(0.0, dt)
        for pos, age in list(ages.items()):
            age += delta
            ages[pos] = age
            if age >= threshold:
                decayed.append(pos)
        return decayed

    def _spawn_flyer_y(self, rng: random.Random, ground_y: int) -> int:
        """Return a spawn y for flyers within top third and >= min altitude above terrain when possible."""
        min_alt = int(round(FLYER_MIN_ALTITUDE_REPRO))
        y_max = max(0, min(self.height // 3, int(ground_y) - min_alt))
        return rng.randint(0, y_max) if y_max > 0 else 0
    spawned_total: int = 0
    died_total: int = 0
    eaten_total: int = 0
    rock_deaths_total: int = 0
    starved_total: int = 0
    # Movement tracking
    moves_total: int = 0
    moves_today: int = 0
    day_moves: List[int] = field(default_factory=list)
    _current_day_index: int = 0

    def configure_surface_for_view(
        self,
        width: int,
        height: int,
        *,
        sea_level_offset: int = 4,
        amplitude: int = 3,
        seed: int | None = None,
    ) -> None:
        """Resize world and regenerate surface to match a viewport.

        The resulting surface spans the full width with a baseline 4 rows above the bottom
        by default, varying ±3 rows.
        """
        old_w, old_h = self.width, self.height
        old_terrain = self.terrain[:] if self.terrain else []
        self.width = max(0, int(width))
        self.height = max(1, int(height))
        self.terrain = generate_surface(
            self.width,
            self.height,
            sea_level_offset=sea_level_offset,
            amplitude=amplitude,
            seed=seed,
        )
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
                    # Preserve height above surface
                    old_ix = int(round(a.x)) % max(1, old_w)
                    old_gy = int(round(old_terrain[old_ix])) if old_terrain else (old_h - 1)
                    above = max(1, old_gy - int(round(a.y)))
                    new_y = max(0, new_gy - above)
                else:
                    new_y = max(0, new_gy - 1)
                a.x = max(0.0, min(float(self.width - 1), new_x))
                a.y = float(max(0, min(self.height - 1, new_y)))

    def seed_population(self, count: int, *, seed: int | None = None) -> None:
        """Seed with randomly distributed automata across species/genders.

        - For paired species (A..Y), pick a species pair uniformly and then a gender (first/second letter) at random.
        - Include Z occasionally; Z has no gender and is a flyer.
        - Landers spawn on terrain at their column; flyers spawn in the top third
          of the screen at least FLYER_MIN_ALTITUDE_REPRO rows above the terrain
          when possible.
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
                # Spawn flyers in the top third with minimum altitude when possible.
                y = self._spawn_flyer_y(rng, gy)
                vx = rng.uniform(-0.5, 0.5)
                vy = 0.0
            else:
                y = max(0, gy - 1)
                vx = rng.uniform(-0.5, 0.5)
                vy = 0.0
            energy = 100.0
            self.add(Automaton(letter=letter, x=float(x), y=float(y), energy=energy, vx=vx, vy=vy))

    def seed_population_balanced(self, total: int = 100, *, seed: int | None = None) -> None:
        """Seed at least `total` automata with ~10% flyers and the rest landers.

        Flyers are chosen from N..Z (including Z); landers from A..M.
        Landers spawn at one cell above the surface; flyers spawn in the top third
        of the screen and at least FLYER_MIN_ALTITUDE_REPRO rows above terrain when possible.
        """
        if self.width <= 0:
            return
        rng = random.Random(seed)
        total = max(0, int(total))
        flyers_target = int(total * 0.1)
        landers_target = total - flyers_target

        flyer_letters = [
            "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
        ]
        land_letters = [chr(ord('A') + i) for i in range(13)]  # A..M

        for _ in range(landers_target):
            letter = rng.choice(land_letters)
            x = rng.randrange(self.width)
            gy = int(round(self.terrain[x])) if self.terrain else self.height - 1
            y = max(0, gy - 1)
            vx = rng.uniform(-0.5, 0.5)
            vy = 0.0
            energy = 100.0
            self.add(Automaton(letter=letter, x=float(x), y=float(y), energy=energy, vx=vx, vy=vy))

        for _ in range(flyers_target):
            letter = rng.choice(flyer_letters)
            x = rng.randrange(self.width)
            gy = int(round(self.terrain[x])) if self.terrain else self.height - 1
            y = self._spawn_flyer_y(rng, gy)
            vx = rng.uniform(-0.5, 0.5)
            vy = 0.0
            energy = 100.0
            self.add(Automaton(letter=letter, x=float(x), y=float(y), energy=energy, vx=vx, vy=vy))

    def __post_init__(self) -> None:
        if not self.terrain:
            self.terrain = flat_terrain(self.width, self.height)
        if not self.life_grid:
            self.life_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def ground_y_at(self, x: float) -> float:
        """Return the terrain surface row at column ``x`` (with wrapping)."""
        if self.width == 0:
            return float(self.height - 1)
        idx = int(round(x)) % self.width
        return float(self.terrain[idx])

    def add(self, a: Automaton) -> None:
        """Add an automaton to the world."""
        self.automata.append(a)
        self.spawned_total += 1

    def drop_rock_from(self, a: Automaton) -> bool:
        """Attempt to spawn a rock from automaton ``a``.

        Returns True on success.
        """
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
        """Advance the entire simulation by ``dt`` seconds."""
        # Advance world clock
        self.world.tick(dt)
        # Reset per-step action flags
        for a in self.automata:
            a.ate_step = False
            a.repro_step = False

        # Update ages and A/B reproduction timers. Transformations applied later
        # in the step to allow A/B auto-spawn before evolving.
        transform_period = 30.0 * DAY_LENGTH_S if DAY_LENGTH_S > 0 else float('inf')
        if transform_period < float('inf'):
            for a in self.automata:
                if not a.alive:
                    continue
                a.age_s += max(0.0, dt)
                if a.letter.upper() in ("A", "B"):
                    a.since_repro_s += max(0.0, dt)

        # Sunlight for A/B during daylight
        if self.world.is_day:
            per_sec = self.world.sunlight_energy_gain(E_MEAL)
            for a in self.automata:
                if a.letter.upper() in ("A", "B"):
                    a.apply_sunlight(per_sec, dt)

        # Precompute blocking cells from rocks and corpses (as '#')
        rock_cells = set()
        for r in self.rocks:
            if r.active and self.width > 0:
                rx = int(round(r.x)) % self.width
                ry = int(round(r.y))
                rock_cells.add((ry, rx))

        # Motion update with simple terrain/# collision: block moves into terrain or '#'.
        # C/D landers can "dig" horizontally by eating a surface cell to create tunnels.
        moved_ids: set[int] = set()
        for a in self.automata:
            # Decide lander horizontal intent (pursue prey / avoid predators)
            if not is_flyer_letter(a.letter) and a.alive and a.energy > 0:
                dir_h = self._lander_choose_direction(a)
                ix0 = int(round(a.x)) % max(1, self.width)
                # Pre-jump attempt if the immediate step is blocked by terrain
                if dir_h != 0 and not self._lander_can_step(ix0, dir_h):
                    cooldown_s = (
                        LANDER_JUMP_COOLDOWN_DAYS * DAY_LENGTH_S if DAY_LENGTH_S > 0 else float('inf')
                    )
                    if (
                        (self.world.t_abs - getattr(a, 'last_jump_time_s', -1e18)) >= cooldown_s
                        and random.random() < LANDER_JUMP_CHANCE
                    ):
                        tgt_ix = (ix0 + dir_h * LANDER_JUMP_DISTANCE_CELLS) % max(1, self.width)
                        cur_h = (
                            int(round(self.terrain[ix0]))
                            if self.terrain
                            else int(round(self.ground_y_at(a.x)))
                        )
                        tgt_h = (
                            int(round(self.terrain[tgt_ix]))
                            if self.terrain
                            else int(round(self.ground_y_at(tgt_ix)))
                        )
                        ascend = cur_h - tgt_h
                        landing_cell = (max(0, min(self.height - 1, tgt_h - 1)), tgt_ix)
                        if (
                            ascend <= LANDER_JUMP_ASCENT_MAX_CELLS
                            and landing_cell not in rock_cells
                            and landing_cell not in self.corpses
                        ):
                            a.x = float(tgt_ix)
                            a.y = float(landing_cell[0])
                            a.vx = 0.0
                            a.vy = 0.0
                            a.last_jump_time_s = self.world.t_abs
                            a.energy = clamp(a.energy - 2.0, 0.0, ENERGY_MAX)
                # Choose intent; allow C/D to attempt digging on blocked primary later.
                a.vx = float(dir_h) * 2.0
            elif is_flyer_letter(a.letter) and a.alive and a.energy > 10.0:
                # Flyers choose a random cardinal direction with bias:
                # - Toward nearby prey (lower relative rank)
                # - Away from nearby predators (higher relative rank)
                # Vision limited to Chebyshev distance <= 2; at distance 2 use 50% visibility.
                ax = int(round(a.x))
                ay = int(round(a.y))
                prey_dirs: list[tuple[int, int]] = []
                threat_dirs: list[tuple[int, int]] = []
                mate_dirs: list[tuple[int, int]] = []
                me_r = relative_rank(a.letter)
                for dx in (-2, -1, 0, 1, 2):
                    for dy in (-2, -1, 0, 1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        if max(abs(dx), abs(dy)) > 2:
                            continue
                        # 50% visibility at exact Chebyshev distance 2
                        if max(abs(dx), abs(dy)) == 2 and random.random() < 0.5:
                            continue
                        nx, ny = ax + dx, ay + dy
                        for b in self.automata:
                            if not b.alive:
                                continue
                            if int(round(b.x)) == nx and int(round(b.y)) == ny:
                                other_r = relative_rank(b.letter)
                                if other_r < me_r:
                                    # Include severity proportional to rank gap
                                    for _ in range(max(1, me_r - other_r)):
                                        prey_dirs.append((dx, dy))
                                elif other_r > me_r:
                                    for _ in range(max(1, other_r - me_r)):
                                        threat_dirs.append((dx, dy))
                                if self._is_mate(a, b):
                                    mate_dirs.append((dx, dy))
                had_signal = bool(prey_dirs or threat_dirs or mate_dirs)
                # Base random weights for 4 directions: left, right, up, down.
                # Bias horizontal (left/right) 4x over vertical (up/down), and
                # bias upward 2x over downward.
                dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                weights = [4.0, 4.0, 2.0, 1.0]
                # Bias toward prey
                for dx, dy in prey_dirs:
                    if dx < 0:
                        weights[0] += 4.0
                    if dx > 0:
                        weights[1] += 4.0
                    if dy < 0:
                        weights[2] += 2.0
                    if dy > 0:
                        weights[3] += 1.0
                # Bias away from predators
                for dx, dy in threat_dirs:
                    if dx < 0:
                        weights[1] += 4.0  # predator left -> go right
                    if dx > 0:
                        weights[0] += 4.0  # predator right -> go left
                    if dy < 0:
                        weights[3] += 1.0  # predator above -> go down
                    if dy > 0:
                        weights[2] += 2.0  # predator below -> go up (upward 2x bias)
                # Bias toward mates
                for dx, dy in mate_dirs:
                    if dx < 0:
                        weights[0] += 8.0  # horizontal mate bias 4x vertical
                    if dx > 0:
                        weights[1] += 8.0
                    if dy < 0:
                        weights[2] += 4.0  # up is 2x down
                    if dy > 0:
                        weights[3] += 2.0
                # Choose direction
                if had_signal:
                    try:
                        import math  # noqa: F401  # keep deterministic import set
                    except Exception:
                        pass
                    # Normalize to avoid zero-sum pathologies
                    if sum(weights) <= 0:
                        weights = [1.0, 1.0, 1.0, 1.0]
                    # Flyers X/Y/Z: add a 'drop rock' action with weight 3x of 'down'
                    can_drop = (
                        a.letter.upper() in ("X", "Y", "Z") and a.energy > ROCK_DROP_THRESHOLD
                    )
                    down_w = weights[3]
                    drop_w = (3.0 * down_w) if can_drop else 0.0
                    if drop_w > 0.0:
                        # Choice space: left,right,up,down,drop
                        choice = random.choices(range(5), weights=weights + [drop_w], k=1)[0]
                        if choice == 4:
                            # Attempt drop, then choose movement among directions
                            self.drop_rock_from(a)
                            choice = random.choices(range(4), weights=weights, k=1)[0]
                        dx, dy = dirs[choice]
                    else:
                        choice = random.choices(range(4), weights=weights, k=1)[0]
                        dx, dy = dirs[choice]
                else:
                    # No visible mate/prey/predator: wander horizontally to explore
                    dx, dy = (-1, 0) if random.random() < 0.5 else (1, 0)
                # Apply a modest horizontal speed and a small vertical impulse
                a.vx = float(dx) * 1.5
                a.vy += float(dy) * 2.0

            prev_x, prev_y = a.x, a.y
            prev_ix, prev_iy = int(round(prev_x)), int(round(prev_y))
            gy = self.ground_y_at(a.x)
            a.tick_motion(dt, gy, self.width)
            # Block entry into terrain cells (surface and below)
            new_gy = self.ground_y_at(a.x)
            xi = int(round(a.x)) % max(1, self.width)
            yi = int(round(a.y))
            blocked_by_terrain = yi >= int(round(new_gy))
            blocked_by_entity = (
                (yi, xi) in self.corpses
                or (yi, xi) in rock_cells
                or (yi, xi) in self.rocks_static
            )

            # Allow C/D to dig horizontally into terrain (but not through rocks/corpses)
            if (
                blocked_by_terrain
                and not blocked_by_entity
                and a.alive
                and a.letter.upper() in ("C", "D")
            ):
                prev_ix = int(round(prev_x)) % max(1, self.width)
                # Consider it a horizontal move if the target column changed
                if xi != prev_ix:
                    # Eat the blocking terrain cell by lowering the fill above current row.
                    # This is achieved by increasing the surface row at this column
                    # to at least one below the automaton (yi + 1), creating an empty cell at yi.
                    cur = int(round(self.terrain[xi])) if self.terrain else int(round(new_gy))
                    new_surface = max(cur, yi + 1)
                    self.terrain[xi] = min(self.height - 1, new_surface)
                    # Recompute blocking against updated surface
                    new_gy = self.ground_y_at(a.x)
                    blocked_by_terrain = yi >= int(round(new_gy))

            blocked = blocked_by_terrain or blocked_by_entity

            # Special lander jump: if blocked by terrain, attempt a one-move jump
            # up to LANDER_JUMP_ASCENT_MAX_CELLS higher, over LANDER_JUMP_DISTANCE_CELLS columns
            # in the attempted horizontal direction, no more than once every
            # LANDER_JUMP_COOLDOWN_DAYS.
            if (
                blocked
                and blocked_by_terrain
                and not is_flyer_letter(a.letter)
                and a.alive
                and self.width > 0
            ):
                # Determine intended horizontal direction from movement this step
                prev_ix = int(round(prev_x)) % max(1, self.width)
                # Prefer sign from velocity if column didn't change
                sign = 0
                if int(round(a.vx)) != 0:
                    sign = 1 if a.vx > 0 else -1
                if sign == 0 and (xi != prev_ix):
                    # Fallback based on column delta
                    if xi == (prev_ix + 1) % self.width:
                        sign = 1
                    elif xi == (prev_ix - 1) % self.width:
                        sign = -1
                if sign != 0:
                    # Cooldown check
                    cooldown_s = (
                        LANDER_JUMP_COOLDOWN_DAYS * DAY_LENGTH_S if DAY_LENGTH_S > 0 else float('inf')
                    )
                    if (
                        (self.world.t_abs - getattr(a, 'last_jump_time_s', -1e18)) >= cooldown_s
                        and random.random() < LANDER_JUMP_CHANCE
                    ):
                        tgt_ix = (prev_ix + sign * LANDER_JUMP_DISTANCE_CELLS) % self.width
                        cur_h = int(round(self.terrain[prev_ix]))
                        tgt_h = int(round(self.terrain[tgt_ix]))
                        ascend = cur_h - tgt_h  # positive means target is higher ground
                        # Check ascent limit and ensure landing cell not blocked by rock/corpse
                        landing_cell = (max(0, min(self.height - 1, tgt_h - 1)), tgt_ix)
                        if (
                            ascend <= LANDER_JUMP_ASCENT_MAX_CELLS
                            and landing_cell not in rock_cells
                            and landing_cell not in self.corpses
                        ):
                            # Perform jump: place on air boundary of target column
                            a.x = float(tgt_ix)
                            a.y = float(landing_cell[0])
                            a.vx = 0.0
                            a.vy = 0.0
                            a.last_jump_time_s = self.world.t_abs
                            # Jump costs two energy
                            a.energy = clamp(a.energy - 2.0, 0.0, ENERGY_MAX)
                            blocked = False

            if blocked:
                # Revert to previous position and stop motion
                a.x, a.y = prev_x, max(0.0, min(prev_y, self.ground_y_at(prev_x) - 1))
                a.vx = 0.0
                a.vy = 0.0
            # flashes removed
            # Track movement by cell change after resolving collisions
            if int(round(a.x)) != prev_ix or int(round(a.y)) != prev_iy:
                moved_ids.add(id(a))
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

        # A/B species can consume corpses ('#') at their cell
        self._consume_corpses()

        # Reproduction before predation to favor population growth
        self._resolve_reproduction()

        # A/B auto-spawn C/D if no reproduction for 30 days and adjacent free cell exists
        self._ab_autospawn_cd()

        # Predation rules
        self._resolve_predation()

        # Auto rock dropping for X/Y/Z when enabled and energetic
        if self.auto_rocks:
            for a in self.automata:
                c = a.letter.upper()
                if c in ("X", "Y", "Z") and a.energy > ROCK_DROP_THRESHOLD:
                    # light stochasticity (module-level RNG)
                    if random.random() < 0.1:
                        self.drop_rock_from(a)

        # Rocks update and impacts
        self._update_rocks(dt)

        # Settle corpses into terrain over time
        self._decay_corpses(dt)
        self._decay_rocks(dt)

        # Apply species transformations (every 30 days of lifetime), after
        # reproduction and A/B auto-spawn have been processed in this step.
        if transform_period < float('inf'):
            for a in self.automata:
                if not a.alive:
                    continue
                if not is_flyer_letter(a.letter):
                    pending = int(a.age_s // transform_period) - int(getattr(a, 'transforms_done', 0))
                    while pending > 0 and (not is_flyer_letter(a.letter)):
                        c = a.letter.upper()
                        if "A" <= c <= "M":
                            new_ord = ord(c) + 2
                            a.letter = chr(new_ord)
                            a.transforms_done = int(getattr(a, 'transforms_done', 0)) + 1
                        else:
                            break
                        pending -= 1

        # Step GoL field for the next update
        if self.width > 0 and self.height > 0:
            self.life_grid = step_life(self.life_grid)

        # Idle energy drain: if an automaton neither moved, ate, nor reproduced this step,
        # reduce its energy slightly to discourage stagnation.
        for a in self.automata:
            if not a.alive:
                continue
            if (id(a) not in moved_ids) and (not a.ate_step) and (not a.repro_step):
                a.energy = clamp(a.energy - (0.1 * max(0.0, dt)), 0.0, ENERGY_MAX)
        # Movement accounting: count per-step unique movers
        step_moves = len(moved_ids)
        if step_moves:
            self.moves_total += step_moves
            self.moves_today += step_moves

        # Roll day bucket if we crossed into a new day
        if DAY_LENGTH_S > 0:
            day_idx = int(self.world.t_abs // DAY_LENGTH_S)
            # Initialize current day index at first call
            if self._current_day_index == 0 and self.world.t_abs == 0.0:
                self._current_day_index = 0
            if day_idx > self._current_day_index:
                # Append completed days; handle potential multi-day jumps
                self.day_moves.append(self.moves_today)
                # Trim to last 14 days
                if len(self.day_moves) > 14:
                    self.day_moves = self.day_moves[-14:]
                # Reset today's counter for the new day span
                self.moves_today = 0
                self._current_day_index = day_idx
        # Starvation deaths
        for a in self.automata:
            if a.alive and a.energy <= 0.0:
                self._bury(a, cause="starved")

    # Movement stats helpers
    def movement_stats(self) -> tuple[int, float, float, float]:
        """Return (total_moves, ma3, ma7, ma14) based on daily movement counts.

        Moving averages use available recent days (including current partial day)
        and divide by the number of days included, up to the window size.
        """
        series = self.day_moves[:] + [self.moves_today]

        def avg(n: int) -> float:
            if not series:
                return 0.0
            vals = series[-n:]
            if not vals:
                return 0.0
            return sum(vals) / float(len(vals))
        return self.moves_total, avg(3), avg(7), avg(14)

    def _consume_corpses(self) -> None:
        if not self.corpses:
            return
        to_remove = []
        for a in self.automata:
            if not a.alive:
                continue
            if a.letter.upper() not in ("A", "B"):
                continue
            xi = int(round(a.x)) % max(1, self.width)
            yi = int(round(a.y))
            if (yi, xi) in self.corpses:
                to_remove.append((yi, xi))
                a.eat_gain(1.0)
        for pos in to_remove:
            self.corpses.discard(pos)
            self.corpse_age.pop(pos, None)

    def _update_rocks(self, dt: float) -> None:
        """Integrate and resolve rock impacts."""
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
                        self._bury(a, cause="rock")
                    r.active = False
                    break
            # Absorb into ground after potential impact
            if r.active and r.y >= gy:
                r.y = gy
                r.active = False
                # Place a static rock marker ('#') at air boundary to decay later
                if self.width > 0:
                    cx = rx % self.width
                    cy = int(round(gy)) - 1
                    cy = max(0, min(self.height - 1, cy))
                    self.rocks_static.add((cy, cx))
                    self.rocks_age[(cy, cx)] = 0.0

    def _resolve_predation(self) -> None:
        """Apply predation interactions based on adjacency and vision rules."""
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
                        if not self._ab_retaliation(ai, aj):
                            self._bury(aj, cause="eaten")
                            ai.eat_gain(1.0)
                    elif self._can_eat(aj, ai, same_cell=True, vertical_relation=0):
                        if not self._ab_retaliation(aj, ai):
                            self._bury(ai, cause="eaten")
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
                            if not self._ab_retaliation(attacker, prey):
                                self._bury(prey, cause="eaten")
                                attacker.eat_gain(1.0)

    def _can_eat(self, attacker: Automaton, prey: Automaton, *, same_cell: bool, vertical_relation: int) -> bool:
        """Return True if ``attacker`` can eat ``prey`` using relative rank rules.

        Eating is based purely on relative letter value aligned across landers
        (A..M) and flyers (N..Z): A==N, B==O, ..., M==Z. Higher rank eats lower.
        Equal rank resolves by 50/50 coin toss. Directional/flight constraints
        do not affect eligibility here (visibility handled by caller).
        """
        if not attacker.alive or not prey.alive:
            return False
        ra = relative_rank(attacker.letter)
        rp = relative_rank(prey.letter)
        if ra > rp:
            return True
        if ra == rp:
            return random.random() < 0.5
        return False

    def _ab_retaliation(self, attacker: Automaton, prey: Automaton) -> bool:
        """Apply A/B prey retaliation when predator energy ≤ 5.

        If the prey is 'A' or 'B' and the attacker energy is ≤ 5, roll a 50/50
        coin toss. On success, the prey eats the attacker instead. Returns True
        if the retaliation occurred (attacker was buried), otherwise False.
        """
        if prey.letter.upper() in ("A", "B") and attacker.energy <= 5.0 and attacker.alive and prey.alive:
            if random.random() < 0.5:
                self._bury(attacker, cause="eaten")
                prey.eat_gain(1.0)
                return True
        return False

    def _resolve_reproduction(self) -> None:
        """Spawn newborns for valid pairings and Z asexual reproduction."""
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
                    # Flyers must be at altitude to reproduce
                    if (self.ground_y_at(a.x) - a.y) < FLYER_MIN_ALTITUDE_REPRO:
                        continue
                    # Spawn near parent (same x, above if free)
                    child = Automaton(letter="Z", x=a.x, y=max(0.0, a.y - 1.0), energy=50.0)
                    newborns.append(child)
                    a.repro_step = True

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
                            # Both must desire reproduction
                            if not (ai.energy >= REPRO_ENERGY_THRESHOLD and aj.energy >= REPRO_ENERGY_THRESHOLD):
                                continue
                            # Flyers can only reproduce at altitude
                            ai_alt_ok = (not is_flyer_letter(ai.letter)) or (
                                (self.ground_y_at(ai.x) - ai.y) >= FLYER_MIN_ALTITUDE_REPRO
                            )
                            aj_alt_ok = (not is_flyer_letter(aj.letter)) or (
                                (self.ground_y_at(aj.x) - aj.y) >= FLYER_MIN_ALTITUDE_REPRO
                            )
                            if not (ai_alt_ok and aj_alt_ok):
                                continue
                            if genders_different:
                                # Spawn child of same species pair, choose lexicographically lower parent letter
                                child_letter = min(ai.letter.upper(), aj.letter.upper())
                                newborns.append(
                                    Automaton(letter=child_letter, x=ai.x, y=ai.y, energy=50.0)
                                )
                                # Reset A/B since-reproduction timers on successful reproduction
                                if ai.letter.upper() in ("A", "B"):
                                    ai.since_repro_s = 0.0
                                if aj.letter.upper() in ("A", "B"):
                                    aj.since_repro_s = 0.0
                                ai.repro_step = True
                                aj.repro_step = True

        # Add newborns via add() to track spawn count
        for nb in newborns:
            self.add(nb)

    # Surface absorption helpers
    def _bury(self, a: Automaton, *, cause: str | None = None) -> None:
        """Mark an automaton as dead and record a corpse on the surface.

        Parameters:
            cause: Optional cause string; increments cause-specific counters for
                "eaten", "rock", or "starved".
        """
        if a.alive:
            self.died_total += 1
            if cause == "eaten":
                self.eaten_total += 1
            elif cause == "rock":
                self.rock_deaths_total += 1
            elif cause == "starved":
                self.starved_total += 1
        a.kill()
        if self.width > 0:
            xi = int(round(a.x)) % self.width
            yi = int(round(self.ground_y_at(a.x))) - 1
            yi = max(0, min(self.height - 1, yi))
            self.corpses.add((yi, xi))
            self.corpse_age[(yi, xi)] = 0.0

    def _bury_at_x(self, x: int) -> None:
        """Increase the terrain stack at column ``x`` (used by rock impacts)."""
        if self.width <= 0:
            return
        idx = x % self.width
        self.terrain[idx] = max(0, self.terrain[idx] - 1)

    def _ab_autospawn_cd(self) -> None:
        """A/B auto-spawn C/D after 30 days without reproduction.

        For each alive A/B whose `since_repro_s` ≥ 30 days, attempt to spawn a
        C/D child in the nearest available adjacent non-terrain cell. If all
        adjacent cells are occupied or blocked (terrain/rock/corpse), do nothing.
        """
        threshold = 30.0 * DAY_LENGTH_S if DAY_LENGTH_S > 0 else float('inf')
        if threshold == float('inf'):
            return
        # Build occupied set of alive automata positions
        occ = set()
        for a in self.automata:
            if a.alive:
                occ.add((int(round(a.y)), int(round(a.x)) % max(1, self.width)))
        for a in self.automata:
            if not a.alive:
                continue
            if a.letter.upper() not in ("A", "B"):
                continue
            if getattr(a, 'since_repro_s', 0.0) < threshold:
                continue
            ax = int(round(a.x)) % max(1, self.width)
            ay = int(round(a.y))
            # Candidate adjacent cells in an order favoring likely free air first
            candidates = [
                (ay - 1, ax),  # up
                (ay, (ax - 1) % self.width),  # left
                (ay, (ax + 1) % self.width),  # right
                (ay + 1, ax),  # down
            ]
            for cy, cx in candidates:
                if cy < 0 or cy >= self.height:
                    continue
                # Block if terrain at or below surface
                if cy >= int(round(self.terrain[cx])):
                    continue
                # Block if rock or corpse present
                if (cy, cx) in self.corpses:
                    continue
                # Occupied by another automaton
                if (cy, cx) in occ:
                    continue
                # Place child here
                child_letter = random.choice(['C', 'D'])
                self.add(Automaton(letter=child_letter, x=float(cx), y=float(cy), energy=50.0))
                # Reset timer
                a.since_repro_s = 0.0
                # Mark occupied to avoid double placement in this pass
                occ.add((cy, cx))
                break
            # If not placed, leave timer as-is; next step will retry

    def _decay_corpses(self, dt: float) -> None:
        """Advance corpse ages and settle into terrain after the decay time.

        When a corpse decays, a block is added to the terrain column, and the
        corpse marker is removed. Decay favors eating first (consumption runs
        before this method in the step order).
        """
        decayed = self._age_and_collect(self.corpse_age, dt, CORPSE_DECAY_SECONDS)
        for (yi, xi) in decayed:
            self._bury_at_x(xi)
            self.corpses.discard((yi, xi))
            self.corpse_age.pop((yi, xi), None)

    def _decay_rocks(self, dt: float) -> None:
        """Advance rock ages and settle into terrain after rock decay time.

        When a landed rock decays, a block is added to the terrain column and
        the rock marker is removed.
        """
        decayed = self._age_and_collect(self.rocks_age, dt, ROCK_DECAY_SECONDS)
        for (ry, cx) in decayed:
            self._bury_at_x(cx)
            self.rocks_static.discard((ry, cx))
            self.rocks_age.pop((ry, cx), None)

    # Land movement helpers
    def _lander_can_step(self, ix: int, dir_h: int) -> bool:
        """Return True if a lander at column ``ix`` may step to ``ix+dir_h``.

        Allows ascending at most 1 row. Descending any amount is allowed.
        """
        if self.width <= 0:
            return False
        nx = (ix + dir_h) % self.width
        cur_h = int(round(self.terrain[ix]))
        nxt_h = int(round(self.terrain[nx]))
        # Compare surface heights; ascending by <=1 allowed, descending any amount allowed
        # Ascending means moving to a smaller y (higher ground). Block if more than 1.
        if nxt_h < cur_h - 1:
            return False
        return True

    def _lander_choose_direction(self, a: Automaton) -> int:
        """Choose lander horizontal direction.

        - Pursue lower-rank neighbors (prey) within Chebyshev distance 2.
        - Avoid higher-rank neighbors (predators) within same range,
          with stronger bias as the rank gap increases.
        - If energy > 10, prefer moving toward a mating partner (same pair,
          opposite gender) within range; avoidance has priority over mating,
          which has priority over prey pursuit.
        Returns -1, 0, or +1.
        """
        ax, ay = int(round(a.x)), int(round(a.y))
        me = relative_rank(a.letter)
        avoid_dir = 0
        pursue_dir = 0
        mate_dir = 0
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx == 0 and dy == 0:
                    continue
                if max(abs(dx), abs(dy)) > 2:
                    continue
                nx, ny = ax + dx, ay + dy
                # Find automata at this neighbor cell
                for b in self.automata:
                    if not b.alive:
                        continue
                    if int(round(b.x)) == nx and int(round(b.y)) == ny:
                        other = relative_rank(b.letter)
                        # Mating partner detection
                        if a.energy > 10.0 and self._is_mate(a, b) and mate_dir == 0:
                            mate_dir = -1 if dx < 0 else (1 if dx > 0 else mate_dir)
                        if other > me:
                            # Predator: move away; prefer stronger opposite bias for bigger gaps
                            avoid_dir = -1 if dx < 0 else (1 if dx > 0 else avoid_dir)
                        elif other < me and pursue_dir == 0:
                            # Prey: remember direction toward it if not already set
                            pursue_dir = -1 if dx < 0 else (1 if dx > 0 else pursue_dir)
        # If energized and mate found, prefer mating bias over avoidance/pursuit
        if a.energy > 10.0 and mate_dir != 0:
            return mate_dir
        if avoid_dir != 0:
            return -avoid_dir
        if pursue_dir != 0:
            return pursue_dir
        # Nothing visible: explore randomly
        return -1 if random.random() < 0.5 else 1

    def _is_mate(self, a: Automaton, b: Automaton) -> bool:
        """Return True if ``a`` and ``b`` are mating partners (A..Y).

        Same species pair index and opposite genders; excludes Z.
        """
        if b.letter.upper() == "Z" or a.letter.upper() == "Z":
            return False
        return pair_index(a.letter) == pair_index(b.letter) and (
            ((ord(a.letter.upper()) - ord("A")) % 2) != ((ord(b.letter.upper()) - ord("A")) % 2)
        )
