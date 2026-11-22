# Step 2: Literature Review and Research Gap

**Project:** Partition-tolerant, self-healing task allocation for decentralized UAV swarms under intermittent connectivity
**Date:** 2026-11-22
**Status:** Revision 2 (2026-11-22). A web search for the seven papers flagged in revision 1 found seven additional papers (R66–R72). The closest one, CC-OPI [R66], was read in full and narrows the gap (Section 6). Three of the seven flagged papers remain at abstract level (Section 7).

Reference IDs `[Rxx]` refer to `Reference_Verification_Table.csv` in this folder. Every listed reference's title, authors, venue, year and DOI were confirmed against Crossref, or against the publisher/arXiv page for the five references without a DOI. The `content_evidence_level` column states how much of each paper was actually read.

---

## 1. Search method

| Item | Detail |
|---|---|
| Database | Crossref REST API (primary). OpenAlex and Semantic Scholar were used for DOI lookups and abstracts only; their search endpoints were rate-limited on 2026-11-22. arXiv API was used for preprint versions. |
| Queries | 21 topic queries (T1–T21) covering: decentralized swarm architectures, MARL task allocation, communication-constrained MARL, CBBA under communication constraints, failure-driven reallocation, FANET routing, DTN/store-carry-forward, intermittent connectivity, self-healing, leader election, failure detection, CRDTs, scalable/GNN MARL, SAR coverage, multi-robot consensus under communication loss, partition/merge, false failure detection, MARL under agent failure, swarm resilience, opportunistic synchronisation. Full strings: `Search_Log.csv`. |
| Filters | Published 2019–2026; journal articles and proceedings papers. Foundational pre-2019 works were added by targeted DOI lookup. |
| Retrieval | Top 30–40 records per query by relevance: 780 records, 708 unique after DOI deduplication. Raw exports: `search_exports/`. |
| Screening | Title screening of the 708 unique records, then metadata and abstract retrieval for 71 shortlisted DOIs (including foundational works added by DOI). 60 DOI records retained, plus 5 non-DOI foundational works: 65 references in total. |
| Exclusions | Security/intrusion detection, edge-computing offloading, formation control only, hardware fault tolerance, physical-layer work, retracted items (several retraction notices appeared in the results and were excluded). |
| Web search (rev. 2) | Targeted web searches for the seven unresolved papers. These surfaced R66–R72, mostly 2026 arXiv preprints not yet indexed in Crossref. Preprints are marked as not peer-reviewed in the reference table. |
| Full-text access | Most publisher pages (MDPI, Springer, IEEE Xplore, ScienceDirect, HAL, SciTePress) refused automated access. Full text was read for four arXiv papers: R34 and R53 partially, R66 mostly verbatim, R67 fully. |
| Total | 72 references (R01–R72). |

## 2. Thematic review

### 2.1 Decentralized task allocation (foundations and baselines)
Gerkey and Matarić's taxonomy [R01] frames multi-robot task allocation (MRTA) formally. CBBA [R02] is the dominant decentralized market-based baseline: it is proven to converge to conflict-free assignments and is robust to inconsistent situational awareness. ACBBA [R03] removes the synchronous-round assumption. CBBA is extended for search and rescue [R31] and for large swarms [R33], and Song et al. [R30] provide a unified evaluation of centralized (Hungarian, auction) and distributed (CBBA, auction 2-opt) allocators. That evaluation includes resilience to UAV failures. **Implication:** CBBA/ACBBA must be baselines, and the Song et al. framework is a useful template for the evaluation design.

### 2.2 Allocation under imperfect communication
This strand is active and growing. Methods address:
- limited bandwidth and message collisions, with learned communication scheduling (CA-CBBA [R22]);
- packet loss and data errors (DTBA-C3 [R24]);
- communication-constrained conflict resolution (LR-PI [R23]);
- limited range with Bernoulli, Gilbert–Elliott and Rayleigh channel models (empirical study [R27]; distance-based Bernoulli model [R29]);
- chance-constrained allocation under intermittent stochastic links with "task-local leases" to resolve conflicts (UCDG-PD [R25], the closest work found).

Otte et al. [R26] study how lossy auctioneer–bidder links degrade multi-round auctions. They find that re-sending winner data in later rounds is a simple, effective remedy (from indexing pages; full text paywalled). Further work:
- AC-DMTA [R68] handles stale and asymmetric information, using timestamp/recency records to resolve asynchronous conflicts and communicating only when an assignment might be invalidated;
- Iterative Best Response [R70] scales to 100 drones under sparse communication;
- entropy-gated belief fusion [R71] handles Poisson-timed intermittent contact in multi-agent search.

