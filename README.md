# A Decentralized Framework for Collaborative Mapping and Resilient Coordination in UAV Swarms under Intermittent Connectivity

MPhil research (Advanced Research Methodology), Department of Information Technology, Lahore Leads University.

- **Author:** Sohail Ishaque (MPhil Scholar)
- **Supervisors:** Dr. Pervez Husnain (first), Dr. Khalid (second)

> **Status:** The framework and research design are complete. The simulator is being built.
> **No experiments have been run yet.** The Results section of the paper is a "pending" template, and no numerical result is claimed.

## The research in brief

UAV swarms used for search and rescue often lose radio contact with each other. When that happens, drones keep mapping on their own, so their maps drift apart. A silent drone may be out of range rather than broken. If a drone is lost, its unfinished tasks and areas still need to be covered.

The paper proposes a decentralized framework with four parts:

- **Collaborative mapping:** each UAV keeps its own copy of a 2D grid map. Each cell records the observation, its confidence, its time and the UAV that made it.
- **Information sharing:** UAVs exchange only the updates the other is missing, with urgent ones (victims, hazards) first. They merge maps using CRDT principles, so receiving the same update twice, or in a different order, gives the same result. Updates can also be carried and passed on at a later contact (store-carry-forward).
- **Task allocation:** tasks (survey, re-check, verify) are created from the map. A temporary coordinator may assign them, but there is no permanent central controller.
- **Failure recovery:** heartbeats and peer checks separate "temporarily unreachable" from "likely failed" (ALIVE, UNREACHABLE, SUSPECTED-FAILED, REJOINED). Recovery reassigns unfinished tasks and re-surveys areas the failed UAV left incomplete.

Machine learning is optional: a learned task selector is kept only if it performs at least as well as the rule-based one.

**Evaluation plan:**
- a custom Python simulator (NumPy, NetworkX, Matplotlib);
- 5, 10 and 20 UAVs; 2 km × 2 km area with 10 m cells; 40-minute missions; 300 m radio range;
- 14 scenarios, covering outages, partitions, environmental change, UAV and coordinator failures, joining and rejoining;
- baselines B0–B3, the proposed method P, and 7 ablations;
- 5 comparisons fixed in advance, summarized with confidence intervals and paired tests.

## Repository structure

| Path | Contents |
|---|---|
| `Research_paper_revised.docx` | **The revised paper** (IEEE style): sections I–VIII, 2 figures, 11 tables, 25 references |
| `Research paper revised - slides.pptx` | Simple 11-slide presentation of the revised paper |
| `Research paper - slides.pptx` | Earlier slide deck, made for the previous paper draft |
| `A_Phase_A_Research_Validation/` | Research validation report, literature review matrix, reference verification table, search log and raw search exports |
| `B_Phase_B_Research_Design/` | Problem statement, research questions and hypotheses, assumptions, architecture, mathematical model, pseudocode, metrics, baselines |
| `C_Phase_C_Methodology/` | Simulation tools, the 14 scenarios, metrics, baselines and ablations, run matrix, implementation roadmap, statistical protocol, result-table templates |

The Phase A–C reports were written for the earlier, more detailed draft. Where they differ from the revised paper, the revised paper is the current version.

## Key decisions

| ID | Decision |
|---|---|
| D-1 | Rule-based core; a learned task-selection policy is optional and kept only if it performs well |
| D-2 | UAV positions are assumed known; no collaborative SLAM |
| D-3 | 2D grid map; 3D mapping is future work |
| D-4 | Accidental disconnection and permanent failure only (no malicious/Byzantine behaviour) |
| D-5 | N ∈ {5, 10, 20}; 2 km × 2 km area; 10 m cells; 40-minute missions |
| D-6 / D-7 | Post-disaster search-and-rescue survey; generated worlds with known ground truth |
| D-9 | Standard IEEE format and citation style |

## Next steps

1. Build the simulator in the paper's 7 stages (about 17 weeks, plus 3 optional weeks for the learned policy). Each stage has a check that must pass.
2. Run the 14 scenarios against the baselines and ablations.
3. Fill in the Results section of the paper and report its limitations.

## History

- **2026-11-27:** The paper was simplified and replaced by `Research_paper_revised.docx`, with a matching simpler slide deck. The earlier draft (`Research paper.docx`) can be recovered from commit `e2d18ba`.
- **Before 2026-11-23:** This repository held an earlier Research 02 framing: self-healing *task allocation* (Steps 1–7, a LaTeX manuscript, and the `uavsim` simulator). It can be recovered from commit `d112c3c`.
