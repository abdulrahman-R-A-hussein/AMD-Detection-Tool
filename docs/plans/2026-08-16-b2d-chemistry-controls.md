# Phase B2d — define the controls by measured chemistry, not by station type

## Context

**Where the framework stands.**

*Land arm:* a verified-faithful SIM 3466 replica (all six index formulas exact),
whose three project-introduced "improvements" were regressions — fixing them
took worst-case cross-site Youden J from 0.107 → 0.440 (4.1×). But its
**categorical output is not an AMD detector**: `AMDclassFrac` scores J = 0.000
against bare ground. Two threshold repairs (v4) failed. **Continuous scoring
fixes it** — J = +0.617 against NLCD bare ground.

*Water arm:* one genuine positive (severity ranking at known sites,
`FerricIron1` vs dissolved Fe rho = +0.568, sign-consistent across all four
districts), three nulls (water column, Arm A catchment loading — retracted at
n=31, B2 detection), and two valuable refutations (resolution is *not* the
constraint; binarisation destroys the signal).

**The one barrier left, and it turns out to be our own control design.**
Every phase has failed on the same tier: C1, the in-stream controls. B2c scored
J = 0.178 there against a 0.25 bar. **Verified on disk 2026-08-16: of 446 C1
"controls", 104 have measured Fe ≥ 1.0 mg/L.** They are AMD-affected water being
used as a *negative class*. Only 222 are chemically clean.

We have been asking every model to call contaminated streams "not AMD" and
scoring it as failure when it refuses.

| region | in-stream | chemically clean | **dirty (Fe ≥ 1.0)** |
|---|---|---|---|
| Silverton | 122 | 39 | **31** |
| Leadville | 72 | 39 | 5 |
| Ouray | 109 | 64 | **22** |
| Central City | 143 | 80 | **46** |
| **total** | **446** | **222** | **104** |

**What this phase does.** Rebuild the control tier from **measured chemistry**
instead of station type, and use the dirty subset as a *positive* control — a
test no phase has run and one that discriminates between two very different
claims about what the score detects.

**Cost: zero Earth Engine.** Chemistry and extracted features are all on disk.

---

## Step 0 — Pre-register, commit, then analyse

`validation/B2D_PREREGISTRATION_2026-08-16.md`, own commit before any analysis,
as `4bb3b63`, `df6a6ae` and `6af0b5b` were.

**Thresholds are taken from published regulatory standards, not chosen by us** —
so they cannot be accused of being fitted to the outcome:

- **C1clean** (negative class): Fe < **0.3 mg/L** (US EPA secondary drinking
  water standard) **and** pH between **6.5 and 9.0** (EPA aquatic-life criteria).
- **C1dirty** (positive control): Fe ≥ **1.0 mg/L** **or** pH < **6.0**.
- Stations between the two bands are **excluded from both** and counted — an
  explicit "don't know" band rather than a forced call.

**Primary outcome:** worst-case leave-one-region-out J of the B2c continuous
model vs **C1clean**. Same model, same features, same folds, same code path —
**only the control definition changes**, so any difference is attributable to
that and nothing else.

**Decision rule, fixed now:**

| result | verdict |
|---|---|
| J ≥ 0.25 vs C1clean, C2 **and** C3b, BH p < 0.05, and beats `FerricIron1` alone | **SUCCESS — first detector claim** |
| clears C1clean but not every tier | **PARTIAL** |
| J < 0.15 vs C1clean | **NULL** — and the C1 failure was never about control contamination |

**The discriminating test (new, and the scientifically interesting one).**
Score C1dirty — chemically contaminated streams that are *not* mine
infrastructure:

| if C1dirty scores… | then the score is detecting… |
|---|---|
| **high**, like targets | **AMD itself** — contamination, wherever it occurs |
| **low**, like clean streams | **mine infrastructure / disturbed ground**, not chemistry |

Registered prediction, stated before running: **if the dose-response result is
real, C1dirty must score above C1clean.** Failure to do so would undercut the
severity claim and must be reported as such.

## Step 1 — Implement (`python/continuous_detector.py`, extend)

- `chem_class(row)` → `"clean" | "dirty" | "grey"` from the registered
  thresholds, reusing chemistry already attached by
  `seep_detect.load_region_points()` (via `watershed_nap.load_station_chemistry`).
- Relabel C1 rows into `C1clean` / `C1dirty` / excluded at load time; leave
  every other tier untouched.
- Reuse unchanged: `loro_evaluate`, `model_perm_p`, `baseline_loro`,
  `zscore_params`, `apply_z`, `fit_logistic`, plus `seep_detect`'s
  `best_threshold`, `j_at`, `auc`, `benjamini_hochberg`, `spearman`,
  `variance_split`.
- **No model changes.** Fixed `C = 1.0`, same 8 features, no tuning.

## Step 2 — Report

- The four-tier table (C1clean, C2, C3b, plus C3 excluded) with per-fold J.
- C1dirty ranked against targets and against C1clean, with the interpretation
  table above applied verbatim.
- Per-fold coefficients again, including sign stability — `ClaySulfateMica`,
  `GreenNIR` and `NDVI_stress` flipped signs in B2c and that must be re-checked
  under the new labels.
- Counts per class per region, including the excluded grey band.

---

## Critical files

| file | change |
|---|---|
| `validation/B2D_PREREGISTRATION_2026-08-16.md` | **new — committed before analysis** |
| `python/continuous_detector.py` | add `chem_class()` + C1 relabelling; no model changes |
| `validation/ARM_B2D_CHEM_CONTROLS_2026-08-16.md` | **new** — the report |
| `validation/STATE.md` | PROVEN / OPEN update |
| `earth-engine/amd_detection_v2.4.0.js` | **only on SUCCESS**, continuous band alongside the classes |

**Interpreter:** repo `.venv` — no Earth Engine this phase.

## Verification

1. **Pre-registration commit precedes analysis** — `git log` order.
2. **Class counts printed before any score**: clean / dirty / grey per region.
   The grey band must be reported, not silently dropped.
3. **Only the control definition changed.** Re-run C2 and C3b and confirm they
   reproduce B2c exactly (J = 0.319 and 0.617). If they move, something other
   than the C1 relabelling changed and the comparison is invalid.
4. **Baseline reproduction:** `FerricIron1` alone vs C3b must still give +0.318.
5. **Leakage positive control** re-run; the C3 anomaly from B2c re-checked.
6. **Decision rule applied verbatim**, verdict in the registered vocabulary.
7. **A null is reported as prominently as a success** — five arms already have.

## Risks

- **This could look like moving the goalposts.** It is not, and the report must
  make that explicit: the thresholds are published EPA standards, fixed before
  running, and the *original* C1 result stays in the record beside the new one.
  Both numbers get reported, always together.
- **C1clean is smaller** (222 vs 446), so confidence intervals widen. Stated.
- **If C1dirty scores low**, the severity claim is in trouble and that outcome
  is registered in advance as a real possibility, not an afterthought.
- **Colorado Mineral Belt only.** The Ohio coal basin remains the registered
  second terrain and the test of B2b's geology explanation.
