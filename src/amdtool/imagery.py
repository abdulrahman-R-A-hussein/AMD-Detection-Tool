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
    return (mndwi.gt(WATER_MNDWI).And(awei.gt(0.0)).And(ndvi.lt(0.0))
            .And(b5.lt(b3)).And(bright.lt(0.30)))


def green_nir_ee(ee_image, green_band, nir_band):
    """Earth Engine version: adds GreenNIR and GreenNIRNorm bands to an image
    that already carries `green_band`/`nir_band`. Caller must have already
    excluded water pixels (see module docstring) - this function does not
    apply any water mask itself, so it can be reused for whatever land subset
    a caller defines (shoreline buffer, streambed at low flow, adit outflow
    polygon, ...).

    Adds GreenNIR and GreenNIRNorm. Applies no water mask itself.
    """
    green = ee_image.select(green_band)
    nir = ee_image.select(nir_band)
    ratio = green.divide(nir.add(EPS)).rename("GreenNIR")
    norm = (green.subtract(nir)).divide(green.add(nir).add(EPS)).rename("GreenNIRNorm")
    return ee_image.addBands([ratio, norm])


def ndvi_stress_ee(ee_image, nir_band, red_band):
    """Standard NDVI, kept here (not in gee_classify.py's NDVI) so Arm C's
    vegetation-stress analysis has one clearly-labelled entry point tied back
    to paper2 sec. 3.2.1 rather than reusing the land-classifier's NDVI band
    for a different purpose without a name change.

    Standard NDVI under a distinct name. Higher = MORE vegetated.
    """
    nir, red = ee_image.select(nir_band), ee_image.select(red_band)
    return nir.subtract(red).divide(nir.add(red).add(EPS)).rename("NDVI_stress")


def index_image(ee, comp):
    """Add the paper2 indices and drop water pixels.

    Water exclusion is the whole point of the B1/B2 split: Green:NIR is
    degenerate on open water (all water absorbs NIR), so applied to a lake it
    detects water, not sulfur. Uses the classifier's OWN water term
    (gee_classify.water_term) rather than a second definition, and deliberately
    NOT the full `land` mask, which would also drop bright/dark/built/vegetated
    pixels and remove legitimate precipitate targets.

    Add the paper2 indices and drop water pixels (the classifier's own water
    term, deliberately NOT the full land mask, which would remove legitimate
    precipitate targets).
    """
    img = green_nir_ee(comp, "SR_B3", "SR_B5")
    img = img.addBands(ndvi_stress_ee(img, "SR_B5", "SR_B4"))
    return img.updateMask(water_term(ee, comp).Not())


# ------------------------------------------------------------ composites

def composite_for_region(ee, region, months=None, start=START, end=END):
    """General-purpose composite builder over an arbitrary geometry (a
    catchment polygon, not one of the fixed SITES). months defaults to
    V3_MONTHS (May-Jul, the paper-faithful season, finding L4).

    Landsat 8 collection over an arbitrary geometry. months defaults to
    V3_MONTHS (May-Jul). Returns (collection, ee.Number size).
    """
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
    """Landsat composite for a named season, with snow masked and scenes capped.

    season="leafoff" -> Nov-Mar. That range WRAPS the year boundary, so it needs
    an Or of two calendarRange filters; calendarRange(11, 3) is empty, not
    inclusive, and would silently return nothing.

    SNOW MASKING is required for winter imagery and is not in the standard
    process_landsat() path: QA_PIXEL bit 5 is snow/ice. Snow is bright and
    seasonal, so leaving it in would create a season-dependent artifact that
    could masquerade as either signal or canopy relief - registered in
    CMD1 amendment 1 before this was run.

    Landsat composite for a named season, snow masked, scenes capped.
    season="leafoff" -> Nov-Mar, which WRAPS the year boundary and so needs an
    Or of two calendarRange filters (calendarRange(11, 3) is empty). Snow is
    QA_PIXEL bit 5 and is masked, because leaving it in would create a season-
    dependent artifact.
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
    """Sentinel-2 SR mapped onto the SR_B1..SR_B7 naming the rest of the
    toolchain uses (match_scenes.S2_MAP), so add_indices() and classify_v3()
    work unchanged. B8A not B8 for SR_B5, matching Landsat 8 B5's 865 nm -
    the same choice match_scenes.py already made and validated.

    B8 (842 nm, 10 m) is carried separately as SR_B8_10 purely for the
    resolution ladder's genuine-10 m green:NIR; it is NOT substituted into the
    SIM 3466 indices, which would silently change their definition.

    SCL classes 1, 3, 8, 9, 10 are masked; snow (11) is NOT.
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

    # CLOUD FILTER IS LOAD-BEARING, not cosmetic. Silverton returns 554 S2
    # scenes in the May-Jul window (Ouray 276) against Landsat's handful, and a
    # median over 554 images with add_indices mapped onto each exceeds the EE
    # memory limit before any tiling or batching downstream can help - retries
    # cannot fix a graph that is too large to build. Capping cloud cover cuts
    # the collection several-fold AND improves the composite, since >60% cloudy
    # scenes contribute almost nothing after SCL masking anyway.
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

    Batch size is small and halves on failure because "User memory limit
    exceeded" here is about SERVER COMPUTE-GRAPH SIZE, not pixel count - the
    recurring trap in this project. Each buffer in the collection re-evaluates
    the whole median-composite-plus-indices graph, so cost scales with batch
    size, and bestEffort does not help because it only mitigates pixel count.
    150 fails; 25 succeeds.
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
                        # EE DROPS THE BAND PREFIX when the image has exactly
                        # one band: properties come back as "mean"/"p90"/
                        # "count", not "<band>_mean". Silently produced an
                        # all-NaN AMDclassFrac column on the first Silverton
                        # run. Normalise so callers see one naming scheme.
                        if len(bands) == 1 and "mean" in pr:
                            for s in ("p90", "mean", "count"):
                                if s in pr:
                                    pr["%s_%s" % (bands[0], s)] = pr.pop(s)
                        out[pr["pid"]] = pr
                break
            except Exception as exc:                       # noqa: BLE001
                # 2026-09-09: floor lowered 2 -> 1. Moshannon Creek, PA (162
                # stations, 120 scenes) failed the 500/1000 m ladder at
                # batch=2 with the band subset ALREADY applied, so the two
                # known request-size levers were exhausted.
                #
                # batch=1 is a request-size change, not a method change: each
                # buffer's p90/mean/count is computed independently, so how
                # many buffers share one reduceRegions call cannot affect any
                # of their values. Only the HTTP request count changes.
                #
                # MEASURED, not assumed: batch=1 vs batch=25 over 20 Chest
                # Creek stations at 500 m gives max abs difference 1.11e-16 -
                # one double-precision ULP, i.e. float representation noise.
                # Note this is NOT bit-identical the way the band subset is
                # (that one measures exactly 0.000 over 27 stations). The
                # difference is ~1e-16 relative and cannot move a Spearman
                # rank, but say "identical to within float epsilon", never
                # "identical".
                #
                # Contrast the SCENE CAP, which is the tempting next lever and
                # is NOT safe: a shallower stack is a different median
                # composite and different numbers. Never reduce it for one
                # region and pool the result with regions that kept 120.
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
