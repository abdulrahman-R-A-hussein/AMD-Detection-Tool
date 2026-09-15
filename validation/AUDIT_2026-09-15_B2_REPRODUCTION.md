# Audit 2026-09-15 — Arm B2's reports regenerate, but three things were wrong with how they were computed or recorded

**Found while building the `amdtool` refactor gate.** Before
`python/seep_detect.py` became a wrapper, every committed B2 report was
regenerated from committed code and committed data, to have a baseline to diff
against. That found three problems. Item numbers continue from
[`AUDIT_2026-09-14_ARMA_AND_TOOLING.md`](AUDIT_2026-09-14_ARMA_AND_TOOLING.md)
(items 1–8).

> **No pre-registered verdict changes. Six printed worst-case J values do.**
> None of the headline numbers is among them.

**Evidence:** [`report_b2_reproduction_2026-09-15.txt`](report_b2_reproduction_2026-09-15.txt),
regenerated with no Earth Engine by

```
python python/b2_reproduction_audit.py --out validation/report_b2_reproduction_2026-09-15.txt
```

It needs `data/matched/seep_*.csv` (gitignored) and the repository's git
history. The committed sweep it compares against is loaded from `ad05971`.

---

## 9. Worst-case LORO J was evaluated inside runs of tied scores

**Mechanism.** `_worst_j_fast` sweeps the training rows by descending score and
evaluates Youden J after every row. It has been in `seep_detect.py` since
`fa1f7e2` and was copied verbatim into `amdtool.stats`. A `>=` threshold cannot
fall between two equal scores, so a J computed part-way through a run of tied
scores is unattainable, yet it can win the maximisation. The cut it selects is
then applied to the held-out region, so **the result depends on the order the
rows arrive in**.

**Demonstrated, not inferred.**
- **Synthetic** (`tests/test_worst_j_ties.py`). The committed sweep changes its
  answer when tied rows are shuffled. The corrected sweep equals a brute force
  over every distinct cut on 40 tied samples and is invariant to shuffling.
- **Archive.** Across 20 random row orders, L8 `AMDclassFrac` vs C2 ranged from
  0.000 to +0.235.

**What ties.**
- `AMDclassFrac`, a fraction: 18–70% of values tied in the B2 tables, 48–95% in
  B2b's v4 grid.
- In-stream C1 controls, where co-located monitoring stations share a buffer:
  27–49% tied.

**Impact: all 57 B2 detection rows recomputed.**

| row | committed J (p, q) | corrected J (p, q) |
|---|---|---|
| L8 `FerricIron1` vs C1 | −0.018 (0.197, 0.483) | −0.019 (0.204, 0.424) |
| L8 `ClaySulfateMica` vs C1 | +0.044 (0.022, 0.086) | +0.030 (0.036, 0.096) |
| L8 `AMDclassFrac` vs C1 | 0.000 (0.339, 0.653) | +0.032 (0.028, 0.095) |
| L8 `AMDclassFrac` vs C2 | 0.000 (0.498, 0.897) | **+0.235 (0.0001, 0.0004)** |
| S2 `AMDclassFrac` vs C2 | 0.000 (0.322, 0.561) | **+0.049 (0.015, 0.031)** |
| S2 `AMDclassFrac` vs C3b | 0.000 | **−0.252** (p not recomputed) |

The corrected J, p and q come from 10,000 within-region permutations,
regenerated through the corrected code with the districts in REGIONS order:
[`report_seep_b2_l8_tiefix_2026-09-15.txt`](report_seep_b2_l8_tiefix_2026-09-15.txt)
and [`report_seep_b2_s2_tiefix_2026-09-15.txt`](report_seep_b2_s2_tiefix_2026-09-15.txt).

```
python python/seep_detect.py --analyse --perms 10000 --out <report> --inputs \
  data/matched/seep_<l8|s2>_silverton_co.csv,data/matched/seep_<l8|s2>_leadville_co.csv,data/matched/seep_<l8|s2>_ouray_co.csv,data/matched/seep_<l8|s2>_central_city_co.csv
```

The C3b report was not regenerated, because its inputs pooled two composites
(item 10). Against the committed tables, the corrected ones differ in worst-case
J only in the rows above; AUC and n are identical everywhere, and so are the
decision-rule and dose-response sections. p and q differ in 17 (L8) and 13 (S2)
rows: the tie-affected rows themselves, and BH q across each family.

**The other 51 rows are identical to three decimals**, including every number
used as a headline:
- S2 `FerricIron1` vs C1 **+0.234**, vs C3 +0.318, vs C3b +0.318
- `NDVI_stress` vs C3b +0.700
- L8 `AMDclassFrac` vs C3 −0.304

**B2b.** The report printed 0.000 at all eight grid points. Corrected, they are
**−0.452, −0.443, 0.000, 0.000, 0.000, 0.000, −0.087, −0.087**. The best is 0.000,
so the **FAILURE verdict is unchanged**. The v3 baseline that both B2b and B2c
compare against (`AMDclassFrac` vs C3b) is **−0.252**, not 0.000.

**Verdicts.** No row crosses the 0.25 bar, so no B2, B2b or B2c verdict changes.
The two claims that leaned on the zeros become **stronger**:
- the shipped classifier scores bare ground *above* mine discharge (−0.252, not
  a neutral 0.000);
