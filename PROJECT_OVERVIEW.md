# Project Overview — AMD/CMD Detection System

> **Rewritten 2026-09-13.** The April 2026 version of this file described a
> validated in-water contamination-detection capability. **That capability was
> retracted** — see the notice in [`README.md`](README.md) and the full record
> in [`validation/STATE.md`](validation/STATE.md). Nothing in the old text
> should be reused.

## What this is

Rockwell & Gnesda (2021, USGS SIM 3466) published a method for automated
iron-sulfate mineral mapping from Landsat 8, plus a result raster — but no
code. This repository:

1. **reimplements that method** in Google Earth Engine and Python, verified
   formula-by-formula against the published pamphlet; and
2. **measures what it can and cannot do**, against real field chemistry, under
   criteria fixed in writing before each test ran.

Author: **Abdulrahman Hussein**, Kent State University, Dr. Joseph D. Ortiz
laboratory. Purpose: preliminary data and methodology for a PhD grant
application.

## The honest summary

**Established:**

- The land replica is faithful at the index level — all six formulas reproduce
  exactly. Three departures this project had introduced as improvements were
  measured as regressions; correcting them took worst-case leave-one-site-out
  Youden J from **0.107 to 0.440** against the published map. *Agreement with
  that map is replica fidelity, not accuracy.*
- **Severity ranking works within a mineral district.** `FerricIron1` tracks
  measured dissolved iron at **rho +0.568** (n=75, within-region permutation
  p=0.0004), sign-consistent across four Colorado districts — but
  leave-one-region-out R² is negative for every index × analyte pair, so it
  **ranks within a district and does not predict across districts**.
- **Catchment delineation is externally validated**: 6/6 within ±33% of
  published USGS drainage areas, where the earlier HydroSHEDS approach managed
  2/6.

**Measured nulls — stated as nulls:**

- **Detection is a null.** At 86 chemically confirmed mine-discharge points,
  all nine candidate indices fail all three control tiers. The best case
  reaches **J 0.234** against a pre-registered bar of **0.25**.
- **The Ohio water column is a null.** No feature's 95% CI excludes zero for
  iron or sulfate. Turbidity, by contrast, is cleanly detected — the water arm
  sees sediment, not iron.
- **Spatial resolution is not the binding constraint** anywhere in 10–100 m,
  for either detection or severity. The earlier Landsat→Sentinel-2 improvement
  was a **sensor** effect, not a pixel-size effect.

**The gap that defines the remaining work:** the difference between *scoring
known points correctly* and *finding unknown sites* — a severity tool versus a
discovery tool. This project owns the first. The second is untested.

## What may not be claimed

- Finding unknown sources in blind scene-wide search.
- Optical **sulfate** detection at any concentration — sulfate has no VNIR
  absorption, so this is never available.
- That the method transfers to forested neutral-pH coal drainage — measured
  null.
- That agreement with Rockwell's map means accuracy.
- Any cost-saving percentage. The previously published 70–90% figure had no
  supporting analysis and is withdrawn.

## Repository structure

```
validation/          the log — dated reports, pre-registrations, STATE.md
  STATE.md           canonical current state: proven / retracted / open / next
  ACCURACY_ASSESSMENT.md   every performance number, with n and reference
  DECISION_LOG.md    the chronological journey, wrong turns included
python/              analysis pipeline
  cmd_detect.py      coal-drainage dose-response
  seep_detect.py     detection statistics library (AUC, Youden J, LORO, permutation)
  cmd_confound.py    confound testing with partial correlations
  catchment_dem.py   MERIT Hydro D8 delineation (validated 6/6)
  fetch_wqp.py       Water Quality Portal acquisition
  gee_classify.py    server-side replica of the GEE classifier
earth-engine/
  amd_detection_v2.4.0.js   the interactive tool (contents are v3.1.0)
docs/
  OPERATOR_GUIDE.md  how to run it and how to read the output
  plans/, memory/    mirrors of otherwise machine-local artefacts
data/                gitignored; regenerable from committed code
paper.pdf            the full 47-page USGS SIM 3466 pamphlet
paper2.pdf           Galaszkiewicz et al. 2024 — tested here, failed
```

## Method discipline

Four claims have been retracted after failing a test this project ran on
itself. The rules that caught them:

- Judge thresholds by **worst-case leave-one-region-out**, never pooled and
  never within-site.
- **Never** put an absolute cutoff on a non-normalised index.
- Report the **between/within variance split** beside any pooled correlation.
- **Never** test a hypothesis on the data that generated it.
- **A null is a result**, reported as prominently as a positive would be.

Each phase is pre-registered before its data exists, and the registration
commit is verifiable in git history.

## Where to start

1. [`validation/STATE.md`](validation/STATE.md) — current state
2. [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) — running it, reading it
3. [`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md) — the numbers
