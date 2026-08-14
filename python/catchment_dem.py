"""True DEM flow-accumulation catchment delineation (MERIT Hydro D8).

Replaces the HydroSHEDS `hybas_12` approach in catchment_delineation.py, which
has a granularity floor (~35-95 sq mi near Silverton) that merges hydrologically
and chemically distinct tributaries into one polygon. The documented case:
Cement Creek - one of the most acidic tributaries in the Animas watershed -
shares a single hybas_12 polygon with the Animas mainstem and Howardsville
gauges, so its signal is averaged into cleaner water before anything is
measured. That dilution biases every Arm A number toward the null
(validation/ARM_A_CROSS_REGION_RETEST_2026-08-13.md), which is why fixing it
is the top open item rather than adding more regions.

Method (standard D8 upstream trace, no new dependencies beyond numpy/rasterio):
  1. Download MERIT Hydro `dir` (flow direction) and `upa` (upstream drainage
     area) as a GeoTIFF over a bbox around the station.
  2. SNAP the station to the channel - WQP/NWIS coordinates routinely sit tens
     to hundreds of metres off the modelled channel, and an unsnapped pour
     point traces a hillslope instead of a river. Snap = highest `upa` within a
     small window.
  3. Trace upstream: breadth-first from the pour point, at each cell checking
     which of its 8 neighbours flow INTO it.
  4. Detect clipping honestly: if any traced cell touches the downloaded
     raster's edge, the catchment ran off the tile and the result is
     incomplete - re-run with a larger radius. (This is a REAL clipping signal,
     unlike the hybas_12 version where no in-band signal existed.)

Verified against official USGS NWIS `drain_area_va` - see --self-test.

MERIT Hydro `dir` D8 encoding (verified empirically 2026-08-13):
  1=E  2=SE  4=S  8=SW  16=W  32=NW  64=N  128=NE
  0=river mouth, -1=inland depression, 247/255=ocean/nodata

    .venv/Scripts/python python/catchment_dem.py --self-test
"""

import argparse
import io
import json
import os
import zipfile

import numpy as np

KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"
SQMI_PER_KM2 = 0.386102
MERIT = "MERIT/Hydro/v1_0_1"

# dir code -> (drow, dcol). row increases SOUTHWARD in a north-up raster.
D8 = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
     16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}
# For neighbour at offset (dr, dc) from cell X, the neighbour flows INTO X iff
# its dir code maps to (-dr, -dc).
INFLOW_CODE = {(-dr, -dc): code for code, (dr, dc) in D8.items()}


def init_ee():
    import ee
    info = json.load(open(KEY))
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], KEY),
                  project=info["project_id"])
    return ee


def _fetch_band(ee, region, band, scale=92.77):
    """Download ONE MERIT band over `region` -> (array, transform)."""
    import rasterio
    import requests

    url = ee.Image(MERIT).select([band]).getDownloadURL({
        "region": region, "scale": scale, "format": "GEO_TIFF",
        "crs": "EPSG:4326",
    })
    resp = requests.get(url, timeout=900)
    if resp.status_code != 200:
        raise RuntimeError("MERIT %s download failed: %s %s"
                           % (band, resp.status_code, resp.content[:160]))
    with rasterio.open(io.BytesIO(resp.content)) as src:
        return src.read(1), src.transform


def fetch_merit(ee, lon, lat, radius_km, verbose=False):
    """Download MERIT `dir` + `upa` as ONE BAND PER REQUEST.

    Requesting both bands together returns "User memory limit exceeded" beyond
    ~20 km radius (the same server-side compute ceiling seen elsewhere in this
    project - it is about compute-graph size, not pixel count, so bestEffort
    does not help). Splitting into two single-band requests halves the per-
    request cost and was verified to work to at least a 60 km radius
    (1297x1630 px).

    Two single-band requests over the SAME region/scale/crs return identical
    shapes AND identical transform origins (verified 2026-08-13), so the two
    arrays align exactly with no resampling or stitching. An earlier attempt
    tiled the download with an explicit `crsTransform` to force alignment; GEE
    ignored the region extent in that mode and returned 1x1 tiles, so that
    approach was abandoned rather than worked around.

    Returns (dir_arr, upa_arr, transform, crs_string).
    """
    region = ee.Geometry.Point([lon, lat]).buffer(radius_km * 1000).bounds()
    if verbose:
        print("      fetching MERIT dir+upa at %d km radius" % radius_km)
    dir_arr, tr_d = _fetch_band(ee, region, "dir")
    upa_arr, tr_u = _fetch_band(ee, region, "upa")
    if dir_arr.shape != upa_arr.shape or tr_d != tr_u:
        raise RuntimeError("dir/upa grids disagree: %s@%s vs %s@%s"
                           % (dir_arr.shape, tr_d, upa_arr.shape, tr_u))
    return dir_arr, upa_arr, tr_d, "EPSG:4326"


