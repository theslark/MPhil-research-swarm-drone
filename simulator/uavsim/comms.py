"""Communication models (Step 5 §2.1, Step 6 §1).

P1 implements only full connectivity. The interface is what later phases extend:
range-limited links (P3), Bernoulli / Gilbert-Elliott loss (P3), forced partitions and
blackouts (P4). Allocators and agents must go through this object, never assume links.
"""
from __future__ import annotations

from collections import defaultdict


class CommModel:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sent = 0
        self.delivered = 0
        self.bytes_sent = 0

    def links(self, world) -> dict[int, set[int]]:
        raise NotImplementedError

    def components(self, world) -> list[set[int]]:
        """Connected components (partitions) of the current communication graph."""
        adj = self.links(world)
        seen, comps = set(), []
        for s in sorted(adj):
            if s in seen:
                continue
            comp, stack = set(), [s]
            while stack:
                u = stack.pop()
                if u in comp:
                    continue
                comp.add(u)
                stack.extend(adj[u] - comp)
            seen |= comp
            comps.append(comp)
        return comps

    def send(self, world, src: int, dst: int, nbytes: int = 0) -> bool:
        """Attempt one message; returns whether it was delivered. Counts overhead."""
        self.sent += 1
        self.bytes_sent += nbytes
        ok = dst in self.links(world).get(src, set())
        self.delivered += ok
        return ok


class FullConnectivity(CommModel):
    """Every airborne drone can reach every other airborne drone, loss-free (scenario S1)."""

    def links(self, world):
        alive = [d.id for d in world.drones if d.airborne]
        adj = defaultdict(set)
        for i in alive:
            adj[i] = set(alive) - {i}
        return dict(adj)


def make_comm(cfg) -> CommModel:
    if cfg.comm_model == "full":
        return FullConnectivity(cfg)
    raise NotImplementedError(f"comm_model '{cfg.comm_model}' arrives in phase P3")
