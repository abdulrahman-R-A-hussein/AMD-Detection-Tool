# Round summary — 2026-09-14 → 2026-09-16

**What this covers:** everything done in the round that started with *"what is
next in terms of new tests, and what app and GEE can I test the framework
through, knowing it will be added to SpectraLab"*. It covers what was built,
every finding with its numbers, what exists on the lab PC now, and what comes
next.

**Canonical state:** [`STATE.md`](STATE.md) · **The journey:** [`DECISION_LOG.md`](DECISION_LOG.md) ·
**How to test it all yourself:** [`../docs/HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) ·
**The plan that was executed:** [`../docs/plans/2026-09-14-blind-search-amdtool-spectralab.md`](../docs/plans/2026-09-14-blind-search-amdtool-spectralab.md)

---

## 1. Status at a glance — what exists, and where

| question | answer (checked 2026-09-16) |
|---|---|
| **Is there a new SpectraLab release?** | **No.** SpectraLab is still **0.39.0**. `releases/` ends at `SpectraLab-0.39.0.exe` and its wheel. |
| **Does `SpectraLab-0.39.0.exe` contain the AMD module?** | **No.** |
| **Is SpectraLab installed on this PC as an app?** | **No.** It is not a `uv` tool and not on PATH. |
| **Where is the AMD module?** | On branch **`feature/amd-severity-module`** of `D:\dev\VPCA+STEPWISE-REGRESSION` (pushed), which is checked out there. You run it from source ([`HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) §C). |
| **What was installed?** | Only **`amdtool` 0.1.0**, *editable* from `D:\dev\Sulfate-Methos`, into `D:\dev\VPCA+STEPWISE-REGRESSION\.venv`. |
| **AMD-Detection-Tool version** | Last tag **v3.10.0** (2026-09-13). Every commit of this round is on `main` and pushed, but **untagged**. |
| **Zenodo** | **NOT updated.** The archive (DOI `10.5281/zenodo.19429983`, `CITATION.cff` 3.10.0) predates everything below. This is the author's action; steps in [`HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) §E. |
| **Earth Engine tool** | Unchanged this round: `earth-engine/amd_detection_v2.4.0.js`, which reports **v3.1.0**. |

---

## 2. What was asked, and what you decided

1. **What is the next test?** The **blind-search test**: does the tool find
   mine sources it was not told about?
2. **What can you test the framework through, knowing it will join
   SpectraLab?**
   - **Library + thin module:** the AMD Detection Tool becomes an importable
     package, `amdtool`, and SpectraLab gets a small module over it.
   - **First module:** the verified **severity report**.
   - **Where:** a SpectraLab **feature branch, no release.**
3. **Wrap-up (2026-09-16):**
   - the record lives in repo files only;
   - SpectraLab stays branch-only;
   - Zenodo is recorded as not updated, with steps;
   - the snow-masked sensitivity is left as a next step.

---

## 3. What was built

### 3.1 `amdtool`, the importable package (`D:\dev\Sulfate-Methos\src\amdtool`)

| module | what it holds |
|---|---|
| `stats` | AUC, worst-case LORO J (**tie-corrected**, §4.9), permutation tests, BH, variance split, Spearman, partial Spearman, exact binomial, McNemar, Wilson, Holm |
| `dose_response` | the dose-response test with a within-group permutation null, returning a result object rather than printed text |
| `imagery` | Landsat and Sentinel-2 composites, index image, buffer extraction, random landscape points |
| `chemistry` | Water Quality Portal download and consolidation, station medians, one station loader |
| `regions`, `geometry` | curated regions and overlay; one `BBox` convention |
| `severity` | the severity report behind SpectraLab (two presets; outputs; claim boundaries) |
| `raster` | score GeoTIFF + PNG preview. It writes only complete downloads, and the preview halves its size on Earth Engine's memory limit |
| `blind_search` | the registered blind-search analysis, including the link-distance sensitivity and the field-frame notice |
| `auth`, `claims`, `io`, `errors` | credentials for standalone use; claim wording as data; CSV loading; exceptions |

- **Rules the package follows:** it never prints, never exits, and never
  authenticates for a host (the host passes in `ee`).
