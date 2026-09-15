"""Golden tests: the library must reproduce committed validation/ numbers.

These are the refactor's behaviour-neutral gate. They read data/ (gitignored,
regenerable from committed code) and skip when it is absent, so a bare clone
still runs the unit tests.

A failure here means the library no longer computes what the committed reports
say it computed - fix the library, never the expected values.
"""
import glob
import io
import math
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED = os.path.join(ROOT, "data", "matched")
VALIDATION = os.path.join(ROOT, "validation")

pytestmark = pytest.mark.golden


def _need(pattern):
    paths = sorted(glob.glob(os.path.join(MATCHED, pattern)))
    if not paths:
        pytest.skip("data/matched/%s not present" % pattern)
    return paths


def _table_line(r):
    return ("  %-16s %-20s %+7.3f %5d %6.0f %8.4f  %s %s"
            % (r.index, r.analyte, r.rho, r.n, r.between_pct, r.p,
               " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(r.per_group.items())),
               "CONSISTENT" if r.sign_consistent else "signs disagree"))


def test_cmd1_30m_report_table_reproduces_line_for_line():
    from amdtool.dose_response import analyse, VERDICT_PARTIAL
    from amdtool.imagery import INDEX_BANDS
    from amdtool.io import load_extracted

    paths = _need("cmdgeo_l8_*.csv")
    report = os.path.join(VALIDATION, "report_cmd1_geo30_2026-08-16.txt")
    rows = [r for r in load_extracted(paths)
            if r.get("tier") == "cmd" and r.get("radius") == 30.0]
    res = analyse(rows, INDEX_BANDS)

    committed = [l.rstrip("\r\n") for l in io.open(report, encoding="utf-8")]
    expected = [l for l in committed
                if l.startswith("  ") and l.split() and l.split()[0] in INDEX_BANDS]

    assert [_table_line(r) for r in res.ranked()] == expected
    assert res.verdict == VERDICT_PARTIAL
    assert round(res.canopy_median_ndvi, 3) == 0.462

    headline = [r for r in res.pairs
                if r.index == "NDVI_stress" and r.analyte == "Sulfate_mgL"][0]
    assert (round(headline.rho, 3), headline.n, round(headline.p, 4)) == (-0.354, 137, 0.0028)


@pytest.mark.parametrize("radius, expected", [
    (30.0, -0.187), (60.0, -0.158), (100.0, -0.138), (500.0, -0.010), (1000.0, 0.003),
])
def test_cmd3_conductance_ladder_reproduces(radius, expected):
    from amdtool.dose_response import analyse
    from amdtool.io import load_extracted

    paths = _need("cmd3geo_l8_*.csv") + _need("cmd3far_l8_*.csv")
    rows = [r for r in load_extracted(paths)
            if r.get("tier") == "cmd" and r.get("radius") == radius]
    # rho does not depend on the permutation count; n_perm=1 keeps this fast.
    res = analyse(rows, ["NDVI_stress"], ("SpecificConductance",), n_perm=1)
    pair = res.pairs[0]
    assert round(pair.rho, 3) == pytest.approx(expected, abs=1e-9)


