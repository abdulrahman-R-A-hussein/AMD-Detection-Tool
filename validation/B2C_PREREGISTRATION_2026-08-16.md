# Phase B2c — PRE-REGISTRATION

**Written 2026-08-16, BEFORE any model was fitted.** Own commit, as `4bb3b63`
(B2) and `df6a6ae` (B2b) were, so `git log` order is auditable evidence.

## 1. What motivates this phase

At 86 chemically-confirmed AMD source points across 4 Colorado districts,
against a bare-ground control independent of our imagery:

| score | worst-case LORO Youden J |
|---|---|
| `FerricIron1`, **continuous** (p90 in buffer) | **+0.318** |
| `AMDclassFrac`, **binarised**, v3 whole-region thresholds | 0.000 |
| `AMDclassFrac`, **binarised**, v4 bare-relative thresholds | 0.000 |

Two threshold references tried; neither recovers what the continuous index does
unaided. B2b confirmed the threshold mechanism 16/16 and still fixed nothing.
**The remaining difference is thresholding itself.**

**H-B2c.** Continuous indices, region-standardised and combined, discriminate
AMD source points from controls out-of-region, where the binarised classifier
does not.

## 2. Features — fixed

The 8 continuous indices at the primary 60 m buffer, **p90** statistic:
`IronSulfate`, `FerricIron1`, `FerricIron2`, `FerrousIron`, `ClaySulfateMica`,
`GreenNIR`, `GreenNIRNorm`, `NDVI_stress`.

`AMDclassFrac` is **excluded** — it is the thing being replaced.

## 3. Standardisation — fixed, and load-bearing

**Within-region z-score, μ and σ computed from TRAINING regions only.**

Rationale fixed in advance: the dose-response LORO showed absolute calibration
does **not** transfer across districts (LORO R² negative for every pair) while
relative structure does (sign consistent in all four). So the model must learn
relative patterns. Using the held-out region's own μ/σ would leak the test set
into preprocessing — the most common silent way a held-out test stops being
held out.

## 4. Model — fixed, deliberately weak

L2-regularised logistic regression, **fixed `C = 1.0`, no tuning, no
hyperparameter search**. With 4 regions there is no honest budget for model
selection; a fixed weak learner is the defensible choice.

**Everything inside the fold:** standardisation, fitting and any weighting use
training regions only.

## 5. Metrics — fixed

- **Primary:** worst-case leave-one-region-out Youden J vs **C1** (in-stream).
  C1 is the hardest tier and has bounded every result in this project.
- **Secondary, reported:** C2 (terrain-matched), C3b (NLCD barren).
- **C3 reported but EXCLUDED from the decision** — it is the NDVI-circular tier
  whose defect was documented on 2026-08-14.
- **Null:** 10,000 within-region label permutations, never across region.
- **Correction:** Benjamini–Hochberg across tiers × sensors; count stated in the
  report.

**Sensor scoping, verified on disk before writing this:** C3b was extracted for
**Sentinel-2 only** (Landsat predates the C3b amendment). The verdict therefore
runs on **Sentinel-2**; Landsat is reported as secondary on C1/C2/C3 and cannot
support a C3b-dependent conclusion.

## 6. Baseline that must be beaten — fixed

`FerricIron1` alone, out-of-region, on the same folds. **A multi-feature model
that does not beat one index is not worth its complexity** and will be reported
as not worth it, not dressed up as a result.

## 7. Decision rule — fixed

| result | verdict |
|---|---|
| worst-case LORO J ≥ 0.25 vs C1, C2 **and** C3b, BH p < 0.05, **and** beats `FerricIron1` alone | **SUCCESS — first detector claim** |
| clears some tiers but not all, or fails to beat the single index | **PARTIAL** |
| below 0.15, or beats the baseline nowhere | **NULL** |

## 8. Leakage test — required, and must FAIL loudly

A deliberate leak (standardising with all regions including the held-out one)
**must inflate** the score relative to the clean pipeline. If it does not, the
leakage guard is not actually doing anything and no result may be reported until
that is explained. This is a positive control on the methodology itself.

## 9. Reproduction check — required before judging any model

`FerricIron1` alone, through the new code path, must reproduce **J = +0.318 vs
C3b** and **+0.234 vs C1** on Sentinel-2. If it does not, the new path is wrong
and nothing computed through it means anything.

## 10. Shipping rule — fixed

On SUCCESS only: add a **continuous score band alongside** the existing classes
in `earth-engine/amd_detection_v2.4.0.js` — never replacing them. The
categorical map remains a faithful SIM 3466 replica; the continuous score is an
addition, so the replica claim and the detector claim stay separable.

## 11. What would falsify each claim

| claim | falsified by |
|---|---|
| H-B2c (continuous combination detects) | worst-case LORO J < 0.15 vs C1 |
| "the combination adds value" | failing to beat `FerricIron1` alone |
| "the model is interpretable/stable" | coefficient signs flipping across folds |
| generalisability | Colorado Mineral Belt only until tested in the Ohio coal basin |
