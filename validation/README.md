# Validation Log — AMD Detection v2

Independent VPCA spectral-library validation (Ortiz-lab method) of the
classifier. Each run: export a per-pixel CSV from the GEE tool, run
`python/vpca_validation.py`, save the report here. Method &
interpretation: [`specs/amd-v2/validation-protocol.md`](../specs/amd-v2/validation-protocol.md).

**Primary metric = AUC** (threshold-free): does the VPCA ferric-component score
rank the classifier's iron-sulfate pixels (classes 9,12,14,17,18,19) above the
rest? 0.5 = no relation, 1.0 = perfect. Cohen's κ is prevalence-biased for rare
AMD and is reference-only.

## Results

| Date | Site | Type | Sensor | Pixels | Ferric comp? | Iron-sulf. % | AUC | Verdict | Report |
|------|------|------|--------|--------|--------------|--------------|-----|---------|--------|
| 2026-07-22 | Silverton, CO | known AMD | Landsat 8 | 20000 | yes (jarosite, \|r\|=0.96) | 1.12% | **0.961** | sensitivity ✓ | [report](report_Silverton_AMD_20260722.txt) |
| 2026-07-22 | Atwood Lake, OH | clean control | Landsat 8 | 20000 | **none** | — | n/a | specificity ✓ | [report](report_AtwoodLake_control_20260722.txt) |
| 2026-07-22 | Silverton, CO **(v2.3.0 re-baseline)** | known AMD | Landsat 8 | 20000 | yes (jarosite, \|r\|=0.96) | 1.12% | **0.961** | sensitivity ✓ | [report](report_Silverton_AMD_v230_20260722.txt) |
| 2026-07-22 | Atwood Lake, OH **(v2.3.0 re-baseline)** | clean control | Landsat 8 | 20000 | **none** | — | n/a | specificity ✓ | [report](report_AtwoodLake_control_v230_20260722.txt) |

**Re-baseline note (v2.3.0):** after adopting the Test C thresholds the closure
AUC is *identical* (0.961, same 225 iron-sulfate px) — verified not-stale by
diffing class distributions: the scene classification changed heavily (Major
Ferric class 2: 942→79 px; SparseVeg+Ferric class 13: 5118→698; unclassified
1863→6345), but iron-sulfate **group** membership is gated only by the
unchanged provisional iron threshold (0.10), so the same pixels redistribute
among subclasses 9/12/14/18/19. The closure metric is invariant to the four
adopted thresholds by construction — headline figures are valid for v2.3.0.

## Interpretation

The pair is the validation figure:
- **Silverton (known AMD):** VPCA independently recovers a jarosite/ferric
  component; its spatial score co-locates with the classifier's iron-sulfate
  classes at **AUC 0.961 (excellent)**. The tool's AMD calls are backed by
  first-principles spectroscopy, not manufactured by the index.
- **Atwood Lake (clean control):** VPCA recovers **no ferric component** — clay
  and vegetation only. No false AMD signal where none should exist.

High agreement where AMD exists, none where it doesn't = sensitivity and
specificity demonstrated with an independent method.

## Test C — Threshold derivation (2026-07-22, Silverton, Landsat 8)

Labelled pixels: **126 AMD / 447 clean** (`amdPolygons` = Red Mountain gossans;
`cleanPolygons` redrawn to include bare-rock **hard negatives** after a first
attempt with vegetation-only negatives gave inflated AUC = 1.0 across the
board). Data: `Thresh_Landsat8_Silverton__CO_20260722-v2.csv` ·
Report: [report_Silverton_thresholds_20260722.txt](report_Silverton_thresholds_20260722.txt)

| Index | AUC | Youden thresh | sens | spec | Adopted? |
|---|---|---|---|---|---|
| IronSulfate | 0.769 | -0.732 | 1.00 | 0.71 | **NO — fails ≥0.8** (kept provisional 0.10) |
| FerricIron1 | 0.992 | **1.983** | 0.98 | 0.95 | yes (was 1.4) |
| FerricIron2 | 0.997 | **3.758** | 0.98 | 0.97 | yes (was 2.5) |
| FerrousIron | 0.983 | **0.959** | 0.96 | 0.91 | yes (was 1.05) |
| ClaySulfateMica | 0.999 | **0.021** | 0.97 | 1.00 | yes (was 0.12) |

