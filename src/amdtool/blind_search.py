"""Blind-search test: does a score find known mine sources above a landscape budget?

Implements validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md. Every constant
below is quoted from that registration; changing one changes the test, so do not
change them. Sensitivity variants are explicit arguments, never new defaults.

The pure analysis (sites, cutoffs, flags, tests, Holm, verdicts, sampling frame)
needs no Earth Engine. `extract_district` is the only function that does, and it
takes an initialised `ee`.
"""

import csv
import io
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from amdtool import imagery, stats

# ---- fixed by the registration ---------------------------------------------
SCORE_BAND = "FerricIron1"          # score = FerricIron1 p90
BASELINE_BAND = "NDVI_stress"       # baseline = -(NDVI_stress mean)
RADIUS_M = 60
SCALE_M = 20
N_LANDSCAPE = 2000
LANDSCAPE_SEED = 20260914
MIN_VALID_LANDSCAPE = 1000          # below this: reported limitation, no re-draw
PRIMARY_BUDGET = 0.05
SECONDARY_BUDGETS = (0.01, 0.10)
FAMILY_ALPHA = 0.05
HYPOTHESES = ("H-BS1", "H-BS2")     # co-primary; T-86 is tertiary
TERTIARY = "T-86"
LINK_M = 250.0
FRAME_N = 40
FRAME_SEED = 20260915
FRAME_EXCLUDE_M = 500.0
POWER_RECALLS = (0.15, 0.20, 0.30)

VERDICT_DISCOVERY = "DISCOVERY SIGNAL"
VERDICT_BARE = "NOT BETTER THAN BARE GROUND"
VERDICT_NONE = "NO SIGNAL DETECTED"


def primary_score(row):
    return row.get(SCORE_BAND + "_p90", float("nan"))


def baseline_score(row):
    v = row.get(BASELINE_BAND + "_mean", float("nan"))
    return -v if v == v else float("nan")


# ---- geometry helpers --------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * 6371000.0 * math.asin(math.sqrt(h))


