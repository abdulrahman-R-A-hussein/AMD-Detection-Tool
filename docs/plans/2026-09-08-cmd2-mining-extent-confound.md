# Plan — CMD2, the mining-extent confound test (2026-09-08)

Mirror of the machine-local session plan, per the logging rule in `CLAUDE.md`.
Repo copy is authoritative on conflict.

**Registered:** [`../../validation/CMD2_PREREGISTRATION_2026-09-08.md`](../../validation/CMD2_PREREGISTRATION_2026-09-08.md),
committed `a452446` before any mine polygon was joined to any chemistry value.

## Why this was the next thing

`ARM_CMD1_GEOMETRY_2026-08-16.md` ended with the confound named explicitly as
the gate on its own finding: high-sulfate stations may simply drain more heavily
mined ground with less vegetation overall. Until tested, the claim could only be
*"a vegetation index tracks sulfate"*, never *"we detect CMD seeps."* It was
open item #1 in both `STATE.md` and the report.

## Environment problem hit first

Both virtualenvs were dead: `pyvenv.cfg` in each pointed `home` at
`C:\Users\ahusse12\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none`,
a path belonging to a user profile that no longer exists after the machine
reinstall. `site-packages` was intact in both (301 packages, cp311 wheels) — only
the base interpreter was missing.

**Fix:** installed `uv` per-user, `uv python install 3.11` (3.11.16, matching the
cp311 ABI of the installed wheels), then repointed `home`/`executable` in both
`pyvenv.cfg` files. Backups left as `pyvenv.cfg.bak-20260908`.

Two wrinkles worth recording:
- uv's minor-version junction (`cpython-3.11-...` → `cpython-3.11.16-...`) does
  not execute reliably on this machine. The venvs are pointed at the **versioned**
  directory instead, bypassing the junction.
- `git` refused the repo for "dubious ownership" (the reinstall changed the
  owning SID). Fixed with `safe.directory`.

## Method

**Covariate — ODNR `MinesOfOhio`** (`MRM_Services/MinesOfOhio/MapServer`), coal
layers only: surface 12/13/14/15, underground 19/20/22/23. Proposed-but-unmined
(11/17/18) and industrial minerals (25–34) excluded. Built from permit records
and historical topo/geology maps, so it owes nothing to satellite reflectance —
which is the point, because the signal under test is a *vegetation* index and an
NLCD covariate would share the NDVI physics.

Paged by `returnIdsOnly` + `objectIds` chunks rather than `resultOffset`:
pagination support varies per layer and an unsupported `resultOffset` is
silently **ignored** rather than erroring, which would return page 1 forever and
quietly truncate the covariate.

**Spatial unit — upstream catchment**, MERIT Hydro D8 via the already-validated
`catchment_dem.py`. One MERIT tile per *watershed* rather than per station (the
stations in a watershed share a grid), which turns 187 downloads into 5.
Delineation itself is unchanged. Clipped catchments are dropped and counted.

Mine polygons are rasterised onto the MERIT grid (`rasterio.features.rasterize`),
honouring ArcGIS ring orientation so donut mines are not double-counted, and the
covariate is the area-weighted mined fraction of the traced catchment.

**Statistic —** partial Spearman on ranks (residualise rank(x) and rank(y) on
rank(z)), with a within-region permutation null shuffling sulfate *within*
watershed while the covariate stays attached to the station.

## Tests

- **T0 (guard, reported first).** Does mine extent predict sulfate at all? If
  not, the confound is structurally impossible and T1 is *uninformative*, not
  supportive.
- **T1 (primary).** Partial Spearman `NDVI_stress` vs sulfate | catchment mined
  fraction, at the 30 m radius. Robustness: surface-only, underground-only, and
  fixed 1 km / 5 km discs.
- **T2 (secondary).** Extend the radius ladder to 500 m and 1000 m through
  `cmd_detect.py` unchanged — tests the same confound with different machinery
  and no over-control risk.

## Checks run before believing anything

- `partial_spearman` cross-validated against the closed-form first-order partial
  correlation and against `scipy.stats.spearmanr` — agreement to 0.0 / 5.6e-17.
- Baseline reproduction: re-ran the published 30 m analysis and got
  rho −0.354, n=137, p=0.0028 exactly.
- **Record fix found by that check:** `ARM_CMD1_GEOMETRY_2026-08-16.md` and
  `STATE.md` both cite p = 0.0013 at 30 m. The raw output says **0.0028**, and
  0.0028 reproduces. Transcription error; corrected in both. No verdict changes.

## Decision rule (fixed before any number)

| outcome | verdict |
|---|---|
| partial \|rho\| ≥ 0.25, same sign, p < 0.05 | CONFOUND REJECTED |
| partial \|rho\| < 0.15 or p ≥ 0.05 | CONFOUND SUPPORTED — claim withdrawn |
| in between, or attenuation > 40% with p < 0.05 | PARTIAL — claim weakened |

The asymmetry between the two failure modes (real confound vs over-control) was
written into the pre-registration §6 in advance, precisely so a collapse could
not be explained away as over-control after the fact.

## Outcome (filled in after the run)

- **T0:** confound is **real** — mine extent → sulfate **+0.519**, mine extent →
  `NDVI_stress` **−0.283**. Guard passes, so T1 is informative.
- **T1:** partial rho **−0.246**, n=131, p=0.0254 → **PARTIAL, by 0.004** against
  the registered 0.25 bar. Not moved.
- **T2:** the decisive one. The ladder is **U-shaped** —
  −0.354 / −0.253 / −0.255 / **−0.393** / **−0.438** at 30/60/100/500/1000 m.
  |rho| *rises* with radius past 100 m, which is CMD1 amendment 2's
  pre-registered signature of **catchment-scale land cover, not the seep**.
  **CMD1's near-channel reading is refuted, and the UAV argument drawn from its
  geometry gradient is withdrawn.**

**Unplanned finding, now in KNOWN TRAPS:** the GEE memory trap has a **third
lever — band count**. Sunday Creek failed its third time at the batch=2 floor
with the 120-scene cap already applied; extracting only the band under test
completed it. Verified identical (max abs diff **0.000** over 27 stations,
one-band vs eight-band), so it is a request-size fix, not a method change.

## Reproduce

```
python python/cmd_confound.py --mines
python python/cmd_confound.py --catchments --conf data/matched/cmdconf.csv
python python/cmd_detect.py --extract --season leafoff --radii 500,1000 \
    --regions <slug> --out data/matched/cmdfar_l8_<slug>.csv
python python/cmd_confound.py --analyse --conf data/matched/cmdconf.csv --perms 5000
```