**Findings:**
- The corrected IronSulfate (2/1 − 5/4) index separates AMD from vegetation
  but **not from non-AMD bare rock** (spec 0.71); its Youden cut sits below
  scene background (p90 ≈ -0.01) and is unusable as a scene-wide threshold.
  At Silverton the discrimination is carried by the ferric indices. Report
  this as a finding, not a defect.
- Methodological note: with vegetation-only clean polygons every index scored
  AUC ≈ 1.0 and `lon` alone scored 0.974 — a spatial-confounding red flag.
  Hard negatives are mandatory for honest AUCs; recorded here so the pitfall
  isn't repeated.
- Adopted values are Silverton/L8-derived; re-derive before trusting on
  desert/humid scenes (esp. ClaySulfateMica 0.021, which is site-tight).

## Test D — Water contamination — ⚠️ RETRACTED 2026-07-25

> **The 2026-07-23 Test D result below is withdrawn. Do not cite it.**
> Neither the Ganau "detection" nor the Piedmont/Atwood "clean" readings were
> valid measurements. Reports `report_{Ganau,Piedmont,Atwood}_water_20260723.txt`
> are retained only as a record of the retracted run.

**Original (invalid) claim:** Ganau matched an Fe³⁺-stained-water end-member
(3/3 components, 99.5% variance) = water sensitivity confirmed; Piedmont and
Atwood matched clear water.

**Why it is invalid — three independent defects:**

1. **No water pixels were analysed.** The run decomposed whole scenes instead
   of filtering to `water_class >= 0` as §D of the protocol requires. Piedmont
   and Atwood carry **zero** water-classified pixels, so their "clear water"
   verdict was computed from ~20,000 mostly-*land* pixels.
2. **The tool's water mask is calibrated to a single site.** `AWEINSH > 0.20`
   in `createUnifiedWaterMask()` was tuned on Ganau (see the code comment
   citing "Ganau Lake testing: Real water AWEINSH=0.249"). AWEInsh is an
   absolute-magnitude index, so it scales with brightness:

   | Scene | optically water (MNDWI>0.3) | pass AWEINSH>0.20 | median AWEINSH | median brightness |
   |---|---|---|---|---|
   | Ganau | 230 | **230** | 0.229 | 0.076 |
   | Piedmont | 497 | **0** | 0.070 | 0.022 |
   | Atwood | 466 | **0** | 0.072 | 0.020 |

   Dark temperate reservoir water can never pass. Two further Ganau-tuned
   gates (`brightness ∈ (0.05, 0.20)` on every scoring criterion, and
   `DepthProxy < 1.3`) each independently exclude the Ohio lakes as well.
   **Piedmont's "no contamination" was an artifact of the mask, not a
   measurement.**
3. **The water end-members are invented.** `fe3_water` / `clear_water` in
   `vpca_validation.py` are hand-written vectors, not library spectra —
   splib07 is a *mineral* library and contains no water-column optics. Run on
   water pixels only, the matching is degenerate: Ganau returns `fe3_water`
   for all three components at weak r = 0.46–0.89, while Piedmont/Atwood
   return `green_veg` dominant (i.e. `MNDWI > 0.3` alone admits mixed
   shoreline pixels).

**Also corrected:** Ganau's ground truth is **675 mg/L sulfate**
([METHODOLOGY.md](../docs/METHODOLOGY.md)), not Fe³⁺ as the retracted table
stated. The distinction is physical, not cosmetic: SO₄²⁻ has **no VNIR
absorption**. No optical sensor can see sulfate. Any optical detection is of
iron, turbidity or colour that happens to *co-vary* with sulfate, and must be
worded that way.

### Water mask rebuild — v2.4.0 (2026-07-25)

The mask is now magnitude-free: `MNDWI > 0.3 ∧ AWEInsh > 0 ∧ NDVI < 0 ∧
NIR < Green ∧ Brightness < 0.30`. The brightness **ceiling** is kept on purpose
— snow/ice passes all four spectral tests and is separable only by albedo.

| scene | water px before | water px after |
|---|---|---|
| Ganau (AMD+) | 230 | **230** (no regression) |
| Piedmont | **0** | **255** |
| Atwood (clean control) | **0** | **365** |
| Silverton (land control) | 2 | 11 / 20000, all class 0 (no mineral pixels stolen) |

