"""Build a POOLED multi-site labelled pixel table for threshold derivation.

Test C derived every adopted threshold from Silverton polygons alone, and
finding L1 showed the result does not transfer. The fix is to derive from more
than one site - but we have hand-drawn polygons only at Silverton.

Rockwell's published USGS map supplies labels at all three Colorado sites, so
it is used as the reference here. Read the caveat before using the output:

    THESE LABELS ARE NOT GROUND TRUTH. Rockwell et al. (2021) is a published,
    peer-reviewed, but still AUTOMATED classification. Thresholds derived
    against it answer "does our reimplementation reproduce theirs, everywhere"
    - a replica-fidelity question. They CANNOT support a claim that our tool is
    more accurate than theirs; only field data can. Keep those two claims
    separate in anything written from this.

label = 1 if Rockwell's class is in AMD_CLASSES {9,12,14,17,18,19}, else 0.

By default only pixels passing OUR land mask are kept, so the derivation is
about cutoffs rather than masking (the confound separated in finding L2/L3).
Pass --all-pixels to override.

    .venv/Scripts/python python/pool_labels.py
"""

import argparse
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RASTER = os.path.join(ROOT, "data", "rockwell", "L8_US_Southwest", "SouthWest",
                      "l8_aa13_southwest_mosaic11.img")
SITES = ["Silverton", "Summitville", "Red_Mountain_Pass"]
OUT = os.path.join(ROOT, "data", "matched", "pooled_labels.csv")

INDEX_COLS = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
              "ClaySulfateMica", "GreenVeg", "NDVI", "MNDWI", "Brightness",
              "AWEINSH", "green_red"]
BAND_COLS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]


def label_site(site, raster=RASTER, land_only=True, prefix="gate"):
    import rasterio
    from rasterio.warp import transform as warp_transform

    from compare_rockwell import AMD_CLASSES, COLLAPSE

    path = os.path.join(ROOT, "data", "imagery",
                        "%s_%s_CO.csv" % (prefix, site))
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    with rasterio.open(raster) as src:
        xs, ys = warp_transform("EPSG:4326", src.crs,
                                d.lon.tolist(), d.lat.tolist())
        d["rockwell"] = [int(v[0]) for v in src.sample(zip(xs, ys))]
    d["rockwell"] = d.rockwell.replace(COLLAPSE)
    n0 = len(d)
    d = d[~d.rockwell.isin([0, 15])].copy()          # their no-data
    n1 = len(d)
    if land_only:
        d = d[d.land_strict.astype(int) == 1].copy()
    d["label"] = d.rockwell.isin(AMD_CLASSES).astype(int)
    d["site"] = site
    print("  %-20s sampled %6d -> valid %6d -> kept %5d   label=1: %4d (%.1f%%)"
          % (site, n0, n1, len(d), d.label.sum(),
             100 * d.label.mean() if len(d) else 0))
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raster", default=RASTER)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--all-pixels", action="store_true",
                    help="keep pixels failing our land mask too")
    ap.add_argument("--prefix", default="gate",
                    help="export filename prefix: 'gate' = Jul-Sep (shipped), "
                         "'may' = May-Jul (paper-faithful season)")
    args = ap.parse_args(argv)

    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    print("Pooling labelled pixels (labels = Rockwell 2021, NOT ground truth)")
    frames = [f for f in (label_site(s, args.raster, not args.all_pixels,
                                     args.prefix)
                          for s in SITES) if f is not None]
    if not frames:
        raise SystemExit("no gate_*.csv exports found - run --mode pixels first")
    d = pd.concat(frames, ignore_index=True)

    keep = ["site", "label", "rockwell", "lon", "lat",
            "cls_strict", "land_strict"] + INDEX_COLS + BAND_COLS
    d = d[[c for c in keep if c in d.columns]]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    d.to_csv(args.out, index=False)
    print("\npooled: %d rows, %d sites, label=1: %d (%.2f%%)"
          % (len(d), d.site.nunique(), d.label.sum(), 100 * d.label.mean()))
    print("->", args.out)


if __name__ == "__main__":
    main()
