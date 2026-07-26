"""Server-side replica of the v2.4.0 pipeline, for classifying NEW sites.

python/classify_v240.py (NumPy) tops out at 94.95% because the tool computes
indices PER IMAGE and then medians them - median(f(x)) != f(median(x)). This
module runs the whole pipeline inside Earth Engine in the same order as
earth-engine/amd_detection_v2.4.0.js, so it is exact and can be pointed at
sites for which we hold no exported pixels.

Self-check: run with --site "Silverton, CO" and compare against the committed
VPCA_Landsat8_Silverton__CO_20260722-v2.csv. Same collection, dates, season,
scale, seed and pixel count, so agreement should be near-total; anything else
means the replica has drifted from the JS.

    .venv/Scripts/python python/gee_classify.py --site "Summitville, CO"
"""

import argparse
import csv
import json
import os

KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"
START, END = "2013-01-01", "2020-12-31"
SUMMER = [7, 8, 9]                       # settings.seasonFilter default

SITES = {                                # from studyAreas in the JS
    "Silverton, CO": (-107.665, 37.812, 15000),
    "Summitville, CO": (-106.5978, 37.4361, 8000),
    "Red Mountain Pass, CO": (-107.72, 37.89, 10000),
    "Leadville, CO": (-106.30, 39.25, 15000),
    "Marysvale, UT": (-112.233, 38.450, 10000),
    "Goldfield, NV": (-117.233, 37.708, 10000),
}

T = dict(iron=0.10, ferric1=1.983, ferric2=3.758, ferrous=0.959, clay=0.021,
         green_veg=1.5, dense_veg=3.0, ndvi_max=0.25, bright_max=0.35,
         dark=0.2125, water=0.3, bu_bright=0.18, bu_ndvi_hi=0.15,
         bu_ndvi_lo=-0.10, bu_mndwi=-0.20)


def init_ee():
    import ee
    info = json.load(open(KEY))
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], KEY),
                  project=info["project_id"])
    return ee


