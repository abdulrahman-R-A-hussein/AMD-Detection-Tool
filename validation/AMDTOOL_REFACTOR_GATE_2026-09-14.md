# `amdtool` refactor gate — 2026-09-14

**Question.** Can the validated pipeline be packaged as an importable library,
for SpectraLab and anyone else, **without moving a single committed number**?

**Answer so far: yes, for everything tested below, and proven by tests, not
asserted.** The gate is **not complete**. What remains is listed at the end
and must not be read as passed.

**Reproduce:** `python -m pytest tests/` with the Earth Engine venv
(`D:/dev/VPCA+STEPWISE-REGRESSION/.venv`). **68 passed, 0 skipped, 59 s.**
Golden tests read the gitignored `data/`, which is regenerable from committed
code. On a clone without it they **skip**, so on such a machine a green run
proves only the unit tests.

---

## What reproduces exactly

| baseline | committed source | reproduced by | result |
|---|---|---|---|
| CMD1, 30 m | `report_cmd1_geo30_2026-08-16.txt` | `amdtool.dose_response.analyse` on `cmdgeo_l8_*.csv` | **16 table lines identical**; headline ρ **−0.354**, n = **137**, p = **0.0028**; verdict PARTIAL; canopy median 0.462 |
| CMD2 T1 table | `report_cmd2_confound_2026-09-08.txt` | `amdtool.stats.partial_spearman` / `perm_p_within` | **every T1 line, permutation p included, identical** |
| CMD3 conductance ladder | CMD3 CSVs | `analyse` | ρ −0.187 / −0.158 / −0.138 / −0.010 / +0.003 |
| B2 detection, S2 | `report_seep_b2_s2_2026-08-15.txt` | `stats.auc`, `stats.loro_worst_j` | `FerricIron1` vs C1: AUC **0.723**, worst-case J **0.234**, n **86 / 446** |
| B2 dose-response, L8 | `report_seep_b2_l8_2026-08-14.txt` | `stats.spearman`, `stats.variance_split` | line identical: ρ **+0.568**, n = **75**, between-region **24%** |
| B2 dose-response LORO | `report_seep_b2_doseloro_2026-08-14.txt` | as above + the committed LORO R² arithmetic | line identical: pooled +0.568, LORO R² **−0.538**, per district +0.64 / +0.00 / +0.68 / +0.64 |
| B2 permutation p | `python/seep_detect.py` at `ad05971` | `stats.perm_p_within_region` | **equal p, and identical RNG state afterwards** (300 permutations, observed J −0.018) |
| WQP consolidation | `python/fetch_wqp.py` at `ad05971` | `amdtool.chemistry.consolidate` | `consolidated.csv` and `consolidated_sediment.csv` **byte-identical** for Huff Run and Silverton |
| Credential resolution | `python/ee_auth.py` at `ad05971` | `ee_auth.py`, now a wrapper over `amdtool.auth` | **identical outcome or error text in all 6 cases** (key env set / set to a missing file / legacy file / project / nothing / SpectraLab variable only) |
| `catchment_dem --self-test` (live Earth Engine) | expected `6/6` and `PASS` (OPERATOR_GUIDE §0) | re-run after the change, **authenticating through the new `ee_auth` wrapper** | **6/6 within ±33% of NWIS, PASS** (ratios 0.99–1.28×) |
| `classify_v240` self-test (offline) | documented 94.95% ceiling | re-run after the change | **94.95% identical on 20,000 Silverton pixels, PASS** |
| **Moved source = committed source** | `seep_detect`, `cmd_detect`, `cmd_confound`, `gee_classify`, `water_indices`, `match_scenes` at `ad05971` | `tests/test_source_parity.py`: AST comparison (docstrings aside), every difference checked against a named harmless kind; every constant read compared by value | **24 functions**. The stats functions and `process_landsat`, `add_indices`, `composite_for_region`, `green_nir_ee`, `ndvi_stress_ee` are identical. `s2_composite`, `l8_composite`, `l8_composite_season` and `index_image` differ only in where they import. `extract_buffers` differs only print→log; `water_term` reads `WATER_MNDWI` = 0.3 = `T['water']`. **Constants: 0 mismatches.** This is the code-level proof that the blind search's composite is the registered `s2_composite` |

**Parity tests are pinned to history.** Every "legacy" comparison imports the
script **as committed at `ad05971`** (via `git show`). Once a script becomes a
wrapper, its parity test therefore keeps comparing against the original code,
not against itself.

---

## Changes that are deliberate, each proven harmless or logged