- **Tests:** **207 pass** (`python -m pytest tests/`, re-run 2026-09-16).
- **The legacy scripts are thin wrappers:** `python/seep_detect.py`,
  `cmd_detect.py`, `cmd_confound.py`, `fetch_wqp.py` and `ee_auth.py` import the
  moved code from `amdtool`. Every documented command still works, and still
  prints the Earth Engine retry lines.

### 3.2 Scripts added

| script | purpose |
|---|---|
| `python/blind_search_sites.py` | fixes the blind-search sample from station metadata only (registered) |
| `python/blind_search.py` | `--extract` / `--analyse` / `--frame`. It refuses to analyse unless the registration is committed and the site list matches its SHA-256 |
| `python/b2_reproduction_audit.py` | the evidence for audit items 9–11 |
| `python/b2_dose_response_regen.py` | regenerates B2's dose-response family (p = 0.0004) from committed code |

### 3.3 SpectraLab "AMD severity report" module (branch only)

- **The module:** `src/spectralab/modules/amd_module.py`, id `amd`. It asks:
  inside a drawn AOI, does the index validated for this drainage type track
  measured water chemistry?
  - **Presets:** `metal_mine` (FerricIron1, 60 m, May–July) and `coal`
    (NDVI_stress, 30 m, leaf-off, canopy gate).
  - **Test:** k × k grid tiles with a within-tile permutation null.
  - **Report:** always marked **EXPLORATORY**; it states that stepwise
    "jarosite" matches are not mine-drainage evidence.
- **Wiring:**
  - registry and New Run form;
  - the manifest now cites Landsat or Sentinel-2 plus the Water Quality Portal
    (VPCA/stepwise attribution unchanged, pinned by a test);
  - an exe build hidden import (no build made).
- **Tests:** the offline AMD tests pass (**25 passed, 1 skipped by design**,
  re-run 2026-09-16); the full suite passed 509 on 2026-09-14. The **live
  Earth Engine test passed** twice (§4.13).
- **Science files untouched:** `vpca_core.py`, `pipeline.py`, `imagery.py`.
- **Guide:** `docs/AMD_MODULE.md`; worklog `docs/WORKLOG.md`.

---

## 4. Findings — each with its numbers, n and caveat

**No pre-registered verdict changed in any audit.** Every item is logged in
full in the linked report.

### Audit 2026-09-14 — [`AUDIT_2026-09-14_ARMA_AND_TOOLING.md`](AUDIT_2026-09-14_ARMA_AND_TOOLING.md)

1. **Arm A computed σ thresholds per catchment**, so catchment size acted as a
   classification parameter. The Arm A retraction stands; its loadings must not
   be reused.
2. **Arm A's "31 catchments" are 28 distinct polygons.** Three are shared
   across regions and leak across leave-one-region-out splits. Quote n = 28.
3. **Creede and Lake City were mislabelled as non-caldera.** Both sit in San
   Juan calderas (USGS I-2799, I-962). OPEN #1's plan to test geology on the
   data that generated the idea is **withdrawn**.
4. **`convolve_splib07` crashed on NumPy 2.x.** Fixed and tested; no reported
   number was affected.
5. **CMD2's absolute decision bars cannot transfer to Pennsylvania.** PA's raw
   values (−0.143 / −0.187) already sit below them.
6. **A code comment claimed a Creede/Alma extraction that never happened.**
   Those districts were genuinely unused, which the blind search relies on.
7. **`partial_spearman` could return 11.97** in a degenerate case. Fixed; a
   golden test proves no committed CMD2 value moved.
8. **"Sign-consistent across four districts" hid a zero.** FerricIron1 vs
   dissolved Fe is +0.64 / +0.68 / +0.64 (n = 20 / 17 / 15), but **+0.004 in
   Leadville (n = 23)**.
   - No number moves.
   - The claim is narrowed to **three of four districts** in README,
     CITATION.cff, PROJECT_OVERVIEW, GRANT_CASE, FIELD_CAMPAIGN,
     ACCURACY_ASSESSMENT, STATE and `amdtool`.
   - **Caveat:** per-district n is small (about ±0.4).

