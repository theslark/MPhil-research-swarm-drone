# Step 7: Manuscript (IEEE format)

**Title:** Self-Healing Task Allocation for Decentralized UAV Swarms under Intermittent Connectivity and Ambiguous Failures
**Type:** Methodology manuscript. **No experimental results.** Every result location is marked `[RESULTS PENDING]`.
**Date:** 2026-11-22

## Files
| Path | What it is |
|---|---|
| `latex/main.tex` | **Master manuscript** (IEEEtran, journal mode). Authoritative version |
| `latex/references.bib` | 82 verified references, generated from `02_Step2_Literature/Reference_Verification_Table.csv`; 59 are cited |
| `latex/figures/fig*.pdf` | Figures used by LaTeX (vector) |
| `latex/figures/fig*.svg / .png` | Editable sources and raster previews |
| `latex/figures/make_figures.py` | Regenerates all figures (Python standard library only) |
| `review_copy/Manuscript_Review_Copy.{docx,pdf,html}` | Single-column review copy for reading and commenting. **Not for submission** |
| `build_review_copy.py` | Rebuilds the review copy from `main.tex` (needs LibreOffice) |

## How to compile the IEEE version
LaTeX was not available on this machine, so **the LaTeX source has not been compiled yet**. It passed a static check:
- every `\cite` key exists in the bib (59/59);
- every `\ref` resolves;
- environments are balanced;
- there are no stray non-ASCII characters.

Easiest route: upload the whole `latex/` folder to **Overleaf**, set `main.tex` as the main document, and compile with pdfLaTeX. Locally:
```bash
cd latex
pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Packages used (all standard): IEEEtran, fontenc, cite, amsmath, amssymb, graphicx, booktabs, array, algorithm, algpseudocode, xcolor, url, hyperref.

Regenerate figures after editing `make_figures.py`:
```bash
cd latex/figures && python3 make_figures.py
soffice --headless --convert-to pdf fig1_overview.svg fig2_components.svg fig3_recovery.svg fig4_example.svg
soffice --headless --convert-to png fig1_overview.svg fig2_components.svg fig3_recovery.svg fig4_example.svg
```

## Manuscript structure (master prompt §14 → IEEE layout)
| Master prompt section | Manuscript |
|---|---|
| Abstract, Keywords | Abstract (241 words), Index Terms |
| Introduction, Background, Motivation, Problem statement | I. Introduction |
| Literature review, Research gap | II. Related Work and Research Gap (Table I) |
| Objectives and questions | III-E Research Questions and Hypotheses |
| Problem formulation, Mathematical formulation | III. Problem Formulation; IV-B ledger with Lemma 1, Propositions 1–2 and proofs |
| Proposed architecture | IV. Proposed Architecture (Figs. 1–4, Algorithms 1–2) |
| Methodology, Simulation, Experimental design, Evaluation framework | V. Experimental Design (Tables II–IV) |
| Results and discussion | VI. **Pending** (template Table V, figure list, interpretation plan) |
| Limitations, Future work, Conclusion | VII, VIII |

## Changes relative to Steps 5–6 (for consistency)
- **Notation:** combined suspicion is ψ (was φ̃); reassertion threshold is ρ_min (was ρ̄). Plain symbols render reliably in figures and Word.
- **Reassertion rule tightened:** a returning UAV reasserts only if ρ ≥ ρ_min **and** its progress strictly exceeds the current owner's. This prevents two live UAVs from repeatedly reclaiming the same task.
- **Assumption 2 (sufficient contacts)** added to make the delivery part of the convergence proof explicit.

## Before submission: checklist
- [ ] Fill in author names, affiliations, e-mail, acknowledgment (placeholders in `[...]`).
- [ ] Choose the target journal and adapt `\markboth`, length and any template differences.
- [ ] Run the experiments (Step 5 phases P1–P7) and replace every `\pending{...}` and Table V.
- [ ] Remove "methodology / results pending" statements from the abstract, introduction and `\thanks` once results exist.
- [ ] Full-text check of HMP [R41] and Chatterjee & Dutta [R42] (institutional access); confirmatory IEEE Xplore and Scopus searches (Step 2 §7).
- [ ] Re-check the novelty claim against any new 2026–2027 preprints (the field is moving fast; CC-OPI appeared Sept 2026).
- [ ] Compile on Overleaf; check figure sizes, table widths and the reference list.
- [ ] Note: R66 (CC-OPI), R67 (IRDS) and other arXiv entries are **not peer-reviewed**. Update them if they get published.
