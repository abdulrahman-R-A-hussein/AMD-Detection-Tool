"""Download per-sample water chemistry from the Water Quality Portal.

The WQP (waterqualitydata.us) aggregates USGS NWIS + EPA STORET + state agency
data. This pulls the DATED, per-sample records for the study lakes - not the
summary statistics - so each measurement can later be matched to a satellite
scene acquired near the same day (see match_scenes.py).

Why the fields matter (validation/WATER_VALIDATION_REPORT_2026-07-25.md):
  ResultSampleFractionText  Dissolved vs Total Recoverable. Total tracks
                            suspended sediment, which IS optically visible, so
                            pooling the two can manufacture a correlation that
                            has nothing to do with dissolved metal. Finding W4
                            showed Atwood's iron is 80/86 Total Recoverable.
  ResultDetectionConditionText  Non-detects carry no value; they must be kept
                            and handled explicitly, not silently dropped.

v3.0.4 (Water Phase 2): added Colorado (Animas River watershed, bbox around
Silverton). Verified 2026-08-10: 1,309 stations, 19,465 result rows, 841 dates,
4,743 DISSOLVED iron measurements (vs Ohio's 4 total) at median ~2.3 mg/L -
this is the water arm's first real positive control and the first place the
dissolved/total confound (finding W4) is actually testable.

Two things the Colorado pull requires that Ohio didn't:
  - REGIONS, not just LAKES. Colorado sites are STREAMS ("ANIMAS RIVER AT
    SILVERTON, CO"), so `_lake_of()` (station-name parsing assuming a lake
    name) is replaced by `_site_key()`, which returns the raw station name for
    stream sites and the parsed lake name for lake sites.
  - UNIT normalisation. Colorado's Iron results carry FOUR unit spellings
    (ug/L, ug/l, mg/L, and empty) plus 1,600 rows in mg/kg, which is SEDIMENT
    not water and must never enter a water regression. `_normalize_units()`
    converts everything to mg/L and tags sediment rows so callers can filter
    them explicitly rather than by accident.

Usage:
    .venv/Scripts/python python/fetch_wqp.py                    # all lakes (Ohio)
    .venv/Scripts/python python/fetch_wqp.py --lake "Lake Hope"
    .venv/Scripts/python python/fetch_wqp.py --region "Silverton, CO"
    .venv/Scripts/python python/fetch_wqp.py --region "Silverton, CO" --consolidate-only
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

# --- Since 2026-09-14 the definitions below live in the amdtool package and are
# imported here, so every name this script ever exported still resolves. Each was
# proven identical to this file as committed at ad05971 by
# tests/test_source_parity.py; see validation/AMDTOOL_REFACTOR_GATE_2026-09-14.md.
import _amdtool_path  # noqa: E402,F401  (src/amdtool importable from a bare clone)
from amdtool.regions import (  # noqa: E402,F401
    region_slug,
    REGIONS,
)
from amdtool.chemistry import (  # noqa: E402,F401
    WQP,
    EXCLUDE_SITE_TYPES,
    SOURCE_POINT_TYPES,
    site_category,
    _UNIT_TO_MGL,
    _NON_WATER_UNITS,
    normalize_iron_value,
    CHARACTERISTICS,
    START_DATE,
    _get,
    _lake_of,
    _site_key,
    consolidate,
)


# Study lakes. Iron values (ug/L) are the WQP medians/maxima established
# 2026-07-25 and are recorded here only as provenance for site selection.
#   name: (lat, lon, half_box_degrees, note)
LAKES = {
    "Piedmont Lake":         (40.1540, -81.2220, 0.07, "462 mg/L sulfate, Fe median 162 ug/L - high SO4 / low Fe"),
    "Atwood Lake":           (40.5496, -81.2462, 0.07, "18 mg/L sulfate control; Fe median 302 ug/L (mostly Total)"),
    "Somerset Reservoir":    (39.7839, -82.2919, 0.04, "Fe max 8510 ug/L - highest recorded; small lake"),
    "Burr Oak Reservoir":    (39.5422, -82.0572, 0.06, "Fe max 6860 ug/L; 2.7 km2 - best size/signal tradeoff"),
    "Lake Logan":            (39.5361, -82.4494, 0.05, "Fe max 6050 ug/L; 1.6 km2"),
    "Lake Hope":             (39.3206, -82.3544, 0.04, "Fe max 5780 ug/L; Carbondale AMD; 0.5 km2"),
    "New Lexington Res 1":   (39.7336, -82.2158, 0.03, "Fe max 3600 ug/L; small"),
    "Lake Rupert":           (39.1775, -82.5203, 0.05, "Fe max 2550 ug/L; 1.3 km2"),
    "St Joseph Lake":        (39.7700, -82.2889, 0.03, "Fe max 1230 ug/L; small"),
}


# ---------------------------------------------------------------------------
# Region registry.
#
# REGIONS below is the CURATED set: hand-checked bounding boxes whose notes
# record actual probed station counts. It stays authoritative.
#
# Regions added at the command line with --bbox land in a JSON overlay at
# data/regions.json instead, so pointing the pipeline at a new area no longer
# needs a source edit here (nor in seep_detect.REGIONS, cmd_detect.CMD_REGIONS
# or watershed_nap.KNOWN_REGIONS, which all resolve through this module).
#
# Lookup order is curated-first: an overlay entry can never shadow a curated
# one, so a stray --bbox cannot silently redefine Silverton.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGIONS_OVERLAY_PATH = os.path.join(REPO_ROOT, "data", "regions.json")


def load_overlay():
    """Read data/regions.json. Returns {} when absent or unreadable."""
    try:
        with open(REGIONS_OVERLAY_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (IOError, OSError, ValueError):
        return {}
    out = {}
    for name, e in raw.items():
        try:
            out[name] = (float(e["lat_lo"]), float(e["lon_lo"]),
                         float(e["lat_hi"]), float(e["lon_hi"]),
                         e.get("site_types"),
                         e.get("note", "added via --bbox"))
        except (KeyError, TypeError, ValueError):
            continue          # a malformed entry is skipped, never fatal
    return out


def all_regions():
    """Curated REGIONS plus the overlay. Curated entries win on conflict."""
    merged = dict(load_overlay())
    merged.update(REGIONS)
    return merged


def save_overlay_entry(name, lat_lo, lon_lo, lat_hi, lon_hi, note=""):
    """Add/replace one overlay region. Refuses to shadow a curated region."""
    if name in REGIONS:
        raise ValueError(
            "%r is a curated region; edit REGIONS in fetch_wqp.py to change it"
            % name)
    if not (-90 <= lat_lo < lat_hi <= 90):
        raise ValueError("need -90 <= lat_lo < lat_hi <= 90, got %s..%s"
                         % (lat_lo, lat_hi))
    if not (-180 <= lon_lo < lon_hi <= 180):
        raise ValueError("need -180 <= lon_lo < lon_hi <= 180, got %s..%s"
                         % (lon_lo, lon_hi))
    try:
        with open(REGIONS_OVERLAY_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (IOError, OSError, ValueError):
        raw = {}
    raw[name] = {"lat_lo": lat_lo, "lon_lo": lon_lo,
                 "lat_hi": lat_hi, "lon_hi": lon_hi,
                 "site_types": None,
                 "note": note or "added via --bbox"}
    os.makedirs(os.path.dirname(REGIONS_OVERLAY_PATH), exist_ok=True)
    with open(REGIONS_OVERLAY_PATH, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2, sort_keys=True)
    return REGIONS_OVERLAY_PATH


OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "chemistry")


def _bbox(lat, lon, half):
    return "%.4f,%.4f,%.4f,%.4f" % (lon - half, lat - half, lon + half, lat + half)


def fetch_lake(name, lat, lon, half):
    """Return (results_text, stations_text) for one lake."""
    common = {
        "bBox": _bbox(lat, lon, half),
        "siteType": "Lake, Reservoir, Impoundment",
        "mimeType": "csv",
        "zip": "no",
    }
    results = _get("Result", dict(common,
                                  characteristicName=CHARACTERISTICS,
                                  startDateLo=START_DATE))
    stations = _get("Station", common)
    return results, stations


def fetch_region(name, lat_lo, lon_lo, lat_hi, lon_hi, site_types=None):
    """Return (results_text, stations_text) for a bbox REGION (streams+lakes).

    site_types is deliberately unfiltered by default (None): WQP's siteType
    FILTER parameter uses a narrower, different vocabulary than
    MonitoringLocationTypeName and rejects (HTTP 400) many real type strings -
    see EXCLUDE_SITE_TYPES above. Filtering happens locally in consolidate().
    """
    common = {
        "bBox": "%.4f,%.4f,%.4f,%.4f" % (lon_lo, lat_lo, lon_hi, lat_hi),
        "mimeType": "csv",
        "zip": "no",
    }
    if site_types:
        common["siteType"] = site_types
    results = _get("Result", dict(common,
                                  characteristicName=CHARACTERISTICS,
                                  startDateLo=START_DATE))
    stations = _get("Station", common)
    return results, stations


def _summarise(text, lake):
    """Count rows and report the iron/sulfate spread, so a bad pull is obvious."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return "%-22s 0 rows" % lake, rows

    def vals(char):
        out = []
        for r in rows:
            if r.get("CharacteristicName") == char:
                try:
                    out.append(float(r.get("ResultMeasureValue") or ""))
                except ValueError:
                    pass                      # non-detect or blank; kept in CSV
        return out

    fe, so4 = vals("Iron"), vals("Sulfate")
    bits = ["%-22s %5d rows" % (lake, len(rows))]
    if fe:
        bits.append("Fe n=%-4d max=%-9.1f" % (len(fe), max(fe)))
    if so4:
        bits.append("SO4 n=%-4d max=%.1f" % (len(so4), max(so4)))
    return "  ".join(bits), rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lake", help="fetch a single lake by name (Ohio)")
    ap.add_argument("--region", help="fetch a named REGION by bbox (e.g. Colorado)")
    ap.add_argument("--out", help="output directory (default: data/chemistry "
                                  "for lakes, data/chemistry/<region-slug> for "
                                  "regions)")
    ap.add_argument("--consolidate-only", action="store_true",
                    help="skip downloading; just rebuild consolidated.csv")
    ap.add_argument("--bbox",
                    help="register a NEW region by bounding box, as "
                         "'lat_lo,lon_lo,lat_hi,lon_hi', then fetch it. "
                         "Requires --region to supply the name. The entry is "
                         "written to data/regions.json so the rest of the "
                         "pipeline can resolve it without a source edit.")
    ap.add_argument("--list-regions", action="store_true",
                    help="print known regions (curated + overlay) and exit")
    args = ap.parse_args(argv)

    if args.list_regions:
        overlay = load_overlay()
        for name in sorted(all_regions()):
            print("  %-32s %-9s %s" % (
                name, "[curated]" if name in REGIONS else "[overlay]",
                region_slug(name)))
        print("\n%d curated, %d overlay" % (len(REGIONS), len(overlay)))
        return

    if args.region and args.lake:
        sys.exit("--region and --lake are mutually exclusive")

    if args.bbox:
        if not args.region:
            sys.exit("--bbox needs --region to name the new region, e.g.\n"
                     '  --region "West Branch Susquehanna, PA" '
                     '--bbox "40.6,-78.6,41.4,-77.2"')
        parts = [p.strip() for p in args.bbox.split(",")]
        if len(parts) != 4:
            sys.exit("--bbox must be 'lat_lo,lon_lo,lat_hi,lon_hi'")
        try:
            lat_lo, lon_lo, lat_hi, lon_hi = [float(p) for p in parts]
        except ValueError:
            sys.exit("--bbox values must all be numbers")
        try:
            path = save_overlay_entry(args.region, lat_lo, lon_lo, lat_hi, lon_hi)
        except ValueError as exc:
            sys.exit(str(exc))
        print("registered %r -> %s" % (args.region, path))
        print("  bbox  %.4f,%.4f .. %.4f,%.4f" % (lat_lo, lon_lo, lat_hi, lon_hi))
        print("  slug  %s" % region_slug(args.region))

    known = all_regions()
    if args.region:
        if args.region not in known:
            sys.exit("Unknown region %r.\nKnown: %s\n"
                     "To add one: --region %r --bbox 'lat_lo,lon_lo,lat_hi,lon_hi'"
                     % (args.region, ", ".join(sorted(known)), args.region))
        out_dir = args.out or os.path.join(OUT_DIR, region_slug(args.region))
    else:
        out_dir = args.out or OUT_DIR

    if args.consolidate_only:
        n_water, n_sed = consolidate(out_dir)
        print("consolidated %d water rows, %d sediment rows" % (n_water, n_sed))
        return

    os.makedirs(out_dir, exist_ok=True)
    station_rows, total = [], 0

    if args.region:
        lat_lo, lon_lo, lat_hi, lon_hi, site_types, _note = known[args.region]
        slug = region_slug(args.region)
        try:
            results, stations = fetch_region(args.region, lat_lo, lon_lo,
                                             lat_hi, lon_hi, site_types)
        except RuntimeError as exc:
            sys.exit("%s FAILED: %s" % (args.region, exc))

        with open(os.path.join(out_dir, "%s_results.csv" % slug), "w",
                  encoding="utf-8", newline="") as fh:
            fh.write(results)

        line, rows = _summarise(results, args.region)
        print(line)
        total += len(rows)

        for s in csv.DictReader(io.StringIO(stations)):
            station_rows.append({
                "lake": _site_key(s.get("MonitoringLocationName", ""),
                                  s.get("MonitoringLocationTypeName", "")),
                "station_id": s.get("MonitoringLocationIdentifier", ""),
                "station_name": s.get("MonitoringLocationName", ""),
                "lat": s.get("LatitudeMeasure", ""),
                "lon": s.get("LongitudeMeasure", ""),
                "site_type": s.get("MonitoringLocationTypeName", ""),
                "organization": s.get("OrganizationFormalName", ""),
            })
    else:
        if args.lake and args.lake not in LAKES:
            sys.exit("Unknown lake %r. Known: %s" % (args.lake, ", ".join(LAKES)))
        targets = ({args.lake: LAKES[args.lake]} if args.lake else LAKES)

        for lake, (lat, lon, half, _note) in targets.items():
            slug = lake.lower().replace(" ", "_")
            try:
                results, stations = fetch_lake(lake, lat, lon, half)
            except RuntimeError as exc:
                print("%-22s FAILED: %s" % (lake, exc))
                continue

            with open(os.path.join(out_dir, "%s_results.csv" % slug), "w",
                      encoding="utf-8", newline="") as fh:
                fh.write(results)

            line, rows = _summarise(results, lake)
            print(line)
            total += len(rows)

            for s in csv.DictReader(io.StringIO(stations)):
                station_rows.append({
                    "lake": lake,
                    "station_id": s.get("MonitoringLocationIdentifier", ""),
                    "station_name": s.get("MonitoringLocationName", ""),
                    "lat": s.get("LatitudeMeasure", ""),
                    "lon": s.get("LongitudeMeasure", ""),
                    "site_type": s.get("MonitoringLocationTypeName", ""),
                    "organization": s.get("OrganizationFormalName", ""),
                })

    if station_rows:
        path = os.path.join(out_dir, "stations.csv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(station_rows[0]))
            w.writeheader()
            w.writerows(station_rows)
        print("\n%d result rows, %d stations -> %s" % (total, len(station_rows), out_dir))
        n_water, n_sed = consolidate(out_dir)
        print("consolidated %d water rows, %d sediment rows (duplicates "
              "removed; site assigned by station name/type)" % (n_water, n_sed))


if __name__ == "__main__":
    main()
