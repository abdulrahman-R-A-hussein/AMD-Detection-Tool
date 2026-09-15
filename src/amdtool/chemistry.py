"""Water chemistry: Water Quality Portal download, consolidation, and per-station medians.

Moved 2026-09-14 from python/fetch_wqp.py (WQP, CHARACTERISTICS, START_DATE,
EXCLUDE_SITE_TYPES, SOURCE_POINT_TYPES, site_category, normalize_iron_value,
_get, fetch_region, _lake_of, _site_key, consolidate, and the stations.csv
mapping in its main) and python/watershed_nap.py (load_station_chemistry,
CHEM_VARS). The bodies are unchanged except where marked: fetch_region takes a
BBox, and a failed request raises WqpRequestError (still a RuntimeError, so
callers that caught RuntimeError keep working).

`stations_in_bbox` and `fetch_wqp` are new: the one loader and the one
downloader the severity report and SpectraLab use, replacing three
near-identical station loaders (seep_detect.load_region_points,
cmd_detect.load_cmd_stations, and the loop in watershed_nap).

Units, as the source scripts assumed and did not check: iron in mg/L
(normalised at fetch time), sulfate in mg/L, conductance as reported. Station
values are MEDIANS OVER EVERY DATE on record, not synchronous with any image.
The Water Quality Portal covers the United States only.
"""

import csv
import glob
import io
import os
import re
import statistics
import time
import urllib.parse
import urllib.request
from collections import defaultdict

from amdtool.errors import AmdToolError, InsufficientDataError

WQP = "https://www.waterqualitydata.us/data"
USER_AGENT = "AMD-Detection-Tool/2.5 (research)"

# Site types that are not surface water. Filtered locally in consolidate():
# WQP's siteType FILTER parameter uses a narrower vocabulary than
# MonitoringLocationTypeName and rejects (HTTP 400) many real type strings.
EXCLUDE_SITE_TYPES = {
    "CERCLA Superfund Site",   # verified: unnamed stations, IDs like -AS-/-SE-
                               # (air/sediment sample codes) - not water
    "Land",                    # snow-course sites (e.g. "... SNOW SITE, CO")
    "Atmosphere",
    "Well", "Well: Multiple wells",
    "Well: Test hole not completed as a well",
    "Facility: Laboratory or sample-preparation area",
}

SOURCE_POINT_TYPES = {
    "Mine/Mine Discharge Adit (Mine Entrance)", "Mine/Mine Discharge",
    "Mine/Mine Discharge Tailings Pile", "Mine/Mine Discharge Waste Rock Pile",
    "Subsurface: Tunnel, shaft, or mine", "Spring",
}

CHEM_VARS = ["Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH",
             "SpecificConductance"]

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

# WQP spells the same unit multiple ways; case differs by source agency.
_UNIT_TO_MGL = {
    "mg/l": 1.0, "mg/L": 1.0,
    "ug/l": 0.001, "ug/L": 0.001, "µg/l": 0.001, "µg/L": 0.001,
}
# Units that are NOT water concentration - must be split out, never regressed
# against water chemistry. mg/kg is sediment; the others are non-concentration.
_NON_WATER_UNITS = {"mg/kg", "mg/kg dry", "ug/kg", "ug/g", "lb/day",
                    "ug/m3", "mg/m3"}

STATION_FIELDS = ["lake", "station_id", "station_name", "lat", "lon",
                  "site_type", "organization"]


class WqpRequestError(AmdToolError, RuntimeError):
    """A Water Quality Portal request failed after its retries."""


def site_category(site_type):
    """'source' (mine discharge/spring/adit) vs 'instream' (stream/lake/canal)."""
    return "source" if site_type in SOURCE_POINT_TYPES else "instream"


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


def _get(endpoint, params, retries=3):
    """GET a WQP CSV endpoint, returning decoded text."""
    qs = urllib.parse.urlencode(params, doseq=True)
    url = "%s/%s/search?%s" % (WQP, endpoint, qs)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as exc:                      # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    # CHANGED: WqpRequestError instead of RuntimeError (it subclasses both).
    raise WqpRequestError("WQP request failed after %d tries: %s\n%s"
                          % (retries, last, url))


def wqp_bbox(bbox):
    """WQP's bBox parameter: west,south,east,north at 4 decimals."""
    return "%.4f,%.4f,%.4f,%.4f" % (bbox.lon_lo, bbox.lat_lo, bbox.lon_hi, bbox.lat_hi)


