# uavsim: Simulator for Self-Healing UAV Task Allocation

Implementation of the evaluation framework in Steps 5–6 (`../05_Step5_Architecture_and_Methodology/`, `../06_Step6_Experimental_Design/`).

**Current phase: P1 complete.** P1 covers the baseline swarm: world model, full-connectivity communication, greedy and centralized-oracle allocators, and ground-truth metrics.

## Requirements
- P1: Python ≥ 3.11, **standard library only** (uses `tomllib` and `unittest`).
- From P5 (MAPPO): PyTorch. Create a virtual environment before that phase (see "Next phases").

## Quick start
```bash
cd simulator
python3 -m unittest discover -s tests -t . -v                     # 15 tests
python3 -m uavsim.run scenarios/s1_normal.toml --methods oracle greedy \
        --seeds 2001-2030 --out results/p1/s1_normal.csv            # P1 exit check
```

## Layout
| Path | Purpose |
|---|---|
| `uavsim/config.py` | `SimConfig` with all Step 6 defaults; scenarios are TOML files that override them |
| `uavsim/world.py` | Ground truth: tasks (sectors), drones, kinematics, service, energy, landing |
| `uavsim/comms.py` | Communication interface; P1 = `FullConnectivity` |
| `uavsim/allocators.py` | `GreedyNearest` (B1) and `CentralizedSGA` oracle (B0) |
| `uavsim/metrics.py` | Ground-truth metrics (MCR, T_mc, coverage AUC, DWR, WDR, distance, energy, score) |
| `uavsim/sim.py`, `uavsim/run.py` | One-run driver (with determinism hash) and command-line batch runner |
| `scenarios/` | `s1_normal.toml` (Step 6 S1), `p1_handcheck.toml` (3 drones, 5 tasks) |
| `tests/` | Hand-check, exit criterion, determinism, physical invariants |
| `results/p1/` | P1 exit-check output (verification data, **not research results**) |

## Design notes
- **Exact event timing.** Time advances in `dt` steps (the granularity communication will use from P3). Within a step, every arrival, completion and decision happens at its exact time, ordered by (time, drone id). Results are therefore deterministic and can be checked by hand.
- **Ground truth vs. beliefs.** `World` records what physically happens. In P1, allocators read it directly (global knowledge). From P2 on, agents act on their own ledger replicas, while metrics keep using ground truth. That is how duplicated work and false takeovers become measurable.
- **Energy.** Airborne time consumes 1 unit/s; landed drones consume nothing. A drone accepts a task only if it can reach it, finish it and fly home with a 10% reserve. With nothing left to do, it flies home.
- **Oracle (B0).** Centralized sequential greedy assignment maximising the time-discounted score of Step 5 §2.5 with *global, instantaneous* information. It bounds *information*, not optimality: time-extended multi-robot routing is NP-hard. In P1 it beats greedy on its own objective (score) on 30/30 seeds, yet greedy has a slightly shorter makespan (median 885 s vs. 914 s). Reports must therefore present B0 as an information bound, and allocation efficiency must be measured with the score.

## P1 exit check (2026-11-22)
| Criterion (Step 5 §3.2) | Result |
|---|---|
| Oracle reaches 100% completion with no faults | **Met**: MCR = 1.0 on 30/30 seeds (S1, seeds 2001–2030) |
| Metrics checked by hand on a 3-drone, 5-task case | **Met**: completion times, completers, landing times, T_mc, AUC, DWR, WDR, distance, energy and score all match the hand derivation in `tests/test_handcheck.py` |

Other P1 observations (verification only):
- **Workload calibration (Step 6 §1):** fault-free makespan is 822–975 s, against T_max = 1800 s. The planned spare capacity for failure scenarios exists.
- **Run time:** about 0.1–0.2 s per run, far below Step 6's 30 s budget assumption. It will grow with communication modelling.

## Next phases (Step 5 §3.2)
| Phase | Adds |
|---|---|
| P2 | Per-agent asynchronous CBBA, isolation/energy policy, agents acting on local views |
| P3 | Range-limited links, Bernoulli / Gilbert–Elliott loss, bandwidth cap; CRDT ledger + sync engine with property tests |
| P4 | Natural and forced partitions, blackouts; CC-OPI re-implementation |
| P5 | Crash injection, suspicion estimator, takeover (threshold + MAPPO), coordinator ablation, recovery and false-takeover metrics |
| P6 | Join/leave, swarm-size sweep |
| P7 | Full scenario matrix, ablations, statistics |

Before P5, set up an environment for PyTorch, e.g. `python3 -m venv .venv && .venv/bin/pip install torch`. The system Python here has no pip.
