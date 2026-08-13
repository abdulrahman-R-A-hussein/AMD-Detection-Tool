# PROJECT STATE — read this first

**Last updated:** 2026-08-10 · **Current tag:** `v3.0.7`

This file is the canonical "where are we right now". It is maintained under
the logging rule in [`../CLAUDE.md`](../CLAUDE.md). It should be sufficient to
resume from cold, with no chat history — if it isn't, it's incomplete and
should be fixed.

---

## Where the project stands in one paragraph

The **land arm** is a verified-faithful reimplementation of USGS SIM 3466: all
six index formulas match the paper exactly. Three departures this project had
introduced as "improvements" turned out to be regressions; fixing them improved
worst-case cross-site agreement 4.1×. The **water arm** was retracted in July
2026 and is being rebuilt as Phase 2 along three arms. The single most
promising result in the whole project is **Arm A** (watershed mineral loading
predicting measured stream chemistry), where our map outperformed Rockwell's
published map against real USGS chemistry — but at n=6 and p=0.136, so it is
suggestive, not proven. Raising that n is the current priority.

---

## PROVEN (with numbers)

### Land arm

- **Faithful replica at the index level.** All six SIM 3466 index formulas
  match exactly (`2/1−5/4`, `4/2`, `4/2×(4+6)/5`, `(3+6)/(4+5)`, `6/7−5/4`,
  `5/4`), as does first-match-wins class assignment. The dark mask constant
  0.2125 is an exact rescaling of Rockwell's 15,000 DN (nominal, not physical —
  L1 DN vs L2 SR are different quantities).
  → [`REPLICA_AUDIT_2026-07-26.md`](REPLICA_AUDIT_2026-07-26.md)
- **Three departures found and fixed (v3.0.0–v3.0.1).** Absolute thresholds
  instead of the paper's per-scene standard-deviation method (D1); Jul–Sep
  season, which the paper explicitly warns against (D2); a clay-free
  `hasIron → class 12` fallback with no counterpart in Rockwell's Table 4 (D3).
  Fixing all three plus relaxing the NDVI gate 0.25→0.35 took worst-case
  leave-one-site-out Youden J from **0.107 → 0.440 (4.1×)** and mean κ from
  0.139 → 0.257.
- **NAP ranks verified** from Table 4: `14=1, 12=2, 17=3, 18=4, 9=5, 19=6`
  (1 = highest net acid production).

### Water arm (Phase 2)

- **Ohio water column is a clean null, at double the earlier sample.**
  Matched dataset expanded 42 → 83 rows. No feature's 95% CI excludes zero for
  iron (n=17) or sulfate (n=23), while **turbidity is cleanly detected**
  (6 features, up to rho=0.499). The water arm sees sediment, not iron.
  → [`WATER_PHASE2_2026-08-10.md`](WATER_PHASE2_2026-08-10.md)
- **Catchment delineation works and is externally validated.** HydroSHEDS
  `NEXT_DOWN` reverse traversal, cross-checked against official USGS NWIS
  `drain_area_va`. Station 09359020 correctly aggregates its two upstream
  neighbours (204.9 sq mi, 1.40× NWIS / 1.39× MERIT).
