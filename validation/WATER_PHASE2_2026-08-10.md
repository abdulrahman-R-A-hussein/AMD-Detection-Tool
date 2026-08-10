# Water Phase 2 — session log, 2026-08-10

**Status: IN PROGRESS.** This file is being built up as each piece completes;
treat any section marked `[PENDING]` as not yet run. Plan:
`C:\Users\ahusse12\.claude\plans\1-lets-do-the-fizzy-river.md` (also copy this
into the repo once finalised, per project practice of keeping plans alongside
validation output).

Full context: [validation/REPLICA_AUDIT_2026-07-26.md](REPLICA_AUDIT_2026-07-26.md)
(land arm, done), [WATER_VALIDATION_REPORT_2026-07-25.md](WATER_VALIDATION_REPORT_2026-07-25.md)
(water arm retraction, findings W1-W4).

## 0. Literature anchors

- **SIM 3466 (`paper.pdf`)** masks water out entirely (band 1/6 ratio) - no
  water-column method to adapt. But p.3: mineral mapping exists for
  "developing predictive models of downstream surface water geochemistry",
  and Table 4 assigns every AMD class a NAP rank. This is Arm A's mandate.
- **Galaszkiewicz, Delaney & Steelman (2024), Geomatica 76, 100024**
  (`paper2.pdf`) - green:NIR band ratio for sulphurous water discharge from
  legacy O&G wells. **Retargeted before use**: their ratio is degenerate on
  open water (every water pixel absorbs NIR and scores high), so it is scoped
  to land-surface seep/precipitate pixels only (`python/water_indices.py`
  docstring). Independent finding worth keeping in mind: they report
  Sentinel-2 (10 m) resolved only 3 of 6 known leaks, concluding 0.16 m aerial
  imagery is "the most viable choice" - the same resolution wall this
  project's W4 finding predicted, from an unrelated group and dataset.

## 1. Pre-execution verification (before any GEE compute was spent)

Two plan assumptions were checked and found wrong; one literature claim was
checked and found to need retargeting. Full detail in the plan file's
"Verification findings" section.

1. **NAP ranks** - verified from Table 4: `14=1, 12=2, 17=3, 18=4, 9=5, 19=6`.
2. **A hybas_12 polygon is a sub-basin, not an upstream catchment.** The
   original plan said "start with hybas_12 basins"; corrected to traversing
   the `NEXT_DOWN` graph (§3 below).
3. **paper2's green:NIR is degenerate on open water** - retargeted to
   land-surface seep/precipitate pixels (Arm B split into B1 water-column /
   B2 precipitate, never conflated).

## 2. Colorado water chemistry (Phase 0)

Code: `python/fetch_wqp.py --region "Silverton, CO"`.

**Two real bugs found and fixed while building this, not after:**

- WQP's `siteType` FILTER parameter is a small fixed domain, DIFFERENT from
  and narrower than `MonitoringLocationTypeName`. It rejects (HTTP 400) real
  values like `"River/Stream"`, `"Reservoir"`, `"Mine/Mine Discharge Adit
  (Mine Entrance)"`. A naive filter silently returned only 3,844 Iron rows;
  fetching unfiltered and excluding junk locally (`EXCLUDE_SITE_TYPES`)
  recovered **11,410 Iron rows**, including 62 mine-discharge/adit/spring
  source-point stations - exactly the highest-concentration AMD samples.
- `consolidate()`'s `fieldnames` was captured from whichever row happened to
  be processed first. When that row wasn't an Iron characteristic, the
  `Iron_mgL` unit-normalised column was silently dropped from every row
  (`extrasaction="ignore"`) - confirmed missing from Ohio's `consolidated.csv`
  while present in Colorado's, purely from file/row iteration order. Fixed:
  fieldnames is now the union across every row, not the first one seen.
  **Ohio's Iron_mgL is now correctly populated (191/216 rows) where it was
  silently empty before this fix.**

**Result:** 17,062 water rows (157 sediment rows split into
`consolidated_sediment.csv`, never pooled). Iron: 3,981 rows, 1,770 with
`ResultSampleFractionText=Dissolved` (median 0.45 mg/L, max 99.7 mg/L) versus
Ohio's 4 total dissolved measurements. Mine-discharge/spring source points:
174 rows, median 6.2 mg/L, max 120 mg/L.

## 3. Catchment delineation (Phase 0)

Code: `python/catchment_delineation.py --self-test`.

Traverses HydroSHEDS `hybas_12`'s `NEXT_DOWN` graph in reverse (BFS) to build
true upstream catchments, bounded by a local buffer around the station rather
than the whole river system (`MAIN_BAS` scoping blew the EE 5000-element
`getInfo` ceiling - the Animas is part of the Colorado River basin, tens of
thousands of sub-basins).

**Verified against OFFICIAL USGS NWIS drainage areas** (real ground truth,
`drain_area_va`, not another remote-sensing product) at 6 Animas-watershed
gauges:

