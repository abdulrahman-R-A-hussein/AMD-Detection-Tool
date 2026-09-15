"""Blind-search test - CLI for validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md.

The science lives in src/amdtool/blind_search.py; this file is orchestration,
disk I/O and the text report.

    # 1. score the landscape and the registered stations (Earth Engine, hours)
    python python/blind_search.py --extract
    python python/blind_search.py --extract --snow-masked       # sensitivity

    # 2. the registered test - refuses to run unless the registration is
    #    committed and the site list still matches its registered SHA-256
    python python/blind_search.py --analyse \
        --registration validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md \
        --out validation/report_blind_search_<date>.txt

    # 3. the field sampling frame (after the verdict)
    python python/blind_search.py --frame \
        --registration validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md \
        --out validation/blind_search_field_frame_<date>.csv

A district that fails extraction writes <file>.FAILED with the error; the
analysis then treats it as FAILED exactly as the registration specifies.
"""

import argparse
import csv
import hashlib
import io
import logging
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from amdtool import blind_search as bs        # noqa: E402
from amdtool.regions import region_bbox       # noqa: E402

SITES_CSV = os.path.join(ROOT, "validation", "blind_search_sites_2026-09-14.csv")
MATCHED = os.path.join(ROOT, "data", "matched")
CHEM = os.path.join(ROOT, "data", "chemistry")
DATA = os.path.join(ROOT, "data")

NUMERIC = {"lat", "lon", "radius", "n_scenes",
           "FerricIron1_p90", "FerricIron1_mean", "FerricIron1_count",
           "NDVI_stress_p90", "NDVI_stress_mean", "NDVI_stress_count", "nlcd"}


def out_path(district, snow_masked):
    return os.path.join(MATCHED, "blindsearch_s2_%s%s.csv"
                        % (district, "_snowmask" if snow_masked else ""))


# ---------------------------------------------------------------- guards

def _git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                          text=True).stdout.strip()


def check_registration(reg_path):
    """Refuse to analyse unless the registration is committed and unchanged."""
    if not os.path.isfile(reg_path):
        raise SystemExit("registration not found: %s" % reg_path)
    text = io.open(reg_path, encoding="utf-8").read()
    m = re.search(r"SHA-256 `([0-9a-f]{64})`", text)
    if not m:
        raise SystemExit("could not find the registered site-list SHA-256 in %s" % reg_path)
    with open(SITES_CSV, "rb") as fh:
        got = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    if got != m.group(1):
        raise SystemExit("site list %s does not match its registered SHA-256\n"
                         "  registered %s\n  found      %s"
                         % (SITES_CSV, m.group(1), got))
    rel = os.path.relpath(reg_path, ROOT).replace(os.sep, "/")
    reg_commit = _git("log", "--diff-filter=A", "--format=%H", "--", rel).splitlines()
    if not reg_commit:
        raise SystemExit("registration %s is not committed - commit it before "
                         "analysing" % rel)
    first = reg_commit[-1]
    return first, m.group(1)


# ---------------------------------------------------------------- extract

def stations_by_district(sites):
    rows = {}
    with io.open(SITES_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["district"], {})[r["station_id"]] = {
                "pid": r["station_id"], "lat": float(r["lat"]), "lon": float(r["lon"])}
    return {d: list(v.values()) for d, v in rows.items()}


def run_extract(districts, snow_masked, force):
    from ee_auth import init_ee
    ee = init_ee()
    sites = bs.load_sites(SITES_CSV)
    stations = stations_by_district(sites)
    os.makedirs(MATCHED, exist_ok=True)
    for d in districts:
        path = out_path(d, snow_masked)
        if os.path.isfile(path) and not force:
            print("%s: exists, skipping (use --force)" % d)
            continue
        failed = path + ".FAILED"
        if os.path.isfile(failed):
            os.remove(failed)
        try:
            bbox = region_bbox(d, DATA)
            n_scenes, land, got_land, got_st = bs.extract_district(
                ee, bbox, stations[d], snow_masked=snow_masked)
            print("\n%s: %d scenes, %d landscape points, %d stations"
                  % (d, n_scenes, len(land), len(stations[d])))
            if n_scenes < 3:
                raise RuntimeError("only %d scenes" % n_scenes)
            nlcd = {} if snow_masked else bs.nlcd_landcover_at(ee, land)
            rows = []
            for tier, pts, got in (("landscape", land, got_land),
                                   ("station", stations[d], got_st)):
                for p in pts:
                    v = got.get(p["pid"], {})
                    row = dict(region=d, tier=tier, pid=p["pid"], lat=p["lat"],
                               lon=p["lon"], radius=bs.RADIUS_M, sensor="S2",
                               composite="snowmask" if snow_masked else "primary",
                               n_scenes=n_scenes)
                    for band in (bs.SCORE_BAND, bs.BASELINE_BAND):
                        for s in ("p90", "mean", "count"):
                            row["%s_%s" % (band, s)] = v.get("%s_%s" % (band, s))
                    if tier == "landscape" and not snow_masked:
                        row["nlcd"] = nlcd.get(p["pid"])
                    rows.append(row)
            keys = sorted({k for r in rows for k in r})
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=keys)
                w.writeheader()
                w.writerows(rows)
            print("  -> %s (%d rows)" % (os.path.relpath(path, ROOT), len(rows)))
        except Exception as exc:                            # noqa: BLE001
            with open(failed, "w", encoding="utf-8") as fh:
                fh.write("%s: %s\n" % (type(exc).__name__, exc))
            print("%s: FAILED - %s" % (d, exc))


