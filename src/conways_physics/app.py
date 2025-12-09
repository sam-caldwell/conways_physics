"""Textual TUI application for the Conways Physics simulation.

Provides the main gameplay panel, status footer, and app lifecycle. The app
uses a fixed timer to gate simulation cycles based on the current speed for a
smooth, predictable feel.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Footer
from textual.reactive import reactive
from textual import events

from .sim import Simulation
from .config import DEFAULT_WIDTH, DEFAULT_HEIGHT, DAY_LENGTH_S
from .renderer import render_sim


class GameplayPanel(Static):
    """Panel responsible for rendering the world state."""
    sim: Simulation

    def __init__(self, sim: Simulation) -> None:
        super().__init__("")
        self.sim = sim

    def on_mount(self) -> None:
        # Refresh at ~10fps
        self.set_interval(0.1, self.refresh)

    def render(self):  # type: ignore[override]
        """Render the world into this panel's bounds."""
        w = max(1, self.size.width)
        h = max(1, self.size.height)
        # Ensure the surface spans the full current view and sits near the bottom
        if (self.sim.width != w) or (self.sim.height != h):
            self.sim.configure_surface_for_view(w, h, sea_level_offset=4, amplitude=3)
        return render_sim(self.sim, w, h)


class StatusPanel(Static):
    """Footer panel displaying summary details and timing."""
    text = reactive("")

    def update_status(
        self,
        *,
        N: int,
        speed: float,
        is_day: bool,
        days: int,
        runtime_s: float,
        avg_energy: float,
        spawned: int,
        died: int,
        eaten: int,
        rocks: int,
        starved: int,
        moves_total: int,
        ma3: float,
        ma7: float,
        ma14: float,
    ) -> None:
        """Update the displayed status string."""
        hh = int(runtime_s // 3600)
        mm = int((runtime_s % 3600) // 60)
        ss = int(runtime_s % 60)
        day_str = "Day" if is_day else "Night"
        self.text = (
            f"N={N}  speed={speed:.1f}/s  {day_str}  days={days}  "
            f"avgE={avg_energy:.1f}  spawned={spawned}  died={died}  "
            f"eaten={eaten}  rocks={rocks}  starved={starved}  "
            f"moves={moves_total}  ma3={ma3:.0f}  ma7={ma7:.0f}  ma14={ma14:.0f}  "
            f"run={hh:02d}:{mm:02d}:{ss:02d}"
        )
        self.update(self.text)


class ConwaysPhysics(App):
    """Textual application container for the simulation."""
    TITLE = "Conways Physics"
    CSS = """
    Screen { layout: vertical; }
    GameplayPanel { height: 1fr; border: round white; }
    StatusPanel { height: 3; }
    """

    BINDINGS = [
        ("+", "speed_up", "Increase speed"),
        ("-", "speed_down", "Decrease speed"),
        ("p", "pause", "Pause"),
        ("s", "resume", "Resume"),
        ("r", "recycle", "Recycle"),
        ("q", "quit", "Quit"),
    ]
    running: bool = True
    speed_cps: float = 30.0
    runtime_s: float = 0.0
    days: int = 0  # maintained for backwards-compat; display derives from t_abs
    sim: Simulation
    _sim_timer = None
    _status_timer = None
    _accum: float = 0.0
    _base_tick: float = 0.05  # 20 Hz timer; we gate sim cycles by speed_cps
    gameplay: GameplayPanel = None
    status: StatusPanel = None

    def compose(self) -> ComposeResult:
        """Construct the layout and initialize the simulation."""
        self.sim = Simulation(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
        self.sim.auto_rocks = True
        self.gameplay = GameplayPanel(self.sim)
        self.status = StatusPanel()
        yield Vertical(
            self.gameplay,
            self.status,
            Footer(),
        )

    def on_mount(self) -> None:
        """Set up timers and seed the world when the app mounts."""
        # Size-aware surface configuration
        w = max(1, self.gameplay.size.width or DEFAULT_WIDTH)
        h = max(1, self.gameplay.size.height or DEFAULT_HEIGHT)
        self.sim.configure_surface_for_view(w, h, sea_level_offset=4, amplitude=3)
        # Seed initial population: at least 100 automata, ~50% flyers/landers
        self.sim.seed_population_balanced(100)
        # Main simulation timer
        self._sim_timer = self.set_interval(self._base_tick, self._tick_sim)
        # Status refresh timer
        self._status_timer = self.set_interval(0.2, self._update_status)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)

    def action_speed_up(self) -> None:
        """Increase the simulation rate."""
        self.speed_cps = min(60.0, self.speed_cps + 1.0)

    def action_speed_down(self) -> None:
        """Decrease the simulation rate."""
        self.speed_cps = max(1.0, self.speed_cps - 1.0)

    def action_pause(self) -> None:
        """Pause simulation stepping."""
        self.running = False

    def action_resume(self) -> None:
        """Resume simulation stepping."""
        self.running = True

    def action_recycle(self) -> None:
        """Reset the world with a fresh surface and population."""
        # Determine current viewport size and rebuild simulation
        w = max(1, self.gameplay.size.width or DEFAULT_WIDTH)
        h = max(1, self.gameplay.size.height or DEFAULT_HEIGHT)
        new_sim = Simulation(width=w, height=h)
        new_sim.auto_rocks = True
        new_sim.configure_surface_for_view(w, h, sea_level_offset=4, amplitude=3)
        new_sim.seed_population_balanced(100)
        # Swap in new simulation and reset runtime counters
        self.sim = new_sim
        self.gameplay.sim = new_sim
        self.runtime_s = 0.0
        self.days = 0
        self._accum = 0.0
        # Trigger immediate repaint
        self.gameplay.refresh()

    def _tick_sim(self) -> None:
        """Timer callback to advance simulation time appropriately."""
        if not self.running:
            return
        # Gate fixed-size sim cycles by speed
        self._accum += self._base_tick
        target = 1.0 / max(1.0, self.speed_cps)
        while self._accum >= target:
            self.sim.step(1.0)
            self.runtime_s += 1.0
            # Auto-respawn when population reaches zero
            if not any(a.alive for a in self.sim.automata):
                self.action_recycle()
            self._accum -= target
            # days displayed is derived in _update_status via t_abs

    def _update_status(self) -> None:
        """Timer callback to refresh the status footer."""
        alive = sum(1 for a in self.sim.automata if a.alive)
        if alive > 0:
            total_energy = sum(a.energy for a in self.sim.automata if a.alive)
            avg_energy = total_energy / float(alive)
        else:
            avg_energy = 0.0
        moves_total, ma3, ma7, ma14 = self.sim.movement_stats()
        days_now = int(self.sim.world.t_abs // DAY_LENGTH_S)
        self.days = days_now
        self.status.update_status(
            N=alive,
            speed=self.speed_cps,
            is_day=self.sim.world.is_day,
            days=days_now,
            runtime_s=self.runtime_s,
            avg_energy=avg_energy,
            spawned=self.sim.spawned_total,
            died=self.sim.died_total,
            eaten=self.sim.eaten_total,
            rocks=self.sim.rock_deaths_total,
            starved=self.sim.starved_total,
            moves_total=moves_total,
            ma3=ma3,
            ma7=ma7,
            ma14=ma14,
        )

    def on_resize(self, event: events.Resize) -> None:  # type: ignore[override]
        """Resize handler to regenerate surface upon viewport changes."""
        # Reconfigure surface to span new viewport
        w = max(1, self.gameplay.size.width or DEFAULT_WIDTH)
        h = max(1, self.gameplay.size.height or DEFAULT_HEIGHT)
        self.sim.configure_surface_for_view(w, h, sea_level_offset=4, amplitude=3)
