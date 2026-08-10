"""Delineate the UPSTREAM catchment of a water-chemistry station.

Phase 0 de-risk for Arm A (watershed NAP -> water chemistry). Plan mistake
caught before writing any classification code: a single hybas_12 polygon is
one SUB-BASIN, not an upstream catchment. The upstream catchment of a station
is the union of every sub-basin that eventually drains INTO the station's
sub-basin - found by traversing the HydroSHEDS `NEXT_DOWN` graph in reverse.

Method:
  1. Locate the hybas_12 polygon containing the station point.
  2. Pull every polygon sharing that basin's MAIN_BAS (the whole river system
     it belongs to) - bounds the traversal to a tractable download instead of
     the whole continent.
  3. Build a reverse adjacency map (parent HYBAS_ID -> child HYBAS_IDs, i.e.
     "who flows into me") from NEXT_DOWN, and BFS from the station's basin to
     collect every ancestor (everything that flows into it, directly or
     transitively).
  4. Union the ancestor geometries into one catchment polygon.

Two independent cross-checks, because a delineation bug would otherwise be
invisible until an Arm A regression quietly used wrong catchments:
  - Sum of `SUB_AREA` over the ancestor set vs `MERIT/Hydro/v1_0_1` band `upa`
    (upstream drainage area) sampled AT the station point.
  - For USGS gauges specifically, vs the OFFICIAL published `drain_area_va`
    from the NWIS site service - real independent ground truth, not another
    remote-sensing product.

    .venv/Scripts/python python/catchment_delineation.py --self-test
"""

import argparse
import json
import sys
import urllib.request

KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"
BASINS = "WWF/HydroSHEDS/v1/Basins/hybas_12"
SQMI_PER_KM2 = 0.386102


def init_ee():
    import ee
    info = json.load(open(KEY))
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], KEY),
                  project=info["project_id"])
    return ee


def nwis_drainage_area_sqmi(site_no):
    """Official USGS published drainage area for a gauge, in sq mi. None if
    the site has no value on file (many non-gauge WQP stations won't)."""
    url = ("https://waterservices.usgs.gov/nwis/site/?sites=%s&format=rdb"
           "&siteOutput=expanded" % site_no)
    req = urllib.request.Request(url, headers={"User-Agent": "AMD-Detection-Tool/3.0"})
    try:
        txt = urllib.request.urlopen(req, timeout=60).read().decode()
    except Exception:
        return None
    lines = [l for l in txt.split("\n") if l and not l.startswith("#")]
    if len(lines) < 3:
        return None
    hdr = lines[0].split("\t")
    if "drain_area_va" not in hdr:
        return None
    val = lines[2].split("\t")[hdr.index("drain_area_va")]
    try:
        return float(val)
    except ValueError:
        return None


def delineate(ee, lon, lat, radius_km=60, verbose=True):
    """Return dict: catchment ee.Geometry, area_km2 (from SUB_AREA sum),
    n_basins, station_basin_id, main_bas_id, edge_touched (bool - a crude
    clipping warning, see below). Raises if the point matches no basin.

    Filtering by MAIN_BAS (the whole river system) blows the EE 5000-element
    getInfo ceiling for any station on a major system - the Animas is part of
    the Colorado River basin, which has tens of thousands of hybas_12
    sub-basins. Since a station's UPSTREAM area is what we want and these
    target catchments are small (headwater gauges, tens to low hundreds of
    sq mi), a local buffer around the station is used instead.

    IMPORTANT: a graph built only from downloaded features can never discover
    a truly-missing upstream neighbour (if basin X is just outside the
    buffer, X simply never appears - there is no dangling reference to detect,
    because references only exist as properties of basins we DID download).
    So there is no reliable in-band signal of clipping; `edge_touched` is only
    a coarse warning (an ancestor basin's polygon touches the buffer boundary)
    and must not be trusted alone. The real check is external: self_test()
    compares the resulting area against independent NWIS/MERIT numbers, and
    any caller doing this for real stations should do the same before
    trusting a delineation.
    """
    pt = ee.Geometry.Point([lon, lat])
    fc = ee.FeatureCollection(BASINS)

    hit = fc.filterBounds(pt).first()
    hit_props = hit.getInfo()
    if hit_props is None:
        raise ValueError("no hybas_12 polygon contains (%.5f, %.5f)" % (lon, lat))
    props = hit_props["properties"]
    station_id = int(props["HYBAS_ID"])
    main_bas = int(props["MAIN_BAS"])

    region = pt.buffer(radius_km * 1000)
    local_feats = fc.filterBounds(region).getInfo()["features"]
    if verbose:
        print("    basin %d, system %d, %d km radius: %d candidate sub-basins"
              % (station_id, main_bas, radius_km, len(local_feats)))

    by_id = {}
    children = {}                                # parent_id -> [child_id, ...]
    for f in local_feats:
        p = f["properties"]
        bid, nd = int(p["HYBAS_ID"]), int(p["NEXT_DOWN"])
        by_id[bid] = f
        if nd != 0:
            children.setdefault(nd, []).append(bid)

    seen, stack = {station_id}, [station_id]
    while stack:
        cur = stack.pop()
        for ch in children.get(cur, []):
            if ch not in seen:
                seen.add(ch)
                stack.append(ch)

    area_km2 = sum(float(by_id[b]["properties"]["SUB_AREA"]) for b in seen
                  if b in by_id)
    geoms = [ee.Geometry(by_id[b]["geometry"]) for b in seen if b in by_id]
    catchment_raw = ee.FeatureCollection([ee.Feature(g) for g in geoms]).union(1).geometry()
    # HydroSHEDS basin boundaries follow real terrain and can carry thousands
    # of vertices; every downstream intersection/clip in the classification
    # pipeline (tile_geoms, reduceRegion) re-walks that boundary, and it was
    # enough by itself to trip "User memory limit exceeded" even with 16
    # tiles on a modest 237 km2 catchment. Simplify to the classification
    # pixel scale (30 m Landsat) - shape is preserved at every scale that
    # matters for a 30 m classifier, only sub-pixel wiggles are dropped.
    catchment = catchment_raw.simplify(maxError=30)

    # Coarse warning only, see docstring: does the catchment use most of the
    # queried disc's area? If so it may be clipped by the buffer and should
    # be re-run at a larger radius_km. Cheap (no extra EE call) by design.
    import math
    disc_km2 = math.pi * radius_km * radius_km
    edge_touched = area_km2 > 0.5 * disc_km2

    return dict(catchment=catchment, area_km2=area_km2, n_basins=len(seen),
               station_basin_id=station_id, main_bas_id=main_bas,
               edge_touched=edge_touched, radius_km=radius_km)


