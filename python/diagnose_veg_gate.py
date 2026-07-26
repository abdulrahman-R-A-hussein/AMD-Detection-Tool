"""Is the green-peak vegetation gate the cause of the Summitville under-call?

ANSWER: NO. Run 2026-07-26 - the gate is REDUNDANT, uniquely excluding 0 px at
Summitville and 6 px at Silverton, because a pixel with a green peak already
fails `NDVI < 0.25`. All four --gate settings give identical class histograms.
The real cause is the absolute `IronSulfate > 0.10` criterion that every AMD
class depends on; see python/iron_index_transfer.py and
validation/GATE_DIAGNOSIS_2026-07-26.md. This module is kept because the audit
it performs is the reusable part.

Context: the v2.8.0 generalization test found the direction of disagreement with
Rockwell's published map REVERSES between sites (over-call at Silverton where
the thresholds were derived, under-call at Summitville). The candidate mechanism
was the land mask's green-peak term, `Green/Red <= 1.0`, which drops a pixel
from EVERY mineral class before the cascade runs.

This module answers four separate questions, and keeps them separate:

  --mode hist   Exact class histogram for a site under each gate setting.
                Uses TILED reduceRegion so the 15 km Silverton and 10 km Red
                Mountain Pass footprints no longer blow the EE memory limit
                (that was the blocker recorded in the Rockwell report).
                Reports two denominators explicitly, because the earlier
                Summitville percentages mixed them:
                  all      = every pixel with valid composite data
                  eligible = pixels that pass the land mask (mineral-eligible)

  --mode pixels Export per-pixel gate variables + our class + lon/lat so the
                gate can be inspected against Rockwell's raster.

  --mode terms  Audit every land-mask term: how many pixels it excludes AND how
                many it ALONE excludes. A term with a unique cost of zero is
                redundant and cannot explain any under-detection. This is what
                falsified the green-peak hypothesis.

  --mode join   Join a --mode pixels export to Rockwell's raster and report,
                for pixels Rockwell calls ferric and we call vegetation, the
                distribution of Green/Red and which gate term actually failed.

  --mode cond   Separate the LAND-MASK effect from the THRESHOLD effect by
                conditioning on our own land mask, so "we under-detect" is never
                again ambiguous between "we refused to look" and "our cutoffs
                missed it".

    .venv/Scripts/python python/diagnose_veg_gate.py --mode hist --site "Summitville, CO"
    .venv/Scripts/python python/diagnose_veg_gate.py --mode hist --site "Silverton, CO" --tiles 4
"""

import argparse
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gee_classify import (SITES, START, END, SUMMER, T, add_indices, classify,
                          init_ee, process_landsat)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES = ["strict", "relaxed", "override", "off"]
AMD_CLASSES = {9, 12, 14, 17, 18, 19}
# Rockwell classes carrying any ferric iron. Deliberately broader than
# AMD_CLASSES: used to locate disputed pixels, not to score AMD agreement.
ROCKWELL_FERRIC = {1, 2, 3, 6, 7, 8, 9, 12, 13, 17, 18}


def composite(ee, site):
    lon, lat, buf = SITES[site]
    region = ee.Geometry.Point([lon, lat]).buffer(buf)
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(START, END)
           .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[-1], "month"))
           .map(lambda i: process_landsat(ee, i))
           .map(lambda i: add_indices(ee, i)))
    return region, col, col.size().getInfo()


def tile_geoms(ee, region, n):
    """n x n grid over the region's bbox, each cell clipped to the region.

    Sequential per-tile getInfo keeps each request small; one whole-region
    request is what exceeded the user memory limit at 15 km.
    """
    ring = region.bounds().coordinates().get(0).getInfo()
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = []
    for i in range(n):
        for j in range(n):
            cell = ee.Geometry.Rectangle(
                [x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * j / n,
                 x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (j + 1) / n],
                None, False)
            out.append(cell.intersection(region, 1))
    return out


def tiled_hist(ee, img, band, region, n_tiles):
    total = Counter()
    for k, cell in enumerate(tile_geoms(ee, region, n_tiles), 1):
        h = img.reduceRegion(reducer=ee.Reducer.frequencyHistogram(),
                             geometry=cell, scale=30,
                             maxPixels=int(1e9)).getInfo()
        for key, v in (h.get(band) or {}).items():
            total[int(float(key))] += int(v)
        sys.stdout.write("\r    tile %d/%d  running total %d px"
                         % (k, n_tiles * n_tiles, sum(total.values())))
        sys.stdout.flush()
    sys.stdout.write("\n")
    return total


