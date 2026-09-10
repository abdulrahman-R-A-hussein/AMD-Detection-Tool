# Phase CMD3 — Pennsylvania: the SIGN replicates, the SCALE does not. CMD2's landscape reading is bounded to Ohio, and the radius ladder fails as a mechanism diagnostic

**Date:** 2026-09-09 · **Registered:** [`CMD3_PREREGISTRATION_2026-09-09.md`](CMD3_PREREGISTRATION_2026-09-09.md), committed `4765bca` **before any Pennsylvania chemistry was downloaded**
**Raw output:** [`report_cmd3_pa_2026-09-09.txt`](report_cmd3_pa_2026-09-09.txt)

## Verdict in one box

> **FAILS TO REPLICATE**, on the registered falsifier, which fired exactly as
> named: **|rho| peaks at 30 m** and collapses to nothing at landscape scale.
>
> Pennsylvania's ladder is **monotone declining** — the **opposite shape** from
> Ohio's, which rose to its maximum at 1 km. Two basins of the same drainage
> type disagree about the *scale* of the association.
>
> **What does replicate is the SIGN.** Negative in both basins, at every near
> radius, in both analytes — and in Pennsylvania it is **sign-consistent across
> sub-basins**, which Ohio never achieved at any radius.
>
> **The load-bearing consequence is methodological: the radius ladder does not
> work as a mechanism diagnostic.** CMD1 amendment 2 registered radius shape as
> the way to tell "seep" from "catchment-scale land cover". That diagnostic
> gives opposite answers in two coal basins, so it cannot carry the inference it
> was built for.

## 1. The two ladders

`NDVI_stress` vs **sulfate** (primary):

| radius | 30 m | 60 m | 100 m | 500 m | 1000 m |
|---|---|---|---|---|---|
| rho | **−0.143** | −0.135 | −0.114 | −0.010 | −0.050 |
| n | 268 | 269 | 271 | 274 | 274 |
| perm p | **0.0200** | 0.0326 | 0.0676 | 0.8758 | 0.4029 |
| signs | **CONSISTENT** | disagree | disagree | disagree | disagree |

`NDVI_stress` vs **specific conductance** (larger n, and the cleaner result):

| radius | 30 m | 60 m | 100 m | 500 m | 1000 m |
|---|---|---|---|---|---|
| rho | **−0.187** | −0.158 | −0.138 | −0.010 | **+0.003** |
| n | 443 | 445 | 447 | 450 | 450 |
| perm p | **0.0002** | 0.0014 | 0.0062 | 0.8332 | 0.9618 |
| signs | **CONSISTENT** | **CONSISTENT** | **CONSISTENT** | disagree | disagree |

Both analytes: monotone decline, significance lost by 100–500 m, and **exactly
nothing at 1 km** (+0.003, p = 0.96).

## 2. Against Ohio, side by side

| radius | Ohio (CMD2) | Pennsylvania (CMD3) |
|---|---|---|
| 30 m | −0.354 | −0.143 |
| 60 m | −0.253 | −0.135 |
| 100 m | −0.255 | −0.114 |
| 500 m | −0.393 | −0.010 |
| **1000 m** | **−0.438** ← max | **−0.050** ← ~zero |
| shape | **U, rising to 1 km** | **monotone declining** |
| |rho| max at | **1000 m** | **30 m** |

These are not merely different magnitudes. They are **opposite functions of
radius**, and each one is the other's registered falsifier.

## 3. The registered verdict, and an ambiguity in my own table

The pre-registration's verdict table had three rows:

| outcome | verdict |
|---|---|
| (a) and (b) | REPLICATES |
| (a) or (b), not both | PARTIAL |
| neither, **or |rho| peaks at 30 m** | FAILS TO REPLICATE |

The observed result satisfies **(a)** — negative pooled rho — and fails **(b)**
— |rho| rising with radius. By row 2 that reads PARTIAL. But row 3 names
"|rho| peaks at 30 m" as a falsifier, **and that is precisely what happened**.

**The rows conflict, and the specific named falsifier governs.** Verdict:
**FAILS TO REPLICATE.** Taking row 2 because it is kinder would be choosing a
reading after seeing the outcome, which is the exact move this project's rules
exist to prevent.

