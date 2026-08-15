# PROJECT STATE — read this first

**Last updated:** 2026-08-14 · **Current tag:** `v3.1.1`

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
2026 and is being rebuilt as Phase 2 along three arms. **Arm A's n=6 headline
(our map predicting dissolved Fe better than Rockwell's) did NOT survive being
raised to n=31 across 7 independent river systems — it is RETRACTED as of
2026-08-13.** Leave-one-region-out R² is negative for every map, every
loading model, on dissolved Fe. This is reported as prominently as the
original finding was, per this project's own rule that a collapse is as
valuable as a confirmation. See "RETRACTED" below before "OPEN" — the
retraction is the load-bearing update this file exists to carry forward.

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
- **Arm B2 dose-response: the first ground-truth-validated POSITIVE in the
  water arm (2026-08-14).** At 86 chemically-confirmed AMD source points across
  4 regions, `FerricIron1` (red/blue) tracks measured **dissolved Fe at
  rho = +0.568** (n=75, within-region permutation p = 0.0004, BH q = 0.0072 over
  36 tests), and pH at −0.554. Only **24% between-region variance**, and the
  p-value comes from permuting labels *within* region — i.e. it passes the exact
  test that destroyed the pooled sulfate claim. Pre-registered as H2 before
  extraction. **Leave-one-region-out, applied the same day, tempers it and the
  tempered version is the one to cite:** the sign holds in **all four**
  districts (Arm A's signs were incoherent — this is the check Arm A failed),
  but it is **heterogeneous** (Leadville rho ≈ 0.00 vs +0.62/+0.64/+0.68) and
  **LORO R² is negative for every pair**. → **`FerricIron1` RANKS severity
  within a district; it does NOT predict concentration across districts.**
  The most robust single relationship is `FerricIron1` vs **pH**: all four
  districts negative and tight in magnitude (−0.24 to −0.40).
  paper2's `GreenNIR`/`GreenNIRNorm` **fail** sign consistency (+0.51, +0.16,
  −0.25, −0.35) — their pooled value is not a relationship.
  → [`ARM_B2_SEEP_DETECTION_2026-08-14.md`](ARM_B2_SEEP_DETECTION_2026-08-14.md)
- **Arm B2 detection is a NULL, at n=86.** All 9 indices fail the pre-registered
  criterion (worst-case LORO Youden J >= 0.25 vs all 3 control tiers, BH
  p < 0.05, 10k permutations). Apparent separation exists only against
  terrain-matched land (C2) and collapses to ~0 against in-stream stations in
  the same region (C1). **Imagery ranks severity at known sites; it does not
  find sites.**
- **The shipped v3.0.x classifier is substantially a BARE-GROUND detector.**
  `AMDclassFrac` vs bare ground: AUC 0.456, worst-case LORO J **−0.304** — it
  scores bare ground *higher* than confirmed mine discharge (Leadville medians
  0.376 vs 0.049, 7.7x). Structural, not a bug: the NDVI gate requires a pixel
  to be unvegetated before it can receive any AMD class. State this whenever
  the classifier is used.
- **Colorado chemistry is rich.** 17,062 water rows; **1,770 dissolved Fe**
  measurements (vs Ohio's 4), median 0.45 mg/L; mine-discharge source points
  median 6.2 mg/L, max 120 mg/L.

---

## OPEN QUESTIONS WORTH FOLLOWING — leads, not results

Both from [`ARM_A_CROSS_REGION_RETEST_2026-08-13.md`](ARM_A_CROSS_REGION_RETEST_2026-08-13.md).

- **Rockwell's map vs pH, within-region: rho = −0.525, p = 0.015.**
  Mechanistically correct direction (more mapped AMD area upstream → lower
  downstream pH), survives region-centering, and both Rockwell loading metrics
  agree while neither of ours reaches significance. **Does NOT survive
  multiple-comparison correction** (20 tests; BH/Bonferroni threshold 0.0025).
  A lead to test on new data. Note it runs *opposite* to the retracted claim —
  if it replicates it favours Rockwell's map, not ours.
- **Does the Arm A sign-flip track geology?** Silverton +0.714 and Ouray +0.667
  (both San Juan volcanic-field calderas) vs Central City −0.700, Creede
  −0.800, Leadville −0.800. **Deliberately untested and given no p-value** —
  the hypothesis was generated from these same signs, so testing it here would
  be circular (the Test C / W1 error). Testing it needs geology labels assigned
  to regions chosen *before* seeing their signs, or sign predicted in advance
  for new regions.

---

## RETRACTED / DISPROVEN — do not cite these

- **Arm A: "our map predicts dissolved Fe better than Rockwell's" (2026-08-10,
  retracted 2026-08-13).** At n=6 (Silverton only): rho=+0.714 vs Rockwell's
  +0.257, LOOCV R²=+0.804 vs −1.542, p=0.136 (suggestive). Raised to **n=31
  across 7 independent river systems**: pooled rho collapses to **+0.056**
  (p=0.760), **every leave-one-region-out R² for dissolved Fe is negative**
  for both maps. Per-region signs are not even consistent (Silverton/Ouray
  positive, Central City/Creede/Leadville negative). Several *other* pooled
  relationships (sulfate, pH, conductance) looked significant at p<0.05 and
  **also failed the leave-one-region-out check** — a direct demonstration of
  why pooled significance without a held-out test is not evidence.
  → [`ARM_A_CROSS_REGION_RETEST_2026-08-13.md`](ARM_A_CROSS_REGION_RETEST_2026-08-13.md)
- **The pooled sulfate correlation (rho = −0.563, p = 0.001).** It **reverses
  sign to +0.220 (p = 0.344)** once between-region structure is removed.
  Sulfate is 67.5% between-region variance, so the pooled figure was comparing
  river systems, not testing the loading relationship — a textbook ecological
  fallacy caught in our own data. Diagnostics also confirm the dissolved-Fe
  null is **robust**, not a masking artifact (within-region rho +0.136,
  p=0.559), and that catchment area is **not** a confound.
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

1. **Test whether Arm A's sign-flip tracks geology** (see "OPEN QUESTION"
   above). Silverton+Ouray (San Juan calderas) vs Central
   City+Creede+Leadville — no new fetching needed, the 31-catchment dataset
   already exists at `data/matched/watershed_nap_*.csv`.
2. ~~Fix the `hybas_12` dilution problem~~ **TOOL BUILT AND VALIDATED
   2026-08-13** (`python/catchment_dem.py`), **not yet wired into Arm A.**
   True MERIT D8 delineation scores **6/6 within ±33%** of published USGS
   drainage areas vs `hybas_12`'s 2/6, and resolves Cement Creek to 13.3 sq mi
   (0.99×) where `hybas_12` gave it the same 91.7 sq mi polygon as the Animas
   mainstem. Tracing independently verified against MERIT's own `upa` band
   (ratio 1.00 at all 6 gauges).
   **Remaining work:** wire it into `watershed_nap.py` and re-run Arm A.
   **Temper expectations on n:** catchments on one river are deeply nested
   (5 Animas gauges → only **3** independent catchments after
   `select_non_nested()`), so DEM delineation will NOT multiply n the way it
   first appeared. Report non-nested n, never station count. Still worth
   running: the question is whether removing Cement-Creek-style dilution
   reveals a relationship `hybas_12` was masking.
3. ~~Arm B2 — precipitate/seep detection~~ **RUN 2026-08-14 on Landsat 8**
   (`python/seep_detect.py`). Detection null, dose-response positive — see
   PROVEN above. **Remaining B2 work, in value order:**
   a. **C3b amendment (required).** The pre-registered C3 bare-ground tier is
      circular for vegetation-sensitive indices — it was defined by NDVI, so
      `NDVI_stress` separates from it by construction. Re-run with NLCD
      `USGS/NLCD_RELEASES/2019_REL/NLCD` class 31 (Barren Land), independent of
      our imagery, as a **labelled amendment**. Does not change the null.
   b. **Hold out a region on the dose-response.** rho=+0.568 is pooled-with-
      within-region-permutation, which is much stronger than the retracted
      sulfate result but is still not a held-out test. Leave-one-region-out is
      the obvious next check and this project's own standard.
   c. **Sentinel-2 + the resolution ladder** (was OPEN #6). NOTE: S2 is NOT
      10 m for most of the panel — SWIR is 20 m and the coastal band 60 m;
      only `FerricIron1` and the green:NIR pair are true 10 m
      (`seep_detect.S2_NATIVE_M`). Report effective GSD per index, not the
      nominal collection resolution.
4. **Colorado B1 stream matching.** Zero matches so far. One bug fixed (width
   screen dropped on *missing* MERIT data, not confirmed narrowness); one open
   — the lake-calibrated water mask returns nothing even on the wide Animas
   mainstem across 6 dates. Needs a hand check of actual pixel values before
   concluding streams are undetectable.
5. **Arm C — vegetation NDVI stress proxy.** Not built. Needs a permutation
   null from the start or it will repeat finding W2.
6. **Resolution-degradation curve.** Blocked on B1/B2 finding something
   detectable to degrade. Would quantitatively reproduce paper2's "Sentinel-2
   resolved 3 of 6 leaks" — the published justification for a 7 cm drone.
7. **Uncalibrated classifier constants.** `ferric1StdMult`, `ferric2StdMult`,
   `ferrousStdMult` are all set to 0.5 *by assumption*; only iron and clay were
   LOSO-fitted. They drive classes 1–8, which nothing has validated.
   `clayStdMult` did not transfer cleanly (per-fold fits −0.5, −0.5, +1.0).
8. **Red Mountain Pass regression** under v3.0.x (J 0.642→0.452) — rests on
   19–23 positive pixels. Compositing (D8) was the prime suspect and is largely
   ruled out; small-sample noise is now the leading explanation.
9. **Departures D4, D5, D6** (class 9/17 split uses brightness where Rockwell
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
