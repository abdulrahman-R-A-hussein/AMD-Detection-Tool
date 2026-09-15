"""Arm B2's committed numbers, rebuilt from the raw extractions with amdtool.

Reads data/matched/seep_{l8,s2}_*.csv (gitignored) and skips without them.
Every assertion compares against a committed validation/ report line, except
the permutation p-values: the reports' p came from one shared RNG stream across
all 27 tests at 10,000 permutations, so p is instead proven RNG-identical to
python/seep_detect.py as committed before the refactor.
"""
import os
import random
import statistics

import pytest

from amdtool import stats
from amdtool.io import load_extracted

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED = os.path.join(ROOT, "data", "matched")
DISTRICTS = ("central_city_co", "leadville_co", "ouray_co", "silverton_co")
SEED = 20260814
KEY = "FerricIron1_p90"


def _rows(sensor):
    paths = [os.path.join(MATCHED, "seep_%s_%s.csv" % (sensor, d)) for d in DISTRICTS]
    if not all(os.path.isfile(p) for p in paths):
        pytest.skip("data/matched/seep_%s_*.csv not present" % sensor)
    return [r for r in load_extracted(paths)
            if r["radius"] == 60 and r["region"] in DISTRICTS]


def _report_line(name, needle):
    with open(os.path.join(ROOT, "validation", name), encoding="utf-8") as fh:
        hits = [ln.rstrip("\n") for ln in fh if needle in ln]
    assert len(hits) == 1, hits
    return hits[0]


def _finite(v):
    return v == v


def _detection(rows, tier):
    pos, neg, sc, lb, rg = [], [], [], [], []
    for r in rows:
        v = r.get(KEY, float("nan"))
        if not _finite(v):
            continue
        if r["tier"] == "target":
            pos.append(v); sc.append(v); lb.append(1); rg.append(r["region"])
        elif r["tier"] == tier:
            neg.append(v); sc.append(v); lb.append(0); rg.append(r["region"])
    return pos, neg, sc, lb, rg


def test_s2_ferriciron1_vs_c1_worst_case_j_is_0_234():
    pos, neg, sc, lb, rg = _detection(_rows("s2"), "C1")
    fields = _report_line("report_seep_b2_s2_2026-08-15.txt",
                          "S2      FerricIron1     C1").split()
    wj, _ = stats.loro_worst_j(sc, lb, rg)
    assert fields[3] == "%.3f" % stats.auc(pos, neg)        # 0.723
    assert fields[4] == "%.3f" % wj == "0.234"
    assert fields[7:] == [str(len(pos)), str(len(neg))]     # 86 446


def test_l8_ferriciron1_dose_response_line_reproduces():
    xs, ys, rg = [], [], []
    for r in _rows("l8"):
        if r["tier"] != "target":
            continue
        a, b = r.get(KEY, float("nan")), r.get("Iron_mgL_dissolved", float("nan"))
        if _finite(a) and _finite(b):
            xs.append(a); ys.append(b); rg.append(r["region"])
    rho, n = stats.spearman(xs, ys)
    line = ("  %-7s %-15s %-20s rho=%+.3f n=%-3d between-region var=%.0f%%"
            % ("L8", "FerricIron1", "Iron_mgL_dissolved", rho, n,
               100 * stats.variance_split(ys, rg)))
    assert line == _report_line("report_seep_b2_l8_2026-08-14.txt",
                                "L8      FerricIron1     Iron_mgL_dissolved")


def test_l8_dose_response_is_positive_in_all_four_districts_and_fails_loro():
    """The line that bounds the metal_mine preset's claim: signs agree, R2 < 0."""
    pts = [(r[KEY], r["Iron_mgL_dissolved"], r["region"]) for r in _rows("l8")
           if r["tier"] == "target" and _finite(r.get(KEY, float("nan")))
           and _finite(r.get("Iron_mgL_dissolved", float("nan")))]
    regs = sorted({p[2] for p in pts})
    pooled, _ = stats.spearman([p[0] for p in pts], [p[1] for p in pts])
    per = {g: stats.spearman([s[0] for s in pts if s[2] == g],
                             [s[1] for s in pts if s[2] == g])[0]
           for g in regs if sum(1 for s in pts if s[2] == g) >= 5}
    ss_res = ss_tot = 0.0                     # the committed LORO R2, verbatim
    for held in regs:
        tr = [p for p in pts if p[2] != held]
        te = [p for p in pts if p[2] == held]
        if len(tr) < 10 or len(te) < 3:
            continue
        mx = statistics.mean(p[0] for p in tr)
        my = statistics.mean(p[1] for p in tr)
        den = sum((p[0] - mx) ** 2 for p in tr)
        if den <= 0:
            continue
        b = sum((p[0] - mx) * (p[1] - my) for p in tr) / den
        a = my - b * mx
        mte = statistics.mean(p[1] for p in te)
        ss_res += sum((p[1] - (a + b * p[0])) ** 2 for p in te)
        ss_tot += sum((p[1] - mte) ** 2 for p in te)
    r2 = 1 - ss_res / ss_tot
    sgn = ("ALL +" if all(v > 0 for v in per.values())
           else "ALL -" if all(v < 0 for v in per.values()) else "*** SIGNS DISAGREE ***")
    line = ("  %-15s %-20s %+7.3f %8.3f  %s  [%s]"
            % ("FerricIron1", "Iron_mgL_dissolved", pooled, r2,
               " ".join("%s=%+.2f" % (g[:4], v) for g, v in sorted(per.items())), sgn))
    assert line == _report_line("report_seep_b2_doseloro_2026-08-14.txt",
                                "FerricIron1     Iron_mgL_dissolved")


