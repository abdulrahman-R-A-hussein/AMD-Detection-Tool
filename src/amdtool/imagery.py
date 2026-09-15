"""Earth Engine imagery: composites, indices, buffer extraction, landscape points.

Moved 2026-09-14, bodies unchanged, from:
  python/gee_classify.py   process_landsat, add_indices, water_term,
                           composite_for_region (and START/END, V3_MONTHS,
                           the water threshold T["water"])
  python/seep_detect.py    l8_composite, s2_composite, index_image,
                           _chunks, extract_buffers
  python/cmd_detect.py     l8_composite_season
  python/match_scenes.py   S2_MAP
  python/water_indices.py  green_nir_ee, ndvi_stress_ee (and EPS)

The only edits: the memory-retry message goes to `logging` instead of `print`,
and `random_landscape_points` is new (for the blind-search test).

`ee` is always a parameter. amdtool never imports or initialises Earth Engine,
so a host application owns authentication.
"""

import logging

log = logging.getLogger(__name__)

START, END = "2013-01-01", "2020-12-31"
V3_MONTHS = [5, 6, 7]            # May-Jul, the paper-faithful season (finding L4)
MIN_SCENES = 3
S2_MAX_CLOUD = 20                # percent; see s2_composite() for why this matters
S2_MAX_SCENES = 120
L8_MAX_SCENES = 120
WATER_MNDWI = 0.3                # gee_classify.T["water"]
EPS = 1e-4                       # water_indices.EPS

INDEX_BANDS = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
               "ClaySulfateMica", "GreenNIR", "GreenNIRNorm", "NDVI_stress"]

S2_MAP = [("B1", "SR_B1"), ("B2", "SR_B2"), ("B3", "SR_B3"), ("B4", "SR_B4"),
          ("B8A", "SR_B5"), ("B11", "SR_B6"), ("B12", "SR_B7")]


# ------------------------------------------------------------ bands and indices

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


def water_term(ee, c):
    """The classifier's own water test, factored out unchanged."""
    ndvi, mndwi = c.select("NDVI"), c.select("MNDWI")
    bright, awei = c.select("Brightness"), c.select("AWEINSH")
    b3, b5 = c.select("SR_B3"), c.select("SR_B5")
    return (mndwi.gt(WATER_MNDWI).And(awei.gt(0.0)).And(ndvi.lt(0.0))
            .And(b5.lt(b3)).And(bright.lt(0.30)))


def green_nir_ee(ee_image, green_band, nir_band):
    """Adds GreenNIR and GreenNIRNorm. Applies no water mask itself."""
    green = ee_image.select(green_band)
    nir = ee_image.select(nir_band)
    ratio = green.divide(nir.add(EPS)).rename("GreenNIR")
    norm = (green.subtract(nir)).divide(green.add(nir).add(EPS)).rename("GreenNIRNorm")
    return ee_image.addBands([ratio, norm])


def ndvi_stress_ee(ee_image, nir_band, red_band):
    """Standard NDVI under a distinct name. Higher = MORE vegetated."""
    nir, red = ee_image.select(nir_band), ee_image.select(red_band)
    return nir.subtract(red).divide(nir.add(red).add(EPS)).rename("NDVI_stress")


def index_image(ee, comp):
    """Add the paper2 indices and drop water pixels (the classifier's own water
    term, deliberately NOT the full land mask, which would remove legitimate
    precipitate targets)."""
    img = green_nir_ee(comp, "SR_B3", "SR_B5")
    img = img.addBands(ndvi_stress_ee(img, "SR_B5", "SR_B4"))
    return img.updateMask(water_term(ee, comp).Not())


# ------------------------------------------------------------ composites

def composite_for_region(ee, region, months=None, start=START, end=END):
    """Landsat 8 collection over an arbitrary geometry. months defaults to
    V3_MONTHS (May-Jul). Returns (collection, ee.Number size)."""
    months = months or V3_MONTHS
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(start, end)
           .filter(ee.Filter.calendarRange(months[0], months[-1], "month"))
           .map(lambda i: process_landsat(ee, i))
           .map(lambda i: add_indices(ee, i)))
    return col, col.size()


def l8_composite(ee, region):
    col, size = composite_for_region(ee, region)
    return col.median().clip(region), int(size.getInfo())


