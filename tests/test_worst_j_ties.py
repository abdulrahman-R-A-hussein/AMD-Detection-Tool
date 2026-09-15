"""Worst-case leave-one-region-out Youden J under tied scores (audit 2026-09-15, item 9).

A `>=` threshold cannot fall between two equal scores. The sweep inherited from
python/seep_detect.py evaluated J after every element, including part-way
through a run of tied scores, so the chosen cut - and the held-out J - depended
on the order rows arrived in. AMDclassFrac, a fraction with 18-95% tied values,
was the only index affected; the continuous indices are unchanged.
"""
import os
import random

import pytest

from amdtool import stats
from amdtool.io import load_extracted

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED = os.path.join(ROOT, "data", "matched")
REGIONS_ORDER = ("silverton_co", "leadville_co", "ouray_co", "central_city_co")


def reference_worst_j(scores, labels, regions):
    """Brute force: every distinct training score is a candidate `>=` cut; the
    highest cut wins ties in J (the sweep's own tie-break); apply it to the
    held-out region."""
    worst, per = None, {}
    for held in sorted(set(regions)):
        tr = [i for i, r in enumerate(regions) if r != held]
        te = [i for i, r in enumerate(regions) if r == held]
        p_tr = sum(labels[i] for i in tr)
        n_tr = len(tr) - p_tr
        p_te = sum(labels[i] for i in te)
        n_te = len(te) - p_te
        if not (p_tr and n_tr and p_te and n_te):
            continue
        best_j, cut = -2.0, None
        for c in sorted({scores[i] for i in tr}, reverse=True):
            tp = sum(1 for i in tr if scores[i] >= c and labels[i])
            fp = sum(1 for i in tr if scores[i] >= c and not labels[i])
            j = tp / p_tr - fp / n_tr
            if j > best_j:
                best_j, cut = j, c
        tp = sum(1 for i in te if scores[i] >= cut and labels[i])
        fp = sum(1 for i in te if scores[i] >= cut and not labels[i])
        per[held] = tp / p_te - fp / n_te
        worst = per[held] if worst is None else min(worst, per[held])
    return (worst if worst is not None else float("nan")), per


def _tied_sample(rng, n=160, levels=6):
    regions = [rng.choice("ABCD") for _ in range(n)]
    labels = [1 if rng.random() < 0.3 else 0 for _ in range(n)]
    scores = [round(rng.randrange(levels) / levels + 0.3 * lab * rng.random(), 1)
              for lab in labels]
    return scores, labels, regions


def _shuffled(rng, *cols):
    idx = list(range(len(cols[0])))
    rng.shuffle(idx)
    return [[c[i] for i in idx] for c in cols]


@pytest.mark.parametrize("seed", range(40))
def test_equals_brute_force_on_tied_scores(seed):
    s, l, g = _tied_sample(random.Random(seed))
    assert stats.loro_worst_j(s, l, g) == reference_worst_j(s, l, g)


@pytest.mark.parametrize("seed", range(20))
def test_row_order_cannot_change_the_answer(seed):
    rng = random.Random(seed)
    s, l, g = _tied_sample(rng)
    base = stats.loro_worst_j(s, l, g)
    for _ in range(10):
        assert stats.loro_worst_j(*_shuffled(rng, s, l, g)) == base


def test_the_committed_sweep_really_was_order_dependent(legacy):
    seep = legacy("seep_detect")
    for seed in range(300):
        rng = random.Random(seed)
        s, l, g = _tied_sample(rng)
        if seep.loro_worst_j(s, l, g)[0] != seep.loro_worst_j(*_shuffled(rng, s, l, g))[0]:
            return
    pytest.fail("no order dependence found in the committed sweep on 300 tied samples")


@pytest.mark.parametrize("seed", range(20))
def test_continuous_scores_are_unchanged_from_the_committed_sweep(seed, legacy):
    seep = legacy("seep_detect")
    rng = random.Random(1000 + seed)
    g = [rng.choice("ABCD") for _ in range(150)]
    l = [1 if rng.random() < 0.35 else 0 for _ in g]
    s = [rng.gauss(0.6 * lab, 1.0) for lab in l]
    assert stats.loro_worst_j(s, l, g) == seep.loro_worst_j(s, l, g)


def test_permutation_p_is_unchanged_for_continuous_scores(legacy):
    seep = legacy("seep_detect")
    rng = random.Random(7)
    g = [rng.choice("ABCD") for _ in range(120)]
    l = [1 if rng.random() < 0.35 else 0 for _ in g]
    s = [rng.gauss(0.3 * lab, 1.0) for lab in l]
    obs = stats.loro_worst_j(s, l, g)[0]
    a, b = random.Random(20260814), random.Random(20260814)
    assert stats.perm_p_within_region(s, l, g, obs, 200, a) == \
        seep.perm_p_within_region(s, l, g, obs, 200, b)
    assert a.random() == b.random()


# ---- the corrected archive values (need the gitignored extractions) --------

def _rows(pattern):
    paths = [os.path.join(MATCHED, pattern % d) for d in REGIONS_ORDER]
    if not all(os.path.isfile(p) for p in paths):
        pytest.skip("%s not present" % pattern)
    return load_extracted(paths)


def _vs(rows, key, tier):
    sel = [r for r in rows if r["radius"] == 60 and r["tier"] in ("target", tier)
           and r["region"] in REGIONS_ORDER and r.get(key) == r.get(key)]
    return ([r[key] for r in sel], [1 if r["tier"] == "target" else 0 for r in sel],
            [r["region"] for r in sel])


@pytest.mark.parametrize("sensor,tier,expected", [
    ("l8", "C1", 0.032), ("l8", "C2", 0.235), ("l8", "C3", -0.304),
    ("s2", "C1", 0.004), ("s2", "C2", 0.049), ("s2", "C3", -0.304),
])
def test_b2_amdclassfrac_tie_correct_worst_j(sensor, tier, expected):
    j, _ = stats.loro_worst_j(*_vs(_rows("seep_" + sensor + "_%s.csv"), "AMDclassFrac_p90", tier))
    assert j == pytest.approx(expected, abs=5e-4)


def test_b2b_sweep_tie_correct_worst_j_is_never_positive():
    rows = _rows("seep_v4_%s.csv")
    got = []
    for k_bare in (0.5, 1.0, 1.5, 2.0):
        for clay in (0.25, 0.5):
            sel = [r for r in rows if r.get("k_bare") == k_bare and r.get("clay_bare") == clay
                   and r.get("AMDclassFrac_v4_p90") == r.get("AMDclassFrac_v4_p90")]
            j, _ = stats.loro_worst_j([r["AMDclassFrac_v4_p90"] for r in sel],
                                      [1 if r["tier"] == "target" else 0 for r in sel],
                                      [r["region"] for r in sel])
            got.append(round(j, 3))
    assert got == [-0.452, -0.443, 0.0, 0.0, 0.0, 0.0, -0.087, -0.087]