- **Colorado chemistry is rich.** 17,062 water rows; **1,770 dissolved Fe**
  measurements (vs Ohio's 4), median 0.45 mg/L; mine-discharge source points
  median 6.2 mg/L, max 120 mg/L.

---

## SUGGESTIVE, NOT PROVEN — the current headline

**Arm A: our map predicts real dissolved Fe better than Rockwell's does.**

| | rho (ours, M1 AMD-area%) | rho (Rockwell M1) |
|---|---|---|
| dissolved Fe | **+0.714** | +0.257 |
| LOOCV R² | **+0.804** | −1.542 (worse than the mean) |

Scored against measured USGS chemistry — the only outcome variable in this
project that **neither map was fitted to**.

**Why it is not yet a result:** n = 6 catchments; exact permutation
p = **0.136** (computed over all 720 permutations, not approximated). Rockwell
shows a same-magnitude correlation with pH (rho = −0.714), so this is not
"their map has no signal". Sulfate and conductance show nothing for either map.

**n=6 is a real ceiling, not laziness:** 82 stations spanning genuinely
different sub-watersheds all collapsed into the same 6 `hybas_12` polygons.
Raising n requires **different river systems**.

---

## RETRACTED / DISPROVEN — do not cite these

- **The whole water contamination module (findings W1–W4, July 2026).** Indices
  ranked the *clean control* highest; the Ganau claim was circular.
  → [`WATER_VALIDATION_REPORT_2026-07-25.md`](WATER_VALIDATION_REPORT_2026-07-25.md)
- **Test C's 0.99-level threshold AUCs.** Silverton-only; collapse to 0.63–0.67
  pooled across three sites. **`FerrousIron` scores 0.437 — below chance, no
  AMD discriminative power at any site**, despite Test C's 0.983.
- **"Our tool is more sensitive than Rockwell's" (v2.7.0).** Withdrawn — the
  direction of disagreement *reverses* between sites (over-call 4.1× where
  thresholds were derived, under-call 5.6× at an independent site).
- **The green-peak vegetation gate as a cause of anything.** Falsified: it
  uniquely excludes 0 px at Summitville, 6 at Silverton, and moves worst-case J
  by ≤0.001 across a full 2-D NDVI × green-peak grid.
- **paper2's green:NIR applied to open water.** Degenerate — all water absorbs
  NIR, so it detects *water*, not sulfur. Retargeted to land-surface
  seep/precipitate pixels only.

---

## OPEN

Ordered by value.

1. **Raise Arm A's n from 6 toward 15–25** — the active task. Requires new
   river systems, not more Silverton stations. Verified available:
   Uncompahgre/Ouray (101 stations with ≥3 Fe samples), Alma/Fairplay (27).
   Unprobed: Lake City, Creede, Leadville, Clear Creek.
   **Must report pooled + per-region + leave-one-REGION-out.**
2. **Arm B2 — precipitate/seep detection.** Not built. `water_indices.py` has
   the paper2 indices correctly scoped; the extraction geometry around the 62
   identified mine-discharge/adit/spring stations is what's missing. This is
   where finding W4 predicts a positive result actually lives.
3. **Colorado B1 stream matching.** Zero matches so far. One bug fixed (width
   screen dropped on *missing* MERIT data, not confirmed narrowness); one open
   — the lake-calibrated water mask returns nothing even on the wide Animas
   mainstem across 6 dates. Needs a hand check of actual pixel values before
   concluding streams are undetectable.
4. **Arm C — vegetation NDVI stress proxy.** Not built. Needs a permutation
   null from the start or it will repeat finding W2.
5. **Resolution-degradation curve.** Blocked on B1/B2 finding something
   detectable to degrade. Would quantitatively reproduce paper2's "Sentinel-2
   resolved 3 of 6 leaks" — the published justification for a 7 cm drone.
6. **Uncalibrated classifier constants.** `ferric1StdMult`, `ferric2StdMult`,
   `ferrousStdMult` are all set to 0.5 *by assumption*; only iron and clay were
   LOSO-fitted. They drive classes 1–8, which nothing has validated.
   `clayStdMult` did not transfer cleanly (per-fold fits −0.5, −0.5, +1.0).
7. **Red Mountain Pass regression** under v3.0.x (J 0.642→0.452) — rests on
   19–23 positive pixels. Compositing (D8) was the prime suspect and is largely
   ruled out; small-sample noise is now the leading explanation.
8. **Departures D4, D5, D6** (class 9/17 split uses brightness where Rockwell
   uses ferrous; water mask; atmospheric correction) remain unmeasured.

---

## KNOWN TRAPS

- **Two venvs.** GEE work needs `D:/dev/VPCA+STEPWISE-REGRESSION/.venv`
  (`ee` + `rasterio`); the repo `.venv` has no `ee`. Cost a wasted run already.
- **EE "User memory limit exceeded" is about compute-graph size, not pixel
  count** — `bestEffort=True` does not help. Fix by tiling the reducer
  (`tile_geoms` + `tiled_mean_stddev`) and materialising stats to Python floats
  so downstream calls don't re-evaluate them.
- **WQP's `siteType` filter parameter uses a narrower vocabulary than
  `MonitoringLocationTypeName`** and returns HTTP 400 on real values like
  `"River/Stream"` or `"Mine/Mine Discharge Adit"`. Fetch unfiltered, exclude
  locally. The naive filter silently cost 66% of Colorado's iron data.
- **`hybas_12` has a granularity floor** (~35–95 sq mi near Silverton) that
  merges Cement Creek — one of the most acidic tributaries — with cleaner
  water. This biases Arm A **toward the null**, so the true effect may be
  stronger than measured. Do not use it to explain away a null.
- **Transient network failures** killed two runs in one session. Structure long
  jobs per-region so a failure costs one region, not the batch.
- **`data/` is gitignored.** Anything in it must be regenerable from committed
  code; record the exact command in the report that uses it.
