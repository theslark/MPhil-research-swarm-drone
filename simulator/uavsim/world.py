"""Ground-truth world: tasks, drones, kinematics, service and energy (Step 5 §2.1).

Time handling
-------------
The simulation advances in steps of ``dt`` (the granularity at which communication will
happen from P3 on), but *within* a step every arrival, completion and task decision is
processed at its exact time, in (time, drone id) order. Because drone motion between events
is independent and linear, all drones can be advanced together to the next event time.
This keeps results exact (hand-checkable) and deterministic.

Ground truth vs. beliefs
------------------------
``World`` is the simulator's truth (true positions, true crash status, true completion).
Allocators in P1 read it directly (global knowledge). From P2 on, agents will act on their
own ledger replicas; the world still records what physically happens, which is what the
metrics measure (e.g., a drone that services an already-completed task creates duplicated work).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .config import SimConfig

EPS = 1e-9


class Mode(Enum):
    IDLE = "idle"              # airborne, no activity -> must decide now
    TO_TASK = "to_task"        # flying to a task
    SERVICING = "servicing"    # sweeping a sector
    RETURNING = "returning"    # flying back to base
    LANDED = "landed"          # on the ground, no energy use
    CRASHED = "crashed"        # fail-silent (used from P5)


@dataclass
class Task:
    id: int
    x: float
    y: float
    service: float             # s_k
    weight: float = 1.0        # w_k
    done_time: Optional[float] = None
    completer: Optional[int] = None

    @property
    def done(self) -> bool:
        return self.done_time is not None


@dataclass
class Drone:
    id: int
    x: float
    y: float
    energy: float
    mode: Mode = Mode.IDLE
    task: Optional[int] = None                     # current target / serviced task
    progress: dict = field(default_factory=dict)   # task id -> own service seconds (rho_ik * s_k)
    alive: bool = True

    @property
    def airborne(self) -> bool:
        return self.mode not in (Mode.LANDED, Mode.CRASHED)


def dist(ax, ay, bx, by) -> float:
    return math.hypot(bx - ax, by - ay)


def make_tasks(cfg: SimConfig, rng: random.Random) -> list[Task]:
    if cfg.tasks is not None:
        return [Task(i, t.x, t.y, t.service, t.weight) for i, t in enumerate(cfg.tasks)]
    tasks = []
    cw, ch = cfg.area_w / cfg.grid_cols, cfg.area_h / cfg.grid_rows
    for r in range(cfg.grid_rows):
        for c in range(cfg.grid_cols):
            s = rng.uniform(cfg.service_min, cfg.service_max)
            tasks.append(Task(len(tasks), (c + 0.5) * cw, (r + 0.5) * ch, s))
    n_pri = int(round(cfg.priority_fraction * len(tasks)))
    for t in rng.sample(tasks, n_pri):
        t.weight = cfg.priority_weight
    return tasks


class World:
    def __init__(self, cfg: SimConfig, recorder=None):
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)
        self.tasks = make_tasks(cfg, self.rng)
        self.drones = [Drone(i, cfg.base_x, cfg.base_y, cfg.energy) for i in range(cfg.n_drones)]
        self.t = 0.0
        self.rec = recorder

    # ------------------------------------------------------------------ queries
    def open_tasks(self) -> list[Task]:
        return [t for t in self.tasks if not t.done]

    def time_to(self, x0, y0, x1, y1) -> float:
        return dist(x0, y0, x1, y1) / self.cfg.speed

    def remaining_service(self, d: Drone, k: int) -> float:
        return max(0.0, self.tasks[k].service - d.progress.get(k, 0.0))

    def feasible(self, d: Drone, k: int, from_xy=None, energy=None) -> bool:
        """Energy check: reach task, finish it, return to base, keep the reserve margin."""
        x, y = from_xy if from_xy else (d.x, d.y)
        e = d.energy if energy is None else energy
        t = self.tasks[k]
        need = (self.time_to(x, y, t.x, t.y) + self.remaining_service(d, k)
                + self.time_to(t.x, t.y, self.cfg.base_x, self.cfg.base_y))
        return need * (1.0 + self.cfg.energy_margin) <= e + EPS

    # ------------------------------------------------------------------ commands
    def assign(self, d: Drone, k: Optional[int]):
        """Point drone d at task k (or send it home if k is None)."""
        if k is None:
            d.task = None
            d.mode = Mode.RETURNING if dist(d.x, d.y, self.cfg.base_x, self.cfg.base_y) > EPS else Mode.LANDED
            return
        d.task = k
        t = self.tasks[k]
        d.mode = Mode.SERVICING if dist(d.x, d.y, t.x, t.y) <= EPS else Mode.TO_TASK

    # ------------------------------------------------------------------ dynamics
    def _time_to_event(self, d: Drone) -> float:
        if d.mode == Mode.IDLE:
            return 0.0
        if d.mode == Mode.TO_TASK:
            t = self.tasks[d.task]
            return self.time_to(d.x, d.y, t.x, t.y)
        if d.mode == Mode.SERVICING:
            return self.remaining_service(d, d.task)
        if d.mode == Mode.RETURNING:
            return self.time_to(d.x, d.y, self.cfg.base_x, self.cfg.base_y)
        return math.inf

    def _advance(self, d: Drone, h: float):
        """Advance drone d by h seconds of its current activity (no event crossing)."""
        if h <= 0 or not d.airborne:
            return
        d.energy -= h
        if self.rec:
            self.rec.on_energy(d.id, h)
        if d.mode in (Mode.TO_TASK, Mode.RETURNING):
            if d.mode == Mode.TO_TASK:
                tx, ty = self.tasks[d.task].x, self.tasks[d.task].y
            else:
                tx, ty = self.cfg.base_x, self.cfg.base_y
            rem = dist(d.x, d.y, tx, ty)
            step = min(rem, self.cfg.speed * h)
            if rem > EPS:
                d.x += (tx - d.x) * step / rem
                d.y += (ty - d.y) * step / rem
            if self.rec:
                self.rec.on_move(d.id, d.task if d.mode == Mode.TO_TASK else None, step)
        elif d.mode == Mode.SERVICING:
            d.progress[d.task] = d.progress.get(d.task, 0.0) + h
            if self.rec:
                self.rec.on_service(d.id, d.task, h)

    def _resolve(self, d: Drone, now: float) -> bool:
        """Handle a finished activity. Returns True if the drone now needs a decision."""
        if d.mode == Mode.TO_TASK:
            t = self.tasks[d.task]
            d.x, d.y = t.x, t.y
            d.mode = Mode.SERVICING
            if self.rec:
                self.rec.on_arrive(d.id, d.task, now)
            return self.remaining_service(d, d.task) <= EPS and self._resolve(d, now)
        if d.mode == Mode.SERVICING:
            t = self.tasks[d.task]
            if not t.done:                      # first drone to finish its own full sweep completes it
                t.done_time, t.completer = now, d.id
                if self.rec:
                    self.rec.on_complete(t.id, d.id, now)
            d.task = None
            d.mode = Mode.IDLE
            return True
        if d.mode == Mode.RETURNING:
            d.x, d.y = self.cfg.base_x, self.cfg.base_y
            d.mode = Mode.LANDED
            if self.rec:
                self.rec.on_land(d.id, now)
            return False
        return d.mode == Mode.IDLE

    def step(self, decide):
        """Advance one dt. ``decide(drone, world, now)`` is called whenever a drone is idle."""
        t_end = min(self.t + self.cfg.dt, self.cfg.t_max)
        # decisions pending at the start of the step (e.g., t = 0)
        for d in self.drones:
            if d.mode == Mode.IDLE:
                decide(d, self, self.t)
        guard = 0
        while self.t < t_end - EPS:
            guard += 1
            if guard > 10000:
                raise RuntimeError("event loop did not converge")
            nxt = min([self._time_to_event(d) for d in self.drones if d.airborne] + [t_end - self.t])
            h = max(0.0, nxt)
            for d in self.drones:
                self._advance(d, h)
            self.t += h
            needs = [d for d in self.drones if d.airborne and self._time_to_event(d) <= EPS]
            for d in sorted(needs, key=lambda q: q.id):
                if self._resolve(d, self.t):
                    decide(d, self, self.t)
            if h <= EPS and not needs:
                break
        self.t = t_end

    def finished(self) -> bool:
        return self.t >= self.cfg.t_max - EPS or all(not d.airborne for d in self.drones)
