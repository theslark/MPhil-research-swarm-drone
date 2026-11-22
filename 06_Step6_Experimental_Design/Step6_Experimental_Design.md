# Step 6: Experimental Design and Performance Evaluation Framework

**Project:** Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity and Ambiguous Failures
**Date:** 2026-11-22
**Builds on:** Step 3 (scope, RQs), Step 4 (selections), Step 5 (architecture, formulation). `[Rxx]` → `02_Step2_Literature/Reference_Verification_Table.csv` (R79–R82 added for this step).

**Status:** this is a *plan*. **No experiment has been run and no result exists.** Every number below is a chosen parameter or a design target, never a finding. Section 9 lists the results that must come from actual runs.

---

## 1. Default simulation parameters

All values are **assumptions chosen for plausibility**. The ones most likely to drive results are swept (§3) or tested for sensitivity (S11).

| Group | Parameter | Default | Sweep / sensitivity | Rationale |
|---|---|---|---|---|
| Area | Size | 2000 m × 1500 m | — | Wide enough that drones spread beyond communication range |
| Tasks | M sectors (grid) | 30 (6 × 5, ≈333 × 300 m each) | M = 3N in the N sweep | Step 3 §3.2 |
| | Service time s_k | Uniform 150–250 s | — | Lawnmower sweep of one sector at cruise speed with ~50 m camera swath (rough estimate) |
| | Weight w_k | 1 (unweighted); priority variant: 20% of tasks with w = 3 | Priority variant in S1, S9 | Weighted vs. unweighted completion |
| Drones | N | 10 | {6, 10, 16, 24, 32} | Step 3 §3.2 |
| | Cruise speed v | 10 m/s | — | Typical small quadrotor survey speed |
| | Energy budget | 1800 s of flight-equivalent | — | Typical 25–30 min endurance; leaves ~40% spare capacity at default load |
| | Launch | All from one base at area edge, t = 0 | — | Search-and-rescue deployment |
| Time | Step Δt | 0.5 s | — | |
| | Mission horizon T_max | 1800 s | — | Equals endurance |
| Communication | Range R_c | 400 m | {200, 400, 800, ∞} | 400 m gives frequent natural partitions in this area |
| | Delivery model | q(d) = 0.95·(1 − (d/R_c)²) | Gilbert–Elliott variant: p_GB = 0.02, p_BG = 0.2, ℓ_G = 0.01, ℓ_B = 0.9 | Distance loss plus bursty loss [R27] |
| | Heartbeat period T_hb | 1 s | — | |
| | Per-link bandwidth | 50 kB/s | — | Abstract cap; no MAC contention (limitation) |
| | Clock skew ε | 0 s | {0, 0.5, 2} s (S11) | GNSS time assumption (Step 3 §3.2) |
| Failures | Crash fraction f | 0 | {0, 0.1, 0.2, 0.3} | Up to 30% loss |
| | Crash times | Uniform [0.1, 0.6]·T_nom (T_nom = fault-free makespan from S1) | — | Failures occur while tasks are in progress |
| Proposed | Reassertion threshold ρ̄ | 0.5 | Pilot | Step 5 §5 |
| | Plan-aware weight κ, margin β | κ tuned on validation seeds; β = 0.8 | κ = 0 ablation | H5 |
| | Candidate tasks K; decision fallback | 5; 5 s | — | Step 5 §5 |
| | Rendezvous period T_rv | 120 s | Pilot | Isolation policy |

**Workload sanity check (design target, not a result):** 30 tasks × ~200 s ≈ 6000 s of service, or about 600 s per drone at N = 10, plus travel. The fault-free makespan should be well below T_max, and 30% crashes should still leave enough capacity in principle. The pilot run in Phase P1 will confirm or recalibrate this.

---

## 2. Scenario matrix

Each scenario keeps the defaults of §1 unless stated. **"Blackout"** means a live drone keeps flying and working but cannot transmit or receive for T_s seconds, as if its radio were blocked by terrain or interference. Blackouts are how the experiments create the *ambiguous* case with known ground truth.