### Audit 2026-09-15 — [`AUDIT_2026-09-15_B2_REPRODUCTION.md`](AUDIT_2026-09-15_B2_REPRODUCTION.md)

Found by regenerating every B2 report from committed code before converting the
scripts.

9. **Worst-case J was evaluated inside runs of tied scores**, which made it
   depend on row order.
   - **Scope:** all 57 B2 detection rows re-computed; **6 printed values
     change**, and none crosses the 0.25 bar.
     - L8 AMDclassFrac vs C2: 0.000 → **+0.235**. Its recomputed q is 0.0004,
       but J stays below the bar.
     - Shipped classifier vs bare ground (C3b): 0.000 → **−0.252**.
     - B2b grid: all 0.000 → **−0.452 … 0.000**.
   - **Unchanged:** the headline S2 FerricIron1 vs C1 **J 0.234**.
   - **Status:** fixed in `amdtool` and tested against brute force; the land
     arm was checked and is unaffected.
   - **Corrected tables:** `report_seep_b2_{l8,s2}_tiefix_2026-09-15.txt`.
10. **The C3b amendment report pooled a cloud-unfiltered composite** into its
    C2/C3 tiers: 161 / 138 scenes against 61 / 59. Its C3b, C1 and target rows
    are clean; its C2/C3 rows must not be cited.
11. **The B2 reports regenerate byte for byte only with the districts in an
    unrecorded order** (Silverton, Leadville, Ouray, Central City). From now on
    a regeneration command lists its inputs in order.

### Traceability closed

- **B2's p = 0.0004** existed only in a .md report. It now regenerates exactly
  from committed code (all five table rows), and a test pins it.
  **Caveat:** p is a Monte Carlo estimate; at 10,000 draws it is 0.0002.
- **The refactor itself changed nothing it shouldn't have.** Through the
  wrapper scripts, CMD1, CMD2, CMD3 (the part the script writes) and B2
  dose-LORO regenerate identically.
- **A live Monday Creek re-extraction** (27 stations) matches the committed
  file **exactly** (max abs diff 0.000).
- **Self-tests:** `catchment_dem` 6/6 PASS; `classify_v240` 94.95% PASS.
- **Rationale that nearly got lost:** the first copies into `amdtool` had
  dropped **53 rationale comments and 9 docstrings**. All were restored before
  any script was converted, and a test now checks every moved function against
  the committed original.

### 4.12 The blind search — [`ARM_BLIND_SEARCH_2026-09-15.md`](ARM_BLIND_SEARCH_2026-09-15.md)

Pre-registered in `ad05971` before any landscape data; all seven districts
extracted; none FAILED.

| hypothesis | sites | flagged (5% budget) | recall (95% CI) | p | vs bare ground | **verdict** |
|---|---|---|---|---|---|---|
| **H-BS1** — districts never used to choose the index | 32 | 4 | 0.125 (0.050–0.281) | 0.074 | 3 vs 1 | **NO SIGNAL DETECTED** |
| **H-BS2** — unused stations where the index was chosen | 50 | 14 | 0.280 (0.175–0.417) | 1.0 × 10⁻⁷ | 12 vs 4, McNemar p 0.038 (level 0.025) | **NOT BETTER THAN BARE GROUND** |

- **H-BS1 was one site short** of the registered bar. Power was 0.54 at a
  threefold lift, so a modest lift is **not excluded**.
- **Flagged landscape is 1.2–4.4× enriched for NLCD barren land** in every
  district.
- **Sensitivities are mixed and never verdicts.** Some variants would pass H-BS2's
  bare-ground test (10% budget, 500 m linking); others would not.
- **T-86**, the in-sample targets: recall 0.243. Labelled in-sample.
- **Field frame:** 40 clusters, a **sampling frame, not detections**. Visiting
  it as candidate sources is not supported.
- **What it means:** discovery moves from *untested* to ***tested, not
  supported***. Severity ranking at known sources, in three of four districts,
  remains the validated use.
- **Not run:** the registered **snow-masked** sensitivity.

### 4.13 SpectraLab module — first live runs