**CC-OPI [R66] (arXiv, Sept 2026) is the closest work found.** Read in full:
- **Partitions:** a short communication radius fragments the swarm into "disjoint information islands". CC-OPI replaces allocate-then-execute with event-driven replanning.
- **Merge rule:** on contact, each UAV takes the union of completed-task sets, "a versioned full-state gossip with a monotone merge". In effect this is a grow-only-set CRDT, though the paper does not use that term.
- **Duplicates:** treated as transient. Two UAVs in different islands "may transiently hold the same task" until the islands merge. Duplicate *travel* is reported as "wasted distance".
- **Results:** about 0.80 task completion at a 250 m radius with 6–16 UAVs, ahead of CBBA/PI online variants.
- **Explicit exclusions:** "no mid-mission UAV failure are modeled". Links within range are "without loss, delay, reordering, or bandwidth contention". There is no failure detector; the "emergency pool" is driven by deadlines, not failures. No learning is involved.

UCDG-PD's "task-local leases" [R25] turn soft assignments into binary, route-executable decisions. Publisher snippets give no evidence that they handle UAV loss.

**What this strand achieves:** allocation that stays conflict-free or near-optimal despite message loss, delay and limited range. With CC-OPI, this now includes partitioned swarms whose completion state merges on reconnection.
**What remains open:** UAV crashes *combined with* partitions, and any reconciliation of ownership or liveness state beyond completion facts.

### 2.3 Failure-triggered reallocation
ES-CBBA [R35] escalates the replanning scope when UAVs fail. Improved PI [R36] and CBAA-based reallocation [R37] handle single or multiple UAV malfunctions.

IRDS [R67] (arXiv 2026, read in full) reallocates SAR sectors with a reverse auction after injected battery faults: 93% success under 25% workforce loss, 8 simulated Crazyflie drones. However, communication is global (a central `MarketSystem` class acts as a proxy for a distributed ledger), the paper describes no detection mechanism, and failure is "treated instantaneously as a market event". Nasir and AlDurgam [R69] fold sensor and actuator faults into an offline stochastic-dynamic-programming assignment policy.

**Common assumption:** failure is an *event* known to the planner. The abstracts give no mechanism for *detecting* failure under lossy communication, and no consideration of a UAV that is merely disconnected and later returns.

### 2.4 Self-healing and fault tolerance in UAV swarms
Most "self-healing" UAV work targets **formation or topology**, not mission state:
- recursive grouping that restores configuration and consistency after individual failures [R38];
- GAT-based DRL that restores network connectivity [R39];
- decentralized fault-tolerant formation and coverage, evaluated in NS-3 + ROS/Gazebo [R40];
- network-level resilience metrics [R45].

The closest to our problem:
- **HMP** [R41]: detects failures at periodic meeting points and redistributes patrol responsibilities. It reports *cascading failures* caused by meeting scheduling under some fault conditions.
- **Chatterjee and Dutta** [R42]: guarantee *partial state synchronization* with bounded variance under message or UAV loss.
- **Gossip-based data redundancy** [R44] for UAV-swarm learning.

Outside robotics, Nikolic et al. [R43] show that a faulty process is indistinguishable from a slow one in decentralized systems. They quantify the resulting dilemma between fault correction and fault tolerance on a 3000-node network.

### 2.5 Leadership and membership
Leader election in UAV swarms is studied mainly for **lead–follow formations**:
- a Raft-inspired voting scheme under constrained communication that outperforms plain Raft [R46];
- greedy dynamic leader selection [R47].

In distributed computing, churn-tolerant leader election handles stale or incorrect membership lists [R48]. Raft itself requires a majority quorum [R65]. SWIM [R08] separates failure detection from membership dissemination, and phi-accrual detectors output continuous suspicion levels [R07].

**Implication:** leader election is not a novel contribution here. It belongs in the design as an ablation (hypothesis H4).

### 2.6 MARL for UAV coordination
CTDE algorithms dominate the field:
- QMIX [R61], VDN [R63] and MAPPO [R62], building on the CTDE framing of MADDPG [R64];
- a survey of communication-based MADRL [R49].

