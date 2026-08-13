# Next phase: make continuity permanent, then strengthen the Arm A result

## Context

Two separate needs, deliberately sequenced continuity first because it is cheap
and it is the thing that protects everything else.

**1. Continuity is not actually durable yet.** This project began with the user
losing a chat by accident, and the request now is explicit: *"even if we delete
the chat between us you always can know."* Current state:

| surface | survives chat delete | survives machine loss |
|---|---|---|
| `validation/*.md` (7 docs, git → GitHub) | yes | yes |
| memory dir (`C:\Users\ahusse12\.claude\projects\...`) | yes | **no** |
| plan file (`C:\Users\...\.claude\plans\`) | yes | **no** |
| repo-root `CLAUDE.md` | — | **does not exist** |

The user's own *global* rules already say "check the current project's own
`CLAUDE.md`" — but this project has never had one, so the auto-loaded entry
point every future session would look for is missing. There is also no single
"where are we right now" doc; resuming means reading 7 separate dated reports.

**2. The one promising result needs its n raised before anything is built on
it.** Arm A found our v3.0.x map predicts measured dissolved Fe better than
Rockwell's published map (rho +0.714 vs +0.257; LOOCV R² +0.804 vs −1.542),
scored against real USGS chemistry neither map was fitted to — the only
ground-truth-validated result in the project. But **n=6 catchments, exact
permutation p=0.136**: suggestive, not significant. It is the natural grant
headline and it is currently one bad-luck draw from being noise.

n=6 was verified to be a real ceiling *within the Silverton search area*: 82
stations spanning genuinely separate sub-watersheds all collapsed into the same
6 `hybas_12` catchments. Raising n therefore requires **different river
systems**, not more stations near Silverton.

**Verified feasible before committing to this plan** (WQP probe, 2026-08-10):
Uncompahgre/Ouray has 134 stations (**101 with ≥3 Fe samples**), Alma/Fairplay
31 (**27 with ≥3**). Both drain different systems from the Animas (Gunnison and
Arkansas headwaters respectively), so they are guaranteed distinct basins and
cannot collapse into the existing 6. Lake City, Creede, Leadville and Clear
Creek probes hit transient network errors and are unmeasured but likely
similar — Colorado Mineral Belt mining districts with long monitoring records.

---

## Part A — Make continuity permanent (do first)

Everything below goes **in the repo**, which is pushed to
`github.com/abdulrahman-R-A-hussein/AMD-Detection-Tool`, so it survives both
chat deletion and machine loss and is restorable by anyone on any machine.

### A1. `CLAUDE.md` at repo root (new) — the auto-loaded entry point

Claude Code loads this automatically in every future session in this project.
Keep it short and high-signal; it is context tax on every single session.
Contents:

- One-paragraph project statement (AMD/CMD detection, land arm reimplements
  SIM 3466, water arm is Phase 2).
- **Pointer to `validation/STATE.md` as the canonical current state**, read
  first, before anything else.
- **The hard-won science rules**, stated as rules, because each one was
  learned by getting it wrong:
  - Never judge a threshold by within-site AUC; use cross-site worst-case
    (leave-one-site-out). This is finding L1 — Test C's 0.99 AUCs did not
    transfer at all.
  - Never use an absolute cutoff on a non-normalised index. Same defect broke
    the water mask (`AWEINSH>0.20` at Ganau) and the land thresholds.
  - Sulfate has no VNIR absorption — never claim optical sulfate detection.
  - Rockwell's map is a published *automated* product, not ground truth.
    Agreement with it ≠ accuracy. Only field/measured chemistry is ground truth.
  - Always report n and the caveat alongside any rho/R².
- **THE LOGGING RULE** (the user's actual ask), stated explicitly:
  > Every session that produces a finding must, before it ends:
  > 1. append the finding + its numbers + its n + its caveat to a dated report
  >    in `validation/`;
  > 2. update `validation/STATE.md` (what's proven / disproven / open / next);
  > 3. commit and push.
  > A finding that exists only in chat does not exist.
- Interpreter note (the recurring foot-gun): EE work needs
  `D:/dev/VPCA+STEPWISE-REGRESSION/.venv` (has `ee` **and** `rasterio`); the
  repo `.venv` has `rasterio` but **not** `ee`.

### A2. `validation/STATE.md` (new) — canonical "where are we"

One file to read to resume cold. Sections: current version/tag · what is
PROVEN (with numbers) · what is DISPROVEN/RETRACTED · what is OPEN · immediate
next steps · known traps. Written so a reader who has never seen the chat can
pick up. This is the file the logging rule keeps current.

### A3. Mirror machine-local artefacts into the repo

- `docs/plans/` ← copy of the active plan file (this document).
- `docs/memory/` ← copy of the 5 memory notes + `MEMORY.md` index.

Both are copies, not moves — the live memory dir keeps working as the fast
recall layer; the repo copy is the durable backup. Note in `CLAUDE.md` that
they are mirrors and which direction is authoritative (repo wins on conflict,
since it is the one that survives).

---

## Part B — Strengthen Arm A (n = 6 → target 15–25)

### B1. Add the new regions

`python/fetch_wqp.py` already has the `REGIONS` bbox mechanism, the
unfiltered-fetch + `EXCLUDE_SITE_TYPES` local filtering fix, and Iron unit
normalisation. Add entries for: **Uncompahgre/Ouray** and **Alma/Fairplay**
(both verified), plus **Lake City/Lake Fork**, **Creede**,
**Leadville/California Gulch**, **Clear Creek/Central City** (probe first —
retry the failed network calls; drop any that turn out to be thin).

Fetch each to `data/chemistry/<region-slug>/`.

### B2. Run the existing Arm A pipeline per region

`python/watershed_nap.py` needs only a generalised `--region` (it currently
hard-codes `colorado`/`ohio` → chem dir). Everything else already works and is
already de-risked: `NEXT_DOWN` traversal, geometry `simplify(30)`,
`tiled_mean_stddev()`, 16-way tiled histograms, Rockwell raster zonal stats.

Rockwell's raster covers all of these (western US), so **the head-to-head is
available in every new region** — not just Colorado.

### B3. Pool and re-test, with the L1 lesson applied

This is the part that must not be rushed, because pooling across regions
introduces between-region confounds (different geology, climate, illumination,
scene availability) that could manufacture a correlation as easily as reveal
one.

- Report **pooled**, **per-region**, and **leave-one-REGION-out** — not just
  leave-one-catchment-out. A result that only survives pooling is not a result.
- Recompute the **exact permutation p-value** at the new n (the existing
  720-permutation exact computation only works to n≈8; above that switch to a
  large random permutation sample, e.g. 100k, and say which was used).
- Keep the three loading models (M1 AMD-area%, M2 NAP-weighted, M3 per-class)
  and keep reporting all three — M3 overfitting at small n is exactly what
  cross-validation is there to expose.
- Report our map vs Rockwell's map side by side, as now.

### B4. Record the known bias honestly

`hybas_12`'s granularity averages Cement Creek (one of the most acidic
tributaries in the Animas) together with cleaner water sharing its polygon.
That biases any true association **toward the null**, i.e. the measured effect
may understate the real one. State this in the write-up; do not use it to
explain away a null if one appears.

---

## Critical files

| File | Change |
|---|---|
| `CLAUDE.md` | **new**, repo root — auto-loaded entry point + logging rule |
| `validation/STATE.md` | **new** — canonical current state |
| `docs/plans/`, `docs/memory/` | **new** — mirrors of machine-local artefacts |
| `python/fetch_wqp.py` | add ~4–6 `REGIONS` entries |
| `python/watershed_nap.py` | generalise `--region`; add pooled + per-region + leave-one-region-out reporting; permutation p at larger n |
| `validation/WATER_PHASE2_2026-08-10.md` | append Part B results |

**Reuse, do not rewrite** (all built and de-risked this session):
`catchment_delineation.delineate()` (`NEXT_DOWN` traversal + NWIS/MERIT
cross-check), `gee_classify.tiled_mean_stddev()` / `classify_v3()`,
`diagnose_veg_gate.tile_geoms()`, `watershed_nap.classify_catchment_rockwell()`
and `loading_metrics()`, `fetch_wqp.normalize_iron_value()`.

## Verification

1. **`CLAUDE.md` actually loads** — confirm it appears in project context at
   the start of the next session (that is the whole point of A1).
2. **`STATE.md` is sufficient alone** — sanity check: could someone resume from
   `STATE.md` + the repo, with no chat history? If not, it is incomplete.
3. **Catchment sanity per new region** — every delineated catchment
   cross-checked against MERIT `upa`, and against NWIS `drain_area_va` wherever
   a USGS gauge exists (`catchment_delineation.py --self-test` pattern).
   Reject and report failures rather than silently including them.
4. **n actually increased** — count *distinct* catchments, not stations. If
   the new regions still collapse, say so and stop.
5. **The headline survives, or it doesn't** — report pooled + per-region +
   leave-one-region-out + permutation p. **A collapse at higher n is a valid
   and important outcome and must be reported as prominently as a confirmation
   would be.**
6. Commit and push at each milestone (Part A, then each region, then the
   pooled result), per the logging rule being established.

## Risks

- **The result may not survive n>6.** That is the point of running it. If it
  collapses, the honest finding is "the n=6 signal was noise", and the project
  is better off knowing before a grant application is written on it.
- **Between-region confounds** could create a spurious pooled correlation —
  mitigated by mandatory per-region and leave-one-region-out reporting.
- Some probed regions may be too thin, or their stations may cluster into few
  basins. Mitigation: probe before fetching; drop thin regions; report actual
  distinct-catchment counts.
- Transient EE/WQP network failures killed two runs this session already. Keep
  runs per-region so a failure costs one region, not the whole batch.
- `CLAUDE.md` is context tax on every future session — keep it tight, and put
  detail in `STATE.md` (read on demand) rather than inlining it.
