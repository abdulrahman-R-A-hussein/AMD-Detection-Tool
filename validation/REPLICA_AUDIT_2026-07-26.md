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

**The fixes may not be free.** Summitville — the site we were failing —
improves enormously (J 0.107→0.440, κ 0.120→0.483) and Silverton improves
slightly, but **Red Mountain Pass appears to degrade** (J 0.642→0.452).
Worst-case across all three still improves 4.1×, which is why the change is
adopted.

Treat the RMP number cautiously: that site carries only **19–23 AMD positive
pixels**, the fewest of any site here, so its J is the least stable estimate in
this audit. §3c tested and largely ruled out the leading mechanistic
explanation (compositing). Increase the RMP sample before concluding the
regression is real — see §6.

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

## 3b. D7 measured — the NDVI gate (added same day, v3.0.1)

D7 was flagged as the highest-value open item, and it is now measured. The
land mask's `NDVI < 0.25` ceiling was swept over all valid pixels (36,391 across
three sites, May–Jul), rebuilding every other mask term per pixel and varying
only this one. AMD rule = v3.0.0 scene-relative iron AND clay. Recall here is
over **all** Rockwell AMD pixels in the scene, including those our mask drops,
so rows are directly comparable.

| NDVI ceiling | eligible px | MIN J | mean J |
|---|---|---|---|
| 0.25 (v2.x / v3.0.0) | 8.0% | 0.262 | 0.313 |
| **0.35 — adopted** | **11.1%** | **0.317** | **0.393** |
| 0.45 | 16.5% | 0.300 | 0.399 |
| 0.55 | 22.2% | 0.271 | 0.379 |
| ≥0.65 (gate off) | 23.5% | 0.266 | 0.373 |

Worst-case J improves **+21%** and mean J **+26%**. The gain is concentrated
where we were failing — Summitville recall 0.26 → 0.51, J 0.262 → 0.491 — and it
does **not** amplify the Silverton over-call (J 0.369 → 0.371) or harm Red
Mountain Pass (0.309 → 0.317). This is the first change in this audit that
improves all three sites at once.

**Finding L2 re-confirmed over a 2-D grid.** The green-peak ceiling was swept
jointly (1.0 / 1.1 / 1.2 / 1.4 / off) against the NDVI ceiling: it changes
worst-case J by **at most 0.001 at every combination**. It is not merely
redundant at the shipped NDVI cut — it is irrelevant across the whole
operating range. The saturation beyond NDVI 0.55 is caused by `notDark`
(`SWIR1 > 0.2125`), which already removes vegetated pixels, not by the
green-peak term.

## 3c. D8 attempted — compositing vs single scenes (inconclusive, and why)

D8 was the prime suspect for the Red Mountain Pass regression. SIM 3466 analyses
**individual scenes**; this tool builds a 2013–2020 median composite, and
`median(ratio) ≠ ratio(median)`, so the composited indices are not the quantity
the published thresholds describe. Tested by re-exporting each site from the
least-cloudy single scene in the May–Jul window
(`diagnose_veg_gate.py --single-scene`).

| site | input | land px | n_pos | Iron AUC | Clay AUC | v3.0 J |
|---|---|---|---|---|---|---|
| Silverton | median composite | 1,349 | 28 | 0.939 | 0.898 | 0.664 |
| Silverton | single scene | 532 | **6** | 0.943 | 0.957 | 0.719 |
| Summitville | median composite | 487 | 128 | **0.810** | 0.777 | **0.431** |
| Summitville | single scene | 439 | 114 | 0.750 | 0.756 | 0.416 |
| Red Mountain Pass | median composite | 1,147 | 19 | 0.858 | 0.894 | 0.704 |
| Red Mountain Pass | single scene | — | — | — | — | **blocked** |

**Verdict: inconclusive, and compositing is not obviously the culprit.** The two
usable sites disagree in direction, and the site that favours single scenes
(Silverton) rests on **6 positive pixels**. Summitville, with 114 positives, is
slightly *worse* on a single scene. Nothing here supports blaming D8 for the
RMP regression.

**The attempt produced a more useful finding than the test.** Red Mountain Pass
returned **0 usable pixels** from its least-cloudy May–Jul scene, and Silverton
lost 60% of its land pixels. At 3,400 m in late spring, single Landsat scenes
are routinely unusable — snow, terrain shadow and cloud remove the AOI even when
scene-level `CLOUD_COVER` metadata looks acceptable. **Compositing is therefore
a necessity at these sites, not a gratuitous deviation**, and the tool cannot
simply "become faithful" on this point. The honest position is that D8 is a
*justified* divergence whose cost is still unquantified.

