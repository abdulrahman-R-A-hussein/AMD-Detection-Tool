# Phase CMD2 — the mining-extent confound test: the confound is REAL, and the "near-channel seep" reading of CMD1 is REFUTED

**Date:** 2026-09-08 · **Registered:** [`CMD2_PREREGISTRATION_2026-09-08.md`](CMD2_PREREGISTRATION_2026-09-08.md), committed `a452446` **before any mine polygon was joined to any chemistry value**
**Raw output:** [`report_cmd2_confound_2026-09-08.txt`](report_cmd2_confound_2026-09-08.txt)

## Verdict in one box

> **T1 (registered primary): PARTIAL, by 0.004.** Partial rho = **−0.246**
> (n=131, within-region permutation p = 0.0254). The registered bar for
> "confound rejected" was |rho| ≥ 0.25. It misses. The bar was fixed in advance
> and is applied as written; it is not moved now.
>
> **T2 (registered secondary, independent machinery): the association is
> LANDSCAPE-SCALE.** Extending the radius ladder to 1 km makes it *stronger*,
> not weaker — **−0.438 at 1000 m versus −0.354 at 30 m**. CMD1 amendment 2
> registered the reading of exactly this pattern in advance: **|rho| rising as
> radius grows ⇒ the association is with catchment-scale land cover, not the
> seep.**
>
> **Net: CMD1's "the Ohio null was sampling-geometry-limited, the target is near
> the channel" interpretation is REFUTED by its own registered criterion.**

## 1. The confound is real and operative (T0)

This holds regardless of anything downstream. Both legs the confound requires are
present:

| leg | rho | reading |
|---|---|---|
| mine extent → sulfate | **+0.519** | strong. More mined upstream ground, more sulfate |
| mine extent → `NDVI_stress` | **−0.283** | present. More mined upstream ground, less vegetation |

The T0 guard therefore **passes**: mining extent moves both the exposure and the
outcome, so it is a genuine confounder. Had this leg been absent, the
pre-registration required T1 to be reported as *uninformative* rather than
supportive. It is not absent, so T1 is informative.

**It explains a real share, but not all.** The three Spearman components:

```
r(NDVI_stress, sulfate)   = -0.348
r(NDVI_stress, mine_frac) = -0.283
r(sulfate,     mine_frac) = +0.519
```

The confound path carries `(−0.283)(+0.519) = −0.147` of the raw `−0.348` — about
**42% of the raw covariance**, leaving a partial of **−0.246**, a **29%
attenuation**.

## 2. T1 — the primary table

| covariate conditioned on | partial rho | n | perm p | attenuation | signs |
|---|---|---|---|---|---|
| **catchment, all coal (PRIMARY)** | **−0.246** | 131 | **0.0254** | +29% | disagree |
| catchment, surface coal only | −0.191 | 131 | 0.1224 | +45% | disagree |
| catchment, underground coal only | −0.279 | 131 | 0.0124 | +20% | disagree |
| 1 km disc *(secondary)* | −0.372 | 137 | 0.0004 | −5% | **CONSISTENT** |
| 5 km disc *(secondary)* | −0.338 | 137 | 0.0014 | +5% | **CONSISTENT** |

Raw, unconditioned, same rows: **−0.354** (n=137).

**The primary arm is the catchment arm, by registration.** The disc arms are the
registered *secondary* ladder. They are reported in full and are **not**
substituted for the primary verdict — picking the covariate that gives the nicer
answer, after seeing all five, is precisely the move this project's rules exist
to prevent.

**One mechanistically coherent detail.** Conditioning on *surface* mining
attenuates most (45%, and it goes non-significant at p = 0.12); conditioning on
*underground* mining attenuates least (20%). Surface mining is the kind that
physically removes vegetation, so it is the kind that should absorb a vegetation
signal — and it does.

## 3. T2 — the result that actually decides this phase

Same leaf-off composite, same index, same stations; only the buffer radius
changes. `NDVI_stress` vs sulfate:

| radius | 30 m | 60 m | 100 m | 500 m | **1000 m** |
|---|---|---|---|---|---|
| **rho** | −0.354 | −0.253 | −0.255 | −0.393 | **−0.438** |
| n | 137 | 140 | 141 | 146 | 146 |
| median n_px | 9 | 26 | 59 | 1184 | 4591 |

**The ladder is U-shaped, and its global maximum is at the largest footprint
tested.** From 100 m outward the association strengthens monotonically and
substantially: 0.255 → 0.393 → 0.438.