def land_mask_of(ee, cls_img):
    """Mineral-eligible = anything the cascade could assign a mineral class to.

    Classes 11 and 13 are assigned OUTSIDE the land mask (they only require
    `water.Not()`), so they are not evidence of mineral eligibility.
    """
    mineral = None
    for c in range(1, 20):
        if c in (11, 13):
            continue
        m = cls_img.eq(c)
        mineral = m if mineral is None else mineral.Or(m)
    return mineral


def mode_hist(ee, site, n_tiles, gates=None):
    gates = gates or GATES
    region, col, n_scenes = composite(ee, site)
    comp = col.median().clip(region)
    valid = comp.select("SR_B4").mask()
    print("%s: %d Landsat 8 summer scenes %s..%s, %dx%d tiles"
          % (site, n_scenes, START[:4], END[:4], n_tiles, n_tiles))

    results = {}
    for gate in GATES:
        # Do NOT unmask: a masked pixel is missing data, not class 0.
        cls = classify(ee, comp, veg_gate=gate).updateMask(valid).rename("class")
        print("  gate=%s" % gate)
        h = tiled_hist(ee, cls, "class", region, n_tiles)
        results[gate] = h

    print("\n--- class histograms by gate setting (%s) ---" % site)
    all_classes = sorted(set().union(*[set(h) for h in results.values()]))
    print("  %-6s" % "class" + "".join("%12s" % g for g in GATES))
    for c in all_classes:
        print("  %-6d" % c + "".join("%12d" % results[g].get(c, 0)
                                     for g in GATES))

    print("\n--- AMD-indicator rate under each gate (%s) ---" % site)
    print("  %-9s %10s %10s %9s %10s %9s"
          % ("gate", "total", "amd_px", "amd_%all", "eligible", "amd_%elig"))
    for g in GATES:
        h = results[g]
        tot = sum(h.values())
        amd = sum(v for c, v in h.items() if c in AMD_CLASSES)
        elig = sum(v for c, v in h.items()
                   if c not in (0, 11, 13))
        print("  %-9s %10d %10d %8.3f%% %10d %8.3f%%"
              % (g, tot, amd, 100 * amd / tot if tot else 0, elig,
                 100 * amd / elig if elig else 0))

    print("\nNOTE 'amd_%all' denominator = every pixel with valid composite "
          "data, including class 0 (gated out) and 11/13 (vegetation).\n"
          "     'eligible' = pixels the cascade actually gave a mineral class; "
          "it is NOT comparable to Rockwell's 'valid' figure, which excludes\n"
          "     only their no-data codes. Use amd_%all for the head-to-head.")
    return results


