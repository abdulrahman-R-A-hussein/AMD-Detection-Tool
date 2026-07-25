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

**Replacement approach** (see `specs/amd-v2/validation-protocol.md`): water
validation moves to the Ortiz-lab VPCA + stepwise pipeline
(`D:\dev\VPCA+STEPWISE-REGRESSION`), which works on z-scored **derivative**
spectra — brightness-invariant by construction, so dark water is not a special
case — and matches against the real splib07 library that already contains
`Acid Mine Dr Assemb2-Fe3+`, `Jarosite GDS24 Na`, ferrihydrite and goethite.
Deliverable is **material identification per lake**, not concentration: no
measured water chemistry exists for these sites beyond Ganau's single number.

## Still to do
- H2 note: the four ferric minerals are not separable at 7 bands (they identify
  as one "ferric" group); distinguishing them needs hyperspectral.
- ~~Threshold derivation (Test C)~~ **done 2026-07-22** (see above). Open
  follow-up: IronSulfate failed vs bare rock — either accept ferric-led
  detection or design a better iron-sulfate discriminator.
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