| ID | Master-prompt scenario | Injected condition | Precise definition |
|---|---|---|---|
| **S1** | Normal operation | None | R_c = ∞, no losses, no failures. Reference for efficiency and overhead |
| **S2** | Communication interruption | Blackouts | 20% of drones (random) each suffer one blackout of T_s ∈ {60, 180, 400} s starting at random times in [0.1, 0.5]·T_nom. **No crashes** → every takeover is a false takeover |
| **S3** | Network partition | Forced split | At t = 0.2·T_nom the swarm is split by a line through the area. No links cross it for T_p ∈ {120, 300, 600} s, whatever the distance (models a ridge or jamming) |
| **S4** | Individual drone failure | 1 crash | One random drone crashes at a random time (§1) |
| **S5** | Leader failure | Critical crash | Coordinator variant (A8): the current coordinator of the largest group crashes. Leaderless methods: the drone owning the most unfinished tasks crashes, so they face an equivalent "most critical node" loss |
| **S6** | Multiple failures | f = 0.3 | Three drones crash at independent random times |
| **S7** | Dynamic expansion | Join | Start with N = 7; 3 drones launch from base at t = 300 s and must join through ledger merge |
| **S8** | Dynamic reduction | Planned leave | 3 drones announce leaving at t = 300 s, release claims and return to base (distinct from crashes) |
| **S9** | Combined failure | Partition + crashes + blackouts | S3 split (T_p = 300 s) **and** f = 0.2 crashes, with at least one crash on the minority side during the split, **and** S2 blackouts on 10% of drones. This is the main ambiguity scenario |
| **S10** | (Added) Ambiguity stress | Matched crash vs. blackout | 4 events at the same random times in every seed: 2 crashes and 2 blackouts (T_s = 180 s), so crashed and silent-but-alive drones are directly comparable. Used for detector evaluation (H5) |
| **S11** | (Added) Clock-skew sensitivity | Skew | S9 with ε ∈ {0.5, 2} s |

**Randomisation per seed:** sector service times, which drones crash and when, blackout and partition timing, and channel randomness. **Common random numbers:** for a given seed, every method sees the identical world, failure schedule and channel realisation. Comparisons are therefore paired.

---

## 3. Factor sweeps (one factor at a time around S9 defaults)

| Sweep | Values | Scenarios | Purpose |
|---|---|---|---|
| Swarm size N | 6, 10, 16, 24, 32 (M = 3N) | S1, S9 | RQ5 scalability; MARL generalisation (trained on N ≤ 16) |
| Range R_c | 200, 400, 800, ∞ | S9 | RQ5; H3 (does learning help only under intermittency?) |
| Crash fraction f | 0, 0.1, 0.2, 0.3 | S9 | RQ5 |
| Loss model | Distance-Bernoulli, Gilbert–Elliott | S9 | Robustness |
| Takeover aggressiveness | CBBA timeout T_to ∈ {5, 10, 20, 40, 80, 160, 320, 640} s; threshold Φ ∈ {1,…,8}; MAPPO penalty λ ∈ {0, 0.25, 0.5, 1, 2, 4} | S2, S9, S10 | RQ1/RQ3 trade-off curves (Pareto fronts) |

A full factorial design (every combination) is avoided to keep compute feasible. Interactions are studied only where hypotheses need them (R_c × method for H3).

---

## 4. Methods compared

### 4.1 Main methods
| ID | Method | Failure handling | Notes |
|---|---|---|---|
| B0 | **Centralized oracle** | Instant, perfect knowledge of failures; global communication | Upper bound, not a competitor |
| B1 | **Greedy nearest-task** | Timeout T_to, then any open task is taken | Lower bound |
| B2 | **CBBA + timeout** [R02, R03] | Fixed timeout T_to; tasks of a silent peer become biddable | Standard decentralized baseline |
| B3a | **CC-OPI (as published)** [R66] | None for crashes (paper excludes them) | Re-implemented. Our tasks have no deadlines, so its deadline-driven emergency pool never fires; reported to show the effect of ignoring failures |
| B3b | **CC-OPI + timeout** | B3a plus the same timeout rule as B2 | **Fair adaptation** to the failure setting; main state-of-the-art comparison |
| P1 | **Proposed + threshold rule** | Ledger + accrual/plan-aware suspicion + threshold Φ | Step 5 §2.4 |
| P2 | **Proposed + MAPPO** | Ledger + suspicion + learned takeover | Step 5 §2.6 |

