# Arm B2 — seep/precipitate detection at 86 AMD source points

**Date:** 2026-08-14 · **Pre-registration:** [`B2_PREREGISTRATION_2026-08-14.md`](B2_PREREGISTRATION_2026-08-14.md),
committed `4bb3b63` **before any imagery was extracted** (auditable in `git log`).
**Raw output:** [`report_seep_b2_l8_2026-08-14.txt`](report_seep_b2_l8_2026-08-14.txt)

## Headline, both halves

> **DETECTION IS A NULL. DOSE–RESPONSE IS REAL.**
>
> Landsat 8 cannot tell you *where* an AMD source is — all 9 indices fail the
> pre-registered criterion against all 3 control tiers at n=86. But at points
> already known to be sources, **`FerricIron1` tracks how contaminated the
> discharge is**: rho = **+0.568** vs measured dissolved Fe (n=75,
> within-region permutation p = 0.0004, BH q = 0.0072), only **24%
> between-region variance**.

Both halves are reported with equal prominence, per project rule.

> **TEMPERED same day by the leave-one-region-out test (Part 3).** The
> direction replicates in **all four** districts — no sign flips, which is
> exactly where Arm A died — but it is **not uniform** (Leadville rho ≈ 0.00
> while the other three are +0.62 to +0.68), and **LORO R² is negative for
> every pair**. Read the claim as: *ranks severity within a district; does not
> predict concentration across districts.* The pooled +0.568 overstates it.

## Sample

n = **86** source points (mine discharge / adit / tailings / waste rock /
spring) across 4 regions — Leadville 23, Ouray 22, Silverton 21, Central City 20.
Reproduces the pre-registered n exactly. Controls: C1 in-stream 446,
C2 terrain-matched 429, C3 bare-ground 371.

**0 of 86 targets lost to the water mask**, so the pre-registered >30%
escalation to a 100 m primary radius did not apply; 60 m stands as registered.

## Part 1 — Detection: NULL

Criterion (fixed in advance): worst-case leave-one-region-out Youden J ≥ 0.25
against **all three** tiers **and** BH-corrected within-region permutation
p < 0.05. Family = 27 tests, 10,000 permutations.

**All 9 indices fail against all 3 tiers.** The pattern is the informative part:

| index | vs C1 in-stream | vs C2 terrain | vs C3 bare ground |
|---|---|---|---|
| `GreenNIR` / `GreenNIRNorm` | −0.097 | +0.235 | fails |
| `ClaySulfateMica` | +0.044 | +0.226 | fails |
| `IronSulfate` | −0.069 | +0.200 | fails |
| `FerricIron2` | +0.008 | +0.198 | −0.139 |
| **`AMDclassFrac`** (shipped classifier) | **0.000** | **0.000** | **−0.304** |

Everything that looks like separation is against **C2 (terrain-matched
vegetated land)** and collapses to ≈0 against **C1 (in-stream stations in the
same region)**. Mine sites are distinguishable from generic hillside; they are
**not** distinguishable from other monitored water features nearby.

### The shipped classifier scores bare ground HIGHER than mine discharge

`AMDclassFrac` vs C3: AUC 0.456, worst-case LORO J **−0.304**. Leadville
medians: bare ground 0.376 vs targets 0.049 — **7.7×**.

Mechanism, and it is structural rather than a bug: the land arm's NDVI gate
requires a pixel to be unvegetated *before* it can receive any AMD class, so
"AMD class fraction" partly measures bareness by construction. C2 scoring
exactly 0.000 (vegetated terrain, gated out entirely) is the same effect seen
from the other side. **This is a real limitation of the v3.0.x classifier and
should be stated in any use of it: it is substantially a bare-ground detector.**

## Part 2 — Dose–response: SIGNIFICANT and correctly signed

Pre-registered as H2. Family = 36 tests (9 indices × 4 analytes), within-region
label permutation (5,000 draws), Benjamini-Hochberg corrected,
Bonferroni threshold 0.00139.

| index | analyte | rho | n | perm p | BH q | between-region var |
|---|---|---|---|---|---|---|
| **`FerricIron1`** | **dissolved Fe** | **+0.568** | 75 | 0.0004 | **0.0072** | **24%** |
| `FerricIron1` | total Fe | +0.558 | 82 | 0.0004 | 0.0072 | 25% |
| `FerricIron2` | pH | −0.488 | 77 | 0.0006 | 0.0072 | 46% |
| `FerricIron1` | pH | −0.554 | 77 | 0.0034 | 0.0302 | 46% |
| `FerricIron2` | dissolved Fe | +0.427 | 75 | 0.0042 | 0.0302 | 24% |

**Why this one is not the sulfate mistake again.** The retracted pooled sulfate
correlation was 67.5% between-region variance and **reversed sign** when region
structure was removed. This result is **24% between-region** — mostly *within*
region — and the p-value above comes from permuting labels **within region
only**, so between-region structure cannot generate it. It is the same test
that destroyed the sulfate claim, and this one survives it.

Signs are mechanistically correct in both directions: more ferric iron staining
→ more dissolved Fe, and → lower pH.

`FerricIron1` = SR_B4/SR_B2 (red/blue), the simplest index in the panel and the
only SIM 3466 index computable at genuine 10 m on Sentinel-2.

## Part 3 — Leave-one-region-out: the Arm A knife, applied

Raw output: [`report_seep_b2_doseloro_2026-08-14.txt`](report_seep_b2_doseloro_2026-08-14.txt)