CMD1 amendment 2 fixed the interpretation of this in advance, in a table with
three rows, one of which reads:

> *|rho| rises as radius **grows** → the association is with **catchment-scale
> land cover**, not the seep — which would be a different (and weaker) claim
> entirely.*

That is the observed pattern. **The registered conclusion is the one that must be
taken.**

**Why CMD1 read it the other way.** CMD1's ladder stopped at 100 m and saw
0.255 → 0.253 → 0.354 as the radius shrank, which looks like a clean monotone
"tighter is better" gradient pointing at the channel. It was the descending left
arm of a U. Widening the window inverts the conclusion. This is the same
failure mode as the Colorado resolution claim, which also looked monotone inside
a narrow window and reversed once the window was extended.

**What this costs.** CMD1's geometry report said the gradient "now supports [a
UAV] with a measured trend rather than an assumption." **That support is
withdrawn.** The measured trend, extended, points the other way: the strongest
vegetation–sulfate association in Ohio lives at ~1 km, not at the seep face. A
drone justification cannot be drawn from this evidence.

**Sign consistency still fails at every radius**, and at 500/1000 m the larger
pooled |rho| is carried by two watersheds (Huff Run −0.43, Raccoon −0.44) while
three go weakly positive (Leading +0.02, Monday +0.26, Sunday +0.13). A pooled
rho with inconsistent signs has never been a result in this project and is not
one here.

## 4. How T1 and T2 sit together

The pre-registration required that a disagreement be reported as a disagreement
rather than resolved by preference. In fact they are not contradictory:

- **T1** says something survives conditioning on *mapped mining extent*.
- **T2** says whatever that something is, it is **strongest at ~1 km**, not at
  the channel.

Both are satisfied by a **landscape-scale vegetation–sulfate relationship** that
mapped mine polygons capture only partially — unsurprising, since ODNR historic
coverage is explicitly incomplete ("from topo maps", "partially known") and cannot
represent unmapped disturbance, spoil, roads or reclamation. On that reading T1's
surviving −0.246 is **residual land cover the covariate missed**, not a seep.

**What T1 alone cannot do is rescue a near-channel claim, because T2 has no
over-control risk and points away from the channel.**

## 5. The over-control caveat — noted, and explicitly not used

The catchment covariate is near-collinear with sulfate inside some watersheds:
per-watershed `mine_frac` vs sulfate runs +0.50, +0.24, **+0.95**, +0.19, −0.06.
In Monday Creek the covariate explains nearly all the sulfate variance, leaving
almost no residual and making that watershed's partial unstable (raw +0.03 →
partial +0.74 on n=12). Sunday swings +0.39 the same way, also on n=12.

That is expected: **mining extent is the physical cause of the sulfate**, so
conditioning on it there removes the exposure itself. It is exactly the
over-control risk anticipated in pre-registration §6, which states that
over-control **may be noted but may not be used to keep a claim alive**. It is
noted here and used for nothing.

## 6. Sample caveats, all registered in advance

- **13 of 187 catchments clipped** the MERIT tile and were dropped from the
  primary arm. The drop is **not random** — it removes large mainstem stations
  (~1,100–1,250 km², Hocking River). The disc arms retain them, which is why they
  carry n=137 against the primary arm's 131.
- **Monday and Sunday Creek fall to n=12 each** in the sulfate subset. Their
  per-watershed partials are not estimates and should not be read as such.
- **n drifts 137 → 146 across the ladder** as larger buffers give more stations a
  valid pixel. The ladder is therefore not a perfectly fixed sample.
- **ODNR historic coverage is incomplete by construction**, which biases T0 and
  T1 *toward finding no confound*. The confound was found anyway.

## 7. What may and may not be said

**MAY**
- The mining-extent confound is **real and operative**: mine extent predicts
  sulfate (+0.519) and vegetation (−0.283), and carries ~42% of the raw
  covariance.
- A significant association survives conditioning on mapped mining extent
  (−0.246, p = 0.025), **below the registered bar**.
- **The Ohio vegetation–sulfate association is strongest at ~1 km and is
  therefore landscape-scale**, by CMD1's own pre-registered criterion.
- Conditioning on **surface** mining attenuates most; **underground**, least.

**MAY NOT**
- That the confound is **rejected** — it missed by 0.004.
- That we **detect CMD seeps**, or that the signal is near-channel. **T2 refutes
  the near-channel reading**, and the earlier geometry-gradient UAV argument is
  **withdrawn**.
