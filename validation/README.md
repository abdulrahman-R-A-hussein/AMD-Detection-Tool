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

## Still to do
- H2 note: the four ferric minerals are not separable at 7 bands (they identify
  as one "ferric" group); distinguishing them needs hyperspectral.
- Threshold derivation (Test C): draw AMD/clean polygons, run
  `derive_thresholds.py` to finalize the provisional iron threshold (0.10).
- Water Fe³⁺ regression (Test D): Ganau / Dukan vs 675 mg/L ground truth.
- Swap embedded end-members for the lab's Sentinel spectral library (exact
  spectra) via `convolve_splib07()`.

## How to add a run
1. GEE tool → pick area → **Export VPCA CSV** → run task → download CSV.
2. `.venv/Scripts/python python/vpca_validation.py --scene <csv> --sensor L8 --classcol class > validation/report_<Site>_<type>_<date>.txt`
3. Add a row to the table above.
