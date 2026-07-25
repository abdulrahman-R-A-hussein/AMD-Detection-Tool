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

Usage:
    .venv/Scripts/python python/fetch_wqp.py            # all lakes
    .venv/Scripts/python python/fetch_wqp.py --lake "Lake Hope"
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
    """Derive the waterbody from a station name.

    Neighbouring lakes fall inside each other's bounding boxes (Somerset and
    St Joseph are ~1.5 km apart), so bbox membership CANNOT be used to say
    which lake a sample belongs to - it produced 614 duplicated rows and
    attributed Somerset's 8510 ug/L peak to St Joseph as well. Station names
    are authoritative: "SOMERSET RESERVOIR, L-1" -> "Somerset Reservoir".
    """
    import re
    head = re.split(r",|\s+L-\d", str(station_name))[0]
    return head.strip().title() or "Unknown"


def consolidate(out_dir):
    """Merge the per-lake pulls into one deduplicated, lake-attributed table."""
    import glob
    seen, rows, fieldnames = set(), [], None
    stations = {}
    spath = os.path.join(out_dir, "stations.csv")
    if os.path.exists(spath):
        with open(spath, encoding="utf-8") as fh:
            for s in csv.DictReader(fh):
                stations[s["station_id"]] = s["station_name"]

    for path in sorted(glob.glob(os.path.join(out_dir, "*_results.csv"))):
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                key = (r.get("MonitoringLocationIdentifier"),
                       r.get("ActivityStartDate"),
                       r.get("CharacteristicName"),
                       r.get("ResultMeasureValue"),
                       r.get("ResultSampleFractionText"),
                       r.get("ActivityDepthHeightMeasure/MeasureValue"))
                if key in seen:
                    continue
                seen.add(key)
                sid = r.get("MonitoringLocationIdentifier", "")
                r["lake"] = _lake_of(stations.get(sid, sid))
                if fieldnames is None:
                    fieldnames = list(r)
                rows.append(r)

    if not rows:
        return 0
    path = os.path.join(out_dir, "consolidated.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lake", help="fetch a single lake by name")
    ap.add_argument("--out", default=OUT_DIR, help="output directory")
    ap.add_argument("--consolidate-only", action="store_true",
                    help="skip downloading; just rebuild consolidated.csv")
    args = ap.parse_args(argv)

    if args.consolidate_only:
        print("consolidated %d unique rows" % consolidate(args.out))
        return

    if args.lake and args.lake not in LAKES:
        sys.exit("Unknown lake %r. Known: %s" % (args.lake, ", ".join(LAKES)))
    targets = ({args.lake: LAKES[args.lake]} if args.lake else LAKES)

    os.makedirs(args.out, exist_ok=True)
    station_rows, total = [], 0

    for lake, (lat, lon, half, _note) in targets.items():
        slug = lake.lower().replace(" ", "_")
        try:
            results, stations = fetch_lake(lake, lat, lon, half)
        except RuntimeError as exc:
            print("%-22s FAILED: %s" % (lake, exc))
            continue

        with open(os.path.join(args.out, "%s_results.csv" % slug), "w",
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
        path = os.path.join(args.out, "stations.csv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(station_rows[0]))
            w.writeheader()
            w.writerows(station_rows)
        print("\n%d result rows, %d stations -> %s" % (total, len(station_rows), args.out))
        print("consolidated %d unique rows (duplicates removed; lake assigned "
              "by station name)" % consolidate(args.out))


if __name__ == "__main__":
    main()
