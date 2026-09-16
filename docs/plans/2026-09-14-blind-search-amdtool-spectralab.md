# Blind-search test, an importable library, and an AMD module for SpectraLab

## Context

You asked two things: **what test comes next**, and **what app and Earth Engine
surface you can test the framework through**, designed to be added to your main
application, **SpectraLab (VPCA + stepwise regression)** at
`D:\dev\VPCA+STEPWISE-REGRESSION`.

**Your decisions:** library + thin module · first module = verified severity
report · next test = blind search · SpectraLab = feature branch, no release.

**What exploration established (verified, not assumed):**

- **SpectraLab 0.39.0** is a NiceGUI local web app with a per-run worker
  process, a PyInstaller exe, and a clean `AnalysisModule` protocol
  (`id, settings_schema, validate, plan, run → RunResult`) registered by hand in
  `src/spectralab/modules/registry.py`. `StepwiseModule` (117 lines) is the
  template: pure orchestration over an existing science function, with an
  offline test producing real files. The worker calls SpectraLab's own
  `ee_init(spec)` before `module.run` when `needs_ee` is declared.
- **Sulfate-Methos is not embeddable.** No package; `sys.path` hacks in 9
  places; library-looking functions `print`, raise `SystemExit`
  (`cmd_detect.cmd_region_name`) or `sys.exit` (`vpca_validation.load_scene`),
  call `init_ee()` themselves, and write to `__file__`-relative `data/` paths.
  Every `run_*` returns `None`; verdicts exist only as printed text. Four
  incompatible bounding-box conventions.
- **SpectraLab cannot consume this project's outputs today.** Its VPCA is
  Sentinel-2-only by design, works on imagery not pixel tables, and refuses
  Landsat in a test. So integration is a new module, not a data hand-off.
- **Three defects confirmed by direct check:**
  1. `vpca_validation.convolve_splib07` calls `np.trapz` — removed in the
     NumPy 2.4.6 both environments run. It crashes.
  2. **Arm A has the AOI-extent defect** already fixed in the Earth Engine
     tool: `watershed_nap.classify_catchment_ours` calls
     `classify_v3(ee, comp, region)` with the catchment as `region`, so σ
     thresholds depend on catchment size.
  3. **Arm A's "31 catchments" are 28 distinct polygons.** Three `basin_id`s
     are counted under two regions — `7121080490` (Alma, Leadville),
     `7121092570` (Ouray, Silverton), `7120588780` (Lake City, Ouray) — so
     identical loadings sit on both sides of leave-one-region-out splits.

**Outcome:** a pre-registered measurement of whether the tool finds sites it was
not told about; a `amdtool` package with a clean API; and a SpectraLab
"AMD severity report" module you can run from its UI.

---

## What you will be able to test when this round is done

| surface | how | what it gives |
|---|---|---|
| **Earth Engine tool** | Code Editor, unchanged | interactive map anywhere on Earth |
| **`amdtool` library + CLIs** | `pip install -e .` in Sulfate-Methos; every existing `python/*.py` command still works | the validated pipeline, now importable |
| **SpectraLab → "AMD severity report"** | `uv run python scripts/run_ui.py` on the feature branch → New Run | draw an AOI, pick a preset, get a claim-bounded report, CSVs and a score raster |

---

## Order of work

1. **Part D** — log the confirmed defects (small). **Part B1** — commit the
   blind-search pre-registration **before any landscape data exists**.
2. **Part A** — build `amdtool`, gated on reproducing every committed baseline.
3. **Part B2** — run the blind search (Earth Engine, hours). **Part C** is built
   in parallel — its first module does not depend on B's outcome.
4. Log, commit, push after each part.

---

## Part A — `amdtool`: an importable library

### A1. Layout (src layout, matching SpectraLab)

