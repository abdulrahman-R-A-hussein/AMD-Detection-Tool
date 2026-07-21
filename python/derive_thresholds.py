"""
Honest threshold derivation for the AMD Detection Tool (v2)
===========================================================

Replaces hand-typed index thresholds (and the old circular control-lake table)
with thresholds that have a defensible statistical provenance.

Method (plan section 4): sample pixels inside CONFIRMED-AMD polygons (label=1)
and CONFIRMED-CLEAN polygons (label=0), then for each spectral index build the
two-population separability test:
  - ROC curve and AUC (how well the index separates AMD from clean at all cuts)
  - Youden's J optimal threshold (max sensitivity+specificity-1)
  - Otsu crossover threshold (histogram-based, label-free cross-check)

Every reported threshold then comes with an AUC and a sensitivity/specificity,
instead of being a guessed constant.

Author: Abdulrahman Hussein, Kent State University (Dr. Joseph D. Ortiz lab)

------------------------------------------------------------------
INPUT CSV
------------------------------------------------------------------
One row per labelled pixel. Columns:
  label     : 1 = confirmed AMD, 0 = confirmed clean   (REQUIRED)
  <index>   : one or more index columns, e.g. IronSulfate, FerricIron1,
              FerricIron2, ClaySulfateMica  (values as the GEE tool computes)
See specs/amd-v2/validation-protocol.md for how to produce it from GEE.

------------------------------------------------------------------
RUN
------------------------------------------------------------------
  python derive_thresholds.py --self-test
  python derive_thresholds.py --csv labelled_pixels.csv
  python derive_thresholds.py --csv labelled_pixels.csv --indices IronSulfate FerricIron1
"""

import argparse
import sys
import numpy as np


