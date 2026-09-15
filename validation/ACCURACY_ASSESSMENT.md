# Accuracy assessment — what this tool does, measured

**Compiled 2026-09-13** from every dated report in `validation/`. Current as of
tag `v3.10.0` (Earth Engine tool `v3.1.0`).

> **There is no single accuracy number for this tool, and anyone who offers you
> one is hiding something.** Performance differs by task, by terrain, and above
> all by *which reference standard* the number was measured against. That last
> distinction is the most important thing on this page.

---

## 0. The three reference standards — read this first

| reference | what it is | what a number against it means |
|---|---|---|
| **Rockwell's published map** (DOI [10.5066/P9BYV5H4](https://doi.org/10.5066/P9BYV5H4)) | an **automated** USGS Landsat classification, never field-verified | **replica fidelity only.** How well we reproduce *their product*. Says nothing about whether either is right. |
| **Measured field chemistry** (USGS NWIS + EPA STORET, via the Water Quality Portal; NWIS drainage areas) | the **only** ground truth here | genuine accuracy, bounded by the control design |
| **Control tiers** C1 / C2 / C3 / C3b | constructed negative classes | accuracy *relative to that specific negative class*. **C3 was found circular** and is excluded from decisions. |

**Pre-registered decision bars**, fixed in writing before each test ran:
worst-case leave-one-region-out Youden **J ≥ 0.25** for detection;
**|rho| ≥ 0.3 with sign consistency** for the coal dose-response;
partial **|rho| ≥ 0.25** for confound rejection.

---

## 1. Land classification — replica fidelity, **not** accuracy

### 1a. Does the replica reproduce the paper's method?

**Yes, exactly, at the index level.** All six SIM 3466 formulas match
(`2/1−5/4`, `4/2`, `4/2×(4+6)/5`, `(3+6)/(4+5)`, `6/7−5/4`, `5/4`), as does
first-match-wins class assignment and the NAP ranking (`14=1, 12=2, 17=3,
18=4, 9=5, 19=6`).

### 1b. Our three "improvements" were regressions

Worst-case (**minimum**) leave-one-site-out over Silverton / Summitville / Red
Mountain Pass, against Rockwell's map. Regenerated 2026-09-13 →
[`report_paper_faithful_2026-09-13.txt`](report_paper_faithful_2026-09-13.txt):

| configuration | **MIN J** | mean J | MIN κ | mean κ | vs shipped |
|---|---|---|---|---|---|
| **A — as shipped (v2.4.0)** | **0.107** | 0.474 | 0.120 | 0.139 | — |
| B — + the paper's May–Jul season | 0.260 | 0.463 | 0.053 | 0.159 | 2.4× |
| C — + per-scene σ cutoffs | 0.403 | 0.528 | 0.068 | 0.227 | 3.8× |
| **D — + clay requirement (v3.0.0)** | **0.440** | 0.541 | 0.101 | **0.257** | **4.1×** |

**Read the MIN column.** A configuration that works at two sites and fails at
the third has not transferred. Mean J *falls* from A to B while the minimum
more than doubles — which is the whole argument for worst-case reporting.

### 1c. The agreement figures, and why they flatter

| metric | Silverton | Summitville |
|---|---|---|
| exact class agreement | **88.1%** | **64.6%** |
| Cohen's κ (all classes) | **0.552** | **0.080** |
| precision vs Rockwell's AMD calls | 0.119 | 0.595 |
| recall vs Rockwell's AMD calls | 0.485 | 0.106 |
| binary κ (AMD vs not) | 0.184 | 0.175 |
| direction of disagreement | we flag **4.1× more** | Rockwell flags **5.6× more** |

n = 13,949 / 11,029 paired pixels on valid Rockwell data.

- **The high agreement is carried by vegetation**, not by AMD. Rockwell calls
  78.9% dense vegetation, we call 79.6%; the AMD base rate is ~0.5%.
- **κ = 0.55 is the honest headline**, not 88%.
- **"Our tool is more sensitive than Rockwell's" is RETRACTED** — the direction
  of disagreement *reverses* between sites.
- The earlier "2.40% vs 0.30% = 8×" Summitville figure is **retracted**; it
  came from independent histograms over mismatched denominators. The paired
  equivalent is 2.13% vs 0.38% = **5.6×**.

