# Arm B2 — PRE-REGISTRATION

**Written 2026-08-14, BEFORE any imagery was extracted.** Committed as its own
commit so `git log` order is auditable evidence that these choices were not made
after seeing the outcome.

## Why this file exists

Three of this project's four retractions came from decisions made after seeing
the result:

- **W1** — the Ganau water claim was circular; the site that defined the
  threshold was then scored against it.
- **Test C** — thresholds judged by within-site AUC (0.99) collapsed to
  0.63–0.67 across sites; `FerrousIron` fell to 0.437, below chance.
- **The pooled sulfate correlation** — rho = −0.563, p = 0.001 **reversed sign**
  to +0.220 once between-region variance (67.5% of the total) was removed.

The project rule *"never test a hypothesis on the data that generated it"* is
unenforceable unless the choices are written down first. Everything below is
fixed. Any departure made later must be labelled **exploratory** in the report.

---

## 1. Hypothesis

**H1 (detection).** Landsat/Sentinel-2 surface reflectance around
chemically-confirmed AMD source points (mine discharge, adit, tailings, waste
rock, spring) carries an iron-mineral / sulphurous-precipitate signal that
separates them from non-source locations.

**H0.** No index separates source points from controls beyond chance once
region blocking and multiple comparisons are respected.

**H2 (dose–response, secondary).** Among source points, index magnitude tracks
measured dissolved Fe / SO₄ / pH.

**Mechanistic basis, stated up front:** this tests **land-surface ferric
precipitate ("yellow boy")**, not dissolved species. Sulfate has no VNIR
absorption and iron in solution is not optically detectable at these
concentrations — both already established here. Any signal found is iron
mineral on the ground surface, and must be worded that way.

## 2. Sample — fixed

86 source points across the 4 regions with n ≥ 10, identified by
`fetch_wqp.SOURCE_POINT_TYPES` and verified 90/90 to resolve to coordinates:

| region | source points |
|---|---|
| Leadville, CO | 23 |
| Ouray, CO | 22 |
| Silverton, CO | 21 |
| Central City, CO | 20 |
| **LORO total** | **86** |

**Creede (3) and Alma (1) are excluded from the primary analysis** — too few for
a region-level fold. They are extracted and reported separately as a held-out
curiosity, never pooled into the primary test.

## 3. Controls — three tiers, all defined before any index is computed

Sampling seed fixed at **20260814**. Exclusion radius **500 m** from any known
source point.

- **C1 — in-stream stations, same region.** All stations with
  `site_category == "instream"`. Same imagery, terrain and processing; differ
  only in not being source points. **Conservative tier**: many sit downstream of
  AMD and may carry real signal.
- **C2 — terrain-matched random land points.** 5 per target, matched to their
  target on elevation ±100 m and slope ±5° (SRTM `USGS/SRTMGL1_003`,
  `ee.Terrain.slope`). Tests "AMD source vs generic terrain of the same shape".
- **C3 — bare-ground control. Load-bearing.** 5 per target, drawn from land
  pixels below the region's 25th-percentile NDVI. Mine sites are roads,
  tailings and disturbed unvegetated ground; without C3, "detects bare ground"
  and "detects iron precipitate" are indistinguishable.

> **Interpretation rule, fixed now:** a result that separates from C1 and C2 but
> **not** from C3 will be reported as a **bare-ground detector, not an AMD
> detector**, in those words, in the headline.

**Stated limitation:** exclusion buffers are drawn around the WQP source list
only, so unmapped mine features may contaminate controls. This biases toward the
null and will **not** be used to explain away a null.

## 4. Extraction — fixed

- **Season** May–Jul (`gee_classify.V3_MONTHS`), the paper's mineral-mapping
  window. **≥3 scenes required**; below that the point is dropped and counted.
- **Water pixels excluded** using the classifier's own water term
  (`gee_classify.py:207`, MNDWI/AWEI/NDVI/brightness). This is the entire point
  of the B1/B2 split: paper2's Green:NIR is degenerate on open water, where it
  detects water, not sulfur.
- **Buffer radii 30 m, 60 m, 100 m — all three always reported.** The
  **primary is 60 m** (≈2 Landsat pixels / 6 Sentinel-2 pixels, sized to WQP
  coordinate accuracy, which the station file does not record).
- **Within-buffer statistic: 90th percentile** of the index over surviving land
  pixels. Rationale fixed in advance: a precipitate fan occupies a minority of
  pixels in the buffer, so the mean dilutes it. **Mean reported as sensitivity.**
