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


def test_within_region_permutation_p_is_rng_identical_to_legacy(legacy):
    seep = legacy("seep_detect")
    _, _, sc, lb, rg = _detection(_rows("l8"), "C1")    # worst J -0.018, p 0.197
    wj_new, per_new = stats.loro_worst_j(sc, lb, rg)
    wj_old, per_old = seep.loro_worst_j(sc, lb, rg)
    assert (wj_new, per_new) == (wj_old, per_old)
    r_new, r_old = random.Random(SEED), random.Random(SEED)
    p_new = stats.perm_p_within_region(sc, lb, rg, wj_new, 300, r_new)
    p_old = seep.perm_p_within_region(sc, lb, rg, wj_old, 300, r_old)
    assert p_new == p_old
    assert 0.02 < p_new < 0.9                      # a p that actually exercises the null
    assert r_new.random() == r_old.random()        # identical RNG consumption
