"""Simulation configuration (Step 6, Table "Default simulation parameters").

Scenarios are TOML files (stdlib ``tomllib``). Every field has a default equal to the
Step 6 default, so a scenario file only lists what it changes.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields, asdict
from typing import Optional


@dataclass
class TaskSpec:
    """Explicit task (used by hand-checkable scenarios). Otherwise tasks are generated on a grid."""
    x: float
    y: float
    service: float
    weight: float = 1.0


@dataclass
class SimConfig:
    # --- area and tasks ---
    area_w: float = 2000.0            # m
    area_h: float = 1500.0            # m
    grid_cols: int = 6                # M = grid_cols * grid_rows sectors
    grid_rows: int = 5
    service_min: float = 150.0        # s, uniform service time per sector
    service_max: float = 250.0
    priority_fraction: float = 0.0    # share of tasks with weight priority_weight (Step 6 priority variant)
    priority_weight: float = 3.0
    tasks: Optional[list[TaskSpec]] = None   # explicit tasks override the grid

    # --- drones ---
    n_drones: int = 10
    speed: float = 10.0               # m/s cruise
    energy: float = 1800.0            # s of airborne flight-equivalent
    energy_margin: float = 0.10       # reserve fraction kept for the return flight
    base_x: float = 0.0               # launch / landing base (area edge, mid-height by default)
    base_y: Optional[float] = None

    # --- time ---
    dt: float = 0.5                   # s, simulation step (communication granularity in later phases)
    t_max: float = 1800.0             # s, mission horizon

    # --- communication (P1: full connectivity) ---
    comm_model: str = "full"          # "full" in P1; "disk" etc. from P3
    comm_range: float = float("inf")

    # --- allocation ---
    lambda_d: float = 0.999           # per-second time discount in the CBBA-style score (Step 5 §2.5)

    # --- experiment ---
    name: str = "unnamed"
    seed: int = 0

    def __post_init__(self):
        if self.base_y is None:
            self.base_y = self.area_h / 2.0
        if self.tasks is not None:
            self.tasks = [t if isinstance(t, TaskSpec) else TaskSpec(**t) for t in self.tasks]

    @property
    def n_tasks(self) -> int:
        return len(self.tasks) if self.tasks is not None else self.grid_cols * self.grid_rows

    def with_overrides(self, **kw) -> "SimConfig":
        d = asdict(self)
        d.update(kw)
        return SimConfig(**d)


def load_config(path: str, **overrides) -> SimConfig:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    known = {f.name for f in fields(SimConfig)}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"Unknown config keys in {path}: {sorted(unknown)}")
    raw.update(overrides)
    return SimConfig(**raw)
