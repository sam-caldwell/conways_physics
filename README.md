# Conways Physics — Terminal World Simulation (Textual/Rich)

Conways Physics is a zero‑player, terminal‑based world simulation. Land species (A–M) and flying species (N–Z)
move, eat, reproduce, and evolve on a scrolling ASCII terrain. The UI is built with Textual/Rich and renders a
two‑panel layout: the world view and a status footer.


## Key Features

- Two‑panel TUI with a white‑bordered world panel and a status footer.
- Terrain spans the full width; baseline sits 4 rows above the bottom with ±3 variation. Terrain and below use
  ASCII 219 (full block) in grey; corpses render as grey `#` and block movement.
- Automata letters colored by energy: 16‑color palette mapping energy 1..100 → indices 0..15 (≤1 uses the lowest color).
- Day/night cycle: 30s days, first 15s daylight. A/B gain sunlight energy during daylight.
- Corpses decay into terrain after 5 in‑game days (surface rises by one, corpse marker removed). A/B can eat corpses.
- Rocks: X/Y/Z can drop rocks when energetic; rocks fall and can kill on impact. Rocks block movement.
- Press `r` any time to recycle: new terrain and a fresh population. Recycles and auto-respawns start paused.


## Species, Spawning, and Energy

- Landers: A–M. Flyers: N–Z.
- Balanced seeding: 10% flyers (including Z), 90% landers. All start at energy 100.
- Weight: Each automaton is assigned a random body weight in the range 20–100 at creation (including newborns).
  - Physics impact: Weight subtly influences motion — heavier flyers experience slightly stronger effective gravity; heavier landers experience slightly more ground friction.
- Spawn locations:
  - Landers spawn on the air boundary (surface−1).
  - Flyers spawn in the top third, and at least 20 rows above local terrain when possible.


## Motion, Bias, Tunneling, and Jumps

- Flyers
  - Move randomly in cardinal directions, biased toward nearby lower‑rank prey and away from higher‑rank predators
    (vision within Chebyshev distance ≤2; at distance 2 visibility is 50%).
  - Actively climb until altitude ≥20; bounce at the air boundary; can’t translate along ground.
- Landers
  - Choose direction using priorities: mate (if energy >10) > avoid predators > pursue prey. May climb up to 1 row;
    larger steps block.
  - C/D tunneling: when colliding laterally with terrain (not rocks/corpses), C/D eat the surface cell to carve
    tunnels.
  - Jump: when blocked by terrain, may randomly perform a single jump up 3 rows and over 2 columns in the intended
    direction. Cooldown: once per 7 in‑game days. Jump costs 2 energy.
- GoL influence: a simple neighborhood count biases horizontal drift (left/right) for emergent flows.
- Stagnation nudge: if an automaton remains in the same cell, the chance of a small “nudge” to its velocity rises over time to discourage getting stuck. No nudges occur for the first ~5s; probability ramps toward ~100% by ~60s.


## Physics Implementation

The simulation uses simple, stable Newtonian-style dynamics designed for readability and deterministic tests.

- Coordinates: Automata have continuous `x/y`; grid cells are integer-rounded for interactions. `y` increases downward.
- Air/Ground boundary: The terrain surface at column `x` defines the ground. The “air boundary” is `surface−1`.
- Motion gating: Movement requires energy above thresholds (`ENERGY_MIN_MOVE`, `ENERGY_MIN_FLY` for flyers).

- Flyers (N–Z):
  - Kick-off: When on the air boundary and not descending, set a small upward `vy` to lift off.
  - Vertical dynamics: `vy += (GRAVITY * weight) - climb`, then apply `AIR_DRAG`. Weight scales with energy. Below preferred altitude, a climb bias (`FLYER_CLIMB_ACCEL`) opposes gravity until altitude ≥ `FLYER_MIN_ALTITUDE_REPRO`.
  - Bounce: Colliding with the air boundary inverts `vy` with `RESTITUTION`.
  - Cost: Flight drains energy when actually moving.
  - Ground behavior: If unable to fly (low energy), flyers rest on the air boundary and cannot translate laterally.
  - Stagnation nudge: When flying, a small horizontal impulse may be applied after prolonged immobility; grounded flyers get a small upward bias to encourage takeoff when energy permits.

- Landers (A–M):
  - Walking: `x += vx * dt` with `GROUND_FRICTION` dampening; energy increases effective mass (more energy → more friction) for stable slowdown.
  - Cost: Horizontal motion costs energy; small passive drain when unable to move.
  - Gradient limit: Cross-column ascent is limited to 1 row; larger steps are blocked.
  - Tunneling (C/D): When blocked by terrain and not by rocks/corpses, C/D can “dig” a single-cell horizontal tunnel by eating the blocking surface cell, creating a passable air cell.
  - Jump: If blocked by terrain, may perform a single jump up to `LANDER_JUMP_ASCENT_MAX_CELLS` higher and `LANDER_JUMP_DISTANCE_CELLS` columns over, with cooldown `LANDER_JUMP_COOLDOWN_DAYS` and cost of 2 energy. Direction derives from attempted motion.
  - Stagnation nudge: After sustained immobility, a small horizontal impulse is applied with increasing probability to break stagnation.