- Any **optical sulfate** claim, ever. Sulfate has no VNIR absorption; this is
  vegetation that co-varies with it.
- That the 1 km/5 km disc sign consistency is a finding — it is a lead generated
  by the same data that would test it.

## 8. Method notes worth keeping

- **Covariate: ODNR `MinesOfOhio`** — coal layers only (surface 12/13/14/15,
  underground 19/20/22/23); proposed-but-unmined and industrial minerals
  excluded. **14,578 polygons** across five watersheds. Built from permit records
  and historical topo/geology maps, so it owes nothing to satellite reflectance.
  That mattered more here than for C3b: the signal under test is a *vegetation*
  index, and an NLCD-derived covariate would have shared the NDVI physics and
  quietly regressed the signal on itself.
- **Unit: upstream catchment**, MERIT Hydro D8 via the validated
  `catchment_dem.py`, one tile per *watershed* rather than per station (187
  downloads → 5). Delineation itself unchanged. 174/187 traced clean.
- **ArcGIS paging by `returnIdsOnly` + `objectIds` chunks**, never
  `resultOffset`: pagination support varies per layer and an unsupported
  `resultOffset` is **silently ignored**, which would have returned page 1
  forever and truncated the covariate without erroring.
- **Ring orientation honoured** when rasterising, so donut mines (works around an
  unmined pillar) are not double-counted.

### New, reusable fix for the recurring GEE memory trap

Sunday Creek died at the batch=2 floor on 1000 m buffers — its **third**
"User memory limit exceeded" failure. The known fix (cap scenes at 120) was
already in place and was not enough.

**The per-request compute graph is proportional to the BAND COUNT**, not only to
scene depth or batch size. Extracting only the band under test
(`--bands NDVI_stress`) completed Sunday with a single retry.

**Verified rather than assumed:** re-extracting Monday Creek at 500 m with one
band and comparing against the 8-band run gives **max absolute difference 0.000
across all 27 stations** — bit-for-bit identical. It is a request-size fix, not a
method change, so Sunday's T2 values are comparable with the others'.

## 9. Checks run before believing any of it

- `partial_spearman` cross-validated against the closed-form first-order partial
  correlation and `scipy.stats.spearmanr`: agreement to **0.0** on the real
  vectors, **5.6e-17** synthetic. The verdict turns on 0.004, so the estimator
  had to be exact rather than approximately right.
- **Baseline reproduction passed exactly:** the published 30 m analysis returns
  rho −0.354, n=137, p=0.0028.
- **Record fix found by that check.** `ARM_CMD1_GEOMETRY_2026-08-16.md` and
  `STATE.md` both cited **p = 0.0013** at 30 m. The raw output says **0.0028**,
  and 0.0028 reproduces. Transcription error, corrected in both. No verdict
  changes — both below 0.05 — but the record should be right.

## 10. Next

1. **Treat the Ohio association as landscape-scale and test it as such.** The
   honest remaining question is no longer "can we see seeps" but "does a
   catchment-scale vegetation metric carry information about CMD loading beyond
   mapped mine extent" — a different, weaker, and still useful claim.
2. **A better disturbance covariate.** ODNR historic coverage is incomplete, and
   T1's surviving −0.246 is most plausibly land cover it missed. Reclamation-era
   and spoil mapping would test that directly.
3. **The 1 km/5 km disc sign consistency, on data that did not generate it.** It
   is the only sign-consistent result the Ohio arm has produced and it is
   currently circular.
4. **More Ohio sulfate coverage.** Two of five watersheds run at n=12.

## Reproduce

```
python python/cmd_confound.py --mines
python python/cmd_confound.py --catchments --conf data/matched/cmdconf.csv
python python/cmd_detect.py --extract --season leafoff --radii 500,1000 \
    --regions <slug> --out data/matched/cmdfar_l8_<slug>.csv
# sunday_creek_oh needs the band subset to fit in the GEE memory budget:
python python/cmd_detect.py --extract --season leafoff --radii 500,1000 \
    --bands NDVI_stress --regions sunday_creek_oh \
    --out data/matched/cmdfar_l8_sunday_creek_oh.csv
python python/cmd_confound.py --analyse --conf data/matched/cmdconf.csv \
    --perms 5000 --ladder "<cmdgeo_l8_*.csv,cmdfar_l8_*.csv>" \
    --out validation/report_cmd2_confound_2026-09-08.txt
```
