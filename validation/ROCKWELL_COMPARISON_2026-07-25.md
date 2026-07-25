# Head-to-head vs Rockwell et al. (2021) published USGS map — Silverton, CO

**Date:** 2026-07-25 · **Tool:** v2.4.0 classification (v2.3.0 thresholds)
**Reference:** Rockwell, B.W. & Gnesda, W.R. (2021), *Digital map of iron sulfate
minerals, other mineral groups, and vegetation of the western United States
derived from automated analysis of Landsat 8 satellite data*,
DOI [10.5066/P9BYV5H4](https://doi.org/10.5066/P9BYV5H4) — the published
**result** of the method described in SIM 3466, whose code was never released.
**Code:** `python/compare_rockwell.py`

## Method

Rockwell's ERDAS `.img` raster (309 MB, EPSG:4326, 84895×55705) was sampled at
the exact coordinates of the 20,000 Silverton pixels already committed in
`VPCA_Landsat8_Silverton__CO_20260722-v2.csv`, which carry our classification.
This avoids re-implementing the classifier: `python/amd_detection.py` is a
**v1.5.1** port that predates every v2.x correction, so using it would have
compared Rockwell against our own superseded code.

Class schemes are directly comparable — our 19 classes were built to reproduce
Rockwell's legend (see `data/rockwell/00Readme_L8_WesternUS.txt`). Their
agricultural variants (16, 20, 21) were collapsed onto their parent classes
(12, 17, 18); their no-data codes (0, 15) were excluded.

- 8,783 / 20,000 points fall on valid Rockwell data (their no-data covers ~56%
  of our AOI — high-relief snow/shadow masking in the San Juans)
- 8,093 classified by both

## Results

### Overall agreement is moderate

| metric | value |
|---|---|
| exact class agreement | **87.9%** |
| Cohen's κ | **0.546** |

Both maps are vegetation-dominated and agree closely on it (Rockwell 78.9%
dense vegetation, ours 79.6%). The high raw agreement is therefore carried
largely by vegetation; κ = 0.55 is the honest figure.

### On AMD indicator classes, agreement is poor — and we over-call

AMD-indicator classes = {9, 12, 14, 17, 18, 19}.

| | Rockwell | ours |
|---|---|---|
| AMD-indicator pixels | 47 (0.54%) | **182 (2.07%)** |

| metric | value |
|---|---|
| precision vs Rockwell | **0.137** |
| recall vs Rockwell | 0.532 |
| binary κ | **0.212** |

**We flag roughly 4× more AMD than the published map**, and only 14% of our AMD
calls are AMD in theirs. We recover about half of their AMD pixels.

### The disagreements are systematic, not random

| n px | ours | theirs |
|---|---|---|
| 180 | 4 ferrous / coarse ferric | 5 clay-sulfate-mica |
| 94 | 11 dense vegetation | 1 minor ferric (hematite) |
| 79 | 13 sparse vegetation + ferric | 5 clay-sulfate-mica |
| 59 | 13 sparse vegetation + ferric | 1 minor ferric |
| 57 | 9 argillic | 8 clay + major ferric |
| 51 | 7 clay + mod-major ferric | 5 clay-sulfate-mica |
| 51 | 8 clay + major ferric | 5 clay-sulfate-mica |

The dominant pattern is that **we assign iron-bearing classes where Rockwell
assigns plain clay (class 5)**. This is the expected consequence of the Test C
threshold derivation, which *lowered* two cutoffs: ferrous 1.05 → **0.959** and
clay-sulfate-mica 0.12 → **0.021**. Both make their respective flags fire more
often, pushing pixels out of class 5 into iron-bearing combinations. The
`9 → 8` and `8 → 6` confusions are single-step severity differences within the
same mineral family, i.e. threshold placement rather than disagreement about
what is present.

## Interpretation — read this before claiming an improvement

This comparison does **not** by itself show our implementation is better. It
shows it is **more sensitive**, and the direction of that difference has to be
argued, not assumed:

- **Argument for ours:** our thresholds are ROC-derived against hand-labelled
  AMD and clean polygons at Silverton (Test C: FerricIron1 AUC 0.992,
  ClaySulfateMica 0.999), and our AMD calls are independently corroborated by
  VPCA spectral closure at AUC 0.961. Rockwell's thresholds are regional
  constants applied continent-wide.
- **Argument against ours:** thresholds derived *at Silverton* and then
  evaluated *at Silverton* are locally tuned; higher local sensitivity is
  exactly what that produces, and it may not transfer. Test C also flagged that
  the IronSulfate index fails against bare rock (AUC 0.769).
- **Neither map is ground truth.** Rockwell's is a published, peer-reviewed
  product but still an automated classification, not field verification.

**Confounds that are not algorithmic:** Rockwell's map is a multi-year Landsat 8
composite; ours is a 2013–2020 summer median with different cloud masking and a
disabled road mask. Some difference is temporal and compositing, not method.

## What this supports for the thesis

A defensible claim: *"Reimplementing the Rockwell method with corrected index
formulas and empirically derived thresholds reproduces the published map at
87.9% agreement (κ = 0.55) over Silverton, while identifying ~4× more
AMD-indicator pixels. The additional detections are concentrated where the
published map assigns undifferentiated clay, and are consistent with locally
ROC-optimised thresholds; independent VPCA spectral closure supports the AMD
calls at AUC 0.961."*

The gap that remains: **no field verification distinguishes our extra
detections from false positives.** That is a direct, fundable question — and
one the drone/ASD campaign answers, since the disputed pixels are mapped and
can be visited.

## Next steps

1. Export the disagreement pixels as a point layer for field targeting — the
   157 "ours-only" AMD pixels are a ready-made ground-truthing list.
2. Repeat on an independent area within Rockwell's coverage that we never tuned
   against (Summitville or Red Mountain Pass) to test whether the higher
   sensitivity transfers or is Silverton-specific.
3. Sentinel-2 rerun: Rockwell used Landsat 8 only. S2's red-edge bands and 10 m
   pixels are the clearest methodological advance available, and a gap this
   comparison cannot address.