```
Sulfate-Methos/pyproject.toml            name "amdtool", hatchling, requires-python >=3.10
Sulfate-Methos/src/amdtool/
  errors.py        AmdToolError, UnknownRegionError, CredentialsError
  geometry.py      BBox(lat_lo, lon_lo, lat_hi, lon_hi) — ONE convention; to_ee(), from_*()
  regions.py       region_slug, curated REGIONS, overlay load/save, all_regions   ← fetch_wqp
  chemistry.py     fetch_region, write_stations, consolidate, site_category,
                   normalize_iron_value ← fetch_wqp; load_station_chemistry ← watershed_nap
  stats.py         ONE implementation each: auc, best_threshold, j_at, loro_worst_j,
                   perm_p_within_region, benjamini_hochberg, variance_split, spearman
                   ← seep_detect; partial_spearman, perm_p_within ← cmd_confound;
                   exact binomial, exact McNemar, Wilson
  imagery.py       l8_composite, l8_composite_season, s2_composite, index_image,
                   extract_buffers, random_landscape_points   ← seep_detect / cmd_detect
  dose_response.py analyse(...) -> DoseResponseResult  ← logic now inline in cmd_detect.run_analyse
  blind_search.py  Part B
  raster.py        tiled GeoTIFF/PNG export of one index over a BBox ← catchment_dem._fetch_band pattern
  claims.py        MAY / MAY NOT and verdict wording, as data
  auth.py          ← ee_auth; also accepts SpectraLab's GEE_SERVICE_ACCOUNT_JSON
  _fixtures/       small CSVs (package data) for offline tests in both repos
```

### A2. Rules for everything in `src/amdtool`

- **No `print`** (use `logging`), **no `sys.exit`/`SystemExit`** (raise), **no
  `init_ee()` calls** — every Earth Engine function takes an initialised `ee`,
  so a host app owns authentication.
- **No `__file__`-relative data paths** — a `data_dir` argument; the CLIs pass
  the repo's `data/`.
- **No `sys.path` mutation.**
- **Preserve RNG consumption order exactly** — permutation p-values depend on it.

### A3. Keep every existing command working

`python/seep_detect.py`, `cmd_detect.py`, `cmd_confound.py`, `fetch_wqp.py`,
`ee_auth.py` become thin wrappers that re-export the moved names, so other
scripts importing them are untouched and every documented flag and output is
byte-compatible. **Out of scope this round:** the land-arm, Rockwell, Arm A and
catchment scripts — they keep working through the re-exports.

Also fix `convolve_splib07`: `np.trapz` → `np.trapezoid`, with a unit test on a
synthetic spectrum.

### A4. Behaviour-neutral gate — every one must reproduce exactly

| baseline | source | expected |
|---|---|---|
| CMD1 30 m | `cmd_detect --analyse` on `cmdgeo_l8_*.csv` | rho −0.354, n=137, p=0.0028 |
| CMD2 partial | `cmd_confound --analyse` | −0.246, p=0.0254 |
| CMD3 conductance ladder | `cmd3*` CSVs | −0.187 / −0.158 / −0.138 / −0.010 / +0.003 |
| B2 dose-response | `seep_detect --analyse`, L8 | +0.568, n=75, p=0.0004 |
| B2 detection | S2, `FerricIron1` vs C1 | worst-case J 0.234 |
| regenerated `validation/report_*.txt` | diff against committed | identical |
| live extraction | re-extract 20 Monday Creek stations, 30 m | max abs diff ≤ 1e-12 |
| `catchment_dem --self-test` · `ee_auth` 5 paths · `classify_v240` | — | unchanged |

Tests in `tests/` (pytest): pure-stat unit tests on committed fixtures; golden
tests read `data/` when present and skip otherwise; live Earth Engine tests only
with `AMDTOOL_EE_TESTS=1`. `docs/OPERATOR_GUIDE.md` §0 switches to
`pip install -e .`.

---

## Part B — Blind-search test

### B1. Pre-registration — `validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md`

Committed **before any landscape point is extracted**; commit ancestry is the
proof.

**Question.** At a fixed flagged-area budget, what fraction of known mine-source
sites fall inside the highest-scoring part of a district?

**Score (fixed; chosen by B2 on the 86 points — disclosed).** `FerricIron1`,
p90, 60 m buffer, Sentinel-2 composite **identical to `s2_composite`**, 20 m.

**Unit = site.** Source-type WQP stations merged by single linkage at **250 m**;
a site's score is the **max** of its stations'.

