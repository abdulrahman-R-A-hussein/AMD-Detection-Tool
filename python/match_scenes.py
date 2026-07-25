"""Match water-chemistry samples to near-coincident Sentinel-2 scenes.

For every (station, sample-date) pair in data/chemistry/consolidated.csv this
finds Sentinel-2 scenes acquired within +/- N days, applies the v2.4.0 water
mask, and extracts a 3x3-window median reflectance at the station coordinate.
The output is the matched spectra <-> chemistry table that the detection-limit
regression consumes.

Design decisions worth knowing (validation/WATER_VALIDATION_REPORT_2026-07-25.md):

* SINGLE SCENES, never a median composite. A composite averages away the very
  event we are trying to observe; chemistry is measured on one day.
* The 3x3 window must be ENTIRELY water. Mixed shoreline pixels are what made
  the earlier water-only VPCA return `green_veg` as its dominant component.
  n_water is recorded so partial windows can be filtered rather than silently
  averaged in.
* Iron is split by sample fraction. Total Recoverable includes suspended
  ferric particulates, which scatter light and ARE optically detectable;
  dissolved Fe is a different physical quantity. 184 of 191 records are Total
  Recoverable, so pooling them would confound the two.

Auth uses the Earth Engine service account from the VPCA project.

Usage:
    .venv/Scripts/python python/match_scenes.py
    .venv/Scripts/python python/match_scenes.py --days 5 --lake "Lake Hope"
"""

import argparse
import csv
import datetime as dt
import os
import sys

CHEM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "chemistry", "consolidated.csv")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "matched", "matched_spectra_chemistry.csv")
KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"

# Sentinel-2 SR -> the SR_B1..SR_B7 naming the rest of the toolchain uses.
# B8A (865 nm) rather than B8 (842 nm) because it matches Landsat 8 B5.
S2_MAP = [("B1", "SR_B1"), ("B2", "SR_B2"), ("B3", "SR_B3"), ("B4", "SR_B4"),
          ("B8A", "SR_B5"), ("B11", "SR_B6"), ("B12", "SR_B7")]

# Chemistry to carry through. Iron is handled separately (split by fraction).
CHARS = ["Sulfate", "pH", "Turbidity", "Total suspended solids",
         "Specific conductance", "Chlorophyll a", "Manganese", "Aluminum"]


def init_ee():
    import json

    import ee
    with open(KEY) as fh:
        info = json.load(fh)
    ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], KEY),
                  project=info["project_id"])
    return ee


def load_samples(path, lake_filter=None):
    """Collapse the long WQP table into one record per (station, date)."""
    stations, samples = {}, {}
    spath = os.path.join(os.path.dirname(path), "stations.csv")
    with open(spath, encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            try:
                stations[s["station_id"]] = (float(s["lat"]), float(s["lon"]))
            except (ValueError, KeyError):
                pass

    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            sid = r.get("MonitoringLocationIdentifier", "")
            date = (r.get("ActivityStartDate") or "")[:10]
            if sid not in stations or len(date) != 10:
                continue
            if lake_filter and r.get("lake") != lake_filter:
                continue
            char = r.get("CharacteristicName", "")
            frac = (r.get("ResultSampleFractionText") or "").replace(" ", "")
            try:
                val = float(r.get("ResultMeasureValue") or "")
            except ValueError:
                continue                      # non-detect / qualifier-only row

            rec = samples.setdefault((sid, date), {
                "station_id": sid, "date": date, "lake": r.get("lake", ""),
                "lat": stations[sid][0], "lon": stations[sid][1],
            })
            col = ("Iron_%s" % (frac or "Unspecified")) if char == "Iron" else char
            if char == "Iron" or char in CHARS:
                rec[col] = val
                if char == "Iron":
                    rec["Iron_unit"] = r.get("ResultMeasure/MeasureUnitCode", "")
    return list(samples.values())


def water_mask(ee, img, sensor):
    """v2.4.0 scene-independent water mask + per-sensor cloud rejection.

    Landsat 8/9 is supported because COPERNICUS/S2_SR_HARMONIZED only begins
    2017-03-28, while the chemistry record starts in 2013 - 316 of 449 samples
    predate Sentinel-2 surface reflectance. L8/L9 is 30 m, so it is only
    trustworthy on the larger lakes.
    """
    if sensor == "S2":
        b = {dst: img.select(src).divide(10000) for src, dst in S2_MAP}
        scl = img.select("SCL")
        clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(1))
    else:                                     # Landsat 8/9 Collection 2 L2
        b = {n: img.select(n).multiply(0.0000275).subtract(0.2)
             for n in ("SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7")}
        qa = img.select("QA_PIXEL")            # bits 1-4: dilated/cirrus/cloud/shadow
        clear = (qa.bitwiseAnd(1 << 1).eq(0).And(qa.bitwiseAnd(1 << 2).eq(0))
                 .And(qa.bitwiseAnd(1 << 3).eq(0)).And(qa.bitwiseAnd(1 << 4).eq(0)))

    mndwi = b["SR_B3"].subtract(b["SR_B6"]).divide(b["SR_B3"].add(b["SR_B6"]))
    ndvi = b["SR_B5"].subtract(b["SR_B4"]).divide(b["SR_B5"].add(b["SR_B4"]))
    bright = b["SR_B2"].add(b["SR_B3"]).add(b["SR_B4"]).divide(3)
    awei = (b["SR_B2"].add(b["SR_B3"].multiply(2.5))
            .subtract(b["SR_B5"].multiply(1.5))
            .subtract(b["SR_B7"].multiply(0.25)))
    mask = (mndwi.gt(0.3).And(awei.gt(0.0)).And(ndvi.lt(0.0))
            .And(b["SR_B5"].lt(b["SR_B3"])).And(bright.lt(0.30)).And(clear))
    stack = ee.Image.cat([b[n].rename(n) for n in
                          ("SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7")])
    return stack, mask