def _same(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return a == b


def test_cmd2_t1_table_reproduces_and_the_partial_guard_changes_nothing():
    """CMD2 T1, assembled exactly as python/cmd_confound.run_analyse does.

    Two claims checked at once: the library reproduces every committed T1 line
    (partial rho, n, permutation p, attenuation, per-watershed partials), and
    the 2026-09-14 tolerance guard in partial_spearman returns the identical
    value to the legacy guard at every covariate and every watershed - including
    near-collinear Monday Creek, the one place a tolerance could bite.
    """
    import csv
    import random

    from amdtool import stats as S
    from amdtool.io import load_extracted
    cmd_confound = pytest.importorskip("cmd_confound")

    geo = _need("cmdgeo_l8_*.csv")
    conf_csv = os.path.join(MATCHED, "cmdconf.csv")
    if not os.path.isfile(conf_csv):
        pytest.skip("data/matched/cmdconf.csv not present")
    report = os.path.join(VALIDATION, "report_cmd2_confound_2026-09-08.txt")
    nan = float("nan")

    conf = {}
    with io.open(conf_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            def f(k, r=r):
                try:
                    return float(r[k])
                except (TypeError, ValueError):
                    return nan
            conf[(r["region"], r["pid"])] = dict(
                clipped=int(r["clipped"]),
                **{k: f(k) for k in r if k.startswith("minefrac_")})

    rows = [r for r in load_extracted(geo)
            if r.get("tier") == "cmd" and r.get("radius") == cmd_confound.PRIMARY_RADIUS]
    X, Y, Z, G = [], [], [], []
    zdisc = {("minefrac_disc%gkm" % rk): [] for rk in cmd_confound.DISC_RADII_KM}
    zsplit = {"minefrac_surf": [], "minefrac_und": []}
    for r in rows:
        c = conf.get((r["region"], r["pid"]))
        v, s = r.get("NDVI_stress_p90", nan), r.get("Sulfate_mgL", nan)
        if v != v or s != s or c is None:
            continue
        X.append(v)
        Y.append(s)
        Z.append(nan if c["clipped"] else c["minefrac_all"])
        G.append(r["region"])
        for k in zdisc:
            zdisc[k].append(c.get(k, nan))
        for k in zsplit:
            zsplit[k].append(nan if c["clipped"] else c.get(k, nan))

    rng = random.Random(cmd_confound.SEED)
    lines = []
    arms = ([("catchment (PRIMARY)", Z),
             ("catchment surface-only", zsplit["minefrac_surf"]),
             ("catchment underground", zsplit["minefrac_und"])]
            + [("disc %s" % k.split("_")[-1], zdisc[k]) for k in sorted(zdisc)])
    for label, zz in arms:
        if any(v != v for v in zz):
            keep = [i for i, v in enumerate(zz) if v == v]
            xs, ys = [X[i] for i in keep], [Y[i] for i in keep]
            zs, gs = [zz[i] for i in keep], [G[i] for i in keep]
        else:
            xs, ys, zs, gs = X, Y, list(zz), G

        pr = S.partial_spearman(xs, ys, zs)
        assert _same(pr, cmd_confound.partial_spearman(xs, ys, zs)), label
        per = S.per_region(xs, ys, gs, z=zs)
        per_old = cmd_confound._per_region(xs, ys, gs, z=zs)
        assert per.keys() == per_old.keys()
        assert all(_same(per[g], per_old[g]) for g in per), label

        p = S.perm_p_within(xs, ys, zs, gs, pr, cmd_confound.N_PERM, rng)
        _, cons = S.signs(per)
        raw_sub, _ = S.spearman(xs, ys)
        atten = (abs(raw_sub) - abs(pr)) / abs(raw_sub) if raw_sub else nan
        lines.append("  %-24s partial rho=%+.3f  n=%3d  perm_p=%.4f  (raw %+.3f, "
                     "atten %+.0f%%)  %s"
                     % (label, pr, len(xs), p, raw_sub, 100 * atten,
                        "CONSISTENT" if cons else "signs disagree"))
        lines.append("      per-watershed: %s"
                     % " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(per.items())))

    committed = [l.rstrip("\r\n") for l in io.open(report, encoding="utf-8")]
    missing = [l for l in lines if l not in committed]
    assert not missing, "not in the committed CMD2 report:\n" + "\n".join(missing)
    assert "  catchment (PRIMARY)      partial rho=-0.246  n=131" in lines[0]


def test_library_loader_matches_the_legacy_loader():
    from amdtool.io import load_extracted as new
    from seep_detect import load_extracted as old

    paths = _need("cmdgeo_l8_*.csv")
    a, b = new(paths), old(paths)
    assert len(a) == len(b)
    for ra, rb in zip(a, b):
        assert ra.keys() == rb.keys()
        for k in ra:
            va, vb = ra[k], rb[k]
            if isinstance(va, float) and math.isnan(va):
                assert isinstance(vb, float) and math.isnan(vb)
            else:
                assert va == vb
