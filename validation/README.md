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

## Test D — Water contamination (2026-07-23, Landsat 8, v2.3.0 tool)

First water-path validation (`vpca_validation.py --water`, raw-reflectance
matching). No `conc_mgL` ground-truth column yet, so end-member evidence only:

| Site | Type | Pixels | Water match | Verdict | Report |
|---|---|---|---|---|---|
| Ganau Pond, Iraq | known AMD (675 mg/L Fe³⁺) | 4284 | **fe3_water** 3/3 comps, \|r\|≈0.99, SAM 3.3–5.8°, 99.5% var | **contamination ✓ (sensitivity)** | [report](report_Ganau_water_20260723.txt) |
| Piedmont Lake, OH | documented sulfate | 20000 | clear_water \|r\|=0.994 | optically clear — see note | [report](report_Piedmont_water_20260723.txt) |
| Atwood Lake, OH | clean control | 20000 | clear_water \|r\|=0.990 | clean ✓ (specificity) | [report](report_Atwood_water_20260723.txt) |

**Findings:**
- Ganau: VPCA independently recovers the Fe³⁺-stained-water end-member as the
  scene's dominant signature — the water sensitivity case holds at the one
  site with known contamination.
- Piedmont reads as clear water. This is a **method limitation, not
  (necessarily) a miss**: SO₄²⁻ has no VNIR absorption; only dissolved or
  colloidal Fe³⁺, turbidity, and color are optically visible. Adjudication
  needs Piedmont water chemistry (dissolved Fe, not just sulfate) — if iron
  is low there, "clear" is the physically correct answer.
- Validator fix shipped with this run: water mode previously fell through to
  the LAND "clean control" closure message even when every component matched
  fe3_water (it mislabeled the Ganau detection as a non-detection). Water
  scenes now print their own WATER VERDICT block; self-test passes.
- Regression (R²/RMSE) still open: needs ≥3 sites with lab values via a
  `conc_mgL` column (Ganau 675 mg/L + Piedmont/Dukan chemistry + clean ≈ 0).

## Still to do
- H2 note: the four ferric minerals are not separable at 7 bands (they identify
  as one "ferric" group); distinguishing them needs hyperspectral.
- ~~Threshold derivation (Test C)~~ **done 2026-07-22** (see above). Open
  follow-up: IronSulfate failed vs bare rock — either accept ferric-led
  detection or design a better iron-sulfate discriminator.
- ~~Water end-member validation (Test D)~~ **first pass done 2026-07-23** (see
  above). Open: obtain dissolved-Fe lab values for Piedmont (Ohio EPA / USGS
  NWIS) and Dukan, then run the `conc_mgL` regression for R²/RMSE.
- Swap embedded end-members for the lab's Sentinel spectral library (exact
  spectra) via `convolve_splib07()`.

## How to add a run
1. GEE tool → pick area → **Export VPCA CSV** → run task → download CSV.
2. `.venv/Scripts/python python/vpca_validation.py --scene <csv> --sensor L8 --classcol class > validation/report_<Site>_<type>_<date>.txt`
3. Add a row to the table above.
