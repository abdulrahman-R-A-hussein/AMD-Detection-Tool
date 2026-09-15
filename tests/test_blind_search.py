"""The blind-search analysis, exercised on SYNTHETIC districts only.

Written before the analysis was run on real data. Every expectation below comes
from validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md, not from any
outcome. The one real input is the committed site list, which holds station
metadata and no scores.
"""
import math
import os
import random

import pytest

from amdtool import blind_search as bs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES_CSV = os.path.join(ROOT, "validation", "blind_search_sites_2026-09-14.csv")
NAN = float("nan")


def _landscape(n=2000, lat=0.0):
    # FerricIron1 rises and -NDVI falls along the sample, so the two cutoffs differ
    return [{"pid": "LS%05d" % i, "FerricIron1_p90": i / n, "NDVI_stress_mean": 1 - i / n,
             "lat": lat + i * 1e-3, "lon": 0.0} for i in range(n)]


def _st(score, ndvi):
    return {"FerricIron1_p90": score, "NDVI_stress_mean": ndvi}


def _scenario():
    S = bs.Site
    sites = [
        S("H-BS1", "A", "A1", True, ["a1"]),            # FerricIron1 flags, baseline does not
        S("H-BS1", "A", "A2", True, ["a2"]),            # baseline flags only
        S("H-BS1", "A", "A3", True, ["a3", "a3b"]),     # max over stations; one unscoreable
        S("H-BS1", "A", "A4", False, ["a4"]),           # spring-only: sensitivity set
        S("H-BS1", "A", "A5", True, ["a5"]),            # no scoreable station
        S("H-BS1", "B", "B1", True, ["b1"]),            # district B failed
        S("H-BS2", "C", "C1", True, ["c1"]),
    ]
    rows = {
        "A": {"landscape": _landscape(), "stations": {
            "a1": _st(0.99, 0.90), "a2": _st(0.10, 0.01), "a3": _st(NAN, NAN),
            "a3b": _st(0.97, 0.02), "a4": _st(0.99, 0.90), "a5": _st(NAN, NAN)}},
        "C": {"landscape": _landscape(), "stations": {"c1": _st(0.20, 0.50)}},
    }
    return sites, rows


def test_cutoff_is_numpy_linear_quantile_and_labels_never_enter():
    land = _landscape()
    cut, n = bs.landscape_cutoff(land, bs.primary_score, 0.05)
    assert n == 2000
    # linear quantile: position 0.95 x (2000 - 1) = 1899.05 between 1899/2000 and 1900/2000
    assert cut == pytest.approx(0.949525)
    land[5]["FerricIron1_p90"] = NAN               # a point with no valid pixel is dropped
    assert bs.landscape_cutoff(land, bs.primary_score, 0.05)[1] == 1999


def test_primary_evaluation_follows_the_registration():
    sites, rows = _scenario()
    r = bs.evaluate(sites, rows, 0.05, "H-BS1")
    assert r.failed_districts == ["B"]             # section 11: sites removed, listed
    assert r.n == 4                                # A1, A2, A3, A5 (A4 spring-only excluded)
    assert r.unscoreable == 1                      # A5: counted, NOT flagged (section 4)
    assert r.k == 2                                # A1, and A3 through its best station
    assert r.k_baseline == 2                       # A2, A3
    assert (r.b, r.c) == (1, 1)
    assert r.p_binomial == pytest.approx(1 - 0.95 ** 4 - 4 * 0.05 * 0.95 ** 3)


def test_sensitivities_change_only_what_they_name():
    sites, rows = _scenario()
    assert bs.evaluate(sites, rows, 0.05, "H-BS1", site_set="all").n == 5
    assert bs.evaluate(sites, rows, 0.05, "H-BS1", unscoreable="exclude").n == 3
    assert bs.evaluate(sites, rows, 0.05, "H-BS1", how="median").k == 2


def test_holm_and_mcnemar_verdict_rows():
    def res(h, p, b, c):
        r = bs.HypothesisResult(h, 0.05, 32, 8, 0.25, (0, 1), p, 3, b, c,
                                bs.stats.mcnemar_exact_greater(b, c), 0, [], {})
        return r
    # both rejected; H-BS1 beats bare ground, H-BS2 does not
    out = bs.apply_verdicts({"H-BS1": res("H-BS1", 0.001, 6, 0), "H-BS2": res("H-BS2", 0.03, 1, 1)})
    assert out["H-BS1"].holm_level == 0.025 and out["H-BS1"].verdict == bs.VERDICT_DISCOVERY
    assert out["H-BS2"].holm_level == 0.05 and out["H-BS2"].verdict == bs.VERDICT_BARE
    # first not rejected: the second is never tested, however small its p
    out = bs.apply_verdicts({"H-BS1": res("H-BS1", 0.04, 6, 0), "H-BS2": res("H-BS2", 0.03, 6, 0)})
    assert out["H-BS2"].holm_level == 0.025 and not out["H-BS2"].rejected
    assert out["H-BS1"].holm_level is None and not out["H-BS1"].rejected
    assert {v.verdict for v in out.values()} == {bs.VERDICT_NONE}
    # equal p: H-BS1 is tested first
    out = bs.apply_verdicts({"H-BS1": res("H-BS1", 0.01, 0, 0), "H-BS2": res("H-BS2", 0.01, 0, 0)})
    assert out["H-BS1"].holm_level == 0.025 and out["H-BS2"].holm_level == 0.05
    # no discordant pairs: McNemar p = 1, so a rejected hypothesis is NOT BETTER THAN BARE GROUND
    assert out["H-BS1"].verdict == bs.VERDICT_BARE
    # an untestable hypothesis (n = 0, p NaN) never rejects
    nan_res = res("H-BS1", NAN, 0, 0)
    out = bs.apply_verdicts({"H-BS1": nan_res, "H-BS2": res("H-BS2", 0.001, 5, 0)})
    assert out["H-BS2"].rejected and not out["H-BS1"].rejected


