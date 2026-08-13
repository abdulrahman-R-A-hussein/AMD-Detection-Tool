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
import os
import sys
import time
import urllib.parse
import urllib.request

WQP = "https://www.waterqualitydata.us/data"

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

# Regions pulled by BBOX rather than a named point - used for Colorado, where
# the target is the whole Animas River watershed (streams + a few lakes), not
# one named waterbody. (lat_lo, lon_lo, lat_hi, lon_hi, siteTypes, note)
# WQP's siteType FILTER parameter is a small fixed domain (Stream, Lake,
# Reservoir, Impoundment, Spring, Well, Facility, Land, Atmosphere, ...) that
# is DIFFERENT from and narrower than the values a station's
# MonitoringLocationTypeName can actually hold. Verified 2026-08-10: passing
# "River/Stream", "Reservoir", "Lake", "Canal *", "Ditch", or any
# "Mine/Mine Discharge *" / "Subsurface: Tunnel..." value as siteType causes an
# HTTP 400 (not a silent empty result) - the filter parameter simply does not
# accept those strings, even though real stations carry them.
#
# The robust fix: fetch_region() sends NO siteType filter (bbox + date +
# characteristics only, so every type comes back), and filtering happens
# locally against MonitoringLocationTypeName via EXCLUDE_SITE_TYPES. That
# recovered 11,410 Iron rows (vs 3,844 under the old "Stream"-only filter),
# including the mine-discharge/adit/spring source points that are the highest-
# concentration, most AMD-diagnostic samples in the record.
EXCLUDE_SITE_TYPES = {
    "CERCLA Superfund Site",   # verified: unnamed stations, IDs like -AS-/-SE-
                               # (air/sediment sample codes) - not water
    "Land",                    # snow-course sites (e.g. "... SNOW SITE, CO")
    "Atmosphere",
    "Well", "Well: Multiple wells",
    "Well: Test hole not completed as a well",
    "Facility: Laboratory or sample-preparation area",
}

REGIONS = {
    "Silverton, CO": (
        37.70, -107.85, 37.95, -107.50, None,
        "Animas River watershed incl. Cement Creek, Mineral Creek. Verified "
        "2026-08-10, no server-side siteType filter (see EXCLUDE_SITE_TYPES): "
        "11410 Iron rows, 5681 Sulfate, across 3606 stations including "
        "62 mine-discharge/adit/tailings/spring source points.",
    ),
    # Added 2026-08-13 (Water Phase 2 Part B) specifically to raise Arm A's n
    # beyond its verified 6-catchment ceiling at Silverton: hybas_12 has a
    # granularity floor there, and 82 stations spanning that whole search area
    # all collapsed into the same 6 polygons. Raising n needs DIFFERENT river
    # systems, not more Silverton stations - each region below drains to a
    # different major system, verified independent by river network, not just
    # by distance:
    #   Animas (Silverton, above)         -> San Juan -> Colorado River
    #   Uncompahgre (Ouray)                -> Gunnison -> Colorado River
    #   Alma/Fairplay, Leadville           -> Arkansas River (two districts)
    #   Creede                             -> Rio Grande
    #   Clear Creek/Central City           -> South Platte River
    #   Lake City/Lake Fork                -> Gunnison (Lake Fork tributary)
    # Counts are Iron-characteristic probe results (WQP, 2026-08-10/13),
    # >=3-sample station counts are what actually matters for a chemistry
    # median; verify per-region distinct-catchment count once delineated,
    # same as Silverton was - do not assume more stations means more n.
    "Ouray, CO": (
        37.95, -107.90, 38.20, -107.55, None,
        "Uncompahgre River watershed (Gunnison system). Probed 2026-08-10: "
        "2935 Iron rows, 134 stations, 101 with >=3 samples.",
    ),
    "Alma, CO": (
        39.20, -106.20, 39.45, -105.95, None,
        "Arkansas River headwaters, Alma/Fairplay mining district. Probed "
        "2026-08-10: 472 Iron rows, 31 stations, 27 with >=3 samples.",
    ),
    "Leadville, CO": (
        39.15, -106.45, 39.35, -106.15, None,
        "Arkansas River headwaters, California Gulch Superfund site "
        "(different district from Alma, same river system). Probed "
        "2026-08-13: 1685 Iron rows, 83 stations, 72 with >=3 samples.",
    ),
    "Creede, CO": (
        37.75, -107.00, 37.95, -106.75, None,
        "Rio Grande headwaters, Creede mining district (Bulldog Mountain/"
        "Nelson Tunnel). Probed 2026-08-13: 438 Iron rows, 34 stations, "
        "21 with >=3 samples.",
    ),
    "Central City, CO": (
        39.65, -105.75, 39.85, -105.40, None,
        "South Platte River system, Clear Creek/Central City Superfund site. "
        "Probed 2026-08-13: 2317 Iron rows, 161 stations, 105 with >=3 "
        "samples - richest of the new regions.",
    ),
    "Lake City, CO": (
        37.90, -107.45, 38.15, -107.15, None,
        "Lake Fork of the Gunnison, Lake City mining district. Probed "
        "2026-08-13: 202 Iron rows, 13 stations, 11 with >=3 samples - "
        "thinnest of the new regions, may collapse to very few catchments.",
    ),
}

