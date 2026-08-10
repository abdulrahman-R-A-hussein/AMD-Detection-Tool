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

## 4. Arm A - watershed NAP head-to-head - DONE

Code: `python/watershed_nap.py --region colorado`. Output:
`data/matched/watershed_nap_colorado.csv` (6 catchment rows).

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

### Results (n=6 catchments, 44-130 Landsat scenes each, 45 stations by
sample count deduped by shared basin)

| chemistry var | loading | n | rho | LOOCV R2 |
|---|---|---|---|---|
| **dissolved Fe** | **ours M1 (AMD%)** | 6 | **+0.714** | **+0.804** |
| dissolved Fe | ours M2 (NAP-weighted) | 6 | +0.600 | +0.668 |
| dissolved Fe | rockwell M1 | 6 | +0.257 | -1.542 |
| dissolved Fe | rockwell M2 | 6 | +0.257 | -1.565 |
| pH | ours M1 | 6 | -0.371 | -0.644 |
| pH | rockwell M1 | 6 | -0.714 | -0.302 |
| sulfate | ours M1 | 6 | +0.314 | -1.272 |
| sulfate | rockwell M1 | 6 | +0.314 | -0.649 |
| specific conductance | rockwell M1 | 5 | +0.600 | -1.034 |

**Headline: our v3.0.x map's upstream AMD-area fraction predicts measured
dissolved Fe substantially better than Rockwell's published map does**, in a
real head-to-head against independent USGS water chemistry - the one result
in this entire project scored against ground truth neither map was fitted to.
Rockwell's M1/M2 have negative LOOCV R² (worse than predicting the mean); ours
is +0.80.

**This is NOT statistically significant at n=6 and must not be oversold.**
Exact permutation p-values (720 permutations, computed directly, not a normal
approximation): ours M1 vs dissolved Fe **p=0.136**; rockwell M1 vs dissolved
Fe p=0.658; rockwell M1 vs pH p=0.136 (same magnitude as our headline result,
opposite variable - Rockwell is not "zero signal everywhere"). Report this as
**suggestive and exploratory**, not proven.

**n=6 is a real ceiling, not an artifact of too few stations searched.**
Re-ran with 82 stations (min_samples lowered 5->3), spanning genuinely
different sub-watersheds (San Miguel/Telluride-area stations: Camp Bird Mine,
Cornet Creek, Poughkeepsie Gulch) at the same 60 km search radius - EVERY one
of the 82 collapsed into the SAME 6 catchments already found. Confirms finding
§3's `hybas_12` granularity floor is the binding constraint here, not station
selection. Increasing n requires either a materially larger search radius
(pulling in genuinely separate river systems) or finer catchment delineation
(true DEM flow-accumulation, logged as a next step in §3).

**Sulfate and specific conductance show no reliable signal for either map**
(both near the ±0.3 rho range, both maps tied on sulfate). Consistent with
sulfate's established optical invisibility (finding W4) extending to
watershed-scale mineral-area as a proxy too - pyrite oxidation chemistry and
downstream transport are not simply proportional to exposed mineral area at
Landsat resolution.

## 5. Arm B - direct optical detection

### B1 - water column - Ohio DONE, Colorado DONE

Code: `python/match_scenes.py`, `python/detection_limit.py`. Full report:
`validation/report_detection_limit_ohio_2026-08-10.txt`.

**Ohio: expanded 42 -> 83 matched rows** (all 355 available station-dates
attempted, not the earlier subset; 83 produced a usable scene within +/-3
days). 49 Sentinel-2, 34 Landsat 8, median 129 water pixels/window.

| variable | n | result |
|---|---|---|
| Iron (Total Recoverable) | 17 | **no feature's CI excludes zero - no detectable response** (0.058-6.2 mg/L range, median 0.345) |
| Iron (Dissolved) | 4 | too few rows to test |
| Sulfate | 23 | **no feature's CI excludes zero** (10.6-439 mg/L range) |
| **Turbidity (confound check)** | 50 | **6 features' CI excludes zero** (green_blue rho=+0.499, f_B2 rho=-0.489, ...) |

**This confirms and sharpens findings W1-W4 with nearly double the sample.**
The water arm optically detects turbidity/sediment cleanly - multiple bands
with confidence intervals that clearly exclude zero - but iron and sulfate
remain undetectable at Ohio's concentrations even with the larger sample. Any
apparent "iron signal" anywhere in this project's water-column work is a
turbidity signal in disguise unless proven otherwise by a confound-controlled
test, exactly as W3 already warned.