def test_power_table_matches_the_registration():
    assert bs.critical_k(32, 0.05, 0.025) == 5
    assert [round(bs.power(32, 0.05, 0.025, r), 2) for r in (0.15, 0.20, 0.30)] == [0.54, 0.80, 0.98]
    assert [round(bs.power(50, 0.05, 0.025, r), 2) for r in (0.15, 0.20, 0.30)] == [0.64, 0.90, 1.00]


def test_relinking_at_250_m_reproduces_the_registered_sites():
    sites = bs.load_sites(SITES_CSV)
    registered = {(s.hypothesis, frozenset(s.station_ids), s.has_mine) for s in sites}
    relinked = {(s.hypothesis, frozenset(s.station_ids), s.has_mine)
                for s in bs.relink_sites(sites, 250.0)}
    assert relinked == registered


def test_relinking_only_regroups_the_same_stations():
    sites = bs.load_sites(SITES_CSV)
    stations = {(s.hypothesis, sid) for s in sites for sid in s.station_ids}
    n250 = len(sites)
    for link in (100.0, 500.0):
        re = bs.relink_sites(sites, link)
        assert {(s.hypothesis, sid) for s in re for sid in s.station_ids} == stations
    assert len(bs.relink_sites(sites, 100.0)) >= n250 >= len(bs.relink_sites(sites, 500.0))


def test_registered_primary_site_counts():
    sites = bs.load_sites(SITES_CSV)
    count = {h: sum(1 for s in sites if s.hypothesis == h and s.has_mine) for h in ("H-BS1", "H-BS2", "T-86")}
    assert count == {"H-BS1": 32, "H-BS2": 50, "T-86": 37}


def test_sampling_frame_excludes_near_stations_and_allocates_by_largest_remainder():
    rows = {"A": {"landscape": _landscape(lat=10.0)}, "C": {"landscape": _landscape(lat=20.0)}}
    # the top 5% of each district is 100 points spaced ~111 m apart - one 250 m chain each
    drawn, counts = bs.sampling_frame(rows, {"A": [], "C": []})
    assert counts == {"A": 1, "C": 1} and len(drawn) == 2
    # a WQP station next to district A's flagged points removes them all
    near = [{"lat": p["lat"], "lon": 0.0} for p in rows["A"]["landscape"][1900:]]
    drawn, counts = bs.sampling_frame(rows, {"A": near, "C": []})
    assert counts["A"] == 0 and all(d["district"] == "C" for d in drawn)


def test_sampling_frame_quota_and_determinism():
    rng = random.Random(3)
    rows = {}
    for d, n_clusters in (("A", 7), ("B", 50), ("C", 13)):
        land = []
        for i in range(2000):
            flagged = i >= 2000 - n_clusters
            land.append({"pid": "%s%d" % (d, i), "FerricIron1_p90": 1.0 if flagged else rng.random() * 0.5,
                         "NDVI_stress_mean": 0.5, "lat": 30.0 + i * 0.05, "lon": 0.0})
        rows[d] = {"landscape": land}
    drawn, counts = bs.sampling_frame(rows, {})
    assert len(drawn) == 40                                         # FRAME_N
    alloc = {d: sum(1 for x in drawn if x["district"] == d) for d in rows}
    total = sum(counts.values())
    assert all(abs(alloc[d] - 40 * counts[d] / total) < 1 for d in rows)   # largest remainder
    assert bs.sampling_frame(rows, {})[0] == drawn                  # seed 20260915, deterministic


def test_frame_notice_says_when_visits_are_not_supported():
    none = bs.HypothesisResult("H-BS1", 0.05, 1, 0, 0.0, (0, 1), 1.0, 0, 0, 0, 1.0, 0, [], {},
                               verdict=bs.VERDICT_NONE)
    other = bs.HypothesisResult("H-BS2", 0.05, 1, 0, 0.0, (0, 1), 1.0, 0, 0, 0, 1.0, 0, [], {},
                                verdict=bs.VERDICT_NONE)
    assert "NOT supported" in bs.frame_notice({"H-BS1": none, "H-BS2": other})
    other.verdict = bs.VERDICT_DISCOVERY
    msg = bs.frame_notice({"H-BS1": none, "H-BS2": other})
    assert "NOT supported" not in msg and bs.VERDICT_DISCOVERY in msg
