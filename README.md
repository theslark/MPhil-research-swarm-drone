# AI-Driven Collaborative Environment Mapping, Resilient Coordination, and Self-Healing in Decentralized UAV Swarms under Intermittent Connectivity

MPhil research (Advanced Research Methodology): a paper draft and its full research record.

> **Status:** Phases A–C (validation, design, methodology) are complete, and the paper draft has been started (Phase D).
> **No experiments have been run yet.** The Results section of the paper is a marked "pending" template, and no numerical result is claimed anywhere.

## The research in brief

A UAV swarm surveying a disaster area has to build a shared picture of a changing environment while its radio links come and go and individual drones may fail. Existing work studies the parts separately:

- collaborative mapping under limited communication;
- self-healing and task reassignment after UAV failures;
- conflict-free replication of shared knowledge, but outside UAV mapping.

This research treats the **shared environment map as replicated mission state**, and couples it to coordination and self-healing:

- **Mapping:** each UAV keeps its own map replica made of per-origin, recency-aware CRDT cells (2D semantic grid plus a 2.5D height layer). Replicas converge regardless of message order or duplication, never double-count evidence, and still reflect environmental change. Updates spread by gossip, anti-entropy on contact, and store-carry-forward.
- **Coordination:** tasks (survey, re-observe, verify, re-survey) are generated from the map and allocated through leases, with a temporary, partition-local coordinator. There is no permanent central controller.
- **Self-healing:** φ-accrual failure suspicion, conditioned on each peer's expected reachability, separates "disconnected" from "failed". Recovery restores both tasks and knowledge (re-surveying areas a failed UAV left stale).
- **AI:** a classical-AI core (probabilistic evidence maps, Bayesian failure inference, information-gain task utility), plus one learned policy (parameter-shared IPPO/MAPPO). The learned policy is adopted only if it passes a pre-defined performance gate.

**Evaluation plan (pre-registered):**
- a Python simulator;
- 14 scenarios, covering partitions, environmental change, single, multiple and leader failures, joining, and rejoining;
- baselines B0–B3 and 7 ablations;
- 5 hypotheses, tested with paired Wilcoxon tests, Holm correction, and Kaplan–Meier analysis.

## Repository structure

| Path | Contents |
|---|---|
| `Research paper.docx` | **The paper draft** (IEEE style). Title, authors and abstract were written by the author. Sections I–VIII, 2 figures, 11 tables, 5 algorithms and 65 references are built on them |
| `A_Phase_A_Research_Validation/` | Research validation report; literature review matrix (46 verified 2023–2026 studies); reference verification table (DOI, venue, pages); search log; raw search exports and query scripts |
| `B_Phase_B_Research_Design/` | Problem statement, research questions and hypotheses, assumptions, architecture (Mermaid diagrams), mathematical model, pseudocode, metrics, baselines |
| `C_Phase_C_Methodology/` | Simulation tools, the 14 scenarios, metric computation, baselines and ablations, run matrix, implementation roadmap with stage gates, statistical protocol, result-table templates |

## Key decisions

| ID | Decision |
|---|---|
| D-1 | "AI-driven" means a classical-AI core plus one gated learned policy |
| D-2 | Localization is assumed (shared global frame, bounded noise); no collaborative SLAM |
| D-3 | 2D semantic grid with a 2.5D height layer; 3D is an optional extension |
| D-4 | Crash-stop and omission faults only (no Byzantine faults) |
| D-5 | N ∈ {5, 10, 20}; 2 km × 2 km area; 10 m cells; T = 2400 s |
| D-6 / D-7 | Post-disaster search-and-rescue survey; synthetic, seeded worlds with exact ground truth |
| D-9 | Standard IEEE format and citation style |
| D-12 | CPU-only compute budget; the learned policy gets at most 48 CPU-hours of training |

Full decision records are in the Phase A report (§10, §12) and the Phase C plan (§0).

## Next steps

1. Read the full texts of the closest studies, then update the literature matrix and the related-work section.
2. Implement the simulator in the stages set out in Phase C §5. Each stage has a test gate.
3. Run the pre-registered experiments and fill in the Results section of the paper.

## History

Before 2026-11-23, this repository held an earlier Research 02 framing: self-healing *task allocation* (Steps 1–7, a LaTeX manuscript, and the `uavsim` simulator). That work was replaced by the current direction. It can still be recovered from commit `d112c3c`.