**Lesson for future pre-registrations, recorded because it cost something
here:** a verdict table must have **mutually exclusive** rows. Mine did not.
Enumerating a named falsifier *and* a generic partial branch that the same data
can satisfy leaves room for exactly the post-hoc choice the registration was
meant to remove.

## 4. What this does to CMD2

**CMD2's finding is not withdrawn — it is bounded.** In Ohio the association
demonstrably strengthens to 1 km; that measurement stands. What cannot stand is
the *general* claim that the coal-basin vegetation–sulfate association is
catchment-scale. It is catchment-scale **in Ohio** and near-field **in
Pennsylvania**.

**And the diagnostic that produced the CMD2 conclusion is now suspect.** CMD1
amendment 2 registered, in advance:

> *|rho| rising as radius grows → the association is with catchment-scale land
> cover, not the seep.*

Applied to Pennsylvania the same rule says "near the seep". Applied to Ohio it
says "catchment-scale". **A diagnostic that returns opposite mechanisms for the
same drainage type is not measuring mechanism.** It is more plausibly measuring
basin geometry — how mining disturbance is spatially arranged relative to
monitoring stations, which differs between the dissected Allegheny Plateau of
southeastern Ohio and the West Branch's broader valleys.

**This is the third time a monotone-looking trend in this project has failed to
generalise** — after the Colorado resolution claim and CMD1's own geometry
gradient. See `DECISION_LOG.md` correction #6, which now has a third instance.

## 5. What Pennsylvania achieved that Ohio never did

**Sign consistency.** Ohio read "signs disagree" at all five radii in CMD2. In
Pennsylvania, conductance is sign-consistent across all three near radii and
sulfate at 30 m, on:

- **274 sulfate-matched stations** vs Ohio's 137, and **450** for conductance;
- **1–3% between-region variance** vs Ohio's 13%;
- three **spatially disjoint** tiles fixed with coordinates before any
  chemistry was seen, so no grouping could be chosen after seeing signs.

That is the strongest *design* the CMD arm has had. It is also why the null at
500/1000 m is credible rather than merely underpowered: the same design detects
the association cleanly at 30 m with p = 0.0002.

**But it is weak.** |rho| = 0.143 (sulfate) and 0.187 (conductance) are far
below this project's |rho| ≥ 0.3 bar. On its own terms Pennsylvania is a
**weak, near-field, sign-consistent negative association** — not a detection
result.

## 6. Limitations, all registered before the data

- **Unconditioned.** The CMD2 mining-extent confound test **cannot** be run
  here: ODNR `MinesOfOhio` is Ohio-only, and NLCD was rejected as a substitute
  because it shares the NDVI physics and would regress the vegetation signal
  partly on itself. **So it is unknown whether Pennsylvania's near-field
  association survives conditioning on mining extent**, and this result cannot
  move CMD2's PARTIAL confound verdict in either direction.
- **Canopy gate passed** — median buffer `NDVI_stress` is below
  `CANOPY_NDVI_LIMIT = 0.6`, so the 500/1000 m null is interpretable and not a
  canopy artifact.
- **All three tiles cleared the pre-registered n ≥ 8 bar** (23 / 113 / 138
  sulfate-matched), so none was excluded from the sign-consistency headline.
- **Tiles are named for their dominant AMD stream but were fixed as bounding
  boxes**, not delineated catchments. The registration stated the
  stream-to-tile correspondence is not load-bearing; what matters is that they
  are disjoint and outcome-blind.

## 7. What may and may not be said

**MAY**
- A **negative** `NDVI_stress`–sulfate/conductance association replicates in an
  independent bituminous coal basin: **−0.143 (n=268, p=0.020)** and
  **−0.187 (n=443, p=0.0002)** at 30 m, **sign-consistent across three disjoint
  sub-basins** — the first sign-consistent result the CMD arm has produced.
- In Pennsylvania that association is **near-field**: it collapses to
  **−0.010 (p=0.88)** at 500 m and **+0.003 (p=0.96)** at 1 km.
