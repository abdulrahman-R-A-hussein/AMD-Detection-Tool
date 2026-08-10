"""Arm A: does upstream mineral mapping predict downstream water chemistry?

The one analysis in this project with an outcome variable NEITHER map was
fitted to. Every number in validation/REPLICA_AUDIT_2026-07-26.md measured
agreement with Rockwell's published raster - useful for replica fidelity, but
it could never answer "is ours better". Measured water chemistry (WQP, real
field samples) is independent ground truth. Computing upstream mineral loading
from BOTH maps and regressing each against the SAME measured chemistry is a
real predictive contest with an external outcome.

SIM 3466 p.3 states the mineral map's own purpose is "developing predictive
models of downstream surface water geochemistry" and Table 4 assigns every
AMD class a NAP rank (net acid production, 1=high). Verified ranks (Table 4):
  14=1  12=2  17=3  18=4  9=5  19=6
Three competing loading models are scored, not just the NAP prior:
  M1  AMD area fraction (classes 9,12,14,17,18,19 / all valid pixels)
  M2  NAP-weighted: sum area * (7 - nap_rank), normalised by catchment area
  M3  per-class area fractions as separate covariates (data sets its own
      weights - watch for overfitting with few catchments; that is exactly
      what leave-one-catchment-out is there to catch)

Method:
  1. For each water-chemistry station with >=N Iron/Sulfate measurements,
     delineate its upstream catchment (catchment_delineation.delineate()).
  2. DEDUPE by catchment identity (station_basin_id) - stations that share a
     hybas_12 polygon get IDENTICAL upstream sets (see
     validation/WATER_PHASE2_ARM_A_2026-08-10.md finding: Howardsville /
     Silverton / Cement Creek gauges all share one polygon). Pooling their
     chemistry under one catchment row is what "count distinct catchments,
     not stations" (the plan's stated risk) requires.
  3. Classify the catchment with OUR v3.0.x classifier (gee_classify.classify_v3,
     scene-relative thresholds, May-Jul, tiled histogram so large polygons
     don't hit the EE getInfo ceiling).
  4. For Colorado ONLY: also zonal-stat Rockwell's published raster over the
     identical polygon (rasterio local read - Rockwell has no EE asset).
  5. Regress. Primary: Spearman rho (monotonic, doesn't need a fitted
     coefficient, robust with few catchments) between each loading model and
     each chemistry variable, for OUR map and ROCKWELL's map separately.
     Secondary: leave-one-catchment-out linear R² on the single predictor
     that scores best in-sample, reported OUT of sample (the LOSO discipline
     from finding L1 - a model judged only in-sample is not validated).

CAVEAT, same as everywhere else in this project: measured chemistry is real
ground truth, but n is catchments (likely a few dozen at most), and 30 m
Landsat mineral fraction is a coarse proxy for what actually drains a
catchment (mixed pixels, mine waste vs weathered rock, transport distance).
A null result bounds how much of the variance satellite mineralogy can
explain - report it as a finding, not a failure.

    .venv/Scripts/python python/watershed_nap.py --region colorado --min-samples 5
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"
ROCKWELL_RASTER = os.path.join(ROOT, "data", "rockwell", "L8_US_Southwest",
                               "SouthWest", "l8_aa13_southwest_mosaic11.img")

# Verified against SIM 3466 Table 4 (validation/REPLICA_AUDIT_2026-07-26.md).
NAP_RANK = {14: 1, 12: 2, 17: 3, 18: 4, 9: 5, 19: 6}
AMD_CLASSES = set(NAP_RANK)
# Rockwell's agricultural variants collapse onto their AMD parent classes
# (python/compare_rockwell.py COLLAPSE).
ROCKWELL_COLLAPSE = {16: 12, 20: 17, 21: 18}

CHEM_VARS = ["Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH",
            "SpecificConductance"]


def init_ee():
    import ee
    info = json.load(open(KEY))
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], KEY),
                  project=info["project_id"])
    return ee


# ---------------------------------------------------------------- chemistry

def load_station_chemistry(chem_dir, min_samples):
    """Return {station_id: {var: median, 'n_'+var: n, 'lat':, 'lon':, 'name':}}
    for stations with >= min_samples Iron_mgL OR Sulfate measurements.
    Excludes sediment (Iron_mgL blank for those rows - already split at fetch
    time) and mixes fraction types only where finding W4 says it is safe:
    Iron is kept split (dissolved vs any), Sulfate/pH/conductance are not
    fraction-sensitive in the same way and are pooled.
    """
    import csv
    cpath = os.path.join(chem_dir, "consolidated.csv")
    spath = os.path.join(chem_dir, "stations.csv")
    stations = {}
    with open(spath, encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            stations[s["station_id"]] = s

    vals = defaultdict(lambda: defaultdict(list))
    with open(cpath, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            sid = r.get("MonitoringLocationIdentifier")
            char = r.get("CharacteristicName")
            if char == "Iron" and r.get("Iron_mgL"):
                v = float(r["Iron_mgL"])
                vals[sid]["Iron_mgL_any"].append(v)
                if r.get("ResultSampleFractionText") == "Dissolved":
                    vals[sid]["Iron_mgL_dissolved"].append(v)
            elif char == "Sulfate":
                try:
                    vals[sid]["Sulfate_mgL"].append(float(r["ResultMeasureValue"]))
                except (TypeError, ValueError):
                    pass
            elif char == "pH":
                try:
                    vals[sid]["pH"].append(float(r["ResultMeasureValue"]))
                except (TypeError, ValueError):
                    pass
            elif char == "Specific conductance":
                try:
                    vals[sid]["SpecificConductance"].append(float(r["ResultMeasureValue"]))
                except (TypeError, ValueError):
                    pass

    import statistics
    out = {}
    for sid, d in vals.items():
        n_iron = len(d.get("Iron_mgL_any", []))
        n_so4 = len(d.get("Sulfate_mgL", []))
        if max(n_iron, n_so4) < min_samples:
            continue
        s = stations.get(sid)
        if not s or not s.get("lat") or not s.get("lon"):
            continue
        row = {"lat": float(s["lat"]), "lon": float(s["lon"]),
              "name": s.get("station_name", sid),
              "site_type": s.get("site_type", "")}
        for var in CHEM_VARS:
            v = d.get(var, [])
            row[var] = statistics.median(v) if v else None
            row["n_" + var] = len(v)
        out[sid] = row
    return out


# ---------------------------------------------------------------- our map

def classify_catchment_ours(ee, region, min_scenes=3, n_tiles=4):
    """Class histogram over `region` using the v3.0.x classifier. Returns
    (Counter class->px, n_scenes) or (None, n_scenes) if too few scenes.

    n_tiles=4 (16 cells) matches the tiling that worked for similarly-sized
    (100-250 km2) areas earlier in this project (diagnose_veg_gate.py at
    Silverton/Red Mountain Pass) - 2x2 was tried first here and hit "User
    memory limit exceeded" even on the smallest test catchment, because the
    EE compute-graph depth (many scenes x full index cascade x classify x
    reduceRegion) is what blows the limit, not just per-tile pixel count.
    """
    from gee_classify import classify_v3, composite_for_region
    from diagnose_veg_gate import tile_geoms

    col, n_scenes_img = composite_for_region(ee, region)
    n_scenes = n_scenes_img.getInfo()
    if n_scenes < min_scenes:
        return None, n_scenes

    comp = col.median().clip(region)
    valid = comp.select("SR_B4").mask()
    cls = classify_v3(ee, comp, region).updateMask(valid).rename("class")

    total = Counter()
    cells = tile_geoms(ee, region, n_tiles)
    for k, cell in enumerate(cells, 1):
        h = cls.reduceRegion(reducer=ee.Reducer.frequencyHistogram(),
                             geometry=cell, scale=30, bestEffort=True,
                             maxPixels=int(1e9)).getInfo()
        for key, v in (h.get("class") or {}).items():
            total[int(float(key))] += int(v)
        print("    tile %d/%d: running total %d px"
              % (k, len(cells), sum(total.values())))
    return total, n_scenes


# ---------------------------------------------------------------- rockwell

def classify_catchment_rockwell(catchment_geojson):
    """Class histogram over the catchment from Rockwell's LOCAL raster.
    Colorado only - Rockwell's product does not cover Ohio."""
    import numpy as np
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom

    with rasterio.open(ROCKWELL_RASTER) as src:
        geom = transform_geom("EPSG:4326", src.crs, catchment_geojson)
        try:
            arr, _ = mask(src, [geom], crop=True, filled=True, nodata=0)
        except ValueError:
            return None                          # catchment doesn't overlap raster
    vals, counts = np.unique(arr[arr > 0], return_counts=True)
    hist = Counter()
    for v, c in zip(vals.tolist(), counts.tolist()):
        v = ROCKWELL_COLLAPSE.get(int(v), int(v))
        if v == 15:
            continue                             # their no-data (smoke/cloud)
        hist[v] += c
    return hist


