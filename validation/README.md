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

## Still to do
- H2 note: the four ferric minerals are not separable at 7 bands (they identify
  as one "ferric" group); distinguishing them needs hyperspectral.
- ~~Threshold derivation (Test C)~~ **done 2026-07-22** (see above). Open
  follow-up: IronSulfate failed vs bare rock — either accept ferric-led
  detection or design a better iron-sulfate discriminator.
- Water Fe³⁺ regression (Test D): Ganau / Dukan vs 675 mg/L ground truth.
- Swap embedded end-members for the lab's Sentinel spectral library (exact
  spectra) via `convolve_splib07()`.

## How to add a run
1. GEE tool → pick area → **Export VPCA CSV** → run task → download CSV.
2. `.venv/Scripts/python python/vpca_validation.py --scene <csv> --sensor L8 --classcol class > validation/report_<Site>_<type>_<date>.txt`
3. Add a row to the table above.