### 4.2 Ablations (on S2, S9, S10, using P1 unless noted)
| ID | Removed or replaced component | Tests |
|---|---|---|
| A1 | Ledger reduced to completion-only merge (as in CC-OPI) | Value of convergent ownership/suspicion state (RQ2) |
| A2 | Accrual suspicion → binary timeout | Value of graded suspicion |
| A3 | κ = 0 (no plan-aware term) | **H5** |
| A4 | Owner rule R-A (epoch-first, no reassertion) | Owner-rule design |
| A5 | Owner rule R-B (progress-first) | Owner-rule design |
| A6 | No prioritised exchange (first-in, first-out deltas) | Contact-aware scheduling |
| A7 | Full-state sync instead of delta sync | Communication overhead |
| A8 | With per-group lease coordinator | **H4** |
| A9 | P2 with IPPO instead of MAPPO | Centralised critic vs. independent learning |
| A10 | P2 without privileged critic (critic sees only pooled observations) | Value of ground-truth-informed training |

### 4.3 Fairness controls
1. **Same world:** identical kinematics, energy, channel and failure realisations per seed (common random numbers).
2. **Same allocator scoring:** B2, B3 and P1/P2 use the same time-discounted score (Step 5 §2.5).
3. **Equal tuning budget:** each method's key parameter (T_to, Φ, λ, κ) is tuned on a grid of at most 8 values on **validation seeds 1001–1010**, never on evaluation seeds. Each method is reported at its best validation setting *and* as a full trade-off curve.
4. **Oracle labelled as a bound**, never as a competitor.
5. **Baseline fidelity:** B3a must reproduce CC-OPI's reported ~0.80 completion in its own published setting (±5 points) before use (Step 5 P4 exit criterion).
6. **MARL compute disclosed:** P2's training cost is reported next to its results.

### 4.4 MARL training protocol (P2)
- **One λ-conditioned policy:** λ is sampled per training episode and given to the actor and critic as an input. A single training run then covers the whole trade-off curve, replacing one training run per λ value from Step 5 §2.6. Cost drops about six-fold.
- **Training distribution:** N ∈ {6, 10, 16}; R_c ∈ {200, 400, 800}; f ∈ [0, 0.3]; random blackouts and partitions; training seeds 0–999.
- **Training seeds:** 5 independent runs; 3 if the compute pilot shows more is infeasible.
- **Evaluation:** every trained policy is run on the 30 evaluation seeds (2001–2030) of each scenario.
- **Generalisation tests:** N ∈ {24, 32}, never seen in training.

---

## 5. Metrics and formulas

**Notation:**
- 𝟙_ik(t) = 1 if drone i is *servicing* task k at time t (ground truth);
- S_k = Σ_i ∫₀^{T_max} 𝟙_ik(t) dt, the total service time spent on task k;
- 𝒦_done = the set of tasks completed by T_max;
- t_k^done = completion time of task k;
- 𝒩_c = the set of drones that crash, each with crash time t_j^c.

### 5.1 Mission effectiveness
| Metric | Formula | Direction |
|---|---|---|
| **Mission completion rate** | MCR = Σ_{k∈𝒦_done} w_k / Σ_{k∈𝒦} w_k | ↑ |
| **Mission completion time** | T_mc = max_{k∈𝒦_done} t_k^done if MCR = 1; otherwise censored at T_max | ↓ |
| **Coverage AUC** | AUC = (1/T_max) ∫₀^{T_max} MCR(t) dt, where MCR(t) counts tasks done by t | ↑ |
| **Allocation efficiency** | AE = S(achieved) / S(oracle B0), using the time-discounted score of Step 5 §2.5 | ↑ (≤ 1 expected) |

