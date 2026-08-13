# Arm A cross-region re-test: the n=6 finding does not replicate

**Date:** 2026-08-13 · **Status: the headline result from 2026-08-10 is
RETRACTED.** Do not cite "our map predicts dissolved Fe better than
Rockwell's" without this file attached.

**Code:** `python/watershed_nap.py` (generalised `--region`),
`python/pool_watershed_nap.py` (new — pooled / per-region / leave-one-region-out
analysis). **Raw output:**
[`report_watershed_nap_pooled_2026-08-13.txt`](report_watershed_nap_pooled_2026-08-13.txt).
**Per-region CSVs:** `data/matched/watershed_nap_*.csv` (gitignored, all
regenerable — see §5).

## What this is answering

The 2026-08-10 report ([`WATER_PHASE2_2026-08-10.md`](WATER_PHASE2_2026-08-10.md))
found, at 6 catchments in a single river system (the Animas, around
Silverton), that our v3.0.x map's AMD-area fraction predicted measured
dissolved Fe far better than Rockwell's published map (rho +0.714 vs +0.257;
LOOCV R² +0.804 vs −1.542) — scored against real USGS chemistry, the only
ground-truth-validated result in the project. It was reported as **suggestive,
not proven**: exact permutation p = 0.136, and n=6 was shown to be a real
ceiling within that one search area (82 stations across genuinely different
sub-watersheds all collapsed into the same 6 `hybas_12` polygons).

The approved plan for this session was explicit: raise n by adding
**genuinely separate river systems**, then report pooled, per-region, and
leave-one-region-out — not just a bigger pooled number — because pooling
across regions with different geology, climate, illumination and scene
availability can manufacture a correlation as easily as reveal one. That is
finding L1's lesson (never judge a threshold or relationship by within-sample
performance) applied to Arm A instead of to the land-arm thresholds.

## Method

Six additional Colorado Mineral Belt mining districts were probed via WQP,
fetched, and run through the unmodified Arm A pipeline (`watershed_nap.py`,
`catchment_delineation.py`'s `NEXT_DOWN` traversal, `classify_v3`'s
scene-relative thresholds, Rockwell raster zonal stats):

| region | distinct catchments | notes |
|---|---|---|
| Silverton (original) | 6 | 2026-08-10 result |
| Ouray | 6 | |
| Central City | 5 | |
| Creede | 4 | |
| Leadville | 4 | |
| Lake City | 3 | |
| Alma | 3 | |
| **total** | **31** | 7 independent river systems |

All six new regions drain entirely different systems from the Animas
(Gunnison, Arkansas headwaters, South Platte, Rio Grande), so none of this n
comes from further subdividing Silverton — it is genuinely new information.

Three checks were run, per the plan, and must be read together:

1. **Pooled** Spearman rho + permutation p (100,000 random permutations —
   exact enumeration is only tractable to n≈8).
2. **Per-region** rho, for regions with ≥4 catchments, to see whether one
   region drives the pooled number.
3. **Leave-one-region-out R²** — fit a linear model on six river systems,
   predict the seventh's chemistry from its loading, pool the squared
   residuals across every region's turn as the held-out set. This is the
   actual generalisation test: does loading measured *elsewhere* predict
   chemistry *here*, in a system the fit never saw.

## Result

### 1. Pooled (n=31) — dissolved Fe collapses to noise

| loading | rho | p |
|---|---|---|
| **ours M1 (AMD-area%)** | **+0.056** | **0.760** |
| ours M2 (NAP-weighted) | +0.042 | 0.820 |
| rockwell M1 | +0.122 | 0.507 |
| rockwell M2 | +0.088 | 0.633 |

The 2026-08-10 headline (+0.714, p=0.136) is gone. At n=31 there is no
detectable pooled relationship between upstream AMD-area and dissolved Fe, for
either map.

### 2. Per-region — the sign is not even consistent

| region | n | ours M1 rho (dissolved Fe) |
|---|---|---|
| Silverton | 6 | **+0.714** |
| Ouray | 6 | **+0.667** |
| Central City | 5 | **−0.700** |
| Creede | 4 | **−0.800** |
| Leadville | 4 | **−0.800** |

Two systems (Silverton, Ouray — both in the San Juan Mountains, geologically
similar) show a strong positive relationship. Three others show a strong
*negative* one. This is not scatter around a weak true effect; it looks like
two different regimes. Geological similarity between the positive pair is a
plausible lead (see §4) but is speculation, not yet tested.