UAV/robot task-allocation MARL includes:
- TACC [R50]: CTDE, learned communication gating, hardware flight with 10 UAVs in SAR;
- Async-VDN combined with ACBBA [R51];
- HIPPO-MAT [R52]: GraphSAGE + IPPO, up to 30 agents;
- BCRT [R54]: belief consensus and role tokens under intermittent communication, reported as more resilient but "not uniformly superior";
- decentralised DQN with selective experience sharing [R56];
- MARL search under aperiodic intermittent communication [R55] (full text not accessed).

On resilience:
- **MAGEC** [R53] trains MAPPO with a shared GNN policy and handles agent attrition and Bernoulli message loss in patrolling. From the partial full text: attrition is *not* detected explicitly, crashed and disconnected agents are not distinguished, and partitions are not modelled.
- MAPPO's robustness to partial agent failure depends strongly on the reward structure [R57].
- Communication can become redundant when agents malfunction [R58].

**Implication:** "MARL + GNN + attrition" is already published, so MARL alone cannot carry the novelty claim. This is consistent with the "partial novelty" rating in Step 1.

### 2.7 Communication substrate (FANET and DTN)
Surveys cover FANET characteristics and routing [R15, R16, R17], RL-based routing [R18] and DTN [R13, R20]. Spray-and-Wait [R14] bounds DTN flooding cost. Xiong et al. [R19] show that store-carry-forward can beat hop-by-hop routing in disconnected UAV networks. Environmental disturbance alone (wind) breaks intra-swarm connectivity [R21]. Joint MADRL routing and trajectory control exists [R60].

**Implication:** learning-based routing is its own mature field, which confirms the Step 1 decision to keep it out of scope.

### 2.8 Replicated state under partition (distributed systems)
The underlying theory is established:
- the CAP theorem [R09], FLP impossibility [R05] and unreliable failure detectors [R06] set the limits;
- CRDTs [R10, R11] provide deterministic convergence while staying available under partition;
- Guidec et al. [R12] evaluate CRDTs in opportunistic (disruption-tolerant) networks and report that delta-state CRDTs need the fewest synchronisation messages. This is from the Semantic Scholar summary; the full text was not read.

The same authors show that mobile relays speed up, or even enable, convergence of state-based CRDT replicas in opportunistic networks [R72]. This is directly relevant, since UAVs can act as their own relays.

**Revised finding:** no reviewed UAV task-allocation paper uses CRDTs *by name*. However, CC-OPI [R66] applies a CRDT-like monotone union merge, limited to the set of *completed* tasks. Partition-tolerant mission state is therefore not absent. What has not been explored is extending it to ownership/claim state and to *suspected-failure* state, where merges are not monotone: a "failed" UAV may come back.

## 3. Comparison of the closest works

Key: ✓ addressed · ◐ partially/indirectly · ✗ not mentioned in the material read · ? text not accessible

