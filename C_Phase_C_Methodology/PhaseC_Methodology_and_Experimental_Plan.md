# Phase C — Methodology, Simulation and Experimental Plan

**Title (unchanged):** AI-Driven Collaborative Environment Mapping, Resilient Coordination, and Self-Healing in Decentralized UAV Swarms under Intermittent Connectivity

**Date:** 2026-11-23 · **Builds on:** Phase B design. Recommended defaults D-4 to D-7 and D-11 to D-13 approved.

**Status:** plan only. No experiments have been run. Every result table below is an empty template.

---

## 0. Decisions now fixed

| ID | Fixed value |
|---|---|
| D-4 | Crash-stop + omission faults only |
| D-5 | N ∈ {5, **10**, 20} (10 = default); area 2 km × 2 km; 10 m cells (200 × 200); horizon T = 2400 s; Δt = 1 s |
| D-6 | Post-disaster SAR survey with victims, hazards, buildings, restricted cells |
| D-7 | Synthetic seeded worlds with exact ground truth |
| D-11 | Parameters set by a sensitivity sweep (§6.2), not hand-picked |
| D-12 | **CPU-only** budget. The development machine has 6 cores, 11 GB RAM and no GPU. Learned policy: small network, ≤ 48 CPU-hours total training, then the go/no-go gate (§5, Stage 4b) |
| D-13 | Two outputs: the long MPhil manuscript (holds the ~25-page literature review), then a condensed IEEE paper |

---

## 1. Simulation technology

### 1.1 Tool evaluation

| Tool | Needed for | Decision | Reason |
|---|---|---|---|
| **Python 3** | Everything | ✅ | One language; reproducible; supervisor-readable |
| **NumPy** | Grid maps, sensor updates, metrics | ✅ | Vectorized 200×200 grids; runs on CPU |
| **NetworkX** | Communication graph, components, centrality (coordinator score) | ✅ | Graph utilities only; small N |
| PyTorch (CPU) | Learned policy (Stage 4b only) | ✅ conditional | Needed only if Stage 4b runs |
| Gymnasium / PettingZoo | RL environment API | ✅ conditional (PettingZoo ParallelEnv wrapper) | Standard multi-agent API; thin wrapper over the simulator |
| SciPy | Statistical tests | ✅ | Wilcoxon, bootstrap |
| Matplotlib | Figures | ✅ | — |
| ns-3 / OMNeT++ | Packet-level networking | ❌ | Routing and MAC are out of scope (A6). Integration cost is high and adds nothing to the RQs |
| Gazebo / PX4 SITL | Flight dynamics | ❌ | Kinematic UAVs suffice (A5). Too heavy for 6 CPU cores at this run count |

**Smallest sufficient combination:** Python + NumPy + NetworkX + SciPy/Matplotlib, plus PyTorch and PettingZoo for Stage 4b only.

### 1.2 Environment setup

- Create a project virtual environment (`python -m venv .venv`) with pinned versions recorded in `requirements.txt`. The system Python 3.14 currently has no NumPy.
- Fix the random seeds of the world generator, the link process, the failure schedule and the policy. Log each run's seeds and git commit hash in its output.

### 1.3 Code reuse

The earlier `uavsim` package (commit `d112c3c`) has a world model, a communication-model interface with connected components, a centralized oracle and greedy allocators, and metrics, with 15 tests. The new package `swarmsim/` will port the kinematics, energy model, comms interface and oracle allocator (B0). It will **not** reuse the earlier task-only framing or metrics.

### 1.4 Simulator structure (planned)

```
simulator/
  swarmsim/
    world.py        # ground truth grid, victims, hazards, scheduled changes, kinematics, energy
    sensing.py      # footprint, p_d / p_fa, semantic confusion, height noise
    crdt_map.py     # per-origin cells, LOCALUPDATE, merge ⊔, fused read, contested/stale masks
    sync.py         # deltas, version vectors, gossip, anti-entropy, priority queue, byte budget
    comms.py        # range, q(d), Gilbert–Elliott, scripted partitions, per-contact budget
    membership.py   # heartbeats, incarnations, φ-accrual, reachability, suspicion states
    tasks.py        # task generation, deterministic task IDs, lease table CRDT
    allocation.py   # coordinator auction, self-assignment, B0 oracle
    election.py     # partition-local coordinator, epochs, merge rule
    agent.py        # Alg. 1 agent loop; heuristic planner; policy hook
    baselines.py    # B1/B2/B3 variants, ablation switches
    metrics.py      # §3 metrics, from ground truth and replicas
    scenarios/      # S01–S14 TOML files
    run.py          # CLI: scenario × config × seeds → CSV/JSON
  rl/               # Stage 4b: PettingZoo wrapper, IPPO trainer, evaluation
  tests/            # unit, property-based and scenario tests
  analysis/         # statistics and figures
```

