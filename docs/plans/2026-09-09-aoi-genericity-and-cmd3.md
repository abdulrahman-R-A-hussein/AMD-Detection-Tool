# Point the tool anywhere — safely — and prove it on a new basin

## Context

You asked what you can test right now on an area of interest. The honest
answer is: **not much, and what you can test would mislead you.**

**Both surfaces are gated behind hardcoded registries.** The GEE tool only
accepts the 30 entries in `studyAreas` (`amd_detection_v2.4.0.js:34-76`); the
Python pipeline needs edits to up to **five** separate dicts that are kept in
sync by hand (`fetch_wqp.REGIONS`, `seep_detect.REGIONS`,
`cmd_detect.CMD_REGIONS`, `watershed_nap.KNOWN_REGIONS`, `gee_classify.SITES`).
`watershed_nap.py:426` admits the duplication in a comment.

**And three defects are confirmed in the GEE tool** — I read the lines:

1. **`useStdDevThresholds: true` (`:615`) while its checkbox renders
   `value: false` (`:2395`).** The tool boots in scene-relative mode while the
   UI says otherwise. First click is a silent no-op; the *second* click
   switches the whole classification to absolute thresholds.
2. **The σ sliders guarantee a configuration the project measured as useless.**
   Sliders are `{min:1.0, max:3.0, value:2.0}` and `1.5`; the calibrated
   settings are `0.5 / 0.5 / 0.25`. The slider *minimum* is already outside the
   calibrated range, so **any drag** produces what the file's own comment at
   `:612-614` records as *"worst-case J = 0.000 — they sit so far into the tail
   that almost nothing is flagged."* `clayStdMult` and `ferrousStdMult` have no
   control at all.
3. **`specificStartDate: '2024-01-01'` (`:516`) sits outside
   `START_DATE='2013-01-01'`/`END_DATE='2020-12-31'` (`:86-87`).** Switching the
   date filter on with defaults returns zero images.

