"""Arm B2 - seep / precipitate detection at chemically-confirmed AMD source points.

READ `validation/B2_PREREGISTRATION_2026-08-14.md` FIRST. Every analysis choice
in this module - buffer radius, within-buffer statistic, primary metric, null
model, multiple-comparison family and the decision rule - was fixed and
committed (4bb3b63) BEFORE any imagery was extracted. Anything done differently
later must be labelled exploratory in the report.

WHAT THIS TESTS, PRECISELY: whether LAND-SURFACE ferric precipitate ("yellow
boy") around mine adits, discharges, tailings piles and springs is optically
separable from non-source ground. It does NOT test dissolved iron or sulfate.
Sulfate has no VNIR absorption, and the water-column hypothesis is already a
clean null (WATER_PHASE2_2026-08-10.md). Output wording must reflect that.

THE THREE CONTROL TIERS EXIST BECAUSE ONE IS NOT ENOUGH. Mine sites are roads,
tailings and disturbed unvegetated ground. Without the bare-ground tier (C3),
"detects iron precipitate" and "detects anything unvegetated" are the same
number. A result that beats C1 and C2 but not C3 is a bare-ground detector and
is reported as one.

    python seep_detect.py --extract          # GEE -> data/matched/seep_*.csv
    python seep_detect.py --analyse          # csv -> stats, no GEE needed
    python seep_detect.py --degrade          # S2 resolution ladder

Interpreter: D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe (needs
`ee`; the repo .venv does not have it).
"""

import argparse
import csv
import json
import math
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "data", "matched")

# ------------------------------------------------------------------ FIXED
# Pre-registered 2026-08-14. Do not tune these to the outcome.

REGIONS = {                      # slug -> fetch_wqp.REGIONS key
    "silverton_co":    "Silverton, CO",
    "leadville_co":    "Leadville, CO",
    "ouray_co":        "Ouray, CO",
    "central_city_co": "Central City, CO",
}
# Excluded from the primary analysis (n < 10 source points): a region-level
# fold cannot be built from 3 or 1 points. Extracted and reported separately.
THIN_REGIONS = {"creede_co": "Creede, CO", "alma_co": "Alma, CO"}

SEED = 20260814
RADII = [30, 60, 100]
PRIMARY_RADIUS = 60
PRIMARY_STAT = "p90"
CONTROL_EXCLUDE_M = 500.0        # min distance of C2/C3 from ANY source point
CONTROLS_PER_TARGET = 5
ELEV_TOL_M = 100.0
SLOPE_TOL_DEG = 5.0
NDVI_BARE_PCTL = 25              # C3 draws below this percentile
MIN_SCENES = 3
S2_MAX_CLOUD = 20        # percent; see s2_composite() for why this matters
# Hard cap on scenes entering the S2 median. The cloud filter alone was still
# not enough for Silverton (278 scenes after filtering, still over the limit),
# and "tighten the threshold until it fits" would make the composite depend on
# a region's weather. Taking the N LEAST-CLOUDY scenes is deterministic, gives
# every region the same compositing depth, and caps graph size directly - the
# actual constraint. 120 x 5-day revisit over May-Jul still spans many years.
S2_MAX_SCENES = 120
N_PERM = 10000                   # primary family
N_PERM_SENS = 2000               # sensitivity radii / statistics
J_THRESHOLD = 0.25               # decision rule, with BH p < 0.05

AMD_CLASSES = (9, 12, 14, 17, 18, 19)

# The 8 reduceRegions bands + the 9th index (AMD class fraction) computed
# separately because it comes from the classifier, not a band ratio.
INDEX_BANDS = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
               "ClaySulfateMica", "GreenNIR", "GreenNIRNorm", "NDVI_stress"]
ALL_INDICES = INDEX_BANDS + ["AMDclassFrac"]

# Native ground sample distance of the bands each index needs. Sentinel-2 is
# NOT 10 m for most of this panel: the SIM 3466 set needs SWIR (B11/B12, 20 m)
# and IronSulfate needs the coastal band (B1, 60 m). Only FerricIron1 (red/blue)
# and the paper2 green:NIR pair are genuinely 10 m. Recorded here so the
# resolution curve reports honest effective resolution instead of the nominal
# collection resolution - otherwise the 10 m tier would be a fiction for 6 of 9.
S2_NATIVE_M = {"IronSulfate": 60, "FerricIron1": 10, "FerricIron2": 20,
               "FerrousIron": 20, "ClaySulfateMica": 20, "GreenNIR": 10,
               "GreenNIRNorm": 10, "NDVI_stress": 10, "AMDclassFrac": 60}


# ------------------------------------------------------------------ points

