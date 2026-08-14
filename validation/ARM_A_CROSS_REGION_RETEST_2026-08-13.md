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

---

# PART 2 — Diagnostics: why it nulled, and what the pooled p-values were really measuring

**Added same day.** Code: `python/arma_diagnostics.py` · Raw output:
[`report_arma_diagnostics_2026-08-13.txt`](report_arma_diagnostics_2026-08-13.txt).

Part 1 established the null. This asks whether between-region variation was
*masking* a real within-system relationship, and what the apparently-significant
pooled sulfate/pH/conductance results actually were.

## First: the geology hypothesis is NOT tested here, on purpose

The "San Juan calderas behave differently" idea in Part 1 §4 was generated *by
looking at these signs*. Testing it on the same 31 catchments would fit the
grouping to the outcome — the identical error behind Test C's within-site
thresholds and finding W1's tuned-until-Ganau-scored-severe water indices.
`arma_diagnostics.py` therefore reports **no p-value** for it. What would
actually test it: assign geology labels from a published source for regions
chosen *before* seeing their signs, or predict the sign of new regions in
advance. Logged as such; not attempted.

## D1 — The dissolved-Fe null is robust, not a masking artifact

Removing every between-region difference by construction (rank within each
region, mean-centre, pool) leaves the relationship still absent:

| loading | within-region rho | perm p |
|---|---|---|
| ours M1 (AMD-area%) | +0.136 | 0.559 |
| ours M2 (NAP-weighted) | +0.170 | 0.461 |
| rockwell M1 | +0.162 | 0.489 |

Permutation shuffles chemistry *within* region only, preserving region
structure under the null. So the Part 1 null is not an artifact of pooling
dissimilar river systems — there is no detectable within-system relationship
between upstream AMD area and downstream dissolved Fe either.

## D2 — The "significant" pooled sulfate result REVERSES SIGN within regions

This is the most important result in Part 2, and it is methodological.

| | pooled | within-region |
|---|---|---|
| **Sulfate vs ours M1** | **−0.563 (p=0.001)** | **+0.220 (p=0.344)** |
| Sulfate vs ours M2 | −0.543 (p=0.002) | +0.203 (p=0.387) |
| Sulfate vs rockwell M2 | −0.496 (p=0.005) | +0.119 (p=0.623) |

Sulfate also has by far the highest between-region variance share (**67.5%**
between vs 32.5% within — variance decomposition on ranks).