**Two co-primary hypotheses, Holm-corrected:**

| | sites | independence | power at 5% budget, α=0.025 |
|---|---|---|---|
| **H-BS1** — Alma, Creede, Lake City (never analysed) | **35** (61 locations) | districts never used for any choice | r=0.15: **0.43** · 0.20: **0.73** · 0.30: **0.97** |
| **H-BS2** — unused stations in Silverton, Ouray, Leadville, Central City | **107** (186 locations) | stations unused, but districts informed index choice | r=0.15: **0.94** · 0.20: 1.00 |

Stated in the registration: **a null on H-BS1 does not exclude a threefold
lift.** The 86 analysed targets are reported as a **labelled in-sample**
tertiary result.

**Landscape sample.** **2,000** random points per district inside
`region_geometry`, seed **20260914**, same statistic; points with no valid
pixels dropped and counted. **Cutoff = the district's 95th percentile** — no
labels involved, so no leakage.

**Budgets.** **5% primary**; 1% and 10% secondary.

**Bare-ground baseline.** The panel's `NDVI_stress` at 60 m (confirm its
direction in `water_indices.ndvi_stress_ee` while writing the registration),
scored at the same budget on the same sites. Paired **exact McNemar**.

**Verdict — one table per hypothesis, mutually exclusive rows:**