**Colorado, stratified across the full concentration range - ATTEMPTED,
produced no usable matches, two distinct real findings:**

221 station-dates were picked at even percentile spacing across 0-99.7 mg/L
dissolved Fe. `--min-width-m 12` dropped **197 of 217 (91%)** before matching
was even attempted, leaving 20. **All 20 of those 20 then failed with "no
usable scene".**

1. **The width pre-filter is too aggressive.** It dropped stations on
   *missing* MERIT `wth` data, not *confirmed* narrowness - logged as
   `station(?)` in the run output. MERIT's modelled channel network does not
   resolve small headwater creeks at all; absence of a value means "MERIT has
   no channel here", not "this channel is narrow". Treating the two the same
   discarded stations that might have been perfectly matchable. Fix: only
   drop a station when `wth` is present AND below threshold; when it's
   missing, let `match_scenes.py`'s own `n_water` pixel count decide (that
   is the actual test of usability, and it already exists).
2. **The lake-calibrated water mask may not generalise to mountain streams at
   all.** Even "Animas River Below Silverton" - the widened mainstem, not a
   narrow tributary - produced zero matches across 6 attempted dates spanning
   2015-2022. The v2.4.0 water mask (`MNDWI>0.3 ∧ AWEInsh>0 ∧ NDVI<0 ∧
   NIR<Green ∧ brightness<0.30`) was built and validated on standing lake
   water (findings W1-W4); a fast, shallow, turbulent, often-shadowed
   mountain river in a narrow valley may simply not satisfy those spectral
   conditions regardless of channel width. This is a genuine, informative
   negative finding, not a bug to paper over - but it means **B1 cannot yet
   answer the Colorado question with the current masking approach**, and
   needs either a stream-specific mask or direct pixel inspection at a known-
   wide, known-good reach before concluding streams are truly undetectable.

Both are logged as concrete next-session fixes (§ "What to do next session"),
not resolved in this session given the point of diminishing returns reached
on this particular sub-question.

### B2 - precipitate/seep [NOT BUILT THIS SESSION]

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
0. **Re-run Colorado B1 stream matching.** Bug (a) is FIXED this session
   (`screen_stream_width()` now only drops on confirmed-narrow, not missing
   data). Bug (b) is not: before re-running the full stratified sample,
   sanity-check the water mask on ONE known-wide, known-good Animas reach and
   date by hand (print the actual MNDWI/AWEInsh/NDVI/brightness values at the
   pixel) to determine whether the lake-calibrated mask needs a stream-
   specific variant - the mainstem produced zero matches across 6 dates even
   before the width filter was the bottleneck.
1. **Build B2 (precipitate/seep extraction)** - needs a defined sampling
   geometry around known discharge points (the 62 mine-discharge/adit/spring
   stations already identified in Colorado are the natural target list; use
   `water_indices.py`'s `GreenNIR`/`GreenNIRNorm`, correctly scoped to
   land-surface pixels this time).
2. **Arm C** (vegetation NDVI stress proxy), with a permutation null from the
   start - do not repeat finding W2.
3. **Resolution-degradation curve**, once B1/B2 give something detectable to
   degrade (S2 10m -> 20/30/60/100m, reproducing paper2's "3 of 6 leaks
   resolved at 10m" finding quantitatively).
4. **Increase Arm A's n** beyond the 6-catchment ceiling: either widen the
   search radius to pull in genuinely separate river systems (Uncompahgre,
   Lake Fork), or build true DEM flow-accumulation delineation
   (`MERIT/Hydro/v1_0_1` `dir` band) for finer catchment resolution than
   `hybas_12` provides near Silverton.
5. Calibrate `ferric1/2StdMult`/`ferrousStdMult` in the v3.0.x classifier
   (still uncalibrated by assumption, per REPLICA_AUDIT_2026-07-26.md) -
   directly affects Arm A's M1/M2 loading metrics since they depend on the
   full classification cascade, not just the iron/clay terms.
6. Investigate whether the Cement Creek / Animas mainstem / Howardsville
   catchment split (currently impossible at hybas_12 resolution) would
   change the Arm A result if resolved - Cement Creek is disproportionately
   acidic and is currently averaged in with cleaner tributaries sharing its
   polygon, which would bias any true association toward the null.
