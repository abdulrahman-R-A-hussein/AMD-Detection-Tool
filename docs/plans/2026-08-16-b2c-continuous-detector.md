# Phase B2c — replace the classifier's decision tree with a continuous score

## Context

**What three phases of evidence now say.** At 86 chemically-confirmed AMD
source points across 4 Colorado districts, against a bare-ground control that
owes nothing to our imagery:

| score | worst-case LORO Youden J |
|---|---|
| `FerricIron1`, **continuous** (p90 in buffer) | **+0.318** |
| `AMDclassFrac`, **binarised**, v3 whole-region thresholds | 0.000 |
| `AMDclassFrac`, **binarised**, v4 bare-relative thresholds | 0.000 |

Two different threshold references have now been tried and neither recovers
what the continuous index does unaided. B2b confirmed the threshold *mechanism*
(16/16) and still failed to fix anything. **The remaining difference is not the
threshold — it is thresholding at all.** SIM 3466 is a categorical *mapping*
product; we have been asking it to be a *detection* product, and the
binarisation step is where the signal dies.

**What this phase does.** Stop repairing the decision tree. Score the continuous
indices directly, combined, region-standardised, and evaluated leave-one-region-out.

**Why now, and why it is cheap.** Every input already exists on disk — all 9
indices, 86 targets, C1 446 / C2 429 / C3 430 / C3b 350, both sensors, primary
radius. **This phase needs zero Earth Engine.** It is analysis only.

**What is at stake.** `FerricIron1` alone already reached J = 0.234 vs C1 on
Sentinel-2 — failing the pre-registered bar by **0.016**. If a principled
combination clears 0.25 against every non-circular tier and holds out-of-region,
the project gets its first genuine *detector* claim, validated against measured
chemistry rather than against agreement with Rockwell's map. If it does not,
that is a clean, cheap null that closes the question.

---

## Step 0 — Pre-register, commit, then analyse

`validation/B2C_PREREGISTRATION_2026-08-16.md`, its own commit before any
model is fitted, as `4bb3b63` and `df6a6ae` were.

Fixed in advance:

- **Features:** the 8 continuous indices (`IronSulfate`, `FerricIron1`,
  `FerricIron2`, `FerrousIron`, `ClaySulfateMica`, `GreenNIR`, `GreenNIRNorm`,
  `NDVI_stress`), p90 statistic, 60 m buffer. `AMDclassFrac` is **excluded** —
  it is the thing being replaced.
- **Standardisation: within-region z-score, computed from the TRAINING regions
  only.** This is the load-bearing choice. The dose-response LORO showed
  absolute calibration does not transfer across districts while rank/relative
  structure does, so the model must learn relative patterns. Computing the
  z-score using the held-out region's own statistics would leak.
- **Model:** L2-regularised logistic regression, fixed `C = 1.0`, no tuning.
  A deliberately weak learner — with 4 regions there is no honest budget for
  hyperparameter search.
- **Everything inside the fold.** Standardisation, fitting, and any feature
  weighting happen on training regions only. No step may see the held-out
  region.
- **Primary metric:** worst-case leave-one-region-out Youden J against **C1**
  (in-stream, the hardest tier and the one that has bounded every result so far).
- **Secondary, all reported:** C2, C3b. **C3 is reported but excluded from the
  decision** — it is the NDVI-circular tier.
- **Null:** 10,000 within-region label permutations. **Correction:** BH across
  (tiers × sensors).
- **Baseline that must be beaten:** `FerricIron1` alone, out-of-region, on the
  same folds. A multi-feature model that does not beat the single index is not
  worth its complexity and will be reported as not worth it.

**Decision rule, fixed now:**

| result | verdict |
|---|---|
| worst-case LORO J ≥ 0.25 vs C1, C2 **and** C3b, BH p < 0.05, **and** beats FerricIron1 alone | **SUCCESS — first detector claim** |
| clears some tiers but not all, or does not beat the single index | **PARTIAL**, stated as such |
| below 0.15, or fails to beat the baseline anywhere | **NULL** |

## Step 1 — Build it (`python/continuous_detector.py`, new)