- B2c's continuous model moved J from **−0.252** to +0.617 against bare ground,
  not from 0.000.

**B2c's own numbers are unaffected.** Its detector takes thresholds from
`best_threshold`, which only evaluates distinct scores. Its printed
reproduction check equals the corrected values.

**Caveats.**
- **Recomputing p changes one reading.** With the corrected statistic,
  `AMDclassFrac` vs C2 is significant after BH correction in both sensors (L8
  q = 0.0004, S2 q = 0.031). Its J (+0.235 and +0.049) is still below the 0.25
  bar, and it still fails C1 and C3, so its verdict is unchanged. It now fits the
  pattern the B2 report already describes for the other indices: mine sites
  separate from terrain-matched vegetated land (C2), not from nearby monitored
  water (C1).
- The land-arm J values ("worst-case J = 0.000" for the v2.x σ multipliers, in
  `REPLICA_AUDIT_2026-07-26.md` and `OPERATOR_GUIDE.md`) come from different code
  and were **not checked**.

**Fix.** `amdtool.stats._worst_j_fast` now evaluates J only after the last
member of a tie. That change is the one allowed difference for this function in
`tests/test_source_parity.py`. On tie-free scores the result, and the
permutation RNG stream, are identical to the committed sweep (tested).

---

## 10. The C3b amendment report pooled two different Sentinel-2 composites

**Evidence.** `report_seep_b2_s2_c3b_2026-08-15.txt` prints C2 n = **575** and
C3 n = **578**. The cloud-filtered S2 files give **378** and **430**. Those
counts are reproduced **only** when two extra files are added:
`seep_s2_central_city_co_nocloudfilter.csv` and
`seep_s2_leadville_co_nocloudfilter.csv`.

Those two are composites built **without the cloud filter, from 161 and 138
scenes**. The files used everywhere else were built from **61 and 59**. Their
control points carry different ids, so the loader's de-duplication kept them:
**+197 C2 and +148 C3 rows from a different composite.** This project's own rule
(`extract_buffers`) forbids pooling results from different scene stacks.

**Impact.**
- **Unaffected:** targets (86), C1 (446) and C3b (350) come from the clean files.
  So `FerricIron1` vs C3b +0.318, `NDVI_stress` vs C3b +0.700 and the C1 rows
  stand.
- **Affected:** every C2 and C3 row of that report differs from the clean S2
  report, e.g. `FerricIron1` vs C2 J 0.310 against 0.291, `NDVI_stress` vs C2
  −0.316 against −0.189.
- **Verdicts:** the decision-rule lines are identical in the two reports.
- **Citations:** a search found no document quoting that report's C2/C3 values.
- **B2c** excluded `nocloud` files and printed the clean counts.

**Caveat.** The command that produced the C3b report was not recorded. The input
set is inferred: it is the only one tested that matches all four printed counts.

---

## 11. The B2 reports regenerate, but only in an input order nobody recorded

**Evidence.** The record gives the command as
`seep_detect.py --analyse --inputs <csvs>` and never says in what order.
- **Alphabetical order:** AUC, J and n reproduce, but 17 (L8) and 15 (S2)
  permutation p-values and one tied J do not.
- **REGIONS order** (Silverton, Leadville, Ouray, Central City): the current
  code reproduces **both committed reports byte for byte**.
- **The reports' own commits** (`fa1f7e2`, `c889f9d`), given alphabetical order,
  fail in exactly the same way. The code did not change; the order did.

**Why order matters.**
- **p-values:** the within-region permutation assigns shuffled labels by row
  position, so each order gives a different, equally valid Monte Carlo draw.
- **J itself:** item 9's defect made it order-dependent under ties.

**Impact.** No verdict changes and no q crosses 0.05.

**Rule from here on:** a regeneration command lists its inputs, in order.

---

## Also regenerated (committed code, before the wrapper conversion)

| report | result |
|---|---|
| `report_cmd1_geo30_2026-08-16.txt` | identical |
| `report_cmd2_confound_2026-09-08.txt` | identical |
| `report_seep_b2_doseloro_2026-08-14.txt` | identical |
| `report_cmd3_pa_2026-09-09.txt` | identical for the 23 lines `cmd_detect --analyse` writes. The committed file also has a "RADIUS LADDER (appended 2026-09-09)" block that no recorded command produces. Its values are reproduced independently by `tests/test_golden.py`; its origin is not recorded |

## Documents corrected

- **Corrected in place** (living documents): `ACCURACY_ASSESSMENT.md` §2a
  (C2, C3b), §2b (the baseline) and §2d (the B2b grid); `STATE.md` (the C3b
  bullet and the continuous-vs-binarised bullet).
- **Errata banners, findings left unedited:** `ARM_B2_SEEP_DETECTION_2026-08-14.md`,
  `ARM_B2_SENTINEL2_RESOLUTION_2026-08-15.md`,
  `ARM_B2B_CLASSIFIER_FIX_2026-08-16.md`, `ARM_B2C_CONTINUOUS_2026-08-16.md`.
- **Deliberately not edited:** pre-registrations, which quote the values known
  when they were written, and committed raw reports.
