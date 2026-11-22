# Step 3: Refined Title and Exact Research Scope

**Project:** Research 02 (MPhil, Advanced Research Methodology)
**Date:** 2026-11-22
**Builds on:** `01_Step1_Feasibility/Step1_Feasibility_and_Scope.md`, `02_Step2_Literature/Step2_Literature_Review.md` (revision 2). Reference IDs `[Rxx]` refer to `02_Step2_Literature/Reference_Verification_Table.csv`.

---

## 1. Refined title

### Recommended
> **Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity and Ambiguous Failures**

Why this title:
- It keeps the original concepts (self-healing, decentralized, UAV swarms, intermittent connectivity), so the research still matches the original proposal.
- "Ambiguous failures" names the specific gap from Step 2: a silent drone may be crashed or merely disconnected. This separates the work from CC-OPI [R66] (partitions, no failures) and IRDS [R67] (failures, perfect communication).
- "Task allocation" fixes the object of study. The title does not promise a whole architecture, routing protocol or flight controller.
- MARL is left out of the title on purpose. Step 2 showed that MARL under attrition already exists [R53], so putting it in the title would overstate the novelty. It appears in the abstract and methods as the learned allocation policy.

### Alternatives considered
| Title | Why not chosen |
|---|---|
| An AI-Driven Self-Organizing and Self-Healing Architecture for Decentralized UAV Swarms under Intermittent Connectivity (original) | Too broad: implies novel architecture, routing, membership and leader election, which Step 2 showed are already published. |
| Failure-Aware, Partition-Tolerant Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity | Accurate, but "partition-tolerant" reads as jargon to aerospace reviewers, and it drops "self-healing". Keep as a backup for a distributed-systems venue. |
| ... A Multi-Agent Reinforcement Learning Approach | Overstates the MARL contribution (see above). |

**Short running title:** *Self-Healing UAV Task Allocation under Ambiguous Failures*

---

## 2. Problem statement (final)

UAV swarms used for search and rescue lose connectivity for two very different reasons: drones fly out of range, or drones crash. Recent decentralized allocators keep a partitioned swarm working and merge completed-task records when groups reconnect [R66]. Other methods reassign the tasks of a drone once its failure is known [R35, R67]. In a real swarm these situations look identical to the remaining drones: a peer has gone silent. No observer can reliably tell a crashed peer from a disconnected one [R05, R06].

Two kinds of mistake follow:
- **Reassign too early:** a live but disconnected drone is treated as failed. Its tasks are done twice, and its records conflict with the swarm's when it returns.
- **Reassign too late:** a crashed drone is treated as merely disconnected. Its tasks stay unserved and the mission is delayed.

Existing UAV task-allocation work neither detects failure under partitions nor measures this trade-off [R43 shows the general dilemma outside robotics]. This research designs and evaluates a decentralized allocation mechanism that:
1. estimates *suspicion* rather than a binary failed/alive verdict;
2. keeps task-ownership and suspicion records that converge correctly even after a wrong suspicion;
3. uses a learned policy to decide when to take over a suspected drone's tasks.

---

## 3. Exact research scope

### 3.1 Mission and task model
| Element | Definition | Rationale |
|---|---|---|
| Mission | Search-and-rescue area coverage | Accepted in Step 1; matches R30, R31, R66, R67 |
| Area | 2-D rectangle split into **M sectors**; each sector is one task | Clean coverage metrics |
| Task | Location, service time *s_k* (time to sweep the sector), optional priority *w_k* | Standard in R31, R66 |
| Task type (MRTA taxonomy [R01]) | **ST-SR-TA**: each drone does one task at a time, each task needs one drone, assignments are time-extended (a queue or bundle per drone) | Single-robot tasks keep "duplicate work" well defined |
| Task arrival | **Fixed task set**, known at mission start | Runtime task arrival is already handled by R66. Leaving it out isolates the failure effect |
| Completion | A task is complete when one drone has fully serviced it. Further service is **duplicate work** | Gives the core metric |

### 3.2 Agent model
| Element | Definition |
|---|---|
| Drones | N homogeneous quadrotors (identical capabilities) |
| Motion | Point-mass kinematics at constant cruise speed. No flight dynamics |
| Energy | Linear budget: flight time plus a fixed cost per transmitted message. A drone returns or lands when its budget runs out |
| Localization | Each drone knows its own position (GNSS assumed) |
| Clock | Clocks loosely synchronized via GNSS time, with bounded skew ε. This lets records carry timestamps; R66 makes a similar global-time assumption |
| Collision avoidance | Out of scope; handled by a lower-level controller (abstracted) |
| Swarm sizes | Main experiments **N = 10**, M = 30. Scalability sweep **N ∈ {6, 10, 16, 24, 32}** with M = 3N |