# ---------------------------------------------------------------- loading

def loading_metrics(hist):
    """From a class histogram, compute M1 (AMD area%), M2 (NAP-weighted,
    normalised 0-1), M3 (per-class fractions dict). None if hist is empty."""
    if not hist:
        return None
    total = sum(hist.values())
    if total == 0:
        return None
    amd_px = sum(v for c, v in hist.items() if c in AMD_CLASSES)
    m1 = amd_px / total
    # NAP weight (7 - rank): rank 1 (highest acid production) -> weight 6.
    nap_weighted_px = sum(v * (7 - NAP_RANK[c]) for c, v in hist.items()
                          if c in NAP_RANK)
    m2 = nap_weighted_px / (total * 6.0)          # normalise to [0,1]
    m3 = {c: v / total for c, v in hist.items()}
    return dict(m1_amd_frac=m1, m2_nap_weighted=m2, m3_class_frac=m3,
               total_px=total, amd_px=amd_px)


# ---------------------------------------------------------------- stats

def spearman(x, y):
    import numpy as np
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    n = len(x)
    if n < 4:
        return float("nan"), n
    rx = _rank(x)
    ry = _rank(y)
    rho = np.corrcoef(rx, ry)[0, 1]
    return float(rho), n


def _rank(a):
    import numpy as np
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1)
    # average ranks over ties
    s = a[order]
    i = 0
    r = ranks[order]
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[i:j + 1] = r[i:j + 1].mean()
        i = j + 1
    ranks[order] = r
    return ranks


