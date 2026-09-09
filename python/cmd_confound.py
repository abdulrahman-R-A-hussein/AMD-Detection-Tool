"""Phase CMD2 - the mining-extent confound test for the Ohio CMD result.

READ validation/CMD2_PREREGISTRATION_2026-09-08.md FIRST (committed as a452446,
before any mine polygon was joined to any chemistry or index value).

WHAT IS BEING TESTED. CMD1's geometry amendment found NDVI_stress tracking
measured sulfate at rho=-0.354 (n=137, 30 m radius, within-region perm
p=0.0028). The report named one confound as the gate on whether that means
anything: high-sulfate stations may simply drain more heavily mined ground with
less vegetation overall - land cover, not a seep.

WHY ODNR AND NOT NLCD. The signal under test is a VEGETATION index. An
NLCD-derived covariate is itself built from Landsat reflectance and shares the
NDVI physics, so conditioning on it would partly regress the signal on itself -
the W1/C3 circularity in a new costume. ODNR MinesOfOhio comes from mine permit
records, historical topographic maps and geologic maps. It owes nothing to any
satellite. That is the whole reason it was chosen.

THE ASYMMETRY, REGISTERED IN ADVANCE (preregistration section 6). Mining extent
is not a nuisance variable - it is the physical CAUSE of the sulfate. So a
surviving partial correlation is strong evidence, while a collapsing one is
ambiguous between a real confound and over-control. The registered rule is that
a collapse counts as CONFOUND SUPPORTED and the claim is withdrawn; over-control
may be noted but may NOT be used to keep the claim alive. T2 (the far-field
radius ladder, run through cmd_detect.py) breaks that tie with independent
machinery.

WORDING CONSTRAINT: sulfate has no VNIR absorption. Nothing here is optical
sulfate detection. Any association is with vegetation that CO-VARIES with it.

    python cmd_confound.py --mines        # VPCA venv (network only)
    python cmd_confound.py --catchments   # VPCA venv (needs ee + rasterio)
    python cmd_confound.py --analyse      # either venv
"""

import argparse
import csv
import glob
import json
import math
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seep_detect import OUTDIR, SEED, load_extracted, spearman, variance_split
from cmd_detect import CMD_REGIONS, load_cmd_stations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINEDIR = os.path.join(ROOT, "data", "mines")

ODNR = ("https://gis.ohiodnr.gov/arcgis/rest/services/MRM_Services"
        "/MinesOfOhio/MapServer")

# Layer ids fixed in the pre-registration. Proposed/permitted-but-unmined
# (11, 17, 18) are excluded - not disturbed ground. Industrial minerals
# (25-34) are excluded - this is a coal-drainage question.
SURFACE_COAL = [12, 13, 14, 15]     # Current, Past, Historic-topo, Historic-geol
UNDER_COAL = [19, 20, 22, 23]       # Current, Past, Abandoned pre-1977 (part/known)
COAL_LAYERS = SURFACE_COAL + UNDER_COAL

MERIT_MARGIN_KM = 25.0     # upstream margin beyond the station bounding box
MERIT_MAX_KM = 60.0        # verified working ceiling in catchment_dem.py
DISC_RADII_KM = [1.0, 5.0]  # secondary robustness ladder
PRIMARY_RADIUS = 30.0      # the radius the confound is being tested at
N_PERM = 5000

# Registered decision thresholds (preregistration section 5).
RHO_REJECT, RHO_SUPPORT, ATTEN_LIMIT = 0.25, 0.15, 0.40
RAW_RHO = -0.354           # the published value attenuation is measured against


# ---------------------------------------------------------------- mine polygons

def _get(url, params, tries=4):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180)
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    return d
                last = d["error"]
            else:
                last = "HTTP %s" % r.status_code
        except Exception as exc:            # network flakiness killed two runs
            last = repr(exc)                # before; retry rather than lose a slug
        time.sleep(2 * (k + 1))
    raise RuntimeError("ODNR query failed after %d tries: %s" % (tries, last))