def mode_terms(ee, site, n_tiles):
    """Count pixels failing each land-mask term, and each term's UNIQUE cost.

    A term only matters if it excludes pixels no other term already excludes.
    """
    region, col, n_scenes = composite(ee, site)
    comp = col.median().clip(region)
    valid = comp.select("SR_B4").mask()

    iron, gv = comp.select("IronSulfate"), comp.select("GreenVeg")
    ndvi, mndwi = comp.select("NDVI"), comp.select("MNDWI")
    bright, awei = comp.select("Brightness"), comp.select("AWEINSH")
    b3, b4, b5, b6 = (comp.select("SR_B3"), comp.select("SR_B4"),
                      comp.select("SR_B5"), comp.select("SR_B6"))

    water = (mndwi.gt(T["water"]).And(awei.gt(0.0)).And(ndvi.lt(0.0))
             .And(b5.lt(b3)).And(bright.lt(0.30)))
    built = (bright.gt(T["bu_bright"]).And(ndvi.lt(T["bu_ndvi_hi"]))
             .And(ndvi.gt(T["bu_ndvi_lo"]))
             .And(mndwi.lt(T["bu_mndwi"])
                  .Or(mndwi.gt(-0.10).And(mndwi.lt(0.10)))))
    not_bright = bright.lt(T["bright_max"])
    not_dark = b6.gt(T["dark"]).And(bright.gt(0.05))
    green_ok = b3.divide(b4).lte(1.0)
    ndvi_ok = ndvi.lt(T["ndvi_max"]).Or(
        iron.gt(T["iron"]).And(b6.lt(0.20)).And(gv.lt(3.5)))

    terms = {"water": water.Not(), "not_bright": not_bright,
             "not_dark": not_dark, "not_builtup": built.Not(),
             "green_peak_ok": green_ok, "ndvi_ok": ndvi_ok}
    land = None
    for v in terms.values():
        land = v if land is None else land.And(v)

    flags = valid.rename("valid").addBands(land.rename("land"))
    for name, ok in terms.items():
        flags = flags.addBands(ok.Not().rename("fail_" + name))
        others = None
        for n2, o2 in terms.items():
            if n2 != name:
                others = o2 if others is None else others.And(o2)
        # unique = this term is the ONLY reason the pixel is not land
        flags = flags.addBands(ok.Not().And(others).rename("only_" + name))
    flags = flags.updateMask(valid)

    print("%s: %d scenes, land-mask term audit, %dx%d tiles"
          % (site, n_scenes, n_tiles, n_tiles))
    total = Counter()
    for k, cell in enumerate(tile_geoms(ee, region, n_tiles), 1):
        r = flags.reduceRegion(reducer=ee.Reducer.sum(), geometry=cell,
                               scale=30, maxPixels=int(1e9)).getInfo()
        for key, v in r.items():
            if v is not None:
                total[key] += int(v)
        sys.stdout.write("\r    tile %d/%d" % (k, n_tiles * n_tiles))
        sys.stdout.flush()
    sys.stdout.write("\n")

    n = total["valid"]
    print("\n  valid pixels %d, pass land mask %d (%.2f%%)"
          % (n, total["land"], 100 * total["land"] / n))
    print("\n  %-16s %12s %10s %12s %10s"
          % ("term", "fails", "%", "ONLY-fails", "%"))
    for name in terms:
        f, o = total["fail_" + name], total["only_" + name]
        print("  %-16s %12d %9.2f%% %12d %9.2f%%"
              % (name, f, 100 * f / n, o, 100 * o / n))
    print("\n  'ONLY-fails' is what the term costs: pixels it alone removes\n"
          "  from mineral eligibility. A term with ONLY-fails = 0 is redundant\n"
          "  at this site and cannot explain any under-detection.")
    return total