Underneath all three is one scientific problem: **`applyStdDevThresholding`
(`:722-736`) reduces over `settings.currentRegion`, so the AOI extent *is* a
classification parameter.** The same pixel changes class depending on how big a
circle you draw. The calibration (worst-case leave-one-site-out Youden
J = 0.440 vs Rockwell's map) was fitted at **8–15 km** buffers — verified:
Summitville 8 km, Red Mountain Pass 10 km, Silverton 15 km
(`python/gee_classify.py:27-29`). Ganau ships at 1 km and Lake Naser at 100 km;
neither was ever calibrated.

Outcome: a free-form AOI on both surfaces, the three defects fixed, the
extent/threshold coupling broken honestly, a current operator guide, and one new
basin run end-to-end as a **pre-registered** out-of-sample test — which is also
`STATE.md` OPEN #0's "more coverage" item.

---

## Part 1 — GEE tool: point it anywhere, safely

Single file, `earth-engine/amd_detection_v2.4.0.js`. No build step, no tests, so
edits go in this order and each is verified before the next.

### 1.1 Dates (`:516-517`, `:2148-2189`)
Bind `specificStartDate`/`specificEndDate` to `START_DATE`/`END_DATE` (declared
at `:86-87`, before the `settings` literal, so the reference resolves). Add a
range guard to `applyDatesButton` that refuses a window lying entirely outside
the collection and says why. Remove `settings.useSpecificDate = true` from both
textbox `onChange` handlers — typing only a start date currently arms the filter
with a stale end date, the same desync family as defect 1. The buttons own the
flag.

### 1.2 Checkbox (`:2395`)
`value: false` → `value: settings.useStdDevThresholds`. GEE's `ui.Checkbox`
constructor does not fire `onChange`, so any state the handler sets must also be
set in the constructor. **Never hard-code a widget's initial value where a
`settings` field exists.**

### 1.3 σ multipliers (`:2405-2434`, `:2596-2629`, `:2708`)
Replace live-updating sliders with **staged edits behind an Apply button** — the
pattern `applyDatesButton` already uses. On the default path show a read-only
summary of the calibrated values and the J numbers behind them. Sliders move to
an "Advanced: override" reveal, range widened to `-1.0 … 3.0` so the calibrated
`0.5`/`0.25` *and* the negative per-fold clay fits are reachable. Add the two
missing controls (`clayStdMult`, `ferrousStdMult`). A drag stages a red
"PENDING — NOT CALIBRATED" warning and changes nothing on the map until Apply.
Add "Restore calibrated σ", and make `resetButton` restore σ too.

Compare against calibrated values with an epsilon, never `===` — slider steps
are floating point and `-1.0 + n*0.05` does not land exactly on `0.25`. A
false "NOT CALIBRATED" on the default config would destroy trust in the warning.

### 1.4 `studyAreas` → client-side specs (`:34-82`)
`ee.Geometry` cannot be read back client-side, so a preset currently cannot
prefill the AOI boxes, be checked against the calibration band, or name an
export by radius. Convert the 30 entries to `STUDY_AREA_SPECS` of
`[lon, lat, radius_m]` and derive `studyAreas` from it in a loop. Mechanical —
only the value expression changes; every coordinate, radius and trailing comment
survives. Downstream code sees the same `studyAreas` object.

### 1.5 Free-form AOI (after `:2215`, panel wiring after `:2686`)
**Lat/lon/radius textboxes**, parsed only on Apply, with strict validation
(reject `''`, `12km`, `1e9`, out-of-range, radius < 0.3 km where the scale-100
reducer has fewer than ~30 pixels). Plus a "Fill lat/lon from map centre" button
that writes **only** the centre and prints why it leaves the radius alone.

`regionSelect` gains a `-- Custom AOI --` sentinel. Flow is: preset → boxes
always; boxes → sentinel on Apply (`setValue(v, false)` suppresses the re-fire).
The two controls can never display different AOIs.

**Rejected — viewport as the AOI.** Viewport extent depends on browser window
size, and the σ threshold is computed over the AOI, so the classification would
depend on how wide your browser is. That is the coupling defect in its purest
form.

### 1.6 Break the extent/threshold coupling (`:443`, `:722-749`, `:1108`)
**Decouple the statistics region from the display region.** Add
`settings.statsRegion` — a fixed 12 km circle (mid-band) on the AOI centre —
used *only* by `applyStdDevThresholding` and `applyIndexClipping`.
`currentRegion` keeps its meaning everywhere else. Two operators typing the same
lat/lon get the same map regardless of display radius, and the geometry matches
what the LOSO fit was actually made on.

**The trap that makes a naive version silently fail:** `:1108` clips the
composite to `currentRegion`. If `statsRegion` is larger, `reduceRegion` sees
masked pixels and quietly computes over the *intersection* — appearing to work
while doing nothing. Fix: keep `currentComposite` clipped as today and add a
second `statsComposite` clipped to `statsRegion`; point `:443`'s `filterBounds`
at a `processRegion` covering both. **Zero changes to any of the eleven
`Map.addLayer` sites.**

**Rejected — absolute-threshold fallback outside the calibrated band.** It would
put an absolute cutoff on a non-normalised ratio index (against the project's
own rule) *and* silently switch to the worse measured mode (J 0.107 vs 0.440)
exactly when the operator is furthest from validated ground.

Add `reportStdDevThresholds()` printing mean / σ / k / resulting cut per index,
and an AOI status label stating the stats radius, the display radius, and
whether either is outside 8–15 km. Fix the stats panel's unconditional
`THRESHOLDS: Iron > 0.10` line, which is false in σ mode.

**This changes output for all 30 presets** (Ganau's σ was computed over 1 km).
That is a correction, not a regression — bump `TOOL_VERSION` to `v3.1.0`,
announce it at startup, and keep `statsRadiusMode: 'matchAOI'` to reproduce old
figures.

### 1.7 Export provenance (`:2983`, `:3008`, `:3067`, `:3144`)
All four exports build filenames via `replace(/[^a-zA-Z0-9]/g,'_')`, which
strips the minus from a custom AOI's longitude and loses the hemisphere. Add
`aoiSlug()` emitting `Custom_37p8120N_107p6650W_r12km`. Verified safe:
`derive_thresholds.py` does not parse filenames. Print full provenance
(sensor, dates, centre, both radii, σ mode and the four multipliers) on export,
since GEE export descriptions cannot carry it.

### Explicitly out of scope for this pass
Classes 6 and 10 unreachable (`:1038`/`:1042`); legend swatches disagreeing with
`classVis` (class 1 `A0522D` vs `8B7355`, class 5 `00FF00` vs `90EE90`); water
class 3 missing from the legend; the six dead settings flags; and the fact that
the stats panel, click inspector (`:1706-2006`) and accuracy masks
(`:1421-1436`) all use absolute thresholds unconditionally. All real, none
shares a verification path with this work. In a 3180-line file with no tests a
mixed diff is unreviewable. **They go in the guide as known quirks and into
`STATE.md` OPEN.**

---

## Part 2 — Python: acquisition without editing five dicts

### 2.1 Shared slug helper
One `region_slug(name)` in `fetch_wqp.py`, imported everywhere else. Removes the
hand-sync `watershed_nap.py:426` documents.

### 2.2 `--bbox` / `--name` on `fetch_wqp.py`
`REGIONS` (`:95`) is the only place a bounding box is ever defined; both
`seep_detect.region_geometry` (`:164`) and `cmd_detect.run_extract` resolve
through it. Add `--bbox "lat_lo,lon_lo,lat_hi,lon_hi"` + `--name`, writing an
entry to a **`data/regions.json` overlay** that `REGIONS` lookups consult after
the built-in dict. Keeps the 12 curated entries authoritative and their notes
intact, while new regions need no source edit.

### 2.3 Teach the consumers the overlay
`seep_detect.REGIONS`, `cmd_detect.CMD_REGIONS`, `watershed_nap.KNOWN_REGIONS`
fall back to the overlay when a slug is absent. The extraction functions already
take arbitrary geometries — only the registry lookups are gated.

### 2.4 What stays region-locked, and must be said
- **Rockwell's raster is US-Southwest only** — `compare_rockwell`, `pool_labels`,
  `iron_index_transfer`, `iron_criterion_search`, `paper_faithful_test` and
  `watershed_nap`'s Rockwell arm are unavailable elsewhere.
- **ODNR MinesOfOhio (`cmd_confound.py:56`) is Ohio-only.** CMD2's confound test
  cannot run on another state without a new non-satellite-derived mine source.
  **This directly bounds Part 4** — see below.
- **WQP is US-only**, so the Python arm cannot follow the GEE tool abroad.

---

## Part 3 — Operator guide

`docs/OPERATOR_GUIDE.md`. The existing `earth-engine/USAGE_GUIDE.md`,
`LAYER_STRUCTURE.md` and `FINAL_LOGIC_VERIFICATION.md` are dated Nov 2025 and
describe v2.x behaviour that no longer matches the code — mark them superseded.

Contents:
- **Point it at an area** — both surfaces, with the calibration-band caveat.
- **Every layer, and how to read it.** All 15 `Map.addLayer` calls: the 19-class
  land raster, the 4-state water raster, the 0–9 score, the diagnostics, the RGB
  references. For each: what it shows and what it does *not* mean.
- **The class table** — the 6 AMD classes (9/12/14/17/18/19), the cascade's
  first-match-wins order (which is *not* numeric order), and the NAP ranks
  `14=1, 12=2, 17=3, 18=4, 9=5, 19=6`.
- **Water class 3 (grey) = INDETERMINATE, never "clean."** Pooling it with class
  0 is the single easiest way to manufacture a false negative.
- **What you may and may not conclude** — lifted verbatim from
  `DECISION_LOG.md`. Especially: no optical sulfate claim ever; Rockwell
  agreement is replica fidelity, not accuracy; blind search is untested; the
  Ohio signal is landscape-scale, not near-channel.
- **Known quirks** — the Part 1 out-of-scope list, so nobody rediscovers them.
- **Two-venv table** and the memory-trap three levers (scene cap, batch, and
  band count — band count being the only one verified to leave numbers
  unchanged, max abs diff 0.000 over 27 stations).

---

## Part 4 — Worked example: West Branch Susquehanna, PA (pre-registered)

Only possible *because* of Part 2 — it is the demonstration.

### 4.1 Register before fetching
`validation/CMD3_PREREGISTRATION_<date>.md`, committed **before any PA data is
downloaded**, stating:

- **H-landscape (from CMD2):** if the Ohio vegetation–sulfate association is
  catchment-scale land cover, an independent coal basin should reproduce
  **(a)** a negative `NDVI_stress`–sulfate rho, and **(b)** |rho| *rising* from
  100 m to 1000 m.
- **Falsifier:** |rho| peaking at 30 m, or a positive pooled rho, means the
  landscape-scale reading does not replicate.
- **Headline check is sign consistency across PA sub-basins**, as in CMD2 — a
  pooled rho with inconsistent signs is not a result in this project.
- Bars, radii (30/60/100/500/1000 m), leaf-off season, permutation count and
  minimum n fixed in advance.
- **Stated up front: the CMD2 confound test cannot be repeated here** — ODNR is
  Ohio-only. So a PA result is *unconditioned*, and can corroborate the radius
  signature but **cannot** re-test the mining-extent confound. Recorded as a
  limitation before seeing any number, not after.

### 4.2 Run
```
fetch_wqp.py --bbox ... --name "West Branch Susquehanna, PA"
cmd_detect.py --extract --season leafoff --radii 30,60,100,500,1000
cmd_detect.py --analyse
```
Use `--bands NDVI_stress` from the start — the memory trap's third lever, and
the only one verified not to change the numbers.

### 4.3 Report honestly
A null or a failure to replicate is written up as prominently as a positive,
per the project's own rule. Either outcome is a real result: replication
strengthens CMD2's landscape reading; failure bounds it to Ohio.

---

## Logging rule (`CLAUDE.md`) — non-negotiable

Before the session ends: dated report in `validation/` with numbers, n and
caveat; `STATE.md` updated (proven / retracted / open / next); a
`DECISION_LOG.md` row; this plan mirrored to `docs/plans/`; commit **and push**.

> Push needs your credentials — Git Credential Manager wants an interactive
> dialog this session cannot drive. `v3.9.0` is still unpushed:
> ```bash
> git push origin main --follow-tags
> ```

---

## Verification

**GEE (in the Code Editor, after each step):**
1. Defaults load with images. Apply `2024-01-01`/`2024-12-31` → refused with a
   reason, map unchanged. Apply `2015-06-01`/`2015-08-31` → images.
2. On load the Adaptive checkbox reads **checked**; one click turns it off and
   the map visibly changes (previously the first click was a no-op).
3. Advanced reveals four sliders at 0.50/0.25/0.50/0.50 all marked
   `(calibrated)`. Drag iron to 2.0 → red warning, **map unchanged**. Apply →
   map changes, console says UNCALIBRATED. Restore → original map back.
4. All 30 presets centre and classify; spot-check Ganau (1 km), Silverton
   (15 km), Lake Naser (100 km).
5. Selecting a preset updates the three boxes; typing Silverton by hand
   (`37.812 / -107.665 / 15`) flips the dropdown to Custom and reports "inside
   the 8–15 km band". Garbage input is rejected with no update.
6. **The key regression test.** With `statsRadiusMode:'matchAOI'`, run one
   centre at r = 8, 12, 20 km and record the printed `IronSulfate` cut — it
   should **move**. That is the defect, confirmed live.
7. Switch to `'fixed'` and repeat: the cut must be **identical** at all three
   radii. If not, `statsComposite` is being truncated — check the `:1108` split
   and that `:443` uses `processRegion`. Then confirm the map still stops at the
   AOI edge, proving `currentComposite` was untouched.

**Python:**
8. `fetch_wqp.py --bbox` on an existing region reproduces its current
   `stations.csv` row count — proves the overlay path matches the built-in dict.
9. `cmd_detect.py --analyse` on the five Ohio slugs still returns
   **rho −0.354, n = 137, p = 0.0028** at 30 m — the committed baseline. Any
   drift means the refactor changed behaviour.
10. `catchment_dem.py --self-test` still passes 6/6 within ±33%.

---

## Outcome (filled in after execution, 2026-09-09)

**Parts 1–3 delivered.** GEE `v3.1.0` free-form AOI, all three defects fixed,
the AOI/threshold coupling broken (σ statistics on a fixed 12 km circle),
`--bbox` overlay on the Python side, and `docs/OPERATOR_GUIDE.md`.

**Verification all green:** CMD1 baseline reproduces exactly (rho −0.354,
n=137, p=0.0028), `catchment_dem --self-test` 6/6, all modules import clean.

**Part 4 — CMD3 ran and FAILED TO REPLICATE**, on the falsifier named in the
registration: |rho| peaks at 30 m and dies at landscape scale.

| radius | 30 m | 60 m | 100 m | 500 m | 1000 m |
|---|---|---|---|---|---|
| vs sulfate | −0.143 | −0.135 | −0.114 | −0.010 | −0.050 |
| vs conductance | −0.187 | −0.158 | −0.138 | −0.010 | **+0.003** |

PA is **monotone declining** — the opposite of Ohio's U-rising-to-1 km. The
**sign** replicates and is sign-consistent across three disjoint tiles
(the CMD arm's first); the **scale** does not. CMD2 is **bounded to Ohio**, and
**radius shape fails as a mechanism diagnostic** — it returns opposite
mechanisms for the same drainage type.

**Two unplanned findings:**
- The memory trap has a **fourth lever** (batch floor 2 → 1, measured at
  1.11e-16 — float epsilon, *not* bit-identical like the band subset), and
  **only two of the four levers are safe**: scene depth and scale change the
  composite, not just the request.
- My own **verdict table had non-exclusive rows**. Logged as correction #8.