| index | analyte | pooled | LORO R² | per-region rho | signs |
|---|---|---|---|---|---|
| `FerricIron1` | dissolved Fe | +0.568 | −0.538 | cent +0.64 · lead **+0.00** · oura +0.68 · silv +0.64 | **all +** |
| `FerricIron1` | total Fe | +0.558 | −0.530 | +0.62 · **+0.07** · +0.34 · +0.62 | **all +** |
| **`FerricIron1`** | **pH** | **−0.554** | −0.882 | **−0.30 · −0.40 · −0.24 · −0.27** | **all −** |
| `FerricIron2` | pH | −0.488 | −1.142 | −0.25 · −0.30 · −0.41 · −0.36 | all − |
| `AMDclassFrac` | dissolved Fe | +0.266 | −0.614 | +0.58 · +0.18 · +0.31 · +0.34 | all + |
| `GreenNIR` | dissolved Fe | −0.113 | −0.719 | +0.51 · +0.16 · −0.25 · −0.35 | **disagree** |

**Two things this establishes, and one it takes away.**

1. **It is not Arm A.** Arm A's per-region signs were +0.71, +0.67, −0.70,
   −0.80, −0.80 — incoherent. Here the sign holds in **all four** districts for
   every `FerricIron1` pair. Sign consistency across four independent mining
   districts is the check Arm A failed, and this passes it.
2. **`FerricIron1` vs pH is the most robust relationship in the study** —
   sign-consistent *and* tight in magnitude (−0.24 to −0.40 across all four),
   where the Fe relationship is sign-consistent but heterogeneous.
3. **Absolute calibration does not transfer. LORO R² is negative for every
   index × analyte pair tested**, including the sign-consistent ones. A linear
   model fitted on three districts predicts the fourth worse than that
   district's own mean. Regions carry their own offsets — different geology,
   baseline Fe, illumination.

**Leadville is the weak district** (rho +0.00 for dissolved Fe, +0.07 total),
so the pooled +0.568 is carried by the other three. Stated rather than averaged
away.

**Therefore the defensible claim is a ranking claim, not a prediction claim:**
within a district, `FerricIron1` orders source points by severity; it cannot be
handed a number and asked for mg/L in a district it has not seen. That is still
useful — ranking is what site-prioritisation and drone-target selection need —
but it is a materially weaker claim than the pooled rho suggests, and the
weaker one is the correct one.

Note the paper2 indices (`GreenNIR`/`GreenNIRNorm`) **fail sign consistency**
here (+0.51, +0.16, −0.25, −0.35). Their pooled −0.113 is not a relationship.

## What this means

The two halves are consistent, not contradictory: **satellite imagery is a poor
prospecting tool here but a usable severity gauge.** Finding sites fails because
mine workings look like other bare and disturbed ground at 30 m. Ranking known
sites works because, among mine sites, the intensity of ferric staining scales
with discharge chemistry.

For the grant: this is the **first ground-truth-validated positive result in the
water arm** — scored against real USGS/EPA chemistry that neither the index nor
the classifier was ever fitted to. It also sharpens the drone case: severity
ranking already works at 30 m, so the resolution argument is about *detection*,
which is exactly what higher resolution should fix.

## Defect found in this study's own design — reported, not hidden

**The pre-registered C3 tier is circular for vegetation-sensitive indices.**
C3 was defined as "land pixels below the region's 25th-percentile NDVI", so
`NDVI_stress` separates targets from C3 *by construction* (AUC 0.898). This is
the W1 error — a control defined using the quantity under test — and it was
built into the pre-registration without being noticed.

- Affected and **invalid**: `NDVI_stress` vs C3, and partly
  `GreenNIR`/`GreenNIRNorm` vs C3.
- **Unaffected**: the `AMDclassFrac` vs C3 result, which runs *opposite* to the
  defect (the circularity would inflate target scores, not depress them), and
  the entire dose-response analysis, which does not use C3 at all.
- Since detection is a null overall, this defect does not rescue or create any
  positive claim.

**Amendment for next session:** re-run C3 as **C3b** using NLCD
`USGS/NLCD_RELEASES/2019_REL/NLCD` class 31 (Barren Land) — independent of our
imagery — as a labelled amendment, never a silent substitution.

## Reproduce

```
python seep_detect.py --extract --sensor L8 --regions <slug>   # per region
python seep_detect.py --analyse --inputs <csvs> --perms 10000
```

Interpreter `D:/dev/VPCA+STEPWISE-REGRESSION/.venv` (needs `ee`).

## Caveats

- **This is land-surface ferric precipitate, never dissolved sulfate.** Sulfate
  has no VNIR absorption. `FerricIron1` correlating with sulfate (+0.305) is
  iron and acidity co-varying with sulfate, and must be worded that way.
- Exclusion buffers use the WQP source list only, so unmapped mine features may
  contaminate controls. This biases toward the null and is **not** used to
  explain the null away.
- Landsat 8 only so far. Sentinel-2 and the resolution-degradation ladder are
  not yet run — and S2 is **not** 10 m for most of this panel (SWIR is 20 m,
  the coastal band 60 m; only `FerricIron1` and the green:NIR pair are true
  10 m). See `seep_detect.S2_NATIVE_M`.
- Dose–response is correlational at n=75–82 across 4 regions; it has not been
  tested on a held-out region, which is the obvious next check.
