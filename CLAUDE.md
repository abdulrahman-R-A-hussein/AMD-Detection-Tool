# AMD Detection Tool — project instructions

Acid/coal mine drainage (AMD/CMD) detection from satellite imagery.
**Land arm** reimplements USGS SIM 3466 (Rockwell & Gnesda 2021) in Earth
Engine — the paper published a method and a result raster but never released
code. **Water arm** is Phase 2, currently in progress. Author: Abdulrahman
Hussein, Kent State (Dr. Joseph D. Ortiz lab). Purpose: preliminary data and
methodology for a PhD grant application.

## Read this first

**→ [`validation/STATE.md`](validation/STATE.md) is the canonical current
state.** Read it before doing anything else. It says what is proven, what is
retracted, what is open, and what to do next. Everything else in this file is
rules that don't change; `STATE.md` is the part that does.

## THE LOGGING RULE — non-negotiable

Every session that produces a finding must, **before it ends**:

1. append the finding to a dated report in `validation/` — with its numbers,
   its **n**, and its caveat;
2. update `validation/STATE.md` (proven / retracted / open / next);
3. add a row to `validation/DECISION_LOG.md` — the chronological journey:
   what was asked, what was done, what happened, what was decided, and **why**.
   `STATE.md` says where we are; `DECISION_LOG.md` says how we got here, wrong
   turns included. A phase that produced a null or a retraction gets the same
   detail as one that produced a positive;
4. mirror any plan used into `docs/plans/` (machine-local plan files do not
   survive a reinstall; the repo copy does);
5. commit and push.

> **A finding that exists only in chat does not exist.**

This project has already lost a chat once. Chat is not storage. The repo is
pushed to `github.com/abdulrahman-R-A-hussein/AMD-Detection-Tool`, which is the
only surface that survives both chat deletion and machine loss.

## Science rules — each learned by getting it wrong

- **Never judge a threshold by within-site AUC.** Use cross-site worst-case
  (leave-one-site-out, or leave-one-region-out). Test C's 0.99-level AUCs were
  Silverton-only and did not transfer at all — they collapsed to 0.63–0.67
  pooled, and `FerrousIron` fell to 0.437 (below chance). Finding **L1**.
- **Never put an absolute cutoff on a non-normalised index.** The same defect
  broke the water mask (`AWEINSH > 0.20`, tuned at Ganau, excluded 100% of
  Piedmont's water) *and* the land thresholds. Use per-scene statistics —
  which is what SIM 3466 itself specifies ("a common standard deviation
  threshold").
- **Sulfate has no VNIR absorption.** Never claim optical sulfate detection at
  any concentration. Any apparent signal is iron, turbidity, or colour that
  co-varies with sulfate — word it that way.
- **Rockwell's map is a published *automated* classification, not ground
  truth.** Agreement with it measures replica fidelity, never accuracy. Only
  measured field chemistry is ground truth. Keep those two claims separate.
- **Always report n and the caveat** next to any rho / R² / AUC. Small-n
  results get an exact permutation p-value, not a hand-wave.
- **Over grouped data, report the between/within variance split next to any
  pooled correlation, and correct for multiple comparisons.** The pooled
  sulfate result (rho = −0.563, p = 0.001) *reversed sign* to +0.220 once
  region effects were removed — it was 67.5% between-region variance, i.e.
  comparing river systems rather than testing the relationship. Learned
  2026-08-13; see `validation/ARM_A_CROSS_REGION_RETEST_2026-08-13.md` Part 2.
- **Never test a hypothesis on the data that generated it.** If a grouping or
  cutoff was chosen by looking at the outcome, any p-value from it is
  meaningless. Say so and state what would actually test it.
- **A null or a collapse is a valid, publishable result** and gets reported as
  prominently as a positive would. Do not bury it.

## Environment foot-gun

Two virtualenvs, and the split is not obvious:

| need | interpreter |
|---|---|
| Earth Engine (`ee`) — **and** `rasterio` | `D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe` |
| `rasterio`, pandas, no `ee` | `.venv/Scripts/python.exe` (repo-local) |

Anything touching GEE must use the VPCA venv. The repo venv will fail with
`ModuleNotFoundError: No module named 'ee'`. The VPCA venv has both, so when in
doubt use it. GEE auth is a service account at
`D:/dev/VPCA+STEPWISE-REGRESSION/planty-gee-backend-*.json` (gitignored; never
print or commit its contents).

## Repo layout

- `validation/` — **the log.** Dated reports, one per investigation, plus
  `STATE.md` and `README.md` (the running validation log).
- `python/` — analysis pipeline. Reuse what's there; most of it is de-risked
  and carries its rationale in module docstrings.
- `earth-engine/amd_detection_v2.4.0.js` — the shipped GEE tool (filename says
  2.4.0, contents are v3.0.x; see `STATE.md`).
- `docs/plans/`, `docs/memory/` — mirrors of otherwise machine-local session
  artefacts. **The repo copy is authoritative on conflict**, since it is the
  one that survives.
- `paper.pdf` — the full 47-page SIM 3466 pamphlet (the method source of
  truth). `paper2.pdf` — Galaszkiewicz et al. 2024, green:NIR sulphurous-water
  detection.
- `data/` — **gitignored.** Everything in it must be regenerable from
  committed code; record the exact command in the report that uses it.