---

## 2. Detection of mine drainage — **a measured NULL**

**This is the headline result of the water arm, and it is negative.**

Sample fixed in advance: **86** chemically confirmed source points (mine
discharge / adit / tailings / waste rock / spring) across four Colorado
districts — Leadville 23, Ouray 22, Silverton 21, Central City 20. Primary
buffer 60 m, statistic p90, 10,000 within-region permutations, seed 20260814.

**All nine candidate indices fail all three control tiers, on both sensors.**

Best cases by tier (Sentinel-2, the decision sensor; worst-case LORO J over 4 folds):

| index | tier | AUC | **worst-case J** | perm p | BH q |
|---|---|---|---|---|---|
| ClaySulfateMica | C2 | 0.785 | 0.320 | 0.0001 | 0.0003 |
| FerricIron1 | C3b | 0.793 | 0.318 | 0.0001 | 0.0003 |
| FerricIron1 | C2 | 0.778 | 0.291 | 0.0001 | 0.0003 |
| **FerricIron1** | **C1 (hardest)** | 0.723 | **0.234** | 0.0001 | 0.0003 |

**The best case misses the pre-registered bar of 0.25 by 0.016.** The bar was
fixed in advance and was not moved.

### 2a. The shipped classifier is substantially a bare-ground detector

| `AMDclassFrac` vs | AUC | worst-case J |
|---|---|---|
| C1 in-stream | 0.586 | 0.004 |
| C2 terrain-matched | 0.743 | **+0.049** |
| **C3b NLCD barren** | **0.442** | **−0.252** |
| C3 | 0.471 | **−0.304** |

Worst-case J corrected for tied scores (audit 2026-09-15, item 9). The raw
report prints 0.000 for C2 and C3b; the other two rows were already right.

At Leadville, median `AMDclassFrac` is **0.376 on bare ground vs 0.049 at
targets — 7.7× the wrong way.** This is the single most important limitation
of the shipped 19-class product.

### 2b. Continuous scoring beats binarising — but not enough

| tier | continuous model J | `FerricIron1` alone |
|---|---|---|
| **C1 (primary)** | 0.178 | **0.234** |
| C2 | 0.319 | 0.291 |
| C3b | **0.617** | 0.318 |

Thresholding *was* part of the problem: J went from −0.252 to +0.617 against bare
ground. The −0.252 is the shipped classifier's value corrected for tied scores;
the B2c report compared against a printed 0.000.
But the model beats the single index only on C2 and C3b, and **loses on the
primary tier**. Verdict: PARTIAL.

⚠️ **Do not cite the Landsat arm of this test as significant.** Its J values
look similar (C1 0.228 vs −0.019) but BH q = **0.2558** on all three tiers.

### 2c. Two numbers that need a warning label

- **`NDVI_stress` vs C3b: J +0.700, AUC 0.962** — the largest separation
  anywhere in the water arm. It still **fails** the criterion (fails C1 and
  C2), and NLCD "barren" plausibly shares NDVI physics — the very reason CMD3
  rejected NLCD as a covariate. Treat with the same suspicion as C3.
- **C3 was circular.** It was defined as pixels below the region's 25th
  NDVI percentile, so `NDVI_stress` separated from it *by construction*
  (AUC 0.898). C3 is excluded from every decision. Unaffected: `AMDclassFrac`
  vs C3 (runs opposite to the defect) and the entire dose-response.

### 2d. A mechanism can be right and the fix still fail

The bare-relative threshold diagnosis passed its falsifiable pre-check
**16/16**. The fix then changed **nothing** — no grid point scored above zero
(worst-case J **−0.452 to 0.000** corrected for tied scores; the raw report
printed 0.000 for all eight), AUC 0.34–0.50. Mechanism supported, fix refuted. Not shipped.

---

## 3. Severity ranking — the one ground-truth-validated positive

`FerricIron1` (red/blue) vs measured chemistry, Landsat 8, n as shown:

| relationship | rho | n | perm p | BH q | between-region var |
|---|---|---|---|---|---|
| **vs dissolved Fe** | **+0.568** | 75 | **0.0004** | 0.0072 | 24% |
| vs total Fe | +0.558 | 82 | 0.0004 | 0.0072 | 25% |
| vs pH | **−0.554** | 77 | 0.0034 | 0.0302 | 46% |
| vs sulfate | +0.305 | 63 | — | — | 22% |