All mechanisms sit behind configuration switches, so baselines and ablations are configurations of one code base rather than separate implementations. This keeps comparisons fair.

---

## 2. Simulation scenarios

Common setup: default N = 10 and default link parameters unless stated otherwise. "Expected behaviour" means *what the mechanism is designed to do*. These are functional checks, not predicted numbers.

| # | Scenario | Setup | Purpose | Expected behaviour of P (design intent) | Main metrics |
|---|---|---|---|---|---|
| S01 | Normal operation | Good links, no failures, static world | Reference and sanity check; compare with B0 | Near-oracle coverage; low disagreement | Completion, completeness, overhead |
| S02 | Single discovery shared | One building placed so UAV A sees it first | Propagation of a single feature | Feature reaches 1-hop, then multi-hop peers; duplicate receipts change nothing | δ_f(β), delivery ratio |
| S03 | Multiple independent discoveries | 3 features discovered simultaneously by different UAVs | Concurrent updates and order independence | All replicas converge to the same state regardless of arrival order | D(t), δ_f |
| S04 | Environmental change | Scheduled at t = 900 s: building collapses (occupied → free/hazard); new hazard appears; obstacle cleared | Change tracking | Recency weighting lets new evidence override old; contested cells trigger verify tasks | Change-reflection delay, accuracy |
| S05 | One UAV loses comms but continues | UAV k radio off for 300 s; it keeps flying its task | Local autonomy; suspicion when k was *expected* to be reachable vs not | k continues and stores deltas; others mark k UNREACHABLE (not failed) where reachability is low; on return, anti-entropy syncs | False-suspicion rate, sync time, duplication |
| S06 | Partial partition | Swarm split 7/3 by a scripted link cut for 600 s; some relays remain intermittent | Divergence and partial propagation | Each side keeps working; store-carry-forward through intermittent relays | D(t), δ_f |
| S07 | Complete partition | Two groups fully isolated for 600 s, then healed | Divergence, then reconciliation | Replicas diverge, then converge after healing; duplicate leases resolved deterministically | Sync time, duplication, D(t) |
| S08 | Physical UAV failure | One non-coordinator crashes at t = 800 s, inside the comm range of others | True failure detection and recovery | SUSPECTED-FAILED after probes; leases released; its sector marked unverified and re-surveyed | Detection latency, task recovery time, completeness |
| S09 | Leader failure | The current coordinator crashes at t = 800 s | Succession | New coordinator with a higher epoch; unique coordinator recognized in the component | Leadership recovery time |
| S10 | Multiple failures | 3 of 10 crash, staggered at t ∈ {600, 900, 1200} s | Repeated reorganization | Successive recovery; graceful degradation of completion | Completion vs number of failures |
| S11 | New UAV joins | 1 UAV launched at t = 1200 s | Join and state transfer | Gets full state from a neighbour; usable map immediately; receives leases | Join bytes, time-to-usable-map |
| S12 | Rejoin after long disconnection | A UAV isolated for 900 s with many unshared observations, then rejoins | Reconnection sync and refutation of suspicion | Higher incarnation refutes suspicion; its unique observations merge into all replicas | Sync time, recovered unique cells |
| S13 | Conflicting / outdated observations | Two groups observe the same region before and after a change while partitioned | Conflict resolution | After merge, newer evidence dominates; contested cells generate verify tasks; provenance kept | Accuracy on changed cells, verify tasks |
| S14 | Combined comms and physical failures | Partition (S07) plus one real crash and one radio-only outage during the partition | Distinguishing disconnection from failure under stress | Crashed UAV eventually SUSPECTED-FAILED; radio-only UAV kept UNREACHABLE, then refuted on return | False-suspicion rate, completion, duplication |

**Scaling and link sweeps (RQ5):** S01, S07 and S14 at N ∈ {5, 10, 20} × link quality ∈ {good, moderate, poor} (Gilbert–Elliott parameter sets fixed in Stage 3).

**Realism limits stated up front:**
- No resilience claim beyond the tested failure counts.
- Observations a UAV never shared before crashing are lost by construction.
- Results hold under assumptions A1–A8.