def single_linkage(points, link_m=LINK_M):
    """[{"lat","lon",...}] -> list of clusters (lists of points).

    Deterministic: sorted by (lat, lon, pid) first, clusters returned in order of
    their first member.
    """
    pts = sorted(points, key=lambda p: (p["lat"], p["lon"], str(p.get("pid", ""))))
    parent = list(range(len(pts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if haversine_m(pts[i]["lat"], pts[i]["lon"],
                           pts[j]["lat"], pts[j]["lon"]) <= link_m:
                parent[find(i)] = find(j)
    groups, order = {}, []
    for i in range(len(pts)):
        root = find(i)
        if root not in groups:
            groups[root] = []
            order.append(root)
        groups[root].append(pts[i])
    return [groups[r] for r in order]


# ---- sites -------------------------------------------------------------------

@dataclass
class Site:
    hypothesis: str
    district: str
    site_id: str
    has_mine: bool
    station_ids: List[str] = field(default_factory=list)
    station_types: List[str] = field(default_factory=list)


def load_sites(path):
    """Read the registered site list (validation/blind_search_sites_*.csv)."""
    sites = {}
    with io.open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = (r["hypothesis"], r["site_id"])
            if key not in sites:
                sites[key] = Site(r["hypothesis"], r["district"], r["site_id"],
                                  r["site_has_mine_station"] == "1")
            sites[key].station_ids.append(r["station_id"])
            sites[key].station_types.append(r["site_type"])
    return list(sites.values())


def site_score(site, station_rows, score_fn, how="max"):
    """Registered: the MAX of the site's valid station scores. NaN if none."""
    vals = [score_fn(station_rows[s]) for s in site.station_ids if s in station_rows]
    vals = [v for v in vals if v == v]
    if not vals:
        return float("nan")
    return max(vals) if how == "max" else statistics.median(vals)


# ---- cutoffs and flags -------------------------------------------------------

def landscape_cutoff(landscape_rows, score_fn, budget):
    """Registered: numpy.quantile (default linear) of valid scores at 1 - budget.

    Returns (cutoff, n_valid). No label enters the cutoff.
    """
    import numpy as np
    vals = [score_fn(r) for r in landscape_rows]
    vals = np.asarray([v for v in vals if v == v], dtype=float)
    if vals.size == 0:
        return float("nan"), 0
    return float(np.quantile(vals, 1.0 - budget)), int(vals.size)


def is_flagged(score, cut):
    return score == score and cut == cut and score >= cut


# ---- evaluation --------------------------------------------------------------

@dataclass
class HypothesisResult:
    hypothesis: str
    budget: float
    n: int
    k: int
    recall: float
    ci: tuple
    p_binomial: float
    k_baseline: int
    b: int                      # FerricIron1 only
    c: int                      # baseline only
    p_mcnemar: float
    unscoreable: int
    failed_districts: List[str]
    per_district: Dict[str, dict]
    holm_level: Optional[float] = None
    rejected: bool = False
    verdict: str = ""
    power_at_level: Dict[float, float] = field(default_factory=dict)


def evaluate(sites, district_rows, budget, hypothesis, *, site_set="primary",
             how="max", unscoreable="not_flagged"):
    """One hypothesis at one budget.

    district_rows: {district: {"landscape": [rows], "stations": {station_id: row}}}.
    A district absent from district_rows is FAILED: its sites are removed from
    the hypothesis and listed (registration section 11).

    site_set     "primary" (>= 1 mine-type station) or "all".
    how          "max" (registered) or "median" (sensitivity).
    unscoreable  "not_flagged" (registered) or "exclude" (sensitivity).
    """
    chosen = [s for s in sites if s.hypothesis == hypothesis
              and (site_set == "all" or s.has_mine)]
    failed = sorted({s.district for s in chosen if s.district not in district_rows})
    chosen = [s for s in chosen if s.district in district_rows]

    cuts = {}
    for d in {s.district for s in chosen}:
        land = district_rows[d]["landscape"]
        cuts[d] = (landscape_cutoff(land, primary_score, budget)[0],
                   landscape_cutoff(land, baseline_score, budget)[0])

    n = k = kb = b = c = n_unscoreable = 0
    per = {}
    for s in chosen:
        st = district_rows[s.district]["stations"]
        sc = site_score(s, st, primary_score, how)
        bs = site_score(s, st, baseline_score, how)
        if sc != sc:
            n_unscoreable += 1
            if unscoreable == "exclude":
                continue
        f_score = is_flagged(sc, cuts[s.district][0])
        f_base = is_flagged(bs, cuts[s.district][1])
        n += 1
        k += f_score
        kb += f_base
        b += f_score and not f_base
        c += f_base and not f_score
        d = per.setdefault(s.district, {"n": 0, "k": 0, "k_baseline": 0})
        d["n"] += 1
        d["k"] += f_score
        d["k_baseline"] += f_base
    for d in per.values():
        d["recall"] = d["k"] / d["n"] if d["n"] else float("nan")
        d["ci"] = stats.wilson_interval(d["k"], d["n"])

    return HypothesisResult(
        hypothesis=hypothesis, budget=budget, n=n, k=k,
        recall=k / n if n else float("nan"),
        ci=stats.wilson_interval(k, n),
        p_binomial=stats.binomial_test_greater(k, n, budget),
        k_baseline=kb, b=b, c=c, p_mcnemar=stats.mcnemar_exact_greater(b, c),
        unscoreable=n_unscoreable, failed_districts=failed, per_district=per)


def critical_k(n, budget, alpha):
    for k in range(n + 1):
        if stats.binomial_sf_ge(k, n, budget) <= alpha:
            return k
    return None


def power(n, budget, alpha, recall):
    k = critical_k(n, budget, alpha)
    return float("nan") if k is None else stats.binomial_sf_ge(k, n, recall)


def apply_verdicts(results, budget=PRIMARY_BUDGET, alpha=FAMILY_ALPHA):
    """Registration section 7: Holm over H-BS1/H-BS2, then McNemar at that level.

    results: {hypothesis: HypothesisResult} at the primary budget. Mutates and
    returns it. Ties in p are broken with H-BS1 first.
    """
    hyps = list(HYPOTHESES)
    ps = [results[h].p_binomial for h in hyps]
    ps_sortable = [p if p == p else 2.0 for p in ps]       # NaN never rejects
    order = sorted(range(len(hyps)), key=lambda i: (ps_sortable[i], i))
    first, second = hyps[order[0]], hyps[order[1]]

    lvl_first = alpha / 2
    rej_first = ps_sortable[order[0]] <= lvl_first
    results[first].holm_level = lvl_first
    results[first].rejected = rej_first

    results[second].holm_level = alpha if rej_first else None
    results[second].rejected = rej_first and ps_sortable[order[1]] <= alpha

    for h in hyps:
        r = results[h]
        if r.rejected:
            r.verdict = (VERDICT_DISCOVERY if r.p_mcnemar <= r.holm_level
                         else VERDICT_BARE)
        else:
            r.verdict = VERDICT_NONE
        level = r.holm_level if r.holm_level is not None else alpha / 2
        r.power_at_level = {rec: power(r.n, budget, level, rec)
                            for rec in POWER_RECALLS}
    return results


# ---- station-level recall (sensitivity) --------------------------------------

def station_recall(sites, district_rows, budget, hypothesis, site_set="primary"):
    k = n = 0
    for s in sites:
        if s.hypothesis != hypothesis or s.district not in district_rows:
            continue
        if site_set != "all" and not s.has_mine:
            continue
        cut = landscape_cutoff(district_rows[s.district]["landscape"],
                               primary_score, budget)[0]
        st = district_rows[s.district]["stations"]
        for sid in s.station_ids:
            if sid in st:
                n += 1
                k += is_flagged(primary_score(st[sid]), cut)
    return k, n


# ---- field sampling frame ----------------------------------------------------

def sampling_frame(district_rows, wqp_stations, budget=PRIMARY_BUDGET,
                   n_draw=FRAME_N, seed=FRAME_SEED):
    """Registration section 10. A sampling frame, NOT a list of detections.

    wqp_stations: {district: [{"lat","lon"}]} - every WQP station of any type.
    Returns (drawn clusters, cluster counts per district).
    """
    clusters_by_d = {}
    for d in sorted(district_rows):
        land = district_rows[d]["landscape"]
        cut = landscape_cutoff(land, primary_score, budget)[0]
        cand = [r for r in land if is_flagged(primary_score(r), cut)]
        near = wqp_stations.get(d, [])
        cand = [r for r in cand
                if not any(haversine_m(r["lat"], r["lon"], s["lat"], s["lon"])
                           <= FRAME_EXCLUDE_M for s in near)]
        clusters_by_d[d] = single_linkage(cand)

    total = sum(len(v) for v in clusters_by_d.values())
    if total == 0:
        return [], {d: 0 for d in clusters_by_d}
    want = min(n_draw, total)
    quotas = {d: want * len(v) / total for d, v in clusters_by_d.items()}
    alloc = {d: int(math.floor(q)) for d, q in quotas.items()}
    remainder = sorted(clusters_by_d, key=lambda d: (-(quotas[d] - alloc[d]), d))
    for d in remainder[:want - sum(alloc.values())]:
        alloc[d] += 1

    rng = random.Random(seed)
    drawn = []
    for d in sorted(clusters_by_d):
        pool = clusters_by_d[d]
        for i, cl in enumerate(rng.sample(pool, min(alloc[d], len(pool)))):
            drawn.append({
                "district": d, "frame_id": "%s_F%02d" % (d, i + 1),
                "n_points": len(cl),
                "lat": sum(p["lat"] for p in cl) / len(cl),
                "lon": sum(p["lon"] for p in cl) / len(cl),
                "max_score": max(primary_score(p) for p in cl),
            })
    return drawn, {d: len(v) for d, v in clusters_by_d.items()}


# ---- Earth Engine extraction -------------------------------------------------

def s2_composite_snow_masked(ee, region):
    """Sensitivity only: imagery.s2_composite with SCL class 11 (snow) masked too."""
    S2 = imagery.S2_MAP

    def prep(img):
        scl = img.select("SCL")
        clear = (scl.neq(1).And(scl.neq(3)).And(scl.neq(8))
                 .And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11)))
        b = img.updateMask(clear)
        scaled = (b.select([s for s, _ in S2]).divide(10000).clamp(0.0, 1.0)
                  .rename([d for _, d in S2]))
        nir10 = b.select("B8").divide(10000).clamp(0.0, 1.0).rename("SR_B8_10")
        return imagery.add_indices(ee, scaled.addBands(nir10))

    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(region).filterDate(imagery.START, imagery.END)
           .filter(ee.Filter.calendarRange(imagery.V3_MONTHS[0],
                                           imagery.V3_MONTHS[-1], "month"))
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", imagery.S2_MAX_CLOUD))
           .sort("CLOUDY_PIXEL_PERCENTAGE").limit(imagery.S2_MAX_SCENES)
           .map(prep))
    return col.median().clip(region), int(col.size().getInfo())