def l8_composite_season(ee, region, season="leafoff", max_scenes=L8_MAX_SCENES):
    """Landsat composite for a named season, snow masked, scenes capped.

    season="leafoff" -> Nov-Mar, which WRAPS the year boundary and so needs an
    Or of two calendarRange filters (calendarRange(11, 3) is empty). Snow is
    QA_PIXEL bit 5 and is masked, because leaving it in would create a
    season-dependent artifact.
    """
    if season == "leafoff":
        mfilter = ee.Filter.Or(ee.Filter.calendarRange(11, 12, "month"),
                               ee.Filter.calendarRange(1, 3, "month"))
    else:
        mfilter = ee.Filter.calendarRange(5, 7, "month")

    def prep(img):
        snow = img.select("QA_PIXEL").bitwiseAnd(1 << 5).eq(0)
        return add_indices(ee, process_landsat(ee, img).updateMask(snow))

    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(START, END).filter(mfilter)
           .sort("CLOUD_COVER").limit(max_scenes).map(prep))
    return col.median().clip(region), int(col.size().getInfo())


def s2_composite(ee, region):
    """Sentinel-2 SR mapped onto SR_B1..SR_B7, B8A (not B8) as SR_B5 to match
    Landsat 8 B5. SCL classes 1, 3, 8, 9, 10 masked; snow (11) is NOT.

    The cloud filter and the 120-scene cap are load-bearing: without them the
    median exceeds Earth Engine's compute-graph limit before any downstream
    tiling or batching can help.
    """
    def prep(img):
        scl = img.select("SCL")
        clear = (scl.neq(1).And(scl.neq(3)).And(scl.neq(8))
                 .And(scl.neq(9)).And(scl.neq(10)))
        b = img.updateMask(clear)
        scaled = (b.select([s for s, _ in S2_MAP])
                  .divide(10000).clamp(0.0, 1.0)
                  .rename([d for _, d in S2_MAP]))
        nir10 = b.select("B8").divide(10000).clamp(0.0, 1.0).rename("SR_B8_10")
        return add_indices(ee, scaled.addBands(nir10))

    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(region).filterDate(START, END)
           .filter(ee.Filter.calendarRange(V3_MONTHS[0], V3_MONTHS[-1], "month"))
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", S2_MAX_CLOUD))
           .sort("CLOUDY_PIXEL_PERCENTAGE").limit(S2_MAX_SCENES)
           .map(prep))
    return col.median().clip(region), int(col.size().getInfo())


# ------------------------------------------------------------ extraction

def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def extract_buffers(ee, img, points, radius_m, scale, bands, batch=25):
    """p90 + mean + valid-pixel count per buffer, one reduceRegions per batch.

    points: [{"pid", "lat", "lon"}]. Returns {pid: {"<band>_p90",
    "<band>_mean", "<band>_count", "pid"}}.

    Batch size halves on "User memory limit exceeded", down to 1. That limit is
    about server compute-graph size, not pixel count. Batch size and band
    subset are request-size levers that do not change the numbers (band subset
    bit-identical; batch=1 vs 25 differs by 1.1e-16). The scene cap is NOT such
    a lever - never reduce it for one region and pool the result.
    """
    red = (ee.Reducer.percentile([90])
           .combine(ee.Reducer.mean(), "", True)
           .combine(ee.Reducer.count(), "", True))
    sel = img.select(bands)
    out = {}
    for grp in _chunks(points, batch):
        size = len(grp)
        while True:
            try:
                for sub in _chunks(grp, size):
                    fc = ee.FeatureCollection([
                        ee.Feature(ee.Geometry.Point([p["lon"], p["lat"]])
                                   .buffer(radius_m), {"pid": p["pid"]})
                        for p in sub])
                    got = sel.reduceRegions(collection=fc, reducer=red,
                                            scale=scale).getInfo()["features"]
                    for f in got:
                        pr = f["properties"]
                        # Earth Engine drops the band prefix when the image
                        # has exactly one band. Normalise so callers see one
                        # naming scheme.
                        if len(bands) == 1 and "mean" in pr:
                            for s in ("p90", "mean", "count"):
                                if s in pr:
                                    pr["%s_%s" % (bands[0], s)] = pr.pop(s)
                        out[pr["pid"]] = pr
                break
            except Exception as exc:                       # noqa: BLE001
                if "memory" not in str(exc).lower() or size <= 1:
                    raise
                size = max(1, size // 2)
                log.info("memory limit - retrying at batch=%d", size)
    return out


def random_landscape_points(ee, region, n, seed, prefix="LS"):
    """n uniformly random points in `region`, deterministic for a given seed.

    Returns [{"pid", "lat", "lon"}] with pids "<prefix>00000", ... in the order
    Earth Engine returns them. Used as the label-free landscape sample that
    sets a district's score cutoff.
    """
    fc = ee.FeatureCollection.randomPoints(region=region, points=n, seed=seed)
    feats = fc.getInfo()["features"]
    out = []
    for i, f in enumerate(feats):
        lon, lat = f["geometry"]["coordinates"][:2]
        out.append({"pid": "%s%05d" % (prefix, i), "lat": lat, "lon": lon})
    return out
