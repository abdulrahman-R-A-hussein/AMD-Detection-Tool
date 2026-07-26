"""Head-to-head: our AMD classification vs Rockwell's published USGS map.

Rockwell et al. (2021, SIM 3466) describe the automated Landsat 8 mineral-
mapping method this tool reimplements, but never released their code. Their
RESULT is published as a raster (DOI 10.5066/P9BYV5H4), so the honest way to
show what our reimplementation changed is a pixel-level comparison against it.

Why sample points rather than export a raster: we already hold 20,000 Silverton
pixels carrying lon/lat and our committed classification
(VPCA_Landsat8_Silverton__CO_20260722-v2.csv). Sampling Rockwell's raster at
those exact coordinates avoids re-implementing the classifier in Python - the
existing python/amd_detection.py port is v1.5.1, i.e. PRE-dating every v2.x
correction, and using it would compare Rockwell against our old broken code.

Class schemes are shared: our 19 classes were built to reproduce Rockwell's
legend, so 1-14 and 17-19 map 1:1. Their 15 (cloud/smoke), 16, 20 and 21
(fallow-agriculture variants of 12/17/18) have no counterpart here.

Usage:
    .venv/Scripts/python python/compare_rockwell.py --raster data/rockwell/<file>.img
"""

import argparse
import os
from collections import Counter

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIXELS = os.path.join(ROOT, "VPCA_Landsat8_Silverton__CO_20260722-v2.csv")

# From data/rockwell/00Readme_L8_WesternUS.txt
ROCKWELL = {
    0: "no data", 1: "minor ferric (hematite)", 2: "major ferric",
    3: "ferric +/- ferrous", 4: "ferrous / coarse ferric",
    5: "clay-sulfate-mica", 6: "clay + minor ferric",
    7: "clay + mod-major ferric", 8: "clay + major ferric",
    9: "clay + major ferric, poss. Fe-sulfate (argillic)",
    10: "clay + ferrous", 11: "dense green vegetation",
    12: "clay + major ferric, poss. oxidizing sulfides + major Fe-sulfate",
    13: "sparse vegetation + ferric",
    14: "clay, poss. oxidizing sulfides + minor Fe-sulfate",
    15: "no data (smoke/cloud/shadow)",
    16: "clay + ferric, fallow agriculture (cf 12)",
    17: "clay + major ferric, poss. major Fe-sulfate (proximal pyritic)",
    18: "clay + major ferric, poss. mod-major Fe-sulfate (distal pyritic)",
    19: "clay + ferrous, poss. minor Fe-sulfate",
    20: "clay + ferric +/- sparse veg, fallow ag (cf 17)",
    21: "clay + ferric +/- sparse veg, fallow ag (cf 18)",
}

# The AMD-indicator subset - what the tool actually claims to find.
AMD_CLASSES = {9, 12, 14, 17, 18, 19}
# Rockwell's agricultural variants collapse onto their parent classes.
COLLAPSE = {16: 12, 20: 17, 21: 18}