| outcome (at the Holm-adjusted level) | verdict |
|---|---|
| binomial recall > budget **and** McNemar: `FerricIron1` flags more sites than baseline | **DISCOVERY SIGNAL** |
| binomial recall > budget, McNemar not significant | **NOT BETTER THAN BARE GROUND** |
| binomial not significant | **NO SIGNAL DETECTED** (with that hypothesis's power) |

**Sensitivities (reported, never verdicts):** snow-masked composite (SCL 11 —
the primary composite does not mask snow); cluster radius 100 / 500 m; median
instead of max; station-level recall; NLCD-barren share of flagged area.

**Disclosures written in advance:** index choice is in-sample on the 86;
Red Mountain Pass (natural iron oxide) lies inside the Silverton and Ouray
boxes, and natural acid rock drainage is chemically AMD-like; known sources are
agency-monitored, so recall on them does not estimate recall on unknown sites;
**precision cannot be measured from the archive.**

### B2. Implementation

`src/amdtool/blind_search.py` + CLI `python/blind_search.py`, reusing
`imagery.random_landscape_points`, `extract_buffers` (one band, batch floor 1,
120 scenes unchanged), `stats.binomial / mcnemar / wilson`.

### B3. Outputs

- `validation/ARM_BLIND_SEARCH_<date>.md` + raw `report_blind_search_<date>.txt`.
- **Field sampling frame for `docs/FIELD_CAMPAIGN.md` H-DISC**, produced after
  the verdict: flagged area (top 5%) per district → clusters → drop anything
  within 500 m of a WQP station → **40 sampled with a fixed seed**. Labelled
  *a sampling frame, not detections.*

---

## Part C — SpectraLab "AMD severity report" (branch `feature/amd-severity-module`)

### C1. What the module does

Stages: **chemistry → composite → extract → statistics → raster → report**.
Outputs under `<mission_base>/amd/` (the module creates it; `MISSION_SUBFOLDERS`
is untouched because the frozen notebooks import it).

Two presets, both already validated:

| preset | index | season / sensor | buffer | analytes | extra gate |
|---|---|---|---|---|---|
| **metal mine** | `FerricIron1` p90 | May–Jul, Landsat 8 (S2 optional) | 60 m | dissolved Fe, total Fe, pH | — |
| **coal drainage** | `NDVI_stress` p90 | leaf-off, Landsat 8 | 30 m | sulfate, conductance | canopy: median NDVI > 0.6 → UNINTERPRETABLE |

**Grouping** for within-group permutation and sign consistency: the AOI split
into a **k × k grid** (default 2 × 2), outcome-blind like CMD3's tiles; groups
under 8 stations are reported but excluded from the sign check.

**`report.md`** states the verdict with n, the per-tile table,
**"EXPLORATORY — not pre-registered"**, the MAY / MAY NOT boundaries, and
explicitly that **SpectraLab stepwise material identifications (e.g. jarosite)
are not evidence of mine drainage** (finding W2). Thin groups, canopy and
outside-CONUS chemistry are `warnings`, never `errors`.

### C2. Files

| file | change |
|---|---|
| **NEW** `src/spectralab/modules/amd_module.py` | `AMDSeverityModule`, id `amd`, capabilities `needs_ee, needs_aoi, produces_tabular, produces_raster`; **no top-level import of `amdtool` or `ee`** (UI-isolation rule); `validate()` returns "install spectralab[amd]" when `amdtool` is missing |
| `modules/registry.py` | lazy `register(AMDSeverityModule())` |
| `ui/pages/new_run.py` | add `amd_*` keys to `_EXTRAS_KEYS`; `_MODULE_LABELS["amd"]` |
| `core/manifest.py` + `jobs/worker.py` | `_attribution_block(..., data_citations=None)`; worker passes the module's; **default output unchanged** |
| `pyproject.toml` | extra `amd = ["amdtool"]`; `[tool.uv.sources] amdtool = { path = "../Sulfate-Methos", editable = true }` |
| `scripts/build_exe.py` | hidden import only — **no build this round** |
| `docs/AMD_MODULE.md`, `docs/WORKLOG.md` | module guide; worklog entry (their §8) |

Settings, all prefixed `amd_` so none collides with the S2 date finder bound to
`dates`: `preset`, `sensor`, `radius_m`, `statistic`, `station_set`,
`chemistry_source` (fetch from WQP / existing folder), `chemistry_folder`,
`grid`, `n_perm` (5000), `seed`, `min_group_n` (8), `export_raster`, and
Advanced `extraction_csv` — analyse an existing extraction without Earth
Engine, which is also what makes the offline test possible.

### C3. SpectraLab rules honoured

- **§2 science invariants:** structural proof — `git diff --name-only main...`
  contains none of `vpca_core.py`, `pipeline.py`, `imagery.py`.
- **§4 staging:** explicit paths only; never `AGENTS.md`, `Stepwise Regrission/`,
  `docs/Bug_Report_Dr.Ortiz.docx`, `recent vpca/`, `uv.lock`, or any key.
- **§6:** every change defaults to today's behaviour, proven by a manifest
  parity test for `vpca` and `stepwise`.
- **§1:** no version bump, wheel, exe or `RELEASES.md`. Branch pushed only.
- Git runs with `git -c safe.directory=D:/dev/VPCA+STEPWISE-REGRESSION` per
  command — no global config change.

### C4. Tests

- `tests/test_registry.py` — add `amd` + protocol check.
- `tests/test_ui_isolation.py` — must pass **unchanged**.
- **NEW** `test_amd_module_offline.py` — `validate`/`plan`/`run` on the packaged
  fixture via `amd_extraction_csv`; writes real files; numbers equal
  `amdtool.dose_response.analyse` on the same input.
- **NEW** `test_amd_settings_reach_spec.py` — copy of `test_new_run_spec.py` for
  the `amd_*` keys (the existing one only covers `vpca`).
- **NEW** `test_manifest_attribution.py` — `vpca`/`stepwise` unchanged; `amd`
  carries the Landsat + WQP citations.
- One live test marked `ee`, behind `SPECTRALAB_EE_TESTS=1`.

---

## Part D — findings to log now

`validation/AUDIT_2026-09-14_ARMA_AND_TOOLING.md`:

1. **Arm A σ thresholds computed per catchment** (the AOI-extent defect).
2. **Arm A 31 rows = 28 distinct polygons**, three leaking across LORO splits.
   The retraction stands — it never rested on these rows passing — but its
   numbers carry the leakage, and any Arm A re-run must dedupe globally first.
3. **`convolve_splib07` crashes on NumPy 2.x** (unused; fixed in Part A).
4. **Creede and Lake City are recorded outside the "San Juan caldera" group**,
   but both sit in San Juan volcanic-field calderas. **Confirm against a
   citable USGS source before correcting** the grouping, and fix labels before
   any geology test.
5. **CMD2's absolute decision bars cannot transfer to Pennsylvania**: its raw
   0.143 / 0.187 already sit below them, so "rejected" is unreachable. A PA
   confound test must be framed as attenuation from PA's own raw value.

---

## Logging rule

Per `CLAUDE.md`, after each part: dated report in `validation/`; `STATE.md`;
a `DECISION_LOG.md` row; this plan mirrored to
`docs/plans/2026-09-14-blind-search-amdtool-spectralab.md`; commit and push.
SpectraLab: its `docs/WORKLOG.md`; branch commit and push.

---

## Verification

**Sulfate-Methos**
1. Every row of the A4 gate reproduces exactly, from both the wrapper CLIs and
   the library.
2. `pytest` passes; live tests pass with `AMDTOOL_EE_TESTS=1`.
3. `git merge-base --is-ancestor <registration> <first landscape-data commit>`
   succeeds.
4. The blind-search report states each hypothesis's verdict **with its power**.

**SpectraLab**
5. `uv run pytest -q` — all existing tests plus the new ones pass.
6. `git diff --name-only main...` excludes `vpca_core.py`, `pipeline.py`,
   `imagery.py`.
7. **End to end in the UI:** `uv pip install -e ../Sulfate-Methos`, then
   `uv run python scripts/run_ui.py` → New Run → *AMD severity report* → draw
   a Silverton AOI → metal-mine preset → Run. Run Detail shows `report.md`, the
   CSVs and the GeoTIFF; `run_manifest.json` cites Landsat and WQP; the report's
   rho equals the `amdtool` CLI on the same inputs.
8. A `vpca` and a `stepwise` run still produce byte-identical attribution
   blocks.

---

## Outcome (recorded 2026-09-16)

Full account: `validation/ROUND_SUMMARY_2026-09-16.md`.

| part | status |
|---|---|
| D — log the defects | **done:** `AUDIT_2026-09-14_ARMA_AND_TOOLING.md` (items 1–8); later `AUDIT_2026-09-15_B2_REPRODUCTION.md` (items 9–11) |
| B1 — pre-register the blind search | **done** in `ad05971`, before any landscape data |
| A — `amdtool` | **done:** package + 207 tests; `seep_detect`, `cmd_detect`, `cmd_confound`, `fetch_wqp` and `ee_auth` are wrappers; gate in `AMDTOOL_REFACTOR_GATE_2026-09-14.md` |
| B2/B3 — run the blind search | **done:** H-BS1 NO SIGNAL DETECTED, H-BS2 NOT BETTER THAN BARE GROUND (`ARM_BLIND_SEARCH_2026-09-15.md`); field frame drawn; **snow-masked sensitivity not run** |
| C — SpectraLab module | **done on branch** `feature/amd-severity-module`; **not merged, not released, not installed as an app** |

| verification item | status |
|---|---|
| 1. The A4 gate reproduces | **passed**, with one deliberate change: B2 detection tables differ only in the tie-corrected rows (audit item 9) |
| 2. `pytest` and live tests | **207 pass.** The `AMDTOOL_EE_TESTS` live tests were **not written**. Live Earth Engine behaviour was checked instead by the Monday Creek re-extraction (max abs diff 0.000), `catchment_dem --self-test` 6/6, and the blind-search extraction |
| 3. Registration ancestry | **passed:** `ad05971` is an ancestor of every result commit |
| 4. Verdicts reported with power | **passed** |
| 5. SpectraLab suite | **509 passed, 3 skipped.** Run with `.venv` python rather than `uv run`, because an extraction was using that venv |
| 6. Science files untouched | **passed** |
| 7. UI end-to-end | **not run; the author's step** (`docs/HOW_TO_TEST.md` §C). The live module test passed against Earth Engine instead |
| 8. vpca/stepwise attribution unchanged | **passed** (`tests/test_manifest_attribution.py`) |

**Deviations, each logged where it happened:**
- No `amd` extra and no `[tool.uv.sources]` in SpectraLab's `pyproject.toml`.
  Either would break `uv lock` on machines without the sibling repo, and the
  bare PyPI name is not ours.
- Preset overrides are allowed under Advanced, but always produce a warning.
