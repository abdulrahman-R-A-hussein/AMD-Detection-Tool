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


# v3.0.x scene-relative multipliers (earth-engine/amd_detection_v2.4.0.js,
# useStdDevThresholds block) - threshold = scene mean + k * scene stdDev,
# computed over the region being classified. ironStdMult/clayStdMult were
# LOSO-fitted (validation/REPLICA_AUDIT_2026-07-26.md); the ferric/ferrous
# multipliers are set to match by assumption and remain uncalibrated.
V3_STD_MULT = dict(iron=0.5, ferric1=0.5, ferric2=0.5, ferrous=0.5, clay=0.25)
V3_NDVI_MAX = 0.35
V3_MONTHS = [5, 6, 7]


def tiled_mean_stddev(ee, image, bands, region, n_tiles=4, scale=30):
    """Pooled mean/stdDev per band, computed from TILED sum/sumSq/count.

    A single whole-region reduceRegion(mean.combine(stdDev)) over a large,
    many-scene composite trips "User memory limit exceeded" even with
    bestEffort=True and a simplified geometry - that error is about server
    compute-graph size, not pixel count, and bestEffort only mitigates the
    latter. Tiling the SAME reducer call the way tile_geoms/frequencyHistogram
    already do successfully elsewhere in this project, then combining the
    tile-level sums in Python (not in EE), sidesteps it entirely: each tile's
    reduceRegion is small enough to evaluate, and pooling sum/sumSq/count
    algebraically reproduces the exact whole-region mean/stdDev.
    """
    from diagnose_veg_gate import tile_geoms

    sq = image.select(bands).pow(2).rename([b + "_sq" for b in bands])
    stack = image.select(bands).addBands(sq)
    sums = {b: 0.0 for b in bands}
    sqsums = {b: 0.0 for b in bands}
    counts = {b: 0 for b in bands}
    for cell in tile_geoms(ee, region, n_tiles):
        r = stack.reduceRegion(reducer=ee.Reducer.sum().combine(
            ee.Reducer.count(), "", True), geometry=cell, scale=scale,
            maxPixels=int(1e9), bestEffort=True).getInfo()
        for b in bands:
            v = r.get(b + "_sum")
            vsq = r.get(b + "_sq_sum")
            n = r.get(b + "_count")
            if v is not None:
                sums[b] += v
            if vsq is not None:
                sqsums[b] += vsq
            if n:
                counts[b] += n

    out = {}
    for b in bands:
        n = counts[b]
        if not n:
            out[b + "_mean"], out[b + "_stdDev"] = 0.0, 0.0
            continue
        mean = sums[b] / n
        var = max(0.0, sqsums[b] / n - mean * mean)
        out[b + "_mean"], out[b + "_stdDev"] = mean, var ** 0.5
    return out


def bare_land_mask(ee, c, ndvi_max=V3_NDVI_MAX):
    """Threshold-INDEPENDENT bare/land mask, for computing threshold statistics.

    Deliberately NOT the classifier's full `land` term. That one contains an
    escape clause - `.Or(has_iron.And(b6.lt(0.20)).And(gv.lt(3.5)))` - which
    depends on the iron threshold itself. Using it to compute the iron
    threshold would be circular: the mask would define the statistic that
    defines the mask. This variant keeps every threshold-free term (water,
    brightness, darkness, built-up, green-peak, NDVI) and drops only the
    iron-dependent escape, so it can be computed before any threshold exists.
    """
    ndvi, mndwi = c.select("NDVI"), c.select("MNDWI")
    bright = c.select("Brightness")
    b3, b4, b6 = c.select("SR_B3"), c.select("SR_B4"), c.select("SR_B6")

    water = water_term(ee, c)
    built = (bright.gt(T["bu_bright"]).And(ndvi.lt(T["bu_ndvi_hi"]))
             .And(ndvi.gt(T["bu_ndvi_lo"]))
             .And(mndwi.lt(T["bu_mndwi"])
                  .Or(mndwi.gt(-0.10).And(mndwi.lt(0.10)))))
    not_bright = bright.lt(T["bright_max"])
    not_dark = b6.gt(T["dark"]).And(bright.gt(0.05))
    no_green_peak = b3.divide(b4).lte(1.0)
    return (water.Not().And(not_bright).And(not_dark).And(built.Not())
            .And(no_green_peak).And(ndvi.lt(ndvi_max)))


