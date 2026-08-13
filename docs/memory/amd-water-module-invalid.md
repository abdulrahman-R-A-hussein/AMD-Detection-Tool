---
name: amd-water-module-invalid
description: "The AMD tool's water contamination module is invalid - indices inverted, Ganau claim circular; only Piedmont-vs-Atwood is a fair test"
metadata: 
  node_type: memory
  type: project
  originSessionId: b822eaed-ed1a-4dfc-83ec-2feb1494f847
  modified: 2026-07-26T17:27:41.337Z
---

**As of 2026-07-25 (v2.4.1) the water contamination module cannot support any
contamination claim.** Established with evidence, committed in
`validation/README.md` (findings W1-W3) — do not re-derive.

- **Root cause of "Piedmont shows nothing"**: `AWEINSH > 0.20` in
  `createUnifiedWaterMask()` was tuned on Ganau. AWEInsh is absolute-magnitude,
  so dark temperate water never passed: Piedmont 0/497 and Atwood 0/466
  optically-water px entered the module. "Clean" was a mask artifact. Fixed in
  v2.4.0 (magnitude-free mask: MNDWI>0.3, AWEInsh>0, NDVI<0, NIR<Green,
  brightness ceiling kept because SNOW passes all four spectral tests).
- **W1, the serious one**: every ratio index ranks the CLEAN control highest —
  Atwood yellow 2.39 / turbidity 1.48 vs Ganau 1.25 / 0.85. Ganau red/blue =
  0.85 (falls), but Fe³⁺ absorbs blue so ferric water must RISE blue→red.
  Ganau has **no ferric signature**; it scores "severe" only because it is
  bright enough to pass the reliability gate while the others are silenced.
  Thresholds were tuned until Ganau scored severe ⇒ circular.
- Ganau's 675 mg/L is **SULFATE, not Fe³⁺** (a v2.3.2 log error, corrected).
  Sulfate has no VNIR absorption — a site can be high-sulfate and correctly
  show no colour. Never claim optical sulfate detection.
- **W2**: 5-band S2 stepwise material ID does not discriminate — Indian River
  Lagoon (Florida, no mining) returns Jarosite R²=0.96 + Ohio Fe concretions.
  N=5 observations fits anything, curated or not. Hypothesis generator only.
- **W3**: Ganau-vs-Atwood (AUC 0.99) is confounded by continent/atmosphere
  (Iraqi dust inflates blue). **Piedmont-vs-Atwood is the only fair test** —
  matched region/sensor/dates — and gives AUC ≈ 0.78 on the blue fraction:
  real but moderate, not attributable to AMD.
- **W4 — RESOLVED 2026-07-25 via Water Quality Portal** (waterqualitydata.us,
  aggregates USGS NWIS + EPA STORET + Ohio EPA; query by `bBox` +
  `characteristicName` + `siteType=Lake, Reservoir, Impoundment`):
  **Piedmont SO₄ median 462 mg/L (n=26, 374–560) vs Atwood 18.3 mg/L (n=101)**
  — Piedmont IS genuinely CMD-contaminated, 25× the control, same order as
  Ganau's 675. But **Fe: Piedmont 162 µg/L vs Atwood 302 µg/L** (Atwood
  HIGHER; 80/86 Atwood values are Total Recoverable). So Atwood is a valid
  control for sulfate but NOT for iron.
  **Physical answer: sulfate has no VNIR absorption at any concentration, and
  0.16–0.30 mg/L Fe is 1–2 orders below visible ferric colouring. Piedmont
  correctly shows nothing — no optical sensor could see it.** Circumneutral
  Ohio CMD precipitates its iron to the bed. Detectable target is the
  precipitate on bed/shoreline, not the water column.
  Sample dates (Piedmont 2013-06→2016-05, Atwood 2015-04→2017-10) fall inside
  the L8 window ⇒ a matched-date spectra↔chemistry dataset (~110 match-ups) is
  buildable from free archival imagery with no fieldwork.
  Full report: `validation/WATER_VALIDATION_REPORT_2026-07-25.md` (v2.5.0).
- Reliability gate `brightness ∈ (0.05, 0.20)` must NOT be widened: doing so
  makes the Atwood clean control read 244/365 px "moderate" and zeroes Ganau's
  severe pixels. v2.4.0 instead added `water_class = 3` INDETERMINATE so dark
  water is never reported as "clean". Consequence: nothing classifies as clean
  in any test scene, so optical specificity is **untested, not passing**.

Lab framework `D:\dev\VPCA+STEPWISE-REGRESSION` (Ortiz method) has real splib07
AMD end-members incl. `Acid Mine Dr Assemb2-Fe3+`, jarosite, Ohio Fe
concretions; **schwertmannite absent from both its libraries**. It identifies
materials, not concentrations — there is NO measured water chemistry anywhere
in that repo. Its `src/stepwise` is GEE-free and importable via
`sys.path.insert(0, <repo>/src)`.

See [[amd-v2-vpca-validation-plan]] for the land-side status.

**CORRECTION 2026-07-26:** this file previously said the land arm "is sound:
Silverton closure AUC 0.961, Test C thresholds adopted". That is withdrawn.
Those numbers are Silverton-only and do not transfer — the Test C thresholds
over-call ~4x at Silverton and under-call ~5.6x at an independent AMD site.
The same single-site-calibration defect described above for `AWEINSH` also
affects the land arm. See [[amd-land-thresholds-do-not-transfer]].
