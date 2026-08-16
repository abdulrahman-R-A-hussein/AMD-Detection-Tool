# Phase B2b — the bare-ground fix FAILED. The mechanism was right; the fix was not.

**Date:** 2026-08-16 · **Pre-registration:** [`B2B_PREREGISTRATION_2026-08-16.md`](B2B_PREREGISTRATION_2026-08-16.md)
committed `df6a6ae` **before any imagery or any parameter sweep**
**Raw output:** [`report_b2b_sweep_2026-08-16.txt`](report_b2b_sweep_2026-08-16.txt)

## Verdict

> **FAILURE by the pre-registered rule.** All 8 grid points give worst-case
> leave-one-region-out J = **0.000** against NLCD bare ground, identical to the
> shipped v3 classifier's 0.000. AUC is **0.34–0.50** — at or *below* chance,
> meaning bare ground scores as high or higher than confirmed mine discharge
> even with bare-ground-relative thresholds.

Reported as prominently as a success would have been.

## The mechanism was confirmed — and fixing it changed nothing

The registered falsifiable pre-check passed **16/16**: bare-subset means exceed
whole-region means for every iron index in every district, often hugely
(`IronSulfate` at Ouray: −2.334 whole-region vs −0.399 bare). So v3's thresholds
genuinely *were* mis-referenced — `mean + 0.5σ` over the whole region sat far
below typical bare ground and admitted nearly all of it.

**Correcting that did not produce discrimination.** Full grid:

| k_bare | clay | AUC | worst-case LORO J | BH q |
|---|---|---|---|---|
| 0.5 | 0.25 | 0.372 | 0.000 | 0.993 |
| 0.5 | 0.50 | 0.381 | 0.000 | 0.993 |
| 1.0 | 0.25 | 0.340 | 0.000 | 0.993 |
| 1.0 | 0.50 | 0.343 | 0.000 | 0.993 |
| 1.5 | 0.25 | 0.355 | 0.000 | 0.993 |
| 1.5 | 0.50 | 0.355 | 0.000 | 0.993 |
| 2.0 | 0.25 | 0.496 | 0.000 | 0.993 |
| 2.0 | 0.50 | 0.496 | 0.000 | 0.993 |

**H-mech SUPPORTED, H-fix REFUTED.** A confirmed mechanism is not a sufficient
cause — worth recording as a methodological lesson in its own right, since the
pre-check passing so cleanly made the fix feel inevitable.

## What this leaves standing, and it is the important part

The contradiction that motivated this phase is **unchanged and now sharper**:

| score at the same 86 points, same control | worst-case LORO J |
|---|---|
| `FerricIron1`, **continuous** (p90 within buffer) | **+0.318** |
| `AMDclassFrac` v3, **binarised** then averaged | 0.000 |
| `AMDclassFrac` v4, **binarised** at bare-relative thresholds | 0.000 |

The information is present in the imagery. Two threshold references have now
been tried and neither recovers it. What separates the working score from the
failing ones is **not** the threshold — it is that one is continuous and the
others are binarised.

## Two post-hoc explanations — LABELLED post-hoc, neither tested here

Generated after seeing the result, so neither carries a p-value and neither may
be cited as a finding. Stated with what would actually test them:

1. **Binarisation destroys the magnitude that carries the signal.** A
   per-pixel yes/no decision, then averaged over a buffer, discards how
   iron-rich a pixel is. The continuous p90 keeps it. **Test:** extract
   "fraction of pixels with `FerricIron1` above a bare-relative cut" — a
   single-index binarisation — and compare against `FerricIron1` p90 on the
   same points. If continuous ≫ binary, binarisation is the culprit,
   independent of cascade complexity.
2. **In a mineralised belt, iron-bearing bare ground is not diagnostic of
   AMD.** NLCD "Barren Land" across the Colorado Mineral Belt is largely
   naturally iron-stained alpine talus and altered rock. A classifier keyed on
   "bare and iron-bearing" is then describing regional geology, not drainage.
   **Test:** repeat in a terrain where bare ground is *not* iron-rich — the
   Ohio coal basin, where AMD exists and the background is sandstone/shale.

Explanation 2 would also predict that the land arm's agreement with Rockwell is
high precisely *because* both maps are keyed to the same regional geology —
which is consistent with agreement being replica fidelity, never accuracy.

## Consequences

- **v4 is NOT shipped.** The pre-registered gate said port to the GEE tool only
  on SUCCESS. `earth-engine/amd_detection_v2.4.0.js` is left untouched.
- **Step 3 (replica-fidelity cost vs Rockwell) was not run.** It exists to price
  a *gain* against a *loss*; with no gain there is nothing to price, and running
  it would only produce a number with no decision attached.
- **The v3 bare-ground limitation stands** and must accompany any use of the
  classifier: it cannot distinguish mine discharge from bare ground, and that is
  now known not to be a threshold-reference problem.

## Process notes

- **An analysis bug was caught before it became the finding.** The first run
  reported FAILURE from a *single* grid point: `load_extracted()`'s dedup key —
  added days earlier for the C3b merge — omitted `k_bare`/`clay_bare`, so all
  8 grid points collapsed onto the first. Caught by checking the CSV's grid
  contents against the analysis output rather than trusting the verdict. Fixed;
  the verdict is unchanged, but it was verified on 8/8 rather than 1/8.
- **A circularity was avoided at design time.** The classifier's own `land` term
  contains an iron-threshold-dependent escape clause; using it to compute the
  iron threshold would have been a mask defining the statistic defining the
  mask. `bare_land_mask()` is threshold-independent by construction.

## Reproduce

```
python b2b_mech_check.py                                   # the pre-check
python seep_detect.py --v4-sweep --regions <slug>          # per region
python seep_detect.py --v4-analyse --inputs <csvs> --perms 10000
```

Interpreter `D:/dev/VPCA+STEPWISE-REGRESSION/.venv` (needs `ee`).
