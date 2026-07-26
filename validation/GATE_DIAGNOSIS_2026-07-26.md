# Why the Rockwell agreement inverts between sites — diagnosis

**Date:** 2026-07-26 · **Supersedes the mechanism claimed in**
[ROCKWELL_COMPARISON_2026-07-25.md](ROCKWELL_COMPARISON_2026-07-25.md) §"Contributing mechanism"
**Code:** `python/diagnose_veg_gate.py`, `python/iron_index_transfer.py`,
`python/compare_rockwell.py --class-col`

v2.8.0 recorded that our agreement with Rockwell's published map inverts
between sites — over-call where the Test C thresholds were derived (Silverton),
under-call at an independent AMD site (Summitville) — and proposed the land
mask's green-peak term (`Green/Red ≤ 1.0`) as the mechanism. **That mechanism is
wrong.** This is the diagnosis.

## Summary of what changed

| v2.8.0 said | actually |
|---|---|
| green-peak gate suppresses mineral detection | gate is **redundant**: it uniquely removes 0 px at Summitville, 6 px at Silverton |
| Summitville under-call is 8× | **5.6×** — the 8× compared two different footprints and denominators |
| mechanism unidentified beyond the gate | **`IronSulfate` loses discriminative power**: AUC 0.938 → 0.678 |
| Silverton/Red Mountain need async `Export.table.toDrive` | **solved** by tiled reducers/sampling; both now run synchronously |

## 1. The green-peak gate is redundant, not harmful

`python/diagnose_veg_gate.py --mode terms` counts, for every term of the land
mask, how many pixels it excludes **and how many it alone excludes** (pixels no
other term already removed). A term whose unique cost is zero cannot explain any
under-detection.

| term | Silverton fails | Silverton **only** | Summitville fails | Summitville **only** |
|---|---|---|---|---|
| water | 0.04% | 0.00% | 0.03% | 0.00% |
| not_bright | 0.01% | 0.00% | 0.03% | 0.02% |
| not_dark | 60.14% | 9.55% | 69.88% | 0.64% |
| not_builtup | 0.82% | 0.80% | 0.60% | 0.60% |
| **green_peak_ok** | 37.06% | **0.00%** (6 px) | 58.03% | **0.00%** (0 px) |
| **ndvi_ok** | 82.41% | **29.29%** | 96.07% | **22.25%** |

Pixels with a green peak essentially always also have NDVI ≥ 0.25, so the NDVI
term has already removed them. Confirmed independently by re-running the whole
classification with the gate set to `strict` / `relaxed` (≤1.15) / `override` /
`off`: **the class histograms are identical to the pixel** at both sites, and on
the disputed pixels (Rockwell ferric, ours vegetation) relaxing the gate recovers
**0 of 3,703**.

The binding term is `ndvi_ok` — `NDVI < 0.25` OR the iron override. It uniquely
removes 29.3% of Silverton and 22.3% of Summitville.

## 2. The land mask is a uniform ceiling, not the cause of the inversion

Only **10.42%** of Silverton and **2.87%** of Summitville pixels pass the land
mask, against Rockwell calling **21.3%** and **36.7%** mineral-eligible. Our
land arm therefore declines to classify most of the terrain Rockwell classifies.

Of Rockwell's AMD-indicator pixels:

| | Silverton | Summitville |
|---|---|---|
| killed by our land mask before the cascade | 28 / 66 = **42.4%** | 108 / 235 = **46.0%** |
| reached the cascade | 57.6% | 54.0% |
| …and we also call AMD | **84.2%** | **19.7%** |
| …and we call some other mineral | 15.8% | 80.3% |

The land-mask loss is ~42–46% at **both** sites — a real sensitivity ceiling,
but symmetric, so it cannot produce an inversion. Conditioning on the land mask
does not remove the inversion; it **sharpens** it:

| subset | n (Silv) | Rockwell | ours | ratio | n (Summ) | Rockwell | ours | ratio |
|---|---|---|---|---|---|---|---|---|
| all paired valid px | 13,949 | 0.47% | 1.94% | 4.09× | 11,029 | 2.13% | 0.38% | **0.18×** |
| passes our land mask | 1,453 | 2.62% | 18.58% | **7.11×** | 316 | 40.19% | 13.29% | **0.33×** |

The last row is the only threshold-vs-threshold comparison — both maps agree the
pixel is classifiable mineral terrain. The inversion is there, so it is about
**cutoffs and indices**, not masking.

## 3. The actual cause: every AMD class is gated on one failing index

All six AMD-indicator classes (9, 12, 14, 17, 18, 19) require
`has_iron` = **IronSulfate > 0.10**, where

```
IronSulfate = (B2/B1) − (B5/B4)
```

is a **difference of two unnormalised band ratios**. Nothing constrains its
absolute level between scenes, so an absolute cutoff is a scene-specific
constant. On pixels passing our land mask, scored against "Rockwell says AMD":

