# Phase A — Research Validation Report

**Title (unchanged):** AI-Driven Collaborative Environment Mapping, Resilient Coordination, and Self-Healing in Decentralized UAV Swarms under Intermittent Connectivity

**Date:** 2026-11-23 · **Status:** awaiting supervisor/author review before Phase B

**Companion files**
- `Literature_Review_Matrix.md` — 46 verified studies from 2023–2026, using the 10 required columns
- `Reference_Verification_Table.csv` — DOI, authors, venue, volume, issue, pages, type, evidence level
- `Search_Log.csv` and `search_exports/` — queries, date, filters, raw metadata/abstracts, scripts

---

## 0. What was and was not done (access statement)

| Done | Not done |
|---|---|
| 37 structured Crossref queries (2023–2026, journal + proceedings), see `Search_Log.csv` | No IEEE Xplore / ScienceDirect / Scopus subscription search |
| Every shortlisted DOI resolved against Crossref; abstracts pulled from OpenAlex | **No full texts read.** Findings are taken from abstracts only |
| Venue, year, volume, pages, and article type cross-checked; preprints excluded from the count | Author-acknowledged limitations mostly cannot be confirmed until full texts are read |
| 82 previously verified references from the earlier Research 02 work (git history) screened for reuse as *foundational* sources | No Google Scholar citation tracking (forward/backward snowballing is still to do) |

This is a **systematic but preliminary** search, not a complete systematic review. The gap claims in §8 are phrased as *"within the screened corpus"* for that reason.

---

## 1. Understanding of the research vision

The research studies the **swarm's shared environmental knowledge as replicated mission state**. The focus is how that state is built, spread, allowed to diverge, reconciled, and protected when the network and the UAVs themselves are unreliable.

- **Agent level.** Each UAV is an autonomous agent with local sensing, its own *replica* of an environment model, and local decision-making. It never assumes it knows the global state.
- **Pillar 1: collaborative mapping.** UAVs write observations into their local replica and spread *deltas* to whoever is reachable. Replicas may diverge during partitions and must converge deterministically after reconnection, without double-counting evidence, while still reflecting genuine environmental change.
- **Pillar 2: resilient coordination.** Tasks such as survey, re-observation, and verification are allocated without a permanent central controller. Each partition keeps working on its local knowledge.
- **Pillar 3: self-healing.** Silence from a peer is treated as *evidence*, not proof. The swarm must weigh "disconnected" against "crashed", reassign that peer's tasks without destructive duplication, elect a temporary coordinator if needed, and reabsorb peers that rejoin. It must also limit knowledge loss when a UAV fails while holding observations nobody else has.

The integrating idea, which is the candidate contribution, is that **the map and the coordination layer are coupled**:
- map conflicts and staleness generate tasks;
- a failure changes what the map can be trusted for;
- reconnection reconciles both map knowledge and task ownership.

**What it is not.** It is not a new SLAM algorithm, a routing protocol, a generic MARL task-allocation study, or a centralized mapping server.

---

## 2. Research scope checklist

| # | Item | In scope | Treatment |
|---|---|---|---|
| 1 | Autonomous UAV agents with local perception, memory, decisions | ✅ | Core |
| 2 | Distributed environment model (per-UAV replica) | ✅ | Core: 2D multi-layer grid (see D-3) |
| 3 | Observation sharing with reachable peers, including multi-hop within a connected component | ✅ | Core |
| 4 | Environmental change over time (new obstacle, hazard appears or disappears) | ✅ | Core: recency-weighted evidence |
| 5 | Confidence, timestamps, provenance, conflict resolution | ✅ | Core |
| 6 | Operation during disconnection; store-carry-forward | ✅ | Core |
| 7 | Reconnection synchronization (anti-entropy) | ✅ | Core |
| 8 | Decentralized task allocation | ✅ | Core, but kept simple; not the contribution in itself |
| 9 | Failure suspicion (disconnection vs crash) | ✅ | Core |
| 10 | Leader succession (temporary, partition-local coordinator) | ✅ | Core, lightweight |
| 11 | Task redistribution and duplicate resolution | ✅ | Core |
| 12 | Dynamic membership (join, rejoin, removal) | ✅ | Limited: join and rejoin with state transfer |
| 13 | Simulation-based evaluation | ✅ | Core |
| 14 | SLAM / relative localization | ⚠️ | **Assumption** (shared global frame, bounded position noise), justified by mature C-SLAM literature (L02–L04, L22) |
| 15 | 3D mapping | ⚠️ | Optional extension only (see D-3) |
| 16 | Physical-layer / routing protocol design | ❌ | Abstract link model; routing scoped out (L38) |
| 17 | Blockchain, quantum, Kubernetes/cloud, satellite-primary, weapons/targeting, unrelated IoT/smart-city/business systems | ❌ | Excluded |
| 18 | Byzantine/malicious UAVs, security | ❌ | Future work (crash-stop and omission faults only) |

