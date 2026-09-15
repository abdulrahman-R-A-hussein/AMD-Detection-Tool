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

---

## NOT yet passed — do not read as done

| gate item | status |
|---|---|
| `seep_detect.py`, `cmd_detect.py`, `cmd_confound.py`, `fetch_wqp.py` → thin wrappers | **not done**; each still carries its own copy of the moved code |
| regenerate `validation/report_*.txt` through the wrapper CLIs and diff | **not run** |
| live re-extraction of 20 Monday Creek stations at 30 m, max abs diff ≤ 1e-12 | **not run** (Earth Engine was busy with the blind-search extraction) |
| B2's within-region permutation p = 0.0004 quoted in README | **not re-derived** here; the function that computes such p is proven RNG-identical to legacy |
| SpectraLab UI end-to-end run | **not run**; the offline module test and full suite pass (SpectraLab `docs/WORKLOG.md`) |

**Caveat.** Exact reproduction proves the refactor changed no computation on
these inputs. It says nothing about whether those results are right; that is
what the validation reports and their caveats are for.
