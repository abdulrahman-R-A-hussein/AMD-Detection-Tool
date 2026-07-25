"""Estimate the optical detection limit for iron in water.

Consumes the matched spectra <-> chemistry table from match_scenes.py and asks
one question: at what concentration, if any, does reflectance start to respond
to iron?

This exists because the water arm's earlier claims were unfalsifiable. Finding
W1 showed the hand-built contamination indices rank the CLEAN control highest;
W4 showed the study lakes carry 0.16-0.30 mg/L Fe, one to two orders below
visible ferric colouring. Rather than assert undetectability, measure it.

Method and its limits:
  * Spearman (rank) correlation, not Pearson - the relationship need not be
    linear and n is small.
  * Bootstrap confidence intervals rather than parametric p-values, because
    repeat visits to the same lake are not independent samples.
  * Turbidity, TSS and chlorophyll are reported alongside iron. If a band
    tracks turbidity better than iron, any apparent "iron detection" is really
    a sediment detection - the exact confound that invalidated finding W3.
  * Iron fractions are NEVER pooled. Total Recoverable includes suspended
    ferric particulates (optically active); Dissolved does not.

A NULL RESULT IS A VALID OUTCOME and should be reported as the measured limit,
not buried.

Usage:
    .venv/Scripts/python python/detection_limit.py
    .venv/Scripts/python python/detection_limit.py --min-water 30
"""

import argparse
import os

import numpy as np
import pandas as pd

MATCHED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "matched", "matched_spectra_chemistry.csv")

BANDS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]


def features(d):
    """Reflectance features: raw bands, diagnostic ratios, albedo-free shape.

    The shape fractions matter most: they remove overall brightness, which is
    what made the Ganau-vs-Atwood comparison uninterpretable (different
    continents, atmospheres and illumination).
    """
    f = pd.DataFrame(index=d.index)
    for b in BANDS:
        f[b] = d[b]
    eps = 1e-6
    f["red_blue"] = d.SR_B4 / (d.SR_B2 + eps)      # ferric staining raises this
    f["green_blue"] = d.SR_B3 / (d.SR_B2 + eps)    # "yellow index"
    f["blue_coastal"] = d.SR_B2 / (d.SR_B1 + eps)
    f["nir"] = d.SR_B5                             # particulate scattering
    f["iron_idx"] = (d.SR_B2 / (d.SR_B1 + eps)) - (d.SR_B5 / (d.SR_B4 + eps))
    vis = d[["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5"]].sum(axis=1) + eps
    for b in ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5"]:
        f["f_" + b[-2:]] = d[b] / vis
    return f


def spearman(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 5:
        return np.nan, 0
    xr = pd.Series(x[m]).rank().to_numpy()
    yr = pd.Series(y[m]).rank().to_numpy()
    if xr.std() == 0 or yr.std() == 0:
        return np.nan, int(m.sum())
    return float(np.corrcoef(xr, yr)[0, 1]), int(m.sum())


def boot_ci(x, y, n=2000, seed=0):
    m = x.notna() & y.notna()
    xv, yv = x[m].to_numpy(), y[m].to_numpy()
    if len(xv) < 6:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        i = rng.integers(0, len(xv), len(xv))
        a, b = pd.Series(xv[i]).rank().to_numpy(), pd.Series(yv[i]).rank().to_numpy()
        if a.std() and b.std():
            out.append(np.corrcoef(a, b)[0, 1])
    if not out:
        return (np.nan, np.nan)
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def report(d, target, label):
    y = d[target]
    ok = y.notna()
    if ok.sum() < 6:
        print("\n%s: only %d usable rows - too few to test." % (label, int(ok.sum())))
        return
    f = features(d)
    print("\n" + "=" * 74)
    print("%s   n=%d   range %.1f - %.1f   median %.1f"
          % (label, int(ok.sum()), y[ok].min(), y[ok].max(), y[ok].median()))
    print("=" * 74)
    print("  %-14s %7s %7s %20s" % ("feature", "rho", "n", "95% CI (bootstrap)"))
    rows = []
    for name in f.columns:
        r, n = spearman(f[name], y)
        if np.isnan(r):
            continue
        lo, hi = boot_ci(f[name], y)
        rows.append((abs(r), name, r, n, lo, hi))
    for _, name, r, n, lo, hi in sorted(rows, reverse=True)[:10]:
        sig = "" if (np.isnan(lo) or lo <= 0 <= hi) else "  <- CI excludes 0"
        print("  %-14s %7.3f %7d   [%6.3f, %6.3f]%s" % (name, r, n, lo, hi, sig))
    if rows and all(np.isnan(lo) or lo <= 0 <= hi for _, _, _, _, lo, hi in rows):
        print("\n  No feature's confidence interval excludes zero: no detectable")
        print("  response at these concentrations. This IS the result.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matched", default=MATCHED)
    ap.add_argument("--min-water", type=int, default=10,
                    help="drop rows whose window held fewer clean water pixels")
    ap.add_argument("--max-offset", type=int, default=5,
                    help="drop rows whose scene is further than this many days "
                         "from the sample")
    args = ap.parse_args(argv)

    d = pd.read_csv(args.matched)
    n0 = len(d)
    d = d[(d.n_water.fillna(0) >= args.min_water)
          & (d.day_offset.abs() <= args.max_offset)]
    print("%d matched rows, %d kept (n_water>=%d, |offset|<=%dd)"
          % (n0, len(d), args.min_water, args.max_offset))
    if "sensor" in d:
        print("sensors:", dict(d.sensor.value_counts()))
    print("lakes:", dict(d.lake.value_counts()))

    for col, label in [("Iron_TotalRecoverable", "IRON - Total Recoverable (ug/L)"),
                       ("Iron_Dissolved", "IRON - Dissolved (ug/L)"),
                       ("Sulfate", "SULFATE (mg/L)"),
                       ("Turbidity", "TURBIDITY (NTU) - confound check"),
                       ("Chlorophyll a", "CHLOROPHYLL a - confound check")]:
        if col in d.columns:
            report(d, col, label)

    print("\n" + "-" * 74)
    print("Read the confound checks before believing any iron result: if a band")
    print("tracks turbidity or chlorophyll more strongly than iron, it is")
    print("detecting sediment or algae, not acid mine drainage.")


if __name__ == "__main__":
    main()
