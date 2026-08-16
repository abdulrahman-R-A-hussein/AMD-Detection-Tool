# Phase B2c — going continuous solves the bare-ground problem. It does not solve detection.

**Date:** 2026-08-16 · **Pre-registration:** [`B2C_PREREGISTRATION_2026-08-16.md`](B2C_PREREGISTRATION_2026-08-16.md)
committed `6af0b5b` **before any model was fitted**
**Raw output:** [`report_b2c_continuous_2026-08-16.txt`](report_b2c_continuous_2026-08-16.txt) (S2),
[`report_b2c_continuous_l8_2026-08-16.txt`](report_b2c_continuous_l8_2026-08-16.txt) (L8)

## Verdict: PARTIAL (pre-registered vocabulary)

> **The bare-ground confound is solved.** Against NLCD bare ground, the
> continuous model reaches worst-case leave-one-region-out **J = +0.617**,
> where the binarised classifier scored **0.000** under two different threshold
> references. Nearly double the single index (+0.318), and every fold between
> +0.62 and +0.88.
>
> **Detection is still not solved.** Against in-stream controls — the
> pre-registered PRIMARY tier — the model scores **0.178**: below the 0.25 bar,
> **and worse than `FerricIron1` alone (0.234)**. Adding features helps against
> land controls and hurts against water-adjacent ones.

## Sentinel-2 (the pre-registered decision sensor)

| tier | model J | `FerricIron1` alone | perm p | BH q | per-region model J |
|---|---|---|---|---|---|
| **C1 in-stream (PRIMARY)** | **0.178** | **0.234** | 0.0020 | 0.0020 | +0.35 +0.18 +0.42 +0.25 |
| C2 terrain-matched | 0.319 | 0.291 | 0.0020 | 0.0020 | +0.64 +0.32 +0.59 +0.63 |
| C3 NDVI-circular *(excluded)* | 0.420 | 0.318 | 0.0020 | 0.0020 | +0.42 +0.70 +0.68 +0.85 |
| **C3b NLCD barren** | **0.617** | 0.318 | 0.0020 | 0.0020 | +0.65 +0.62 +0.75 +0.88 |

p = 0.0020 is the floor for 500 model permutations — no permuted draw reached
the observed J at any tier. Baseline reproduction check passed exactly
(+0.234 vs C1, +0.318 vs C3b), so the code path was verified before any model
was judged through it.

**Model beats the single index on C2 and C3b — but not on C1.** By the
pre-registered rule, a combination that fails to beat one index where it
matters most is not worth its complexity *there*.

## Landsat 8 (secondary — no C3b coverage)

| tier | model J | `FerricIron1` alone |
|---|---|---|
| C1 | **0.228** | **−0.019** |
| C2 | **0.330** | −0.010 |
| C3 *(excluded)* | 0.120 | −0.045 |

**On the weaker sensor the combination does real work**: the single index has
*no* discrimination (negative J) while the model reaches 0.228–0.330. This is
the mirror image of Sentinel-2, where the single index is already strong and
the combination adds nothing on C1. Reading the two together: the multi-index
combination substitutes for sensor quality rather than adding to it.

## What the model learned — and where it is unstable

Per-fold coefficients on standardised features (S2, C1 fold set):

| feature | cent | lead | oura | silv | |
|---|---|---|---|---|---|
| `FerricIron2` | +0.772 | +1.492 | +0.507 | +1.135 | stable, strongest |
| `FerricIron1` | +0.507 | +0.167 | +0.850 | +0.646 | stable |
| `IronSulfate` | +0.650 | +0.086 | +0.343 | +0.501 | stable |
| `FerrousIron` | −0.464 | −1.091 | −0.286 | −0.570 | stable (negative) |
| `GreenNIRNorm` | +0.555 | +0.231 | +0.528 | +0.081 | stable |
| `ClaySulfateMica` | −1.040 | +0.174 | −0.838 | −1.077 | **SIGN FLIPS** |
| `GreenNIR` | +0.057 | −0.324 | −0.166 | +0.115 | **SIGN FLIPS** |
| `NDVI_stress` | +0.221 | +0.183 | +0.071 | −0.172 | **SIGN FLIPS** |

**3 of 8 features flip sign across folds** — reported, not smoothed. This is the
same diagnostic that exposed Arm A. The three ferric/iron indices carry the
signal consistently; clay and both paper2 vegetation indices do not.

Note `FerrousIron` is consistently **negative** — mine discharge scores *lower*
on it than controls. Consistent with the earlier finding that `FerrousIron` had
no AMD discriminative power (AUC 0.437, below chance) in Test C.

## Methodological problems found in this phase, both reported

1. **The permutation null initially tested the wrong quantity.** The first
   implementation permuted the *baseline* score for speed, so the p-values
   described `FerricIron1` alone rather than the fitted model. Invisible on
   Sentinel-2 (strong baseline → tiny p) but obvious on Landsat, where the
   baseline is ~0 while the model scores 0.228 and p came out 0.21. Fixed by
   vectorising the fit with numpy so a refit-per-draw null became affordable.
   All p-values above are from the corrected null.
2. **The leakage positive control did not fire on one tier.** A deliberate leak
   inflated J as required on C1 (+0.178→+0.214), C2 (+0.319→+0.360) and C3b
   (+0.617→+0.700), but **not on C3** (+0.420→+0.410). C3 is the excluded
   NDVI-circular tier, so no reported conclusion depends on it — but a positive
   control that fails anywhere is stated, not omitted. Most likely the circular
   tier's separation is already so structurally determined that region
   standardisation barely moves it; **untested, and labelled as speculation.**

## Interpretation

The three phases now say something coherent:

- **Binarisation was destroying the signal.** Continuous scoring recovers it —
  0.000 → 0.617 against bare ground is not a marginal gain.
- **What remains is not a bare-ground problem.** It is that in-stream
  monitoring stations are hard negatives. Many sit *downstream* of AMD and
  plausibly carry real signal; the pre-registration called C1 "the conservative
  tier" for exactly this reason. **This is a stated limitation of the control
  design, not an excuse** — C1 was chosen as primary in advance and the result
  stands as PARTIAL.
- **The tool's honest capability is now bounded on both sides:** it separates
  mine discharge from *land* (bare, vegetated, terrain-matched) reliably and
  out-of-region; it does not separate mine discharge from *other monitored
  water features* in the same district.

## Consequences

- **Not shipped.** The pre-registered gate required SUCCESS on C1, C2 *and*
  C3b. `earth-engine/amd_detection_v2.4.0.js` is untouched.
- **The v3 classifier's bare-ground limitation now has a demonstrated remedy**
  (continuous scoring) even though the remedy does not reach the detection bar.
- Colorado Mineral Belt only. The Ohio coal basin remains the registered second
  terrain.

## Reproduce

```
python continuous_detector.py --sensor S2 --model-perms 500
python continuous_detector.py --sensor L8 --model-perms 500
```

Repo `.venv` is sufficient — no Earth Engine needed for this phase.