def kappa(a, b):
    """Cohen's kappa over the union of labels present."""
    labels = sorted(set(a) | set(b))
    idx = {l: i for i, l in enumerate(labels)}
    m = np.zeros((len(labels), len(labels)))
    for x, y in zip(a, b):
        m[idx[x], idx[y]] += 1
    n = m.sum()
    if not n:
        return float("nan")
    po = np.trace(m) / n
    pe = (m.sum(0) * m.sum(1)).sum() / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raster", required=True, help="Rockwell .img file")
    ap.add_argument("--pixels", default=PIXELS)
    ap.add_argument("--class-col", default="class",
                    help="column holding OUR class; gate_*.csv uses cls_strict")
    ap.add_argument("--label", default=None, help="site name for the header")
    args = ap.parse_args(argv)

    import rasterio
    from rasterio.warp import transform as warp_transform

    d = pd.read_csv(args.pixels)
    print("=== %s ===" % (args.label or os.path.basename(args.pixels)))
    print("our pixels: %d from %s" % (len(d), os.path.basename(args.pixels)))

    with rasterio.open(args.raster) as src:
        print("rockwell raster: %s  crs=%s  size=%dx%d  res=%s"
              % (os.path.basename(args.raster), src.crs, src.width, src.height,
                 tuple(round(v, 1) for v in src.res)))
        xs, ys = warp_transform("EPSG:4326", src.crs,
                                d.lon.tolist(), d.lat.tolist())
        vals = [v[0] for v in src.sample(zip(xs, ys))]

    d["rockwell"] = [int(v) for v in vals]
    d["rockwell"] = d.rockwell.replace(COLLAPSE)
    d["ours"] = d[args.class_col].astype(int)

    inside = d[~d.rockwell.isin([0, 15])]
    print("\n%d/%d points fall on valid Rockwell data (excl. their no-data 0/15)"
          % (len(inside), len(d)))
    if not len(inside):
        print("No overlap - is this the right regional tile for Silverton?")
        return

    both = inside[inside.ours > 0]
    print("%d of those are classified by BOTH (our 0 = unclassified)" % len(both))

    print("\n--- Rockwell class distribution over our Silverton AOI ---")
    for c, n in Counter(inside.rockwell).most_common(10):
        print("  %2d %-58s %6d (%4.1f%%)"
              % (c, ROCKWELL.get(c, "?")[:58], n, 100 * n / len(inside)))

    print("\n--- Our class distribution (same points) ---")
    for c, n in Counter(inside.ours).most_common(10):
        print("  %2d %-58s %6d (%4.1f%%)"
              % (c, ROCKWELL.get(c, "?")[:58], n, 100 * n / len(inside)))

    if len(both):
        agree = (both.ours == both.rockwell).mean()
        print("\n--- Agreement, classified-by-both (n=%d) ---" % len(both))
        print("  exact class agreement : %.1f%%" % (100 * agree))
        print("  Cohen's kappa         : %.3f"
              % kappa(both.ours.tolist(), both.rockwell.tolist()))

    print("\n--- AMD-indicator agreement (classes %s) ---"
          % sorted(AMD_CLASSES))
    ra = inside.rockwell.isin(AMD_CLASSES)
    oa = inside.ours.isin(AMD_CLASSES)
    tp = int((ra & oa).sum())
    fp = int((~ra & oa).sum())
    fn = int((ra & ~oa).sum())
    tn = int((~ra & ~oa).sum())
    print("  Rockwell AMD: %d px (%.2f%%)   ours: %d px (%.2f%%)"
          % (ra.sum(), 100 * ra.mean(), oa.sum(), 100 * oa.mean()))
    print("  agree both-AMD=%d  both-not=%d  ours-only=%d  Rockwell-only=%d"
          % (tp, tn, fp, fn))
    if tp + fp:
        print("  precision vs Rockwell : %.3f" % (tp / (tp + fp)))
    if tp + fn:
        print("  recall vs Rockwell    : %.3f" % (tp / (tp + fn)))
    print("  binary kappa          : %.3f"
          % kappa(oa.astype(int).tolist(), ra.astype(int).tolist()))

    print("\n--- Where we differ most (our class -> their class) ---")
    dis = both[both.ours != both.rockwell]
    for (o, r), n in Counter(zip(dis.ours, dis.rockwell)).most_common(12):
        print("  %6d px  ours %2d (%-28s) -> theirs %2d (%s)"
              % (n, o, ROCKWELL.get(o, "?")[:28], r, ROCKWELL.get(r, "?")[:34]))

    print("\nNOTE: Rockwell's map is a multi-year Landsat 8 product; ours is a "
          "2013-2020 summer median. Differences include real temporal and "
          "compositing differences, not only algorithmic ones.")


if __name__ == "__main__":
    main()