| Ref | Work (year) | Intermittent comm / partitions | UAV failure handled | Explicit failure detection | Crash vs. disconnection ambiguity | Reconciliation / duplicate work after reconnection | Learning-based | Leader / succession | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| R02 | CBBA (2009) | ◐ inconsistent SA | ✗ | ✗ | ✗ | ✗ | ✗ | leaderless | Abstract |
| R22 | CA-CBBA (2022) | ✓ bandwidth, collisions | ✗ | ✗ | ✗ | ✗ | ✓ DRL comm | leaderless | Abstract |
| R24 | DTBA-C3 (2026) | ✓ loss, data errors | ✗ | ✗ | ✗ | ✗ | ✗ | leaderless | Abstract |
| R25 | UCDG-PD (2026) | ✓ stochastic links | ✗ | ✗ | ✗ | ◐ task-local leases | ✗ | leaderless | Abstract + snippets |
| **R66** | **CC-OPI (2026, preprint)** | **✓ islands + merge** | **✗ "not modeled"** | **✗** | **✗** | **◐ union merge of completed set; wasted distance measured** | **✗** | **leaderless** | **Full text** |
| R67 | IRDS (2026, preprint) | ✗ global comm | ✓ battery faults | ✗ instantaneous | ✗ | ✗ | ✗ | — | Full text |
| R68 | AC-DMTA (2026) | ✓ stale/asymmetric | ✗ | ✗ | ✗ | ◐ timestamp/recency | ✗ | leaderless | Abstract |
| R27 | Verma et al. (2025) | ✓ range, GE, fading | ✗ | ✗ | ✗ | ✗ | ✗ | — | Abstract |
| R30 | Song et al. (2025) | ◐ intermittent | ✓ | ? | ✗ | ✗ | ✗ (RL outlined) | — | Abstract |
| R34 | Bramblett et al. (2023) | ✓ planned disconnection | ✓ | ◐ belief-based | ◐ belief tracking | ◐ rebalance on rendezvous | ✗ | central auction | Partial full text |
| R35 | ES-CBBA (2026) | ✗ | ✓ | ✗ (event given) | ✗ | ✗ | ✗ | leaderless | Abstract |
| R41 | HMP (2026) | ✓ meeting-based | ✓ | ✓ at meetings | ? | ? | ✗ | ? | Abstract |
| R42 | Chatterjee & Dutta (2024) | ✓ message loss | ✓ UAV loss | ? | ? | ◐ bounded state sync | ✗ | ? | Abstract |
| R46 | Zuo et al. (2022) | ✓ constrained | ✓ leader only | ? | ✗ | ✗ | ✗ | ✓ Raft-inspired | Abstract |
| R50 | TACC (2026) | ✓ comm limits | ✗ | ✗ | ✗ | ✗ | ✓ CTDE | — | Abstract |
| R51 | Async-VDN (2025) | ✓ async | ✗ | ✗ | ✗ | ✗ | ✓ VDN | — | Abstract |
| R53 | MAGEC (2024) | ✓ Bernoulli loss; no partitions | ✓ attrition | ✗ implicit | ✗ | ✗ | ✓ MAPPO+GNN | — | Partial full text |
| R54 | BCRT (2026) | ✓ packet loss | ? | ? | ? | ◐ "coordination consistency" | ✓ MARL | token roles | Abstract |
| R55 | Fu et al. (2025), AICoRL | ✓ aperiodic disruptions | ? | ? | ? | ? | ✓ MARL (noisy policy) | ? | Abstract via indexing |
| R43 | Nikolic et al. (2021) | generic async net | ✓ | ✓ | ✓ (core topic) | ◐ inconsistency measured | ✗ | — | Abstract; not robotics |

## 4. What existing research has achieved

1. Decentralized allocation with convergence guarantees (CBBA family), plus many variants that tolerate packet loss, delay, limited range and bandwidth limits.
2. Reallocation after UAV failure, provided the failure is known.
3. MARL policies (mostly CTDE, often GNN-based) that cope with lossy communication and, in one case [R53], agent attrition. They are validated in simulation and occasionally on hardware [R50].
4. Swarm self-healing at the formation and topology level.
5. Raft-inspired leader election for UAV formations.
6. A mature distributed-systems theory of failure detection, partitions and convergent replicated state.

## 5. Remaining limitations

- **L1. Communication imperfection and agent failure are studied separately.** The strongest partition-tolerant allocator, CC-OPI, explicitly excludes UAV failures [R66]. The SAR self-healing allocator IRDS assumes global communication [R67]. Other communication-robust allocators [R22–R27, R68, R70] do not model crashed UAVs in their abstracts, and failure-reallocation methods [R35–R37, R69] do not model lossy links.
- **L2. Failure is treated as known.** No reviewed UAV/MRTA paper explicitly models the crash-vs-disconnection ambiguity, although distributed-systems research shows it is unavoidable [R05, R06] and that acting on it causes measurable inconsistency [R43].
- **L3. The cost of wrong suspicion is unmeasured.** Duplicated task execution, and conflicting mission state when a presumed-failed UAV returns, are not reported as metrics in the reviewed abstracts. HMP [R41] reports cascading failures from fault-handling, which suggests this cost is real.
- **L4. Partition-tolerant mission state is only partial.** CC-OPI merges completed-task facts monotonically [R66], and AC-DMTA resolves stale conflicts with timestamps [R68]. Neither replicates *ownership* and *liveness/suspicion* state in a form that converges correctly when a UAV presumed failed returns. CRDT theory [R10–R12, R72] provides the tools.
- **L5. MARL resilience is implicit.** MAGEC-type policies generalise over attrition but do not detect failures or reconcile state, and their robustness is sensitive to the reward structure [R57].
- **L6. Evaluation scale is small** (2–30 agents), and fault scenarios are usually limited to a few removals at fixed times.

## 6. Evidence-supported research gap

