"""Simulation driver: one run = (scenario config, method, seed) -> metrics."""
from __future__ import annotations

import hashlib
import json

from .allocators import make_allocator
from .comms import make_comm
from .config import SimConfig
from .metrics import Recorder, compute
from .world import World


def run(cfg: SimConfig, method: str, keep_events: bool = False) -> dict:
    rec = Recorder()
    world = World(cfg, recorder=rec)
    comm = make_comm(cfg)
    alloc = make_allocator(method)
    alloc.plan(world)
    while not world.finished():
        world.step(alloc.decide)
    m = compute(world, rec, comm)
    m.update(scenario=cfg.name, method=method, seed=cfg.seed, end_time=world.t)
    m["result_hash"] = result_hash(world, rec)
    if keep_events:
        m["events"] = rec.events
        m["completions"] = {k: v for k, v in sorted(rec.completions.items())}
    return m


def result_hash(world, rec) -> str:
    """Fingerprint of the physical outcome, used to check determinism."""
    payload = {
        "completions": sorted((k, round(t, 9), i) for k, (t, i) in rec.completions.items()),
        "service": sorted((i, k, round(h, 9)) for (i, k), h in rec.service.items()),
        "final": [(d.id, round(d.x, 6), round(d.y, 6), round(d.energy, 6), d.mode.value) for d in world.drones],
    }
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16]