`NDVI < 0` was checked against the positive control before adoption: Ganau
water is NDVI ≤ −0.12 at the 95th percentile, so the strict cut costs the
contaminated site nothing, while looser cuts increase land leakage at
Silverton (11 → 20 px).

**New class 3 = INDETERMINATE.** The reliability gate (`brightness ∈
(0.05, 0.20)`) is retained — testing showed relaxing it makes the **Atwood
clean control read 244/365 px "moderate"** and drops Ganau from 98 severe px
to 0, because `B4/B2` and `B3/B2` are noise-dominated at ρ ≈ 0.02. What
changed is the consequence of failing it: such water is now reported as
INDETERMINATE rather than silently scoring 0 and being labelled "clean".

| scene | water | clean | mod | severe | INDETERMINATE |
|---|---|---|---|---|---|
| Ganau (AMD+) | 230 | 0 | 132 | 98 | **0%** |
| Piedmont | 255 | 0 | 0 | 0 | **100%** |
| Atwood (clean ctl) | 365 | 0 | 0 | 3 | **99%** |
| Silverton (land ctl) | 11 | 0 | 0 | 0 | 100% |

**Honest limitation:** no pixel in any of these four scenes now classifies as
"clean" — the only water bright enough to measure is Ganau's contaminated
water. Optical **specificity is therefore untested**, not passing, under
v2.4.0. Atwood's 3 residual "severe" px (0.8%) are likely mixed shoreline.
Resolving specificity is what the VPCA material-identification path is for.

### Finding W1 — the water contamination indices are inverted (2026-07-25)

Computed on v2.4.0 water pixels (Ganau 230, Piedmont 255, Atwood 365):

| site | yellow (G/B) | turbidity (R/B) | iron idx | NIR | red/blue |
|---|---|---|---|---|---|
| Ganau — 675 mg/L sulfate | 1.25 | 0.85 | 0.53 | 0.044 | **0.85** |
| Piedmont | 1.93 | 1.21 | 0.55 | 0.016 | 1.13 |
| **Atwood — clean control** | **2.39** | **1.48** | **1.09** | 0.012 | **1.35** |

**Every ratio-based contamination index is highest at the clean control and
lowest at the contaminated site.** The ranking is inverted. Only NIR anomaly
orders correctly, and NIR is raised by suspended sediment and atmospheric path
radiance as much as by dissolved iron.

**Physical check:** Fe³⁺ absorbs strongly in the blue, so ferric-stained water
must *rise* from blue to red. Ganau's red/blue = **0.85 — it falls.** Ganau
water shows **no ferric signature**. The only scene showing a ferric-like rise
is Atwood, the clean control (and at ρ≈0.014 its ratios are noise-dominated,
which is why the reliability gate exists).

**Consequence:** Ganau scores "severe" not because its indices indicate iron,
but because it is bright enough to pass the reliability gate while Atwood and
Piedmont are silenced by it. The module is responding to **brightness and
turbidity, not contamination**. Combined with the fact that the thresholds
were tuned until Ganau scored severe, the v1.5.4–v2.4.0 water claim is
**circular and unsupported**.

This is not necessarily a physics failure at Ganau: its ground truth is
**sulfate**, which is optically invisible. A site can carry 675 mg/L SO₄²⁻ with
little dissolved Fe³⁺ and correctly show no ferric colour. What is unsupported
is the inference *from* the optical indices *to* "severe contamination".

### Finding W2 — 5-band material ID does not discriminate

Reproduced the lab pipeline's stepwise identification
(`D:\dev\VPCA+STEPWISE-REGRESSION`) on its own reference loadings:

| site | expected | curated-12 result |
|---|---|---|
| Vaal Dam (Witwatersrand mining) | AMD | VPC6 → `Acid Mine Dr Assemb2-Fe3+`; VPC2/3 → jarosite ✓ |
| **Indian River Lagoon (FL, no mining)** | **no AMD** | **VPC2 → Jarosite R²=0.96; VPC4/5 → Ohio Fe concretions** ✗ |