def loocv_r2(x, y):
    """Leave-one-out cross-validated R^2 for simple linear regression y~x.
    Returns (r2, n) - r2 can be negative (worse than predicting the mean)."""
    import numpy as np
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    n = len(x)
    if n < 5:
        return float("nan"), n
    preds = np.empty(n)
    for i in range(n):
        xi = np.delete(x, i)
        yi = np.delete(y, i)
        b1, b0 = np.polyfit(xi, yi, 1)
        preds[i] = b0 + b1 * x[i]
    ss_res = np.sum((y - preds) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(r2), n


# ---------------------------------------------------------------- pipeline

def run(region_key, chem_dir, min_samples, max_stations, out_csv, radius_km=60):
    from catchment_delineation import delineate, merit_upstream_area_km2

    ee = init_ee()
    stations = load_station_chemistry(chem_dir, min_samples)
    print("%s: %d stations with >=%d Fe/SO4 samples"
          % (region_key, len(stations), min_samples))

    ranked = sorted(stations.items(),
                    key=lambda kv: -max(kv[1].get("n_Iron_mgL_any", 0),
                                        kv[1].get("n_Sulfate_mgL", 0)))
    if max_stations:
        ranked = ranked[:max_stations]
    print("processing top %d by sample count" % len(ranked))

    catchments = {}                              # basin_id -> {geom, area, station_ids:[]}
    for sid, row in ranked:
        try:
            d = delineate(ee, row["lon"], row["lat"], radius_km=radius_km,
                          verbose=False)
        except Exception as exc:
            print("  %-22s DELINEATE FAILED: %s" % (sid, exc))
            continue
        bid = d["station_basin_id"]
        if bid not in catchments:
            catchments[bid] = dict(geom=d["catchment"], area_km2=d["area_km2"],
                                   n_basins=d["n_basins"],
                                   edge_touched=d["edge_touched"],
                                   station_ids=[], stations=[])
        catchments[bid]["station_ids"].append(sid)
        catchments[bid]["stations"].append(row)

    print("%d stations -> %d distinct catchments (dedup by shared basin)"
          % (len(ranked), len(catchments)))

    import statistics
    rows_out = []
    for i, (bid, c) in enumerate(catchments.items(), 1):
        names = ", ".join(s["name"][:20] for s in c["stations"][:3])
        print("\n[%d/%d] basin %s  area=%.1f km2  n_basins=%d  stations: %s%s"
              % (i, len(catchments), bid, c["area_km2"], c["n_basins"], names,
                 " (edge_touched!)" if c["edge_touched"] else ""))

        hist_ours, n_scenes = classify_catchment_ours(ee, c["geom"])
        if hist_ours is None:
            print("    SKIP - only %d scenes available" % n_scenes)
            continue
        m_ours = loading_metrics(hist_ours)
        print("    ours : %d scenes, %d valid px, AMD%%=%.2f%%, NAP-w=%.3f"
              % (n_scenes, m_ours["total_px"], 100 * m_ours["m1_amd_frac"],
                 m_ours["m2_nap_weighted"]))

        m_rw = None
        if region_key == "colorado":
            try:
                geojson = c["geom"].getInfo()
                hist_rw = classify_catchment_rockwell(geojson)
                m_rw = loading_metrics(hist_rw)
                if m_rw:
                    print("    rockwell: %d valid px, AMD%%=%.2f%%, NAP-w=%.3f"
                          % (m_rw["total_px"], 100 * m_rw["m1_amd_frac"],
                             m_rw["m2_nap_weighted"]))
            except Exception as exc:
                print("    rockwell FAILED: %s" % exc)

        # pool chemistry across every station sharing this catchment
        pooled_chem = {}
        for var in CHEM_VARS:
            vals = [s[var] for s in c["stations"] if s.get(var) is not None]
            pooled_chem[var] = statistics.median(vals) if vals else None

        rows_out.append(dict(
            basin_id=bid, area_km2=c["area_km2"], n_basins=c["n_basins"],
            n_stations=len(c["station_ids"]), n_scenes=n_scenes,
            edge_touched=c["edge_touched"],
            ours_m1=m_ours["m1_amd_frac"], ours_m2=m_ours["m2_nap_weighted"],
            rockwell_m1=m_rw["m1_amd_frac"] if m_rw else None,
            rockwell_m2=m_rw["m2_nap_weighted"] if m_rw else None,
            **pooled_chem))

    if not rows_out:
        print("\nNo catchments produced usable results.")
        return

    import csv as csvmod
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csvmod.DictWriter(fh, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
    print("\n-> %s (%d catchment rows)" % (out_csv, len(rows_out)))

    # ---------------- head-to-head report ----------------
    import math
    print("\n" + "=" * 88)
    print("HEAD-TO-HEAD: mineral loading vs measured chemistry (n=%d catchments)"
          % len(rows_out))
    print("CAVEAT: labels/pixels differ (ours=v3.0.x, Rockwell=published map); "
          "chemistry is REAL ground truth neither map was fitted to.")
    print("=" * 88)
    print("  %-24s %-10s %8s %8s %10s %10s"
          % ("chemistry var", "loading", "n", "spearman", "LOOCV_R2", "LOOCV_n"))
    for var in CHEM_VARS:
        y = [r.get(var) for r in rows_out]
        if all(v is None for v in y):
            continue
        y_f = [v if v is not None else float("nan") for v in y]
        for label, key in [("ours M1 (AMD%)", "ours_m1"),
                           ("ours M2 (NAP-w)", "ours_m2"),
                           ("rockwell M1", "rockwell_m1"),
                           ("rockwell M2", "rockwell_m2")]:
            x = [r.get(key) if r.get(key) is not None else float("nan")
                for r in rows_out]
            rho, n = spearman(x, y_f)
            r2, n2 = loocv_r2(x, y_f)
            if n < 4:
                continue
            print("  %-24s %-10s %8d %8.3f %10s %10s"
                  % (var, label, n, rho,
                     "%.3f" % r2 if not math.isnan(r2) else "n/a (n<5)",
                     n2 if not math.isnan(r2) else ""))
        print()

    print("Read rho as the primary result: monotonic association, no fitted\n"
          "coefficient, robust to outliers with few catchments. LOOCV R2 is\n"
          "the stricter OUT-OF-SAMPLE check on the linear form specifically -\n"
          "a negative value means the linear fit is worse than predicting the\n"
          "mean, which is common and informative with this few catchments.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", choices=["colorado", "ohio"], required=True)
    ap.add_argument("--min-samples", type=int, default=5)
    ap.add_argument("--max-stations", type=int, default=25)
    ap.add_argument("--radius-km", type=float, default=60)
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    if args.region == "colorado":
        chem_dir = os.path.join(ROOT, "data", "chemistry", "silverton_co")
    else:
        chem_dir = os.path.join(ROOT, "data", "chemistry")

    out = args.out or os.path.join(ROOT, "data", "matched",
                                   "watershed_nap_%s.csv" % args.region)
    run(args.region, chem_dir, args.min_samples, args.max_stations, out,
        args.radius_km)


if __name__ == "__main__":
    main()
