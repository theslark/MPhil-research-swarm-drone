# Step 4: Selection of Algorithms, Communication Mechanisms and Coordination Protocols

**Project:** Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity and Ambiguous Failures
**Date:** 2026-11-22
**Builds on:** Step 3 scope (`03_Step3_Title_and_Scope/Step3_Title_and_Scope.md`). Reference IDs `[Rxx]` refer to `02_Step2_Literature/Reference_Verification_Table.csv`; R73–R78 were added and verified for this step.

This step chooses one approach per component (M1–M7 from Step 3, §3.5) and justifies each choice against the alternatives. Exact equations, data structures and pseudocode follow in Step 5.

---

## 0. Selection criteria

Each candidate is judged on six criteria:

| Code | Criterion | Why it matters here |
|---|---|---|
| K1 | **Partition tolerance**: keeps working inside a minority partition | Core requirement (CAP choice: availability [R09]) |
| K2 | **Correct under wrong suspicion**: state stays consistent if a "failed" drone returns | Core gap (Step 2, L2–L4) |
| K3 | **Communication cost**: messages and bytes per contact | Limited links; energy |
| K4 | **Variable swarm size**: handles drones joining, leaving and crashing | Self-organisation requirement |
| K5 | **Implementation effort** for one MPhil student in 3–5 months | Feasibility |
| K6 | **Evidence base**: published, verifiable, comparable | Defensibility |

Ratings in the tables: ● good · ◐ partial · ○ poor.

---

## 1. Overall decision: hybrid allocation, not end-to-end MARL

| Option | Description | Assessment |
|---|---|---|
| A. End-to-end MARL | The policy picks tasks directly (as in TACC [R50], HIPPO-MAT [R52]) | ○ K2: no guarantee of conflict-free assignment; ○ K5: hard to train at M = 30–96 tasks; ◐ K6: already published, so little novelty |
| B. Pure rule-based | CBBA plus a fixed timeout for reassignment | ● K5, ● K6, but cannot learn *when* waiting beats taking over (RQ3 would have nothing to test) |
| **C. Hybrid (selected)** | CBBA-style allocation handles the normal case among drones that can talk to each other. A learned **takeover policy** decides only the hard question: *should I claim the task of a peer I can't hear from, wait, or carry on?* | ● K2: the ledger keeps state consistent whatever the policy does; ● K5: small action space; ● RQ3 is testable against a threshold rule; ◐ K6: "learning to override a classical allocator" is less common but builds on established parts |

**Why C:** the learning is limited to the decision the literature leaves open (Step 2, §6). Correctness never depends on the network: a bad policy can only waste effort, it cannot corrupt mission state. This also answers a likely examiner question: *"Why use RL at all?"* Because the best moment to take over depends on the communication range, the failure rate and the peer's last known plan, and no fixed rule fits all three. RQ3 tests exactly this claim.

---

## 2. M3: MARL algorithm for the takeover policy

### 2.1 Training paradigms
The master prompt asks for this distinction explicitly.

| Paradigm | Training | Execution | Algorithms |
|---|---|---|---|
| **Fully decentralized learning** | Each agent learns from its own experience; at most it exchanges parameters with neighbours | Decentralized | IQL [R75], IPPO [R76], networked actor-critic [R77] |
| **CTDE** (centralized training, decentralized execution) | A centralized critic or mixer sees the global state *during training only* | Decentralized: each drone runs its own actor on local observations | VDN [R63], QMIX [R61], MADDPG [R64], MAPPO [R62], MAAC [R78] |

**Execution is decentralized in both paradigms.** CTDE needs a global view only in the simulator, which we have. Learning *during flight* (fully decentralized, online) is out of scope (Step 3, §3.6). So CTDE is allowed and is the stronger choice.

### 2.2 Comparison