def bare_subset_stats(ee, c, region, bands, n_tiles=4, scale=30,
                      ndvi_max=V3_NDVI_MAX):
    """Scene statistics over the BARE/LAND subset instead of the whole region.

    THE POINT (Phase B2b, validation/B2B_PREREGISTRATION_2026-08-16.md):
    whole-region statistics include vegetation and water, whose iron-index
    values are low. They drag the scene mean down, so `mean + 0.5*sd` admits a
    large share of ORDINARY BARE GROUND. Since the classifier's NDVI gate
    already requires a pixel to be unvegetated before any AMD class is
    assigned, the effective question becomes "bare, and iron-rich compared with
    grass and water" - which most bare pixels pass. Measured consequence:
    AMDclassFrac scores worst-case LORO J = 0.000 against NLCD bare ground
    while FerricIron1 alone scores +0.318.

    Restricting the statistics to bare land makes the threshold ask the
    question that actually discriminates: iron-rich compared with OTHER BARE
    GROUND in the same scene.
    """
    return tiled_mean_stddev(ee, c.updateMask(bare_land_mask(ee, c, ndvi_max)),
                             bands, region, n_tiles=n_tiles, scale=scale)


def classify_v3(ee, c, region, scale=30, iron_fallback=False, n_tiles=4):
    """The v3.0.x cascade: scene-relative thresholds + relaxed NDVI gate + no
    iron fallback, matching earth-engine/amd_detection_v2.4.0.js as shipped.

    Unlike classify(), thresholds are computed from `region`'s own pixel
    statistics (Rockwell's own method, SIM 3466 "common standard deviation
    threshold"), via tiled_mean_stddev() rather than a single whole-region
    reduceRegion - see that function's docstring for why. Stats are plain
    Python floats by construction here, so no lazy ee.Number is ever chained
    into the classification expression.
    """
    stats = tiled_mean_stddev(
        ee, c, ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
               "ClaySulfateMica"], region, n_tiles=n_tiles, scale=scale)

    def cut(band, mult):
        return stats[band + "_mean"] + stats[band + "_stdDev"] * mult

    t = dict(
        iron=cut("IronSulfate", V3_STD_MULT["iron"]),
        ferric1=cut("FerricIron1", V3_STD_MULT["ferric1"]),
        ferric2=cut("FerricIron2", V3_STD_MULT["ferric2"]),
        ferrous=cut("FerrousIron", V3_STD_MULT["ferrous"]),
        clay=cut("ClaySulfateMica", V3_STD_MULT["clay"]),
    )
    return classify(ee, c, veg_gate="strict", iron_fallback=iron_fallback,
                    ndvi_max=V3_NDVI_MAX, thresholds=t)


def water_term(ee, c):
    """The classifier's own water test, factored out unchanged.

    Extracted 2026-08-14 for Arm B2, which must exclude water pixels WITHOUT
    applying the rest of the land gate: paper2's Green:NIR is degenerate on
    open water (every water pixel absorbs NIR and scores high), but the full
    `land` mask also drops bright/dark/built/vegetated pixels, which would
    remove legitimate precipitate targets. Factored rather than copied so the
    two definitions cannot drift apart - classify() calls this.
    """
    ndvi, mndwi = c.select("NDVI"), c.select("MNDWI")
    bright, awei = c.select("Brightness"), c.select("AWEINSH")
    b3, b5 = c.select("SR_B3"), c.select("SR_B5")
    return (mndwi.gt(T["water"]).And(awei.gt(0.0)).And(ndvi.lt(0.0))
            .And(b5.lt(b3)).And(bright.lt(0.30)))


