"""Task allocators (Step 4 §3, Step 6 §4.1).

P1 provides the two reference methods:

* ``GreedyNearest`` (B1, lower bound): whenever a drone is idle it takes the nearest open,
  unclaimed, energy-feasible task. Ties: lower task id.
* ``CentralizedSGA`` (B0, "oracle"): a central planner with global, instantaneous information
  builds every drone's task sequence by *sequential greedy assignment* on the time-discounted
  score of Step 5 §2.5,  S_i(path) = sum_k w_k * lambda_d ** tau_ik,  repeatedly inserting the
  (drone, task, position) with the largest marginal gain. It replans on events
  (``replan_on`` hook; used for failures from P5).
  NOTE: the oracle is an upper bound in *information*, not a provably optimal schedule
  (time-extended multi-robot routing is NP-hard). SGA is the centralized counterpart of the
  solution CBBA converges to, which makes B0-vs-CBBA comparisons interpretable.

Interface: ``plan(world)`` once at t = 0; ``on_idle(drone, world, now) -> task id | None``.
"""
from __future__ import annotations

from .world import World, Drone, dist


class Allocator:
    name = "base"

    def plan(self, world: World):
        pass

    def on_idle(self, d: Drone, world: World, now: float):
        raise NotImplementedError

    def decide(self, d: Drone, world: World, now: float):
        k = self.on_idle(d, world, now)
        world.assign(d, k)
        if world.rec:
            world.rec.on_decision(d.id, k, now)


class GreedyNearest(Allocator):
    name = "greedy"

    def __init__(self):
        self.claimed: dict[int, int] = {}          # task -> drone (global knowledge in P1)

    def on_idle(self, d, world, now):
        for k, i in list(self.claimed.items()):    # release tasks that are finished
            if world.tasks[k].done:
                del self.claimed[k]
        best, best_d = None, None
        for t in world.tasks:
            if t.done or t.id in self.claimed or not world.feasible(d, t.id):
                continue
            dd = dist(d.x, d.y, t.x, t.y)
            if best is None or dd < best_d - 1e-9:
                best, best_d = t.id, dd
        if best is not None:
            self.claimed[best] = d.id
        return best


class CentralizedSGA(Allocator):
    name = "oracle"

    def __init__(self):
        self.paths: dict[int, list[int]] = {}

    # --- score of a path for one drone, starting at (x, y) at time t0 with energy e0 ---
    def _path_eval(self, world, d, path, x, y, t0, e0):
        lam, score, t, e = world.cfg.lambda_d, 0.0, t0, e0
        for k in path:
            if not world.feasible(d, k, from_xy=(x, y), energy=e):
                return None
            tk = world.tasks[k]
            leg = world.time_to(x, y, tk.x, tk.y) + world.remaining_service(d, k)
            t += leg
            e -= leg
            x, y = tk.x, tk.y
            score += tk.weight * lam ** t
        return score

    def plan(self, world):
        self.replan(world, world.t)

    def replan(self, world, now):
        drones = [d for d in world.drones if d.airborne]
        pending = [t.id for t in world.tasks if not t.done]
        # keep the task each drone is currently flying to / servicing at the head of its path
        self.paths = {d.id: ([d.task] if d.task is not None else []) for d in drones}
        pending = [k for k in pending if all(k not in p for p in self.paths.values())]
        base = {d.id: self._path_eval(world, d, self.paths[d.id], d.x, d.y, now, d.energy) or 0.0
                for d in drones}
        while pending:
            best = None                       # (gain, drone id, task, position)
            for d in drones:
                p = self.paths[d.id]
                start = 1 if (p and d.task == p[0]) else 0
                for k in pending:
                    for pos in range(start, len(p) + 1):
                        cand = p[:pos] + [k] + p[pos:]
                        s = self._path_eval(world, d, cand, d.x, d.y, now, d.energy)
                        if s is None:
                            continue
                        gain = s - base[d.id]
                        key = (gain, -d.id, -k, -pos)
                        if best is None or key > best[0]:
                            best = (key, d.id, k, pos, s)
            if best is None or best[0][0] <= 0:
                break
            _, i, k, pos, s = best
            self.paths[i].insert(pos, k)
            base[i] = s
            pending.remove(k)

    def on_idle(self, d, world, now):
        # The head of a path may be the task just finished (kept there by replan); skip done tasks.
        p = self.paths.get(d.id, [])
        while p and world.tasks[p[0]].done:
            p.pop(0)
        return p.pop(0) if p else None


ALLOCATORS = {"greedy": GreedyNearest, "oracle": CentralizedSGA}


def make_allocator(name: str) -> Allocator:
    try:
        return ALLOCATORS[name]()
    except KeyError:
        raise ValueError(f"unknown allocator '{name}'; available: {sorted(ALLOCATORS)}") from None