| Algorithm | Type | Variable N (K4) | Training stability | Fits our action space | Effort (K5) | Verdict |
|---|---|---|---|---|---|---|
| IQL [R75] / independent DQN | Decentralized, value-based | ● | ○ non-stationary | ● discrete | ● | Too weak; ablation only if time allows |
| IPPO [R76] | Decentralized, policy gradient | ● | ◐ surprisingly strong in benchmarks [R76] | ● | ● | **Ablation**: tests whether the central critic matters |
| Networked actor-critic [R77] | Fully decentralized with consensus | ◐ | ◐ | ● | ○ | Out of scope (online learning) |
| VDN [R63] | CTDE, additive value | ◐ sum over agents | ◐ | ● | ● | Not chosen: additivity cannot express "exactly one drone should take over" |
| QMIX [R61] | CTDE, monotonic mixer | ○ mixer sized for fixed N | ◐ | ● | ◐ | Not chosen: fixed-N mixer conflicts with join/leave and crashes |
| MADDPG [R64] | CTDE, deterministic policy | ○ critic input grows with N | ○ | ○ continuous actions | ◐ | Not chosen |
| MAAC [R78] | CTDE, attention critic | ● | ◐ | ● | ◐ | Not chosen as the algorithm, but its **attention idea** is reused in the encoder |
| **MAPPO [R62]** | CTDE, PPO with centralized value function | ● with parameter sharing + attention | ● strong cooperative benchmark results [R62]; already used under attrition [R53] | ● discrete with action masking | ● | **Selected** |

### 2.3 Selected configuration (to be specified in Step 5)
- **Algorithm:** MAPPO with **shared actor parameters** across drones. One policy works for any N [R53].
- **Actor input (local only):** own state; K nearest *candidate* tasks from the local ledger, with features such as distance, owner, owner's suspicion level, time since the owner was last heard, owner's planned arrival time, and number of known claimants; plus visible neighbours. Encoded with **attention over sets**, which makes it independent of order and size [R78].
- **Critic input (training only):** global simulator state, **including ground truth about which drones have really crashed**. This asymmetric (privileged) critic helps the actor learn to judge from evidence. It is allowed because the critic is discarded at execution.
- **Actions** (discrete, masked), at each decision epoch:
  `CONTINUE` (follow the current allocator plan) · `CLAIM(k)` (take over orphaned task k from the top-K list) · `HOLD` (stay on the current task but delay any takeover).
  Allocation among drones in contact stays with the allocator (M4).
- **Reward (team):** `+1` per task completed; `−λ` per unit of duplicated service time; `−μ` per unit of energy. **λ is swept** to trace the recovery-vs-duplicate Pareto front (RQ1, RQ3).
- **Generalisation:** train with N ∈ {6, 10, 16} and randomised failure and partition schedules; evaluate on unseen seeds and on N ∈ {24, 32}.
- **Compute (estimate, to be confirmed in Phase 2):** actor and critic each under 200k parameters; 10–30 M environment steps using vectorised CPU environments. Roughly one to a few days on one workstation GPU. To be confirmed by a pilot run.

---

## 3. M4: Base task allocator

| Algorithm | K1 | K2 | K3 | K4 | K5 | K6 | Note |
|---|---|---|---|---|---|---|---|
| Centralized Hungarian / auction | ○ | — | ● | ● | ● | ● | Oracle **baseline** only |
| CBBA [R02] | ◐ needs synchronous rounds | ◐ | ◐ | ● | ● | ● | Convergence guarantees |
| **ACBBA-style asynchronous CBBA [R03]** | ● works with whatever messages arrive | ◐ | ◐ | ● | ● | ● | **Selected** |
| Performance Impact (PI) [R23, R36] | ◐ | ◐ | ◐ | ● | ◐ | ● | Basis of CC-OPI |
| CC-OPI [R66] | ● islands | ◐ completion only | ○ full-state gossip | ● | ◐ | ◐ preprint | **Baseline** |
| AC-DMTA [R68] | ◐ | ◐ | ● | ● | ○ | ● | Interesting, but complex |
| Market / reverse auction (IRDS) [R67] | ○ global market | ○ | ● | ● | ● | ◐ | Not chosen |

**Selected:** an **event-driven asynchronous CBBA** that runs within each connected group, with these changes:
1. Bundles are rebuilt on topology events (contact gained or lost) and ledger events (completion, claim, suspicion change), similar in spirit to CC-OPI's event-driven replanning [R66].
2. Tasks marked complete in the ledger are excluded. Tasks owned by a *suspected* peer are passed to the takeover policy (M3), not bid on automatically.
3. Conflicts between groups are not handled by CBBA. They are handled by the ledger merge (M2).

Reasons: CBBA/ACBBA is the most cited decentralized baseline and has convergence guarantees [R02, R03]. Its main weakness, the cost of synchronous rounds, is avoided by the asynchronous rules. Using CBBA as the base also makes the CBBA baseline a clean ablation: the same allocator without the ledger, suspicion or learned takeover.

---

## 4. M1: Failure detection (suspicion estimator)