def process_landsat(ee, img):
    qa = img.select("QA_PIXEL")
    clear = (qa.bitwiseAnd(1 << 3).eq(0)
             .And(qa.bitwiseAnd(1 << 4).eq(0))
             .And(qa.bitwiseAnd(1 << 2).eq(0)))
    m = img.updateMask(clear)
    scaled = (m.select("SR_B[1-7]").multiply(0.0000275).add(-0.2)
              .clamp(0.0, 1.0)
              .rename(["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]))
    return m.addBands(scaled, None, True)


def add_indices(ee, img):
    e = 0.0001
    b1, b2, b3 = img.select("SR_B1"), img.select("SR_B2"), img.select("SR_B3")
    b4, b5, b6, b7 = (img.select("SR_B4"), img.select("SR_B5"),
                      img.select("SR_B6"), img.select("SR_B7"))
    iron = (b2.divide(b1.add(e)).subtract(b5.divide(b4.add(e)))
            .clamp(-5, 5).rename("IronSulfate"))
    f1 = b4.divide(b2.add(e)).rename("FerricIron1")
    f2 = b4.divide(b2.add(e)).multiply(b4.add(b6).divide(b5.add(e))).rename("FerricIron2")
    fe2 = b3.add(b6).divide(b4.add(b5).add(e)).rename("FerrousIron")
    clay = b6.divide(b7.add(e)).subtract(b5.divide(b4.add(e))).rename("ClaySulfateMica")
    gv = b5.divide(b4.add(e)).rename("GreenVeg")
    ndvi = img.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    mndwi = img.normalizedDifference(["SR_B3", "SR_B6"]).rename("MNDWI")
    bright = b2.add(b3).add(b4).divide(3).rename("Brightness")
    awei = (b2.add(b3.multiply(2.5)).subtract(b5.multiply(1.5))
            .subtract(b7.multiply(0.25)).rename("AWEINSH"))
    return img.addBands([iron, f1, f2, fe2, clay, gv, ndvi, mndwi, bright, awei])


def classify(ee, c, veg_gate="strict", iron_fallback=True):
    """The v2.4.0 first-match-wins cascade, server-side.

    NOTE ON VERSIONS: the defaults here reproduce **v2.4.0**, because every
    analysis in validation/ was computed against that behaviour and must stay
    reproducible. The shipped JS tool moved to v3.0.0 defaults (May-Jul season,
    scene-relative thresholds, no iron fallback) - see
    validation/REPLICA_AUDIT_2026-07-26.md. Pass iron_fallback=False and use
    diagnose_veg_gate.py --months 5,7 to approximate the v3.0.0 configuration.

    iron_fallback: v2.x assigned class 12 to ANY remaining iron pixel with no
    clay requirement. Rockwell Table 4 has no such rule - all six of their
    iron-sulfate classes require clay - and it collapsed the AMD decision onto
    the single weakest index. Removed in v3.0.0.

    veg_gate controls the green-peak term of the land mask ONLY. "strict" is
    the shipped v2.4.0 behaviour (Green/Red <= 1.0) and is the default, so this
    stays a faithful replica; the other modes exist for the sensitivity study in
    python/diagnose_veg_gate.py and must not be used to produce tool results.
      strict  : Green/Red <= 1.0                       (v2.4.0)
      relaxed : Green/Red <= 1.15                      (admits mildly green px)
      off     : no green-peak term at all
      override: strict, but a pixel carrying BOTH iron and clay bypasses it
    """
    iron, f1 = c.select("IronSulfate"), c.select("FerricIron1")
    f2, fe2 = c.select("FerricIron2"), c.select("FerrousIron")
    clay, gv = c.select("ClaySulfateMica"), c.select("GreenVeg")
    ndvi, mndwi = c.select("NDVI"), c.select("MNDWI")
    bright, awei = c.select("Brightness"), c.select("AWEINSH")
    b3, b4, b5, b6 = (c.select("SR_B3"), c.select("SR_B4"),
                      c.select("SR_B5"), c.select("SR_B6"))

    has_iron, has_f1 = iron.gt(T["iron"]), f1.gt(T["ferric1"])
    has_f2, has_fe2 = f2.gt(T["ferric2"]), fe2.gt(T["ferrous"])
    has_clay = clay.gt(T["clay"])
    sparse = gv.gt(T["green_veg"]).And(gv.lte(T["dense_veg"]))
    dense = gv.gt(T["dense_veg"])

    water = (mndwi.gt(T["water"]).And(awei.gt(0.0)).And(ndvi.lt(0.0))
             .And(b5.lt(b3)).And(bright.lt(0.30)))
    built = (bright.gt(T["bu_bright"]).And(ndvi.lt(T["bu_ndvi_hi"]))
             .And(ndvi.gt(T["bu_ndvi_lo"]))
             .And(mndwi.lt(T["bu_mndwi"])
                  .Or(mndwi.gt(-0.10).And(mndwi.lt(0.10)))))
    not_bright = bright.lt(T["bright_max"])
    not_dark = b6.gt(T["dark"]).And(bright.gt(0.05))

    green_red = b3.divide(b4)
    if veg_gate == "strict":
        no_green_peak = green_red.lte(1.0)
    elif veg_gate == "relaxed":
        no_green_peak = green_red.lte(1.15)
    elif veg_gate == "off":
        no_green_peak = ee.Image(1)
    elif veg_gate == "override":
        no_green_peak = green_red.lte(1.0).Or(has_iron.And(has_clay))
    else:
        raise ValueError("unknown veg_gate %r" % veg_gate)

    veg_road = no_green_peak.And(
        ndvi.lt(T["ndvi_max"]).Or(has_iron.And(b6.lt(0.20)).And(gv.lt(3.5))))
    land = (water.Not().And(not_bright).And(not_dark)
            .And(built.Not()).And(veg_road))
    classify.last_land = land.rename("land")

    out = ee.Image(0)

    def assign(cond, val):
        nonlocal out
        out = out.where(cond.And(out.eq(0)), val)

    assign(has_iron.And(has_f1).And(has_f2).And(has_clay).And(land).And(not_bright), 9)
    assign(has_iron.And(has_f1).And(has_f2).And(has_clay).And(land), 17)
    assign(has_iron.And(has_f1).And(has_f2.Not()).And(has_clay).And(land), 12)
    assign(has_iron.And(has_f1.Not()).And(has_f2).And(has_clay).And(land), 18)
    assign(has_iron.And(has_fe2).And(has_clay).And(land), 19)
    assign(has_iron.And(has_clay).And(has_f1.Not()).And(has_f2.Not()).And(land), 14)
    if iron_fallback:
        assign(has_iron.And(land), 12)
    assign(has_clay.And(has_f1).And(has_f2).And(has_iron.Not()).And(land), 8)
    assign(has_clay.And(has_f1.Or(has_f2)).And(has_iron.Not()).And(land), 7)
    assign(has_clay.And(has_f1).And(has_f2.Not()).And(has_iron.Not()).And(land), 6)
    assign(has_clay.And(has_f1.Not()).And(has_iron.Not()).And(land), 5)
    assign(has_clay.And(has_fe2).And(has_iron.Not()).And(land), 10)
    assign(has_f1.And(has_f2).And(has_clay.Not()).And(has_iron.Not()).And(land), 2)
    assign(has_f1.And(has_fe2).And(has_clay.Not()).And(has_iron.Not()).And(land), 3)
    assign(has_f1.And(has_f2.Not()).And(has_clay.Not()).And(has_iron.Not()).And(land), 1)
    assign(has_fe2.And(has_clay.Not()).And(has_f1.Not()).And(has_iron.Not()).And(land), 4)
    assign(sparse.And(has_f1).And(has_iron.Not()).And(water.Not()), 13)
    assign(dense.And(has_iron.Not()).And(water.Not()), 11)
    return out.rename("class")


def run(ee, site, n_pixels, seed):
    lon, lat, buf = SITES[site]
    region = ee.Geometry.Point([lon, lat]).buffer(buf)
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(START, END)
           .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[-1], "month"))
           .map(lambda i: process_landsat(ee, i))
           .map(lambda i: add_indices(ee, i)))
    n = col.size().getInfo()
    comp = col.median().clip(region)
    cls = classify(ee, comp).unmask(0)
    stack = comp.select(["SR_B1", "SR_B2", "SR_B3", "SR_B4",
                         "SR_B5", "SR_B6", "SR_B7"]).addBands(cls)
    fc = stack.sample(region=region, scale=30, numPixels=n_pixels,
                      seed=seed, geometries=True, dropNulls=True)
    feats = fc.getInfo()["features"]
    rows = []
    for f in feats:
        p = dict(f["properties"])
        c = f["geometry"]["coordinates"]
        p["lon"], p["lat"] = c[0], c[1]
        rows.append(p)
    return n, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", required=True, choices=sorted(SITES))
    ap.add_argument("--pixels", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    ee = init_ee()
    n, rows = run(ee, args.site, args.pixels, args.seed)
    print("%s: %d Landsat 8 summer scenes 2013-2020, %d sampled pixels"
          % (args.site, n, len(rows)))
    if not rows:
        return
    out = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
        "imagery", "GEE_%s.csv" % args.site.replace(", ", "_").replace(" ", "_"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cols = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7",
            "class", "lon", "lat"]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("class distribution:",
          dict(sorted(Counter(int(r.get("class", 0)) for r in rows).items())))
    print("->", out)


if __name__ == "__main__":
    main()