---

## 3. Feasibility assessment of the three pillars

| Pillar | Technical risk | MPhil feasibility | Why |
|---|---|---|---|
| **1. Collaborative mapping** | Medium | **High if 2D/2.5D grid + assumed localization**; low if C-SLAM or 3D is in scope | A gridded, semantically labelled map with per-cell evidence fits a Python simulator. Ground truth is known, so accuracy, completeness, and consistency are directly measurable. Full multi-agent SLAM is a PhD-scale topic on its own (L02, L22). |
| **2. Resilient coordination** | Low–Medium | **High** | Lease-based auctions and greedy information-gain allocation are well understood (L35, L36). The new part is only the coupling to map state. |
| **3. Self-healing** | Medium | **High for crash-stop and omission faults** | Accrual suspicion, leases, and term-numbered coordinator election can be implemented in a few hundred lines each. Distinguishing a crash from a disconnection can only be *probabilistic*. That limit is a stated, defensible result, not a failure of the method. |
| **AI component** | Medium–High | **Medium** | A learned policy adds training cost and reproducibility burden. See D-1 for a staged option. |
| **Integration** | Medium | **High if staged** | The main risk is breadth. The mitigation is one simulator and one map type, with every module ablatable. |

**Overall:** feasible as an MPhil if the decisions in §10 are taken as recommended. The earlier Research 02 simulator (`uavsim`, now deleted from the working tree but recoverable from commit `d112c3c`) already contains a world model, comms interface, allocators, and metrics, and can be reused.

---

## 4. Literature search strategy

**Sources.** Crossref REST API (bibliographic search, filtered to 2023-01-01 onward and to `journal-article`/`proceedings-article`) and OpenAlex (abstracts and metadata check). Publisher venues are prioritized: IEEE, Springer, Elsevier, MDPI, ACM, SAGE.

**Query blocks, one per required theme.** Full list in `Search_Log.csv`.

| Theme | Example query strings |
|---|---|
| A Swarm systems | `UAV swarm survey decentralized coordination autonomy` |
| B Mapping | `multi-robot SLAM decentralized communication constrained`; `distributed occupancy grid map merging`; `semantic map sharing multi-robot`; `multi-UAV collaborative exploration decentralized` |
| C Shared intelligence | `map synchronization reconnection multi-robot`; `UAV swarm shared situational awareness decentralized`; `CRDT robotics replicated map`; `change detection map update multi-robot` |
| D Communication | `store carry forward UAV data dissemination`; `multi-robot exploration intermittent communication rendezvous`; `delay tolerant multi-robot mapping` |
| E Self-healing | `failure detection UAV swarm heartbeat partition`; `distinguishing node failure from disconnection ad hoc` |
| F AI | `multi-agent reinforcement learning UAV exploration mapping communication` |
| Known-item checks | D²SLAM, Kimera-Multi, Hydra-Multi, DCL-SLAM, Swarm-SLAM, RACER |

**Inclusion criteria**
- Peer-reviewed journal or conference paper, 2023–2026, with a resolvable DOI
- Addresses at least one theme in a multi-agent or multi-UAV setting
- Abstract retrievable

**Exclusion criteria**
- Preprints and editorials
- Single-robot SLAM
- Physical-layer-only UAV communication (beamforming, RIS, outage)
- Excluded technologies (e.g., the blockchain data-management paper that appeared in the query results)

**Still to do (Phase D)**
- Full-text reading of the ~30 papers finally cited
- Backward and forward snowballing from L01, L08, L12, L22, L35, L45
- A focused search for a 2023–2026 multi-robot SLAM *survey* in a high-tier venue (none was confirmed in this pass)
- Re-check of the abstract-less L31