STAT_BANDS = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
              "ClaySulfateMica"]


def classify_v4_from_stats(ee, c, stats, k_bare=0.5, clay_bare=0.25,
                           iron_fallback=False):
    """v4 cascade from PRE-COMPUTED statistics.

    Split out so a parameter sweep computes the (expensive, tiled) scene
    statistics ONCE per region and reuses them across every grid point - the
    multipliers only rescale an already-known mean and sd, so recomputing them
    per grid point would be 8x the Earth Engine cost for identical numbers.
    """
    def cut(band, mult):
        return stats[band + "_mean"] + stats[band + "_stdDev"] * mult

    t = dict(iron=cut("IronSulfate", k_bare),
             ferric1=cut("FerricIron1", k_bare),
             ferric2=cut("FerricIron2", k_bare),
             ferrous=cut("FerrousIron", k_bare),
             clay=cut("ClaySulfateMica", clay_bare))
    return classify(ee, c, veg_gate="strict", iron_fallback=iron_fallback,
                    ndvi_max=V3_NDVI_MAX, thresholds=t)


def classify_v4(ee, c, region, scale=30, iron_fallback=False, n_tiles=4,
                k_bare=0.5, clay_bare=0.25, whole_region=False):
    """v4: identical cascade to v3, thresholds relative to BARE GROUND.

    The ONLY difference from classify_v3() is where the mean/sd come from.
    Cascade order, class codes, first-match-wins and NAP ranks are untouched,
    so any change in output is attributable to the statistics and nothing else.

    `whole_region=True` reproduces v3's statistics exactly, which is the
    equivalence test required by the plan: with it set, v4 must equal v3.
    """
    stats = (tiled_mean_stddev(ee, c, STAT_BANDS, region, n_tiles=n_tiles,
                               scale=scale) if whole_region else
             bare_subset_stats(ee, c, region, STAT_BANDS, n_tiles=n_tiles,
                               scale=scale))

    def cut(band, mult):
        return stats[band + "_mean"] + stats[band + "_stdDev"] * mult

    t = dict(iron=cut("IronSulfate", k_bare),
             ferric1=cut("FerricIron1", k_bare),
             ferric2=cut("FerricIron2", k_bare),
             ferrous=cut("FerrousIron", k_bare),
             clay=cut("ClaySulfateMica", clay_bare))
    return classify(ee, c, veg_gate="strict", iron_fallback=iron_fallback,
                    ndvi_max=V3_NDVI_MAX, thresholds=t)


def classify(ee, c, veg_gate="strict", iron_fallback=True, ndvi_max=None,
            thresholds=None):
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

    th = thresholds or T                        # accepts ee.Number overrides
    has_iron, has_f1 = iron.gt(th["iron"]), f1.gt(th["ferric1"])
    has_f2, has_fe2 = f2.gt(th["ferric2"]), fe2.gt(th["ferrous"])
    has_clay = clay.gt(th["clay"])
    sparse = gv.gt(T["green_veg"]).And(gv.lte(T["dense_veg"]))
    dense = gv.gt(T["dense_veg"])

    water = water_term(ee, c)
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
        ndvi.lt(ndvi_max if ndvi_max is not None else T["ndvi_max"])
        .Or(has_iron.And(b6.lt(0.20)).And(gv.lt(3.5))))
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


def composite_for_region(ee, region, months=None, start=START, end=END):
    """General-purpose composite builder over an arbitrary geometry (a
    catchment polygon, not one of the fixed SITES). months defaults to
    V3_MONTHS (May-Jul, the paper-faithful season, finding L4)."""
    months = months or V3_MONTHS
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(start, end)
           .filter(ee.Filter.calendarRange(months[0], months[-1], "month"))
           .map(lambda i: process_landsat(ee, i))
           .map(lambda i: add_indices(ee, i)))
    return col, col.size()


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
