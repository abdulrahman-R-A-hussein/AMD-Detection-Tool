# Replica audit: our land arm vs Rockwell & Gnesda, SIM 3466

**Date:** 2026-07-26 · **Source of truth:** `paper.pdf` = USGS Scientific
Investigations Map 3466 pamphlet (47 pp.), *Improved Automated Identification
and Mapping of Iron Sulfate Minerals, Other Mineral Groups, and Vegetation using
Landsat 8 OLI Data, San Juan Mountains, Colorado, and Four Corners Region*
· **Published result:** DOI [10.5066/P9BYV5H4](https://doi.org/10.5066/P9BYV5H4)
· **Code:** `python/pool_labels.py`, `python/iron_criterion_search.py`,
`python/paper_faithful_test.py`

Rockwell's code was never released, so this tool is a reimplementation from the
published method. Two questions follow, and they must not be conflated:

1. **Is it a faithful replica?** Answerable from the pamphlet + their raster.
2. **Is it an improvement?** **Not answerable here.** Both maps are automated
   classifications; neither is field-verified. Everything below measures
   agreement with a published product, never correctness on the ground.

## 1. Component-by-component audit

### Faithful (verified against the pamphlet)

| component | SIM 3466 | ours | |
|---|---|---|---|
| Iron sulfate index | `2/1 − 5/4` | `(B2/B1) − (B5/B4)` | ✅ exact |
| Ferric iron 1 "redness" | `4/2` | `B4/B2` | ✅ exact |
| Ferric iron 2 | `4/2 × (4+6)/5` | `(B4/B2) × ((B4+B6)/B5)` | ✅ exact |
| Ferrous / coarse ferric | `(3+6)/(4+5)` | `(B3+B6)/(B4+B5)` | ✅ exact |
| Clay-sulfate-mica-marble | `6/7 − 5/4` | `B6/B7 − B5/B4` | ✅ exact |
| Green vegetation | `5/4` | `B5/B4` | ✅ exact |
| Class assignment order | "assigned to the first class for which all conditions are met" | first-match-wins | ✅ (v1.5.4 was last-match-wins; fixed in v2.0) |
| Dark-area mask | raw band 6 DN < 15,000 removed | `SR_B6 > 0.2125` | ⚠️ see note |
| Sensor / bands | Landsat 8 OLI, bands 1–7 | same | ✅ |

**Dark-mask note.** 15,000 × 0.0000275 − 0.2 = **0.2125** exactly, so our
constant is an arithmetically exact application of the Collection-2 Level-2
scaling to Rockwell's number. But their threshold is on *raw L1 DN* and ours is
on *L2 surface reflectance* — different physical quantities. The equivalence is
**nominal, not physical**, and is an open item.

### Departures (each measured below)

| # | component | SIM 3466 | v2.4.0 | severity |
|---|---|---|---|---|
| D1 | **Index thresholding** | "isolating the highest values using a **common standard deviation threshold**", then an index-specific clip — i.e. **per-scene statistics** | absolute constants derived at Silverton | **critical** |
| D2 | **Season** | "scenes acquired in **late May through early July are optimal**"; explicitly warns mid-July–October, where senesced dry vegetation mimics clay-sulfate-mica and causes **false identifications** | **Jul–Aug–Sep** | **critical** |
| D3 | **Iron fallback class** | every one of classes 9, 12, 14, 17, 18, 19 carries `AND` in the clay column | catch-all `hasIron → 12` with **no clay requirement** | **critical** |
| D4 | Class 9 vs 17 split | class 9 additionally requires **ferrous** | we use **brightness** | moderate |
| D5 | Atmospheric correction | dark-target subtraction on raw DN (Kaufman 1989, C = 5) | USGS C2 L2 surface reflectance (LaSRC) | defensible |
| D6 | Water mask | Landsat `1/6` ratio threshold | `MNDWI ∧ AWEInsh ∧ NDVI ∧ NIR<Green ∧ brightness` | deviation |
| D7 | Vegetation handling | mixed veg+mineral classes (13, 20, 21) | hard `NDVI < 0.25` gate | deviation |
| D8 | Input imagery | individual scenes | 2013–2020 multi-year summer **median composite** | deviation |

**D3 is the one that explains the most.** Because the fallback caught every
remaining iron pixel, our AMD decision reduced to `hasIron` alone — discarding
the clay and ferric corroboration Rockwell requires, and inheriting the
behaviour of the single weakest index. Test C had already scored `IronSulfate`
at **AUC 0.769 (FAILED)**; the pamphlet independently says the iron-sulfate
index needs the heaviest clipping of all and that "a lower degree of confidence
in the accuracies of results for these two groups is necessitated."

**D1 and D2 together are the direct cause of finding L1.** We replaced a
scene-relative statistical threshold with a site-specific constant, *and* chose
the season the authors warn against.

## 2. How much does each departure cost?

Leave-one-site-out over **Silverton + Summitville + Red Mountain Pass**: any
cutoff is fitted on two sites and applied unchanged to the third. Scored against
Rockwell's AMD classes {9,12,14,17,18,19} on pixels passing our land mask.
Worst-case Youden J (= TPR − FPR) is the headline because it is
prevalence-independent — AMD base rates differ 24-fold across these sites
(1.7% / 2.1% / 26.3%) — and cannot be gamed by flagging most of the scene.

| configuration | MIN J | mean J | MIN κ | mean κ | |
|---|---|---|---|---|---|
| **A — as shipped (v2.4.0)** | **0.107** | 0.474 | 0.120 | 0.139 | baseline |
| B — + paper season (D2) | 0.260 | 0.463 | 0.053 | 0.159 | 2.4× |
| C — + scene-relative cutoffs (D1) | 0.403 | 0.528 | 0.068 | 0.227 | 3.8× |
| **D — + clay requirement (D3)** | **0.440** | **0.541** | 0.101 | **0.257** | **4.1×** |
| — scene-relative only, wrong season | 0.149 | 0.491 | 0.121 | 0.168 | 1.4× |

Per-site, configuration A → D:

| site | J (A) | J (D) | κ (A) | κ (D) |
|---|---|---|---|---|
| Silverton | 0.674 | 0.729 | 0.170 | 0.188 |
| **Summitville** | **0.107** | **0.440** | **0.120** | **0.483** |
| Red Mountain Pass | 0.642 | 0.452 | 0.128 | 0.101 |

**The fixes are not free.** Summitville — the site we were failing — improves
enormously (J 0.107→0.440, κ 0.120→0.483) and Silverton improves slightly, but
**Red Mountain Pass degrades** (J 0.642→0.452). Worst-case across all three
still improves 4.1×, which is why the change is adopted, but the RMP regression
is real and should be watched.

**MIN κ does not improve** (0.120 → 0.101). κ is prevalence-sensitive and at
RMP/Silverton the AMD base rate is under 2.5%, which suppresses it structurally.
Mean κ nearly doubles. Report J, and report κ with its base rate attached.

### The season effect in isolation

Per-site AUC against Rockwell's AMD labels, Jul–Sep → May–Jul:

| index | Silverton | Summitville | Red Mtn Pass |
|---|---|---|---|
| IronSulfate | 0.938 → 0.939 | **0.678 → 0.810** | 0.896 → 0.858 |
| FerricIron2 | 0.733 → 0.791 | 0.718 → 0.806 | 0.780 → 0.762 |
| ClaySulfateMica | 0.858 → 0.898 | 0.743 → 0.777 | 0.905 → 0.894 |
| FerrousIron | 0.393 → 0.444 | 0.521 → 0.643 | 0.485 → 0.492 |

The single largest gain anywhere in this audit is IronSulfate at Summitville,
**+0.132 AUC**, purely from using the season the authors specify. Pooled across
sites every index improves. Red Mountain Pass alone gets slightly worse.

### The criterion search

34 candidate scores were tested (raw, normalised-difference, within-scene
z-score, within-scene percentile, and MIN/MEAN composites), ranked by worst-case
LOSO J. In the correct season:

| candidate | MIN J | MIN AUC |
|---|---|---|
| IronSulfate [within-scene percentile] | **0.470** | 0.810 |
| IronSulfate normdiff [z-score] | 0.472 | 0.835 |
| MEAN z(iron, f1, f2, clay) | 0.459 | 0.825 |
| **IronSulfate absolute (v2.4.0 form)** | **0.288** | 0.810 |

The winner is **the paper's own index with the paper's own thresholding style**.
A normalised-difference reformulation is statistically equivalent within noise
(0.472 vs 0.470) and was **not** adopted — it would be a departure from SIM 3466
with no demonstrated benefit.

### Pooled multi-site threshold re-derivation

Test C derived thresholds from Silverton polygons only. Re-derived on 3,158
pooled pixels across three sites (labels = Rockwell):

| index | Test C AUC | pooled AUC | per-site Youden range | shipped |
|---|---|---|---|---|
| IronSulfate | 0.769 | 0.657 | −0.045 … +0.107 | 0.10 |
| FerricIron1 | 0.992 | 0.642 | +1.910 … +2.075 | 1.983 |
| FerricIron2 | 0.997 | 0.630 | +3.749 … +4.281 | 3.758 |
| **FerrousIron** | 0.983 | **0.437** | +0.942 … +1.036 | 0.959 |
| ClaySulfateMica | 0.999 | 0.674 | +0.008 … +0.329 | 0.021 |

Two things to read carefully:

- **Every shipped constant lies inside its per-site optimal range.** The
  constants are not absurd — they are compromises that happen to suit some
  scenes and not others. `ClaySulfateMica` at 0.021 sits at the extreme low end
  (Silverton optimum 0.248, RMP 0.329), which fires clay far too readily at
  those two sites and is the mechanism of the **Silverton over-call**; iron at
  0.10 is far too high for Summitville (optimum −0.045), the mechanism of the
  **Summitville under-call**. Opposite errors at opposite sites — that composition
  *is* the inversion reported in v2.8.0.
- **`FerrousIron` has no discriminative power for AMD at any site**
  (0.485 / 0.393 / 0.521 — at or below chance). Its Test C AUC of 0.983 came
  from hand-drawn Silverton polygons; against Rockwell's labels it is noise.

Test C's 0.99-level AUCs do **not** reproduce. Part of that is a genuine label
change (hand polygons with bare-rock hard negatives vs Rockwell's classes), so
this is not proof Test C was wrong — but it does mean those AUCs cannot be
quoted as evidence the thresholds generalise.

## 3. Changes made (v3.0.0)

In `earth-engine/amd_detection_v2.4.0.js`:

1. `seasonFilter` default → **`'Mineral Mapping (May-Jul)'`** (new option);
   `'Summer (Jul-Sep)'` retained and annotated as known-biased.
2. `useStdDevThresholds` → **`true`**, with recalibrated multipliers
   `ironStdMult 2.0 → 0.5`, `clayStdMult 1.5 → 0.25`.
   ⚠️ **The old 2.0 / 1.5 multipliers score worst-case J = 0.000** — so far into
   the tail that nothing is flagged. Enabling this feature without recalibrating
   would have been much worse than leaving it off.
3. Unconditional `hasIron → 12` fallback **removed**, behind
   `useIronFallbackClass12` (default `false`) for reproducing v2.x.

`python/gee_classify.py` keeps **v2.4.0 defaults** so every existing validation
result stays reproducible; `iron_fallback=False` selects the new behaviour. The
NumPy port self-test still passes at its documented 94.95% ceiling.

## 4. What can and cannot be claimed

**Supported:**

> The tool is a faithful reimplementation of SIM 3466 at the level of spectral
> indices — all six index formulas and the first-match-wins assignment rule
> match the published definitions exactly. It departed from the published
> method in three respects: absolute rather than per-scene thresholds, a season
> window the authors explicitly warn against, and an iron-only fallback class
> absent from their Boolean logic. Those departures do not degrade agreement
> uniformly; they make it **site-dependent**, producing a 4.1× over-call where
> the thresholds were tuned and a 5.6× under-call at an independent AMD site.
> Restoring the published specification improves worst-case cross-site
> agreement 4.1× (Youden J 0.107 → 0.440).

**Not supported, and must not be claimed:**

- That our tool is *more accurate* than Rockwell's. No field data has been
  compared to either map. Every number here is agreement with an automated
  product.
- That Sentinel-2, the corrected water mask, or the ROC thresholds are
  improvements *on the published method*. They are changes; only D1–D3 have
  been measured, and all three were regressions.
- That Test C's thresholds are validated. They are Silverton-specific and, at
  the pooled level, three of the five indices score below AUC 0.68.

## 5. Caveats

- Labels come from Rockwell's published map, not the field.
- Positives are few at two of three sites (Silverton 28–38, RMP 19–23 pixels).
  Wilson intervals are reported per fold in the tool output; treat single-fold
  differences as indicative.
- Three sites is the minimum for leave-one-site-out. Conclusions about
  *stability* rest on three points.
- All three sites are Colorado alpine/subalpine. Nothing here tests desert or
  humid terrain, where the pamphlet warns behaviour differs most.
- D4–D8 remain unmeasured.

## 6. Next steps

1. **Measure the remaining departures**, in cost order: D7 (`NDVI < 0.25` gate,
   which costs 42–46% of Rockwell's AMD pixels before the cascade runs),
   D8 (median composite vs single scenes — the pamphlet analyses single scenes,
   and compositing is the most likely source of the Red Mountain Pass
   regression), then D4, D6, D5.
2. **Calibrate the ferric and ferrous multipliers.** Only `ironStdMult` and
   `clayStdMult` were LOSO-fitted; the ferric/ferrous multipliers are set to
   0.5 by assumption and drive classes 1–8, which nothing here validates.
3. **Investigate the Red Mountain Pass regression** (J 0.642 → 0.452). It is
   the one site where the paper-faithful configuration is worse, and it is
   3 km from Silverton — so it is not a climate effect.
4. **Add a fourth and fifth site outside Colorado** (Marysvale UT, Goldfield NV
   are already in `SITES`) to test the pamphlet's own claim that behaviour
   varies by climate.
5. **Re-derive `clayStdMult` properly** — it did not transfer (per-fold fits
   −0.5, −0.5, +1.0) and is currently the weakest adopted constant.
6. **Field verification remains the only route to an accuracy claim.** The
   Silverton "ours-only" and Summitville "Rockwell-only" AMD pixels are two
   oppositely-signed, mapped, ready-made ground-truthing lists.