# ---------------------------------------------------------------- analyse

def load_district_rows(districts, snow_masked=False):
    out, failed = {}, []
    for d in districts:
        path = out_path(d, snow_masked)
        if not os.path.isfile(path):
            failed.append(d)
            continue
        land, st = [], {}
        with io.open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for k in NUMERIC & set(r):
                    r[k] = float(r[k]) if r[k] not in ("", "None") else float("nan")
                if r["tier"] == "landscape":
                    land.append(r)
                else:
                    st[r["pid"]] = r
        out[d] = {"landscape": land, "stations": st}
    return out, failed


def fmt_ci(ci):
    return "[%.3f, %.3f]" % ci


def run_analyse(reg_path, out_txt):
    reg_commit, sha = check_registration(reg_path)
    sites = bs.load_sites(SITES_CSV)
    districts = sorted({s.district for s in sites})
    rows, failed = load_district_rows(districts)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 92)
    say("BLIND-SEARCH TEST - pre-registered (%s)" % os.path.relpath(reg_path, ROOT))
    say("registration first committed in %s; site list SHA-256 verified %s" % (reg_commit[:7], sha[:12]))
    say("score FerricIron1 p90 @60 m (S2, 20 m) | baseline -NDVI mean | primary budget 5%")
    say("=" * 92)
    if failed:
        say("FAILED districts (sites removed per registration section 11): %s" % ", ".join(failed))

    say("")
    say("--- LANDSCAPE SAMPLE AND CUTOFFS ---")
    say("  %-16s %6s %7s  %-26s  %-26s" % ("district", "valid", "dropped", "FerricIron1 cut 1/5/10%", "-NDVI cut 1/5/10%"))
    for d in sorted(rows):
        land = rows[d]["landscape"]
        nv = bs.landscape_cutoff(land, bs.primary_score, 0.05)[1]
        pc = [bs.landscape_cutoff(land, bs.primary_score, b)[0] for b in (0.01, 0.05, 0.10)]
        bc = [bs.landscape_cutoff(land, bs.baseline_score, b)[0] for b in (0.01, 0.05, 0.10)]
        flag = "  <- below %d valid" % bs.MIN_VALID_LANDSCAPE if nv < bs.MIN_VALID_LANDSCAPE else ""
        say("  %-16s %6d %7d  %7.4f %7.4f %7.4f   %7.4f %7.4f %7.4f%s"
            % (d, nv, len(land) - nv, pc[0], pc[1], pc[2], bc[0], bc[1], bc[2], flag))

    def block(title, **kw):
        res = {h: bs.evaluate(kw.get("sites", sites), rows, kw.get("budget", bs.PRIMARY_BUDGET), h,
                              site_set=kw.get("site_set", "primary"),
                              how=kw.get("how", "max"),
                              unscoreable=kw.get("unscoreable", "not_flagged"))
               for h in bs.HYPOTHESES}
        say("")
        say("--- %s ---" % title)
        for h in bs.HYPOTHESES:
            r = res[h]
            say("  %-6s n=%-3d flagged=%-3d recall=%.3f %s  binomial p=%.4f | baseline flagged=%d  b=%d c=%d  McNemar p=%.4f  unscoreable=%d"
                % (h, r.n, r.k, r.recall, fmt_ci(r.ci), r.p_binomial, r.k_baseline, r.b, r.c, r.p_mcnemar, r.unscoreable))
        return res

    primary = block("PRIMARY - 5% budget, sites with >=1 mine-type station, max score, unscoreable = not flagged")
    bs.apply_verdicts(primary)
    say("")
    say("--- VERDICTS (registration section 7) ---")
    for h in bs.HYPOTHESES:
        r = primary[h]
        lvl = "%.3f" % r.holm_level if r.holm_level is not None else "not reached"
        say("  %-6s Holm level %-11s binomial rejected=%-5s -> %s" % (h, lvl, r.rejected, r.verdict))
        say("         power at this n and level: %s" % "  ".join(
            "r=%.2f:%.2f" % (rec, pw) for rec, pw in sorted(r.power_at_level.items())))
        if r.failed_districts:
            say("         reduced by FAILED districts: %s" % ", ".join(r.failed_districts))
        for d, v in sorted(r.per_district.items()):
            say("         %-16s n=%-3d flagged=%-3d recall=%.3f %s  baseline=%d"
                % (d, v["n"], v["k"], v["recall"], fmt_ci(v["ci"]), v["k_baseline"]))

    say("")
    say("=" * 92)
    say("SECONDARY AND SENSITIVITY - reported, never verdicts")
    say("=" * 92)
    for b in bs.SECONDARY_BUDGETS:
        block("budget %.0f%%" % (100 * b), budget=b)
    block("all sites including spring-only", site_set="all")
    block("median site score", how="median")
    block("unscoreable sites excluded", unscoreable="exclude")
    for link in (100.0, 500.0):
        block("link distance %.0f m - the same registered stations, re-clustered" % link,
              sites=bs.relink_sites(sites, link))
    say("")
    say("--- station-level recall (5%) ---")
    for h in bs.HYPOTHESES:
        k, n = bs.station_recall(sites, rows, bs.PRIMARY_BUDGET, h)
        say("  %-6s stations flagged %d / %d  recall=%.3f" % (h, k, n, k / n if n else float("nan")))

    say("")
    say("--- NLCD barren (class 31) share of flagged landscape points (5%) ---")
    for d in sorted(rows):
        land = rows[d]["landscape"]
        cut = bs.landscape_cutoff(land, bs.primary_score, bs.PRIMARY_BUDGET)[0]
        fl = [r for r in land if bs.is_flagged(bs.primary_score(r), cut)]
        allv = [r for r in land if r.get("nlcd") == r.get("nlcd")]
        share = sum(1 for r in fl if r.get("nlcd") == bs.NLCD_BARREN) / len(fl) if fl else float("nan")
        base = sum(1 for r in allv if r.get("nlcd") == bs.NLCD_BARREN) / len(allv) if allv else float("nan")
        say("  %-16s flagged=%-4d barren share=%.3f  (landscape overall %.3f)" % (d, len(fl), share, base))

    snow, snow_failed = load_district_rows(districts, snow_masked=True)
    say("")
    if snow and not snow_failed:
        say("--- snow-masked composite (SCL 11) ---")
        for h in bs.HYPOTHESES:
            r = bs.evaluate(sites, snow, bs.PRIMARY_BUDGET, h)
            say("  %-6s n=%-3d flagged=%-3d recall=%.3f %s  binomial p=%.4f" % (h, r.n, r.k, r.recall, fmt_ci(r.ci), r.p_binomial))
    else:
        say("--- snow-masked composite: not extracted for all districts (run --extract --snow-masked) ---")

    say("")
    say("--- TERTIARY T-86 - in-sample for index choice; NOT evidence of discovery ---")
    t = bs.evaluate(sites, rows, bs.PRIMARY_BUDGET, bs.TERTIARY)
    say("  T-86   n=%-3d flagged=%-3d recall=%.3f %s  binomial p=%.4f  baseline=%d"
        % (t.n, t.k, t.recall, fmt_ci(t.ci), t.p_binomial, t.k_baseline))

    say("")
    say("Recall on KNOWN sources only. Precision on unrecorded ground cannot be")
    say("measured from the archive, and agency-monitored sources are a biased sample.")
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