# For downstream regression: source points (mine discharge) carry the highest
# concentrations and are point sources; in-stream sites are diluted and
# integrate upstream area. Arm A should NOT pool these two categories without
# recording which is which - a station's category is a first-class covariate.
SOURCE_POINT_TYPES = {
    "Mine/Mine Discharge Adit (Mine Entrance)", "Mine/Mine Discharge",
    "Mine/Mine Discharge Tailings Pile", "Mine/Mine Discharge Waste Rock Pile",
    "Subsurface: Tunnel, shaft, or mine", "Spring",
}


def site_category(site_type):
    """'source' (mine discharge/spring/adit) vs 'instream' (stream/lake/canal)."""
    return "source" if site_type in SOURCE_POINT_TYPES else "instream"

# WQP spells the same unit multiple ways; case differs by source agency.
_UNIT_TO_MGL = {
    "mg/l": 1.0, "mg/L": 1.0,
    "ug/l": 0.001, "ug/L": 0.001, "µg/l": 0.001, "µg/L": 0.001,
}
# Units that are NOT water concentration - must be split out, never regressed
# against water chemistry. mg/kg is sediment; the others are non-concentration.
_NON_WATER_UNITS = {"mg/kg", "mg/kg dry", "ug/kg", "ug/g", "lb/day",
                    "ug/m3", "mg/m3"}


def normalize_iron_value(raw_value, raw_unit):
    """Return (mg_per_L, is_water) for one WQP Iron result.

    mg_per_L is None if the unit is unrecognised or non-numeric. is_water is
    False for sediment/loading units (mg/kg, lb/day, ...) - these rows must be
    routed to a separate table, never silently dropped OR silently pooled.
    """
    unit = (raw_unit or "").strip()
    unit_ci = unit.lower()
    try:
        val = float(raw_value)
    except (TypeError, ValueError):
        return None, None
    if unit_ci in _NON_WATER_UNITS or unit_ci.replace(" ", "") in _NON_WATER_UNITS:
        return val, False
    factor = _UNIT_TO_MGL.get(unit) or _UNIT_TO_MGL.get(unit_ci)
    if factor is None:
        return None, None                    # unrecognised unit - flag, don't guess
    return val * factor, True

# Iron and sulfate are the targets; the rest are the optical confounds that
# finding W3 could not rule out, plus co-varying AMD metals.
CHARACTERISTICS = [
    "Iron",
    "Sulfate",
    "pH",
    "Turbidity",
    "Total suspended solids",
    "Specific conductance",
    "Chlorophyll a",
    "Manganese",
    "Aluminum",
    "Temperature, water",
    "Depth, Secchi disk depth",
]

START_DATE = "01-01-2013"   # Landsat 8 onward; WQP wants MM-DD-YYYY
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "chemistry")


def _bbox(lat, lon, half):
    return "%.4f,%.4f,%.4f,%.4f" % (lon - half, lat - half, lon + half, lat + half)


def _get(endpoint, params, retries=3):
    """GET a WQP CSV endpoint, returning decoded text."""
    qs = urllib.parse.urlencode(params, doseq=True)
    url = "%s/%s/search?%s" % (WQP, endpoint, qs)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "AMD-Detection-Tool/2.5 (research)"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as exc:                      # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("WQP request failed after %d tries: %s\n%s"
                       % (retries, last, url))


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


def _lake_of(station_name):
    """Derive the waterbody from a LAKE station name (Ohio-style).

    Neighbouring lakes fall inside each other's bounding boxes (Somerset and
    St Joseph are ~1.5 km apart), so bbox membership CANNOT be used to say
    which lake a sample belongs to - it produced 614 duplicated rows and
    attributed Somerset's 8510 ug/L peak to St Joseph as well. Station names
    are authoritative: "SOMERSET RESERVOIR, L-1" -> "Somerset Reservoir".
    """
    import re
    head = re.split(r",|\s+L-\d", str(station_name))[0]
    return head.strip().title() or "Unknown"


def _site_key(station_name, site_type):
    """Generalisation of _lake_of() for regions with STREAMS as well as lakes.

    A stream station name ("ANIMAS RIVER AT SILVERTON, CO.") does not name a
    single shared waterbody the way "SOMERSET RESERVOIR, L-1" does - the comma
    splits off a real, meaningful qualifier (the location on the river), not a
    station-number suffix. So streams keep their full station name as the key
    (one key per gauge), while lakes still collapse via _lake_of() so repeat
    stations on one lake (L-1, L-2, ...) merge as before.
    """
    if str(site_type).strip().lower().startswith("stream"):
        return str(station_name).strip().title() or "Unknown"
    return _lake_of(station_name)


