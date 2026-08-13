"""Arm A, Part B3: pool all regions and re-test with the L1 lesson applied.

Finding L1 (validation/STATE.md): a threshold or correlation judged only
within the sample it was found in is not validated. Test C's 0.99 AUCs were
Silverton-only and collapsed pooled. The n=6 Arm A headline (rho=0.714,
p=0.136 at Silverton alone) must not be allowed to repeat that mistake by
simply adding more catchments and reporting a bigger pooled rho as if that
settles it - pooling across river systems (different geology, climate,
illumination, scene availability) can manufacture a correlation as easily as
reveal one.

This module reads every data/matched/watershed_nap_*.csv produced by
watershed_nap.py (one file per region, each tagged with a `region` column) and
reports THREE things, never just the first:

  1. POOLED   - Spearman rho + a large-sample permutation p-value (exact
                enumeration is only tractable to n~8; above that this samples
                100,000 random permutations and says so).
  2. PER-REGION - rho for each region with n>=4 catchments, so a single region
                driving the whole pooled result is visible, not hidden.
  3. LEAVE-ONE-REGION-OUT R^2 - fit a linear model on every region EXCEPT one,
                predict the held-out region's chemistry from its loading, pool
                the squared residuals across every region's turn as the
                held-out set. This is the real test: does a relationship
                learned in five river systems predict the sixth? Leave-one-
                CATCHMENT-out (what watershed_nap.py's per-run report does) is
                not equivalent - catchments within one region share geology,
                so it can look validated while still being one system's quirk.

A COLLAPSE AT HIGHER n IS A VALID, IMPORTANT OUTCOME and is reported exactly
as prominently as a confirmation would be - this module does not have a
"success" path and a "failure" path, only a report.

    .venv/Scripts/python python/pool_watershed_nap.py
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED_DIR = os.path.join(ROOT, "data", "matched")
CHEM_VARS = ["Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH",
            "SpecificConductance"]
LOADINGS = [("ours_m1", "ours M1 (AMD%)"), ("ours_m2", "ours M2 (NAP-w)"),
           ("rockwell_m1", "rockwell M1"), ("rockwell_m2", "rockwell M2")]


def load_all(pattern):
    paths = sorted(glob.glob(os.path.join(MATCHED_DIR, pattern)))
    if not paths:
        raise SystemExit("no watershed_nap_*.csv found in %s - run "
                         "watershed_nap.py first" % MATCHED_DIR)
    frames = []
    for p in paths:
        d = pd.read_csv(p)
        if "region" not in d.columns:
            # pre-2026-08-13 files predate the region column
            d["region"] = os.path.basename(p).replace("watershed_nap_", "") \
                .replace(".csv", "")
        frames.append(d)
        print("  %-42s %3d catchments  region(s): %s"
              % (os.path.basename(p), len(d), ", ".join(sorted(d.region.unique()))))
    d = pd.concat(frames, ignore_index=True)
    before = len(d)
    d = d.drop_duplicates(subset=["region", "basin_id"])
    if len(d) < before:
        print("  dropped %d duplicate (region, basin_id) rows" % (before - len(d)))
    return d


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    n = len(x)
    if n < 4:
        return float("nan"), n
    rx, ry = _rank(x), _rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan"), n
    return float(np.corrcoef(rx, ry)[0, 1]), n


def _rank(a):
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1)
    s = a[order]
    i = 0
    r = ranks[order]
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[i:j + 1] = r[i:j + 1].mean()
        i = j + 1
    ranks[order] = r
    return ranks


def permutation_p(x, y, n_perm=100_000, seed=0):
    """Two-sided permutation p-value for Spearman rho.

    Exact enumeration (n! permutations) is only tractable to about n=8-9;
    above that this draws n_perm random permutations of y and asks how often
    |rho(x, perm(y))| >= |rho(x, y)| observed. Reports which method was used.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    n = len(x)
    if n < 4:
        return float("nan"), n, "n/a"
    rho_obs, _ = spearman(x, y)
    if np.isnan(rho_obs):
        return float("nan"), n, "n/a"

    if n <= 8:
        import itertools
        rhos = []
        for perm in itertools.permutations(range(n)):
            r, _ = spearman(x, y[list(perm)])
            rhos.append(r)
        rhos = np.array(rhos)
        p = float(np.mean(np.abs(rhos) >= abs(rho_obs) - 1e-9))
        return p, n, "exact (%d perms)" % len(rhos)

    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        yp = rng.permutation(y)
        r, _ = spearman(x, yp)
        if not np.isnan(r) and abs(r) >= abs(rho_obs):
            count += 1
    p = count / n_perm
    return p, n, "random (%d perms, seed=%d)" % (n_perm, seed)