# ---------------------------------------------------------------- frame

def run_frame(reg_path, out_csv):
    check_registration(reg_path)
    sites = bs.load_sites(SITES_CSV)
    districts = sorted({s.district for s in sites})
    rows, failed = load_district_rows(districts)
    wqp = {}
    for d in districts:
        path = os.path.join(CHEM, d, "stations.csv")
        with io.open(path, encoding="utf-8") as fh:
            wqp[d] = [{"lat": float(r["lat"]), "lon": float(r["lon"])}
                      for r in csv.DictReader(fh) if r.get("lat") and r.get("lon")]
    primary = {h: bs.evaluate(sites, rows, bs.PRIMARY_BUDGET, h) for h in bs.HYPOTHESES}
    bs.apply_verdicts(primary)
    notice = bs.frame_notice(primary)
    drawn, counts = bs.sampling_frame(rows, wqp)
    print(notice)
    print("cluster counts per district: %s" % counts)
    if failed:
        print("FAILED districts, excluded from the frame: %s" % ", ".join(failed))
    keys = ["district", "frame_id", "n_points", "lat", "lon", "max_score"]
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        fh.write("# A SAMPLING FRAME, NOT A LIST OF DETECTIONS - see the blind-search report verdicts.\n")
        fh.write("# %s\n" % notice)
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(drawn)
    print("-> %s (%d clusters)" % (out_csv, len(drawn)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract", action="store_true")
    g.add_argument("--analyse", action="store_true")
    g.add_argument("--frame", action="store_true")
    ap.add_argument("--districts", default="", help="comma-separated slugs; default all seven")
    ap.add_argument("--snow-masked", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--registration", default=os.path.join(
        ROOT, "validation", "BLIND_SEARCH_PREREGISTRATION_2026-09-14.md"))
    ap.add_argument("--out")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="      %(message)s")

    if a.extract:
        all_d = sorted({s.district for s in bs.load_sites(SITES_CSV)})
        run_extract([d for d in a.districts.split(",") if d] or all_d,
                    a.snow_masked, a.force)
    elif a.analyse:
        run_analyse(a.registration, a.out)
    else:
        if not a.out:
            ap.error("--frame needs --out")
        run_frame(a.registration, a.out)


if __name__ == "__main__":
    main()
