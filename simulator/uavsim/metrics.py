"""Ground-truth metrics (Step 6 §5). P1 implements the metrics that are defined without
failures or communication; the rest are listed in ``PENDING_METRICS`` and arrive with the
phase that makes them meaningful.

All quantities are computed from what physically happened in the World, never from an
agent's beliefs.
"""
from __future__ import annotations

from collections import defaultdict

PENDING_METRICS = {
    "task_recovery_time / service_resumption / unrecovered_fraction": "P5 (crashes)",
    "false_takeover_rate / false_takeover_cost / detector_auroc": "P5 (suspicion)",
    "owner_divergence / time_to_consistency": "P3-P4 (ledger, partitions)",
    "packet_delivery_ratio / dissemination_latency / connectivity": "P3 (comm models)",
    "autonomy_during_isolation": "P4 (partitions)",
    "leader_recovery_time": "P5 (coordinator ablation)",
}


class Recorder:
    def __init__(self):
        self.service = defaultdict(float)        # (drone, task) -> service seconds
        self.move_to = defaultdict(float)        # (drone, task) -> distance flown toward task
        self.move_home = defaultdict(float)      # drone -> distance flown returning to base
        self.energy = defaultdict(float)         # drone -> airborne seconds consumed
        self.completions = {}                    # task -> (time, drone)
        self.land_time = {}
        self.events = []                         # (time, kind, drone, task) for debugging/tests

    # callbacks from World / Allocator
    def on_move(self, i, k, step):
        if k is None:
            self.move_home[i] += step
        else:
            self.move_to[(i, k)] += step

    def on_service(self, i, k, h):
        self.service[(i, k)] += h

    def on_energy(self, i, h):
        self.energy[i] += h

    def on_complete(self, k, i, t):
        self.completions[k] = (t, i)
        self.events.append((t, "complete", i, k))

    def on_arrive(self, i, k, t):
        self.events.append((t, "arrive", i, k))

    def on_land(self, i, t):
        self.land_time[i] = t
        self.events.append((t, "land", i, None))

    def on_decision(self, i, k, t):
        self.events.append((t, "decide", i, k))


def compute(world, rec: Recorder, comm=None) -> dict:
    cfg = world.cfg
    tasks = world.tasks
    W = sum(t.weight for t in tasks)
    S = sum(t.service for t in tasks)
    done = [t for t in tasks if t.done]
    T = cfg.t_max

    mcr = sum(t.weight for t in done) / W
    mcr_unweighted = len(done) / len(tasks)
    t_mc = max(t.done_time for t in done) if len(done) == len(tasks) else None   # censored if incomplete
    # coverage AUC: (1/T) * integral_0^T MCR(t) dt, exact for the step function MCR(t)
    auc = sum(t.weight * (T - t.done_time) for t in done) / (W * T)

    serv_k = defaultdict(float)
    for (i, k), h in rec.service.items():
        serv_k[k] += h
    dwr = sum(serv_k[t.id] - t.service for t in done) / S
    total_service = sum(serv_k.values())

    dist_total = sum(rec.move_to.values()) + sum(rec.move_home.values())
    wasted = sum(dd for (i, k), dd in rec.move_to.items() if rec.service.get((i, k), 0.0) <= 0.0)
    wdr = wasted / dist_total if dist_total > 0 else 0.0

    energy_total = sum(rec.energy.values())
    score = sum(t.weight * cfg.lambda_d ** t.done_time for t in done)

    m = {
        "mcr": mcr,
        "mcr_unweighted": mcr_unweighted,
        "t_mc": t_mc,
        "coverage_auc": auc,
        "dwr": dwr,
        "wdr": wdr,
        "distance_total_m": dist_total,
        "energy_total_s": energy_total,
        "energy_per_task_s": energy_total / len(done) if done else None,
        "score": score,
        "n_done": len(done),
        "n_tasks": len(tasks),
        "total_service_s": total_service,
    }
    if comm is not None:
        m["messages_sent"] = comm.sent
        m["bytes_sent"] = comm.bytes_sent
        m["messages_per_task"] = comm.sent / len(done) if done else None
    return m
