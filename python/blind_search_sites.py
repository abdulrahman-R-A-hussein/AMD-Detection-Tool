"""Fix the blind-search sample BEFORE any landscape data exists.

Part of the blind-search pre-registration
(validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md). This script reads only
station METADATA - locations and site types from data/chemistry/<slug>/
stations.csv, plus the ids of the 86 B2 targets. It reads no index value and no
imagery, so running it cannot peek at the outcome.

It writes the site list the registration commits to, and prints the exact
binomial power table the registration quotes.

Definitions, each fixed here rather than chosen later:

  source station   fetch_wqp.site_category(site_type) == "source"
                   (mine discharge / adit / tailings / waste rock / tunnel /
                   spring), with a latitude and longitude. This is B2's
                   definition, kept for comparability with the 86 targets.
  mine-type        a source station whose site_type is NOT "Spring".
  site             single-linkage cluster of source stations within 250 m.
  PRIMARY sites    sites containing >= 1 mine-type station. Spring-only sites
                   are a SENSITIVITY set. Decided from site-type metadata before
                   any score exists: 43 of the 93 H-BS2 sites were spring-only,
                   so keeping them primary would have made nearly half of that
                   test a measure of finding natural springs, not mine sources.
  H-BS1            Alma, Creede, Lake City - districts never used to choose the
                   index. A station is EXCLUDED if it lies inside any analysed
                   district's box (the Alma and Leadville boxes overlap) or
                   within 250 m of any of the 86 B2 targets.
  H-BS2            source stations in Silverton, Ouray, Leadville, Central City
                   that are NOT among the 86 B2 targets and NOT within 250 m of
                   any of them.
  T-86             the 86 B2 targets themselves - in-sample for index choice,
                   reported as a labelled tertiary result only.

A station reached from two district files is kept once, under the first district
in DISTRICT_ORDER.

Usage:
    python python/blind_search_sites.py > validation/report_blind_search_sites_2026-09-14.txt
"""

import csv
import hashlib
import io
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_wqp import REGIONS, site_category   # noqa: E402
import seep_detect as sd                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "validation", "blind_search_sites_2026-09-14.csv")

LINK_M = 250.0
ANALYSED = ["silverton_co", "ouray_co", "leadville_co", "central_city_co"]
NEW = ["alma_co", "creede_co", "lake_city_co"]
DISTRICT_ORDER = ANALYSED + NEW
NAME = {"silverton_co": "Silverton, CO", "ouray_co": "Ouray, CO",
        "leadville_co": "Leadville, CO", "central_city_co": "Central City, CO",
        "alma_co": "Alma, CO", "creede_co": "Creede, CO",
        "lake_city_co": "Lake City, CO"}

BUDGETS = (0.01, 0.05, 0.10)
TRUE_RECALL = (0.10, 0.15, 0.20, 0.30)
SPRING = "Spring"


def haversine_m(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * 6371000.0 * math.asin(math.sqrt(h))


def in_box(lat, lon, slug):
    lat_lo, lon_lo, lat_hi, lon_hi = REGIONS[NAME[slug]][:4]
    return lat_lo <= lat <= lat_hi and lon_lo <= lon <= lon_hi


def source_stations(slug):
    path = os.path.join(ROOT, "data", "chemistry", slug, "stations.csv")
    out = []
    with io.open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if site_category(r.get("site_type", "")) != "source":
                continue
            if not r.get("lat") or not r.get("lon"):
                continue
            out.append({"station_id": r["station_id"],
                        "station_name": r.get("station_name", ""),
                        "site_type": r.get("site_type", ""),
                        "lat": float(r["lat"]), "lon": float(r["lon"])})
    return out


def cluster(stations):
    """Single-linkage at LINK_M. Deterministic: stations sorted first, site ids
    assigned in order of each cluster's first member."""
    st = sorted(stations, key=lambda s: (s["lat"], s["lon"], s["station_id"]))
    parent = list(range(len(st)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(st)):
        for j in range(i + 1, len(st)):
            if haversine_m((st[i]["lat"], st[i]["lon"]),
                           (st[j]["lat"], st[j]["lon"])) <= LINK_M:
                parent[find(i)] = find(j)
    order, labels = {}, []
    for i in range(len(st)):
        root = find(i)
        if root not in order:
            order[root] = len(order)
        labels.append(order[root])
    return st, labels, len(order)


def binom_sf_ge(k, n, p):
    """P(X >= k), X ~ Binomial(n, p). Exact, standard library only."""
    return sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x)
               for x in range(k, n + 1))


def critical_k(n, budget, alpha):
    for k in range(n + 1):
        if binom_sf_ge(k, n, budget) <= alpha:
            return k
    return None