A Florida coastal lagoon returning jarosite is a false positive. With **N = 5
observations** (5 water-penetrating S2 bands) any single library spectrum
reaches R² ≈ 0.9 by chance, with or without curation — consistent with the
lab's own caveat in `docs/REAL_GEE_RUN_RESULTS.md`. Per-component material ID
at 5 bands is a **hypothesis generator, not a discriminative test**, and must
not be used to certify a lake as AMD-positive.
Curated candidate set retained at `python/library_s2_amd_curated.csv`.
Note: **schwertmannite is absent from both lab libraries.**

### Finding W4 — ground truth resolves it (2026-07-25)

From the **Water Quality Portal** (USGS NWIS + EPA STORET + Ohio EPA), in-lake
stations, 2013 onward:

| lake | sulfate median | range | iron median | iron max |
|---|---|---|---|---|
| **Piedmont** (n=26) | **462 mg/L** | 374–560 | **162 µg/L** | 1,530 |
| **Atwood** control (n=101 SO₄ / 86 Fe) | **18.3 mg/L** | 10.6–23.1 | **302 µg/L** | 2,750 |
| Ganau (published) | 675 mg/L | — | never measured | — |

1. **Piedmont IS contaminated** — 462 mg/L sulfate, 25× the control and the
   same order as Ganau. The site selection was right; the CMD legacy is real.
2. **Atwood is a valid control for sulfate but NOT for iron** — its iron is
   *higher* than Piedmont's (though 80/86 values are Total Recoverable, so
   partly suspended sediment). Iron-phrased specificity claims are invalid.
3. **Neither lake is optically detectable.** Sulfate has no VNIR absorption at
   any concentration; 0.16–0.30 mg/L iron is 1–2 orders of magnitude below
   visible ferric colouring.

**The complete answer to "why does Piedmont show nothing":** it is
sulfate-contaminated, sulfate is invisible, and its iron has already
precipitated out of the water column (circumneutral CMD). The negative is
physically correct — but it was reached for the wrong reason, because the mask
had excluded the lake entirely.

Full write-up, next steps and PhD field-campaign design:
[WATER_VALIDATION_REPORT_2026-07-25.md](WATER_VALIDATION_REPORT_2026-07-25.md)

### Finding W3 — the only defensible comparison so far

Albedo-normalised band fractions (magnitude removed), ROC AUC vs the Atwood
clean control:

| feature | Ganau vs Atwood | **Piedmont vs Atwood** |
|---|---|---|
| fB1 (443 nm) | 0.986 | **0.780** |
| fB2 (482 nm) | 0.996 | **0.731** |
| fB3 (561 nm) | 0.005 | 0.270 |

**Ganau vs Atwood is confounded** — different continent, atmosphere (Iraqi
dust inflates blue), water type and depth. Its AUC ≈ 0.99 cannot be attributed
to contamination.

**Piedmont vs Atwood is the fair test**: same region, same sensor, same date
range, same atmospheric correction. It shows a real but *moderate* difference
(AUC ≈ 0.78 in the coastal/blue fraction) — enough to say the two lakes differ
spectrally, not enough to attribute the difference to AMD rather than to
turbidity, depth, or algae.

**What would settle it:** dissolved-iron measurements (not sulfate) for
Piedmont and Atwood, from USGS NWIS / Ohio EPA. That is the missing input, and
no amount of reprocessing substitutes for it.

**Replacement approach** (see `specs/amd-v2/validation-protocol.md`): water
validation moves to the Ortiz-lab VPCA + stepwise pipeline
(`D:\dev\VPCA+STEPWISE-REGRESSION`), which works on z-scored **derivative**
spectra — brightness-invariant by construction, so dark water is not a special
case — and matches against the real splib07 library that already contains
`Acid Mine Dr Assemb2-Fe3+`, `Jarosite GDS24 Na`, ferrihydrite and goethite.
Deliverable is **material identification per lake**, not concentration: no
measured water chemistry exists for these sites beyond Ganau's single number.

### Finding L1 — the land thresholds do not transfer between sites (2026-07-26)

Full diagnosis: [GATE_DIAGNOSIS_2026-07-26.md](GATE_DIAGNOSIS_2026-07-26.md).
Code: `python/diagnose_veg_gate.py`, `python/iron_index_transfer.py`.

Head-to-head against Rockwell's published USGS map, paired on identical pixels
through one code path:

| | Silverton (thresholds derived here) | Summitville (never tuned) |
|---|---|---|
| exact class agreement | 88.1% | **64.6%** |
| Cohen's κ | 0.552 | **0.080** |
| Rockwell AMD / ours | 0.47% / **1.94%** | **2.13%** / 0.38% |
| recall vs Rockwell | 0.485 | **0.106** |