def leave_one_region_out_r2(d, xcol, ycol):
    """Fit linear model on every region EXCEPT one, predict the held-out
    region's y from its x, pool squared residuals across every region's turn
    as the held-out set. Returns (r2, n_used, n_regions_evaluated)."""
    sub = d[[xcol, ycol, "region"]].dropna()
    regions = sorted(sub.region.unique())
    if len(regions) < 3:
        return float("nan"), len(sub), len(regions)

    preds, actuals = [], []
    n_eval = 0
    for held_out in regions:
        train = sub[sub.region != held_out]
        test = sub[sub.region == held_out]
        if len(train) < 4 or len(test) < 1:
            continue
        if train[xcol].std() == 0:
            continue
        b1, b0 = np.polyfit(train[xcol].to_numpy(), train[ycol].to_numpy(), 1)
        preds.extend(b0 + b1 * test[xcol].to_numpy())
        actuals.extend(test[ycol].to_numpy())
        n_eval += 1
    if n_eval < 2 or not preds:
        return float("nan"), len(sub), n_eval
    preds, actuals = np.array(preds), np.array(actuals)
    ss_res = np.sum((actuals - preds) ** 2)
    ss_tot = np.sum((actuals - actuals.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(r2), len(sub), n_eval


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="watershed_nap_*.csv",
                    help="glob (relative to data/matched/) of files to pool")
    ap.add_argument("--exclude-region", action="append", default=[],
                    help="drop a region entirely (repeatable) - e.g. to test "
                         "sensitivity to one region's inclusion")
    ap.add_argument("--n-perm", type=int, default=100_000)
    args = ap.parse_args(argv)

    print("Loading catchment files:")
    d = load_all(args.pattern)
    if args.exclude_region:
        before = len(d)
        d = d[~d.region.isin(args.exclude_region)]
        print("excluded %s: %d -> %d rows" % (args.exclude_region, before, len(d)))

    regions = sorted(d.region.unique())
    print("\n%d catchments total across %d region(s): %s"
          % (len(d), len(regions), ", ".join(regions)))
    print("catchments per region: %s"
          % dict(d.region.value_counts().sort_index()))

    print("\n" + "=" * 100)
    print("1. POOLED (n=%d catchments) - primary headline number, but see 2 and 3 before believing it"
          % len(d))
    print("=" * 100)
    print("  %-24s %-16s %6s %9s %9s %-28s" %
          ("chemistry var", "loading", "n", "rho", "p", "p-method"))
    pooled_results = {}
    for var in CHEM_VARS:
        if var not in d.columns or d[var].notna().sum() < 4:
            continue
        for key, label in LOADINGS:
            if key not in d.columns:
                continue
            rho, n = spearman(d[key], d[var])
            if np.isnan(rho):
                continue
            p, _, method = permutation_p(d[key], d[var], args.n_perm)
            pooled_results[(var, key)] = (rho, n, p)
            print("  %-24s %-16s %6d %+9.3f %9.3f %-28s" % (var, label, n, rho, p, method))
        print()

    print("=" * 100)
    print("2. PER-REGION (n>=4 catchments only) - is one region driving the pooled result?")
    print("=" * 100)
    for var in CHEM_VARS:
        if var not in d.columns:
            continue
        printed_header = False
        for reg in regions:
            sub = d[d.region == reg]
            if sub[var].notna().sum() < 4:
                continue
            for key, label in LOADINGS:
                if key not in sub.columns:
                    continue
                rho, n = spearman(sub[key], sub[var])
                if np.isnan(rho):
                    continue
                if not printed_header:
                    print("  %-24s" % var)
                    printed_header = True
                print("    %-20s %-16s n=%-4d rho=%+.3f" % (reg, label, n, rho))
        if printed_header:
            print()
    print("  (regions with <4 catchments contribute to the pooled figure above\n"
          "  but are too small to show a per-region rho on their own)")

    print("\n" + "=" * 100)
    print("3. LEAVE-ONE-REGION-OUT R^2 - fit on 5 systems, predict the 6th. The real test.")
    print("=" * 100)
    print("  %-24s %-16s %8s %10s %14s" % ("chemistry var", "loading", "n", "LORO_R2", "regions_used"))
    for var in CHEM_VARS:
        if var not in d.columns:
            continue
        for key, label in LOADINGS:
            if key not in d.columns:
                continue
            r2, n, n_reg = leave_one_region_out_r2(d, key, var)
            if np.isnan(r2):
                continue
            print("  %-24s %-16s %8d %+10.3f %14d" % (var, label, n, r2, n_reg))
        print()

    print("-" * 100)
    print("Read section 3 as the real generalisation test. A positive LORO R2\n"
          "means loading measured in OTHER river systems predicts chemistry in\n"
          "one it has never seen - that is what 'our map beats Rockwell's' would\n"
          "actually have to mean to support a grant claim. Section 1's pooled rho\n"
          "alone is NOT sufficient evidence by itself; a result that only shows\n"
          "up in section 1 and collapses in sections 2-3 is a pooling artefact,\n"
          "not a finding, and must be reported as such.")


if __name__ == "__main__":
    main()
