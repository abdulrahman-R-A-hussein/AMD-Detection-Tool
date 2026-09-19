# SpectraLab AMD module — first full UI run, 2026-09-19

**The gate item from `AMDTOOL_REFACTOR_GATE_2026-09-14.md` is now closed.** The
AMD severity report was driven end to end through the SpectraLab interface, not
through a test harness, on an AOI spanning two mineral districts.

> **The run's own numbers are EXPLORATORY.** Its AOI, grouping and settings were
> chosen interactively, so its p-values describe that run only. Nothing here
> enters a claim. What this document records is that **the software works**, and
> one defect it exposed.

---

## What was run

| | |
|---|---|
| Interface | `scripts/run_ui.py` from branch `feature/amd-severity-module`, at localhost:8080 |
| Module | AMD severity report: index vs water chemistry |
| AOI | lat 37.70–38.20, lon −107.90 to −107.50 — **1,950 km², Silverton + Ouray** |
| Settings | drainage type `metal_mine`, sensor L8, 2 × 2 outcome-blind grid, defaults elsewhere |
| Credentials | `GEE_SERVICE_ACCOUNT_JSON` |
| Run id | `20260919T220551Z-5990a7` |
| Duration | **1 min 15 s** |
| Status | **completed with warnings** |

**Stages:** water chemistry 22 s → composite and station buffers 31 s →
dose-response 0.9 s → score raster **failed** → report 0.0 s.

**Produced:** `amd_report.md`, `amd_stations_extracted.csv`,
`amd_dose_response.csv`, and the Water Quality Portal download under
`amd/chemistry/`. **39 stations** extracted from a **134-scene** composite.

## What the report said (exploratory, not evidence)

Verdict **SUCCESS**, on the module's stated rule.

| index | analyte | rho | n | perm p | BH q | between-tile % | signs |
|---|---|---|---|---|---|---|---|
| `FerricIron1` | Iron, dissolved | **+0.527** | 32 | 0.0070 | 0.0132 | 16 | consistent |
| `FerricIron1` | Iron, any fraction | +0.458 | 39 | 0.0088 | 0.0132 | 18 | disagree |
| `FerricIron1` | pH | −0.142 | 38 | 0.6019 | 0.6019 | 38 | disagree |

Tiles holding fewer than 8 stations were dropped from the sign check, and the
report said so in three warnings. The report carried the EXPLORATORY banner, the
preset's validation history (including Leadville's +0.004), and the full claim
boundaries — **including the blind-search MAY-NOT line**, so the 2026-09-15
result reaches the product a user reads.

## The defect this exposed

**The score raster was lost:**

```
Warning: Score raster not exported: Earth Engine download failed: 400
  "User memory limit exceeded."
```

`amdtool.raster.export_geotiff` already coarsened its scale for the **32 MB
request cap**, and `export_png` already halved its dimensions on a **memory**
error — but `export_geotiff` had no memory-error path at all. Earth Engine's
memory limit is about computing the composite behind the file, not the file's
size, so a request well inside the size cap still failed: 1,950 km² over 134
Landsat scenes at 30 m.

The statistics were unaffected. They are computed per station buffer, and they
had already finished. **The loss was display only** — but silent to anyone who
does not read the warning, which is how the 0-byte PNG slipped through on
2026-09-15.

## The fix, and how it was verified

`export_geotiff` now doubles its scale and retries on a memory error, up to
`MAX_GEOTIFF_SCALE_FACTOR = 16` times the scale first requested. The scale used
is returned and reported, because **a coarsened raster is a display product and
no statistic is computed from it**.

**Live check, on the AOI that failed** (scratchpad script, `ee_auth` credentials):

```
scenes: 134
starting scale: 30.0
      raster memory limit - retrying at 60 m
      raster memory limit - retrying at 120 m
RESULT: scale_m 120.0, 1,292,591 bytes, 24 s
```

**Offline:** two new tests pin the behaviour — one that the scale doubles once
and the file is written, one that it gives up at the ceiling and leaves **no
file**. Suite: **212 passed**.

## Caveats

- **The run's statistics are exploratory** and are quoted here only as evidence
  the pipeline runs. A two-district AOI was chosen because one district usually
  has too few stations; that choice was made before the run, but the grouping
  was not pre-registered.
- **The live verification used a scratchpad script**, not the UI, because the
  defect lives in `amdtool`. The UI run itself is what proved the module.
- **Not re-run through the UI after the fix.** The next UI run is expected to
  write `amd_score.tif` at a coarsened scale; if it does not, that is a new
  finding.
- The three "fewer than 8 stations" warnings are the module behaving as
  designed, not a fault.