def roc_auc(values, labels):
    """ROC-AUC via the rank (Mann-Whitney U) identity. Assumes higher index =>
    more AMD. Returns AUC in [0,1]; 0.5 = no separation."""
    values = np.asarray(values, float)
    labels = np.asarray(labels, int)
    pos = values[labels == 1]
    neg = values[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # average ranks (handle ties) over all values
    _, inv, counts = np.unique(values, return_inverse=True, return_counts=True)
    order = np.argsort(values, kind="mergesort")
    ord_ranks = np.empty(len(values), float)
    ord_ranks[order] = np.arange(1, len(values) + 1)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ord_ranks)
    ranks = (sums / counts)[inv]
    r_pos = ranks[labels == 1].sum()
    auc = (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    return float(auc)


def youden_threshold(values, labels):
    """Threshold maximising Youden's J = sensitivity + specificity - 1.

    Returns (threshold, sensitivity, specificity, J). Rule: predict AMD if
    value > threshold.
    """
    values = np.asarray(values, float)
    labels = np.asarray(labels, int)
    P = np.sum(labels == 1)
    N = np.sum(labels == 0)
    if P == 0 or N == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    uniq = np.unique(values)
    cuts = (uniq[:-1] + uniq[1:]) / 2 if len(uniq) > 1 else uniq
    best = (-1.0, float(uniq[0]), 0.0, 0.0)
    for t in cuts:
        pred = values > t
        tp = np.sum(pred & (labels == 1))
        tn = np.sum(~pred & (labels == 0))
        sens = tp / P
        spec = tn / N
        J = sens + spec - 1
        if J > best[0]:
            best = (J, float(t), sens, spec)
    J, t, sens, spec = best
    return float(t), float(sens), float(spec), float(J)


def otsu_threshold(values, nbins=256):
    """Otsu crossover threshold (label-free) as an independent cross-check."""
    x = np.asarray(values, float)
    hist, edges = np.histogram(x, bins=nbins)
    centers = (edges[:-1] + edges[1:]) / 2
    w = np.cumsum(hist).astype(float)
    if w[-1] == 0:
        return float("nan")
    cum_mean = np.cumsum(hist * centers)
    wb = w / w[-1]
    wf = 1 - wb
    mb = cum_mean / np.maximum(w, 1)
    mf = (cum_mean[-1] - cum_mean) / np.maximum(w[-1] - w, 1)
    between = wb * wf * (mb - mf) ** 2
    return float(centers[int(np.nanargmax(between))])


def analyze_index(name, values, labels):
    values = np.asarray(values, float)
    labels = np.asarray(labels, int)
    keep = np.isfinite(values)
    values, labels = values[keep], labels[keep]
    auc = roc_auc(values, labels)
    t, sens, spec, J = youden_threshold(values, labels)
    otsu = otsu_threshold(values)
    return {"index": name, "n": int(len(values)),
            "n_amd": int(np.sum(labels == 1)), "n_clean": int(np.sum(labels == 0)),
            "auc": auc, "threshold": t, "sensitivity": sens,
            "specificity": spec, "youden_j": J, "otsu": otsu}


def print_results(rows):
    print("\n" + "=" * 78)
    print("THRESHOLD DERIVATION  (two-population separability, plan section 4)")
    print("=" * 78)
    print(f"  {'index':>16} {'AUC':>6} {'thresh':>9} {'sens':>6} {'spec':>6} "
          f"{'Otsu':>9} {'quality':>10}")
    for r in rows:
        print(f"  {r['index']:>16} {r['auc']:>6.3f} {r['threshold']:>9.3f} "
              f"{r['sensitivity']:>6.2f} {r['specificity']:>6.2f} "
              f"{r['otsu']:>9.3f} {_auc_label(r['auc']):>10}")
    print("-" * 78)
    print("  Rule: predict AMD if index > threshold. AUC: 0.5=random, "
          "1.0=perfect.")
    print("  Use the Youden threshold as the tool's setting; Otsu is a "
          "label-free check.")
    print("=" * 78 + "\n")


def _auc_label(a):
    if a != a:
        return "n/a"
    if a < 0.6: return "poor"
    if a < 0.7: return "fair"
    if a < 0.8: return "good"
    if a < 0.9: return "very good"
    return "excellent"


def self_test(seed=0, n=2000, verbose=True):
    """Two Gaussian populations with a known crossover; confirm the derived
    threshold lands near it and AUC is high."""
    rng = np.random.default_rng(seed)
    clean = rng.normal(0.00, 0.05, n)      # clean index ~ 0.0
    amd = rng.normal(0.20, 0.05, n)        # AMD index ~ 0.2
    values = np.concatenate([clean, amd])
    labels = np.concatenate([np.zeros(n, int), np.ones(n, int)])
    r = analyze_index("synthetic", values, labels)
    # true crossover of two equal-variance Gaussians is the midpoint (0.10)
    ok = (r["auc"] >= 0.95 and abs(r["threshold"] - 0.10) < 0.03
          and abs(r["otsu"] - 0.10) < 0.03)
    if verbose:
        print("\n" + "=" * 78)
        print("SELF-TEST: recover a known crossover threshold (true = 0.100)")
        print("=" * 78)
        print_results([r])
        print(f"  RESULT: {'PASS' if ok else 'FAIL'} "
              f"(threshold {r['threshold']:.3f}, otsu {r['otsu']:.3f}, "
              f"AUC {r['auc']:.3f})")
        print("=" * 78 + "\n")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description="Derive AMD index thresholds from "
                                             "labelled AMD/clean pixels.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--csv", help="labelled pixel CSV (needs a 'label' column)")
    ap.add_argument("--label", default="label", help="name of the 0/1 column")
    ap.add_argument("--indices", nargs="*",
                    help="index columns to analyze (default: all numeric "
                         "columns except the label)")
    args = ap.parse_args(argv)

    if args.self_test or not args.csv:
        ok = self_test()
        if not args.csv:
            sys.exit(0 if ok else 1)

    import pandas as pd
    df = pd.read_csv(args.csv)
    if args.label not in df.columns:
        sys.exit(f"ERROR: CSV has no '{args.label}' column (0=clean, 1=AMD).")
    labels = df[args.label].to_numpy(int)
    if args.indices:
        cols = args.indices
    else:
        cols = [c for c in df.columns
                if c != args.label and np.issubdtype(df[c].dtype, np.number)]
    rows = [analyze_index(c, df[c].to_numpy(float), labels) for c in cols]
    print(f"\nLoaded {len(df)} labelled pixels "
          f"({int(np.sum(labels==1))} AMD, {int(np.sum(labels==0))} clean) "
          f"from {args.csv}")
    print_results(rows)


if __name__ == "__main__":
    main()