---

## 5. Preliminary verified studies

There are **46 studies** in the matrix, all 2023–2026 and peer-reviewed: 42 primary studies and 4 reviews/surveys. Distribution by theme:

| Theme | IDs | n |
|---|---|---|
| B Collaborative mapping | L01–L09, L19, L21, L22, L24–L26, L28 | 16 |
| B/C Exploration and sharing under restricted comms | L10–L16, L20, L23, L29, L30 | 11 |
| C Shared intelligence / replicated knowledge | L18, L27, L41 | 3 |
| D Communication resilience | L37, L38, L44, L48 | 4 |
| E Self-healing / fault tolerance | L33–L36, L39, L40, L45, L47 | 8 |
| F AI coordination | L32, L42, L43, L46 | 4 |

**Theme A** (decentralized swarm architectures) has no dedicated 2023–2026 survey yet. It is currently covered by L01, L19, L33, L34 and by foundational works from the earlier reference set (Chung et al., *IEEE T-RO* 2018, aerial swarm survey). A targeted Theme A search is the first Phase D task.

---

## 6. Literature review matrix

See `Literature_Review_Matrix.md`. It uses the exact required columns. Limitations are split into **A** (author-stated in the abstract) and **C** (my critical assessment).

---

## 7. Comparison of the closest existing research

✓ = addressed in the abstract · ~ = partial · — = not reported in the abstract (full-text check pending)

| Study | Decentralized | Shared env. map | Intermittent / partition | Reconnection merge semantics | Env. change | UAV failure detection | Task redistribution | Leader succession | UAV |
|---|---|---|---|---|---|---|---|---|---|
| L01 RACER (T-RO 2023) | ✓ | ✓ | ~ (limited, async) | — | — | — | ~ (re-partition) | — | ✓ |
| L22 Kimera-Multi resilient (IROS 2023) | ✓ | ✓ (metric-semantic) | ✓ | ~ | ~ (dynamic entities) | — | — | — | — |
| L12 Intermittent rendezvous (IROS 2024) | ✓ | ✓ | ✓ | ~ (opportunistic) | — | — | — | — | — |
| L08 OGM sync (IROS 2024) | ✓ | ✓ (OGM) | ~ (bandwidth only) | — | — | — | — | — | ✓ |
| L18 δ-CRDT knowledge (CVIU 2025) | ✓ | ~ (knowledge model) | ~ | ✓ (CRDT) | ✓ (context) | — | — | — | — |
| L27 Evidence-theoretic SA (Drones 2026) | ✓ | ~ (situational) | — | ~ (commutative fusion) | ✓ | — | — | — | ✓ |
| L45 HMP patrolling (ICAART 2026) | ✓ | — | ✓ (meetings) | — | — | ✓ (missed meetings) | ✓ | — | ✓ |
| L32 MAGEC (IROS 2024) | ✓ | — | ✓ | — | — | ~ (implicit) | ✓ (learned) | — | — |
| L35 UCDG-PD (Drones 2026) | ✓ | — | ✓ | — | — | — | ✓ (leases) | — | ✓ |
| L40 RGLF (TDSC 2026) | ✓ | — (model data) | ~ | — | — | ~ | ~ | ✓ (gossipmonger) | ✓ |
| L39 Churn-tolerant election (ICDCS 2023) | ✓ | — | ✓ (churn) | — | — | ✓ (membership) | — | ✓ | — |
| **This research (proposed)** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (probabilistic) | ✓ | ✓ (partition-local) | ✓ |

**How to read this table**
- **Mapping works** (L01, L08, L12, L22) handle maps under weak communication. None of them, *per the abstracts*, treats UAV failure, task recovery, or leadership.
- **Self-healing works** (L32, L35, L45) handle failures and reassignment. None of them maintains a shared environment model.
- **Replicated-knowledge works** (L18, L27) provide the right algebra (CRDTs, commutative fusion) but outside UAV mapping.

The candidate contribution sits at the intersection of these three groups. That claim can only become firm after full-text checks of L01, L12, L22, and L45, because their full texts may cover more than their abstracts.

---

## 8. Preliminary research-gap analysis

### 8.1 Primary gap (candidate)