REGIONS_ORDER = ("silverton_co", "leadville_co", "ouray_co", "central_city_co")


@pytest.mark.parametrize("index,analyte,rho,n,p,q,between", [
    ("FerricIron1", "Iron_mgL_dissolved", "+0.568", 75, "0.0004", "0.0072", "24"),
    ("FerricIron1", "Iron_mgL_any", "+0.558", 82, "0.0004", "0.0072", "25"),
    ("FerricIron2", "pH", "-0.488", 77, "0.0006", "0.0072", "46"),
    ("FerricIron1", "pH", "-0.554", 77, "0.0034", "0.0302", "46"),
    ("FerricIron2", "Iron_mgL_dissolved", "+0.427", 75, "0.0042", "0.0302", "24"),
])
def test_b2_dose_response_table_p_and_q_reproduce(index, analyte, rho, n, p, q, between):
    """ARM_B2_SEEP_DETECTION_2026-08-14.md Part 2: 36 tests, within-district
    permutation, 5,000 draws. Its p and q were in no committed raw output; this
    regenerates them from committed code (python/b2_dose_response_regen.py)."""
    from amdtool import dose_response

    paths = [os.path.join(MATCHED, "seep_l8_%s.csv" % d) for d in REGIONS_ORDER]
    if not all(os.path.isfile(x) for x in paths):
        pytest.skip("data/matched/seep_l8_*.csv not present")
    rows = [r for r in load_extracted(paths) if r["radius"] == 60 and r["tier"] == "target"]
    res = _dose_family(rows, dose_response)
    got = {(x.index, x.analyte): x for x in res.pairs}[(index, analyte)]
    assert len(res.pairs) == 36
    assert ("%+.3f" % got.rho, got.n, "%.4f" % got.p, "%.4f" % got.q, "%.0f" % got.between_pct) == \
        (rho, n, p, q, between)


_FAMILY_CACHE = {}


def _dose_family(rows, dose_response):
    if "res" not in _FAMILY_CACHE:
        _FAMILY_CACHE["res"] = dose_response.analyse(
            rows, ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron", "ClaySulfateMica",
                   "GreenNIR", "GreenNIRNorm", "NDVI_stress", "AMDclassFrac"],
            ("Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH"),
            stat="p90", group_key="region", n_perm=5000, seed=SEED, min_n=10,
            min_group_n=5, canopy_limit=None)
    return _FAMILY_CACHE["res"]


def test_l8_ferriciron1_vs_c1_committed_and_tie_corrected(legacy):
    """36% of these scores are tied (co-located in-stream stations share a buffer).
    The committed sweep reproduces the report's -0.018; the tie-corrected sweep
    gives -0.019 (audit 2026-09-15, item 9). Permutation p stays RNG-identical on
    tie-free scores - proven in tests/test_worst_j_ties.py."""
    seep = legacy("seep_detect")
    _, _, sc, lb, rg = _detection(_rows("l8"), "C1")
    fields = _report_line("report_seep_b2_l8_2026-08-14.txt", "L8      FerricIron1     C1").split()
    assert fields[4] == "%.3f" % seep.loro_worst_j(sc, lb, rg)[0] == "-0.018"
    assert "%.3f" % stats.loro_worst_j(sc, lb, rg)[0] == "-0.019"
    r = random.Random(SEED)
    p = stats.perm_p_within_region(sc, lb, rg, stats.loro_worst_j(sc, lb, rg)[0], 300, r)
    assert 0.02 < p < 0.9                            # still nowhere near significant