> Decentralized UAV task allocation has recently been made robust to swarm partitioning, with completion state merged on reconnection [R66], and, separately, to UAV failures that the planner is told about [R35, R67]. The reviewed literature does not address the case where both happen together. There, (a) a silent UAV may be crashed or merely partitioned and cannot be told apart reliably [R05, R06, R43], (b) treating it as failed triggers reassignment that may duplicate work when it returns, and (c) treating it as alive leaves its tasks unserved if it really crashed. No reviewed UAV/MRTA work detects failure under partitions, replicates ownership and suspicion state so that it converges after a wrong suspicion, or quantifies the resulting **recovery-time vs. duplicated-work trade-off**.

**Why this is not merely "an uncommon combination":** L2 and L3 identify a *failure mode* that existing methods cannot avoid, because their correctness assumes failures are known. Nikolic et al. [R43] show the failure mode is real and measurable. The contribution is to characterise and mitigate it for UAV task allocation, not simply to combine technologies.

**Consequences for the Step 1 scope**
- **Confirmed (core):** a replicated mission-state ledger plus suspicion-based detection and reassignment, and the recovery-time vs. duplicated-work trade-off (H2).
- **Confirmed (partial novelty only):** MARL. MAPPO + GNN under attrition already exists [R53]. Our MARL component must be framed as *ledger- and suspicion-aware* policy learning, compared against CBBA/ACBBA and a communication-robust variant (e.g., DTBA-C3 [R24] or the UCDG-PD idea [R25]).
- **Confirmed (not novel):** leader election [R46, R48]. It is retained only for the H4 ablation.
- **Confirmed out of scope:** topology self-healing [R39] and learning-based routing [R18, R60].
- **Adopt:** Song et al.'s unified evaluation framework [R30] and the channel models from Verma et al. [R27] (Bernoulli, Gilbert–Elliott).
- **New key baseline:** CC-OPI [R66], the state of the art for partitioned allocation without failures. Our method must match it when no failures occur and beat it when failures are injected. Its "wasted distance" metric should be adopted alongside our duplicated-work metric.
- **Narrowed novelty claim:** the core contribution is now specifically **failure-aware partition tolerance**: suspicion-based detection, plus convergent ownership and suspicion state, plus the measured trade-off. "Partition-tolerant allocation" in general is no longer novel.

## 7. Threats to the gap claim (must be resolved before Step 3)

Most evidence is at abstract level. The gap could be weakened if any of these papers address L2–L4 in their full text:

Outcome of the revision-2 web search for the seven flagged papers:

| Priority | Ref | Status | Remaining risk |
|---|---|---|---|
| 1 | R25 UCDG-PD | Snippets only: leases make allocation decisions binary; no sign of UAV-loss handling | Low–medium; full text still blocked |
| 2 | R41 HMP | Abstract only; no open-access PDF exists (repository links the DOI only) | **Medium.** It detects failures at meetings and reports cascading failures. It may touch the crash-vs-late ambiguity |
| 3 | R55 Fu et al. | Abstract via indexing pages: AICoRL, MARL with noisy policy, aperiodic disruptions; no failure modelling mentioned | Low |
| 4 | R54 BCRT | Not found anywhere outside IEEE | Low (6-page conference paper; abstract says robustness to packet loss) |
| 5 | R26 Otte et al. | Key finding obtained: lossy auctioneer–bidder links; re-sending winner data helps | Low |
| 6 | R12 Guidec et al. | Paywalled; authors' 2026 follow-up [R72] read instead | Low (design input, not a gap threat) |
| 7 | R42 Chatterjee & Dutta | Not found outside IEEE | Low–medium (bounded state sync under UAV loss) |
| new | R66 CC-OPI | **Read in full.** Covers partitions and completion merge; excludes failures | Gap narrowed but survives (Section 6) |

HMP [R41] and Chatterjee & Dutta [R42] are the only papers that still need institutional access.

**Search limitations:** Crossref relevance ranking only, with no Scopus, IEEE Xplore or Web of Science access. Retrieval stopped at the top 30–40 records per query, and screening was single-reviewer and largely abstract-level.

**Confirmatory searches to run in IEEE Xplore and Scopus (2019–2026):**
1. `("task allocation" OR "task assignment") AND (UAV OR "multi-robot") AND ("network partition" OR "intermittent") AND (failure OR fault)`
2. `("failure detection" OR "failure detector") AND (UAV OR swarm OR "multi-robot") AND ("task allocation" OR "task reallocation")`
3. `("CRDT" OR "conflict-free replicated" OR "eventual consistency") AND (UAV OR robot OR swarm)`
