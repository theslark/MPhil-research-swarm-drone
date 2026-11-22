# Step 1: Feasibility Analysis and Research Scope

**Project:** AI-driven self-organizing and self-healing architecture for decentralized UAV swarms under intermittent connectivity
**Date:** 2026-11-22
**Status:** Scope accepted by the researcher (2026-11-22). References listed here are unverified and are checked in Step 2.

---

## 1. Overall verdict

The concept is feasible as a simulation-based MPhil study, but not at its original breadth. The original proposal combines about nine components (MARL task allocation, learning-based routing, DTN, contact scheduling, failure detection, leader election, membership management, scalability and self-organisation), each of which is a research area in its own right. A paper that tries to contribute to all of them becomes an integration exercise with no clear contribution.

Decision: pick one core research problem and treat the other components as well-specified supporting machinery that is evaluated but not claimed as novel.

## 2. Technical challenges and conceptual tensions

### 2.1 "Decentralized" vs. "leader election"
- Raft-style consensus needs a majority quorum. During a partition, the minority side cannot elect a leader or commit decisions, which contradicts "every partition continues its mission".
- If each partition elects its own leader instead, the result is split-brain: duplicate task assignment that must be reconciled when partitions merge.
- This is the CAP trade-off. The design explicitly chooses **availability under partition, with reconciliation afterwards**.
- Design implication: "Raft-inspired" means borrowing terms/epochs for conflict resolution, not majority consensus. The leader is a **partition-local, optional coordinator**, not a requirement for correctness.

### 2.2 Crash vs. disconnection is indistinguishable
- In an asynchronous network, a silent drone may be crashed, out of range, or delayed (FLP impossibility; Chandra–Toueg unreliable failure detectors).
- Design implication: failure detection produces **graded suspicion** (e.g., an adapted phi-accrual detector), and the system must tolerate false suspicion: duplicated task execution and conflicting state when the "failed" drone returns.
- The recovery-speed vs. duplicated-work trade-off is measurable and is the most interesting part of the concept.

### 2.3 MARL vs. dynamic membership
- QMIX and VDN assume a fixed number of agents. Variable team sizes need parameter sharing plus attention or GNN observation encoders.
- CTDE algorithms (QMIX, VDN, MAPPO) train centrally and execute in a decentralized way; this is acceptable in simulation. Fully decentralized learning (IQL, networked actor-critic) is less stable and not needed for an MPhil.
- CBBA is a decentralized allocator with convergence guarantees and is a strong baseline that MARL may not beat. MARL is justified only if it learns communication-aware decisions (wait for a peer, commit, or move to regain contact).

### 2.4 Learning-based routing is out of scope
Learning-based FANET routing is a separate research field. Use established routing (AODV/OLSR) plus standard DTN (epidemic / Spray-and-Wait), with no novelty claimed.

### 2.5 Simulation stack
Co-simulating ns-3, Gazebo, PX4 SITL and PyTorch is months of engineering, and MARL needs millions of fast episodes.
- Train and evaluate in a **Python simulator** with point-mass kinematics and an abstracted channel model (range, distance-dependent loss, Gilbert–Elliott bursty loss, latency, partitions).
- Optionally validate communication assumptions in **ns-3** via ns3-ai / ns3-gym.
- Gazebo and PX4 are dropped.

### 2.6 Other issues

| Issue | Why it matters |
|---|---|
| Scalability claims | Realistic MARL evaluation covers about 5–50 drones; do not imply hundreds. |
| Centralized baseline | Under full connectivity it is an upper bound (oracle) and is presented as such. |
| Collision avoidance and flight safety | Assumed handled by a low-level controller; out of scope. |
| Energy model | Simple flight-time plus per-message transmission model; no physical accuracy claimed. |
| Leader flapping | Mobility causes repeated re-elections; needs hysteresis or leases. |
| Mission type | Mission continuity is not measurable without a concrete task model. |

## 3. Accepted research scope

### Core problem
> How can a UAV swarm keep allocating and completing tasks consistently when the network repeatedly partitions and drones fail, given that drones cannot reliably tell a crashed peer from a disconnected one?

Expected gap (hypothesis, to be confirmed or refuted in Step 2): resilient task allocation and mission-state consistency under partitions and ambiguous failures.

### In scope

| Layer | Role | Novelty claimed? |
|---|---|---|
| Replicated mission-state ledger (CRDT-style, version vectors, merge on reconnection) | Independent mission knowledge per drone; post-partition reconciliation | Yes (core) |
| Suspicion-based failure detector + false-suspicion-tolerant reassignment | Self-healing; recovery-speed vs. duplicated-work trade-off | Yes (core) |
| Communication-aware MAPPO task-selection policy (CTDE, shared parameters, attention encoder) | The AI component; compared with CBBA and greedy | Partial (application and design) |
| Partition-local coordinator with epochs (lease-based, optional) | Leader succession; leaderless vs. leader-based ablation | Minor |
| Store-carry-forward gossip (anti-entropy over DTN contacts) | Communication resilience | No |
| Join/leave via ledger and gossip | Dynamic membership | No |

### Out of scope
Learning-based routing, physical flight simulation (Gazebo/PX4), security and adversarial drones, collision avoidance, hardware, heterogeneous payloads beyond a simple capability vector, fully decentralized online learning, blockchain, QKD, Kubernetes.

### Reference mission
Search-and-rescue area coverage: the area is divided into sectors; each sector is a task with location, duration and optional priority. Metrics: coverage over time, duplicated coverage, completion time.

### Candidate hypotheses (to be tested, not claimed)
- **H1.** Under partitions, the decentralized design keeps a higher mission completion rate than centralized and leader-dependent baselines.
- **H2.** Suspicion-based reassignment shortens task recovery time at a measurable cost in duplicated work that depends on the suspicion threshold.
- **H3.** Communication-aware MARL reduces duplicated or missed tasks compared with CBBA under intermittent connectivity, but not necessarily under full connectivity.
- **H4.** Partition-local leadership gives no significant advantage over leaderless allocation (ablation; a negative result is still publishable).

## 4. Provisional title
> Partition-Tolerant Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity: A Multi-Agent Reinforcement Learning Approach

Alternative if MARL proves secondary:
> Resilient Decentralized Coordination of UAV Swarms under Network Partitions and Ambiguous Failures

## 5. Paper type
Methodology/proposal manuscript first, with the Results section marked pending. A results paper requires the Python simulator and MARL training (estimated 3–5 months for one MPhil student).

## 6. Researcher decisions (2026-11-22)
1. Narrowed core problem accepted; routing and physical simulation out of scope.
2. Search-and-rescue area coverage accepted as reference mission.
3. MARL (MAPPO, CTDE) is the central AI component; researcher confirmed readiness for Python/PyTorch implementation.