| Approach | How it works | K1 | K2 | K3 | Verdict |
|---|---|---|---|---|---|
| Fixed heartbeat timeout | Declare failed after T seconds of silence | ● | ○ binary; long partitions cause false failures | ● | **Baseline / ablation** |
| SWIM [R08] | Random direct and indirect probing | ○ probes cannot cross partitions | ◐ | ● | Not chosen |
| Chandra–Toueg classes [R06] | Theoretical | — | — | — | Used to *frame* the problem, not implemented |
| Gossip-style heartbeats [R74] | Heartbeat counters spread by gossip; max-merge | ● evidence crosses partitions through carriers | ◐ | ● | **Selected as the evidence channel** |
| Phi-accrual [R07] | Continuous suspicion from the distribution of gaps between heartbeats | ● | ● graded | ● | **Selected as the suspicion function, adapted** |

**Selected: gossip-carried heartbeat evidence + adapted accrual suspicion.**
- **Evidence:** each drone keeps, for every peer *j*, the freshest *evidence of life* it has seen: (heartbeat counter, timestamp, position, plan version). Evidence spreads by gossip and is merged by taking the maximum counter. This is itself a CRDT, so it merges correctly [R74, R10].
- **Suspicion:** φ_ij = −log₁₀ P(gap ≥ current silence), as in phi-accrual [R07]. One change: the gap distribution is the **empirical distribution of evidence gaps under partitions**, estimated per scenario during training and refined online. Phi-accrual's assumption of near-regular heartbeats does not hold when heartbeats are carried by flying drones.
- **Plan-aware correction (proposed design idea):** the ledger holds peer *j*'s last published plan, so drone *i* can tell whether *j* *should* be within range now. Silence while *j* is expected to be nearby raises suspicion faster than silence while *j* is expected to be far away. This uses information the swarm already has to partly separate crash from disconnection. Evaluated as an ablation (with vs. without plan-awareness).
- Suspicion is **local and never merged**. Each drone forms its own view, as accrual detectors intend [R07]. What *is* merged is the evidence and the takeover claims (M2).

---

## 5. M2: Convergent mission ledger (core contribution)

### 5.1 Why CRDTs
| Approach | K1 | K2 | Verdict |
|---|---|---|---|
| Consensus / replicated log (Raft [R65]) | ○ minority partitions block | ● | Not chosen: violates K1 |
| Last-writer-wins on timestamps only | ● | ○ loses information; clock skew picks arbitrary winners | Ablation (naive merge) |
| Completion-only union merge (CC-OPI [R66]) | ● | ◐ ownership and suspicion conflicts left to allocator rules | **Baseline** (as CC-OPI) |
| **CRDT composition [R10, R11]** | ● available under partition | ● deterministic convergence | **Selected** |

CRDTs guarantee that replicas which have received the same updates hold the same state, whatever the delivery order [R11]. That is the property needed when updates arrive through unpredictable contacts.

### 5.2 Ledger components (types chosen; exact rules in Step 5)
| Ledger part | CRDT type | Content |
|---|---|---|
| Completed tasks | **G-Set** (grow-only set) | task id, completer, time |
| Evidence of life | **Map of max-registers** | per drone: heartbeat counter, timestamp, position, plan version |
| Task claims | **Map: task → (map: claimant → lattice)** | per (task, claimant): takeover epoch, progress (both only increase) |
| Membership | **2P-Set** (add-once, remove-once) | joined drones; drones that *announced* leaving. Crashes are **not** removed; suspicion handles them |

**Owner rule:** the current owner of task k is a *deterministic function* of the merged claim state, so every drone with the same ledger agrees. Candidate rules, compared as a design ablation in Step 6:

| Rule | Behaviour when a "failed" drone returns |
|---|---|
| R-A Epoch-first | The higher takeover epoch wins. The returning drone yields, even if it was nearly finished, so some work is wasted |
| R-B Progress-first | Most progress wins. But a crashed drone's frozen progress can block takeover forever unless progress expires |
| **R-C Epoch-first with reassertion (recommended)** | A takeover increments the epoch. A returning drone with progress above ρ may *reassert*, issuing epoch + 1. Ties are broken by drone id. Both epoch and progress only increase, so the rule stays monotone and converges |

### 5.3 Synchronisation
- **Delta-state anti-entropy** [R73]: on contact, drones first exchange a compact digest (version vector), then only the missing deltas. Guidec et al. found delta-state synchronisation needs the fewest messages in opportunistic networks [R12; from their summary].
- **Full-state fallback** after long separations, or when deltas have been garbage-collected.
- **Bounded size:** the ledger grows with M + N, not with time, because registers are overwritten, not appended.