def add_sites(rows, hyp, slug, stations, prefix):
    st, labels, n_sites = cluster(stations)
    sizes, has_mine = {}, {}
    for s, lab in zip(st, labels):
        sizes[lab] = sizes.get(lab, 0) + 1
        has_mine[lab] = has_mine.get(lab, False) or s["site_type"] != SPRING
    for s, lab in zip(st, labels):
        rows.append({"hypothesis": hyp, "district": slug,
                     "site_id": "%s_%s%03d" % (slug, prefix, lab + 1),
                     "n_stations_in_site": sizes[lab],
                     "site_has_mine_station": int(has_mine[lab]), **s})
    return n_sites, sum(1 for v in has_mine.values() if v)


def power_block(title, totals):
    print("\n" + title)
    for hyp in ("H-BS1", "H-BS2"):
        n = totals[hyp]
        for budget in BUDGETS:
            for alpha in (0.025, 0.05):
                k = critical_k(n, budget, alpha)
                pw = "  ".join("r=%.2f:%.2f" % (r, binom_sf_ge(k, n, r))
                               for r in TRUE_RECALL)
                print("  %-6s n=%-3d budget=%.2f alpha=%.3f  reject if >=%-3d sites flagged   %s"
                      % (hyp, n, budget, alpha, k, pw))


def main():
    targets = []
    for slug in ANALYSED:
        t, _ = sd.load_region_points(slug)
        targets.extend(t)
    used_ids = {t["pid"] for t in targets}
    used_xy = [(t["lat"], t["lon"]) for t in targets]
    assert len(used_ids) == 86, "expected the 86 registered B2 targets"

    seen, rows, summary = set(), [], []
    for slug in DISTRICT_ORDER:
        stations = source_stations(slug)
        n_dup = n_used = n_near = n_box = 0
        keep = []
        for s in stations:
            if s["station_id"] in seen:
                n_dup += 1
                continue
            seen.add(s["station_id"])
            if slug in ANALYSED and s["station_id"] in used_ids:
                n_used += 1
                continue
            if slug in NEW and any(in_box(s["lat"], s["lon"], a) for a in ANALYSED):
                n_box += 1
                continue
            if any(haversine_m((s["lat"], s["lon"]), u) <= LINK_M for u in used_xy):
                n_near += 1
                continue
            keep.append(s)
        hyp = "H-BS1" if slug in NEW else "H-BS2"
        n_sites, n_mine_sites = add_sites(rows, hyp, slug, keep, "S")
        summary.append((hyp, slug, len(stations), n_dup, n_used, n_box,
                        n_near, len(keep), n_sites, n_mine_sites))

    for slug in ANALYSED:
        sub = [{"station_id": t["pid"], "station_name": t.get("name", ""),
                "site_type": t.get("site_type", ""),
                "lat": t["lat"], "lon": t["lon"]}
               for t in targets if t["region"] == slug]
        n_sites, n_mine_sites = add_sites(rows, "T-86", slug, sub, "T")
        summary.append(("T-86", slug, len(sub), 0, 0, 0, 0, len(sub),
                        n_sites, n_mine_sites))

    cols = ["hypothesis", "district", "site_id", "n_stations_in_site",
            "site_has_mine_station", "station_id", "station_name",
            "site_type", "lat", "lon"]
    rows.sort(key=lambda r: (r["hypothesis"], r["district"], r["site_id"],
                             r["station_id"]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r[c] for c in cols})
    data = buf.getvalue().encode("utf-8")
    with open(OUT, "wb") as fh:
        fh.write(data)

    print("BLIND-SEARCH SAMPLE - fixed from station metadata only (no index values read)")
    print("link distance %.0f m; B2 targets n=%d\n" % (LINK_M, len(used_ids)))
    print("  hyp    district          source  dup  used  in-analysed-box  <250m-of-target  kept  SITES  PRIMARY(mine)")
    tot_all, tot_primary = {}, {}
    for hyp, slug, n, dup, used, box, near, kept, sites, mine_sites in summary:
        print("  %-6s %-17s %6d %4d %5d %16d %16d %5d %6d %14d"
              % (hyp, slug, n, dup, used, box, near, kept, sites, mine_sites))
        tot_all[hyp] = tot_all.get(hyp, 0) + sites
        tot_primary[hyp] = tot_primary.get(hyp, 0) + mine_sites
    print("\n  PRIMARY sites (>=1 mine-type station): "
          + "   ".join("%s=%d" % kv for kv in sorted(tot_primary.items())))
    print("  SENSITIVITY sites (incl. spring-only): "
          + "   ".join("%s=%d" % kv for kv in sorted(tot_all.items())))

    print("\nEXACT ONE-SIDED BINOMIAL POWER - is recall above the flagged-area budget?")
    print("Holm over the two co-primary hypotheses: the smaller p is tested at "
          "0.025, the other at 0.05.")
    power_block("PRIMARY - sites with >= 1 mine-type station", tot_primary)
    power_block("SENSITIVITY - all sites, including spring-only", tot_all)

    print("\nsite list -> %s" % os.path.relpath(OUT, ROOT))
    print("rows=%d  sha256=%s" % (len(rows), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