Read together: the pooled sulfate correlation, which at p=0.001 would have
read as one of the strongest results this project has ever produced, was
**almost entirely a comparison between river systems, not a test of the
loading relationship** — and it points the *opposite* direction once that
between-system structure is removed. This is a textbook ecological fallacy
(Simpson's paradox), caught in our own data with the mechanism identified.

Variance decomposition for all variables:

| chemistry var | between-region | within-region |
|---|---|---|
| Sulfate | **67.5%** | 32.5% |
| dissolved Fe | 46.2% | 53.8% |
| specific conductance | 44.3% | 55.7% |
| pH | 39.6% | 60.4% |
| Fe (any fraction) | 19.0% | 81.0% |

## D3 — One lead, it favours ROCKWELL, and it does not survive correction

The only within-region relationships reaching uncorrected p<0.05:

| | within-region rho | perm p |
|---|---|---|
| pH vs **rockwell** M1 | **−0.525** | **0.015** |
| pH vs **rockwell** M2 | −0.458 | 0.039 |
| pH vs ours M1 | −0.237 | 0.311 |
| pH vs ours M2 | −0.271 | 0.242 |

The direction is mechanistically correct — more mapped AMD area upstream,
lower downstream pH — and it is the variable most directly tied to acid
production. Both of Rockwell's loading metrics agree; neither of ours reaches
significance.

**It does not survive multiple-comparison correction.** 20 within-region tests
were run; Benjamini-Hochberg threshold for the smallest p is 0.0025 and
Bonferroni α is 0.0025, against an observed p of 0.015. At uncorrected α=0.05,
20 tests produce ~1 false positive by chance, which is approximately what was
seen. **Treat as a lead to test on new data, not a finding.**

Worth stating plainly: this lead runs *opposite* to the retracted claim. If it
does replicate, it would support Rockwell's map predicting pH better than
ours — not the reverse.

## D4 — Catchment area is not the confound

| | rho |
|---|---|
| area vs dissolved Fe | +0.030 |
| area vs ours M1 | +0.367 |

Area correlates moderately with AMD-area fraction but essentially not at all
with dissolved Fe, and every rank partial correlation controlling for area is
within ~0.09 of its raw value (dissolved Fe/ours M1: +0.056 → +0.048). Area is
ruled out as an explanation for both the null and the sulfate reversal.

Dimensionally this is the expected result: outlet concentration ≈ load /
discharge, load scales with absolute AMD area and discharge with catchment
area, so AMD *fraction* (M1) is already the area-normalised quantity.

## D5 — Two regions contribute 6 catchments with no usable chemistry variation

| region | n | dissolved Fe range |
|---|---|---|
| Alma | 3 | 0.033 – 0.037 mg/L |
| Lake City | 3 | 0.000 – 0.018 mg/L |

Neither spans enough Fe to support a correlation; they were correctly below
the n≥4 cutoff for a per-region rho in Part 1 §2, so no reported per-region
number is affected — but they do contribute 6 of the 31 catchments to every
pooled figure, adding noise. Any future pooled estimate should screen on
outcome dynamic range, not just catchment count.

## What Part 2 changes

- The Part 1 retraction **stands and is strengthened**: the dissolved-Fe null
  survives removal of all between-region structure.
- The pooled sulfate/pH/conductance results flagged in Part 1 as "failed
  leave-one-region-out" now have a **named mechanism**: they were
  between-region comparisons, and sulfate's actively reverses sign.
- A concrete methodological rule for this project, beyond "use LORO": **report
  the between/within variance split alongside any pooled correlation over
  grouped data.** A pooled rho over 67%-between-variance data is not measuring
  what it appears to measure.

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

---

# PART 3 — DEM catchment delineation built and validated (the dilution fix)

**Added 2026-08-13.** Code: `python/catchment_dem.py` (`--self-test`).
Addresses OPEN item 2: the `hybas_12` granularity floor that averages
chemically distinct tributaries together and biases every Arm A number toward
the null.

## Validation against official USGS drainage areas

True D8 upstream tracing on MERIT Hydro (92.77 m), pour points snapped to the
modelled channel, validated on the same 6 Animas gauges used for `hybas_12`:

| gauge | NWIS sq mi | hybas_12 | **DEM** |
|---|---|---|---|
| Animas at Howardsville | 55.9 | 91.7 (1.64×) | **57.1 (1.02×)** |
| Animas at Silverton | 70.6 | 91.7 (1.30×) | 90.2 (1.28×) |
| **Cement Ck nr Silverton** | 13.5 | **91.7 (6.79×)** | **13.3 (0.99×)** |
| Mineral Ck abv Silverton | 11.0 | 51.9 (4.72×) | **11.0 (1.00×)** |
| Mineral Ck nr Silverton | 44.3 | 51.9 (1.17×) | 49.7 (1.12×) |
| Animas blw Silverton | 146.0 | 204.9 (1.40×) | **146.7 (1.00×)** |
| **within ±33%** | | **2/6** | **6/6** |

**The dilution problem is fixed.** `hybas_12` gave Howardsville, Silverton and
Cement Creek the *identical* 91.7 sq mi polygon; the DEM separates them into
57.1 / 90.2 / 13.3. Cement Creek — the acidic tributary whose signal was being
averaged away — is now resolved to within 1% of its published area.

**The tracing algorithm is independently verified.** MERIT's own `upa` band is
a precomputed upstream drainage area; our trace reproduces it at **ratio 1.00
for all 6 gauges**. That cleanly separates two error sources: tracing is
correct, so any residual disagreement with NWIS is about *where the pour point
sits*, not about the algorithm.

**The one imperfect gauge is diagnosed, not hand-waved.** Animas at Silverton
(1.28×) snapped *below* the Cement Creek confluence, absorbing Cement Creek's
area — confirmed independently by the nesting analysis below, which finds
Cement Creek fully contained in "Silverton". 70.6 + 13.3 ≈ 84, against a traced
90.2. Snap window was tested at 2 and 3 cells; it made no difference here
(the confluence is further than 3 cells), so the smaller window (2, ~185 m) was
adopted as it was never worse and fixed Mineral Ck abv (1.10× → 1.00×).

## The catch: nesting caps how much n can actually grow

With true delineation every station gets its own catchment, and stations on one
river are **deeply nested**. Measured on 5 Animas gauges:

```
Howardsville  ⊂ Silverton ⊂ Animas blw      (mainstem, overlap 1.00)
Cement Ck     ⊂ Silverton, Animas blw       (overlap 1.00)
Mineral nr    ⊂ Animas blw                  (overlap 1.00)
non-nested subset retained: 3 of 5
```

Their loading and their chemistry are largely *the same water*. Treating nested
catchments as independent observations would inflate n and manufacture
significance — the single biggest statistical hazard in moving from `hybas_12`
(whose coarse polygons accidentally prevented this) to DEM delineation.

`select_non_nested()` greedily retains the smallest/headwater catchments first,
since those carry the most independent information. **Consequence: DEM
delineation will NOT multiply n as hoped.** 5 stations → 3 independent
catchments here. The realistic gain over the current 31 is modest, and any
future Arm A run must report the non-nested n, not the station count.

## Status and what remains

The tool is built, validated 6/6 against published areas, internally
cross-checked against MERIT `upa`, and carries an explicit nesting guard. It is
**not yet wired into `watershed_nap.py`** — that integration, and the re-run of
Arm A on DEM catchments, is the next step. The scientific question it answers
is unchanged: does removing the Cement-Creek-style dilution reveal a
relationship that `hybas_12` was masking?