---

## 3. How each metric is measured

| Metric | Computation in simulator | Logged |
|---|---|---|
| Mission completion | Victims with confirmed class in ≥ 1 alive replica ÷ total victims at T; also time to 95% coverage | per run |
| Completeness | Mean over alive i of the fraction of non-restricted cells with ‖L_c^i‖ > θ_known | every 10 s |
| Accuracy | On known cells, (occ, class) vs ground truth *at that time* (so changes count) | every 10 s |
| Replica disagreement D(t) | Mean over alive pairs of the fraction of cells with differing (occ, class) estimates | every 10 s |
| Propagation delay δ_f(β) | Ground-truth first-observation time vs first time a fraction β of alive replicas classify f correctly | per feature |
| Sync time | Partition heal time → D(t) between former groups < ε = 0.01 | per heal event |
| Change-reflection delay | Change event → ≥ 90% of alive replicas correct on changed cells | per change event |
| Detection latency / false suspicion | Crash time → first SUSPECTED-FAILED by any alive UAV; SUSPECTED-FAILED events on alive UAVs ÷ all SUSPECTED-FAILED events | per event |
| Task recovery time | Crash time → all leases of the failed UAV re-held by alive UAVs | per event |
| Leadership recovery time | Coordinator crash → single coordinator agreed by all members of the surviving component | per event |
| Duplication rate | Σ time two or more alive UAVs execute the same task ÷ total task time; duplicated coverage cells | per run |
| Overhead | Bytes and messages per UAV per second, split into map / task / heartbeat / election | per run |
| Delivery ratio | Delivered deltas ÷ deltas with ≥ 1 reachable recipient | per run |
| Compute cost | Wall-clock time per simulated second per UAV | per run |

Recovery times can be **censored**: there may be no recovery by T. These are reported with Kaplan–Meier estimates rather than dropped [Kaplan & Meier 1958].

---

## 4. Baselines and ablations (experimental protocol)

### 4.1 Configurations

| ID | Map merge | Failure handling | Recovery | Coordination | Why needed |
|---|---|---|---|---|---|
| B0 | Global ground-truth-fed map | Omniscient | Instant | Centralized auction | Upper bound; shows the cost of decentralization |
| B1 | LWW by timestamp | Fixed timeout = crash | None | Decentralized self-assignment | "Decentralized without self-healing" |
| B2 | Additive log-odds | Fixed timeout = crash | Task reassignment | Same coordinator auction as P | Naive fusion; double-counting effect |
| B3 | Proposed CRDT | Proposed suspicion | **Task-only** (no unverified marking, no re-survey) | As P | Isolates map-aware recovery (H3) |
| **P** | Proposed CRDT + recency | Context-aware accrual + probes | Map-aware | Lease auction + partition-local coordinator | Full framework |
| P+π | As P | As P | As P | Learned task selection | H4 (only if Stage 4b passes its gate) |

### 4.2 Ablations (each removes one component from P)

| Ablation | What is removed | Isolates | Scenarios |
|---|---|---|---|
| −AE | Anti-entropy on contact (gossip push only) | Reconnection sync | S06, S07, S12 |
| −REC | Recency weighting (w ≡ 1) | Change handling | S04, S13 |
| −ρ | Reachability term (plain φ-accrual) | Disconnection vs failure | S05, S14 |
| −PROBE | Indirect probing | False suspicion within a component | S05, S08, S14 |
| −COORD | Coordinator (pure self-assignment) | Value of leadership | S07, S09, S10 |
| −PRIO | Priority ordering of deltas | Critical-information latency under budget | S06, S07 (poor links) |
| −MAPREC | Map-aware recovery (= B3) | Knowledge recovery | S08, S10, S14 |

### 4.3 Run matrix and budget estimate

| Block | Scenarios × configs × seeds | Runs |
|---|---|---|
| Main comparison | 14 × 5 (B0, B1, B2, B3, P) × 30 | 2100 |
| Ablations | 6 non-B3 ablations × their 2–3 scenarios × 30 | ≈ 450 |
| Scaling / link sweep | 3 scenarios × 3 N × 3 link levels × 2 (B2, P) × 30 | 1620 |
| Sensitivity sweep (§6.2) | ~40 parameter points × S07/S14 × 10 seeds | ≈ 800 |
| **Total** | | **≈ 5000** |

**Estimate:** assuming ~60 s per run at N = 10 (to be measured in Stage 1), that is ≈ 80 CPU-hours, or ≈ 14 h wall-clock on 6 cores. N = 20 runs cost more. If the measured runtime is higher, seeds are reduced only after a power check (§6.1).