Source: [`report_seep_b2_l8_2026-08-14.txt`](report_seep_b2_l8_2026-08-14.txt).
36-test BH family. **The p-value comes from permuting within region** — the
exact test that destroyed the earlier pooled sulfate claim (which was 67.5%
between-region and reversed sign when corrected).

### 3a. The temper — cite this version, not the pooled one

| | pooled | **LORO R²** | per-district rho | signs |
|---|---|---|---|---|
| vs dissolved Fe | +0.568 | **−0.538** | +0.64 · **+0.004** · +0.68 · +0.64 | all > 0, but **Leadville ≈ 0** |
| vs pH | −0.554 | −0.882 | −0.30 · −0.40 · −0.24 · −0.27 | all − |

**Leave-one-region-out R² is negative for every index × analyte pair tested**,
including the sign-consistent ones.

> **`FerricIron1` RANKS severity within a district. It does NOT predict
> concentration across districts.**

Leadville is the weak district: **+0.004, n=23, no relationship**, so the pooled
value is carried by the other three (audit 2026-09-14 item 8). The most robust single relationship
is **vs pH** — all four districts negative and tight in magnitude.

**Citation hygiene:** **+0.568 is the Landsat 8 value. Sentinel-2 gives
+0.549.** `STATE.md` quotes +0.568 without naming the sensor.

### 3b. paper2's indices fail here

`GreenNIR` / `GreenNIRNorm` (Galaszkiewicz et al. 2024) vs dissolved Fe:
+0.51 / +0.16 / −0.25 / −0.35 across the four districts. **Signs disagree, so
the pooled value is not a relationship.** Cite paper2 as the source of a
tested-and-failed hypothesis, not as support.

---

## 4. Spatial resolution — **not** the binding constraint

Within Sentinel-2, only pixel size varying (n=75 Fe / 77 pH):

| | 10 m | 20 m | 30 m | 60 m | 100 m |
|---|---|---|---|---|---|
| `FerricIron1` vs dissolved Fe | +0.494 | +0.526 | +0.493 | +0.523 | +0.517 |
| `FerricIron1` vs pH | −0.575 | −0.582 | −0.558 | −0.613 | **−0.658** |

Detection AUC is likewise flat: 0.732 / 0.724 / 0.740 at 10 / 20 / 40 m.

**Flat — and pH is marginally *stronger* at coarser pixels.** Therefore the
earlier Landsat 30 m → Sentinel-2 20 m improvement (worst-case J −0.018 →
+0.234 vs C1) was a **sensor** effect — bands, radiometry, SNR, atmospheric
correction, deeper scene stacks — **not** a resolution effect.

**Consequence for instrumentation, against this project's own earlier framing:**
these data point at the **spectral/radiometric** axis, not the spatial one. A
multi-band sensor and a field spectrometer sit on the implicated axis; **7 cm
pixels do not.** Tested range is 10–100 m, which does span the mixed→pure pixel
transition for a 5–20 m precipitate fan; sub-metre is untested, so a 7 cm claim
is extrapolation *against a flat trend*.

---

## 5. Coal / CMD vegetation signal — real, weak, and basin-specific

`NDVI_stress` vs measured chemistry, leaf-off:

| radius | **Ohio** (5 watersheds) | **Pennsylvania** (3 tiles) |
|---|---|---|
| 30 m | **−0.354** (n=137, p=0.0028) | −0.143 (n=268, p=0.0200) |
| 60 m | −0.253 | −0.135 |
| 100 m | −0.255 | −0.114 |
| 500 m | −0.393 | −0.010 |
| **1000 m** | **−0.438** ← max | **−0.050** |
| shape | **U, rising to 1 km** | **monotone declining** |
| signs | **disagree at every radius** | **CONSISTENT at 30 m** |

Pennsylvania conductance is the better-powered arm and the cleaner result:
**−0.187 (n=443, p=0.0002), sign-consistent at 30/60/100 m**, collapsing to
**+0.003 (p=0.96)** at 1 km.

**The two basins have opposite radius signatures, and each is the other's
pre-registered falsifier.** Consequences:

- The Ohio "catchment-scale" reading is **bounded to Ohio**.
- **Radius shape does not diagnose mechanism** — it returns opposite mechanisms
  for the same drainage type, so it more plausibly measures basin geometry.
- What **does** replicate is the **sign**, and in Pennsylvania its consistency
  across disjoint sub-basins — the first such result in this arm.
- Magnitudes of 0.14–0.19 are **far below** the |rho| ≥ 0.3 bar.

**The Ohio mining-extent confound is real:** mine extent predicts sulfate
**+0.519** and vegetation **−0.283**, carrying ~42% of the raw covariance.
Conditioning leaves partial rho **−0.246** (n=131, p=0.0254) against a
pre-registered rejection bar of 0.25 — **PARTIAL by 0.004**, not cleared.
Pennsylvania is **unconditioned and cannot be conditioned**: ODNR is Ohio-only
and NLCD is rejected for sharing the NDVI physics.

**Record correction:** the Ohio 30 m p-value was published as 0.0013 until
2026-09-08. The raw output says **0.0028** and reproduces exactly.
Transcription error; use 0.0028.

---

## 6. Supporting infrastructure — the cleanest result in the project

**Catchment delineation**, MERIT Hydro D8, vs official USGS NWIS drainage areas:

| gauge | NWIS mi² | DEM mi² | ratio |
|---|---|---|---|
| Animas at Howardsville | 55.9 | 57.1 | 1.02× |
| Animas at Silverton | 70.6 | 90.2 | 1.28× |
| Cement Ck nr Silverton | 13.5 | 13.3 | **0.99×** |
| Mineral Ck abv Silverton | 11.0 | 11.0 | 1.00× |
| Mineral Ck nr Silverton | 44.3 | 49.7 | 1.12× |
| Animas blw Silverton | 146.0 | 146.7 | 1.00× |

**6/6 within ±33%**, where the previous HydroSHEDS approach managed **2/6** and
gave Cement Creek — one of the most acidic Animas tributaries — the same
91.7 mi² polygon as the mainstem, biasing every upstream analysis toward the
null. **Note this is validated against published measurements, not against
another model.**

**Turbidity detection** (Ohio, n=83 matched rows): cleanly detected, 6 features
up to rho **0.499**, while iron (n=17) and sulfate (n=23) are nulls. **The water
arm sees sediment.**

---

## 7. The bottom line

**What this tool is:** a faithful, open reimplementation of a published USGS
method, plus a within-district severity ranker validated against real chemistry,
plus externally validated catchment delineation.

**What it is not:** a detector. It does not find mine drainage — that is a
measured null at n=86 — and a pre-registered blind scene-wide search (2026-09-15)
found no evidence that it finds unrecorded sources: no signal in districts never
used to choose the index, and no advantage over bare ground where it was chosen
([`ARM_BLIND_SEARCH_2026-09-15.md`](ARM_BLIND_SEARCH_2026-09-15.md)).

**The single sentence that survives every test run so far:**

> A single continuous band ratio separates AMD-affected water from
> chemically-verified clean water at **monitored locations** in open
> acid-drainage terrain, and **ranks** severity within a mineral district; it
> does not predict concentration across districts, does not find unknown sites,
> and does not transfer to forested neutral-pH coal drainage.

**The gap that defines the remaining work:** the difference between *scoring
known points correctly* and *finding unknown sites* — a severity tool versus a
discovery tool. Closing it requires measurements that free satellite data
cannot provide. See [`docs/FIELD_CAMPAIGN.md`](../docs/FIELD_CAMPAIGN.md).

---

## 8. Provenance and one traceability note

Every figure above traces to a dated report in `validation/`, and the four
load-bearing ones were re-verified against **raw output** on 2026-09-13:
0.440 · 0.234 · +0.568 · −0.354.

**One gap was found and closed in the process.** The land-arm
`0.107 → 0.440` figures existed only in `.md` reports — the scripts print to
stdout and no raw output had ever been committed. Regenerating with
`python python/paper_faithful_test.py` reproduces
`REPLICA_AUDIT_2026-07-26.md` **exactly**, and the output is now committed as
[`report_paper_faithful_2026-09-13.txt`](report_paper_faithful_2026-09-13.txt).