def extract_district(ee, bbox, stations, *, snow_masked=False,
                     n_landscape=N_LANDSCAPE, seed=LANDSCAPE_SEED):
    """Score the landscape sample and the registered stations for one district.

    stations: [{"pid","lat","lon"}]. Returns (n_scenes, landscape_points,
    landscape_values, station_values) where *_values are extract_buffers dicts.
    """
    region = bbox.to_ee(ee)
    comp, n_scenes = (s2_composite_snow_masked(ee, region) if snow_masked
                      else imagery.s2_composite(ee, region))
    img = imagery.index_image(ee, comp)
    bands = [SCORE_BAND, BASELINE_BAND]
    land = imagery.random_landscape_points(ee, region, n_landscape, seed)
    got_land = imagery.extract_buffers(ee, img, land, RADIUS_M, SCALE_M, bands)
    got_st = imagery.extract_buffers(ee, img, stations, RADIUS_M, SCALE_M, bands)
    return n_scenes, land, got_land, got_st


NLCD_BARREN = 31          # NLCD "Barren Land (Rock/Sand/Clay)"


def nlcd_landcover_at(ee, points, batch=500):
    """NLCD 2019 land-cover class at each point (sensitivity: barren share).

    Same asset, band, reducer and scale as B2's C3b tier
    (python/seep_detect.sample_c3b), so the two are directly comparable.
    Returns {pid: class or None}.
    """
    nlcd = (ee.ImageCollection("USGS/NLCD_RELEASES/2019_REL/NLCD")
            .filter(ee.Filter.eq("system:index", "2019")).first()
            .select("landcover"))
    out = {}
    for i in range(0, len(points), batch):
        sub = points[i:i + batch]
        fc = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([p["lon"], p["lat"]]), {"pid": p["pid"]})
            for p in sub])
        got = nlcd.reduceRegions(collection=fc, reducer=ee.Reducer.first(),
                                 scale=30).getInfo()["features"]
        for f in got:
            out[f["properties"]["pid"]] = f["properties"].get("first")
    return out