def rowcol(transform, lon, lat):
    import rasterio
    r, c = rasterio.transform.rowcol(transform, lon, lat)
    return int(r), int(c)


def snap_to_channel(upa, r, c, window=2):
    """Move the pour point to the highest-accumulation cell within +/-window.

    WQP and NWIS coordinates sit off the modelled channel often enough that an
    unsnapped trace silently returns a hillslope of a few cells instead of a
    catchment. Snapping to max `upa` puts the pour point on the main channel.
    """
    r0, r1 = max(0, r - window), min(upa.shape[0], r + window + 1)
    c0, c1 = max(0, c - window), min(upa.shape[1], c + window + 1)
    sub = upa[r0:r1, c0:c1]
    if sub.size == 0:
        return r, c, float("nan")
    idx = np.unravel_index(np.nanargmax(sub), sub.shape)
    return r0 + int(idx[0]), c0 + int(idx[1]), float(sub[idx])


def trace_upstream(dir_arr, r, c):
    """Breadth-first upstream trace from a pour point.

    Returns (mask, touched_edge). mask[i,j] True for every cell draining to
    (r, c). touched_edge is True if the traced set reaches the raster border,
    which means the catchment continues beyond the downloaded tile and the
    result is INCOMPLETE.
    """
    nrow, ncol = dir_arr.shape
    mask = np.zeros(dir_arr.shape, dtype=bool)
    mask[r, c] = True
    stack = [(r, c)]
    touched_edge = False
    while stack:
        cr, cc = stack.pop()
        if cr == 0 or cc == 0 or cr == nrow - 1 or cc == ncol - 1:
            touched_edge = True
        for (dr, dc), code in INFLOW_CODE.items():
            nr, nc = cr + dr, cc + dc
            if nr < 0 or nc < 0 or nr >= nrow or nc >= ncol:
                continue
            if mask[nr, nc]:
                continue
            if int(dir_arr[nr, nc]) == code:
                mask[nr, nc] = True
                stack.append((nr, nc))
    return mask, touched_edge


def cell_area_km2(transform, lat):
    """Approximate cell area at a given latitude for an EPSG:4326 grid."""
    deg_lon = abs(transform.a)
    deg_lat = abs(transform.e)
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320 * np.cos(np.radians(lat))
    return deg_lon * km_per_deg_lon * deg_lat * km_per_deg_lat


def mask_to_geometry(ee, mask, transform, simplify_m=90):
    """Polygonise the catchment mask into an ee.Geometry."""
    import rasterio.features
    from shapely.geometry import shape
    from shapely.ops import unary_union

    shapes = list(rasterio.features.shapes(
        mask.astype(np.uint8), mask=mask, transform=transform))
    if not shapes:
        return None
    polys = [shape(geom) for geom, val in shapes if val == 1]
    merged = unary_union(polys)
    return ee.Geometry(json.loads(json.dumps(
        merged.__geo_interface__))).simplify(maxError=simplify_m)