### 5.2 Self-healing: the core trade-off
| Metric | Formula | Direction |
|---|---|---|
| **Duplicated work ratio** | DWR = Σ_{k∈𝒦_done} (S_k − s_k) / Σ_{k∈𝒦} s_k | ↓ |
| **Wasted distance ratio** (from [R66]) | WDR = Σ_i (distance i flew toward tasks it neither serviced nor completed) / Σ_i (total distance of i) | ↓ |
| **Task recovery time** (claim latency) | For each *orphaned* task (k, j): its owner j crashed at t_j^c with k unfinished. τ_k^cl = (first claim time by another alive drone) − t_j^c | ↓ |
| **Service resumption time** | τ_k^rs = (first service by another drone) − t_j^c | ↓ |
| **Unrecovered fraction** | UF = (orphaned tasks never claimed before T_max) / (all orphaned tasks) | ↓ |
| **False takeover rate** | FTR = (takeover claims made while the previous owner was alive) / (all takeover claims) | ↓ |
| **False takeover cost** | FTC = total service time + travel spent on false takeovers, as a fraction of Σ s_k | ↓ |
| **Detector discrimination** | AUROC of φ̃_ij(t), computed over samples (i, j, t) where j has been silent to i for ≥ 3·T_hb, labelled crashed vs. alive (S10) | ↑ |
| **Trade-off quality** | Hypervolume HV of the method's (median τ^cl, DWR) front, normalised to [0,1]², relative to the reference point (T_max, 1) | ↑ |

**Censoring:** recovery times are *censored* when a task is never recovered before T_max. Averaging only recovered tasks would bias the result, so recovery times are analysed with the **Kaplan–Meier estimator** [R79]. Reported: median and **restricted mean up to T_max**, with UF alongside.

### 5.3 Consistency (shared ledger)
| Metric | Formula | Direction |
|---|---|---|
| **Owner divergence** | Div(t) = fraction of (alive drone pair in the same group, task) where the two drones' owner views o_i(k) and o_j(k) differ | ↓ |
| **Time to consistency** | For each partition-merge event at t_m: TTC = min{t ≥ t_m : all replicas in the merged group have identical done and owner projections} − t_m | ↓ |

### 5.4 Network and communication
| Metric | Formula | Direction |
|---|---|---|
| **Packet delivery ratio** | PDR = messages received / messages sent to in-range neighbours | ↑ |
| **Update dissemination latency** (end-to-end latency for a store-carry-forward system) | For each ledger update u created at t_u: L_u = mean over alive drones j of (t_{u,j}^arr − t_u). Report mean and 95th percentile; undelivered updates censored at T_max | ↓ |
| **Network connectivity** | Mean component count C̄ = (1/T) Σ_t c(t); pairwise connectivity PC = (1/T) Σ_t (alive pairs in the same component) / (all alive pairs) | Descriptive |
| **Communication overhead** | Messages per completed task; bytes per completed task; bytes per drone per second | ↓ |

### 5.5 Energy, autonomy, leadership, scalability
| Metric | Formula | Direction |
|---|---|---|
| **Energy per completed task** | E_task = Σ_i (E₀ − e_i(T_end)) / \|𝒦_done\| | ↓ |
| **Autonomy during disconnection** | For each isolation episode (drone i with no neighbour for ≥ 30 s): AI = (tasks i completes during the episode) / (unfinished tasks i owned at episode start, capped by what is achievable in the episode length); plus idle-time fraction | ↑ |
| **Leader recovery time** (A8 only) | LRT = time from coordinator crash until all members of its group hold a valid lease from a new coordinator | ↓ |
| **Decision computation time** | Wall-clock ms per agent decision (allocator + policy) on reference hardware | Reported vs. N |
| **Scalability** | All metrics as functions of N (§3) | Trend |

---

## 6. Hypotheses, tests and success criteria

