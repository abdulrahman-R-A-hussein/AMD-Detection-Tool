---
name: amd-arma-cross-region-null
description: "Arm A's n=6 finding (our map beats Rockwell predicting real Fe) did not replicate at n=31 across 7 river systems - retracted 2026-08-13"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0fc5c60d-44e9-423f-b015-759ff98e4182
  modified: 2026-08-13T23:25:24.829Z
---

**As of 2026-08-13 the Arm A headline is RETRACTED.** On 2026-08-10, at 6
catchments in one river system (Animas/Silverton), our v3.0.x map's AMD-area
fraction predicted measured dissolved Fe far better than Rockwell's published
map (rho +0.714 vs +0.257; LOOCV R² +0.804 vs −1.542) — scored against real
USGS chemistry, the only ground-truth-validated result in the project. It was
already flagged suggestive-not-proven (exact p=0.136 at n=6).

Raised to **n=31 across 7 independent river systems** (added Ouray, Alma,
Leadville, Creede, Central City, Lake City — all different Colorado Mineral
Belt districts, guaranteed distinct HydroSHEDS basins): **pooled rho collapses
to +0.056 (p=0.760). Leave-one-region-out R² is negative for dissolved Fe, for
BOTH maps, on every loading model.** Full report:
`validation/ARM_A_CROSS_REGION_RETEST_2026-08-13.md`.

**Interesting nuance, not yet a finding:** per-region sign is not random noise
— Silverton and Ouray (both San Juan volcanic-field calderas) are positive;
Central City, Creede, Leadville (different geology) are negative. Worth
testing whether the relationship holds *within* consistent alteration-style
terrain — no new fetching needed, data already exists.

**Methodological lesson worth generalising:** several OTHER pooled
relationships in the same dataset (sulfate, pH, conductance vs our map) looked
significant at p<0.05 in the pooled test and ALSO failed leave-one-region-out.
20 pooled tests were run at uncorrected α=0.05; roughly the expected number of
chance false positives appeared. **Pooled/within-sample significance is not
evidence of a generalisable relationship** — this is finding [[amd-land-thresholds-do-not-transfer]]'s
lesson (never judge by within-sample performance) demonstrated directly on a
regression result, not just a classification threshold. Any future small-n
correlation in this project must be leave-one-group-out tested before being
reported as a result, not just pooled-tested.

The `hybas_12` catchment-resolution dilution problem (documented 2026-08-10 —
Cement Creek gets averaged with cleaner tributaries sharing its polygon) biases
every number here toward the null and is the leading candidate explanation if
a true effect exists but is masked. Fixing it (true DEM flow-accumulation) is
the top open item before running Arm A further — logged in `validation/STATE.md`.