def consolidate(out_dir):
    """Merge the per-lake/region pulls into one deduplicated, site-attributed
    table, with Iron unit-normalised and sediment rows split out.

    The "lake" column name is kept for backward compatibility with
    match_scenes.py and everything downstream that reads it - it now holds a
    lake name OR a stream station name, produced by _site_key(). Sediment rows
    (mg/kg Iron) are written to a SEPARATE consolidated_sediment.csv rather
    than dropped or mixed in, per the Colorado verification finding that 1,600
    of Silverton's Iron rows are mg/kg.
    """
    import glob
    seen, rows, sed_rows, fieldnames = set(), [], [], None
    stations = {}
    spath = os.path.join(out_dir, "stations.csv")
    if os.path.exists(spath):
        with open(spath, encoding="utf-8") as fh:
            for s in csv.DictReader(fh):
                stations[s["station_id"]] = (s["station_name"], s.get("site_type", ""))

    for path in sorted(glob.glob(os.path.join(out_dir, "*_results.csv"))):
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                key = (r.get("MonitoringLocationIdentifier"),
                       r.get("ActivityStartDate"),
                       r.get("CharacteristicName"),
                       r.get("ResultMeasureValue"),
                       r.get("ResultMeasure/MeasureUnitCode"),
                       r.get("ResultSampleFractionText"),
                       r.get("ActivityDepthHeightMeasure/MeasureValue"))
                if key in seen:
                    continue
                seen.add(key)
                sid = r.get("MonitoringLocationIdentifier", "")
                sname, stype = stations.get(sid, (sid, ""))
                if stype in EXCLUDE_SITE_TYPES:
                    continue                    # snow/air/sediment/well/lab - not surface water
                r["lake"] = _site_key(sname, stype)
                r["site_type"] = stype
                r["site_category"] = site_category(stype)

                if r.get("CharacteristicName") == "Iron":
                    mgl, is_water = normalize_iron_value(
                        r.get("ResultMeasureValue"),
                        r.get("ResultMeasure/MeasureUnitCode"))
                    r["Iron_mgL"] = "" if mgl is None else "%.6g" % mgl
                    if is_water is False:
                        sed_rows.append(r)
                        continue                    # sediment - not a water row
                    if is_water is None:
                        r["Iron_mgL"] = ""           # unrecognised unit - flagged, not guessed

                if fieldnames is None:
                    fieldnames = list(r)
                elif len(r) > len(fieldnames):
                    # BUG FIXED 2026-08-10: capturing fieldnames from only the
                    # FIRST row silently dropped Iron_mgL whenever that first
                    # row wasn't an Iron characteristic (extrasaction="ignore"
                    # discards any key not in `fieldnames` from every later
                    # row too) - confirmed missing from Ohio's consolidated.csv
                    # while present in Colorado's, purely because of file/row
                    # iteration order. Track the widest row seen instead.
                    fieldnames = list(r)
                rows.append(r)

    if not rows and not sed_rows:
        return 0, 0

    # Union of every key seen across BOTH tables, not just the widest single
    # row - a key present only on some water rows (or only on sediment rows)
    # must still make it into the shared column list for both files.
    all_fields = list(fieldnames or [])
    for r in rows + sed_rows:
        for k in r:
            if k not in all_fields:
                all_fields.append(k)

    path = os.path.join(out_dir, "consolidated.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=all_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    if sed_rows:
        spath2 = os.path.join(out_dir, "consolidated_sediment.csv")
        with open(spath2, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=all_fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(sed_rows)

    return len(rows), len(sed_rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lake", help="fetch a single lake by name (Ohio)")
    ap.add_argument("--region", help="fetch a named REGION by bbox (e.g. Colorado)")
    ap.add_argument("--out", help="output directory (default: data/chemistry "
                                  "for lakes, data/chemistry/<region-slug> for "
                                  "regions)")
    ap.add_argument("--consolidate-only", action="store_true",
                    help="skip downloading; just rebuild consolidated.csv")
    args = ap.parse_args(argv)

    if args.region and args.lake:
        sys.exit("--region and --lake are mutually exclusive")

    if args.region:
        if args.region not in REGIONS:
            sys.exit("Unknown region %r. Known: %s" % (args.region, ", ".join(REGIONS)))
        out_dir = args.out or os.path.join(
            OUT_DIR, args.region.lower().replace(", ", "_").replace(" ", "_"))
    else:
        out_dir = args.out or OUT_DIR

    if args.consolidate_only:
        n_water, n_sed = consolidate(out_dir)
        print("consolidated %d water rows, %d sediment rows" % (n_water, n_sed))
        return

    os.makedirs(out_dir, exist_ok=True)
    station_rows, total = [], 0

    if args.region:
        lat_lo, lon_lo, lat_hi, lon_hi, site_types, _note = REGIONS[args.region]
        slug = args.region.lower().replace(", ", "_").replace(" ", "_")
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