| H | Statement (from Steps 3 and 5) | Scenarios | Metric | Test | Supported if |
|---|---|---|---|---|---|
| **H1** | When failures occur, the proposed method completes more of the mission than the decentralized baselines, and costs little when there are none | S4, S6, S9 (superiority); S1, S3 (non-inferiority) | MCR, AUC | Paired Wilcoxon signed-rank [R81], Holm-corrected [R80]; non-inferiority margin δ = 2 percentage points (one-sided) | P1 or P2 > B2 and B3b in S4/S6/S9 (adjusted p < 0.05), **and** the lower CI bound of (P − B3a) > −δ in S1/S3 |
| **H2** | Recovery time and duplicated work trade off monotonically with takeover aggressiveness | S2, S9, S10 | median τ^cl, DWR, FTR vs. Φ (and T_to) | Spearman rank correlation across the sweep; bootstrap CI | ρ_S(Φ, τ^cl) > 0 and ρ_S(Φ, DWR) < 0, both CIs excluding 0 |
| **H3** | The learned policy gives a better trade-off than the threshold rule under intermittent connectivity, but not under full connectivity | S9 at R_c ∈ {200, 400}; R_c = ∞ | HV | Paired bootstrap on HV(P2) − HV(P1) per evaluation seed, across 5 training seeds | CI > 0 at R_c ≤ 400 **and** CI includes 0 at R_c = ∞ |
| **H4** | A per-group coordinator gives no significant benefit | S5, S9 | MCR, τ^cl, LRT, overhead | Equivalence test (TOST) on MCR with margin ±2 points | Equivalence shown. If rejected, report the direction |
| **H5** | Plan-aware suspicion reduces false suspicion without slowing detection | S10, S9 | AUROC; FTR at matched median τ^cl | Paired bootstrap test on AUROC (resampling seeds); FTR compared at the Φ giving equal median τ^cl | AUROC(κ > 0) > AUROC(κ = 0) with CI excluding 0, and lower FTR at matched τ^cl |
| RQ2 | (Design question) The ledger converges after partitions and wrong suspicions | S3, S9 | TTC, Div(t); A1 vs. P1 | Descriptive + Wilcoxon on DWR/FTC (A1 vs. P1) | TTC finite in all merge events with temporal connectivity; A1 shows higher DWR or FTC |

**Interpreting outcomes:** each hypothesis can fail, and a failure is reported as such. A failed H3 means "learning did not help", which is a valid finding (Step 3 §8). A failed H5 means the plan-aware term is dropped from the recommended design.

---

## 7. Statistical analysis plan

1. **Seeds:**
   - 30 evaluation seeds per configuration (2001–2030);
   - validation seeds 1001–1010 for tuning;
   - training seeds 0–999 for MARL.
   These three sets never overlap.
2. **Paired design:** common random numbers give paired samples per seed. Primary test: **Wilcoxon signed-rank** [R81], which assumes no normal distribution.
3. **Multiple comparisons:** **Holm–Bonferroni** [R80] within each hypothesis family (H1–H5 are separate families).
4. **Effect sizes:** matched-pairs rank-biserial correlation, plus the median paired difference with a **95% bootstrap CI** (10,000 resamples).
5. **Censored times:** Kaplan–Meier curves [R79], log-rank test between methods, restricted mean survival time up to T_max.
6. **MARL results:** report across training seeds using interquartile mean (IQM) and stratified bootstrap CIs, as recommended for RL [R82]. Never report a single best training run.
7. **Sample size:** 30 paired seeds give roughly 80% power to detect a standardised paired effect of about 0.55 at α = 0.05 (approximation from the paired t-test; Wilcoxon is nearly as efficient). If pilot runs show high variance, raise to 50 seeds for the affected scenarios. The decision is made and recorded **before** the main runs.
8. **Pre-registration (internal):** this document is frozen before main experiments. Any later change to metrics, hypotheses or tests is logged with a date and reason in a change log.

---

## 8. Compute budget (estimate, to be checked by pilot)