| site | n | n_AMD | **AUC** | median(AMD) | median(non-AMD) | separation |
|---|---|---|---|---|---|---|
| Silverton | 1,453 | 38 | **0.938** | +0.2023 | −0.0022 | +0.2045 |
| Summitville | 316 | 127 | **0.678** | −0.0166 | −0.1154 | +0.0988 |

Two things are happening at once:

1. **An offset.** The whole distribution sits ~0.09–0.22 lower at Summitville,
   so the fixed 0.10 captures 84.2% of Rockwell's AMD pixels at Silverton and
   only 19.7% at Summitville. Youden-optimal cutoffs: **+0.0906** at Silverton
   vs **−0.0464** at Summitville — opposite signs.
2. **A genuine loss of information.** AUC falls from 0.938 to 0.678. The index
   still separates at Summitville, but weakly. **No placement of a threshold
   repairs an AUC of 0.678.**

### Making the criterion scene-relative helps, and is not sufficient

Each rule was calibrated **once at Silverton** and applied unchanged to
Summitville — the transfer test Test C never ran:

| site | rule | flagged | precision | **recall** |
|---|---|---|---|---|
| Silverton | absolute > 0.10 | 18.6% | 0.119 | **0.842** |
| Summitville | absolute > 0.10 | 13.3% | 0.595 | **0.197** |
| Summitville | within-scene percentile (81.42) | 18.7% | 0.610 | **0.283** |
| Summitville | within-scene z-score (0.855) | 19.6% | 0.629 | **0.307** |

Scene-relative thresholding recovers recall from 0.197 to 0.307 — **+56%
relative** — confirming the offset is real and worth fixing. It still leaves
recall less than half the Silverton value.

There is also a hard arithmetic ceiling: at Summitville **40.2%** of land-mask
pixels are Rockwell-AMD, so a rule flagging ~19% of pixels cannot exceed
19/40 ≈ 47.5% recall. At 30.7% we reach about two-thirds of that ceiling. Raising
recall further requires flagging far more pixels, which only a **more
discriminative index** justifies.

### This was already predicted and overridden

Test C measured IronSulfate at **AUC 0.769 (FAILED, < 0.8)** against
hand-labelled polygons and recorded that its Youden cut "sits below scene
background and is unusable as a scene-wide threshold", and that adopted values
are "Silverton/L8-derived; re-derive before trusting on desert/humid scenes."
The threshold was nevertheless kept at 0.10 as "provisional". Summitville's
AUC 0.678 is consistent with that warning and inconsistent with the 0.938 the
same index scores against Rockwell labels at Silverton. **The independent site
confirms the Test C failure that was waved through.**

Note this is the *same defect class* as water finding W1, where `AWEINSH > 0.20`
tuned at Ganau excluded 100% of Piedmont's water pixels — an absolute cutoff on
a non-normalised index, calibrated at one site. It is now documented on both the
water and the land arm.

## 4. Corrected head-to-head numbers

Summitville was previously compared as two **independent histograms** over
different footprints with different denominators. Redone as a paired join on
identical pixels, through the same code path as Silverton:

| | Silverton | Summitville |
|---|---|---|
| sampled px / paired on valid Rockwell data | 31,888 / 13,949 | 18,008 / 11,029 |
| exact class agreement | 88.1% | **64.6%** |
| Cohen's κ | 0.552 | **0.080** |
| Rockwell AMD | 0.47% | 2.13% |
| ours AMD | 1.94% | 0.38% |
| precision vs Rockwell | 0.119 | 0.595 |
| recall vs Rockwell | 0.485 | **0.106** |
| binary κ | 0.184 | 0.175 |
| direction | we flag **4.1× more** | Rockwell flags **5.6× more** |

The inversion **survives** the corrected comparison at **5.6×** (2.13 / 0.38),
not the 8× reported in v2.8.0. Overall κ at Summitville is **0.080** — no
agreement beyond chance. The precision/recall pair swaps between sites: at
Summitville our few AMD calls are more often corroborated (0.595) but we find
only 10.6% of theirs.

**Cross-check.** The Silverton column here is a fresh 31,888-pixel export at the
full 15 km buffer; the v2.7.0 comparison used the 20,000 pixels exported by the
JS tool. They agree closely — 88.1% vs 87.9% agreement, κ 0.552 vs 0.546,
precision 0.119 vs 0.137, recall 0.485 vs 0.532 — so `gee_classify.py`'s
server-side replica reproduces the JS tool on an independent sample, and the
inversion is not an artifact of either sampling run.

**Is Rockwell plausible at Summitville?** 40.2% of our land-mask pixels being
AMD looks extreme, but our land mask keeps only 2.87% of the scene — the bare,
mine-disturbed ground of a Superfund open pit and heap-leach pad. A high AMD
fraction on exactly those pixels is what the site should look like, so the
reference labels are credible here.

## 5. Caveats