def delineate(ee, lon, lat, radius_km=40, verbose=True, _tries=0):
    """Full DEM delineation with automatic tile growth on clipping.

    Returns dict with catchment geometry, area_km2, n_cells, snapped upa,
    touched_edge, radius_km used.
    """
    dir_arr, upa_arr, transform, _crs = fetch_merit(ee, lon, lat, radius_km, verbose)
    r, c = rowcol(transform, lon, lat)
    if not (0 <= r < dir_arr.shape[0] and 0 <= c < dir_arr.shape[1]):
        raise ValueError("station falls outside the fetched tile")
    sr, sc, snapped_upa = snap_to_channel(upa_arr, r, c)
    mask, touched_edge = trace_upstream(dir_arr, sr, sc)

    if touched_edge and _tries < 2:
        if verbose:
            print("      catchment reached tile edge - refetching at %d km"
                  % (radius_km * 2))
        return delineate(ee, lon, lat, radius_km * 2, verbose, _tries + 1)

    n_cells = int(mask.sum())
    area_km2 = n_cells * cell_area_km2(transform, lat)
    # Internal consistency check, free and independent of any external source:
    # MERIT's own `upa` band at the snapped cell is its precomputed upstream
    # drainage area. If our D8 trace is correct it must reproduce that number.
    # Verified 2026-08-13: ratio = 1.00 at all 6 validation gauges, which
    # separates "tracing is right" from "pour point is where USGS meant".
    trace_vs_upa = (area_km2 / snapped_upa if snapped_upa and
                   not np.isnan(snapped_upa) else float("nan"))
    return dict(mask=mask, transform=transform, n_cells=n_cells,
               area_km2=area_km2, snapped_upa_km2=snapped_upa,
               trace_vs_upa=trace_vs_upa,
               touched_edge=touched_edge, radius_km=radius_km,
               snap_offset_cells=(abs(sr - r), abs(sc - c)))


MERIT_DEG = 1.0 / 1200.0            # native 3 arcsec


def mask_to_global_cells(mask, transform):
    """Convert a catchment mask to a set of global MERIT grid indices.

    Each delineate() call downloads its own tile centred on its own station,
    and GEE's scale-based downloads do NOT land on exactly the same pixel grid
    (observed resolution 0.00083337 vs the native 1/1200 = 0.00083333, and
    arbitrary origins). Comparing two masks array-to-array is therefore invalid.
    Projecting both onto the shared global 1/1200-degree grid by rounding cell
    centres makes overlap well defined; the resolution discrepancy is 0.005%,
    i.e. <0.06 cells over a 1000-cell span, so rounding is safe.
    """
    rows, cols = np.nonzero(mask)
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    gcol = np.round((xs + 180.0) / MERIT_DEG).astype(np.int64)
    grow = np.round((90.0 - ys) / MERIT_DEG).astype(np.int64)
    return set(zip(grow.tolist(), gcol.tolist()))


def overlap_fraction(cells_a, cells_b):
    """Fraction of the SMALLER catchment contained in the larger.

    1.0 means one is fully nested inside the other. Takes global-cell SETS
    from mask_to_global_cells(), not raw masks - see that function for why.
    """
    if not cells_a or not cells_b:
        return 0.0
    inter = len(cells_a & cells_b)
    return inter / min(len(cells_a), len(cells_b))


def select_non_nested(catchments, max_overlap=0.5):
    """Greedily pick a set of catchments that are not substantially nested.

    WHY THIS MATTERS: with true DEM delineation every station gets its own
    catchment, and stations on the same river are DEEPLY nested - Animas below
    Silverton (146.7 sq mi) fully contains Animas at Silverton (90.2) which
    fully contains Howardsville (57.1). Their mineral loading and their
    chemistry are both largely the same water. Treating them as independent
    observations would inflate n and manufacture significance, which is the
    single biggest statistical hazard in moving from hybas_12 (where the
    coarse polygons accidentally prevented this) to DEM delineation.

    `catchments` is a list of dicts each with 'mask', 'transform' and
    'area_km2'. Smallest first, so headwaters are kept preferentially and the
    retained set carries the most independent information. Returns
    (kept_indices, dropped_pairs).
    """
    cells = [c.get("cells") or mask_to_global_cells(c["mask"], c["transform"])
            for c in catchments]
    order = sorted(range(len(catchments)), key=lambda i: catchments[i]["area_km2"])
    kept, dropped = [], []
    for i in order:
        conflict = None
        for j in kept:
            ov = overlap_fraction(cells[i], cells[j])
            if ov > max_overlap:
                conflict = (i, j, ov)
                break
        if conflict is None:
            kept.append(i)
        else:
            dropped.append(conflict)
    return sorted(kept), dropped