### 3. Leave-one-region-out R² — confirms no generalisation, for anything

| chemistry var | loading | LORO R² |
|---|---|---|
| dissolved Fe | ours M1 | **−0.168** |
| dissolved Fe | rockwell M1 | −0.093 |
| sulfate | ours M1 | +0.081 |
| sulfate | rockwell M1 | −0.258 |
| pH | ours M1 | −0.141 |
| specific conductance | ours M1 | −0.109 |

**Every dissolved-Fe LORO R² is negative** — worse than predicting the mean.
The best value anywhere in the whole table is sulfate/ours-M1 at **+0.081**,
barely above zero and not a usable predictive result. Nothing here
generalises across river systems, for either map, for any chemistry variable
tested.

### A methodological illustration worth keeping

Pooled sulfate, pH, and specific-conductance results *look* significant:
sulfate/ours-M1 rho=−0.563, p=0.001; pH/ours-M1 rho=+0.415, p=0.021;
conductance/ours-M1 rho=−0.415, p=0.036. Taken alone, any one of these would
read as a real finding. **All three fail the leave-one-region-out test** —
their LORO R² is negative or negligible. Twenty pooled tests were run (5
chemistry variables × 4 loading metrics); at uncorrected α=0.05, roughly one
false positive is expected by chance alone, and that is approximately what
was observed. **This is exactly the L1 risk, demonstrated directly**:
pooled/within-sample significance is not evidence of a generalisable
relationship, and must not be reported as one without the held-out check.

## What this does and does not mean

**Does not mean:** the tool is broken, or that watershed-scale mineral
mapping can never predict water chemistry. Two real limitations bound how
strong a test this was:

- **`hybas_12`'s granularity floor** (documented 2026-08-10) merges
  disproportionately acidic tributaries — Cement Creek at Silverton is the
  known example — with cleaner water sharing its polygon. This dilutes any
  true relationship *within every region*, not just Silverton, biasing every
  number in this report toward the null.
- **31 catchments is still not large.** The per-region split (§2) suggests
  something systematic rather than pure noise — geological or climatic
  differences between mining districts are a real, physical candidate
  explanation, not yet tested.

**Does mean:** the specific claim "our v3.0.x map's AMD-area fraction
predicts dissolved Fe better than Rockwell's map" is **not supported** by the
evidence gathered so far, and must not appear in a grant application or any
other document without this retraction attached. The honest current position
is: *no cross-region-validated relationship between satellite-derived
watershed mineral loading and measured water chemistry has been demonstrated
by either map.*

## Why this is a good outcome, not a bad session

This is precisely what the leave-one-region-out test was built to catch, and
it caught it **before** the finding went into a grant narrative. Finding an
n=6 false positive collapse at n=31, in-house, with the mechanism understood,
is a far better outcome than a reviewer or a field season finding it later.

## Next steps

1. **Test the geological-cluster hypothesis directly.** Silverton and Ouray
   (both positive) are both San Juan volcanic-field caldera systems; Central
   City, Creede, Leadville (negative or mixed) are not. If the sign tracks
   geology, that is itself a finding — "mineral-area loading predicts
   chemistry only within consistent alteration-style terrain" — and a testable
   one with the data already in hand (no new fetching required).
2. **Address the `hybas_12` dilution problem before concluding further.** True
   DEM flow-accumulation delineation (`MERIT/Hydro/v1_0_1` `dir` band) would
   let Cement-Creek-type tributaries be scored separately from the water they
   currently get averaged into. This is the highest-leverage open item — it
   affects every region, not just one.
3. **Do not add more regions to chase significance.** 31 catchments across 7
   systems is already a reasonably powered test for an effect of this
   plausible size; the result is a clean null with the current methodology,
   not an underpowered one. Fix the catchment-resolution confound (item 2)
   before spending more compute on more river systems with the same
   resolution ceiling.
4. **B2 (precipitate/seep) and B1 (Colorado streams)** remain the other two
   open water-arm items from 2026-08-10, unaffected by this result.

## 5. Reproducing this

```bash
# per region (repeat for each; VPCA venv, has ee)
D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe python/watershed_nap.py \
  --region "Ouray, CO" --min-samples 5 --max-stations 30 --radius-km 60

# pool everything and run all three checks (repo venv, no ee needed)
.venv/Scripts/python.exe python/pool_watershed_nap.py
```

`REGIONS` bboxes for the six new districts are in `python/fetch_wqp.py`.
