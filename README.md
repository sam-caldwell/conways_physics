# Conways Physics — Terminal World Simulation (Textual/Rich)

Conways Physics is a zero‑player, terminal‑based world simulation. Land species (A–M) and flying species (N–Z)
move, eat, reproduce, and evolve on a scrolling ASCII terrain. The UI is built with Textual/Rich and renders a
two‑panel layout: the world view and a status footer.


## Key Features

- Two‑panel TUI with a white‑bordered world panel and a status footer.
- Terrain spans the full width; baseline sits 4 rows above the bottom with ±3 variation. Terrain and below use
  ASCII 219 (full block) in grey; corpses render as grey `#` and block movement.
- Automata letters colored by energy via a 16‑color palette.
- Day/night cycle: 30s days, first 15s daylight. A/B gain sunlight energy during daylight.
- Corpses decay into terrain after 5 in‑game days (surface rises by one, corpse marker removed). A/B can eat corpses.
- Rocks: X/Y/Z can drop rocks when energetic; rocks fall and can kill on impact. Rocks block movement.
- Press `r` any time to recycle: new terrain and a fresh population.


## Species, Spawning, and Energy

- Landers: A–M. Flyers: N–Z.
- Balanced seeding: 10% flyers (including Z), 90% landers. All start at energy 100.
- Spawn locations:
  - Landers spawn on the air boundary (surface−1).
  - Flyers spawn in the top third, and at least 20 rows above local terrain when possible.


## Motion, Bias, Tunneling, and Jumps

- Flyers
  - Move randomly in cardinal directions, biased toward nearby lower‑rank prey and away from higher‑rank predators
    (vision within Chebyshev distance ≤2; at distance 2 visibility is 50%).
  - Actively climb until altitude ≥20; bounce at the air boundary; can’t translate along ground.
- Landers
  - Choose direction using priorities: mate (if energy >10) > avoid predators > pursue prey. If the chosen side is
    blocked by terrain, try the opposite side. May climb up to 1 row; larger steps block.
  - C/D tunneling: when colliding laterally with terrain (not rocks/corpses), C/D eat the surface cell to carve
    tunnels.
  - Jump: when blocked by terrain, may randomly perform a single jump up 3 rows and over 2 columns in the intended
    direction. Cooldown: once per 7 in‑game days. Jump costs 2 energy.
- GoL influence: a simple neighborhood count biases horizontal drift (left/right) for emergent flows.


## Predation and Visibility (Relative Ranks)

- Relative rank aligns landers (A..M) and flyers (N..Z): A==N, B==O, …, M==Z.
- Eating rules: higher rank eats lower; equal rank eats by 50/50 coin toss (e.g., A vs N, M vs Z).
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

- Displays: `N`, speed (cycles/s), Day/Night, days, average energy, spawned/died totals, deaths by cause
  (eaten/rocks/starved), total movements, and 3/7/14‑day moving averages of movements; runtime hh:mm:ss.
- Controls:
  - `+` / `-` — Faster / slower (1–60 cycles/s). Starts at 30/s.
  - `p` / `s` — Pause / resume.
  - `r` — Recycle: new terrain + new population.
  - `q` — Quit.


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


## Repository Layout

- `src/conways_physics/`
  - `app.py` — Textual UI (ConwaysPhysics), key bindings, status bar
  - `sim.py` — Simulation orchestration and rules
  - `automata.py` — Automaton + Rock physics
  - `species.py` — Species helpers and relative rank
  - `terrain.py` — Surface generation
  - `life.py` — GoL stepping
  - `world.py` — Day/night clock
  - `renderer.py` — Text rendering (Rich)
  - `config.py` — Tunables and defaults
- `tests/` — Unit + integration tests (coverage gate ≥95%)
- `.github/workflows/ci.yml` — CI: test matrix + build and upload artifacts
- `.github/dependabot.yml` — Weekly dependency updates (pip, GitHub Actions)


## License

MIT. See `LICENSE.txt`.