### 3.3 Communication model
| Element | Definition |
|---|---|
| Topology | Drone-to-drone links only, no infrastructure. Two drones are linked if their distance is at most the range **R_c** |
| Message loss | Distance-dependent Bernoulli loss, with an optional **Gilbert–Elliott** burst-loss mode [R27] |
| Partitions | (a) **Natural**: emerge from mobility under limited R_c. (b) **Forced**: scripted partition events, e.g., the swarm split into two groups for T_p seconds |
| Multi-hop | Store-carry-forward gossip within a connected group; no routing protocol research |
| Ground station | Used only by the centralized baseline, which assumes global communication |

### 3.4 Failure model
| Element | Definition |
|---|---|
| Failure type | **Crash-stop (fail-silent)**: a failed drone stops moving and stops transmitting permanently |
| Not modelled | Byzantine or malicious behaviour, sensor faults, partial degradation |
| Disconnection | A live drone can be silent for a long time (out of range or in another partition) and later reconnect |
| Ground truth | The simulator records each drone's true state (crashed or alive). Drones never see it; it is used only for metrics, e.g., false-suspicion rate |
| Fault injection | Failure times and identities drawn randomly per seed. 0–30% of the swarm fails, combined with partition events |

### 3.5 What the proposed mechanism includes
Components and their novelty status (detailed design in Steps 4–5):

| # | Component | Novelty claimed |
|---|---|---|
| M1 | **Suspicion estimator**: each drone keeps a continuous suspicion level for every peer, from its last direct or relayed evidence of life (heartbeats carried by gossip), adapted from phi-accrual [R07] | Yes (adaptation to partitioned swarms) |
| M2 | **Convergent mission ledger**: replicated records of task completion, task ownership and suspicion that merge correctly after partitions and wrong suspicions (CRDT-based [R10, R11]) | **Yes (core)** |
| M3 | **Takeover policy**: decides *when* a drone claims a suspected peer's task. Two versions: a threshold rule (analytical baseline) and a **MAPPO policy** (CTDE, shared parameters, attention encoder for variable N) [R62, R53] | Partial (MARL design) |
| M4 | **Underlying allocator**: CBBA-style bundle allocation within each connected group [R02, R03] | No (reused) |
| M5 | **Optional group coordinator**: a lease-based coordinator per partition, used only in the leader ablation [R46, R65] | No (ablation only) |
| M6 | **Store-carry-forward gossip** of ledger updates [R13, R19] | No (reused) |
| M7 | **Join/leave**: a new drone joins by merging the ledger. A drone leaving announces it, or is treated as a suspected failure | No |

### 3.6 Explicitly out of scope
- FANET routing protocol design, and learning-based routing [R18, R60]
- Physical flight simulation (Gazebo, PX4 SITL) and hardware experiments
- Network topology self-healing by repositioning drones [R39]
- Formation control, collision avoidance, path planning beyond straight-line travel
- Security, Byzantine faults, blockchain, quantum communication, cloud/Kubernetes orchestration
- Heterogeneous drones (possible future work)
- Online or fully decentralized learning in flight. Training is centralized, in simulation
- Runtime task arrival and target detection/recognition

### 3.7 Implementation scope
- **Simulator:** custom Python discrete-time simulator. The MARL environment uses the PettingZoo API; MAPPO is implemented in PyTorch.
- **Optional:** ns-3 cross-check of the channel model for one scenario. Only if time permits; not required for the thesis.
- **Reproducibility:** fixed seeds, configuration files per experiment, code released with the thesis.
- **Estimated effort:** 3–5 months of implementation and experiments (from Step 1).

---

## 4. Research objectives (refined, measurable)

| ID | Objective | Measurable outcome |
|---|---|---|
| O1 | Formalise the decentralized task-allocation problem under partitions and crash-stop failures, including ground-truth definitions of duplicated work and abandoned tasks | Formal problem definition and metric definitions (Step 6) |
| O2 | Design a suspicion estimator that works when evidence of life arrives only through intermittent, multi-hop gossip | False-suspicion rate and detection delay under the communication model of §3.3 |
| O3 | Design a convergent mission ledger for completion, ownership and suspicion state, and show it converges after partitions and wrong suspicions | Proof or argument of convergence; measured time to consistency after reconnection |
| O4 | Develop takeover policies (threshold rule and MAPPO) that balance recovery speed against duplicated work | Trade-off curve: task recovery time vs. duplicated work, swept over threshold or reward weighting |
| O5 | Evaluate the full mechanism against centralized, CBBA, CC-OPI and greedy baselines across the scenarios of Step 6, with ablations | Mission completion rate, completion time, duplicated work, wasted distance, message overhead, energy; statistical tests over ≥ 30 seeds |
| O6 | Assess scalability and sensitivity to swarm size, communication range and failure rate | Metrics as functions of N, R_c and failure fraction |

## 5. Research questions