The direction of disagreement **reverses**: we over-call 4.1× where the
thresholds were derived and under-call **5.6×** at an independent Superfund AMD
site. Conditioning on our own land mask sharpens it (7.11× / 0.33×), so it is
not a masking artifact.

**Root cause.** All six AMD classes require `IronSulfate = (B2/B1) − (B5/B4)`
to exceed an absolute 0.10. That index scores **AUC 0.938** against reference
labels at Silverton but **0.678** at Summitville, and its Youden-optimal cutoff
flips sign (+0.0906 → −0.0464). Scene-relative thresholding (within-scene
z-score calibrated at Silverton) lifts Summitville recall 0.197 → 0.307, **+56%
relative**, but cannot repair the AUC loss.

This is the **same defect class as W1** — an absolute cutoff on a non-normalised
index calibrated at a single site — now documented on the land arm too. Test C
had already flagged IronSulfate at AUC 0.769 as "unusable as a scene-wide
threshold"; keeping 0.10 as "provisional" is what propagated the failure.

### Finding L2 — the green-peak vegetation gate is redundant (2026-07-26)

`noGreenPeak` (Green/Red ≤ 1.0) uniquely excludes **0 px at Summitville and 6 px
at Silverton** — pixels with a green peak already fail `NDVI < 0.25`. Running the
full classification with the gate `strict` / `relaxed` / `override` / `off` gives
**identical class histograms**. This falsifies the mechanism proposed in v2.8.0,
which is now corrected in place in the Rockwell report.

The binding term is `NDVI < 0.25`, which uniquely removes 29.3% (Silverton) and
22.3% (Summitville) of valid pixels, and costs **42–46% of Rockwell's AMD
pixels at both sites** before the cascade runs.

### Finding L3 — the EE memory limit was a tooling problem, not a real one

Silverton (15 km) and Red Mountain Pass (10 km) previously failed with
"User memory limit exceeded" and were thought to need async
`Export.table.toDrive`. `tile_geoms()` splits the AOI into an n×n grid and
accumulates per-tile results; Silverton now reduces 983,860 px and samples
31,888 px synchronously. Tiled sampling also clears the separate
"Collection query aborted after accumulating over 5000 elements" ceiling.
Multi-site threshold re-derivation is therefore unblocked.

### Finding L4 — the departures from SIM 3466 were the defect (2026-07-26)

Full audit: [REPLICA_AUDIT_2026-07-26.md](REPLICA_AUDIT_2026-07-26.md).
Code: `python/pool_labels.py`, `python/iron_criterion_search.py`,
`python/paper_faithful_test.py`. Source: `paper.pdf` = the SIM 3466 pamphlet.

**All six index formulas match the paper exactly** (`2/1−5/4`, `4/2`,
`4/2×(4+6)/5`, `(3+6)/(4+5)`, `6/7−5/4`, `5/4`), as does first-match-wins
assignment. The replica is faithful at the index level. Three departures are
not:

| # | SIM 3466 says | v2.4.0 did |
|---|---|---|
| D1 | thresholds from "a common **standard deviation threshold**" per scene | absolute constants from Silverton |
| D2 | "late May through early July are **optimal**"; mid-Jul–Oct warned against (dry vegetation mimics clay-sulfate-mica) | **Jul–Sep** |
| D3 | all six iron-sulfate classes require **clay AND** | catch-all `hasIron → 12`, no clay |

D3 collapsed the AMD decision to `hasIron` alone — which is why the whole AMD
arm inherited the behaviour of the index Test C had already failed at AUC 0.769.

**Leave-one-site-out over 3 sites, worst-case Youden J vs Rockwell:**

| configuration | MIN J | mean κ |
|---|---|---|
| as shipped (v2.4.0) | **0.107** | 0.139 |
| + paper season | 0.260 | 0.159 |
| + scene-relative cutoffs | 0.403 | 0.227 |
| + clay requirement (**v3.0.0**) | **0.440** (4.1×) | 0.257 |

Summitville J 0.107→0.440, κ 0.120→0.483; Silverton improves slightly;
**Red Mountain Pass regresses** (0.642→0.452) — a real trade-off, not yet
explained. Largest single gain anywhere: IronSulfate AUC at Summitville
**0.678→0.810** from the season change alone.