def candidates(ee, pts, lo, hi, sensors):
    """Yield (sensor, image, scale) options for a date window, finest first."""
    out = []
    if "S2" in sensors:
        c = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterBounds(pts).filterDate(lo, hi).sort("CLOUDY_PIXEL_PERCENTAGE"))
        out.append(("S2", c, 20.0, "CLOUDY_PIXEL_PERCENTAGE"))
    if "L8" in sensors:
        c = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
             .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
             .filterBounds(pts).filterDate(lo, hi).sort("CLOUD_COVER"))
        out.append(("L8", c, 30.0, "CLOUD_COVER"))
    return out


def match(ee, samples, days, radius, scale, min_water=10, sensors=("S2", "L8")):
    """One GEE round-trip per (lake, date); returns matched rows.

    Grouped by LAKE as well as date: the study lakes are >100 km apart, so a
    MultiPoint spanning all of them selects the least-cloudy Sentinel-2 tile
    over ANY of them, which then contains no data at the rest. Grouping keeps
    every point inside one tile footprint.
    """
    by_date = {}
    for s in samples:
        by_date.setdefault((s["lake"], s["date"]), []).append(s)

    rows, dates = [], sorted(by_date)
    for i, (lake, date) in enumerate(dates, 1):
        group = by_date[(lake, date)]
        d0 = dt.date.fromisoformat(date)
        lo = (d0 - dt.timedelta(days=days)).isoformat()
        hi = (d0 + dt.timedelta(days=days + 1)).isoformat()
        pts = ee.Geometry.MultiPoint([[s["lon"], s["lat"]] for s in group])

        best = None
        for sensor, col, sscale, cloudkey in candidates(ee, pts, lo, hi, sensors):
            try:
                if not col.size().getInfo():
                    continue
            except Exception as exc:                  # noqa: BLE001
                print("  [%3d/%3d] %-26s %s  EE error: %s"
                      % (i, len(dates), lake[:26], date, str(exc)[:60]))
                continue

            img = ee.Image(col.first())
            stack, mask = water_mask(ee, img, sensor)
            masked = stack.updateMask(mask)
            feats = []
            for s in group:
                pt = ee.Geometry.Point([s["lon"], s["lat"]]).buffer(radius)
                vals = masked.reduceRegion(ee.Reducer.median(), pt, sscale, maxPixels=1e7)
                cnt = mask.rename("n_water").reduceRegion(ee.Reducer.sum(), pt, sscale,
                                                          maxPixels=1e7)
                feats.append(ee.Feature(None, vals.combine(cnt)
                                        .set("station_id", s["station_id"])))
            try:
                got = ee.FeatureCollection(feats).getInfo()["features"]
                scene = img.get("system:index").getInfo()
                cloud = img.get(cloudkey).getInfo()
                sdate = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()
            except Exception as exc:                  # noqa: BLE001
                print("  [%3d/%3d] %-26s %s  sample failed: %s"
                      % (i, len(dates), lake[:26], date, str(exc)[:60]))
                continue

            usable = [(s, f["properties"]) for s, f in zip(group, got)
                      if f["properties"].get("SR_B3") is not None
                      and (f["properties"].get("n_water") or 0) >= min_water]
            # Prefer the finer sensor, but fall back if it yields nothing usable.
            if usable and (best is None or len(usable) > len(best[0])):
                best = (usable, sensor, scene, cloud, sdate)
            if best and sensor == "S2":
                break

        if not best:
            print("  [%3d/%3d] %-26s %s  no usable scene" % (i, len(dates), lake[:26], date))
            continue

        usable, sensor, scene, cloud, sdate = best
        off = (dt.date.fromisoformat(sdate) - d0).days
        for s, p in usable:
            row = dict(s)
            row.update({k: p.get(k) for k in
                        ("SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7")})
            row.update({"n_water": p.get("n_water"), "sensor": sensor,
                        "scene_id": scene, "scene_date": sdate,
                        "cloud_pct": cloud, "day_offset": off})
            rows.append(row)
        print("  [%3d/%3d] %-26s %s  %s %+dd %2.0f%% cloud  %d/%d matched"
              % (i, len(dates), lake[:26], date, sensor, off, cloud, len(usable), len(group)))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=3, help="match window, +/- days")
    ap.add_argument("--radius", type=float, default=300.0,
                    help="sampling buffer in metres. NOT 30 m: WQP station "
                         "coordinates sit on shore access points and dams, not "
                         "open water - at r=30 m most stations return 0-6 water "
                         "pixels, at r=150-400 m they return 21-900. We "
                         "therefore sample lake water NEAR the station, not the "
                         "station pixel itself; defensible for small, well-mixed "
                         "reservoirs but it must be stated in any write-up")
    ap.add_argument("--scale", type=float, default=20.0, help="sampling scale (m)")
    ap.add_argument("--min-water", type=int, default=10,
                    help="minimum clean water pixels in the buffer to keep a row")
    ap.add_argument("--lake", help="restrict to one lake")
    ap.add_argument("--start", default="2013-04-11",
                    help="earliest sample date (default: Landsat 8 first light). "
                         "S2 surface reflectance only begins 2017-03-28, so "
                         "earlier samples are matched against Landsat 8/9")
    ap.add_argument("--sensors", default="S2,L8",
                    help="comma list, finest first. S2 is 10-20 m; L8/L9 is 30 m "
                         "and only trustworthy on the larger lakes")
    ap.add_argument("--require", default="any",
                    choices=["any", "iron", "iron_or_sulfate"],
                    help="only match samples carrying these analytes")
    ap.add_argument("--chem", default=CHEM)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    samples = load_samples(args.chem, args.lake)
    if not samples:
        sys.exit("No samples found in %s" % args.chem)

    n0 = len(samples)
    samples = [s for s in samples if s["date"] >= args.start]
    dropped = n0 - len(samples)
    if args.require != "any":
        def has(s):
            fe = any(k.startswith("Iron_") for k in s)
            return fe if args.require == "iron" else (fe or "Sulfate" in s)
        samples = [s for s in samples if has(s)]
    if not samples:
        sys.exit("No samples left after filtering (start=%s)" % args.start)
    print("dropped %d sample(s) before %s (no S2 surface reflectance)"
          % (dropped, args.start))
    dates = sorted({s["date"] for s in samples})
    print("%d station-date samples, %d distinct dates (%s .. %s)"
          % (len(samples), len(dates), dates[0], dates[-1]))

    ee = init_ee()
    rows = match(ee, samples, args.days, args.radius, args.scale, args.min_water,
                 tuple(s.strip() for s in args.sensors.split(",") if s.strip()))
    if not rows:
        sys.exit("No matches produced.")

    cols, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    fe = sum(1 for r in rows if any(k.startswith("Iron_") for k in r))
    print("\n%d matched rows -> %s" % (len(rows), args.out))
    print("%d carry an iron measurement; median water pixels/window = %d"
          % (fe, sorted(r.get("n_water") or 0 for r in rows)[len(rows) // 2]))


if __name__ == "__main__":
    main()