---

## 5. Implementation roadmap

Each stage ends with a **gate**: its tests must pass before the next stage starts.

| Stage | Required implementation | Expected behaviour | Depends on | Test cases | Measurable outcome | Est. effort |
|---|---|---|---|---|---|---|
| **1. Agents and local knowledge** | `world`, `sensing`, `crdt_map` (local update + fused read), kinematics/energy (ported), single-UAV planner, metrics skeleton | Each UAV builds only its own replica from noisy sensing | — | Sensor-model statistics match p_d/p_fa (χ² test); log-odds clamping; hand-checked 5×5 world; deterministic replay per seed | Single-UAV completeness/accuracy curves; runtime per step | 2 weeks |
| **2. Collaborative mapping and exchange** | Merge ⊔, deltas, version vectors, gossip, anti-entropy; full connectivity first | Discoveries propagate; replicas converge | 1 | **Property tests:** random merges are commutative, associative and idempotent; replicas equal after the same delta set in random orders and with duplicates; no double counting (vs B2); S02, S03 | δ_f, D(t) → 0 under full connectivity | 2 weeks |
| **3. Intermittent comms and partitions** | `comms`: range, q(d), Gilbert–Elliott, scripted partitions, byte budget, priority queue, store-carry-forward | Divergence during partitions, convergence after healing | 2 | Link-process statistics match parameters; components computed correctly; budget never exceeded; S06, S07 map-only | Sync time; D(t) under partitions | 2 weeks |
| **4a. Coordination and task allocation** | `tasks` (deterministic IDs, lease CRDT), `allocation` (coordinator auction, self-assignment, B0), heuristic planner | No permanent controller; partitions work independently; duplicates resolved on merge | 3 | Lease-merge determinism; two partitions leasing the same task converge to one owner; B0 ≥ P on S01; S01 | Completion; duplication | 2 weeks |
| **4b. Learned policy (gated)** | PettingZoo wrapper; parameter-shared IPPO (small CNN on 15×15 crop, ~50k parameters); training with randomized links and failures, on seeds disjoint from evaluation | Policy picks among the task generator's candidates | 4a | Wrapper API test; reward bookkeeping; deterministic eval | **Gate:** coverage AUC ≥ heuristic on 10 validation seeds within ≤ 48 CPU-h. Otherwise report as negative and stop | 3 weeks (time-boxed) |
| **5. Failure detection, succession, redistribution** | `membership` (heartbeats, incarnations, φ-accrual, reachability, probes), `election`, recovery manager, map-aware recovery | Silence ≠ crash; leases released for suspected failures only; coordinator replaced | 4a | Accrual calibration on synthetic inter-arrivals; reachability unit tests; single-coordinator invariant after election; S05, S08, S09, S10 | Detection latency, false suspicion, recovery times | 3 weeks |
| **6. Reconnection and synchronization (full)** | Rejoin with incarnation refutation, join state transfer, coordinator merge, contested-cell verify tasks | Rejoining and joining UAVs integrate; conflicts become tasks | 5 | S11, S12, S13; invariant: after healing and enough contact, all replicas equal | Sync time, join cost, accuracy on changed cells | 2 weeks |
| **7. Experiments and analysis** | Batch runner, sensitivity sweep, main/ablation/scaling blocks, statistics, figures | — | 1–6 (and 4b if passed) | Pilot run (10 seeds) → power check; spot-check logs; re-run 5% of runs for determinism | Filled result tables (§7) | 4 weeks |

**Total ≈ 22 weeks**, including the time-boxed Stage 4b. Writing (Phase D) runs alongside from Stage 3 onward, starting with the literature review.

---

## 6. Experimental protocol and statistics

### 6.1 Seeds, pairing, power

- **Common random numbers:** for a given seed, every configuration sees the same world, link process and failure schedule, so comparisons are *paired*.
- **Disjoint seed ranges:** training/tuning seeds 1000–1999, sensitivity 2000–2999, evaluation 5000–5999. Tuning never touches evaluation seeds.
- **Pilot:** 10 seeds on S07 and S14. The paired standard deviation of the primary metrics sets the seed count needed to detect a practically relevant difference (pre-registered below) at α = 0.05 and power 0.8. The count is capped at 50 and floored at 30.

### 6.2 Parameter setting (D-11)