- **Rockwell's map is not ground truth.** It is a published automated
  classification. "Precision" here measures agreement, not correctness; neither
  map has been field-verified at either site.
- Silverton's AUC 0.938 rests on **38 positive pixels**. Treat as indicative.
- Rockwell's product is a multi-year Landsat 8 composite; ours is a 2013–2020
  summer median with different cloud masking. Some difference is temporal.
- Pixel counts come from EE reducers at `scale=30` in EPSG:4326, so a "pixel"
  is ~24 × 30 m at this latitude, not 30 × 30 m. Ratios are unaffected
  (numerator and denominator share the grid); absolute counts are not 30 m px.
- The `--mode terms` audit and the paired joins use different denominators by
  design; do not mix them.

## 6. Reproducing this

`data/` is gitignored repo-wide, so the two pixel exports behind these numbers
are not committed. Every step is deterministic (fixed seed, fixed date range and
season filter), so they regenerate exactly:

```bash
# 1. pixel exports with the land mask included (tiled; needed for 15 km Silverton)
python/diagnose_veg_gate.py --mode pixels --site "Summitville, CO" --pixels-n 18000 --tiles 3
python/diagnose_veg_gate.py --mode pixels --site "Silverton, CO"   --pixels-n 32000 --tiles 4

# 2. land-mask term audit (§1) and gate sensitivity
python/diagnose_veg_gate.py --mode terms --site "Summitville, CO" --tiles 3
python/diagnose_veg_gate.py --mode hist  --site "Summitville, CO" --tiles 3

# 3. land mask vs thresholds (§2)
python/diagnose_veg_gate.py --mode cond --csv data/imagery/gate_Silverton_CO.csv
python/diagnose_veg_gate.py --mode cond --csv data/imagery/gate_Summitville_CO.csv

# 4. the index transfer test (§3)
python/iron_index_transfer.py

# 5. paired head-to-head, same code path as Silverton (§4)
python/compare_rockwell.py --raster data/rockwell/L8_US_Southwest/SouthWest/l8_aa13_southwest_mosaic11.img \
  --pixels data/imagery/gate_Summitville_CO.csv --class-col cls_strict --label "Summitville, CO"
```

Two interpreters are needed: the Earth Engine steps (1, 2) run under
`D:/dev/VPCA+STEPWISE-REGRESSION/.venv` (which has `ee`), the raster steps
(3, 4, 5) under this repo's `.venv` (which has `rasterio`).

## 7. What this means for the thesis

Unchanged from v2.8.0 in direction, sharper in content. The defensible claim:

> Reimplementing the Rockwell method reproduces the published map at 87.9%
> agreement (κ = 0.55) over Silverton, but AMD-indicator agreement is poor
> (κ = 0.21) and **reverses at an independent AMD site** (Summitville: κ = 0.08,
> we detect 0.38% against their 2.13%). The reversal is traced to a single
> index: all six AMD classes require `IronSulfate = (B2/B1) − (B5/B4)` to exceed
> an absolute constant, and that index scores AUC 0.938 against reference labels
> at the calibration site but 0.678 at the independent site, with a
> Youden-optimal cutoff of opposite sign. Making the criterion scene-relative
> recovers 56% of the lost recall but cannot repair the discriminative loss.
> Fixed absolute thresholds on unnormalised ratio-difference indices do not
> transfer between scenes.

That is a specific, mechanistic, reproducible negative result with a named
cause — considerably more useful than an unexamined agreement score, and it
motivates hyperspectral/field calibration directly.

## 8. Next steps

1. **Replace or renormalise the iron criterion.** Two candidates to test
   head-to-head, both cheap: (a) a normalised difference form,
   `((B2/B1) − (B5/B4)) / ((B2/B1) + (B5/B4))`; (b) scene-standardised z-score
   with the cutoff carried across sites. Judge by *recall stability across
   sites*, not by within-site AUC — that is the error Test C made.
2. **Re-derive thresholds on pooled multi-site polygons** (Silverton +
   Summitville + Red Mountain Pass), which `derive_thresholds.py` supports.
   Now unblocked: tiled sampling handles the 15 km and 10 km footprints.
3. **Reconsider `NDVI < 0.25`.** It uniquely removes 22–29% of both scenes and
   costs ~42–46% of Rockwell's AMD pixels. Rockwell instead carries mixed
   vegetation-plus-mineral classes. A mixed class, or a higher NDVI ceiling with
   an unmixing step, is the principled fix — but it must be checked at Silverton
   so it does not amplify the 7.11× over-call.
4. **Red Mountain Pass** as a third site, now that tiling makes it runnable.
5. Sentinel-2 rerun of the land arm (Rockwell used L8 only) — red-edge bands and
   10 m pixels remain the clearest methodological advance available.
6. Field targeting: the Silverton "ours-only" AMD pixels and the Summitville
   "Rockwell-only" pixels are two ready-made, oppositely-signed ground-truthing
   lists. Visiting both settles which map is right where they disagree.
