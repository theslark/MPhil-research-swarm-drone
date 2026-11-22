"""Command-line runner.

    python -m uavsim.run scenarios/s1_normal.toml --methods oracle greedy --seeds 2001-2030 --out results/s1.csv

Writes one CSV row per (method, seed) and prints a median summary per method.
"""
from __future__ import annotations

import argparse
import csv
import os
import statistics

from .config import load_config
from .sim import run

FIELDS = ["scenario", "method", "seed", "mcr", "mcr_unweighted", "t_mc", "coverage_auc", "dwr", "wdr",
          "distance_total_m", "energy_total_s", "energy_per_task_s", "score", "n_done", "n_tasks",
          "messages_sent", "end_time", "result_hash"]


def parse_seeds(spec: str) -> list[int]:
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="UAV swarm task-allocation simulator")
    ap.add_argument("scenario")
    ap.add_argument("--methods", nargs="+", default=["oracle", "greedy"])
    ap.add_argument("--seeds", default="2001-2030")
    ap.add_argument("--out", default=None, help="CSV output path")
    args = ap.parse_args(argv)

    rows = []
    for method in args.methods:
        for seed in parse_seeds(args.seeds):
            cfg = load_config(args.scenario, seed=seed)
            rows.append(run(cfg, method))

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.out}")

    print(f"\n{'method':8} {'n':>3} {'MCR':>6} {'T_mc med':>9} {'AUC med':>8} {'DWR':>6} {'WDR':>6} {'E/task':>7}")
    for method in args.methods:
        r = [x for x in rows if x["method"] == method]
        med = lambda key: statistics.median([x[key] for x in r if x[key] is not None]) if any(x[key] is not None for x in r) else float("nan")
        print(f"{method:8} {len(r):3d} {min(x['mcr'] for x in r):6.3f} {med('t_mc'):9.1f} "
              f"{med('coverage_auc'):8.3f} {max(x['dwr'] for x in r):6.3f} {max(x['wdr'] for x in r):6.3f} "
              f"{med('energy_per_task_s'):7.1f}")
    print("(MCR column = minimum over seeds; DWR/WDR = maximum over seeds; others = medians)")


if __name__ == "__main__":
    main()
