# PROJECT STATE — read this first

**Last updated:** 2026-09-19 · **Current tag:** `v3.10.0` (tool: `v3.1.0`). Every commit since the tag is untagged, and **Zenodo has not been updated** (see OPEN → NEXT).

**Start here after a break:** [`ROUND_SUMMARY_2026-09-16.md`](ROUND_SUMMARY_2026-09-16.md) (what was done and found) · [`../docs/HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) (test everything yourself) · [`FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md`](FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md) (the field campaign, Ohio first)

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

## TOOL STATE (what can actually be run, updated 2026-09-14)

**The tool can now be pointed at any area of interest.** Before this it could
not: the GEE tool accepted only its 30 hardcoded `studyAreas`, and the Python
pipeline needed edits to five hand-synced dicts.

- **GEE `v3.1.0`** — free-form AOI (lat/lon/radius) alongside the 30 presets.
- **Python `--bbox`** — `fetch_wqp.py --region "<Name>" --bbox "..."` writes a
  `data/regions.json` overlay that `seep_detect`, `cmd_detect` and
  `watershed_nap` all resolve through. Curated regions always win on conflict.
  One `region_slug()` replaces the inline expression `watershed_nap` admitted
  was hand-kept. **Proven end-to-end**: three new PA regions registered and
  fetched with no source edit.
- **`docs/OPERATOR_GUIDE.md`** — what every layer means and what may/may not be
  concluded. **Supersedes** the Nov 2025 `earth-engine/*.md` guides, which
  document v2.x behaviour the code no longer has.
- **`amdtool` package (2026-09-14).** Install with `pip install -e .` (`src/amdtool`).
  It holds statistics, dose-response, imagery, WQP chemistry, the severity
  report, the score raster, the blind search, auth and claim text. It never
  prints, exits or authenticates on a host's behalf: a host passes in `ee`.
  **Behaviour-neutral, proven:** 207 tests, including exact golden rebuilds
  of CMD1, CMD2 T1, the CMD3 ladder, B2's J 0.234 and its ρ +0.568 / LORO lines.
  **Since 2026-09-15** `seep_detect`, `cmd_detect`, `cmd_confound`, `fetch_wqp`
  and `ee_auth` are thin wrappers over it. CMD1, CMD2, CMD3 and B2 dose-LORO
  regenerate identically through them, and a live Monday Creek re-extraction
  matches the committed file exactly (max abs diff 0.000). B2's detection
  tables now carry the tied-score correction (audit 2026-09-15, item 9). Gate:
  `AMDTOOL_REFACTOR_GATE_2026-09-14.md`.
- **SpectraLab "AMD severity report" module** — branch
  `feature/amd-severity-module` of VPCA+STEPWISE-REGRESSION, **not released**.
  Draw an AOI, choose a preset (metal mine / coal), and get a claim-bounded,
  explicitly EXPLORATORY report: within-tile permutation, per-tile signs, CSVs
  and a score raster. Guide: `docs/AMD_MODULE.md` in that repository.

**⚠ Three defects were fixed that would have misled anyone testing a new area:**

1. **The adaptive-threshold checkbox rendered `false` while the setting was
   `true`** — the tool booted in scene-relative mode while the UI claimed
   otherwise, so the first click was a silent no-op and the *second* switched
   the whole classification to absolute thresholds.
2. **The σ sliders started at 2.0/1.5 against calibrated 0.5/0.25, with a
   slider MINIMUM of 1.0** — so *any* drag silently applied what the file's own
   comment measures as **worst-case J = 0.000**. Now staged behind an Apply
   button, with the two missing controls (`clayStdMult`, `ferrousStdMult`)
   added. `resetButton` restores σ too.
3. **The date filter defaulted to 2024**, outside the 2013–2020 collection
   window, so switching it on returned zero images.

**⚠ And the scientific one underneath them: the AOI extent WAS a classification
parameter.** `applyStdDevThresholding` reduced over `currentRegion`, so the same
pixel changed class depending on how large a circle the operator drew. σ
statistics now come from a **fixed 12 km circle on the AOI centre** — inside the
8–15 km LOSO band (Summitville 8, Red Mountain Pass 10, Silverton 15) — while
display and export keep the AOI. `statsRadiusMode = 'matchAOI'` reproduces
pre-v3.1.0 figures. **This changes output for all 30 presets** (Ganau's σ was
computed over 1 km, Lake Naser's over 100 km); that is a correction, announced
at startup.
**Verify it yourself:** run one centre at r = 8, 12, 20 km — the printed σ cut
must be identical. In `matchAOI` mode it moves; that is the defect, live.

Still open on the tool, tracked in `docs/OPERATOR_GUIDE.md` §7: the statistics
panel, click inspector and accuracy masks use absolute thresholds
unconditionally and so disagree with the map; classes 6/10 unreachable; two
legend swatches disagree with the palette; the legend omits water class 3
(grey = INDETERMINATE, which must never be pooled with clean).

---

## RECORD AND GRANT READINESS (2026-09-13)

**The externally-facing record now matches the measured one.** Before this,
nine documents asserted a validated in-water detection capability that this
file records as retracted — most seriously `CITATION.cff`, minted under DOI
`10.5281/zenodo.19429983`, which claimed validation against Muskingum Watershed
chemistry: the **opposite** of the measured null.
- **Rewritten:** `CITATION.cff`, `README.md`, `PROJECT_OVERVIEW.md`,
  `python/README.md` (its spectral-index formulas were wrong).
- **Bannered, findings unedited:** the six Nov-2025 `earth-engine/*.md` guides,
  `docs/METHODOLOGY.md`, `specs/amd-v2/*`, `PUBLIC_RELEASE_SUMMARY.md`,
  `DOI_UPDATE_SUMMARY.md`, `PUBLISHING_CHECKLIST.md`.
- **Renamed:** `earth-engine/validation_results.md` →
  `validation_results_2025-11_SUPERSEDED.md` — its filename asserted a
  validation it does not contain.
- A sweep for every refuted-claim pattern finds **zero** unqualified hits.

**New documents:**
[`ACCURACY_ASSESSMENT.md`](ACCURACY_ASSESSMENT.md) (every number with n and
reference standard) · [`../docs/GRANT_CASE.md`](../docs/GRANT_CASE.md) (the
honest fundable argument) · [`../docs/FIELD_CAMPAIGN.md`](../docs/FIELD_CAMPAIGN.md)
(sites, hypotheses, sample sizes from `python/field_power.py`).

**Verified while writing them, and worth knowing:**
- **A load-bearing number could not be traced.** The land-arm `0.107 → 0.440`
  existed only in `.md` reports; those scripts print to stdout, so it had only
  ever been checked against another summary. Regenerated — **reproduces
  exactly** — and committed as `report_paper_faithful_2026-09-13.txt`. The
  other load-bearing figures (0.234, +0.568, −0.354) verified against existing
  raw output.
- **All 7 pre-registrations were committed before their results**, checked by
  commit ancestry, not filenames. Gaps run **11 min to 5 h 06 m**. Commit order
  proves order; it does **not** prove analysis was not run locally in the gap.
  The CMD1 files carry 2026-08-16 in their names but entered git on
  **2026-08-24** (ordering still holds).
- **The planned drone prediction did not discriminate.** It predicted UAV
  imaging would bring the canopy diagnostic below 0.6 — **leaf-off satellite
  already does** (0.462 Ohio, 0.529 Pennsylvania). Replaced by **H-UAV**: UAV
  against leaf-off satellite on the same stations.
- **Why archival data could not settle sign consistency:** at ~20 source points
  per district, a true rho of 0.3 fails the four-district sign check about one
  time in three — P(all 4 positive) = **0.681**. Leadville's +0.004 may be partly
  sampling, not only heterogeneity.
- **Archival iron tiers are uneven:** Ouray has **no** source point ≥10 mg/L
  dissolved Fe on record; Silverton has one; Central City has 14.

**Cold start fixed — the Python arm was unrunnable anywhere but this machine.**
`python/ee_auth.py` replaces five copies of `init_ee()` that hard-coded a key
path inside a sibling repository. Credentials now resolve
`$GEE_SERVICE_ACCOUNT_KEY` → legacy path → `$GEE_PROJECT` (personal
`earthengine authenticate`) → a clear setup error. `requirements.txt` gained
`rasterio`, `requests`, `shapely`. `docs/OPERATOR_GUIDE.md` §0 is a real setup
section. **Verified behaviour-neutral:** 27 modules compile; the old
`from gee_classify import init_ee` path resolves to the shared function; a live
Earth Engine call succeeds; the CMD1 baseline still reproduces (−0.354, n=137,
p=0.0028); `catchment_dem --self-test` 6/6 PASS; `classify_v240` bare-clone
smoke test PASS (94.95%, its documented ceiling).

**Outstanding — only the author can do these:**
1. **Publish a new Zenodo version.** `CITATION.cff` is corrected in-repo, but a
   minted DOI is not changed by a local edit; until then anyone citing
   `10.5281/zenodo.19429983` gets the retracted Muskingum claim.
2. **`.private/EB2_DOCUMENTATION.md`** carries the same retracted claim and
   lists the retracted water module as evidence of ability. Deliberately
   untouched — gitignored, and may already be with an attorney.
3. **Author name.** `PUBLIC_RELEASE_SUMMARY.md` gave "Ahmad A. Hussein" six
   times; unified to Abdulrahman Hussein. Check it did not propagate elsewhere.
4. **The earlier ResearchGate item** on "cryptic sulfate pollution" carries the
   retracted claims.
5. **Push** — commits are local.

---

## AUDIT 2026-09-14 — found while scoping the next test

→ [`AUDIT_2026-09-14_ARMA_AND_TOOLING.md`](AUDIT_2026-09-14_ARMA_AND_TOOLING.md).
All eight verified directly. **None rescues a retracted claim.**

1. **Arm A computed σ thresholds per catchment** (`watershed_nap.py:165`) — the
   AOI-extent defect fixed in the Earth Engine tool at v3.1.0, so catchment size
   acted as a classification parameter.
2. **Arm A's "31 catchments" are 28 distinct polygons.** `7121080490`
   (Alma/Leadville), `7121092570` (Ouray/Silverton) and `7120588780` (Lake
   City/Ouray) each appear under two regions, so identical loadings sit on both
   sides of leave-one-region-out splits. The curated Alma and Leadville boxes
   overlap. **Quote n as 28.**
3. **Creede and Lake City were mislabelled as non-caldera** — see the corrected
   OPEN QUESTION below.
4. **`vpca_validation.convolve_splib07` crashes on NumPy 2.x** (`np.trapz`
   removed). Nothing calls it, so no number is affected.
5. **CMD2's absolute bars (0.25 / 0.15) cannot be reused for Pennsylvania**,
   whose raw values (−0.143 / −0.187) already sit below them. A PA confound
   test must measure attenuation from PA's own raw value.
6. **A `seep_detect` comment claims Creede and Alma were extracted; they never
   were.** That confirms those districts are independent of the index choice,
   which the blind-search test relies on.
7. **`partial_spearman` could return a "correlation" of 11.97** when z explains
   x's ranks exactly — its guard tested for residual spread of exactly zero.
   Found by a unit test, fixed in `amdtool` with a relative tolerance.
   **No committed number moved**: a golden test rebuilds CMD2's T1 table and
   proves the new guard returns identical values at every covariate and every
   watershed, and every line (permutation p included) matches the report.
8. **"Sign-consistent across four districts" hid a zero.** `FerricIron1` vs
   dissolved Fe (Landsat 8) is +0.64 / +0.68 / +0.64 in Central City, Ouray and
   Silverton (n = 20, 17, 15), but **+0.004 in Leadville (n = 23)**. The report's
   `[ALL +]` tests only ρ > 0. **No number changes.** The claim narrows to three
   of four districts, corrected in README, CITATION.cff, PROJECT_OVERVIEW,
   GRANT_CASE, FIELD_CAMPAIGN and `amdtool`. The caveat: per-district n is small
   (about ±0.4), so the statement is "not shown to be universal", not "null in
   Leadville".

---

## AUDIT 2026-09-15 — Arm B2 regenerated from committed code and data

→ [`AUDIT_2026-09-15_B2_REPRODUCTION.md`](AUDIT_2026-09-15_B2_REPRODUCTION.md) ·
raw: [`report_b2_reproduction_2026-09-15.txt`](report_b2_reproduction_2026-09-15.txt)

**No pre-registered verdict changes. No headline number changes.**

9. **Worst-case J was evaluated inside runs of tied scores**, making it depend
   on row order. Six printed values change. Most notable: L8 `AMDclassFrac` vs
   C2 goes 0.000 → +0.235, the shipped classifier vs C3b 0.000 → **−0.252**, and
   the B2b grid goes from 0.000 everywhere to −0.452…0.000. No row crosses 0.25.
   With p recomputed, `AMDclassFrac` vs C2 becomes significant (L8 q 0.0004,
   S2 q 0.031) but stays below the J bar and still fails C1 and C3, so no verdict
   moves. The claims that leaned on the zeros get stronger. Fixed in `amdtool` and
   tested against brute force.
10. **The C3b report pooled a cloud-unfiltered composite** (161 and 138 scenes
    vs 61 and 59) into its C2/C3 tiers. Its C3b, C1 and target rows are clean.
11. **The B2 reports regenerate byte for byte, but only in an input order
    nobody recorded** (Silverton, Leadville, Ouray, Central City). From now on a
    regeneration command lists its inputs in order.

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
  rho = +0.568** (n=75, within-region permutation p = 0.0004 at 5,000 draws, BH q = 0.0072, regenerated
  from committed code on 2026-09-15 (`report_b2_dose_response_2026-09-15.txt`), over
  36 tests), and pH at −0.554. Only **24% between-region variance**, and the
  p-value comes from permuting labels *within* region — i.e. it passes the exact
  test that destroyed the pooled sulfate claim. Pre-registered as H2 before
  extraction. **Leave-one-region-out, applied the same day, tempers it and the
  tempered version is the one to cite:** ρ is above zero in all four districts
  (Arm A's signs were incoherent — this is the check Arm A failed), but it holds
  in **three of four**: Leadville is **+0.004 (n=23)**, vs +0.64/+0.68/+0.64
  (audit 2026-09-14 item 8), and
  **LORO R² is negative for every pair**. → **`FerricIron1` RANKS severity
  within a district; it does NOT predict concentration across districts.**
  The most robust single relationship is `FerricIron1` vs **pH**: all four
  districts negative and tight in magnitude (−0.24 to −0.40).
  paper2's `GreenNIR`/`GreenNIRNorm` **fail** sign consistency (+0.51, +0.16,
  −0.25, −0.35) — their pooled value is not a relationship.
  → [`ARM_B2_SEEP_DETECTION_2026-08-14.md`](ARM_B2_SEEP_DETECTION_2026-08-14.md)
- **⛔ RESOLUTION IS *NOT* THE BINDING CONSTRAINT — REFUTED 2026-08-16.**
  The within-Sentinel-2 detection ladder (only pixel size varies, one sensor)
  gives `FerricIron1` mean AUC **0.732 / 0.724 / 0.740 at 10 / 20 / 40 m** —
  flat, 3 of 4 regions (Silverton died on GEE memory). With the dose-response
  ladder also flat over 10–100 m, **neither detection nor severity improves with
  finer pixels anywhere in 10–100 m.**
  **So the Landsat→Sentinel-2 jump (J −0.018 → +0.234) was a SENSOR effect —
  bands, SNR, atmospheric correction, deeper scene stacks — not resolution.**
  **Instrumentation consequence, against our own earlier framing:** these data
  point at the **spectral/radiometric** axis (multi-band, spectrometer), **not**
  at spatial resolution. Do not justify a 7 cm platform from this evidence;
  a 10-band sensor and ASD spectrometer sit on the axis actually implicated.
  **Bound:** tested range is 10–100 m, which does span the mixed→pure pixel
  transition for a 5–20 m fan. Sub-metre is untested; a 7 cm claim is
  extrapolation *against a flat trend*.
- **SEVERITY RANKING DOES NOT NEED FINE RESOLUTION (2026-08-15).** The
  resolution ladder — which varies **only** pixel size inside one sensor — shows
  the dose-response is **FLAT from 10 m to 100 m**: `FerricIron1` vs dissolved
  Fe = +0.494/+0.526/+0.493/+0.523/+0.517 at 10/20/30/60/100 m; vs pH
  −0.575 → −0.658, marginally *stronger* at coarser pixels. The severity signal
  lives at scales ≥100 m, so **free 30 m Landsat suffices for ranking** and a
  drone adds nothing to that specific use. → [`report_seep_b2_ladder_2026-08-15.txt`](report_seep_b2_ladder_2026-08-15.txt)
- **⚠ The "resolution is the binding constraint" claim below is CORRECTED and
  currently UNPROVEN for detection.** The 30 m→20 m jump is Landsat vs
  Sentinel-2, which confounds **sensor** with pixel size. A within-Sentinel-2
  detection ladder is required and was still running when this was written.
  Cite the corrected version, not the original.
- **C3b amendment CONFIRMS rather than overturns (2026-08-15).** With bare
  ground redefined from NLCD class 31 (independent of our imagery, fixing C3's
  NDVI circularity): `FerricIron1` vs C3b J = **+0.318**, identical to its
  circular-C3 value — so that separation was **not** an artifact. And
  `AMDclassFrac` vs C3b = **−0.252, AUC 0.442**, confirming with a non-circular
  control that the shipped classifier cannot tell mine discharge from bare
  ground. The −0.252 is corrected for tied scores; the report printed 0.000
  (audit 2026-09-15, item 9). That report's C2/C3 rows pooled a
  cloud-unfiltered composite and must not be cited (item 10).
- **RESOLUTION IS THE BINDING CONSTRAINT — as originally claimed, now corrected
  above (2026-08-15).**
  Same 86 points, same controls, same pre-registered test; only pixel size
  changes. `FerricIron1` worst-case LORO Youden J, **Landsat 30 m → Sentinel-2
  20 m**: vs C1 in-stream **−0.018 → +0.234**, vs C2 **−0.101 → +0.291**, vs C3
  **−0.045 → +0.318** (all BH q = 0.0003). Every tier flips from below zero to
  strongly positive. At 20 m it misses the pre-registered bar **only on C1 and
  only by 0.016** — still a null by the registered rule, but a qualitatively
  different one from Landsat's all-negative failure. **`AMDclassFrac` does NOT
  improve with resolution** (≈0.000 vs C1/C2 at both), consistent with its AMD
  calls being driven by the bare-ground gate rather than by iron.
  Independent convergence with paper2's "S2 resolved 3 of 6 leaks" conclusion,
  at n=86 vs their n=6, with a pre-registered criterion instead of a visual
  count — and reached *despite* their green:NIR indices performing poorly here.
  **Extrapolation to 7 cm is extrapolation, not measurement.**
  → [`ARM_B2_SENTINEL2_RESOLUTION_2026-08-15.md`](ARM_B2_SENTINEL2_RESOLUTION_2026-08-15.md)
- **Arm B2 detection is a NULL, at n=86.** All 9 indices fail the pre-registered
  criterion (worst-case LORO Youden J >= 0.25 vs all 3 control tiers, BH
  p < 0.05, 10k permutations). Apparent separation exists only against
  terrain-matched land (C2) and collapses to ~0 against in-stream stations in
  the same region (C1). **Imagery ranks severity at known sites; it does not
  find sites.**
- **★ CMD3 — PENNSYLVANIA: the SIGN replicates, the SCALE does NOT, and the
  radius ladder fails as a mechanism diagnostic (2026-09-09, pre-registered
  `4765bca` before any PA data was fetched).** Three **spatially disjoint**
  tiles over the upper West Branch Susquehanna (Chest / Clearfield / Moshannon
  Creek), fixed with coordinates in advance. **274 sulfate-matched stations**
  (Ohio had 137), **450** for conductance, **1–3% between-region variance**
  (Ohio 13%). All three cleared the pre-registered n ≥ 8 bar. Registered and
  fetched with **no source edit** — first use of the `--bbox` overlay.
  **VERDICT: FAILS TO REPLICATE**, on the falsifier named in advance —
  **|rho| peaks at 30 m** and collapses to nothing at landscape scale:

  | radius | 30 m | 60 m | 100 m | 500 m | 1000 m |
  |---|---|---|---|---|---|
  | vs sulfate | **−0.143** | −0.135 | −0.114 | −0.010 | −0.050 |
  | vs conductance | **−0.187** | −0.158 | −0.138 | −0.010 | **+0.003** |

  Conductance is the better-powered arm (n=443, **p = 0.0002** at 30 m) and is
  **sign-consistent at all three near radii** — Ohio read "signs disagree" at
  every radius, so **this is the first sign-consistent result the CMD arm has
  produced**. The canopy gate passed, so the far null is interpretable.
  **PA's ladder is the OPPOSITE SHAPE from Ohio's** — monotone declining vs
  U-rising-to-1 km. Each basin's result is the other's registered falsifier.
  **Consequences:**
  (i) **CMD2 is not withdrawn but BOUNDED** — catchment-scale *in Ohio*,
  near-field *in Pennsylvania*; the general claim cannot be made.
  (ii) **Radius shape does not diagnose mechanism.** CMD1 amendment 2
  registered it as the way to tell "seep" from "catchment-scale land cover";
  it returns opposite mechanisms for the same drainage type, so it is more
  plausibly measuring basin geometry. **Third time a monotone-looking trend in
  this project failed to generalise.**
  (iii) **PA is UNCONDITIONED and cannot be conditioned** — ODNR is Ohio-only,
  NLCD rejected for sharing the NDVI physics. Registered before the data; this
  result cannot move CMD2's confound verdict either way.
  (iv) **It is weak**: 0.143 / 0.187 are far below the |rho| ≥ 0.3 bar. A
  weak *near-field* association in one basin against a strong *far-field* one
  in another is evidence that radius tells us about basin geometry, **not**
  about seeps — so this does **not** restore any near-channel claim.
  **Also, honestly: my own verdict table had non-exclusive rows** (a generic
  PARTIAL branch and a named falsifier the same data could satisfy). The
  specific falsifier governs; taking the kinder row would have been choosing a
  reading after seeing the outcome. Future tables must be mutually exclusive.
  → [`ARM_CMD3_PA_REPLICATION_2026-09-09.md`](ARM_CMD3_PA_REPLICATION_2026-09-09.md)
- **⛔ THE "GEOMETRY-LIMITED / NEAR-CHANNEL" READING BELOW IS REFUTED
  (2026-09-08, CMD2). Read that entry only together with this one.**
  ⚠ **And CMD2's own catchment-scale conclusion is now BOUNDED TO OHIO by CMD3
  — see the entry above.** Extending
  the radius ladder past 100 m shows it is **U-shaped**, with the strongest
  association at the **largest** footprint tested: `NDVI_stress` vs sulfate
  **−0.354 (30 m) / −0.253 (60 m) / −0.255 (100 m) / −0.393 (500 m) /
  −0.438 (1000 m)**. CMD1 amendment 2 registered the reading in advance —
  *|rho| rising as radius grows ⇒ catchment-scale land cover, not the seep* —
  so the registered conclusion is **landscape-scale land cover**. CMD1 saw a
  clean monotone gradient only because its window stopped at 100 m and sat on
  the descending left arm of a U. **Same failure mode as the Colorado
  resolution claim**, which also looked monotone inside a narrow window and
  reversed once the window was widened.
  **Consequence: the UAV argument CMD1 drew from the geometry gradient is
  WITHDRAWN.** The measured trend, extended, points away from the seep face.
  → [`ARM_CMD2_CONFOUND_2026-09-08.md`](ARM_CMD2_CONFOUND_2026-09-08.md)
- **★ CMD/OHIO CONFOUND TEST: the mining-extent confound is REAL and operative
  (2026-09-08, CMD2, pre-registered `a452446` before any join).** Covariate is
  ODNR `MinesOfOhio` — 14,578 coal polygons from permit records and historic
  topo/geology maps, owing **nothing** to satellite reflectance, which matters
  because the signal under test is a *vegetation* index. Upstream catchments by
  MERIT D8 (174/187 clean).
  **Both legs present:** mine extent → sulfate **+0.519**, mine extent →
  `NDVI_stress` **−0.283**. The confound path carries ~**42% of the raw
  covariance**.
  **Registered primary verdict: PARTIAL, by 0.004.** Partial rho **−0.246**
  (n=131, within-region perm p = 0.0254) against a registered
  "confound rejected" bar of |rho| ≥ 0.25. The bar was fixed in advance and is
  **not moved**.
  Conditioning on **surface** mining attenuates most (45%, p = 0.12);
  **underground**, least (20%) — coherent, since surface mining is what removes
  vegetation. The 1 km/5 km disc arms are stronger (−0.372 / −0.338) and are the
  **first sign-consistent result anywhere in the Ohio arm**, but they are
  registered *secondary* and are a **lead, not a finding** — the same data
  generated them.
  **Standing claim, as amended by CMD3 (2026-09-09):** *"a vegetation index
  tracks sulfate in coal watersheds, negatively and sign-consistently, at a
  scale that is BASIN-SPECIFIC — landscape-scale in Ohio, near-field in
  Pennsylvania — and in Ohio is partly explained by catchment mining extent."*
  **NOT** *"we detect CMD seeps"*, and **no longer** the unqualified
  *"at landscape scale"* — CMD3 bounded that to Ohio.
  **Also fixed, and verified rather than assumed: the recurring GEE memory
  trap has a second lever — BAND COUNT.** Sunday Creek failed a third time at
  the batch=2 floor with the 120-scene cap already in place; extracting only
  the band under test completed it. Re-extracting Monday Creek one-band vs
  eight-band gives **max abs difference 0.000 over 27 stations**, so it is a
  request-size fix, not a method change.
  → [`ARM_CMD2_CONFOUND_2026-09-08.md`](ARM_CMD2_CONFOUND_2026-09-08.md)
- **★ CMD/OHIO GEOMETRY: the null WAS geometry-limited, and the signal is
  VEGETATION not iron (2026-08-16, amendment 2, two-sided test registered
  first).** ⛔ **The "geometry-limited / near-channel" half of this is REFUTED —
  see the CMD2 entry above.** The *vegetation rather than iron* half stands.
  Shrinking the buffer strengthens the association **monotonically**:
  `NDVI_stress` vs sulfate **−0.255 (100 m) → −0.253 (60 m) → −0.354 (30 m)**,
  p **0.119 → 0.083 → 0.0028**, sign pattern mixed → mixed → **4 of 5 negative**
  (5th = +0.03, essentially zero not a reversal). **Verdict PARTIAL at 30 m**
  (was NULL at 60 m) — the strict all-five sign rule was fixed in advance and is
  applied as written.
  **The registered pixel-count risk did not materialise:** median 9 surviving
  pixels at 30 m, only 5% below 3 px (vs 4% at 60 m).
  **The signal is `NDVI_stress`, NEGATIVE — vegetation, not iron.** Iron indices
  stay weak and sign-inconsistent at every radius. This is the **first time
  paper2's vegetation-proxy framing has held up anywhere in this project**
  (their green:NIR ratios have now failed sign consistency 3 times), and it runs
  **opposite** to Colorado where iron carried everything and NDVI carried
  nothing. Mechanistically coherent for neutral CMD: no acid signature, iron
  precipitating locally, so the landscape expression is stressed riparian
  vegetation rather than ochre.
  **⚠ UNTESTED CONFOUND, and it gates the whole finding:** high-sulfate stations
  may simply sit in more heavily mined catchments with less vegetation overall —
  land cover, not a seep signal. **Until tested, this is "vegetation index
  tracks sulfate", NOT "we detect CMD seeps."**
  ~~**NEXT: mining-extent confound test**, then tighter/channel-masked
  sampling (the gradient has not bottomed out).~~ **DONE 2026-09-08 (CMD2).**
  The confound is **real**; the primary test came back **PARTIAL by 0.004**; and
  the gradient **had** bottomed out — extending it past 100 m reversed the
  reading entirely. See the CMD2 entry above.
  → [`ARM_CMD1_GEOMETRY_2026-08-16.md`](ARM_CMD1_GEOMETRY_2026-08-16.md)
- **★ CMD/OHIO LEAF-OFF: canopy removed, and the signal is NOT there — a REAL
  null (2026-08-16, amendment 1, registered before the run).** Median buffer
  NDVI fell **0.870 → 0.496** (p90) / 0.791 → 0.426 (mean), below the 0.6 limit;
  coverage 159 → **187 stations, 5/5 watersheds**. Registered prediction 1
  CONFIRMED: deciduous canopy was the May–Jul barrier. **With the ground
  visible, no index is sign-consistent across the five watersheds** vs sulfate
  or conductance (best |rho| 0.253, p 0.075, signs disagree). **NULL.**
  July said "we cannot see"; this says "we can see, and it is not there" — only
  the second is evidence.
  **H-CMD2 REFUTED as stated:** Ohio is weaker than Colorado, not equal.
  **The Colorado method does NOT transfer to neutral-pH coal drainage.**
  **Boundary, not a dead end — this is a null at 30 m in 60 m circular buffers.**
  Leading remaining explanations, both testable: (a) sampling geometry — Ohio
  streams are metres wide, so the buffer is mostly floodplain even leaf-off;
  (b) neutral-pH ochre is concentrated at the seep face, i.e. a few square
  metres, sub-pixel at Landsat. Both point the same way and give the **most
  specific UAV justification yet** — not the generic resolution claim Colorado
  refuted, but a measured geometry argument in a watershed where the satellite
  has now been shown to see the ground and still find nothing.
  **NEXT: riparian-only sampling** (channel-adjacent pixels, not circular
  buffers) — cheap, and directly tests the leading explanation.
  **Also fixed: the recurring GEE memory failure. 5/5 completed including
  Sunday Creek** (failed twice before). Cause was compute-GRAPH size, not batch
  size — a median over hundreds of scenes cannot be BUILT; capping at the 120
  least-cloudy scenes fixes it deterministically. Same fix that completed
  Silverton S2 after four failures.
  → [`ARM_CMD1_LEAFOFF_2026-08-16.md`](ARM_CMD1_LEAFOFF_2026-08-16.md)
- **★ CMD/OHIO: THE CANOPY BLOCKS THE MEASUREMENT — terrain-dependent finding
  (2026-08-16, CMD1).** Pre-registered before extraction, including the canopy
  diagnostic that produced this verdict. At 30 m over Ohio coal-basin streams,
  60 m buffers are **closed forest canopy**: median NDVI **0.870** (p90) /
  **0.791** (mean), p10 0.660, only 5.1% below 0.4. Pixels survive the water
  mask (median 26/buffer) — they are trees. **Verdict UNINTERPRETABLE, NOT a
  null**: the measurement never reached the water, so H-CMD1/H-CMD2 are
  **untested, not refuted**. Every index shows inconsistent signs across
  watersheds, exactly as looking at canopy should.
  **Why this beats a null:** placed beside Colorado it gives a TERRAIN-DEPENDENT
  result. Open alpine Colorado → detection J +0.30, dose-response +0.568, and
  resolution provably NOT the constraint. Forested Ohio → not measurable at all,
  and the barrier is **optical access**, not chemistry or bands.
  **Instrumentation consequence, and it is terrain-specific:** the 2026-08-16
  refutation of "resolution is the constraint" is **Colorado-only**. Under
  closed canopy no band configuration and no nadir pixel size helps; what
  changes the measurement is imaging **beneath/between canopy** — low-altitude
  UAV along the channel, off-nadir, or **leaf-off timing**. This is a stronger
  and more specific drone justification than the resolution argument ever was,
  and it applies to the terrain the PhD targets.
  **Also confirmed on real data:** Ohio CMD is genuinely neutral-pH (median
  7.46–7.72, five watersheds), and Ohio has **1** mine-discharge source point vs
  Colorado's 86, so the target-vs-control design does not transfer.
  **NEXT, cheap and obvious: leaf-off (Nov–Mar) composites** — a declared
  departure from the SIM 3466 May–Jul season, which exists for mineral mapping
  in open terrain, not for seeing under a canopy.
  → [`ARM_CMD1_OHIO_2026-08-16.md`](ARM_CMD1_OHIO_2026-08-16.md)
- **★★ THE WATER-ARM RESULT: the score tracks CONTAMINATION, and the in-stream
  failure was our own control design (2026-08-16, B2d).** Pre-registered
  `56aa3aa` before any analysis, with published EPA thresholds.
  **(a) The failure was an artifact.** 104 of 446 in-stream "controls" had
  measured Fe ≥ 1.0 mg/L — AMD-affected water used as a *negative class*. With
  controls defined by chemistry instead of station type, worst-case LORO J goes
  **0.178 → 0.297**, clearing the 0.25 bar. *(Original 0.178 retained.)*
  **(b) The discriminating test — never run before — settles what the score
  responds to.** Median score is **monotone in measured contamination**:
  C1clean −0.718 (n=222) < C1grey −0.211 (n=86) < **target +0.899** (n=86) <
  **C1dirty +1.157** (n=133). Contaminated streams *without* mine
  infrastructure score **above the mine discharge points themselves**. → **the
  score responds to WATER CHEMISTRY, not to the presence of a mine.** This also
  explains J = −0.311 vs C1dirty: it cannot separate targets from contaminated
  streams *because both are AMD-affected* — correct behaviour the old control
  design scored as failure.
  **(c) THE CLEANEST CLAIM IS ONE BAND RATIO.** `FerricIron1` (red/blue) used
  **continuously** clears the bar unaided on all three decision tiers:
  **C1clean +0.298, C2 +0.291, C3b +0.318**. The 8-feature model ties it on the
  primary tier (0.297 vs 0.298) so the verdict is **PARTIAL** by the letter of
  the rule — but the single index is the simpler, more transferable headline.
  **MAY claim:** separates AMD-affected from chemically-verified clean water at
  monitored locations, out-of-region, monotone in contamination.
  **MAY NOT claim:** finds unknown sources in blind search — tested 2026-09-15, not
  supported ([`ARM_BLIND_SEARCH_2026-09-15.md`](ARM_BLIND_SEARCH_2026-09-15.md)).
  → [`ARM_B2D_CHEM_CONTROLS_2026-08-16.md`](ARM_B2D_CHEM_CONTROLS_2026-08-16.md)
- **⭐ GOING CONTINUOUS SOLVES THE BARE-GROUND PROBLEM (2026-08-16, B2c).**
  Pre-registered `6af0b5b` before any fitting. Against NLCD bare ground, an
  8-index continuous model scores worst-case LORO **J = +0.617** (all folds
  +0.62 to +0.88) where the **binarised** classifier scored **0.000** under two
  different threshold references, and the single index +0.318. **Binarisation
  was destroying the signal.** Baseline reproduction check passed exactly, and
  the model null (refit per draw) gives p = 0.0020 at every tier — the floor
  for 500 permutations.
  **BUT the verdict is PARTIAL, not success:** against in-stream controls (the
  pre-registered PRIMARY tier) the model scores **0.178** — under the 0.25 bar
  **and worse than `FerricIron1` alone (0.234)**. Not shipped.
  **Capability is now bounded on both sides:** separates mine discharge from
  *land* reliably and out-of-region; does **not** separate it from *other
  monitored water features* in the same district.
  **On Landsat the combination does real work** (C1 0.228 vs single index
  −0.019) — the multi-index model substitutes for sensor quality rather than
  adding to it. **3 of 8 coefficients flip sign across folds**
  (`ClaySulfateMica`, `GreenNIR`, `NDVI_stress`); the ferric/iron indices are
  stable, paper2's vegetation indices are not.
  → [`ARM_B2C_CONTINUOUS_2026-08-16.md`](ARM_B2C_CONTINUOUS_2026-08-16.md)
- **The bare-ground fix FAILED, and the failure is informative (2026-08-16).**
  Pre-registered (`df6a6ae`) before any run. The mechanism check passed
  **16/16** — v3's thresholds really were mis-referenced (whole-region
  `mean+0.5σ` sat far below typical bare ground; `IronSulfate` at Ouray −2.334
  vs −0.399). **But correcting it changed nothing:** all 8 grid points give
  worst-case LORO J **−0.452 to 0.000** vs NLCD bare ground (corrected for tied
  scores; printed as 0.000), AUC **0.34–0.50**,
  identical to v3. **H-mech supported, H-fix refuted** — a confirmed mechanism
  is not a sufficient cause. **v4 was NOT shipped**, per the pre-registered
  gate. → [`ARM_B2B_CLASSIFIER_FIX_2026-08-16.md`](ARM_B2B_CLASSIFIER_FIX_2026-08-16.md)
- **⭐ THE SHARPEST OPEN LEAD: continuous beats binarised.** Same 86 points,
  same control: `FerricIron1` **continuous** (p90) = **J +0.318**;
  `AMDclassFrac` **binarised** ≤ 0 at two different threshold references: v3
  −0.252, v4 best 0.000. Both are corrected for tied scores; the reports printed
  0.000 for both (audit 2026-09-15, item 9).
  The information is in the imagery; thresholding discards it. Two post-hoc
  explanations, both UNTESTED and neither citable as a finding: (a)
  binarisation destroys the magnitude carrying the signal; (b) in a mineralised
  belt, iron-bearing bare ground is not diagnostic of AMD, so a "bare + iron"
  classifier describes regional geology. Tests for each are written in the
  report.
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
- **Does the Arm A sign-flip track geology?** ⚠ **Corrected 2026-09-14 — the
  grouping below is geologically wrong.** Creede lies in the central San Juan
  caldera cluster (USGS I-2799) and Lake City in the western San Juan caldera
  complex (USGS I-962), so Creede belongs with Silverton and Ouray — and at
  −0.800 it runs *against* the idea. Labels must be defined on one explicit
  axis (volcanic setting vs deposit style) from a citable source before any new
  region's sign is seen. → `AUDIT_2026-09-14_ARMA_AND_TOOLING.md` §3.
  *Original text, unedited:* Silverton +0.714 and Ouray +0.667
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

### NEXT — as of 2026-09-16 (start here)

**Author actions (not analysis):**
1. **Zenodo — NOT updated yet.** The archive is still v3.10.0 (2026-09-13).
   Everything since exists only on GitHub: the `amdtool` package, audits
   2026-09-14/15, the blind-search result, and the narrowed severity claim.
   Steps: `docs/HOW_TO_TEST.md` §E.
2. **Run the SpectraLab AMD module in the UI.** It lives on branch
   `feature/amd-severity-module`; it is **not released**, SpectraLab is **not
   installed as an app**, and `SpectraLab-0.39.0.exe` does **not** contain it.
   Steps: `docs/HOW_TO_TEST.md` §C. This is the one gate item still open.
3. **Decide:** merge the branch and cut SpectraLab 0.40.0, or keep it on the
   branch.
4. Review `.private/EB2_DOCUMENTATION.md` (deliberately untouched).

**Analysis, in value order:**

5. **Field campaign — REGISTERED 2026-09-19, Ohio first.**
   → [`FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md`](FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md).
   - **Order:** Piedmont, then Clendening, then Atwood (the sulfate control),
     sampling the **inflow streams**, not the open water.
   - **Verdict tests:** H-RANK-OH, H-UAV-OH, H-PRECIP and H-CONF.
   - **Estimation only:** H-LIMIT and magnetism.
   - **Colorado severity, H-DET and H-DISC** are carried to a later
     registration.
   - **Still to do before field day 1:** the station-list amendment (§10 of the
     registration), which holds the placed stations with a SHA-256, the drone
     camera, the cover-scoring protocol, and the lab.
6. **Snow-masked blind-search sensitivity: extraction STARTED 2026-09-19.**
   - Log: `data/matched/blindsearch_snowmask_extract.log`.
   - **Resume (skips finished districts):**
     `D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe python/blind_search.py --extract --snow-masked`.
   - When all seven `data/matched/blindsearch_s2_*_snowmask.csv` exist, run
     `--analyse`.
   - The verdicts do not depend on it.
7. The science leads from item 0 below: a PA disturbance covariate, a better
   Ohio covariate, an Arm A re-run (DEM catchments, global de-duplication,
   per-district σ), and geology labels fixed before any new region's sign is
   seen.

### Field-campaign registration, 2026-09-19 (no field data yet)

**Why Ohio first:** the author's lakes are near the lab, which the supervisor
prefers; the drones are easy to take there; travel costs less. That reverses
`FIELD_CAMPAIGN.md`'s "Dropped: Ohio reservoirs", but not its reason. **The lake
water column stays a measured null and is not re-tested.**

**Archival chemistry fetched before writing** (disclosed in §9 of the
registration; `report_ohio_lakes_archive_2026-09-19.txt`):
- **Clendening Lake** (never analysed before): in-lake sulfate median 310 mg/L
  (n=25). Its 16 inflow stream stations span **12–1,370 mg/L**, with dissolved
  Fe median **17 µg/L** (n=24).
- **Piedmont's catchment:** 8 stream stations span **15–967 mg/L**, with
  dissolved Fe median **11 µg/L** (n=16).
- **pH** is 7.1–9.0 throughout. The iron has left the water, which is why the
  drone test is scored against **measured precipitate cover**, not chemistry.

**Out-of-sample test:** neither catchment was among CMD1–3's five Ohio
watersheds. H-RANK-OH is therefore an out-of-sample test of the standing Ohio
claim.

**Power** (`report_field_power_2026-09-19.txt`):
- **51 inflow stations per catchment** gives power 0.83 at |ρ| 0.40;
- **42** is the minimum, 0.83 at the archival Ohio |ρ| 0.438;
- the confound-adjusted |ρ| 0.246 would need 132, so it is estimate-only.

### Record of the round that led here

**Blind-search test — REGISTERED 2026-09-14; RESULT 2026-09-15 (below).** → [`BLIND_SEARCH_PREREGISTRATION_2026-09-14.md`](BLIND_SEARCH_PREREGISTRATION_2026-09-14.md),
with a site list fixed from station metadata only (321 rows, SHA-256
`6ee8aec0…eb5`). Two co-primary hypotheses, Holm-corrected: **H-BS1** — 32 mine
sites in never-analysed Alma, Creede and Lake City (power at a threefold lift
**0.54**, at recall 0.20 **0.80**); **H-BS2** — 50 mine sites from unused
stations in the four analysed districts (**0.64** / **0.90**). **Spring-only
sites were moved out of the primary set before any score existed:** 43 of
H-BS2's 93 sites were springs, which would have made half of that test a
spring-finder. Scored against a −NDVI bare-ground baseline; verdict rows are
DISCOVERY SIGNAL / NOT BETTER THAN BARE GROUND / NO SIGNAL DETECTED.

**Blind-search analysis code — completed 2026-09-15, before any analysis ran.**
Checked against the registration on synthetic districts only. §9's
link-distance sensitivity and §10's frame notice were missing; both are now
implemented and tested. The snow-masked sensitivity still needs its own
extraction once the primary extraction finishes.

**Blind-search RESULT, 2026-09-15 — no evidence the tool finds mine sources it
was not told about.** → [`ARM_BLIND_SEARCH_2026-09-15.md`](ARM_BLIND_SEARCH_2026-09-15.md)

- **H-BS1: NO SIGNAL DETECTED.** 4 of 32 sites flagged at a 5% budget, recall
  0.125 [0.050, 0.281], p = 0.074; one site short of the registered bar. Power
  was 0.54 at a threefold lift, so a modest lift is not excluded.
- **H-BS2: NOT BETTER THAN BARE GROUND.** Recall 0.280 (p = 1e-7), but McNemar
  p = 0.038 against its Holm level of 0.025 (12 vs 4 discordant sites).
- Flagged ground is 1.2–4.4× enriched for NLCD barren land.
- All seven districts extracted; none FAILED. The run spanned two sessions (Ouray
  and Silverton re-extracted with behaviour-identical code) and survived
  intermittent Earth Engine 5xx errors and two local DNS outages.
- **Not run:** the snow-masked sensitivity.
- The 40-cluster field frame is a sampling frame, not detections; visiting it
  as candidate sources is not supported.

**Rule fixed now, before any result:** a district that stops on a transient
Earth Engine service error (HTTP 502/503, seen intermittently during Ouray) is
re-extracted, **not** declared FAILED. The registration reserves FAILED (§11)
for a district that cannot be extracted after the safe memory levers (band
subset, batch floor 1). The scene cap and composite stay unchanged.

**Field campaign — pre-register before the first field day.** Design in
`docs/FIELD_CAMPAIGN.md`: H-RANK, H-DET, H-LIMIT, H-PRECIP, H-DISC, H-UAV, each
with mutually exclusive verdict rows. Recommended: **144** stations across 4
Colorado districts (9 per iron tier), **~80** discovery visits, **90** stations
across Huff Run / Clearfield / Moshannon for the UAV comparison.

0. **Pursue the SIGN, not the scale — that is what replicated (post-CMD3).**
   A negative vegetation–sulfate/conductance association now holds in **two**
   independent coal basins and, in Pennsylvania, **across three disjoint
   sub-basins** (conductance −0.187, n=443, p=0.0002, sign-consistent at
   30/60/100 m). Its *scale* is basin-specific and its magnitude is weak
   (0.14–0.19). The claim worth pursuing is the direction and its consistency.
   a. **A Pennsylvania disturbance covariate — the single biggest gap.** PA DEP
      mine-drainage / abandoned-mine-land data is the ODNR analogue and would
      make the PA result conditionable. It is currently **unconditioned** and
      cannot be conditioned with anything available.
   b. **A better Ohio covariate.** ODNR historic coverage is incomplete by
      construction, so CMD2's surviving −0.246 is most plausibly land cover the
      covariate missed. Reclamation-era / spoil mapping tests that directly.
   c. **STOP using radius shape to infer mechanism.** It gave opposite answers
      in two basins of the same drainage type. If mechanism is the question it
      needs a design that varies mechanism, not footprint.
   d. **The basin-geometry hypothesis** (Ohio's dissected plateau vs the West
      Branch's broader valleys) was generated by looking at these two results
      and **cannot be tested on them**. It needs a third basin with the
      prediction fixed in advance.
   e. **The 1 km / 5 km disc sign consistency, on data that did not generate
      it.** Still circular — the same data suggested it and scored it.
   Also: **more Ohio sulfate coverage.** Two of five watersheds run at n=12,
   and n=12 is what decides sign consistency there.
1. ~~**Test whether Arm A's sign-flip tracks geology** on the existing
   31-catchment dataset.~~ **Withdrawn as written, 2026-09-14.** That dataset
   *generated* the idea, so it cannot test it; its grouping mislabels Creede
   (central San Juan caldera cluster); and its 31 rows are 28 distinct polygons,
   three shared across regions. A real test needs **new regions labelled on
   one explicit axis from a citable source before their signs are seen**, plus
   an Arm A re-run with global de-duplication and per-district σ thresholds.
   → `AUDIT_2026-09-14_ARMA_AND_TOOLING.md`
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
   PROVEN above. **All three follow-ups below were DONE in August 2026:** C3b
   amendment 2026-08-15, leave-one-region-out 2026-08-14, and Sentinel-2 +
   resolution ladder 2026-08-15/16. They were re-audited on 2026-09-15
   (`AUDIT_2026-09-15_B2_REPRODUCTION.md`) and are kept here for the record:
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

- **Earth Engine credentials resolve in ONE place: `python/ee_auth.py`.**
  Order: `$GEE_SERVICE_ACCOUNT_KEY` → the author's legacy key path →
  `$GEE_PROJECT` with personal `earthengine authenticate` credentials → a
  RuntimeError with setup steps. `python python/ee_auth.py` checks it.
  **Never re-add a `KEY` constant to a module** — that is how five copies
  pointing into a sibling repository accumulated.
- **Verify a number against RAW output, never against another summary.** The
  land-arm 0.440 was cited in five documents but existed only in prose; every
  prior check had compared one summary with another.
- **Two venvs.** GEE work needs `D:/dev/VPCA+STEPWISE-REGRESSION/.venv`
  (`ee` + `rasterio`); the repo `.venv` has no `ee`. Cost a wasted run already.
- **⚠ BOTH VENVS BREAK ON A MACHINE REINSTALL, and the error does not say so.**
  `pyvenv.cfg` pins `home` to an absolute path under the *old* user profile, so
  after a reinstall every interpreter call dies with
  `No Python at '...\ahusse12\...'` — while `site-packages` is perfectly intact.
  **Fix (2026-09-08, done):** install a matching CPython (`uv python install
  3.11` — the wheels are cp311, so 3.11 specifically) and repoint `home` and
  `executable` in both `pyvenv.cfg` files. Nothing needs reinstalling.
  Two wrinkles: uv's minor-version **junction** (`cpython-3.11-...`) does not
  execute reliably here, so point at the **versioned** directory; and `git`
  refuses the repo for "dubious ownership" after the SID change, fixed with
  `git config --global --add safe.directory D:/dev/Sulfate-Methos`.
- **EE "User memory limit exceeded" is about compute-graph size, not pixel
  count** — `bestEffort=True` does not help. Fix by tiling the reducer
  (`tile_geoms` + `tiled_mean_stddev`) and materialising stats to Python floats
  so downstream calls don't re-evaluate them.
- **The memory trap has THREE levers, not one (2026-09-08).** Scene depth (cap
  at 120), batch size (halve to a floor of 2) — **and BAND COUNT**, which was
  not previously recorded. Sunday Creek failed a *third* time at the batch floor
  on 1000 m buffers with the scene cap already applied; extracting only the band
  under test (`cmd_detect.py --bands NDVI_stress`) completed it with one retry.
  **Verified identical, not assumed:** one-band vs eight-band extraction of the
  same stations gives max absolute difference **0.000**. Reach for the band
  subset before touching the composite — it is the only one of the three levers
  that provably does not change the numbers.
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