**Pooled re-derivation across 3 sites** (Test C used one): every Test C AUC
collapses — FerricIron1 0.992→0.642, ClaySulfateMica 0.999→0.674,
**FerrousIron 0.983→0.437 (below chance, no AMD discriminative power at any
site)**. Every shipped constant sits *inside* its per-site optimal range, but at
opposite ends: clay 0.021 vs Silverton optimum 0.248 (→ over-call there), iron
0.10 vs Summitville optimum −0.045 (→ under-call there). **Opposite errors at
opposite sites is exactly the inversion.**

⚠️ Labels are Rockwell's published map, not field data. This measures replica
fidelity, **not** accuracy. No claim that our tool beats theirs is supportable
without fieldwork.

## Still to do
- H2 note: the four ferric minerals are not separable at 7 bands (they identify
  as one "ferric" group); distinguishing them needs hyperspectral.
- ~~Threshold derivation (Test C)~~ **done 2026-07-22** (see above).
  ~~Open follow-up: IronSulfate failed vs bare rock~~ — **resolved as a
  confirmed defect, finding L1.** The follow-up is now: replace or renormalise
  the iron criterion and judge candidates by *recall stability across sites*,
  not within-site AUC.
- ~~Re-derive thresholds on **pooled** sites~~ **done 2026-07-26, finding L4.**
- ~~Reconsider `NDVI < 0.25`~~ **done 2026-07-26 (v3.0.1): relaxed to 0.35.**
  Swept 0.25-1.01 over 36,391 px / 3 sites: worst-case J 0.262 -> 0.317 (+21%),
  mean 0.313 -> 0.393 (+26%). Summitville recall 0.26 -> 0.51; Silverton and
  RMP unharmed - the only change so far that improves all three sites. The
  green-peak ceiling was swept jointly and moves worst-case J by <=0.001 at
  every combination, re-confirming L2 across a 2-D grid rather than one point.
- **Explain the Red Mountain Pass regression** (J 0.642→0.452 under v3.0.0).
  Only site where the paper-faithful config is worse. D8 (compositing) was the
  prime suspect and is now partly ruled out — see REPLICA_AUDIT §3c. Leading
  explanation is now small-sample noise (RMP has only 19–23 AMD positives).
  **Increase the RMP sample before treating the regression as real.**
- **D8 cannot be tested naively**: at 3,400 m the least-cloudy single May–Jul
  scene yields ZERO usable pixels at Red Mountain Pass and costs Silverton 60%
  of its land pixels. Compositing is a necessity here, not a gratuitous
  deviation. Proper test = select scenes by clear-pixel count INSIDE the AOI,
  and pool several scenes per site.
- **Calibrate `ferric1/2StdMult` and `ferrousStdMult`.** v3.0.0 sets them to 0.5
  by assumption; only iron and clay were LOSO-fitted. They drive classes 1–8,
  which nothing has validated.
- **Re-derive `clayStdMult`** — it did not transfer (per-fold fits −0.5, −0.5,
  +1.0) and is the weakest adopted constant.
- Measure the remaining departures D4–D6 (class 9/17 split uses brightness where
  Rockwell uses ferrous; water mask; atmospheric correction).
- Add sites outside Colorado (Marysvale UT, Goldfield NV already in `SITES`) —
  all three current sites are Colorado alpine, and the pamphlet warns behaviour
  varies most by climate.
- **Test D water validation: RETRACTED and being rebuilt** (see above). Work:
  (a) make the tool's water mask scene-independent so Piedmont/Atwood water is
  analysed at all; (b) re-run all three lakes on Sentinel-2 through the
  Ortiz-lab VPCA + stepwise pipeline for material identification. Concentration
  regression is **out of scope** — no lab chemistry exists for these sites
  beyond Ganau's single published sulfate value.
- Swap embedded end-members for the lab's Sentinel spectral library (exact
  spectra) via `convolve_splib07()`.

## How to add a run
1. GEE tool → pick area → **Export VPCA CSV** → run task → download CSV.
2. `.venv/Scripts/python python/vpca_validation.py --scene <csv> --sensor L8 --classcol class > validation/report_<Site>_<type>_<date>.txt`
3. Add a row to the table above.