def _rings_to_polygons(rings):
    """ArcGIS rings -> shapely polygons, honouring holes by ring orientation.

    ArcGIS encodes exterior rings clockwise (negative shoelace in standard
    orientation) and holes counter-clockwise, all in one flat list. Treating
    every ring as its own polygon would double-count donuts; mine polygons do
    contain them (an underground works mapped around an unmined pillar).
    """
    from shapely.geometry import Polygon
    out, holes = [], []
    for ring in rings:
        if len(ring) < 4:
            continue
        area2 = 0.0
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            area2 += x0 * y1 - x1 * y0
        (out if area2 < 0 else holes).append(ring)
    polys = []
    for shell in out:
        poly = Polygon(shell)
        mine = [h for h in holes if Polygon(h).representative_point().within(poly)]
        polys.append(Polygon(shell, mine) if mine else poly)
    if not polys and holes:                 # all rings CCW -> orientation is not
        polys = [Polygon(h) for h in holes]  # meaningful here, keep them as areas
    return [p for p in polys if p.is_valid or p.buffer(0).is_valid]


def fetch_mines(slug, bbox, out_path):
    """Download every coal-mining polygon intersecting bbox -> GeoJSON cache.

    Paged by OBJECTID rather than resultOffset: returnIdsOnly is supported on
    every layer here, while pagination support varies by layer, and an
    unsupported resultOffset is silently IGNORED rather than erroring - which
    would return page 1 forever and quietly truncate the covariate.
    """
    geom = dict(xmin=bbox[0], ymin=bbox[1], xmax=bbox[2], ymax=bbox[3],
                spatialReference=dict(wkid=4326))
    feats = []
    for lid in COAL_LAYERS:
        base = dict(geometry=json.dumps(geom),
                    geometryType="esriGeometryEnvelope", inSR=4326,
                    spatialRel="esriSpatialRelIntersects", where="1=1", f="json")
        ids = _get("%s/%d/query" % (ODNR, lid),
                   dict(base, returnIdsOnly="true")).get("objectIds") or []
        got = 0
        for i in range(0, len(ids), 400):
            chunk = ids[i:i + 400]
            d = _get("%s/%d/query" % (ODNR, lid),
                     dict(base, objectIds=",".join(str(x) for x in chunk),
                          outFields="", returnGeometry="true", outSR=4326))
            for f in d.get("features", []):
                rings = (f.get("geometry") or {}).get("rings")
                if rings:
                    feats.append(dict(layer=lid, rings=rings))
                    got += 1
        print("    L%-2d %-38s %5d polygons"
              % (lid, _LAYER_NAME.get(lid, ""), got))
    os.makedirs(MINEDIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(dict(slug=slug, bbox=bbox, features=feats), fh)
    print("  -> %s (%d polygons)" % (out_path, len(feats)))
    return feats


_LAYER_NAME = {12: "surface coal - current", 13: "surface coal - past",
               14: "surface coal - historic (topo)",
               15: "surface coal - historic (geology)",
               19: "underground coal - current", 20: "underground coal - past",
               22: "underground - abandoned <1977 (partial)",
               23: "underground - abandoned <1977 (known)"}


def station_bbox(pts, margin_deg):
    lats = [p["lat"] for p in pts]
    lons = [p["lon"] for p in pts]
    return (min(lons) - margin_deg, min(lats) - margin_deg,
            max(lons) + margin_deg, max(lats) + margin_deg)


def run_mines(slugs):
    for slug in slugs:
        pts = load_cmd_stations(slug)
        if not pts:
            print("%s: no stations" % slug)
            continue
        # margin must cover the upstream catchments, not just the stations
        bbox = station_bbox(pts, MERIT_MARGIN_KM / 111.0)
        print("\n%s: %d stations, bbox %.3f,%.3f,%.3f,%.3f"
              % (slug, len(pts), *bbox))
        fetch_mines(slug, bbox, os.path.join(MINEDIR, "%s.json" % slug))


# ------------------------------------------------------------- catchment + join

def rasterize_mines(feats, layers, transform, shape):
    """Burn the selected mine layers onto the MERIT grid -> boolean array."""
    from rasterio.features import rasterize
    geoms = []
    for f in feats:
        if f["layer"] not in layers:
            continue
        for p in _rings_to_polygons(f["rings"]):
            geoms.append(p if p.is_valid else p.buffer(0))
    if not geoms:
        return np.zeros(shape, dtype=bool)
    return rasterize(((g, 1) for g in geoms), out_shape=shape,
                     transform=transform, fill=0, dtype="uint8",
                     all_touched=False).astype(bool)


def _grid_lonlat(transform, shape):
    """Cell-centre lon/lat as 1-D axes. Built ONCE per watershed.

    The obvious np.indices(shape) form allocates two full 2-D index arrays per
    call; at a 60 km MERIT radius that is ~2M cells each, times two disc radii
    times 187 stations. Separable axes make the same mask a broadcast.
    """
    lon = transform.c + (np.arange(shape[1]) + 0.5) * transform.a
    lat = transform.f + (np.arange(shape[0]) + 0.5) * transform.e
    return lon, lat


def _disc_mask(grid, lon, lat, radius_km):
    glon, glat = grid
    dx = (glon - lon) * 111.320 * math.cos(math.radians(lat))
    dy = (glat - lat) * 110.574
    return (dy[:, None] ** 2 + dx[None, :] ** 2) <= radius_km * radius_km


def run_catchments(slugs, out_csv):
    """One MERIT tile per WATERSHED, not per station.

    187 stations across 5 small watersheds would be 187 downloads at ~1 min
    each. The stations in a watershed share a grid, so one tile per watershed
    is 5 downloads and every trace runs off the same arrays. This is the only
    departure from catchment_dem.py's per-station flow and it changes nothing
    about the delineation itself.
    """
    from catchment_dem import (init_ee, fetch_merit, rowcol, snap_to_channel,
                               trace_upstream, cell_area_km2)
    ee = init_ee()
    rows = []
    for slug in slugs:
        pts = load_cmd_stations(slug)
        mine_path = os.path.join(MINEDIR, "%s.json" % slug)
        if not pts or not os.path.exists(mine_path):
            print("%s: SKIP (stations=%d, mines=%s)"
                  % (slug, len(pts), os.path.exists(mine_path)))
            continue
        feats = json.load(open(mine_path, encoding="utf-8"))["features"]

        lats = [p["lat"] for p in pts]
        lons = [p["lon"] for p in pts]
        clat, clon = (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2
        half = max((max(lats) - min(lats)) * 110.574,
                   (max(lons) - min(lons)) * 111.320
                   * math.cos(math.radians(clat))) / 2
        radius = min(MERIT_MAX_KM, half + MERIT_MARGIN_KM)
        print("\n%s: %d stations, %d mine polygons, MERIT radius %.0f km"
              % (slug, len(pts), len(feats), radius))

        dir_arr, upa, tr, _ = fetch_merit(ee, clon, clat, radius, verbose=True)
        shape = dir_arr.shape
        burn = {"all": rasterize_mines(feats, set(COAL_LAYERS), tr, shape),
                "surf": rasterize_mines(feats, set(SURFACE_COAL), tr, shape),
                "und": rasterize_mines(feats, set(UNDER_COAL), tr, shape)}
        print("  grid %dx%d | mined cells all=%d surf=%d und=%d"
              % (shape[0], shape[1], burn["all"].sum(),
                 burn["surf"].sum(), burn["und"].sum()))

        grid = _grid_lonlat(tr, shape)
        area_row = np.array([cell_area_km2(tr, la) for la in grid[1]])
        area = np.repeat(area_row[:, None], shape[1], axis=1)

        ok = clipped = 0
        for p in pts:
            r, c = rowcol(tr, p["lon"], p["lat"])
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            r, c, _ = snap_to_channel(upa, r, c)
            mask, edge = trace_upstream(dir_arr, r, c)
            rec = dict(region=slug, pid=p["pid"], lat=p["lat"], lon=p["lon"],
                       catch_km2=float(area[mask].sum()),
                       n_cells=int(mask.sum()), clipped=int(edge))
            if edge:
                clipped += 1
            else:
                ok += 1
            tot = float(area[mask].sum())
            for k, b in burn.items():
                rec["minefrac_" + k] = (float(area[mask & b].sum()) / tot
                                        if tot > 0 else float("nan"))
            for rk in DISC_RADII_KM:
                d = _disc_mask(grid, p["lon"], p["lat"], rk)
                dt = float(area[d].sum())
                rec["minefrac_disc%gkm" % rk] = (float(area[d & burn["all"]].sum())
                                                 / dt if dt > 0 else float("nan"))
            rows.append(rec)
        print("  traced %d stations: %d clean, %d CLIPPED (dropped in analysis)"
              % (ok + clipped, ok, clipped))

    os.makedirs(OUTDIR, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s (%d rows)" % (out_csv, len(rows)))


# ------------------------------------------------------------------ statistics

def _rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return np.asarray(out)


def partial_spearman(x, y, z):
    """Spearman rho of x vs y with z removed, on ranks.

    Residualise rank(x) and rank(y) on rank(z) by least squares, then correlate
    the residuals. This is the rank analogue of a partial correlation and is
    what the pre-registration fixed as the primary statistic.
    """
    rx, ry, rz = _rank(x), _rank(y), _rank(z)
    A = np.column_stack([rz, np.ones(len(rz))])
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    sx, sy = ex.std(), ey.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float((ex * ey).mean() / (sx * sy))


def perm_p_within(x, y, z, regions, observed, n_perm, rng):
    """Shuffle y WITHIN watershed; z travels with the station, not with y.

    This is the null that destroyed the pooled Colorado sulfate claim and that
    Arm B2 passed. Keeping z attached to the station is the point: it asks
    whether the x-y link survives at equal mining extent, not whether the
    triple is jointly random.
    """
    by = {}
    for i, g in enumerate(regions):
        by.setdefault(g, []).append(i)
    hits = 0
    for _ in range(n_perm):
        yp = list(y)
        for ix in by.values():
            sub = [y[i] for i in ix]
            rng.shuffle(sub)
            for i, v in zip(ix, sub):
                yp[i] = v
        r = partial_spearman(x, yp, z)
        if r == r and abs(r) >= abs(observed):
            hits += 1
    return (hits + 1) / (n_perm + 1)


def _per_region(x, y, regions, z=None, minn=5):
    by = {}
    for i, g in enumerate(regions):
        by.setdefault(g, []).append(i)
    out = {}
    for g, ix in by.items():
        if len(ix) < minn:
            continue
        xs, ys = [x[i] for i in ix], [y[i] for i in ix]
        if z is None:
            out[g] = spearman(xs, ys)[0]
        else:
            out[g] = partial_spearman(xs, ys, [z[i] for i in ix])
    return out


def _signs(per):
    v = [s for s in per.values() if s == s]
    return v, bool(v) and (all(s > 0 for s in v) or all(s < 0 for s in v))


# -------------------------------------------------------------------- analysis

def run_analyse(geo_paths, conf_csv, out_txt=None, n_perm=N_PERM,
                ladder_paths=None):
    conf = {}
    with open(conf_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            def f(k):
                try:
                    return float(r[k])
                except (TypeError, ValueError):
                    return float("nan")
            conf[(r["region"], r["pid"])] = dict(
                clipped=int(r["clipped"]), catch_km2=f("catch_km2"),
                **{k: f(k) for k in r if k.startswith("minefrac_")})

    rows = [r for r in load_extracted(geo_paths)
            if r.get("tier") == "cmd" and r.get("radius") == PRIMARY_RADIUS]
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 88)
    say("PHASE CMD2 - MINING-EXTENT CONFOUND TEST (PRE-REGISTERED a452446)")
    say("Covariate: ODNR MinesOfOhio - permit records + historic topo/geology")
    say("maps. Owes NOTHING to satellite reflectance, which is why it was")
    say("chosen: the signal under test is a VEGETATION index.")
    say("CAVEAT (binding): sulfate has NO VNIR absorption. Any association is")
    say("with vegetation / iron precipitate / turbidity that CO-VARIES with it.")
    say("=" * 88)

    # assemble the analysis table
    X, Y, Z, G, dropped, nomine = [], [], [], [], 0, 0
    zdisc = {("minefrac_disc%gkm" % rk): [] for rk in DISC_RADII_KM}
    zsplit = {"minefrac_surf": [], "minefrac_und": []}
    for r in rows:
        c = conf.get((r["region"], r["pid"]))
        v, s = r.get("NDVI_stress_p90", float("nan")), r.get("Sulfate_mgL",
                                                             float("nan"))
        if v != v or s != s:
            continue
        if c is None:
            nomine += 1
            continue
        # A CLIPPED catchment is unusable as a covariate, but the fixed-radius
        # discs around the same station are not - they cannot clip. So the row
        # is kept with a NaN catchment value and the per-covariate NaN filter
        # drops it from the PRIMARY arm only. This matters because the drop is
        # not random: clipping hits large mainstem catchments specifically, so
        # discarding those stations from the disc arms too would narrow the
        # sample for no reason. Counted either way.
        zc = float("nan") if c["clipped"] else c["minefrac_all"]
        if zc != zc:
            dropped += 1
        X.append(v)
        Y.append(s)
        Z.append(zc)
        G.append(r["region"])
        for k in zdisc:
            zdisc[k].append(c.get(k, float("nan")))
        for k in zsplit:                      # catchment-derived -> clips too
            zsplit[k].append(float("nan") if c["clipped"]
                             else c.get(k, float("nan")))

    say("")
    say("--- SAMPLE ---")
    say("  stations with NDVI_stress + sulfate at 30 m : %d"
        % sum(1 for r in rows if r.get("NDVI_stress_p90", float("nan")) ==
              r.get("NDVI_stress_p90", float("nan")) and
              r.get("Sulfate_mgL", float("nan")) == r.get("Sulfate_mgL",
                                                          float("nan"))))
    say("  catchment CLIPPED - dropped from primary arm : %d" % dropped)
    say("  dropped - no catchment record                : %d" % nomine)
    say("  rows carried (disc arms keep the clipped)    : %d" % len(X))
    zok = [v for v in Z if v == v]
    say("  ANALYSED in PRIMARY arm                      : %d" % len(zok))
    if len(zok) < 20:
        say("  TOO FEW to test. Reported as a failure to test, not as a null.")
        if out_txt:
            open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        return
    say("  mined fraction of catchment: min %.3f  median %.3f  max %.3f"
        % (min(zok), sorted(zok)[len(zok) // 2], max(zok)))

    # ---- T0: is the confound even structurally possible? ----
    say("")
    say("--- T0 (REQUIRED GUARD): does mining extent predict the exposure? ---")
    say("  A variable that does not move sulfate CANNOT confound it. If this")
    say("  leg is absent, T1 is UNINFORMATIVE, not supportive.")
    t0 = []
    keep0 = [i for i, v in enumerate(Z) if v == v]
    for name, other in [("mine_frac vs sulfate", Y),
                        ("mine_frac vs NDVI_stress", X)]:
        a = [Z[i] for i in keep0]
        b = [other[i] for i in keep0]
        g0 = [G[i] for i in keep0]
        rho, n = spearman(a, b)
        per = _per_region(a, b, g0)
        sg, cons = _signs(per)
        t0.append((name, rho, n, cons))
        say("  %-26s rho=%+.3f  n=%d  btw%%=%.0f  %s"
            % (name, rho, n, 100 * variance_split(b, g0),
               "CONSISTENT" if cons else "signs disagree"))
        say("      per-watershed: %s"
            % " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(per.items())))
    leg_sulfate = abs(t0[0][1])
    confound_possible = leg_sulfate >= 0.15
    say("  => mine_frac->sulfate leg |rho|=%.3f : %s"
        % (leg_sulfate,
           "present, confound is structurally possible" if confound_possible
           else "ABSENT - the confound cannot operate; T1 is uninformative"))

    # ---- T1: primary ----
    say("")
    say("--- T1 (PRIMARY): NDVI_stress vs sulfate, conditioning on mine extent ---")
    raw, n_raw = spearman(X, Y)
    per_raw = _per_region(X, Y, G)
    _, cons_raw = _signs(per_raw)
    say("  raw     rho=%+.3f  n=%d   per-watershed: %s  %s"
        % (raw, n_raw,
           " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(per_raw.items())),
           "CONSISTENT" if cons_raw else "signs disagree"))

    results = []
    for label, zz in ([("catchment (PRIMARY)", Z),
                       ("catchment surface-only", zsplit["minefrac_surf"]),
                       ("catchment underground", zsplit["minefrac_und"])]
                      + [("disc %s" % k.split("_")[-1], zdisc[k])
                         for k in sorted(zdisc)]):
        zc = [v for v in zz]
        if any(v != v for v in zc):
            keep = [i for i, v in enumerate(zc) if v == v]
            xs = [X[i] for i in keep]
            ys = [Y[i] for i in keep]
            zs = [zc[i] for i in keep]
            gs = [G[i] for i in keep]
        else:
            xs, ys, zs, gs = X, Y, zc, G
        pr = partial_spearman(xs, ys, zs)
        p = perm_p_within(xs, ys, zs, gs, pr, n_perm, rng)
        per = _per_region(xs, ys, gs, z=zs)
        sg, cons = _signs(per)
        # attenuation must be measured against the RAW rho on the SAME rows.
        # Comparing a subsample's partial against the full-sample raw would
        # charge the covariate for sample loss it did not cause.
        raw_sub, _ = spearman(xs, ys)
        atten = ((abs(raw_sub) - abs(pr)) / abs(raw_sub)
                 if raw_sub else float("nan"))
        results.append(dict(label=label, rho=pr, p=p, n=len(xs), cons=cons,
                            per=per, atten=atten, raw=raw_sub))
        say("  %-24s partial rho=%+.3f  n=%3d  perm_p=%.4f  (raw %+.3f, "
            "atten %+.0f%%)  %s"
            % (label, pr, len(xs), p, raw_sub, 100 * atten,
               "CONSISTENT" if cons else "signs disagree"))
        say("      per-watershed: %s"
            % " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(per.items())))

    # ---- T2: far-field ladder ----
    say("")
    say("--- T2 (SECONDARY): far-field radius ladder, independent machinery ---")
    say("  CMD1 amendment 2 registered the reading in advance: |rho| RISING as")
    say("  radius grows => catchment-scale land cover, not the seep.")
    if ladder_paths:
        lrows = [r for r in load_extracted(ladder_paths) if r.get("tier") == "cmd"]
        seen = sorted({r.get("radius") for r in lrows if r.get("radius")})
        for rad in seen:
            xs, ys, gs = [], [], []
            for r in lrows:
                if r.get("radius") != rad:
                    continue
                v = r.get("NDVI_stress_p90", float("nan"))
                s = r.get("Sulfate_mgL", float("nan"))
                if v == v and s == s:
                    xs.append(v)
                    ys.append(s)
                    gs.append(r["region"])
            if len(xs) < 20:
                continue
            rho, n = spearman(xs, ys)
            per = _per_region(xs, ys, gs)
            _, cons = _signs(per)
            npx = [r.get("n_px") for r in lrows
                   if r.get("radius") == rad and r.get("n_px") == r.get("n_px")]
            say("  r=%6.0fm  rho=%+.3f  n=%3d  median n_px=%s  %s"
                % (rad, rho, n,
                   "%.0f" % sorted(npx)[len(npx) // 2] if npx else "-",
                   "CONSISTENT" if cons else "signs disagree"))
            say("      per-watershed: %s"
                % " ".join("%s%+.2f" % (g[:4], v) for g, v in sorted(per.items())))
    else:
        say("  (no far-field extraction supplied - run cmd_detect.py --extract")
        say("   --season leafoff --radii 500,1000 and pass --ladder)")

    # ---- verdict ----
    prim = results[0]
    say("")
    say("--- VERDICT (pre-registered, section 5) ---")
    if not confound_possible:
        say("  CONFOUND NOT OPERATIVE - mine extent does not predict sulfate")
        say("  (|rho|=%.3f < 0.15), so it cannot be the confounder. T1 below is")
        say("  reported but is UNINFORMATIVE about H-CONF, per the T0 guard." % ())
    if abs(prim["rho"]) >= RHO_REJECT and prim["p"] < 0.05 and \
            (prim["rho"] < 0) == (raw < 0):
        say("  CONFOUND REJECTED - partial |rho|=%.3f >= %.2f, p=%.4f < 0.05,"
            % (abs(prim["rho"]), RHO_REJECT, prim["p"]))
        say("  sign retained. At EQUAL mining extent, sulfate still tracks")
        say("  vegetation. Land cover alone cannot produce that.")
    elif abs(prim["rho"]) < RHO_SUPPORT or prim["p"] >= 0.05:
        say("  CONFOUND SUPPORTED - partial |rho|=%.3f, p=%.4f."
            % (abs(prim["rho"]), prim["p"]))
        say("  The CMD vegetation claim is WITHDRAWN, per the registered rule.")
        say("  Over-control is an alternative reading and is NOTED, but the")
        say("  pre-registration forbids using it to keep the claim alive.")
    else:
        say("  PARTIAL - partial |rho|=%.3f (%.0f%% attenuation), p=%.4f."
            % (abs(prim["rho"]), 100 * prim["atten"], prim["p"]))
        say("  Materially attenuated. The claim is WEAKENED, not withdrawn,")
        say("  and must be reported as weakened wherever it is cited.")
    say("")
    say("  Sign consistency remains the headline check, as at every radius:")
    say("  raw %s / partial %s"
        % ("CONSISTENT" if cons_raw else "signs disagree",
           "CONSISTENT" if prim["cons"] else "signs disagree"))
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mines", action="store_true")
    ap.add_argument("--catchments", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--regions", default="")
    ap.add_argument("--inputs", default="")
    ap.add_argument("--ladder", default="")
    ap.add_argument("--conf", default=os.path.join(OUTDIR, "cmdconf.csv"))
    ap.add_argument("--perms", type=int, default=N_PERM)
    ap.add_argument("--out")
    a = ap.parse_args()
    slugs = [s for s in a.regions.split(",") if s] or list(CMD_REGIONS)
    if a.mines:
        run_mines(slugs)
    elif a.catchments:
        run_catchments(slugs, a.conf)
    elif a.analyse:
        paths = ([p for p in a.inputs.split(",") if p] or
                 glob.glob(os.path.join(OUTDIR, "cmdgeo_l8_*.csv")))
        lad = ([p for p in a.ladder.split(",") if p] or
               glob.glob(os.path.join(OUTDIR, "cmdfar_l8_*.csv")))
        run_analyse(paths, a.conf, a.out, a.perms, lad or None)
    else:
        ap.print_help()