- **Sensors:** Landsat 8 C2 L2 at 30 m (matches the v3.0.x calibration exactly)
  and Sentinel-2 SR Harmonized at 10 m (band mapping from
  `match_scenes.S2_MAP`). Sentinel-2 uses the **scene-relative std-dev
  thresholds** (`V3_STD_MULT`), never a transplanted Landsat absolute cutoff —
  which is what SIM 3466 specifies regardless.

**Drop-rate escalation rule, fixed now:** if >30% of targets yield zero
surviving land pixels at 60 m, the primary radius escalates to 100 m and the
report says so explicitly. Drop counts are reported per region either way.

## 5. Index panel — fixed, 9 indices

| source | indices |
|---|---|
| `water_indices.py` (paper2) | `GreenNIR`, `GreenNIRNorm`, `NDVI_stress` |
| SIM 3466 land arm | `IronSulfate`, `FerricIron1`, `FerricIron2`, `FerrousIron`, `ClaySulfateMica` |
| land arm, end-to-end | **AMD class fraction of buffer** via `classify_v3()` |

The last row is the highest-value single test: it scores the **shipped
classifier, unchanged**, against chemically-confirmed AMD point sources — the
first time the working deliverable is checked against measured chemistry at
source.

## 6. Statistics — fixed

- **Primary metric: worst-case leave-one-region-out Youden J** across the 4
  folds. Pooled AUC is reported but is **explicitly not the criterion** —
  finding L1 exists because within-sample AUC lied by 0.35.
- **Null: 10,000 label permutations shuffled WITHIN region.** Never across:
  source points cluster spatially, and a global shuffle breaks the blocking and
  inflates significance.
- **Multiple comparisons: Benjamini–Hochberg over the primary family of
  9 indices × 3 control tiers × 2 sensors = 54 tests.** Bonferroni threshold
  reported alongside. Secondary radii (30/100 m) and the mean statistic are
  **sensitivity analyses, not added to the BH family** — and any claim resting
  only on a secondary is labelled exploratory.
- **Dose–response (H2):** Spearman rho of index vs median measured Fe / SO₄ /
  pH at source points, reported **with the between/within-region variance
  split**, mandatory after the sulfate sign reversal.
- **n and the caveat reported next to every number.**

## 7. Decision rule — fixed

> **Detection is claimed only if worst-case LORO Youden J ≥ 0.25 against ALL
> THREE control tiers AND the BH-corrected within-region permutation p < 0.05.**
>
> Anything less is reported as a **null**, as prominently as a positive would
> be. A null here is a valid and publishable result: paired with the resolution
> curve it bounds what free satellite imagery can do and prices the drone.

## 8. Resolution-degradation curve

Sentinel-2 10 m extraction aggregated with `reduceResolution` to
**20 / 30 / 60 / 100 m**; the identical §6 test re-run at each. Reported as
worst-case LORO J vs ground sample distance.

Informative in both directions, fixed in advance:
- holds at 30 m → the tool works on free imagery at scale;
- decays sharply between 10 m and 30 m → an independent, larger-n (86 vs 6)
  replication of paper2's "Sentinel-2 resolved only 3 of 6 leaks", and a
  quantitative argument for higher-resolution airborne survey.

Extrapolation below 10 m will be **labelled extrapolation**, not measurement.

---

## 9. Companion pre-registration — Arm A geology sign-flip (STATE.md OPEN #1)

Arm A's per-region signs were Silverton +0.714 and Ouray +0.667 (both San Juan
volcanic-field calderas) vs Central City −0.700, Creede −0.800, Leadville
−0.800. The hypothesis "the sign tracks alteration style" was **generated from
those signs**, so testing it on the same 31 catchments is circular and has
deliberately been given no p-value.

**Prediction registered now, for regions not yet in the dataset:**

> In a region whose ore deposits are **volcanic-hosted epithermal / caldera-
> related** (San Juan style), the correlation between mapped AMD loading and
> downstream dissolved Fe will be **positive**. In regions of
> **polymetallic vein / carbonate-replacement** style (Leadville, Central City),
> it will be **non-positive**.

**This is testable only on regions added after today.** Labels must come from
published geology, assigned before the correlation is computed. Recorded here so
the lead stays alive without repeating the circularity.

---

## 10. What would falsify each claim

| claim | falsified by |
|---|---|
| H1 detection | worst-case LORO J < 0.25 against any tier, or BH p ≥ 0.05 |
| "AMD detector" (vs bare ground) | separation from C1/C2 but not C3 |
| H2 dose–response | rho losing significance, or reversing sign, after region-centering |
| resolution wall | J flat across 10→100 m (i.e. resolution is not the limit) |
