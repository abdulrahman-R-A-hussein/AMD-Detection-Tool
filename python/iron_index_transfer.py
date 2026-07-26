"""Why the Rockwell agreement inverts between sites: the IronSulfate offset.

Every one of the six AMD-indicator classes (9, 12, 14, 17, 18, 19) requires
`has_iron` = IronSulfate > 0.10, where

    IronSulfate = (B2/B1) - (B5/B4)

is a DIFFERENCE OF TWO UNNORMALISED BAND RATIOS. Nothing constrains its
absolute level across scenes, so an absolute cutoff is a scene-specific
constant masquerading as a physical one. This is the same defect class as the
`AWEINSH > 0.20` water mask tuned at Ganau (finding W1), on the land arm.

This script tests that claim three ways, treating "Rockwell says AMD" as the
reference label (it is a published product, not ground truth - see the report):

  1. Per-site ROC of IronSulfate against Rockwell-AMD, over pixels that pass
     our land mask. If the index still SEPARATES at both sites, the index is
     not broken - only its fixed cutoff is.
  2. The Youden-optimal cutoff per site. If those differ substantially while
     AUC stays healthy, the failure is an offset, not a loss of information.
  3. Whether making the criterion scene-relative (a within-scene percentile, or
     a within-scene z-score) transfers where the absolute cutoff does not.

    .venv/Scripts/python python/iron_index_transfer.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_rockwell import AMD_CLASSES, COLLAPSE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RASTER = os.path.join(ROOT, "data", "rockwell", "L8_US_Southwest", "SouthWest",
                      "l8_aa13_southwest_mosaic11.img")
SITES = ["Silverton", "Summitville"]
ABS_CUT = 0.10          # the shipped v2.4.0 threshold


def load(site):
    import rasterio
    from rasterio.warp import transform as warp_transform

    d = pd.read_csv(os.path.join(ROOT, "data", "imagery",
                                 "gate_%s_CO.csv" % site))
    with rasterio.open(RASTER) as src:
        xs, ys = warp_transform("EPSG:4326", src.crs,
                                d.lon.tolist(), d.lat.tolist())
        d["rw"] = [int(v[0]) for v in src.sample(zip(xs, ys))]
    d["rw"] = d.rw.replace(COLLAPSE)
    d = d[~d.rw.isin([0, 15])].copy()
    d = d[d.land_strict.astype(int) == 1].copy()      # land mask held constant
    d["y"] = d.rw.isin(AMD_CLASSES).astype(int)
    return d


def roc_auc(score, y):
    """AUC via the Mann-Whitney identity, with ties at 0.5."""
    pos, neg = score[y == 1], score[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order), float)
    s = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[i:j + 1] = (i + j) / 2.0 + 1
        i = j + 1
    inv = np.empty(len(order), int)
    inv[order] = np.arange(len(order))
    rpos = ranks[inv[:len(pos)]]
    return (rpos.sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def youden(score, y):
    cuts = np.unique(score)
    if len(cuts) > 2000:
        cuts = np.quantile(score, np.linspace(0, 1, 2000))
    best = (-1, None, 0, 0)
    for c in cuts:
        p = score > c
        tpr = p[y == 1].mean() if (y == 1).any() else 0
        fpr = p[y == 0].mean() if (y == 0).any() else 0
        if tpr - fpr > best[0]:
            best = (tpr - fpr, c, tpr, fpr)
    return best


def rates(pred, y):
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    return prec, rec


def main():
    data = {s: load(s) for s in SITES}

    print("=" * 74)
    print("1. Does IronSulfate still separate AMD from non-AMD at both sites?")
    print("=" * 74)
    print("  %-13s %7s %7s %8s %10s %10s %10s"
          % ("site", "n", "n_amd", "AUC", "med(AMD)", "med(non)", "shift"))
    for s in SITES:
        d = data[s]
        x, y = d.IronSulfate.to_numpy(float), d.y.to_numpy(int)
        m1, m0 = x[y == 1], x[y == 0]
        print("  %-13s %7d %7d %8.3f %+10.4f %+10.4f %+10.4f"
              % (s, len(d), int(y.sum()), roc_auc(x, y),
                 np.median(m1), np.median(m0), np.median(m1) - np.median(m0)))
    print("\n  Separation ('shift') surviving at both sites means the index\n"
          "  still carries the signal. Compare the ABSOLUTE levels below.")

    print("\n" + "=" * 74)
    print("2. Where does the optimal cutoff actually sit at each site?")
    print("=" * 74)
    print("  %-13s %10s %10s %10s %9s %9s"
          % ("site", "shipped", "Youden", "pctile of", "TPR@opt", "FPR@opt"))
    print("  %-13s %10s %10s %10s"
          % ("", "cut=0.10", "cutoff", "0.10 here"))
    opt = {}
    for s in SITES:
        d = data[s]
        x, y = d.IronSulfate.to_numpy(float), d.y.to_numpy(int)
        j, c, tpr, fpr = youden(x, y)
        opt[s] = c
        pct = 100.0 * (x <= ABS_CUT).mean()
        print("  %-13s %10.3f %10.4f %9.1f%% %9.3f %9.3f"
              % (s, ABS_CUT, c, pct, tpr, fpr))
    print("\n  The shipped 0.10 sits at very different points in the two\n"
          "  distributions - that is the whole failure.")

    print("\n" + "=" * 74)
    print("3. Absolute cutoff vs scene-relative criteria")
    print("=" * 74)
    # Calibrate each rule ONCE at Silverton, then apply it unchanged to
    # Summitville. That is the transfer test the original Test C never ran.
    ref = data["Silverton"]
    rx = ref.IronSulfate.to_numpy(float)
    ref_pct = 100.0 * (rx <= ABS_CUT).mean()        # 0.10 as a percentile
    ref_z = (ABS_CUT - rx.mean()) / rx.std()        # 0.10 as a z-score

    print("  calibrated at Silverton:  absolute=%.3f   percentile=%.2f   "
          "z=%.3f\n" % (ABS_CUT, ref_pct, ref_z))
    print("  %-13s %-22s %9s %9s %9s"
          % ("site", "rule", "flagged%", "precision", "recall"))
    for s in SITES:
        d = data[s]
        x, y = d.IronSulfate.to_numpy(float), d.y.to_numpy(int)
        rules = {
            "absolute > 0.10": x > ABS_CUT,
            "within-scene pctile": x > np.percentile(x, ref_pct),
            "within-scene z-score": (x - x.mean()) / x.std() > ref_z,
        }
        for name, pred in rules.items():
            prec, rec = rates(pred, y)
            print("  %-13s %-22s %8.1f%% %9.3f %9.3f"
                  % (s, name, 100 * pred.mean(), prec, rec))
        print()

    print("  A rule that generalises should hold RECALL roughly steady across\n"
          "  the two sites. Read the recall column, not the precision column:\n"
          "  precision is measured against Rockwell's map, which is itself an\n"
          "  automated product, so 'false positives' here are disagreements,\n"
          "  not confirmed errors.")


if __name__ == "__main__":
    main()