- A one-at-a-time and small-grid sweep over λ, θ_F, lease length L, ℓ_max and byte budget, on sensitivity seeds only.
- The chosen values are then **frozen** before evaluation runs.
- The sweep is reported in full, so readers can see how sensitive the method is.

### 6.3 Pre-registered comparisons and thresholds (set before running)

| Hypothesis | Comparison | Primary metric | Practically relevant difference |
|---|---|---|---|
| H1 | P vs B1, B2 (S04, S06, S07, S13) | D(t) AUC after heal; accuracy on changed cells | 20% relative reduction in D-AUC; +5 percentage points accuracy |
| H2 | P vs −ρ and B2 (S05, S14) | False-suspicion rate; detection latency | ≥ 50% fewer false suspicions with ≤ 30 s added latency |
| H3 | P vs B3 (S08, S10, S14) | Completion; completeness at T | +5 percentage points |
| H4 | P+π vs P (S01, S07, S14) | Coverage-time AUC; duplicated coverage | Non-inferiority margin of 2% on AUC |
| H5 | P across N (S01, S07, S14) | Bytes/UAV/s vs N | Fitted log–log slope < 1 |

### 6.4 Statistical tests

- **Paired comparisons:** Wilcoxon signed-rank test [Wilcoxon 1945] with Holm correction across the comparison family [Holm 1979].
- **Reporting:** median, IQR and bootstrap 95% CIs, plus the matched-pairs rank-biserial effect size.
- **Censored recovery times:** Kaplan–Meier curves with log-rank tests.
- **Learned policy:** results across training seeds (≥ 5 policy seeds) reported with IQM and bootstrap CIs [Agarwal et al. 2021].
- **Failed hypotheses are reported as failed.** No post-hoc metric switching.

### 6.5 Verification vs validation

- **Verification** (is the code correct?): the unit, property and invariant tests listed per stage; deterministic replay; a hand-checked small world.
- **Validation** (is the model credible?):
  - link-model parameters set within ranges reported in the FANET literature, with sources cited in Phase D;
  - B0 bound sanity checks;
  - qualitative comparison with the behaviours reported by L12, L22 and L45.
- No claim of real-world performance.

---

## 7. Result table templates (to be filled in Stage 7, currently empty)

**Table R1 — Main comparison (median [95% CI], 30+ paired seeds)**

| Scenario | Metric | B0 | B1 | B2 | B3 | P |
|---|---|---|---|---|---|---|
| S01 | Completion | *pending* | *pending* | *pending* | *pending* | *pending* |
| S07 | Sync time (s) | *pending* | … | … | … | … |
| S14 | False suspicion | *pending* | … | … | … | … |
| … | … | | | | | |

**Table R2 — Ablations (Δ vs P, median [95% CI])** · **Table R3 — Scaling (bytes/UAV/s by N and link level)** · **Figure set:** D(t) around partition and heal; Kaplan–Meier recovery curves; change-reflection CDFs; overhead vs N.

---

## 8. Threats to validity (summary; expanded in the paper)

- **Internal:**
  - The simulator implements both the proposal and the baselines, which risks implementation bias. Mitigation: shared code paths and switches, plus published code.
  - Parameter tuning could leak into evaluation. Mitigation: disjoint seeds and frozen parameters.
- **Construct:** replica disagreement measures consistency, not usefulness. It is therefore always paired with accuracy and completion.
- **External:**
  - Assumptions A1–A8 limit generality: a known global frame, a kinematic model, an abstract link layer and synthetic worlds.
  - Byzantine faults are not covered.
- **Conclusion:** multiple comparisons are handled with Holm correction; censoring with Kaplan–Meier.

## 9. Open items requiring your input

None blocking. Two notes:
1. Stage 1 needs NumPy, NetworkX, SciPy and Matplotlib installed in a project virtualenv. I'll create it when Stage 1 starts.
2. The roadmap assumes about 22 weeks of implementation and experiments. If your submission deadline is earlier, tell me the date and I'll cut scope. The first candidates to cut are Stage 4b and the N = 20 sweep.

## 10. Scope-control check

- **Pillar 1:** Stages 1–3 and 6; S02–S04, S06, S07, S12, S13. ✅
- **Pillar 2:** Stages 3–4a; S05–S07; partitions explicitly modelled. ✅
- **Pillar 3:** Stages 5–6; S08–S12, S14. ✅
- Tools are minimal: no ns-3, Gazebo, cloud or excluded technologies. ✅
- No results fabricated. All result tables are marked *pending*. ✅