- Collisions:
  - Terrain: Entities cannot enter the surface or below. A path sampler prevents sliding through edges on fast steps.
  - Wrap-around: Horizontal positions wrap within the world width.
  - Corpses and rocks: Both block movement; C/D tunneling does not penetrate rocks/corpses.

- GoL bias: Before and after motion, local Life density nudges `vx` right when neighbors ≥5 and left when ≤2 to create emergent flows.

- Rocks (X/Y/Z):
  - Energetic flyers (energy > `ROCK_DROP_THRESHOLD`) occasionally drop rocks. Rocks integrate downward with gravity and can kill on impact based on kinetic energy. Landed rocks become static blockers and decay after `ROCK_DECAY_SECONDS`, merging into terrain.

- Day/night and energy:
  - Day length is `DAY_LENGTH_S` with `DAYLIGHT_S` of sunlight. A/B gain sunlight energy during daylight (integral equals 0.25 meal per day).
  - Idle drain applies during daylight to non-A/B that neither moved, ate, nor reproduced.

- Reproduction and ordering:
  - Pair reproduction resolves before motion. Flyers require altitude ≥ `FLYER_MIN_ALTITUDE_REPRO`. Newborns spawn in the parent cell with the lower parent letter.
  - Z reproduce asexually when energetic and at altitude. A/B auto-spawn C/D if they fail to reproduce for 30 in‑game days.
  - Internal dt==0 utility steps used by tests preserve mating pairs for a single frame to avoid same-cell predation before altitude adjustments.


## Predation and Visibility (Relative Ranks)

- Relative rank aligns landers (A..M) and flyers (N..Z): A==N, B==O, …, M==Z.
- Eating rules: higher rank eats lower; equal rank eats by 50/50 coin toss (e.g., A vs N, M vs Z). High‑energy predators are less likely to eat: above ~90 energy their appetite is damped, reducing the chance of eating as energy approaches max.
- Visibility limited to Chebyshev distance ≤2; at distance 2, a 50% visibility coin toss applies.
- A/B retaliation: if attacker energy ≤5 when attacking A/B, 50/50 chance the A/B eats the attacker instead.


## Reproduction and Evolution

- Pair reproduction (A–Y): same species pair with opposite genders, both energy ≥60.
  - Flyers only reproduce if altitude ≥20.
  - Child gets the lower parent letter and spawns in the same cell.
- Z asexual reproduction: energy >90 and altitude ≥20.
- A/B auto‑spawn C/D: if an A/B hasn’t reproduced in 30 days, it spawns a C/D in the nearest free adjacent
  non‑terrain cell (up/left/right/down). Skips if all adjacent cells are blocked.
- Long‑lived landers evolve: each 30‑day lifetime period shifts letter +2 (A→C, B→D, … M→O). Landers can become flyers.


## Corpses and Terrain

- Corpses persist as `#`, can be eaten by A/B (one meal), and block movement.
- After 5 in‑game days, corpses settle into terrain (surface rises by one; marker removed).
- Terrain and corpses are blocking; rocks are also blocking.


## Status Bar and Controls

- Displays: `N`, speed (cycles/s) [shows "[Paused]" when paused], Day/Night, days, average energy, spawned/repro/died totals, deaths by cause
  (eaten/rocks/starved), total movements, and 3/7/14‑day moving averages of movements; runtime hh:mm:ss.
- Controls:
  - `+` / `-` — Faster / slower (1–60 cycles/s). Starts paused; default speed is 30/s.
  - `p` / `s` — Pause / resume.
  - `n` — Set spawn range: prompts for MIN/MAX automata to spawn on recycle and auto-respawn. If unset, a random count between 50 and 800 is chosen.
  - `r` — Recycle: new terrain + new population.
  - `q` — Quit.

- Initialization: On program start the status shows "initializing...please wait!" until the first status update.


## Install, Run, and Develop

Prereqs: Python 3.10+.

Setup and run:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional: dev tools
pip install -r requirements-dev.txt

# Run
python -m conways_physics
# or
./run.sh
```

Makefile targets:

```bash
make clean       # remove build/test artifacts
make configure   # install build tools (build, twine)
make lint        # flake8 (120 cols; excludes .venv)
make test        # pytest with coverage (>=95%)
make cover       # verbose coverage report
make build       # sdist + wheel in dist/
```

## License

MIT. See `LICENSE.txt`.