def mode_pixels(ee, site, n_pixels, seed, out, n_tiles=3):
    """Export the gate variables per pixel, for the Rockwell join."""
    region, col, n_scenes = composite(ee, site)
    comp = col.median().clip(region)
    b3, b4 = comp.select("SR_B3"), comp.select("SR_B4")
    stack = (comp.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"])
             .addBands(b3.divide(b4).rename("green_red"))
             .addBands(comp.select("NDVI"))
             .addBands(comp.select("GreenVeg"))
             .addBands(comp.select("Brightness"))
             .addBands(comp.select("IronSulfate"))
             .addBands(comp.select("ClaySulfateMica"))
             .addBands(comp.select("FerricIron1")))
    for gate in GATES:
        stack = stack.addBands(
            classify(ee, comp, veg_gate=gate).rename("cls_" + gate))
        # classify() stashes the land mask it just built; export it so the
        # land-mask effect can be separated from the threshold effect.
        stack = stack.addBands(classify.last_land.rename("land_" + gate))

    # Sample per tile: one whole-region sample aborts at EE's 5000-element
    # getInfo ceiling, so keep each request well under it and accumulate.
    cells = tile_geoms(ee, region, n_tiles)
    per = max(1, min(4000, n_pixels // len(cells)))
    rows = []
    for k, cell in enumerate(cells, 1):
        fc = stack.sample(region=cell, scale=30, numPixels=per,
                          seed=seed + k, geometries=True, dropNulls=True)
        for f in fc.getInfo()["features"]:
            p = dict(f["properties"])
            c = f["geometry"]["coordinates"]
            p["lon"], p["lat"] = c[0], c[1]
            rows.append(p)
        sys.stdout.write("\r    tile %d/%d  %d px" % (k, len(cells), len(rows)))
        sys.stdout.flush()
    sys.stdout.write("\n")
    print("%s: %d scenes, %d sampled pixels" % (site, n_scenes, len(rows)))
    if not rows:
        return
    cols = (["lon", "lat", "green_red", "NDVI", "GreenVeg", "Brightness",
             "IronSulfate", "ClaySulfateMica", "FerricIron1",
             "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"]
            + ["cls_" + g for g in GATES] + ["land_" + g for g in GATES])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("->", out)


def mode_join(pixels_csv, raster):
    import numpy as np
    import pandas as pd
    import rasterio
    from rasterio.warp import transform as warp_transform

    from compare_rockwell import COLLAPSE, ROCKWELL

    d = pd.read_csv(pixels_csv)
    with rasterio.open(raster) as src:
        xs, ys = warp_transform("EPSG:4326", src.crs,
                                d.lon.tolist(), d.lat.tolist())
        d["rockwell"] = [int(v[0]) for v in src.sample(zip(xs, ys))]
    d["rockwell"] = d.rockwell.replace(COLLAPSE)
    d = d[~d.rockwell.isin([0, 15])].copy()
    print("%d pixels on valid Rockwell data" % len(d))

    fer = d.rockwell.isin(ROCKWELL_FERRIC)
    print("\n--- Rockwell says ferric-bearing (n=%d): what do we say? ---"
          % int(fer.sum()))
    for c, n in Counter(d.loc[fer, "cls_strict"]).most_common(8):
        print("  ours %2d %-42s %6d (%4.1f%%)"
              % (c, ROCKWELL.get(c, "unclassified")[:42], n,
                 100 * n / max(int(fer.sum()), 1)))

    veg = fer & d.cls_strict.isin([0, 11, 13])
    sub = d[veg]
    print("\n--- The disputed set: Rockwell ferric, ours veg/unclassified "
          "(n=%d) ---" % len(sub))
    if not len(sub):
        return
    q = sub.green_red.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    print("  Green/Red percentiles: " + "  ".join(
        "p%02d=%.3f" % (100 * k, v) for k, v in q.items()))
    print("  fails green-peak gate (Green/Red > 1.0) : %d (%.1f%%)"
          % ((sub.green_red > 1.0).sum(),
             100 * (sub.green_red > 1.0).mean()))
    print("  NDVI  median %.3f   GreenVeg median %.3f   Brightness median %.3f"
          % (sub.NDVI.median(), sub.GreenVeg.median(),
             sub.Brightness.median()))
    print("  also fails NDVI<0.25                    : %d (%.1f%%)"
          % ((sub.NDVI >= 0.25).sum(), 100 * (sub.NDVI >= 0.25).mean()))
    print("  carries our iron flag  (IronSulfate>%.2f): %d (%.1f%%)"
          % (T["iron"], (sub.IronSulfate > T["iron"]).sum(),
             100 * (sub.IronSulfate > T["iron"]).mean()))
    print("  carries our clay flag  (Clay>%.3f)      : %d (%.1f%%)"
          % (T["clay"], (sub.ClaySulfateMica > T["clay"]).sum(),
             100 * (sub.ClaySulfateMica > T["clay"]).mean()))

    print("\n--- Would relaxing the gate recover them? ---")
    for g in GATES:
        got = sub["cls_" + g].isin(AMD_CLASSES).sum()
        anymin = (~sub["cls_" + g].isin([0, 11, 13])).sum()
        print("  gate=%-9s recovered as AMD %5d (%5.1f%%)   "
              "as any mineral class %5d (%5.1f%%)"
              % (g, got, 100 * got / len(sub), anymin,
                 100 * anymin / len(sub)))

    print("\n--- Cost of relaxing: pixels Rockwell calls vegetation (11) ---")
    rveg = d[d.rockwell == 11]
    for g in GATES:
        bad = rveg["cls_" + g].isin(AMD_CLASSES).sum()
        print("  gate=%-9s we call AMD on %5d / %5d (%5.2f%%) of their veg"
              % (g, bad, len(rveg), 100 * bad / max(len(rveg), 1)))


def mode_cond(pixels_csv, raster, label):
    """Separate the LAND-MASK effect from the THRESHOLD effect.

    "We under-detect" can mean two very different things:
      (a) our land mask refuses to classify the terrain at all, or
      (b) the terrain is classified but our iron thresholds do not fire.
    Only (b) is a statement about the thresholds. This conditions on our own
    land mask so the two are never conflated again.
    """
    import pandas as pd
    import rasterio
    from rasterio.warp import transform as warp_transform

    from compare_rockwell import AMD_CLASSES as RA
    from compare_rockwell import COLLAPSE

    d = pd.read_csv(pixels_csv)
    with rasterio.open(raster) as src:
        xs, ys = warp_transform("EPSG:4326", src.crs,
                                d.lon.tolist(), d.lat.tolist())
        d["rockwell"] = [int(v[0]) for v in src.sample(zip(xs, ys))]
    d["rockwell"] = d.rockwell.replace(COLLAPSE)
    d = d[~d.rockwell.isin([0, 15])].copy()
    d["land"] = d.land_strict.astype(int) == 1
    d["r_amd"] = d.rockwell.isin(RA)
    d["o_amd"] = d.cls_strict.isin(RA)
    # Rockwell's own vegetation classes - where THEY declined to call mineral.
    d["r_min_elig"] = ~d.rockwell.isin([11, 13])

    print("=== %s: land mask vs thresholds ===" % label)
    print("paired pixels on valid Rockwell data: %d" % len(d))
    print("pass OUR land mask                  : %d (%.2f%%)"
          % (d.land.sum(), 100 * d.land.mean()))
    print("Rockwell calls mineral-eligible      : %d (%.2f%%)"
          % (d.r_min_elig.sum(), 100 * d.r_min_elig.mean()))

    print("\n--- Where do Rockwell's AMD pixels go in our map? ---")
    ra = d[d.r_amd]
    print("  Rockwell AMD pixels                     : %d" % len(ra))
    if len(ra):
        lost = (~ra.land).sum()
        print("  killed by OUR LAND MASK before cascade  : %d (%.1f%%)"
              % (lost, 100 * lost / len(ra)))
        kept = ra[ra.land]
        print("  reached the cascade                     : %d (%.1f%%)"
              % (len(kept), 100 * len(kept) / len(ra)))
        if len(kept):
            print("    of those, we also call AMD            : %d (%.1f%%)"
                  % (kept.o_amd.sum(), 100 * kept.o_amd.mean()))
            print("    of those, we call some other mineral  : %d (%.1f%%)"
                  % ((~kept.o_amd).sum(), 100 * (~kept.o_amd).mean()))

    print("\n--- AMD rate on the SAME pixels, by conditioning set ---")
    print("  %-38s %8s %10s %10s %7s"
          % ("subset", "n", "rockwell%", "ours%", "ratio"))
    for name, sub in [("all paired valid px", d),
                      ("passes our land mask", d[d.land]),
                      ("our land mask AND Rockwell mineral",
                       d[d.land & d.r_min_elig])]:
        if not len(sub):
            continue
        r, o = 100 * sub.r_amd.mean(), 100 * sub.o_amd.mean()
        print("  %-38s %8d %9.2f%% %9.2f%% %7s"
              % (name, len(sub), r, o,
                 "%.2fx" % (o / r) if r else "n/a"))
    print("\n  The last row is the only threshold-vs-threshold comparison:\n"
          "  both maps agree the pixel is classifiable mineral terrain, so a\n"
          "  difference there is about cutoffs, not about masking.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True,
                    choices=["hist", "terms", "pixels", "join", "cond"])
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--tiles", type=int, default=3)
    ap.add_argument("--pixels-n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--csv")
    ap.add_argument("--label")
    ap.add_argument("--raster",
                    default=os.path.join(ROOT, "data", "rockwell",
                                         "L8_US_Southwest", "SouthWest",
                                         "l8_aa13_southwest_mosaic11.img"))
    args = ap.parse_args(argv)

    if args.mode in ("join", "cond"):
        if not args.csv:
            ap.error("--mode %s needs --csv from a --mode pixels run" % args.mode)
        if args.mode == "join":
            mode_join(args.csv, args.raster)
        else:
            mode_cond(args.csv, args.raster, args.label or args.csv)
        return
    if not args.site:
        ap.error("--mode %s needs --site" % args.mode)

    ee = init_ee()
    if args.mode == "hist":
        mode_hist(ee, args.site, args.tiles)
    elif args.mode == "terms":
        mode_terms(ee, args.site, args.tiles)
    else:
        out = args.csv or os.path.join(
            ROOT, "data", "imagery", "gate_%s.csv"
            % args.site.replace(", ", "_").replace(" ", "_"))
        mode_pixels(ee, args.site, args.pixels_n, args.seed, out, args.tiles)


if __name__ == "__main__":
    main()