Pure Python + the existing stats layer. No new dependencies, no GEE.

- `load_features(paths, sensor, radius, stat)` — reuse
  `seep_detect.load_extracted()` (already dedupes correctly, including the
  `k_bare`/`clay_bare` fix from 2026-08-16).
- `zscore_within_region(rows, train_regions)` — fit μ/σ per region **on
  training folds only**.
- `fit_logistic(X, y)` — small, dependency-free gradient descent with L2; the
  repo has no sklearn and this keeps it that way. ~30 lines.
- `loro_evaluate()` — for each held-out region: standardise, fit on the other
  three, score the held-out, compute Youden J at the training-optimal
  threshold. Reuse `seep_detect.best_threshold()`, `j_at()`, `auc()`,
  `perm_p_within_region()`, `benjamini_hochberg()` — all already unit-tested
  against known answers.

**Reuse, do not rewrite:** `seep_detect.load_extracted`, `_prep_folds`,
`_worst_j_fast`, `best_threshold`, `j_at`, `auc`,
`perm_p_within_region`, `benjamini_hochberg`, `spearman`, `variance_split`.

## Step 2 — Report what the model actually learned

Not just the score. Per-fold coefficients on the standardised features, so the
result is interpretable rather than a black box:

- if `FerricIron1` dominates and the rest are noise, say so — the honest
  finding is then "one index, continuous, is the detector";
- if `NDVI_stress` or `GreenNIR` carry weight, that is a genuine multi-index
  result and paper2's indices earn a place they have not yet earned;
- **coefficient sign instability across folds is a red flag** and is reported,
  not smoothed. It is the same diagnostic that exposed Arm A.

## Step 3 — Dose-response with the same score

Re-run the severity test using the fitted continuous score in place of
`FerricIron1`, with the mandatory between/within-region variance split and
per-region signs. Report whether it improves on `FerricIron1`'s rho = +0.568 /
pH −0.554, and whether sign consistency across all four districts survives.

---

## Critical files

| file | change |
|---|---|
| `validation/B2C_PREREGISTRATION_2026-08-16.md` | **new — committed before fitting** |
| `python/continuous_detector.py` | **new** — features, z-scoring, logistic, LORO |
| `validation/ARM_B2C_CONTINUOUS_2026-08-16.md` | **new** — the report |
| `validation/STATE.md` | PROVEN / OPEN update |
| `earth-engine/amd_detection_v2.4.0.js` | **only on SUCCESS** — add a continuous score band alongside the classes, never replacing them |

**Interpreter:** repo `.venv` is sufficient — no `ee` needed for this phase.

## Verification

1. **Pre-registration commit precedes any fitting** — check `git log` order.
2. **No leakage:** assert the held-out region contributes nothing to μ/σ or to
   the fit. A deliberate leak test — standardise using all regions — should
   *inflate* the score; if it does not, the pipeline is not doing what it says.
3. **Baseline reproduced:** `FerricIron1` alone must reproduce J = +0.318 vs
   C3b and +0.234 vs C1 on S2 through the new code path. If it does not, the
   new path is wrong before any model is judged by it.
4. **Decision rule applied verbatim**, verdict stated in the pre-registered
   vocabulary.
5. **Coefficients reported per fold**, including sign instability.
6. **A null is reported as prominently as a success.**
7. Commit + push at each milestone; `STATE.md` updated before the session ends.

## Risks

- **Overfitting with 4 regions.** Mitigated by a fixed weak learner, no
  hyperparameter search, everything inside the fold, and a mandatory
  beat-the-single-index test.
- **The single index may already be the whole story.** That is a legitimate and
  publishable outcome, not a failure — it would say the detector is one band
  ratio used continuously, which is a simpler and stronger claim than a model.
- **Colorado-only.** Any success remains a Colorado Mineral Belt result. The
  natural follow-on — and the test of B2b's post-hoc geology explanation — is
  the **Ohio coal basin**, where AMD exists but background rock is
  sandstone/shale rather than iron-stained altered volcanics. That needs a new
  WQP fetch for Ohio mine-discharge source points and is deliberately **not** in
  this phase.