def nwis_drainage_area_sqmi(site_no):
    import urllib.request
    url = ("https://waterservices.usgs.gov/nwis/site/?sites=%s&format=rdb"
           "&siteOutput=expanded" % site_no)
    req = urllib.request.Request(url, headers={"User-Agent": "AMD-Detection-Tool/3.0"})
    try:
        txt = urllib.request.urlopen(req, timeout=60).read().decode()
    except Exception:
        return None
    lines = [l for l in txt.split("\n") if l and not l.startswith("#")]
    if len(lines) < 3 or "drain_area_va" not in lines[0]:
        return None
    try:
        return float(lines[2].split("\t")[lines[0].split("\t").index("drain_area_va")])
    except (ValueError, IndexError):
        return None


def self_test():
    """Validate against official USGS published drainage areas.

    Same 6 Animas gauges used to validate the hybas_12 approach, so the two
    methods are directly comparable. hybas_12 scored 1.17x-6.79x (it could not
    separate Howardsville / Silverton / Cement Creek at all - all three
    returned the identical 91.7 sq mi polygon).
    """
    ee = init_ee()
    stations = [
        ("09357500", -107.5995046, 37.83305235, 55.9, "Animas at Howardsville"),
        ("09358000", -107.6592278, 37.81110770, 70.6, "Animas at Silverton"),
        ("09358500", -107.6767278, 37.85555149, 13.5, "Cement Ck nr Silverton"),
        ("09358900", -107.7258952, 37.85110670, 11.0, "Mineral Ck abv Silverton"),
        ("09359000", -107.6958889, 37.81475000, 44.3, "Mineral Ck nr Silverton"),
        ("09359020", -107.6682222, 37.78833330, 146.0, "Animas blw Silverton"),
    ]
    print("%-10s %-26s %10s %10s %8s %7s %6s"
          % ("site", "name", "NWIS_sqmi", "DEM_sqmi", "ratio", "cells", "snap"))
    print("-" * 86)
    ratios = []
    for site, lon, lat, nwis, name in stations:
        try:
            d = delineate(ee, lon, lat, radius_km=40, verbose=False)
        except Exception as exc:
            print("%-10s %-26s FAILED: %s" % (site, name[:26], str(exc)[:34]))
            continue
        dem_sqmi = d["area_km2"] * SQMI_PER_KM2
        ratio = dem_sqmi / nwis if nwis else float("nan")
        ratios.append(ratio)
        flag = " EDGE!" if d["touched_edge"] else ""
        print("%-10s %-26s %10.1f %10.1f %7.2fx %7d %6s%s"
              % (site, name[:26], nwis, dem_sqmi, ratio, d["n_cells"],
                 "%d,%d" % d["snap_offset_cells"], flag))

    if not ratios:
        print("\nFAIL - nothing delineated.")
        return False
    within = [r for r in ratios if 0.75 <= r <= 1.33]
    print("\n%d/%d within +/-33%% of the official NWIS area (hybas_12 managed "
          "%d/6)" % (len(within), len(ratios), 2))
    print("Critically: Howardsville / Silverton / Cement Creek must now differ\n"
          "from each other - hybas_12 gave all three the identical 91.7 sq mi.")
    ok = len(within) >= max(4, int(0.66 * len(ratios)))
    print("\n%s" % ("PASS - DEM delineation is usable for Arm A."
                   if ok else "MARGINAL - inspect before trusting."))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--lon", type=float)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--radius-km", type=float, default=40)
    args = ap.parse_args(argv)

    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.lon is None or args.lat is None:
        ap.error("provide --lon/--lat, or --self-test")

    ee = init_ee()
    d = delineate(ee, args.lon, args.lat, args.radius_km)
    print("%d cells, %.1f km2 (%.1f sq mi), snapped upa=%.1f km2, edge=%s"
          % (d["n_cells"], d["area_km2"], d["area_km2"] * SQMI_PER_KM2,
             d["snapped_upa_km2"], d["touched_edge"]))


if __name__ == "__main__":
    main()
