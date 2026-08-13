---
name: amd-sim3466-method-source
description: "paper.pdf in the Sulfate-Methos repo root IS the full SIM 3466 method pamphlet - the source of truth for the land arm, easy to overlook"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0fc5c60d-44e9-423f-b015-759ff98e4182
  modified: 2026-07-26T17:27:02.739Z
---

`D:\dev\Sulfate-Methos\paper.pdf` is the **complete 47-page USGS SIM 3466
pamphlet** (Rockwell & Gnesda), not a summary or a preprint. It contains the
full method the land arm reimplements: the six index formulas (table 3), the
Boolean class-assignment logic (table 4), the masking rules, and the
thresholding procedure.

**Why this is worth recording:** it is easy to conclude the method is
undocumented. `data/rockwell/00Readme_L8_WesternUS.txt` ships with the raster
and gives *only* class names — no formulas, no thresholds — and the repo has no
`docs/` file pointing at paper.pdf. Before 2026-07-26 the project treated the
method as unavailable ("they never published the code"), which is true of the
code but **not** of the method.

Extraction: `pypdf` works (`pip install pypdf` into the repo `.venv`); the
Read tool cannot render it without poppler. Table 4's columns are garbled by
text extraction but readable — column order is
`[iron sulfate, ferric1, ferric2, ferrous, clay, green veg, NAP]`, where a
dash means NOT.

Consult it before changing any land-arm threshold, index, or mask. Three
"improvements" this project made turned out to be departures from it, all
regressions — see [[amd-land-thresholds-do-not-transfer]] and
`validation/REPLICA_AUDIT_2026-07-26.md`.
