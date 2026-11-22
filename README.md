# Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity and Ambiguous Failures

MPhil research (Advanced Research Methodology): a methodology paper with its full research record.

> **Status:** design and evaluation protocol complete; **experiments not yet run**.
> The manuscript contains no experimental results. Every place that needs data is marked **[RESULTS PENDING]**.

## The research in brief

UAV swarms used for search and rescue lose contact with their members for two different reasons: drones fly out of range, or drones crash. To the rest of the swarm the two cases look identical, because a peer has simply gone silent.

- **Reassign its tasks too early** and work is duplicated, and mission state conflicts when the drone returns.
- **Reassign too late** and the tasks of a crashed drone go unserved.

**Research gap:** existing decentralized allocators handle either network partitions (e.g., CC-OPI) or known failures (e.g., IRDS, ES-CBBA), but not the ambiguity between the two. None of them measures the resulting trade-off between recovery time and duplicated work.

**Proposed design:**
- **Mission ledger:** a CRDT-based ledger on every UAV that converges after partitions and after wrong failure suspicions (with proofs).
- **Suspicion estimator:** a plan-aware accrual detector that grades how strongly a silent peer is suspected.
- **Takeover policy:** a threshold rule, or a MAPPO policy trained centrally and executed decentrally, that decides when to claim a suspected peer's task.
- **Base allocator:** event-driven asynchronous CBBA within each connected group.

**Evaluation plan (pre-specified):** a Python simulation with
- 11 scenarios;
- 7 methods, including centralized, CBBA, CC-OPI and greedy baselines;
- 10 ablations;
- 5 hypotheses (H1–H5) tested with paired Wilcoxon tests, Holm correction and Kaplan–Meier analysis.

## Repository structure

| Folder | Contents |
|---|---|
| `01_Step1_Feasibility/` | Critical evaluation of the original concept, technical challenges, accepted scope |
| `02_Step2_Literature/` | Literature review and research gap, **reference verification table (82 references)**, search log, raw search exports |
| `03_Step3_Title_and_Scope/` | Refined title, exact scope, objectives, research questions, hypotheses |
| `04_Step4_Algorithm_Selection/` | Comparison and selection of MARL algorithms, allocator, failure detection, CRDTs, communication, leader election |
| `05_Step5_Architecture_and_Methodology/` | Architecture (Mermaid diagrams), mathematical formulation, pseudocode, phased implementation plan |
| `06_Step6_Experimental_Design/` | Parameters, scenario matrix, baselines and ablations, metric formulas, statistical analysis plan |
| `07_Step7_Manuscript/` | The manuscript (see below) |

## Manuscript files

| File | Use |
|---|---|
| `07_Step7_Manuscript/latex/main.tex` + `references.bib` + `figures/` | **Master source** (IEEEtran, journal mode) |
| `07_Step7_Manuscript/ieee_word/Manuscript_IEEE.docx` | IEEE-format Word version (two-column) |
| `07_Step7_Manuscript/ieee_word/Manuscript_IEEE_preview.pdf` | Preview of the Word version |
| `07_Step7_Manuscript/review_copy/Manuscript_Review_Copy.{docx,pdf}` | Single-column copy for reading and commenting |

Both Word files are **generated from `main.tex`**, and rebuilding overwrites them. Details and a pre-submission checklist are in [`07_Step7_Manuscript/README.md`](07_Step7_Manuscript/README.md).

## Building

```bash
# IEEE PDF: upload 07_Step7_Manuscript/latex/ to Overleaf, or locally:
cd 07_Step7_Manuscript/latex
pdflatex main && bibtex main && pdflatex main && pdflatex main

# Figures (Python standard library + LibreOffice for SVG -> PDF/PNG)
cd figures && python3 make_figures.py
soffice --headless --convert-to pdf *.svg && soffice --headless --convert-to png *.svg

# Word versions (from 07_Step7_Manuscript/; needs LibreOffice)
python3 build_ieee_docx.py      # -> ieee_word/
python3 build_review_copy.py    # -> review_copy/
```

## Research integrity

- **References:** every reference was checked against Crossref, arXiv or the publisher page (`02_Step2_Literature/Reference_Verification_Table.csv`). The table records how much of each paper was actually read: metadata, abstract or full text.
- **Preprints:** arXiv entries (e.g., CC-OPI, IRDS) are marked as not peer-reviewed.
- **Results:** none are reported or implied. Hypotheses and decision rules were fixed before any experiment.
- **Known limits:**
  - the literature search used Crossref, arXiv and web search, not Scopus or IEEE Xplore;
  - several works were assessed at abstract level only;
  - two papers (HMP, Chatterjee & Dutta) still need a full-text check.

## Next steps

1. Fill in author names and affiliations (placeholders in `main.tex`).
2. Complete the confirmatory literature searches and full-text checks (Step 2, §7).
3. Implement the simulator and run phases P1–P7 (Step 5, §3).
4. Run the experiments, then replace every `[RESULTS PENDING]` block.
5. Choose the target journal and submit.