| Block | Configurations | Runs (× 30 seeds) |
|---|---|---|
| Main matrix: S1–S9 (with S2/S3 sub-values: 13 settings) × B0–B3b, P1, P2 (7 methods) | 91 | 2,730 |
| Sweeps: N (5) + R_c (4) + f (4) + loss (2) on S9; N also on S1 → about 20 settings × 7 methods | 140 | 4,200 |
| Trade-off sweeps: T_to (8) + Φ (8) + λ (6) on S2, S9, S10 | 66 | 1,980 |
| Ablations: A1–A10 on S2, S9, S10 | 30 | 900 |
| S10, S11 extras | ~20 | 600 |
| **Total simulation runs** | | **≈ 10,400** |

- **Simulation:** if one run takes ≤ 30 s on one CPU core (to be confirmed in P1), the total is ≈ 87 CPU-hours: about one day on a 4-core machine, or overnight on 8 cores.
- **MARL training:** 5 seeds × one λ-conditioned policy. Estimated 1–3 days each on one GPU workstation (Step 4 §2.3). That is up to about 2 weeks sequentially if the upper estimate holds, and the main compute risk. Mitigation: 3 seeds, or run in parallel if there are several GPUs.

---

## 9. Results that require experimental data (do not fill in before running)

The manuscript (Step 7) will contain these with **placeholders only**:

| Item | Content | Source runs |
|---|---|---|
| Table R1 | MCR, T_mc, DWR, median τ^cl, UF, FTR, bytes per task: all methods × S1–S9 (median [95% CI]) | Main matrix |
| Table R2 | Ablations A1–A10 vs. P1/P2 on S2, S9, S10 | Ablations |
| Table R3 | Hypothesis test summary H1–H5 (effect, CI, adjusted p, supported?) | All |
| Fig. F1 | Pareto fronts (median τ^cl vs. DWR) for B2, B3b, P1, P2 on S9 | Trade-off sweeps |
| Fig. F2 | Kaplan–Meier recovery curves per method (S6, S9) | Main matrix |
| Fig. F3 | MCR and overhead vs. N | N sweep |
| Fig. F4 | HV(P2) − HV(P1) vs. R_c (H3) | R_c sweep |
| Fig. F5 | ROC curves of φ̃ with κ > 0 vs. κ = 0 (H5) | S10 |
| Fig. F6 | Owner divergence over time around partition merges (P1 vs. A1) | S3, S9 |
| Fig. F7 | MAPPO training curves (IQM ± CI across training seeds) | Training |

---

## 10. Threats to validity

| Type | Threat | Mitigation |
|---|---|---|
| Internal | Implementation bugs in the simulator or baselines | Property-based tests for CRDT laws; hand-checked micro-scenarios; determinism checks (Step 5 §3.3) |
| Internal | Re-implementation of CC-OPI differs from the original | Reproduce its published result first; report the deviation |
| Internal | Unequal tuning effort favours the proposed method | Equal tuning budget on separate validation seeds; full trade-off curves reported |
| Construct | Duplicated work and recovery time may not capture operational value (e.g., time-critical victims) | Priority-weighted variant; coverage AUC; discussed as a limitation |
| Construct | Blackouts are a stylised model of real disconnection | Also natural partitions from limited range; Gilbert–Elliott bursts |
| External | Point-mass motion, disk communication, no MAC contention, no wind | Stated as scope limits. Optional ns-3 cross-check; physical simulation and hardware are future work |
| External | Results may depend on area size and task density | N and R_c sweeps; workload sanity check in pilot |
| Statistical | Multiple testing; small effects | Holm correction; effect sizes with CIs; power check from pilot |
| Statistical (RL) | Training-seed variance; cherry-picking | ≥ 3–5 training seeds; IQM and bootstrap CIs [R82]; all seeds reported |

---

## 11. Changes to earlier steps
- **MAPPO is trained as one λ-conditioned policy** (§4.4) instead of one policy per λ value (Step 5 §2.6). Same trade-off curve at about one sixth of the training cost.
- **B3 split into B3a (as published) and B3b (+ timeout)** for a fair comparison, since CC-OPI does not handle crashes.
- **Added scenarios S10 (matched crash vs. blackout) and S11 (clock skew).**
- **Added metrics:** false takeover rate and cost, detector AUROC, hypervolume, owner divergence, time to consistency.