---

## 6. M6: Communication mechanism

| Mechanism | Role | Selected? |
|---|---|---|
| Hop-by-hop MANET routing (AODV/OLSR) [R16, R17] | End-to-end paths | **No.** The ledger needs no end-to-end delivery; contact-to-contact merging spreads state over multiple hops anyway |
| Epidemic store-carry-forward [R13, R19] | Spreads every update to every node | **Yes, implicitly.** Anti-entropy of a CRDT *is* epidemic spreading, with duplicates absorbed by the merge |
| Spray-and-Wait [R14] | Limits copies | No. Ledger deltas are small and absorbed on duplicate delivery; the copy limit is not needed |
| **Contact-aware exchange scheduling** | On a new contact: (1) heartbeat + digest, (2) deltas for claims of *suspected* peers' tasks first, (3) the rest | **Yes.** Prioritises what matters most for self-healing within short contacts |
| Learning-based routing [R18] | — | Out of scope |

**Channel model (simulation):** disk range R_c; per-message Bernoulli loss rising with distance; optional Gilbert–Elliott bursts [R27]; per-contact bandwidth cap (bytes per second). MAC-layer contention is not modelled, a limitation shared with CC-OPI [R66].

---

## 7. M5: Leader / coordinator (ablation only)

| Approach | K1 | Verdict |
|---|---|---|
| Raft [R65] | ○ needs a majority; minority partitions get no leader | Not chosen. Its *term number* idea is reused as the epoch |
| Raft-inspired voting for UAVs [R46] | ◐ | Not chosen (designed for formation control) |
| Bully / highest-id | ◐ unstable when the swarm changes often | Not chosen |
| **Lease-based coordinator per group** | ● each connected group derives its coordinator deterministically from the ledger: the unsuspected drone with the most energy, ties broken by id, holding a lease for T_L | **Selected for the H4 ablation** |

With a coordinator, the group's allocation is solved by the coordinator (centralized auction within the group) instead of CBBA. H4 predicts no significant benefit. The scheme needs no voting, because the input (the ledger) is already shared.

---

## 8. M7: Dynamic membership
- **Join:** the new drone receives a full ledger snapshot on first contact, adds itself to the membership set, publishes a heartbeat, and enters the allocator. No global announcement is needed; it spreads by gossip.
- **Planned leave:** the drone releases its claims (progress kept), marks itself removed, and spreads this before departing.
- **Unplanned silence:** handled by suspicion (M1), never by removal. This keeps the "communication failure vs. physical failure" distinction the master prompt requires (§3D).

---

## 9. Summary of selections

| Component | Selected | Alternatives kept as baseline or ablation | Research question |
|---|---|---|---|
| Overall | Hybrid: classical allocator + learned takeover | End-to-end MARL (not used); rule-only (threshold) | RQ3 |
| M1 Suspicion | Gossip heartbeats [R74] + adapted accrual [R07] + plan-aware correction | Fixed timeout; no plan-awareness | RQ1 |
| M2 Ledger | CRDT composition [R10, R11], owner rule R-C, delta sync [R73] | Completion-only merge (CC-OPI); LWW; rules R-A, R-B | RQ2 |
| M3 Takeover | MAPPO [R62], shared actor, attention encoder [R78], privileged critic | Threshold rule; IPPO [R76] | RQ1, RQ3 |
| M4 Allocator | Event-driven asynchronous CBBA [R02, R03] | Centralized oracle; CBBA + timeout; CC-OPI [R66]; greedy | RQ4 |
| M5 Coordinator | Lease-based, per group (ablation only) | Leaderless (default) | RQ5 / H4 |
| M6 Communication | Delta anti-entropy over contacts, prioritised exchange | Full-state gossip (as CC-OPI) | RQ2 |
| M7 Membership | 2P-Set + snapshot join | — | Expansion/reduction scenarios |

## 10. Open design decisions for Step 5
1. Exact reassertion threshold ρ and lease duration T_L. Fix by a pilot sensitivity test.
2. How the empirical gap distribution for φ is estimated online. Options: per-scenario prior vs. per-peer running estimate. Recommend the per-peer estimate initialised from a prior.
3. Decision-epoch timing for the takeover policy. Recommend event-triggered (on any suspicion change of a task owner) plus a periodic fallback every 5 s.
4. Size K of the candidate-task list. Recommend K = 5 for action masking.