- **The live Earth Engine test passed.** It did the WQP download, a 103-scene
  Landsat composite, extraction, statistics, the raster and the report over a
  391 km² Silverton box.
- **It caught a real bug: a 0-byte PNG.**
  - **Cause, reproduced:** Earth Engine refuses the 1024 px preview with "User
    memory limit exceeded", while 512 px works.
  - **Fix:** the preview now halves its size, and files are written only from
    complete downloads.
  - **Re-run:** passed, with a 470 KB preview.
- **NO_TESTABLE_PAIRS on one district is correct.** The Silverton box held 12
  mine-source stations against a minimum of 20, and B2's per-district counts
  were 15–23. Draw AOIs across more than one district.

---

## 5. Operational log

- **The blind-search extraction spanned two sessions.** The first process
  (started 2026-09-14 20:40) died with its Claude session partway through
  Ouray. Ouray and Silverton were re-extracted from 2026-09-15 09:34 with
  behaviour-identical code, and finished at 17:18.
- **Earth Engine returned intermittent HTTP 502/503 errors, and this PC had two
  short DNS outages.** All recovered within the client's retries.
- **A rule was committed before any result** (`724acc8`): a transient
  service/network failure means re-extract, never FAILED.
- **Two registered analysis pieces were missing** (the link-distance
  sensitivity and the frame notice). They were implemented and committed
  (`d5c30f3`) **before** the analysis ran, tested on synthetic data only.
- **Git:** every commit was staged by explicit path. Untracked items created
  outside this work (`.codex/`, `AGENTS.md`, the GSS/Denver documents, and in
  SpectraLab `AGENTS.md`, `Stepwise Regrission/`, the bug-report docx,
  `recent vpca/`, `uv.lock`) were never staged. The service-account key was
  never printed or committed.

---

## 6. Commits

**AMD-Detection-Tool (`main`, pushed):**

| commit | what |
|---|---|
| `ad05971` | blind-search pre-registration + six-item audit |
| `10dbdbf` | `amdtool` package; audit items 7–8; severity claim narrowed to 3 of 4 districts |
| `17746b0` | tied-score fix; pooled composites; order; legacy scripts → wrappers |
| `d5c30f3` | registered blind-search sensitivities implemented before analysis; raster preview fix |
| `e94c902` | B2 p = 0.0004 regenerated; land arm unaffected |
| `724acc8` | extraction status, resume command, 5xx rule fixed before any result |
| `0e3e7e8` | **blind-search result** |
| `02d061d` | last stale passages corrected |
| *this commit* | round summary, testing guide, refreshed STATE |

**SpectraLab (`feature/amd-severity-module`, pushed; not merged, not released):**

| commit | what |
|---|---|
| `6dc0b17` | AMD severity report module over `amdtool` |
| `a3ac5d4` | first live run: passed; 0-byte preview caught; single-district limit documented |
| *wrap-up commit* | status entry: branch only, nothing released or installed |

---

## 7. What is next

**Author actions:**
1. **Publish the Zenodo update.** Bump `CITATION.cff` to 3.11.0 and today's
   date, tag, and release ([`HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) §E).
2. **Run the SpectraLab AMD module in the UI** ([`HOW_TO_TEST.md`](../docs/HOW_TO_TEST.md) §C).
   This is the one gate item still open.
3. **Decide:** merge the branch and cut **SpectraLab 0.40.0**, or keep it on the
   branch.
4. **Review** `.private/EB2_DOCUMENTATION.md`.

**Analysis:**

5. **Field campaign:** pre-register before the first field day
   (`docs/FIELD_CAMPAIGN.md`). H-DISC is now a test of the blind search's
   *negative* expectation, sampled from the registered 40-cluster frame.
6. **Snow-masked blind-search sensitivity:** about a day of Earth Engine time,
   then re-run the analysis. The verdicts do not depend on it.
7. **Science leads** (details in [`STATE.md`](STATE.md) OPEN):
   - a Pennsylvania disturbance covariate;
   - a better Ohio covariate;
   - an Arm A re-run with DEM catchments, global de-duplication and
     per-district σ;
   - geology labels fixed from a citable source before any new region's sign is
     seen.