> Within the screened 2023–2026 literature, collaborative UAV/multi-robot mapping under intermittent connectivity and self-healing UAV coordination have been studied **separately**. No screened study treats the shared environment map as **replicated mission state** whose (i) divergence during partitions, (ii) deterministic reconciliation after reconnection, and (iii) exposure to knowledge loss when a UAV fails are **explicitly coupled** to failure suspicion, task redistribution, and leadership succession. There is also no evaluation that measures map consistency and mission continuity *together* under combined communication and physical failures.

**Supporting evidence**
- The mapping works (L01–L09, L12, L22, L24–L26) optimize bandwidth, alignment, or exploration speed.
- The self-healing works (L33, L34, L45, L47) restore formation, topology, or patrol coverage.
- The allocation works (L35, L36) reconcile *assignments* with timestamps or leases, but not *environment knowledge*.

### 8.2 Supporting gaps

| ID | Supporting gap | Evidence | Status |
|---|---|---|---|
| G1 | **"Map merging" mostly means registration (frame alignment), not replica convergence.** Merge rules that are idempotent, avoid double-counting, and stay change-aware for repeated anti-entropy exchanges are not addressed in the robotics corpus screened. | L09, L24, L26 (registration); L08 (encoding); L18, L41 (CRDTs outside mapping) | Strong at the abstract level |
| G2 | **Telling a disconnected UAV from a crashed one is rarely modelled.** Self-healing studies either assume the failure is known or infer it from fixed events such as missed meetings, which can cascade (L45, author-stated). | L33, L45, L47; L37 shows that physical link loss happens without UAV failure | Moderate; full text needed |
| G3 | **Knowledge preservation under UAV loss.** The only screened UAV work on protecting data against UAV loss (L40) handles learning-model data, not spatial observations. | L40 | Moderate |
| G4 | **Evaluation gap.** Map consistency across replicas, staleness, and duplicate work are rarely reported alongside mission completion under *combined* partition and failure scenarios. | L34 separates network and mission metrics; L22 evaluates communication scenarios but not failures | Moderate |

### 8.3 What can realistically be claimed as original (tentative)

1. A **per-origin, recency-aware, conflict-free replicated grid** for semantic environment maps. It adapts the published δ-state CRDT principles (L41, L18) to evidence-based UAV maps. *This is an adaptation, not new CRDT theory.*
2. **Context-aware failure suspicion.** φ-accrual style suspicion (foundational) is conditioned on the map, the last known position, and expected link availability, producing separate *disconnected* vs *failed* hypotheses.
3. **Map-aware self-healing.** Task leases (L35) are extended so that recovery also handles the knowledge side: re-survey of stale or unshared areas, and verification tasks triggered by map conflicts.
4. **Integration and evaluation.** One decentralized framework and one evaluation protocol with metrics for both mapping and mission continuity, plus ablations.

**Not claimed:** new SLAM, new consensus, new MARL algorithms, guaranteed failure detection, or unlimited resilience.

---

## 9. Candidate algorithms and technologies, with recommendations

### 9.1 Environmental representation

| Option | Solves | Cost | Under intermittency | MPhil feasibility | Recommendation |
|---|---|---|---|---|---|
| 2D occupancy grid (log-odds) | Free/occupied space | Low | Grid cells merge naturally | High | ✅ Base layer |
| Semantic layer per cell (building, obstacle, hazard, restricted, victim/POI) | Buildings, hazards, objects | Low | Small categorical deltas | High | ✅ |
| 2.5D height field (per-cell max height) | Terrain and buildings without full 3D | Low | Same as grid | High | ✅ Recommended middle ground |
| Full 3D voxel map (OctoMap-style) | True 3D structure | High memory/bandwidth (L30, L26) | Heavy deltas | Low–Medium | ⏸ Optional extension |
| 3D scene graphs (L05–L07) | Rich semantics | High perception cost | Compressible | Low | ❌ Cite only |
| Visual / multi-agent SLAM (L02–L04, L22) | Localization + geometry | Very high | Studied separately | Low | ❌ Assumption; cite as related work |

### 9.2 Synchronization and conflict resolution