To test it properly one would select scenes by **clear-pixel count inside the
AOI** rather than scene-level cloud metadata, and pool several single scenes per
site to get adequate positives. That is the correct next experiment.

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

1. ~~Measure D7 (`NDVI < 0.25` gate)~~ **done — see §3b. Relaxed to 0.35 in
   v3.0.1; worst-case J +21%, and the only change so far that helps all three
   sites.** ~~D8~~ **attempted — inconclusive, see §3c; single scenes are
   frequently unusable at these altitudes, so compositing is a justified
   divergence.** Remaining, in cost order: **D4** (class 9/17 split uses
   brightness where Rockwell uses ferrous), **D6** (water mask), **D5**
   (atmospheric correction).
2. **Calibrate the ferric and ferrous multipliers.** Only `ironStdMult` and
   `clayStdMult` were LOSO-fitted; the ferric/ferrous multipliers are set to
   0.5 by assumption and drive classes 1–8, which nothing here validates.
3. **Investigate the Red Mountain Pass regression** (J 0.642 → 0.452). It is
   the one site where the paper-faithful configuration is worse, and it sits
   ~3 km from Silverton, so climate is not the explanation. D8 is the prime
   suspect **and has now been partly ruled out** (§3c: the two testable sites
   disagree in direction, and Summitville is slightly worse on single scenes).
   The remaining and more likely explanation is small-sample noise: RMP has the
   fewest AMD positives of any site (19–23 px), so its J estimate is the least
   stable. Increase the sample at RMP before treating the regression as real.
4. **Add a fourth and fifth site outside Colorado** (Marysvale UT, Goldfield NV
   are already in `SITES`) to test the pamphlet's own claim that behaviour
   varies by climate.
5. **Re-derive `clayStdMult` properly** — it did not transfer (per-fold fits
   −0.5, −0.5, +1.0) and is currently the weakest adopted constant.
6. **Field verification remains the only route to an accuracy claim.** The
   Silverton "ours-only" and Summitville "Rockwell-only" AMD pixels are two
   oppositely-signed, mapped, ready-made ground-truthing lists.

---

## 7. Session state, 2026-07-26 — where to pick up

Shipped this session: **v2.9.0 → v3.0.2**. Every claim below is reproducible
from committed code; `data/` is gitignored but all pipelines are deterministic
(fixed seed, fixed dates) — see §6 for the exact commands.

### Settled (do not re-derive)

| | |
|---|---|
| Green-peak gate `Green/Red ≤ 1.0` | **irrelevant.** Moves worst-case J by ≤0.001 at every point of a 2-D NDVI × green-peak grid. Not the cause of anything. |
| Root cause of the v2.8.0 inversion | Three departures from SIM 3466: absolute thresholds (D1), wrong season (D2), clay-free iron fallback (D3). |
| Index formulas | All six match the pamphlet **exactly**. The replica is faithful at the index level. |
| `FerrousIron` index | **AUC 0.437 pooled, at or below chance at all three sites.** No AMD discriminative power. Test C's 0.983 does not reproduce. |
| EE memory limit | Solved by tiled reducers/sampling. No async `Export.table.toDrive` needed. |
| Summitville under-call | 5.6× (paired), not the 8× first reported. |

### Open, in priority order

1. **Increase the Red Mountain Pass sample** (19–23 positives). Everything about
   the one apparent regression under v3.0.x rests on that thin estimate.
2. **Calibrate `ferric1StdMult`, `ferric2StdMult`, `ferrousStdMult`.** v3.0.0
   sets all three to 0.5 *by assumption*; only iron and clay were LOSO-fitted.
   They drive classes 1–8, which nothing here validates.
3. **Re-derive `clayStdMult`** — did not transfer (per-fold fits −0.5, −0.5,
   +1.0). Weakest adopted constant.
4. **D8 properly**: select scenes by clear-pixel count *inside the AOI*, not
   scene-level `CLOUD_COVER`, and pool several scenes per site.
5. **D4, D6, D5** unmeasured (class 9/17 split; water mask; atmospheric
   correction).
6. **Sites outside Colorado** — Marysvale UT and Goldfield NV are already in
   `SITES`. All three current sites are Colorado alpine; the pamphlet warns
   behaviour varies most by climate.
7. **Field verification** is the only route to an accuracy claim. Two mapped,
   oppositely-signed ground-truthing lists already exist: Silverton
   "ours-only" AMD pixels and Summitville "Rockwell-only" AMD pixels.

### The one thing to keep straight

Every number in this audit is **agreement with Rockwell's published automated
map**, not accuracy. The supportable claim is that restoring the published
specification improves cross-site agreement 4.1×. The claim that this tool is
*better than* Rockwell's remains unsupported and requires fieldwork.