- **CMD2's catchment-scale reading is bounded to Ohio** and does not generalise.
- **Radius shape does not diagnose mechanism** across basins.

**MAY NOT**
- That the landscape-scale reading **replicated** — the named falsifier fired.
- That this **restores** a near-channel or seep-detection claim. |rho| = 0.14–0.19
  is far below the project's bar, and a weak near-field association in one basin
  against a strong far-field one in another is evidence that **radius tells us
  about basin geometry, not about seeps**.
- That the confound is addressed in Pennsylvania — **it was never tested there.**
- Any **optical sulfate** claim, ever. Sulfate has no VNIR absorption; this is
  vegetation that co-varies with it.
- Any revival of the withdrawn UAV argument. If anything this weakens it
  further: the one basin where the signal is near-field is also the basin where
  it is weakest.

## 8. Method notes worth keeping

**The GEE memory trap has a fourth lever, and only two of the four are safe.**
Moshannon Creek (162 stations, 120 scenes) failed the 500/1000 m ladder at
batch=2 with the band subset **already** applied — both previously known
request-size levers exhausted.

Lowering the batch floor **2 → 1** completed it. Measured rather than assumed:
batch=1 vs batch=25 over 20 stations at 500 m gives max absolute difference
**1.11e-16**, one double-precision ULP. **Note this is *not* bit-identical the
way the band subset is** (that measures exactly **0.000** over 27 stations), so
the honest wording is *"identical to within float epsilon"*.

The ordering is the reusable part:

| lever | safe? | why |
|---|---|---|
| band count | ✅ bit-identical (0.000) | request size only |
| batch size (floor 1) | ✅ to float epsilon (1.1e-16) | request size only |
| **scene depth** | ❌ | a shallower stack is a **different composite and different numbers** |
| **coarser scale** | ❌ | same objection, more so |

Reaching for the scene cap first is the tempting mistake and it silently
converts a memory problem into a methodology problem. It was **not** used here:
all three tiles kept the full 120 scenes, so the three are mutually comparable.

**`--bbox` acquisition worked end-to-end.** All three Pennsylvania regions were
registered and fetched with **no source edit** — the first use of the
`data/regions.json` overlay, and the demonstration that the pipeline is no
longer registry-gated.

## 9. Next

1. **The sign is what replicated, so test the sign properly.** A negative
   vegetation–sulfate association now holds in two basins and, in
   Pennsylvania, across three disjoint sub-basins. That is the claim worth
   pursuing — not its scale.
2. **A Pennsylvania disturbance covariate.** PA DEP mine-drainage and
   abandoned-mine-land datasets are the analogue of ODNR and would make the
   PA result conditionable, which is currently its biggest gap.
3. **Stop using radius shape to infer mechanism.** It has now given opposite
   answers in two basins. If mechanism is the question, it needs a design that
   varies mechanism, not footprint.
4. **Explain the basin difference.** Ohio's dissected plateau vs the West
   Branch's broader valleys is the obvious hypothesis — but it was generated by
   looking at these two results, so it cannot be tested on them. It needs a
   third basin with the prediction fixed in advance.

## Reproduce

```
python python/fetch_wqp.py --region "Chest Creek, PA"      --bbox "40.55,-78.85,40.95,-78.63"
python python/fetch_wqp.py --region "Clearfield Creek, PA" --bbox "40.50,-78.62,41.05,-78.32"
python python/fetch_wqp.py --region "Moshannon Creek, PA"  --bbox "40.78,-78.32,41.18,-77.95"

# near and far ladders, per tile (--bands is the memory fix; keeps all 120 scenes)
python python/cmd_detect.py --extract --season leafoff --radii 30,60,100 \
    --bands NDVI_stress --regions <slug> --out data/matched/cmd3geo_l8_<slug>.csv
python python/cmd_detect.py --extract --season leafoff --radii 500,1000 \
    --bands NDVI_stress --regions <slug> --out data/matched/cmd3far_l8_<slug>.csv

python python/cmd_detect.py --analyse \
    --inputs "data/matched/cmd3geo_l8_*.csv,data/matched/cmd3far_l8_*.csv" --radii 30 \
    --out validation/report_cmd3_pa_2026-09-09.txt
```