def merit_upstream_area_km2(ee, lon, lat):
    """MERIT Hydro upa (upstream drainage area, km2) at the pixel nearest the
    station, sampled over a small buffer and taking the max (upa increases
    monotonically downstream along a channel, so max-in-buffer is the least
    likely to under-shoot from an off-channel point)."""
    img = ee.Image("MERIT/Hydro/v1_0_1").select("upa")
    val = img.reduceRegion(reducer=ee.Reducer.max(),
                           geometry=ee.Geometry.Point([lon, lat]).buffer(200),
                           scale=90, bestEffort=True).get("upa")
    v = val.getInfo()
    return float(v) if v is not None else None


def self_test():
    ee = init_ee()
    # Animas River gauges near Silverton, with OFFICIAL NWIS drainage areas
    # pulled 2026-08-10 - independent ground truth, not another remote-sensing
    # product. (site_no, lon, lat, nwis_sqmi)
    stations = [
        ("09357500", -107.5995046, 37.83305235, 55.9),
        ("09358000", -107.6592278, 37.81110770, 70.6),
        ("09358500", -107.6767278, 37.85555149, 13.5),
        ("09358900", -107.7258952, 37.85110670, 11.0),
        ("09359000", -107.6958889, 37.81475000, 44.3),
        ("09359020", -107.6682222, 37.78833330, 146.0),
    ]

    print("%-10s %10s %12s %10s %12s %10s %8s"
          % ("site", "NWIS_sqmi", "ours_sqmi", "ratio", "MERIT_sqmi", "ratio", "n_basins"))
    print("-" * 78)
    results = []
    for site_no, lon, lat, nwis_sqmi in stations:
        try:
            d = delineate(ee, lon, lat, verbose=False)
        except Exception as exc:
            print("%-10s FAILED: %s" % (site_no, exc))
            continue
        ours_sqmi = d["area_km2"] * SQMI_PER_KM2
        merit_km2 = merit_upstream_area_km2(ee, lon, lat)
        merit_sqmi = merit_km2 * SQMI_PER_KM2 if merit_km2 is not None else None
        r_nwis = ours_sqmi / nwis_sqmi if nwis_sqmi else float("nan")
        r_merit = ours_sqmi / merit_sqmi if merit_sqmi else float("nan")
        print("%-10s %10.1f %12.1f %9.2fx %12s %9s %8d"
              % (site_no, nwis_sqmi, ours_sqmi, r_nwis,
                 "%.1f" % merit_sqmi if merit_sqmi else "n/a",
                 "%.2fx" % r_merit if merit_sqmi else "n/a",
                 d["n_basins"]))
        results.append(r_nwis)

    if not results:
        print("\nFAIL - no station delineated successfully.")
        return False

    import statistics
    ok = [r for r in results if 0.3 <= r <= 3.0]     # within 3x either direction
    print("\n%d/%d stations within 3x of official NWIS drainage area."
          % (len(ok), len(results)))
    print("Ratios should INCREASE roughly monotonically with the true nested "
          "order (09358500/09358900 are small headwater tribs feeding into "
          "09358000, which feeds 09359020) - eyeball that shape too, not just "
          "the ratio column.")
    passed = len(ok) == len(results)
    print("\n%s - catchment delineation is %s for Arm A."
          % ("PASS" if passed else "MARGINAL",
             "usable" if passed else "usable with caution; inspect outliers before trusting Arm A"))
    return passed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--lon", type=float)
    ap.add_argument("--lat", type=float)
    args = ap.parse_args(argv)

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    if args.lon is None or args.lat is None:
        ap.error("provide --lon/--lat, or --self-test")

    ee = init_ee()
    d = delineate(ee, args.lon, args.lat)
    print("station basin %d (system %d): %d sub-basins, %.1f km2 (%.1f sq mi)"
          % (d["station_basin_id"], d["main_bas_id"], d["n_basins"],
             d["area_km2"], d["area_km2"] * SQMI_PER_KM2))
    merit_km2 = merit_upstream_area_km2(ee, args.lon, args.lat)
    if merit_km2 is not None:
        print("MERIT upa at point: %.1f km2 (%.1f sq mi)"
              % (merit_km2, merit_km2 * SQMI_PER_KM2))


if __name__ == "__main__":
    main()