def fetch_region(bbox, site_types=None):
    """Return (results_text, stations_text) for a bbox REGION (streams+lakes).

    CHANGED: takes an amdtool.geometry.BBox instead of (name, lat_lo, lon_lo,
    lat_hi, lon_hi); the request is byte-identical.

    site_types is deliberately unfiltered by default (None): WQP's siteType
    FILTER parameter uses a narrower, different vocabulary than
    MonitoringLocationTypeName and rejects (HTTP 400) many real type strings -
    see EXCLUDE_SITE_TYPES above. Filtering happens locally in consolidate().
    """
    common = {
        "bBox": wqp_bbox(bbox),
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


def _lake_of(station_name):
    """Derive the waterbody from a LAKE station name (Ohio-style).

    Neighbouring lakes fall inside each other's bounding boxes (Somerset and
    St Joseph are ~1.5 km apart), so bbox membership CANNOT be used to say
    which lake a sample belongs to - it produced 614 duplicated rows and
    attributed Somerset's 8510 ug/L peak to St Joseph as well. Station names
    are authoritative: "SOMERSET RESERVOIR, L-1" -> "Somerset Reservoir".
    """
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


def station_rows_from_wqp(stations_text):
    """WQP Station CSV text -> stations.csv rows (the region branch of fetch_wqp.main)."""
    rows = []
    for s in csv.DictReader(io.StringIO(stations_text)):
        rows.append({
            "lake": _site_key(s.get("MonitoringLocationName", ""),
                              s.get("MonitoringLocationTypeName", "")),
            "station_id": s.get("MonitoringLocationIdentifier", ""),
            "station_name": s.get("MonitoringLocationName", ""),
            "lat": s.get("LatitudeMeasure", ""),
            "lon": s.get("LongitudeMeasure", ""),
            "site_type": s.get("MonitoringLocationTypeName", ""),
            "organization": s.get("OrganizationFormalName", ""),
        })
    return rows


def write_stations(out_dir, station_rows):
    path = os.path.join(out_dir, "stations.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(station_rows[0]))
        w.writeheader()
        w.writerows(station_rows)
    return path


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


def fetch_wqp(bbox, out_dir, slug="aoi", site_types=None):
    """Download every WQP station and result in `bbox` into `out_dir`, then
    consolidate. Returns (n_water_rows, n_sediment_rows).

    Writes <slug>_results.csv, stations.csv, consolidated.csv (and
    consolidated_sediment.csv when there is sediment) - the folder layout every
    loader here reads. Raises InsufficientDataError when the portal has no
    stations or no water results in the box (it covers the United States only).
    """
    os.makedirs(out_dir, exist_ok=True)
    results, stations = fetch_region(bbox, site_types)
    station_rows = station_rows_from_wqp(stations)
    if not station_rows:
        raise InsufficientDataError(
            "the Water Quality Portal has no monitoring stations in this AOI "
            "(it covers the United States only)")
    with open(os.path.join(out_dir, "%s_results.csv" % slug), "w",
              encoding="utf-8", newline="") as fh:
        fh.write(results)
    write_stations(out_dir, station_rows)
    n_water, n_sed = consolidate(out_dir)
    if n_water == 0:
        raise InsufficientDataError(
            "the Water Quality Portal has %d stations in this AOI but no water "
            "results for %s since %s" % (len(station_rows), ", ".join(CHARACTERISTICS[:2]),
                                         START_DATE))
    return n_water, n_sed


def load_station_chemistry(chem_dir, min_samples):
    """Return {station_id: {var: median, 'n_'+var: n, 'lat':, 'lon':, 'name':}}
    for stations with >= min_samples Iron_mgL OR Sulfate measurements.
    Excludes sediment (Iron_mgL blank for those rows - already split at fetch
    time) and mixes fraction types only where finding W4 says it is safe:
    Iron is kept split (dissolved vs any), Sulfate/pH/conductance are not
    fraction-sensitive in the same way and are pooled.
    """
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


def stations_in_bbox(chem_dir, bbox=None, station_set="all", require_any=None):
    """Stations with chemistry, as [{"pid","lat","lon","site_type","name",<CHEM_VARS>}].

    bbox         amdtool.geometry.BBox, or None for every station in the folder.
    station_set  "all", "sources" (mine discharge / adit / tailings / tunnel /
                 spring) or "instream".
    require_any  analyte names; a station is kept only if at least one of them
                 has a value. None keeps every station with any chemistry.
    """
    if station_set not in ("all", "sources", "instream"):
        raise ValueError("station_set must be 'all', 'sources' or 'instream'")
    chem = load_station_chemistry(chem_dir, 0)
    out = []
    with open(os.path.join(chem_dir, "stations.csv"), encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            c = chem.get(s["station_id"])
            if not c or not s.get("lat") or not s.get("lon"):
                continue
            lat, lon = float(s["lat"]), float(s["lon"])
            if bbox is not None and not bbox.contains(lat, lon):
                continue
            cat = site_category(s.get("site_type", ""))
            if station_set == "sources" and cat != "source":
                continue
            if station_set == "instream" and cat != "instream":
                continue
            if require_any and all(c.get(a) is None for a in require_any):
                continue
            rec = dict(c)
            rec.update(pid=s["station_id"], lat=lat, lon=lon)
            out.append(rec)
    return out