| RQ | Question | Hypothesis | Objective | Method |
|---|---|---|---|---|
| RQ1 | When drones cannot tell a crashed peer from a disconnected one, what is the measurable trade-off between task recovery time and duplicated work in decentralized UAV task allocation? | H2: recovery time and duplicated work trade off monotonically as the suspicion threshold varies | O1, O2, O4 | Threshold sweep, Pareto curves |
| RQ2 | Can a convergent mission ledger keep mission state consistent across partitions and wrong suspicions, and at what communication cost? | (Design question) The ledger converges once groups reconnect; overhead grows at most linearly in M per contact | O3 | Analysis + time-to-consistency and message measurements |
| RQ3 | Does a learned (MAPPO) takeover policy give a better recovery/duplicate trade-off than a tuned threshold rule? | H3: MAPPO dominates the threshold rule's Pareto front under intermittent connectivity, but not under full connectivity | O4 | Pareto comparison, held-out seeds |
| RQ4 | How does the complete mechanism compare with centralized, CBBA-based and CC-OPI allocation when partitions and failures occur together? | H1: higher completion rate than all decentralized baselines when failures occur; within a small margin of CC-OPI when there are none | O5 | Scenario matrix (Step 6), ablations |
| RQ5 | How do performance and overhead change with swarm size, communication range and failure rate, and does a per-partition coordinator help? | H4: a per-partition coordinator gives no significant advantage over leaderless operation | O5, O6 | Parameter sweeps, leader ablation |

### Mapping to the original research questions (from the master prompt)
| Original RQ | Covered by |
|---|---|
| 1. Coordinating without continuous central control | RQ4 (decentralized vs. centralized baseline) |
| 2. Mission continuity during intermittent communication | RQ2, RQ4 |
| 3. Recovering from leader or individual drone failure | RQ1, RQ5 (leader ablation) |
| 4. Redistributing tasks intelligently | RQ1, RQ3 |
| 5. New drones joining without disruption | Dynamic-expansion scenario under RQ4 (M7 is not a novelty claim) |
| 6. Performance with swarm size and network conditions | RQ5 |

## 6. Expected contributions (conditional on results)

1. **Problem formalisation and metrics:** the first formal treatment, to our knowledge, of decentralized UAV task allocation under *combined* partitions and crash-stop failures, with ground-truth metrics for duplicated work and abandoned tasks.
2. **Convergent mission ledger:** a CRDT-based design that extends completion-only merging [R66] to ownership and suspicion state, with a convergence argument.
3. **Characterisation of the trade-off:** empirical Pareto fronts of recovery time vs. duplicated work, and how they change with communication range and failure rate.
4. **Learned takeover policy:** evidence on whether MAPPO improves on a tuned threshold rule. A negative result is also reported as a contribution.
5. **Reproducible simulation framework:** open-source simulator and scenario suite, including a re-implementation of the CC-OPI baseline.

The novelty claims in contributions 1–2 rest on the Step 2 search (Crossref, arXiv, web) and still need confirmation by the IEEE Xplore and Scopus searches listed in Step 2, Section 7.

## 7. Baselines (fixed now; details in Step 6)
| Baseline | Role |
|---|---|
| **Centralized oracle** (global communication, instant knowledge of failures, Hungarian/auction replanning) | Upper bound |
| **CBBA / ACBBA** [R02, R03], with timeout-based reassignment | Standard decentralized baseline |
| **CC-OPI** [R66], re-implemented from the paper | State of the art for partitioned swarms without failures |
| **Greedy nearest-task** | Lower bound |
| **Ablations** of the proposed mechanism: no ledger (completion-only merge), binary timeout instead of suspicion, threshold rule instead of MAPPO, with vs. without coordinator, no store-carry-forward | Contribution of each component |

## 8. Risks and mitigations
| Risk | Mitigation |
|---|---|
| CC-OPI has no public code, so a re-implementation may differ from the original | Re-implement from the paper's algorithm and equations; check it reproduces the reported ~0.80 completion rate in their setting before using it |
| MAPPO fails to beat the threshold rule | Report as a negative result (RQ3). Contributions 1–3 do not depend on MARL |
| A full-text check of HMP [R41] shows it already covers the ambiguity | Reposition the contribution as a generalisation from patrolling meetings to allocation over arbitrary contacts, and add HMP as a baseline |
| Scope creep back toward routing or physical simulation | §3.6 is binding; changes require an explicit decision |
| Clock-synchronization assumption is challenged | Use bounded skew ε, and include a sensitivity test with larger ε in Step 6 |

## 9. Decisions recorded (recommended defaults; change if needed)
1. Fixed task set (no runtime arrivals).
2. Crash-stop failures only.
3. Homogeneous drones.
4. GNSS-synchronized clocks with bounded skew.
5. Python simulator; ns-3 cross-check optional.
6. Title as in §1.
