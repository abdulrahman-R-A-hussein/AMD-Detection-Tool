# CMD3 pre-registration — does the Ohio landscape-scale reading replicate in Pennsylvania?

**Written 2026-09-09. Committed BEFORE any Pennsylvania chemistry was
downloaded and before any index was extracted.** That is the point of this
file; if it is not in the commit history ahead of the data, it is worthless.

## 1. Why this test exists

CMD2 (2026-09-08) refuted CMD1's near-channel reading. Extending the radius
ladder past 100 m showed it is **U-shaped**, strongest at the largest footprint:

| radius | 30 m | 60 m | 100 m | 500 m | 1000 m |
|---|---|---|---|---|---|
| rho | −0.354 | −0.253 | −0.255 | −0.393 | **−0.438** |

CMD1 amendment 2 had registered the reading of exactly that pattern in advance:
*|rho| rising as radius grows ⇒ catchment-scale land cover, not the seep.*

**That conclusion currently rests on one basin.** It was also derived from the
same five Ohio watersheds that generated it. An independent coal basin is the
obvious test, and `STATE.md` OPEN #0 asks for exactly this.

## 2. Hypothesis and prediction, fixed now

**H-landscape** — the `NDVI_stress`–sulfate association in coal watersheds is
catchment-scale land cover.

If H-landscape holds, an independent bituminous coal basin must reproduce:

- **(a)** a **negative** pooled `NDVI_stress`–sulfate rho, and
- **(b)** **|rho| rising with radius**: `|rho(1000 m)| > |rho(100 m)|`.

**Falsifiers, stated before the data:**

- |rho| **peaking at 30 m** — the near-channel signature CMD2 refuted in Ohio.
- A **positive** pooled rho.

Either means the landscape-scale reading does not replicate and is bounded to
Ohio. That is a real and reportable result.

## 3. Verdict rule

| outcome | verdict |
|---|---|
| (a) **and** (b) | **REPLICATES** — H-landscape holds out of basin |
| (a) or (b), not both | **PARTIAL** — reported as partial, not as support |
| neither, or |rho| peaks at 30 m | **FAILS TO REPLICATE** — bounded to Ohio |

**The headline check is sign consistency across sub-basins, as in CMD2.** A
pooled rho with inconsistent signs is not a result in this project and will not
be reported as one, whatever the verdict row says.

## 4. Design, fixed now

- **Region:** upper West Branch Susquehanna, PA — bituminous coal drainage, the
  closest available analogue to the Ohio watersheds.
- **Grouping unit: three spatially DISJOINT tiles**, fixed below. They tile
  without overlap, so no station is double-counted. They are named for the
  dominant AMD stream in each, but the stream-to-tile correspondence is **not
  load-bearing** — what matters is that they are disjoint sub-regions of one
  coal basin, chosen before any chemistry was seen.

  | tile | lat_lo | lon_lo | lat_hi | lon_hi |
  |---|---|---|---|---|
  | Chest Creek, PA | 40.55 | −78.85 | 40.95 | −78.63 |
  | Clearfield Creek, PA | 40.50 | −78.62 | 41.05 | −78.32 |
  | Moshannon Creek, PA | 40.78 | −78.32 | 41.18 | −77.95 |

- **Index:** `NDVI_stress` is the **primary**. The full 8-index panel is
  reported, BH-corrected across it.
- **Analyte:** `Sulfate_mgL` primary; specific conductance secondary.
- **Radii:** 30, 60, 100, 500, 1000 m — the same ladder as CMD2, so the shapes
  are directly comparable.
- **Season:** leaf-off. Non-negotiable — CMD1 showed leaf-on Ohio was
  canopy-limited (NDVI 0.870) and therefore uninterpretable.
- **Permutations:** 5000, shuffled **within tile**.
- **Minimum n:** a tile with **fewer than 8** sulfate-matched stations is
  reported but **excluded from the sign-consistency headline**. CMD2 ran two
  Ohio watersheds at n=12 and flagged them; this fixes the bar in advance
  rather than after seeing which tiles are thin.
- **Canopy gate:** the existing `CANOPY_NDVI_LIMIT = 0.6` applies. If median
  buffer `NDVI_stress` exceeds it, the verdict is **UNINTERPRETABLE —
  canopy-limited**, *not* a null. Pennsylvania is forested; this is a live
  possibility and is registered as such now.
- **Extraction:** `--bands NDVI_stress` for the memory-limited passes. Verified
  identical to full-panel extraction (max abs difference **0.000** over 27
  stations), so it is a request-size fix, not a method change.

## 5. The limitation that cannot be fixed here — registered up front

**The CMD2 mining-extent confound test CANNOT be repeated in Pennsylvania.**

The covariate was ODNR `MinesOfOhio` — 14,578 coal polygons from permit records
and historic topo/geology maps, chosen precisely because it owes **nothing** to
satellite reflectance. It is Ohio-only. NLCD is explicitly rejected as a
substitute: it shares the NDVI physics and would regress the vegetation signal
partly on itself.

So a Pennsylvania result is **unconditioned**. It can corroborate or refute the
**radius signature**; it **cannot** re-test the confound, and it cannot move
CMD2's PARTIAL verdict in either direction.

This is recorded now, before any number exists, so it cannot later be presented
as a caveat discovered conveniently after the fact.

## 6. What a positive would and would not license

**Would:** that the landscape-scale vegetation–sulfate association is not an
Ohio peculiarity.

**Would NOT**, under any outcome:
- any **optical sulfate** claim — sulfate has no VNIR absorption, ever;
- any **seep detection** or near-channel claim;
- any revival of the withdrawn UAV argument;
- any claim that the mining-extent confound is cleared anywhere.

## 7. Commands to be run (recorded before running them)

```
python python/fetch_wqp.py --region "Chest Creek, PA"      --bbox "40.55,-78.85,40.95,-78.63"
python python/fetch_wqp.py --region "Clearfield Creek, PA" --bbox "40.50,-78.62,41.05,-78.32"
python python/fetch_wqp.py --region "Moshannon Creek, PA"  --bbox "40.78,-78.32,41.18,-77.95"

python python/cmd_detect.py --extract --season leafoff --radii 30,60,100 \
    --bands NDVI_stress --regions <slugs> --out data/matched/cmd3geo_l8_<slug>.csv
python python/cmd_detect.py --extract --season leafoff --radii 500,1000 \
    --bands NDVI_stress --regions <slugs> --out data/matched/cmd3far_l8_<slug>.csv
python python/cmd_detect.py --analyse --inputs <all of the above>
```

**A station-count probe before extraction is permitted and is not a peek at the
outcome** — it reads how many stations carry sulfate, never the relationship
between sulfate and any index. The project's own `REGIONS` notes record such
probes. If a tile has too few stations it is dropped under the §4 rule, which
was fixed before the probe.

## 8. Reporting commitment

A **failure to replicate is written up as prominently as a replication**, per
this project's standing rule that a null or a collapse is a valid, publishable
result. Both outcomes are useful: replication strengthens CMD2's landscape
reading; failure bounds it to Ohio and says so.