| site | NWIS sq mi | ours sq mi | ratio | n_basins |
|---|---|---|---|---|
| 09357500 Howardsville | 55.9 | 91.7 | 1.64x | 1 |
| 09358000 Silverton | 70.6 | 91.7 | 1.30x | 1 |
| 09358500 Cement Ck | 13.5 | 91.7 | 6.79x | 1 |
| 09358900 Mineral Ck | 11.0 | 51.9 | 4.72x | 1 |
| 09359000 Mineral Ck (lower) | 44.3 | 51.9 | 1.17x | 1 |
| 09359020 Animas blw Silverton | 146.0 | 204.9 | 1.40x | 3 |

**Traversal mechanism verified correct**: 09359020's catchment correctly
aggregates its two upstream neighbours via `NEXT_DOWN` (204.9 sq mi, matching
the hand-computed sum, 1.40x NWIS / 1.39x MERIT).

**Real finding, not a bug**: `hybas_12` has a granularity floor here
(~35-95 sq mi) that merges Howardsville / Silverton / Cement Creek into ONE
shared polygon despite very different true drainage areas (55.9/70.6/13.5 sq
mi) and very different AMD character - Cement Creek is one of the most acidic
tributaries in the watershed. Stations sharing a polygon are deduplicated into
one catchment row in Arm A (pooled chemistry), per the plan's stated risk
("count distinct catchments, not stations"). Upgrade path if this granularity
turns out to matter: true DEM flow-accumulation from MERIT Hydro `dir`.

## 4. Arm A - watershed NAP head-to-head [PENDING - run in progress]

Code: `python/watershed_nap.py --region colorado`.

Two EE performance bugs found and fixed while building this (both are the
same class of problem the plan's Phase-0 caution was meant to catch, just one
layer deeper than catchment delineation):

- `classify_v3`'s scene-relative threshold computation was a single
  whole-catchment `reduceRegion(mean+stdDev)`, which alone tripped "User
  memory limit exceeded" on a modest 237 km2 catchment - even with
  `bestEffort=True` and a simplified geometry. That error is about EE's
  *server compute-graph size*, not pixel count, so `bestEffort` (which only
  mitigates pixel-count overruns) did not help.
- Fixed by tiling the stats computation itself (`tiled_mean_stddev()`):
  compute sum/sumSq/count per tile via the SAME `tile_geoms` pattern already
  proven for the histogram step, then pool mean/variance algebraically in
  Python. Verified end-to-end on the failing catchment after the fix: 130
  scenes, 334,876 classified pixels, full class histogram produced.

[RESULTS TO BE FILLED IN]

## 5. Arm B - direct optical detection [PENDING]

### B1 - water column

Code: `python/match_scenes.py`, `python/detection_limit.py`.

Ohio matched dataset expanded from 42 rows (all 3,023 available consolidated
rows now attempted, not the earlier subset). [RESULTS TO BE FILLED IN]

Colorado matched dataset: [NOT YET RUN - stream stations need the
`--min-width-m` MERIT Hydro screen added this session before matching, since
most Animas tributaries are narrower than a Sentinel-2 pixel].

### B2 - precipitate/seep [NOT BUILT THIS SESSION]

`python/water_indices.py` implements the paper2 indices (`GreenNIR`,
`GreenNIRNorm`) correctly scoped to land-surface pixels, but the extraction
pipeline (identify shoreline/streambed/adit-outflow pixels near a known
discharge point, sample them, correlate with chemistry) was not built this
session - it needs its own spatial design distinct from `match_scenes.py`'s
water-window sampling, and building it under time pressure risked the same
kind of un-verified assumption this session repeatedly caught elsewhere.
Logged as the top Arm B next step.

## 6. Arm C - vegetation NDVI proxy [NOT BUILT THIS SESSION]

Deliberately deferred - it is the highest-risk arm in the plan (many causes
of vegetation stress) and requires a permutation-null harness to be
trustworthy at all. Building it without that harness would repeat finding W2
(5-band material ID fits anything with few observations). Next-session item.

## 7. Resolution-degradation curve [NOT BUILT THIS SESSION]

Depends on Arm B finding something detectable to degrade (plan sequencing,
Phase 3). Deferred until B1/B2 results are in.

## What to do next session

In priority order:
1. Finish reading Arm A's results once the run completes; write the
   head-to-head verdict (does either map predict measured chemistry, and if
   so does ours or Rockwell's do it better).
2. Run Colorado B1 (water column) via `match_scenes.py --chem
   data/chemistry/silverton_co/consolidated.csv --min-width-m 12` (or similar)
   now that width screening exists.
3. Build B2 (precipitate/seep extraction) - needs a defined sampling geometry
   around known discharge points (the 62 mine-discharge/adit/spring stations
   already identified are the natural target list).
4. Arm C, with a permutation null from the start.
5. Resolution-degradation curve, once B1/B2 give something to degrade.