def load_region_points(slug):
    """Split a region's stations into source points (targets) and in-stream
    controls (C1), reusing the loaders that already exist rather than
    re-parsing WQP here.

    A point qualifies if it is a source-type station (fetch_wqp
    SOURCE_POINT_TYPES) that appears in consolidated.csv - i.e. it has at least
    one fetched water-chemistry record, so it is a MONITORED discharge, not a
    map label. That is exactly the definition the pre-registered n=86 was
    counted from, and it is reproduced here rather than re-derived, so the
    sample cannot drift from what was registered.

    Two definitions were rejected, both recorded here because either would have
    silently changed n after the fact:
      - stations.csv alone -> 307 targets, most with no water chemistry at all;
      - load_station_chemistry() alone -> 85, because it keeps only
        Iron/Sulfate/pH/conductance and one Silverton source point reports
        none of those.
    Chemistry is attached where available, for the dose-response test only; the
    DETECTION test needs none.
    """
    from watershed_nap import load_station_chemistry
    from fetch_wqp import site_category

    chem_dir = os.path.join(ROOT, "data", "chemistry", slug)
    chem = load_station_chemistry(chem_dir, 0)

    seen = {}
    with open(os.path.join(chem_dir, "consolidated.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            seen[r["MonitoringLocationIdentifier"]] = r.get("site_category", "")

    targets, instream = [], []
    with open(os.path.join(chem_dir, "stations.csv"), encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            sid = s["station_id"]
            if sid not in seen or not s.get("lat") or not s.get("lon"):
                continue
            stype = s.get("site_type", "")
            rec = dict(chem.get(sid, {}))
            rec.update(pid=sid, region=slug, site_type=stype,
                       name=s.get("station_name", sid),
                       lat=float(s["lat"]), lon=float(s["lon"]))
            (targets if site_category(stype) == "source"
             else instream).append(rec)
    return targets, instream


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def far_from_sources(lat, lon, targets, min_m=CONTROL_EXCLUDE_M):
    return all(haversine_m(lat, lon, t["lat"], t["lon"]) >= min_m
               for t in targets)


# ------------------------------------------------------------------ imagery

def region_geometry(ee, region_key):
    """The registered analysis region: the fetch_wqp bbox the chemistry was
    pulled from, so region-relative statistics (scene std-dev thresholds, the
    C3 NDVI percentile) are computed over exactly the area the points came
    from."""
    from fetch_wqp import REGIONS as WQP_REGIONS
    lat_lo, lon_lo, lat_hi, lon_hi = WQP_REGIONS[region_key][:4]
    return ee.Geometry.Rectangle([lon_lo, lat_lo, lon_hi, lat_hi])


def l8_composite(ee, region):
    from gee_classify import composite_for_region
    col, size = composite_for_region(ee, region)
    return col.median().clip(region), int(size.getInfo())


def s2_composite(ee, region):
    """Sentinel-2 SR mapped onto the SR_B1..SR_B7 naming the rest of the
    toolchain uses (match_scenes.S2_MAP), so add_indices() and classify_v3()
    work unchanged. B8A not B8 for SR_B5, matching Landsat 8 B5's 865 nm -
    the same choice match_scenes.py already made and validated.

    B8 (842 nm, 10 m) is carried separately as SR_B8_10 purely for the
    resolution ladder's genuine-10 m green:NIR; it is NOT substituted into the
    SIM 3466 indices, which would silently change their definition.
    """
    from gee_classify import add_indices, START, END, V3_MONTHS
    from match_scenes import S2_MAP

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


def index_image(ee, comp):
    """Add the paper2 indices and drop water pixels.

    Water exclusion is the whole point of the B1/B2 split: Green:NIR is
    degenerate on open water (all water absorbs NIR), so applied to a lake it
    detects water, not sulfur. Uses the classifier's OWN water term
    (gee_classify.water_term) rather than a second definition, and deliberately
    NOT the full `land` mask, which would also drop bright/dark/built/vegetated
    pixels and remove legitimate precipitate targets.
    """
    from gee_classify import water_term
    from water_indices import green_nir_ee, ndvi_stress_ee

    img = green_nir_ee(comp, "SR_B3", "SR_B5")
    img = img.addBands(ndvi_stress_ee(img, "SR_B5", "SR_B4"))
    return img.updateMask(water_term(ee, comp).Not())


NLCD_BARREN = 31          # NLCD "Barren Land (Rock/Sand/Clay)"


def sample_c3b(ee, region, targets, rng, n_candidates=3000):
    """C3b - bare ground defined by NLCD, INDEPENDENT of our imagery.

    AMENDMENT to the pre-registration, added 2026-08-15 and labelled as one.
    The registered C3 tier drew bare ground as "land pixels below the region's
    25th-percentile NDVI", which makes any NDVI-based index separate targets
    from C3 by construction - the W1 circularity, rebuilt by accident. NDVI_stress
    duly scored AUC 0.898 against it, which measures the control definition,
    not the imagery.

    NLCD class 31 owes nothing to the Landsat/Sentinel composite being tested,
    so it breaks the circularity. C3 is kept and reported alongside rather than
    replaced, so the defect stays visible in the record.
    """
    nlcd = (ee.ImageCollection("USGS/NLCD_RELEASES/2019_REL/NLCD")
            .filter(ee.Filter.eq("system:index", "2019")).first()
            .select("landcover"))
    pts = ee.FeatureCollection.randomPoints(region, n_candidates, SEED + 1)
    got = _retry_mem(
        lambda: nlcd.reduceRegions(collection=pts, reducer=ee.Reducer.first(),
                                   scale=30).getInfo()["features"],
        lambda: None)
    out = []
    for f in got:
        p, g = f["properties"], f["geometry"]["coordinates"]
        if p.get("first") != NLCD_BARREN:
            continue
        lon, lat = float(g[0]), float(g[1])
        if not far_from_sources(lat, lon, targets):
            continue
        out.append(dict(pid="C3b_%d" % len(out), lat=lat, lon=lon,
                        region=targets[0]["region"]))
        if len(out) >= CONTROLS_PER_TARGET * len(targets):
            break
    return out


def _retry_mem(fn, shrink, tries=4):
    """Run fn(), and on an EE memory error call shrink() and try again.

    Added 2026-08-15: the batch-shrinking inside extract_buffers covered only
    the buffer reductions, but Sentinel-2 (finer scale, more scenes, so a much
    larger compute graph) also blew the limit in sample_controls' random-point
    reduction and in classify_v3's tiled stats, which had no guard. That killed
    the Silverton and Ouray S2 runs outright while Leadville and Central City
    survived - the same job succeeding or failing on region size alone.
    """
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:                            # noqa: BLE001
            if "memory" not in str(exc).lower() or i == tries - 1:
                raise
            shrink()
            print("      memory limit - shrinking and retrying")


def amd_binary(ee, comp, region, scale, n_tiles=4):
    """1 where the SHIPPED v3.0.x classifier calls the pixel an AMD class.

    This is the highest-value single index in the panel: it scores the actual
    deliverable, unchanged and with its own scene-relative thresholds, against
    chemically-confirmed AMD point sources.
    """
    from gee_classify import classify_v3
    cls = classify_v3(ee, comp, region, scale=scale, n_tiles=n_tiles)
    amd = cls.remap(list(AMD_CLASSES), [1] * len(AMD_CLASSES), 0)
    return amd.updateMask(comp.select("SR_B4").mask()).rename("AMDclassFrac")


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def extract_buffers(ee, img, points, radius_m, scale, bands, batch=25):
    """p90 + mean + valid-pixel count per buffer, one reduceRegions per batch.

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
                if "memory" not in str(exc).lower() or size <= 2:
                    raise
                size = max(2, size // 2)
                print("      memory limit - retrying at batch=%d" % size)
    return out


# ------------------------------------------------------------------ controls

def sample_controls(ee, region, comp, targets, rng, n_candidates=1500):
    """C2 (terrain-matched) and C3 (bare ground), both drawn before any index
    is looked at, both excluded within 500 m of ANY source point.

    Candidates are screened at 90 m because elevation/slope/NDVI matching only
    needs to be approximate; the indices themselves are extracted at native
    scale for the selected points only.
    """
    srtm = ee.Image("USGS/SRTMGL1_003")
    terrain = srtm.rename("elev").addBands(
        ee.Terrain.slope(srtm).rename("slope")).addBands(
        comp.select("NDVI"))

    state = {"n": n_candidates}

    def _cand():
        pts = ee.FeatureCollection.randomPoints(region, state["n"], SEED)
        return terrain.reduceRegions(collection=pts, reducer=ee.Reducer.first(),
                                     scale=90).getInfo()["features"]

    got = _retry_mem(_cand, lambda: state.__setitem__("n", max(200, state["n"] // 2)))

    cand = []
    for f in got:
        p, g = f["properties"], f["geometry"]["coordinates"]
        if p.get("elev") is None or p.get("slope") is None:
            continue
        lon, lat = float(g[0]), float(g[1])
        if not far_from_sources(lat, lon, targets):
            continue
        cand.append(dict(lat=lat, lon=lon, elev=float(p["elev"]),
                         slope=float(p["slope"]),
                         ndvi=None if p.get("NDVI") is None else float(p["NDVI"])))

    # target terrain, same source and scale so the match is like-for-like
    tfc = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point([t["lon"], t["lat"]]), {"pid": t["pid"]})
        for t in targets])
    tgot = _retry_mem(
        lambda: terrain.reduceRegions(collection=tfc, reducer=ee.Reducer.first(),
                                      scale=90).getInfo()["features"],
        lambda: None)
    tterr = {f["properties"]["pid"]: f["properties"] for f in tgot}

    ndvis = sorted(c["ndvi"] for c in cand if c["ndvi"] is not None)
    ndvi_cut = (ndvis[max(0, int(len(ndvis) * NDVI_BARE_PCTL / 100.0) - 1)]
                if ndvis else None)

    used, c2, c3 = set(), [], []
    for t in targets:
        te = tterr.get(t["pid"], {})
        if te.get("elev") is None:
            continue
        pool = [i for i, c in enumerate(cand)
                if i not in used
                and abs(c["elev"] - float(te["elev"])) <= ELEV_TOL_M
                and abs(c["slope"] - float(te.get("slope") or 0)) <= SLOPE_TOL_DEG]
        rng.shuffle(pool)
        for i in pool[:CONTROLS_PER_TARGET]:
            used.add(i)
            c2.append(dict(pid="C2_%s_%d" % (t["pid"], i), lat=cand[i]["lat"],
                           lon=cand[i]["lon"], region=t["region"]))

    if ndvi_cut is not None:
        bare = [i for i, c in enumerate(cand)
                if i not in used and c["ndvi"] is not None and c["ndvi"] <= ndvi_cut]
        rng.shuffle(bare)
        for i in bare[:CONTROLS_PER_TARGET * len(targets)]:
            used.add(i)
            c3.append(dict(pid="C3_%d" % i, lat=cand[i]["lat"],
                           lon=cand[i]["lon"], region=targets[0]["region"]))
    return c2, c3, ndvi_cut


# ------------------------------------------------------------------ extract

def run_extract(sensor, slugs, out_csv, tiers=None, radii=None):
    from gee_classify import init_ee
    ee = init_ee()
    rng = random.Random(SEED)
    scale = 30 if sensor == "L8" else 20   # S2: SWIR-limited, see S2_NATIVE_M

    rows = []
    for slug in slugs:
        key = REGIONS.get(slug) or THIN_REGIONS[slug]
        print("\n=== %s (%s) ===" % (slug, sensor))
        region = region_geometry(ee, key)
        targets, instream = load_region_points(slug)
        print("  %d source targets, %d in-stream (C1)" % (len(targets), len(instream)))
        if not targets:
            continue

        comp, n_scenes = (l8_composite(ee, region) if sensor == "L8"
                          else s2_composite(ee, region))
        print("  %d scenes in May-Jul composite" % n_scenes)
        if n_scenes < MIN_SCENES:
            print("  SKIP - fewer than %d scenes" % MIN_SCENES)
            continue

        n_tiles = 4 if sensor == "L8" else 8
        c2, c3, ndvi_cut = sample_controls(
            ee, region, comp, targets, rng,
            n_candidates=1500 if sensor == "L8" else 600)
        print("  controls: C1=%d  C2=%d  C3=%d  (C3 NDVI cut %.3f)"
              % (len(instream), len(c2), len(c3),
                 ndvi_cut if ndvi_cut is not None else float("nan")))

        img = index_image(ee, comp)
        amd = amd_binary(ee, comp, region, scale, n_tiles=n_tiles)

        groups = [("target", targets), ("C1", instream), ("C2", c2), ("C3", c3)]
        if tiers is None or "C3b" in tiers:
            c3b = sample_c3b(ee, region, targets, rng)
            print("  C3b (NLCD barren, amendment): %d pts" % len(c3b))
            groups.append(("C3b", c3b))
        if tiers is not None:
            groups = [(t, p) for t, p in groups if t in tiers]
        for radius in (radii or RADII):
            for tier, pts in groups:
                if not pts:
                    continue
                vals = extract_buffers(ee, img, pts, radius, scale, INDEX_BANDS)
                afrac = extract_buffers(ee, amd, pts, radius, scale,
                                        ["AMDclassFrac"])
                for p in pts:
                    v = vals.get(p["pid"], {})
                    a = afrac.get(p["pid"], {})
                    row = dict(region=slug, sensor=sensor, radius=radius,
                               tier=tier, pid=p["pid"], lat=p["lat"],
                               lon=p["lon"], n_scenes=n_scenes,
                               n_px=v.get("IronSulfate_count"))
                    for b in INDEX_BANDS:
                        row[b + "_p90"] = v.get(b + "_p90")
                        row[b + "_mean"] = v.get(b + "_mean")
                    # AMD class fraction is a MEAN of a 0/1 image by definition
                    # (fraction of buffer classified AMD); the p90 of a binary
                    # image is just 0 or 1, so the mean is used for both the
                    # primary and sensitivity statistic and that is stated.
                    row["AMDclassFrac_p90"] = a.get("AMDclassFrac_mean")
                    row["AMDclassFrac_mean"] = a.get("AMDclassFrac_mean")
                    for cv in ("Iron_mgL_dissolved", "Iron_mgL_any",
                               "Sulfate_mgL", "pH"):
                        row[cv] = p.get(cv)
                    rows.append(row)
                print("    r=%3dm %-7s %d pts" % (radius, tier, len(pts)))

    if not rows:
        print("no rows extracted")
        return
    os.makedirs(OUTDIR, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s (%d rows)" % (out_csv, len(rows)))


# ------------------------------------------------------------------ stats

def auc(pos, neg):
    """Mann-Whitney U / (n1*n2), ties at 0.5."""
    if not pos or not neg:
        return float("nan")
    allv = sorted(pos + neg)
    n = len(allv)
    ranks, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2.0 + 1
        ranks[allv[i]] = r
        i = j + 1
    rp = sum(ranks[v] for v in pos)
    u = rp - len(pos) * (len(pos) + 1) / 2.0
    return u / (len(pos) * len(neg))


def best_threshold(pos, neg):
    """Threshold maximising Youden J (TPR - FPR) on the given sample."""
    if not pos or not neg:
        return float("nan"), float("nan")
    cuts = sorted(set(pos + neg))
    bj, bt = -2.0, float("nan")
    for c in cuts:
        tpr = sum(1 for v in pos if v >= c) / len(pos)
        fpr = sum(1 for v in neg if v >= c) / len(neg)
        if tpr - fpr > bj:
            bj, bt = tpr - fpr, c
    return bt, bj


def j_at(pos, neg, cut):
    if not pos or not neg or cut != cut:
        return float("nan")
    tpr = sum(1 for v in pos if v >= cut) / len(pos)
    fpr = sum(1 for v in neg if v >= cut) / len(neg)
    return tpr - fpr


def _prep_folds(scores, regions):
    """Precompute each LORO fold's score-descending index order ONCE.

    Scores never change under label permutation - only labels do - so the sort
    is loop-invariant. Hoisting it turns the O(n^2)-per-draw threshold search
    into a single O(n) sweep, which is what makes 10,000 permutations x 27
    tests finish in minutes instead of hours.
    """
    regs = sorted(set(regions))
    folds = {}
    for held in regs:
        tr = [i for i, r in enumerate(regions) if r != held]
        te = [i for i, r in enumerate(regions) if r == held]
        tr.sort(key=lambda i: -scores[i])
        te.sort(key=lambda i: -scores[i])
        folds[held] = (tr, te)
    return regs, folds


def _worst_j_fast(scores, labels, regs, folds):
    """Worst-case LORO Youden J via one descending sweep per fold."""
    worst, per = None, {}
    for held in regs:
        tr, te = folds[held]
        p_tr = sum(labels[i] for i in tr)
        n_tr = len(tr) - p_tr
        p_te = sum(labels[i] for i in te)
        n_te = len(te) - p_te
        if not (p_tr and n_tr and p_te and n_te):
            continue
        tp = fp = 0
        best_j, cut = -2.0, None
        for i in tr:                       # fit threshold on the OTHER regions
            if labels[i]:
                tp += 1
            else:
                fp += 1
            j = tp / p_tr - fp / n_tr
            if j > best_j:
                best_j, cut = j, scores[i]
        tp = fp = 0
        for i in te:                       # apply it to the held-out region
            if scores[i] >= cut:
                if labels[i]:
                    tp += 1
                else:
                    fp += 1
        jt = tp / p_te - fp / n_te
        per[held] = jt
        worst = jt if worst is None else min(worst, jt)
    return (worst if worst is not None else float("nan")), per


def loro_worst_j(scores, labels, regions):
    """Worst-case leave-one-REGION-out Youden J.

    THE criterion, per the pre-registration. Fit the threshold on every region
    except one, apply it to the held-out region, keep the worst fold. Pooled
    or within-region J is reported alongside but is NOT the criterion - Test C
    scored 0.99 within-site and 0.63 across sites, which is exactly the failure
    mode this guards against.
    """
    if len(set(regions)) < 2:
        return float("nan"), {}
    regs, folds = _prep_folds(scores, regions)
    return _worst_j_fast(scores, labels, regs, folds)


def perm_p_within_region(scores, labels, regions, observed, n_perm, rng):
    """One-sided p from shuffling labels WITHIN region only.

    Never across regions: source points cluster spatially and regions differ in
    geology, illumination and scene availability, so a global shuffle destroys
    the blocking and inflates significance.
    """
    if observed != observed:
        return float("nan")
    by = {}
    for i, r in enumerate(regions):
        by.setdefault(r, []).append(i)
    regs, folds = _prep_folds(scores, regions)
    lab = list(labels)
    perm = list(lab)
    hits = 0
    for _ in range(n_perm):
        for idx in by.values():
            sub = [lab[i] for i in idx]
            rng.shuffle(sub)
            for i, v in zip(idx, sub):
                perm[i] = v
        j, _ = _worst_j_fast(scores, perm, regs, folds)
        if j == j and j >= observed:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def benjamini_hochberg(pvals):
    """Return the BH-adjusted p-values, order preserved."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [1.0] * m
    prev = 1.0
    for rank, i in enumerate(reversed(idx), 1):
        k = m - rank + 1
        prev = min(prev, pvals[i] * m / k)
        adj[i] = prev
    return adj


def variance_split(values, regions):
    """Fraction of total variance that is BETWEEN regions.

    Mandatory next to any pooled correlation here: the pooled sulfate result
    reversed sign once 67.5%-between-region structure was removed.
    """
    vals = [(v, r) for v, r in zip(values, regions) if v == v]
    if len(vals) < 3:
        return float("nan")
    grand = statistics.mean(v for v, _ in vals)
    by = {}
    for v, r in vals:
        by.setdefault(r, []).append(v)
    ss_b = sum(len(g) * (statistics.mean(g) - grand) ** 2 for g in by.values())
    ss_t = sum((v - grand) ** 2 for v, _ in vals)
    return ss_b / ss_t if ss_t else float("nan")


def spearman(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a == a and b == b]
    if len(pairs) < 4:
        return float("nan"), len(pairs)
    def rank(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and a[order[j + 1]] == a[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    n = len(pairs)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return (num / den if den else float("nan")), n


# ------------------------------------------------------------------ analyse

def load_extracted(paths):
    """Load extracted CSVs, DEDUPED on (sensor, radius, tier, pid).

    The C3b amendment was extracted in a separate pass that also re-extracted
    the targets (a control tier is meaningless without something to compare it
    to), so target rows appear in two files. Without deduping they would be
    counted twice, inflating n+ and every statistic built on it.
    """
    rows = []
    seen = set()
    for p in paths:
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                key = (r.get("sensor"), r.get("radius"), r.get("tier"),
                       r.get("region"), r.get("pid"))
                if key in seen:
                    continue
                seen.add(key)
                for k, v in list(r.items()):
                    if k in ("region", "sensor", "tier", "pid", "name", "site_type"):
                        continue
                    r[k] = float(v) if v not in ("", None, "None") else float("nan")
                rows.append(r)
    return rows


def _score_key(index, stat):
    return "%s_%s" % (index, stat)


def run_analyse(paths, radius=PRIMARY_RADIUS, stat=PRIMARY_STAT,
                n_perm=N_PERM, out_txt=None):
    """The pre-registered test. Nothing here is chosen after the fact."""
    rows = load_extracted(paths)
    if not rows:
        print("no extracted rows found - run --extract first")
        return
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    sensors = sorted({r["sensor"] for r in rows})
    sel = [r for r in rows if r["radius"] == radius and r["region"] in REGIONS]

    say("=" * 92)
    say("ARM B2 - seep/precipitate detection, PRE-REGISTERED test")
    say("radius=%dm  statistic=%s  perms=%d  seed=%d" % (radius, stat, n_perm, SEED))
    say("Criterion: worst-case leave-one-REGION-out Youden J (NOT pooled AUC).")
    say("Decision rule: J >= %.2f vs ALL THREE tiers AND BH p < 0.05." % J_THRESHOLD)
    say("=" * 92)

    n_t = len({r["pid"] for r in sel if r["tier"] == "target"})
    say("targets n=%d across %d regions; controls C1=%d C2=%d C3=%d"
        % (n_t, len({r["region"] for r in sel if r["tier"] == "target"}),
           len({r["pid"] for r in sel if r["tier"] == "C1"}),
           len({r["pid"] for r in sel if r["tier"] == "C2"}),
           len({r["pid"] for r in sel if r["tier"] == "C3"})))
    n_c3b = len({r["pid"] for r in sel if r["tier"] == "C3b"})
    if n_c3b:
        say("C3b (NLCD barren, AMENDMENT - fixes C3's NDVI circularity): %d" % n_c3b)

    drops = [r for r in sel if r["tier"] == "target"
             and (r.get("n_px") != r.get("n_px") or (r.get("n_px") or 0) < 1)]
    say("targets with ZERO surviving land pixels after water mask: %d/%d (%.0f%%)"
        % (len(drops), n_t, 100.0 * len(drops) / max(1, n_t)))
    if len(drops) > 0.30 * max(1, n_t):
        say("*** >30%% drop rate - pre-registered escalation to r=100m applies ***")
    say()

    results = []
    for sensor in sensors:
        for index in ALL_INDICES:
            key = _score_key(index, stat)
            for tier in ("C1", "C2", "C3", "C3b"):
                pos, neg, sc, lb, rg = [], [], [], [], []
                for r in sel:
                    if r["sensor"] != sensor:
                        continue
                    v = r.get(key, float("nan"))
                    if v != v:
                        continue
                    if r["tier"] == "target":
                        pos.append(v); sc.append(v); lb.append(1); rg.append(r["region"])
                    elif r["tier"] == tier:
                        neg.append(v); sc.append(v); lb.append(0); rg.append(r["region"])
                if len(pos) < 10 or len(neg) < 10:
                    continue
                a = auc(pos, neg)
                wj, per = loro_worst_j(sc, lb, rg)
                p = perm_p_within_region(sc, lb, rg, wj, n_perm, rng)
                results.append(dict(sensor=sensor, index=index, tier=tier,
                                    auc=a, worst_j=wj, p=p, per=per,
                                    n_pos=len(pos), n_neg=len(neg)))

    if not results:
        say("no testable index/tier combinations")
        return

    adj = benjamini_hochberg([r["p"] if r["p"] == r["p"] else 1.0 for r in results])
    for r, q in zip(results, adj):
        r["q"] = q

    say("BH family = %d tests (%d indices x 3 tiers x %d sensors, "
        "minus untestable)" % (len(results), len(ALL_INDICES), len(sensors)))
    say("Bonferroni threshold = %.5f" % (0.05 / len(results)))
    say()
    say("  %-7s %-15s %-4s %7s %7s %8s %8s %6s %6s"
        % ("sensor", "index", "tier", "AUC", "worstJ", "perm_p", "BH_q",
           "n+", "n-"))
    for r in sorted(results, key=lambda d: -(d["worst_j"] if d["worst_j"] == d["worst_j"] else -9)):
        say("  %-7s %-15s %-4s %7.3f %7.3f %8.4f %8.4f %6d %6d"
            % (r["sensor"], r["index"], r["tier"], r["auc"], r["worst_j"],
               r["p"], r["q"], r["n_pos"], r["n_neg"]))
    say()

    say("-" * 92)
    say("DECISION RULE APPLIED (pre-registered)")
    say("-" * 92)
    any_pass = False
    for sensor in sensors:
        for index in ALL_INDICES:
            got = {r["tier"]: r for r in results
                   if r["sensor"] == sensor and r["index"] == index}
            # Decision rule stays on the three PRE-REGISTERED tiers. C3b is an
            # amendment and is reported, never used to change a pass/fail.
            if not all(t in got for t in ("C1", "C2", "C3")):
                continue
            ok = all(got[t]["worst_j"] >= J_THRESHOLD and got[t]["q"] < 0.05
                     for t in ("C1", "C2", "C3"))
            weak = [t for t in ("C1", "C2", "C3")
                    if not (got[t]["worst_j"] >= J_THRESHOLD and got[t]["q"] < 0.05)]
            if ok:
                any_pass = True
                say("  PASS  %-7s %-15s  detection claimed" % (sensor, index))
            elif weak == ["C3"]:
                say("  BARE  %-7s %-15s  separates C1+C2 but NOT C3 -> "
                    "bare-ground detector, NOT an AMD detector" % (sensor, index))
            else:
                say("  null  %-7s %-15s  fails: %s"
                    % (sensor, index, ",".join(weak)))
    if not any_pass:
        say()
        say("  NO INDEX MEETS THE PRE-REGISTERED CRITERION -> Arm B2 is a NULL.")
        say("  Reported as prominently as a positive would be, per project rule.")
    say()

    say("-" * 92)
    say("DOSE-RESPONSE at source points (secondary)")
    say("between-region variance share reported per the sulfate sign-reversal rule")
    say("-" * 92)
    for sensor in sensors:
        for index in ALL_INDICES:
            key = _score_key(index, stat)
            for cv in ("Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH"):
                xs, ys, rg = [], [], []
                for r in sel:
                    if r["sensor"] != sensor or r["tier"] != "target":
                        continue
                    a_, b_ = r.get(key, float("nan")), r.get(cv, float("nan"))
                    if a_ == a_ and b_ == b_:
                        xs.append(a_); ys.append(b_); rg.append(r["region"])
                if len(xs) < 10:
                    continue
                rho, n = spearman(xs, ys)
                if rho != rho:
                    continue
                say("  %-7s %-15s %-20s rho=%+.3f n=%-3d between-region var=%.0f%%"
                    % (sensor, index, cv, rho, n, 100 * variance_split(ys, rg)))
    say()
    say("CAVEAT: this tests LAND-SURFACE ferric precipitate, never dissolved")
    say("iron or sulfate. Sulfate has no VNIR absorption.")

    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


def run_dose_loro(paths, radius=PRIMARY_RADIUS, stat=PRIMARY_STAT, out_txt=None):
    """Leave-one-REGION-out test of the dose-response relationship.

    The pooled rho (+0.568 for FerricIron1 vs dissolved Fe) already survives
    within-region permutation, which is far stronger than the retracted sulfate
    result ever was. But this project's own standard is a HELD-OUT test:
    Arm A's n=6 headline also looked significant pooled and died leave-one-
    region-out. So the same knife is applied here.

    Two things are reported per pair:
      - per-region rho, i.e. does the sign even replicate in each district;
      - LORO R2: fit y~x on three regions, predict the fourth, pooled against
        the held-out region's own mean. Negative means worse than predicting
        the mean - the standard that killed Arm A.
    """
    rows = load_extracted(paths)
    sel = [r for r in rows if r["radius"] == radius and r["tier"] == "target"
           and r["region"] in REGIONS]
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 92)
    say("ARM B2 DOSE-RESPONSE - LEAVE-ONE-REGION-OUT (the Arm A knife)")
    say("radius=%dm statistic=%s" % (radius, stat))
    say("=" * 92)
    say("  %-15s %-20s %7s %8s %s" % ("index", "analyte", "pooled", "LORO_R2",
                                      "per-region rho"))

    for index in ALL_INDICES:
        key = _score_key(index, stat)
        for cv in ("Iron_mgL_dissolved", "Iron_mgL_any", "pH"):
            pts = [(r[key], r[cv], r["region"]) for r in sel
                   if r.get(key, float("nan")) == r.get(key, float("nan"))
                   and r.get(cv, float("nan")) == r.get(cv, float("nan"))]
            if len(pts) < 20:
                continue
            regs = sorted({p[2] for p in pts})
            if len(regs) < 3:
                continue
            pooled, _ = spearman([p[0] for p in pts], [p[1] for p in pts])
            if pooled != pooled:
                continue

            per = {}
            for g in regs:
                sub = [p for p in pts if p[2] == g]
                if len(sub) >= 5:
                    per[g] = spearman([s[0] for s in sub], [s[1] for s in sub])[0]

            ss_res = ss_tot = 0.0
            for held in regs:
                tr = [p for p in pts if p[2] != held]
                te = [p for p in pts if p[2] == held]
                if len(tr) < 10 or len(te) < 3:
                    continue
                mx = statistics.mean(p[0] for p in tr)
                my = statistics.mean(p[1] for p in tr)
                den = sum((p[0] - mx) ** 2 for p in tr)
                if den <= 0:
                    continue
                b = sum((p[0] - mx) * (p[1] - my) for p in tr) / den
                a = my - b * mx
                mte = statistics.mean(p[1] for p in te)
                ss_res += sum((p[1] - (a + b * p[0])) ** 2 for p in te)
                ss_tot += sum((p[1] - mte) ** 2 for p in te)
            r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")

            sgn = ("ALL +" if all(v > 0 for v in per.values())
                   else "ALL -" if all(v < 0 for v in per.values())
                   else "*** SIGNS DISAGREE ***")
            say("  %-15s %-20s %+7.3f %8.3f  %s  [%s]"
                % (index, cv, pooled, r2,
                   " ".join("%s=%+.2f" % (g[:4], v) for g, v in sorted(per.items())),
                   sgn))
    say()
    say("Sign consistency across all four districts is the headline check:")
    say("Arm A failed exactly here (Silverton +0.71, Ouray +0.67, but Creede")
    say("-0.80, Leadville -0.80), which is why it was retracted.")
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


V4_GRID = [(k, c) for k in (0.5, 1.0, 1.5, 2.0) for c in (0.25, 0.5)]


def run_v4_sweep(slugs, out_csv):
    """Phase B2b sweep: AMDclassFrac_v4 over the pre-registered 8-point grid.

    Extracts ONLY targets and C3b, because C3b is the pre-registered PRIMARY
    outcome (bare ground is the confound under repair). Selection happens on
    that tier alone; the winning parameter set is then re-extracted against all
    four tiers for reporting. Sweeping every tier would multiply cost by four
    for numbers that cannot influence the selection.
    """
    from gee_classify import (init_ee, STAT_BANDS, bare_subset_stats,
                              classify_v4_from_stats)
    ee = init_ee()
    rng = random.Random(SEED)
    rows = []

    for slug in slugs:
        region = region_geometry(ee, REGIONS[slug])
        targets, _ = load_region_points(slug)
        comp, n_scenes = l8_composite(ee, region)
        if n_scenes < MIN_SCENES:
            continue
        c3b = sample_c3b(ee, region, targets, rng)
        # Computed once per region and reused across all 8 grid points.
        stats = bare_subset_stats(ee, comp, region, STAT_BANDS, n_tiles=4)
        print("\n%s: %d scenes, %d targets, %d C3b"
              % (slug, n_scenes, len(targets), len(c3b)))

        for k_bare, clay_bare in V4_GRID:
            cls = classify_v4_from_stats(ee, comp, stats, k_bare, clay_bare)
            amd = (cls.remap(list(AMD_CLASSES), [1] * len(AMD_CLASSES), 0)
                   .updateMask(comp.select("SR_B4").mask())
                   .rename("AMDclassFrac_v4"))
            for tier, pts in (("target", targets), ("C3b", c3b)):
                got = extract_buffers(ee, amd, pts, PRIMARY_RADIUS, 30,
                                      ["AMDclassFrac_v4"])
                for p in pts:
                    v = got.get(p["pid"], {})
                    rows.append(dict(
                        region=slug, sensor="L8", radius=PRIMARY_RADIUS,
                        tier=tier, pid=p["pid"], k_bare=k_bare,
                        clay_bare=clay_bare,
                        AMDclassFrac_v4_p90=v.get("AMDclassFrac_v4_mean"),
                        AMDclassFrac_v4_mean=v.get("AMDclassFrac_v4_mean")))
            print("    k=%.1f clay=%.2f done" % (k_bare, clay_bare))

    os.makedirs(OUTDIR, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s (%d rows)" % (out_csv, len(rows)))


def analyse_v4_sweep(paths, n_perm=N_PERM, out_txt=None):
    """Score every grid point by worst-case LORO J vs C3b, BH-corrected.

    Reports the FULL grid, not the winner alone, so the selection is visible
    and a lucky cell cannot be presented as if it were the only thing tried.
    """
    rows = load_extracted(paths)
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 84)
    say("B2b SWEEP - AMDclassFrac_v4 vs C3b (NLCD barren), PRE-REGISTERED")
    say("Baseline: shipped v3 classifier scores worst-case LORO J = 0.000")
    say("Rule: >=0.25 SUCCESS | 0.15-0.25 PARTIAL | <0.15 FAILURE")
    say("=" * 84)
    say("  %6s %6s %8s %8s %9s %9s" % ("k_bare", "clay", "AUC", "worstJ",
                                       "perm_p", "BH_q"))

    res = []
    for k_bare, clay_bare in V4_GRID:
        sc, lb, rg = [], [], []
        for r in rows:
            if (r.get("k_bare") != k_bare or r.get("clay_bare") != clay_bare
                    or r["region"] not in REGIONS):
                continue
            v = r.get("AMDclassFrac_v4_p90", float("nan"))
            if v != v:
                continue
            sc.append(v)
            lb.append(1 if r["tier"] == "target" else 0)
            rg.append(r["region"])
        if sum(lb) < 10 or len(lb) - sum(lb) < 10:
            continue
        pos = [v for v, l in zip(sc, lb) if l]
        neg = [v for v, l in zip(sc, lb) if not l]
        wj, per = loro_worst_j(sc, lb, rg)
        p = perm_p_within_region(sc, lb, rg, wj, n_perm, rng)
        res.append(dict(k=k_bare, clay=clay_bare, auc=auc(pos, neg),
                        wj=wj, p=p, per=per))

    if not res:
        say("no usable grid points")
        return
    for r, q in zip(res, benjamini_hochberg([r["p"] for r in res])):
        r["q"] = q
    for r in res:
        say("  %6.1f %6.2f %8.3f %8.3f %9.4f %9.4f"
            % (r["k"], r["clay"], r["auc"], r["wj"], r["p"], r["q"]))

    best = max(res, key=lambda r: r["wj"])
    say()
    say("BEST by worst-case LORO J (the pre-registered criterion):")
    say("  k_bare=%.1f clay_bare=%.2f  J=%.3f  AUC=%.3f  BH_q=%.4f"
        % (best["k"], best["clay"], best["wj"], best["auc"], best["q"]))
    say("  per-region J: %s"
        % " ".join("%s=%+.2f" % (g[:4], v) for g, v in sorted(best["per"].items())))
    verdict = ("SUCCESS" if best["wj"] >= 0.25 and best["q"] < 0.05
               else "PARTIAL" if best["wj"] >= 0.15 else "FAILURE")
    say()
    say("VERDICT (pre-registered): %s   [v3 baseline was 0.000]" % verdict)
    if verdict == "FAILURE":
        say("Reported as a null, as prominently as a success would be.")
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


DEGRADE_SCALES = [10, 20, 30, 60, 100]
# Only indices whose Sentinel-2 bands are natively 10 m can honestly be tested
# at 10 m. FerricIron1 = red/blue, both 10 m - and it is also the index that
# carried the only surviving positive result, so the ladder lands exactly where
# it matters. The SWIR- and coastal-band indices are excluded rather than
# resampled up and reported as if they were 10 m.
DEGRADE_INDICES = ["FerricIron1", "GreenNIR", "GreenNIRNorm", "NDVI_stress"]


def run_degrade(slugs, out_txt=None, radius=PRIMARY_RADIUS,
                with_controls=False, scales=None, indices=None,
                max_controls=40):
    """Resolution-degradation ladder on the DOSE-RESPONSE, Sentinel-2.

    Applied to the dose-response rather than to detection because detection is
    already a null at both 30 m (Landsat) and 20 m (S2) - degrading a null
    yields a flat line of nulls and answers nothing. The dose-response is the
    result that survived, so the question worth asking is whether finer pixels
    strengthen it. That is precisely the drone-justification question, and it
    reproduces paper2's resolution argument on a quantity that actually exists
    here rather than on their leak-count.

    Targets only (86 points), so this is cheap: one reduceRegions per region
    per scale.
    """
    from gee_classify import init_ee
    ee = init_ee()
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 88)
    say("ARM B2 RESOLUTION LADDER - Sentinel-2, dose-response vs pixel size")
    say("buffer=%dm, targets only, indices natively 10m on S2" % radius)
    say("=" * 88)

    per_scale, det = {}, {}
    for slug in slugs:
        region = region_geometry(ee, REGIONS[slug])
        targets, _ = load_region_points(slug)
        comp, n_scenes = s2_composite(ee, region)
        if n_scenes < MIN_SCENES:
            continue
        img = index_image(ee, comp)
        # A median composite carries no default projection, so reduceResolution
        # refuses it. Anchor at 10 m in UTM 13N (EPSG:32613) - Colorado's zone,
        # metric and true-scale here. EPSG:3857 would be wrong: at latitude 38
        # its metres are inflated ~1.27x, so a nominal "10 m" would really be
        # ~7.9 m on the ground and every rung of the ladder would be mislabelled.
        idxs = indices or DEGRADE_INDICES
        base = img.select(idxs).setDefaultProjection(
            crs="EPSG:32613", scale=10)
        for sc in (scales or DEGRADE_SCALES):
            if sc <= 10:
                deg = base
            else:
                deg = (base.reduceResolution(ee.Reducer.mean(), maxPixels=1024)
                       .reproject(crs="EPSG:32613", scale=sc))
            if with_controls:
                _, instream = load_region_points(slug)
                # Subsample controls. The full ladder (5 scales x 4 regions x
                # ~570 buffers, each behind a reduceResolution) hit GEE's
                # per-computation TIME limit, not the memory limit - a
                # different failure that retrying cannot fix. 40 controls per
                # region still gives ~160 vs 86 targets, ample for an AUC.
                rng.shuffle(instream)
                instream = instream[:max_controls]
                cvals = extract_buffers(ee, deg, instream, radius, sc,
                                        idxs, batch=15)
                for c in instream:
                    v = cvals.get(c["pid"], {})
                    for idx in idxs:
                        det.setdefault((sc, idx), []).append(
                            (v.get(idx + "_p90"), 0, slug))
            vals = extract_buffers(ee, deg, targets, radius, sc,
                                   idxs, batch=15)
            if with_controls:
                for t in targets:
                    v = vals.get(t["pid"], {})
                    for idx in idxs:
                        det.setdefault((sc, idx), []).append(
                            (v.get(idx + "_p90"), 1, slug))
            for t in targets:
                v = vals.get(t["pid"], {})
                for idx in idxs:
                    per_scale.setdefault((sc, idx), []).append(
                        (v.get(idx + "_p90"), t.get("Iron_mgL_dissolved"),
                         t.get("pH"), slug))
            print("  %s scale=%3dm done" % (slug, sc))

    say("  %-14s %5s %8s %5s %8s %5s  %s"
        % ("index", "GSD", "rho_Fe", "n", "rho_pH", "n", "per-region sign (Fe)"))
    for idx in DEGRADE_INDICES:
        for sc in (scales or DEGRADE_SCALES):
            rows = per_scale.get((sc, idx), [])
            fe = [(a, b, r) for a, b, _, r in rows if a is not None and b is not None]
            ph = [(a, c) for a, _, c, _ in rows if a is not None and c is not None]
            if len(fe) < 10:
                continue
            rho_fe, n_fe = spearman([f[0] for f in fe], [f[1] for f in fe])
            rho_ph, n_ph = (spearman([p[0] for p in ph], [p[1] for p in ph])
                            if len(ph) >= 10 else (float("nan"), 0))
            signs = {}
            for g in sorted({f[2] for f in fe}):
                sub = [f for f in fe if f[2] == g]
                if len(sub) >= 5:
                    signs[g] = spearman([s[0] for s in sub], [s[1] for s in sub])[0]
            say("  %-14s %4dm %8.3f %5d %8.3f %5d  %s"
                % (idx, sc, rho_fe, n_fe, rho_ph, n_ph,
                   " ".join("%s%+.2f" % (g[:4], v) for g, v in signs.items())))
        say()
    if det:
        say()
        say("DETECTION vs GSD - within ONE sensor, so resolution is the ONLY")
        say("variable. This is the test the L8-vs-S2 comparison could not make,")
        say("because that one confounds sensor with pixel size.")
        say("  %-14s %5s %8s %8s  %s" % ("index", "GSD", "AUC", "worstJ", "n+/n-"))
        for idx in DEGRADE_INDICES:
            for sc in (scales or DEGRADE_SCALES):
                rows = [r for r in det.get((sc, idx), []) if r[0] is not None]
                if len(rows) < 40:
                    continue
                sc_v = [r[0] for r in rows]
                lb = [r[1] for r in rows]
                rg = [r[2] for r in rows]
                pos = [v for v, l in zip(sc_v, lb) if l]
                neg = [v for v, l in zip(sc_v, lb) if not l]
                wj, _ = loro_worst_j(sc_v, lb, rg)
                say("  %-14s %4dm %8.3f %8.3f  %d/%d"
                    % (idx, sc, auc(pos, neg), wj, len(pos), len(neg)))
            say()
    say("Read DOWN each index: if |rho| rises as GSD falls, finer pixels help")
    say("and the drone case is quantitative. If flat, resolution is not the")
    say("limiting factor and the ceiling is spectral, not spatial.")
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--dose-loro", action="store_true")
    ap.add_argument("--degrade", action="store_true")
    ap.add_argument("--v4-sweep", action="store_true")
    ap.add_argument("--v4-analyse", action="store_true")
    ap.add_argument("--detection-ladder", action="store_true")
    ap.add_argument("--scales", default="")
    ap.add_argument("--dindices", default="")
    ap.add_argument("--tiers", default="", help="limit extraction to these tiers")
    ap.add_argument("--radii", default="", help="limit extraction to these radii (m)")
    ap.add_argument("--sensor", default="L8", choices=["L8", "S2"])
    ap.add_argument("--regions", default="")
    ap.add_argument("--inputs", default="",
                    help="comma-separated extracted CSVs for --analyse")
    ap.add_argument("--radius", type=int, default=PRIMARY_RADIUS)
    ap.add_argument("--stat", default=PRIMARY_STAT, choices=["p90", "mean"])
    ap.add_argument("--perms", type=int, default=N_PERM)
    ap.add_argument("--out")
    a = ap.parse_args()
    slugs = ([s for s in a.regions.split(",") if s] or list(REGIONS))
    if a.extract:
        out = a.out or os.path.join(OUTDIR, "seep_%s.csv" % a.sensor.lower())
        run_extract(a.sensor, slugs, out,
                    [t for t in a.tiers.split(",") if t] or None,
                    [int(x) for x in a.radii.split(",") if x] or None)
    elif a.v4_sweep:
        run_v4_sweep(slugs, a.out or os.path.join(OUTDIR, "seep_v4_sweep.csv"))
    elif a.v4_analyse:
        analyse_v4_sweep([p for p in a.inputs.split(",") if p], a.perms, a.out)
    elif a.degrade:
        run_degrade(slugs, a.out, with_controls=a.detection_ladder,
                    scales=[int(x) for x in a.scales.split(",") if x] or None,
                    indices=[i for i in a.dindices.split(",") if i] or None)
    elif a.dose_loro:
        paths = [p for p in a.inputs.split(",") if p]
        run_dose_loro(paths, a.radius, a.stat, a.out)
    elif a.analyse:
        paths = ([p for p in a.inputs.split(",") if p]
                 or [os.path.join(OUTDIR, "seep_l8.csv"),
                     os.path.join(OUTDIR, "seep_s2.csv")])
        run_analyse(paths, a.radius, a.stat, a.perms, a.out)
    else:
        ap.print_help()