| Option | Assessment | Recommendation |
|---|---|---|
| Plain last-writer-wins by timestamp | Simple, but discards evidence from multiple observers and needs synchronized clocks | ❌ Use as a **baseline** |
| Additive log-odds fusion of received maps | Not idempotent: re-receiving a map double-counts evidence, which is a known pitfall | ❌ Use as a **baseline / ablation** |
| **Per-origin δ-state CRDT cell** (each cell keeps, per observer, a versioned evidence summary with timestamp and confidence; merge = per-origin max-by-version; fused value = recency-weighted combination) | Idempotent, commutative, associative, so replicas converge regardless of order or duplicates (L41). Recency weighting captures environmental change (L09). Provenance comes for free. | ✅ **Core** |
| Version vectors / digests + anti-entropy on contact | Sends only missing deltas after reconnection | ✅ Core |
| Gossip within a component + store-carry-forward across components | Matches FANET/DTN practice (L38, L48) | ✅ Core |
| Dempster–Shafer fusion (L27) | Richer uncertainty but heavier | ⏸ Discuss; possible extension |

### 9.3 Coordination and task allocation

| Option | Assessment | Recommendation |
|---|---|---|
| CBBA / ACBBA (foundational) | Well-known baseline; consensus is slow under partitions | Baseline |
| **Lease-based greedy auction over map-derived tasks** (frontier/sector survey, re-observation of stale cells, conflict verification) | Lightweight; works within each partition; leases expire on suspicion (L35) | ✅ **Core** |
| Centralized oracle (full knowledge, perfect comms) | Upper bound | Baseline |
| MARL (IPPO/MAPPO with parameter sharing, GNN encoders; L32, L14, L15) | Learns target selection; does **not** provide delivery, replication, or election guarantees | ⏸ See D-1 |
| QMIX / VDN | Fixed agent count conflicts with dynamic membership | ❌ |
| Independent Q-learning | Simple but unstable; L14 shows a viable distributed Q-learning variant | Optional baseline if D-1 = B |

### 9.4 Communication model

| Option | Recommendation |
|---|---|
| ns-3 / OMNeT++ packet-level FANET | ❌ Too costly to integrate; not the contribution |
| **Range-based link model + distance-dependent loss + Gilbert–Elliott burst outages + scripted partitions + per-contact bandwidth budget** (in Python/NetworkX) | ✅ Core. Matches what the claims need. ns-3 cross-validation is optional future work |

### 9.5 Failure detection, leadership, membership

| Option | Assessment | Recommendation |
|---|---|---|
| Fixed heartbeat timeout | Treats every timeout as a crash, which the brief explicitly forbids | Baseline / ablation |
| **φ-accrual suspicion conditioned on expected reachability** (last known position, planned path, link model) → states ALIVE / UNREACHABLE (likely disconnected) / SUSPECTED-FAILED / REJOINED | Models uncertainty and stays tunable | ✅ Core |
| SWIM-style indirect probing via neighbours | Reduces false suspicion within a component | ✅ Core (lightweight) |
| Raft / majority consensus | A minority partition cannot elect a leader (CAP), so it is unsuitable for a non-permanent leader | ❌ Cite as contrast |
| **Partition-local coordinator by deterministic rank (health/energy/ID) + epoch (term) numbers; merge resolves dual leaders by higher epoch, then rank** (L39 informs health preference) | Leader is an *optimization* (tie-breaking, re-planning trigger). Correctness never depends on it | ✅ Core |
| Join/rejoin via full-state transfer of map replica + membership incarnation numbers | Simple, testable | ✅ Core |

### 9.6 Simulation tools

| Tool | Recommendation |
|---|---|
| **Python 3 + NumPy + NetworkX** (custom discrete-time simulator; reuse `uavsim` from commit `d112c3c`) | ✅ Core |
| Gymnasium / PettingZoo + PyTorch | Only if D-1 = B |
| Gazebo / PX4 SITL | ❌ Not needed; flight dynamics are not part of the contribution |
| ns-3 / OMNeT++ | ❌ (optional validation) |

**Recommended combination:** 2D semantic grid + 2.5D height · per-origin δ-CRDT cells with version-vector anti-entropy · gossip + store-carry-forward · lease-based auction over map-derived tasks · context-aware accrual suspicion + indirect probing · partition-local epoch-numbered coordinator · a pure-Python simulator. Optionally, one learned component, gated per D-1.

---

## 10. Unresolved decisions requiring your approval