| change | why | proof |
|---|---|---|
| `partial_spearman` degenerate-case guard | returned **11.97** when rank(z) explains rank(x) exactly | audit item 7; the guard returns identical values at every CMD2 covariate and watershed |
| `np.trapz` → `np.trapezoid` in `convolve_splib07` | crashed on NumPy 2.4.6 | audit item 4; unit tests on synthetic spectra |
| `chemistry._get` raises `WqpRequestError` | a host must not be killed by `sys.exit`; the class subclasses `RuntimeError`, so old `except RuntimeError` still catches it | unit test |
| `amdtool.auth` also reads `$GEE_SERVICE_ACCOUNT_JSON` | one key serves SpectraLab and the CLIs | `ee_auth.py` passes only the old variable, so CLI resolution is unchanged; test case "SpectraLab variable only" |

## Found while building the gate

**Audit item 8.** B2's "sign-consistent across four districts" hides
**Leadville ρ = +0.004 (n = 23)**. No number moves; the claim narrows to three of
four districts. Corrected in six documents. See
`AUDIT_2026-09-14_ARMA_AND_TOOLING.md` §8.

**Regenerating the archive before converting the scripts (2026-09-15)** found
audit items 9–11 (`AUDIT_2026-09-15_B2_REPRODUCTION.md`):
- worst-case J was computed inside runs of tied scores, now fixed in `amdtool`;
- the C3b report pooled two composites;
- the B2 reports regenerate byte for byte only in an unrecorded input order.

Committed code regenerated CMD1, CMD2, CMD3 (CLI part) and B2 dose-LORO
identically, and B2 L8/S2 identically in REGIONS order. **So the tie fix is a
deliberate change**: after it, B2 regenerates identically except the five
tie-corrected rows listed there.

---

## Wrapper conversion and regeneration (2026-09-15)

| gate item | result |
|---|---|
| `seep_detect.py`, `cmd_detect.py`, `cmd_confound.py`, `fetch_wqp.py` → thin wrappers | **done.** 35 definitions removed and imported from `amdtool`. Checked against `ad05971`: no public name lost; every moved name *is* the `amdtool` object; no undefined global in any function body. The first copies into `amdtool` had dropped 53 rationale comment lines and 9 docstrings; those were restored before any script was converted |
| regenerate `validation/report_*.txt` through the wrapper CLIs | CMD1 30 m, CMD2 and B2 dose-LORO **identical**. CMD3 **identical** in the 23 lines the CLI writes; the rest of that file is the separately appended ladder block. B2 L8 and S2: **identical except the tie-corrected rows.** Worst-case J changed in exactly the 4 L8 rows and 1 S2 row of audit item 9. AUC and n are identical everywhere, and the decision-rule and dose-response sections are byte-identical. p and q changed in 17 and 13 rows: the tie-affected rows, and BH q across each family. With p recomputed, `AMDclassFrac` vs C2 is significant (L8 q 0.0004, S2 q 0.031) but below the J bar, so no verdict moves. Corrected tables: `report_seep_b2_{l8,s2}_tiefix_2026-09-15.txt`. **Suite after conversion: 185 passed** |
| live re-extraction, Monday Creek, leaf-off, 30 m, `NDVI_stress` | **27 stations, 120 scenes, max abs diff 0.000** against the committed `cmdgeo_l8_monday_creek_oh.csv` (27 of 27 stations common), i.e. identical, not merely within 1e-12 |
| CLI output | `amdtool` logs instead of printing; `python/_amdtool_path.py` routes that to stdout with the scripts' old prefix, so the retry lines still appear (`tests/test_cli_logging.py`, and seen in the live run) |

## Closed 2026-09-15, after the wrapper conversion

| gate item | result |
|---|---|
| B2's within-region permutation p = 0.0004 (quoted in README, CITATION.cff, GRANT_CASE, ACCURACY_ASSESSMENT) | **Regenerated exactly** from committed code. All five rows of ARM_B2's Part 2 table match (rho, n, p, q, between-region share), for the 36-test family at 5,000 within-district draws, seed 20260814, districts in REGIONS order. Script `python/b2_dose_response_regen.py` writes `report_b2_dose_response_2026-09-15.txt`; `tests/test_golden_b2.py` pins the rows. Until now these numbers existed only in the .md report. **Caveat:** p is a Monte Carlo estimate; at 10,000 draws the same pair gives p = 0.0002, q = 0.0036 |
| land-arm J values vs the tied-score defect | **Unaffected.** `derive_thresholds`, `iron_criterion_search` and `iron_index_transfer` search only distinct cut values with `>`. `paper_faithful_test` scores fixed binary predictions, so "worst-case J = 0.000" for the v2.x multipliers simply means nothing was flagged |

## NOT yet passed — do not read as done

| gate item | status |
|---|---|
| SpectraLab UI end-to-end run | **not run**. The live module test passes against Earth Engine (SpectraLab `docs/WORKLOG.md`, 2026-09-15) |

**Caveat.** Exact reproduction proves the refactor changed no computation on
these inputs. It says nothing about whether those results are right; that is
what the validation reports and their caveats are for.