| ID | Decision | Options | My recommendation and reason |
|---|---|---|---|
| **D-1** | **What makes the framework "AI-driven"?** (affects how examiners read the title) | **A.** Agents use probabilistic reasoning (Bayesian evidence maps, accrual suspicion) and utility/information-gain planning, i.e. classical AI with no learning. **B.** A plus one learned policy (parameter-shared IPPO/MAPPO on each UAV's *local map replica*) for exploration/task selection, compared with the heuristic. **C.** MARL as the core coordinator | **B, staged.** Build A first so that every pillar works without learning. Add the learned policy in Stage 4b behind a go/no-go gate. This keeps "AI-driven" defensible without making the research depend on RL training. |
| **D-2** | Localization assumption | Assume a shared global frame with bounded Gaussian position noise **vs** model relative pose / C-SLAM | **Assume it.** C-SLAM is mature (L02–L04, L22) and would double the scope. State it as a threat to validity. |
| **D-3** | Map dimensionality | 2D · **2D + 2.5D height** · full 3D | **2D + 2.5D.** It represents terrain and buildings and is cheap to sync. 3D stays an optional extension. The title is unaffected. |
| **D-4** | Fault model | Crash-stop + omission (message loss) **vs** also Byzantine | **Crash-stop + omission only.** Byzantine faults become future work. |
| **D-5** | Swarm sizes and area | e.g. N ∈ {5, 10, 20}; 2 km × 2 km; 10 m cells | Approve or adjust. This drives compute budget and the scaling claims. |
| **D-6** | Mission type for scenarios | Post-disaster search & rescue survey **vs** environmental monitoring | **SAR survey.** It is non-military, has clear victim/hazard semantics, and matches most of the cited literature. |
| **D-7** | Public dataset or purely synthetic worlds | Synthetic procedurally generated worlds with ground truth **vs** derived from a real map | **Synthetic, seeded.** Ground truth is exact and reproducible. A real-map layout can be added if time allows. |
| **D-8** | Reuse of earlier Research 02 material | The working tree currently shows all Step 1–7 files and the simulator as *deleted* (uncommitted) | Please confirm the deletion is intentional. I will not commit it unless you ask. I recommend reusing the `uavsim` core and the foundational references, and **not** reusing the earlier task-allocation framing. |
| **D-9** | Target length/template | University template? IEEE two-column? | Please supply the template if one exists. The ~25-page literature review needs a defined page format. |
| **D-10** | Second supervisor and affiliation details in the manuscript | Placeholders in `Research paper.docx` | Fill in when known. |

---

## 11. Proposed next steps (after your approval)

1. Full-text reading of the closest studies (L01, L08, L12, L22, L35, L45, L32, L18), then update the matrix limitation columns with author-acknowledged limitations.
2. A targeted Theme A survey search, and snowballing.
3. Phase B: research questions and objectives, formal model, architecture diagrams, and pseudocode built on the decisions above.

## Scope-control check (Section 14 of the brief)

- **Pillar 1:** The per-UAV replica, delta sharing, change-aware evidence, and reconnection anti-entropy are the core of §9.1–9.2. ✅
- **Pillar 2:** There is no permanent controller. Partition-local operation and explicit partitions are part of the communication model (§9.3–9.4). ✅
- **Pillar 3:** Suspicion distinguishes disconnection from failure. Leader succession, task redistribution, and join/rejoin with state transfer are covered (§9.5). ✅
- Excluded technologies are not used anywhere. ✅
- The title, abstract, and objectives are unchanged. ✅

---

## 12. Decision record (author review, 2026-11-23)

| ID | Outcome |
|---|---|
| D-1 | **Approved: recommended option B, staged.** Classical-AI core, plus one learned policy behind a go/no-go gate |
| D-2 | **Approved:** localization assumed (shared global frame, bounded position noise) |
| D-3 | **Approved:** 2D semantic grid + 2.5D height layer; 3D is an optional extension |
| D-8 | **Confirmed:** the deletion of the earlier Research 02 material is intentional |
| D-9 | **Approved:** standard IEEE format (IEEE two-column template, IEEE citation style) |
| D-4, D-5, D-6, D-7 | Not explicitly answered. **The recommended defaults are adopted provisionally** and are listed again in Phase B §9 for confirmation |
| D-10 | Open (supervisor names and affiliation) |
