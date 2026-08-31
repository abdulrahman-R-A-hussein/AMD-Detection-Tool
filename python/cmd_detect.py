"""Phase CMD1 - neutral-pH COAL mine drainage, Ohio Appalachian basin.

READ validation/CMD1_PREREGISTRATION_2026-08-16.md FIRST (committed before any
Ohio imagery was extracted).

WHY THIS IS A DIFFERENT PROBLEM. Everything validated so far is ACID metal-mine
drainage in Colorado, where low pH is itself diagnostic. Here alkaline
overburden buffers the acid: median pH is 7.46-7.72 across all five watersheds
while sulfate stays elevated. Contamination is HIDDEN UNDER NEUTRAL pH, so any
method keyed on acidity is blind - including this project's own B2d "clean
water" definition, which would file a 500 mg/L-sulfate neutral CMD stream as
clean.

DESIGN CHANGE FORCED BY THE DATA: Ohio has 1 mine-discharge source point vs
Colorado's 86, so the target-vs-control design does not transfer. This is a
DOSE-RESPONSE design over in-stream stations - no class balance needed, and it
is the design that produced Colorado's robust result.

WORDING CONSTRAINT: sulfate has no VNIR absorption. Nothing here may be reported
as optical sulfate detection. Any association is with iron precipitate,
turbidity, vegetation or colour that CO-VARIES with sulfate.

    python cmd_detect.py --extract     # VPCA venv (needs ee)
    python cmd_detect.py --analyse     # repo venv
"""

import argparse
import csv
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seep_detect import (OUTDIR, SEED, PRIMARY_RADIUS, INDEX_BANDS,
                         MIN_SCENES, region_geometry, l8_composite,
                         index_image, extract_buffers, load_extracted,
                         spearman, variance_split, benjamini_hochberg)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CMD_REGIONS = {
    "monday_creek_oh":  "Monday Creek, OH",
    "sunday_creek_oh":  "Sunday Creek, OH",
    "raccoon_creek_oh": "Raccoon Creek, OH",
    "huff_run_oh":      "Huff Run, OH",
    "leading_creek_oh": "Leading Creek, OH",
}

# Published thresholds, pre-registered. pH deliberately NOT used - that is the
# entire point of this phase.
SO4_DIRTY, SO4_CLEAN = 250.0, 25.0      # EPA secondary MCL / Appalachian background
COND_DIRTY, COND_CLEAN = 500.0, 300.0   # USEPA 2011 Appalachian benchmark
CANOPY_NDVI_LIMIT = 0.6                 # above this, a null is uninterpretable

ANALYTES = ["Sulfate_mgL", "SpecificConductance", "Iron_mgL_any", "pH"]

# Cap on scenes entering the median. The recurring "User memory limit exceeded"
# is about compute-GRAPH size: a median over hundreds of scenes, each with
# add_indices mapped onto it, is too large to BUILD, so no downstream tiling or
# batch-shrinking can rescue it. Capping at the N least-cloudy scenes is
# deterministic, gives every watershed the same compositing depth, and caps the
# graph directly. This is the fix that finally made Silverton S2 complete after
# four failures; applied here to Landsat for the same reason.
L8_MAX_SCENES = 120


def l8_composite_season(ee, region, season="leafoff", max_scenes=L8_MAX_SCENES):
    """Landsat composite for a named season, with snow masked and scenes capped.

    season="leafoff" -> Nov-Mar. That range WRAPS the year boundary, so it needs
    an Or of two calendarRange filters; calendarRange(11, 3) is empty, not
    inclusive, and would silently return nothing.

    SNOW MASKING is required for winter imagery and is not in the standard
    process_landsat() path: QA_PIXEL bit 5 is snow/ice. Snow is bright and
    seasonal, so leaving it in would create a season-dependent artifact that
    could masquerade as either signal or canopy relief - registered in
    CMD1 amendment 1 before this was run.
    """
    from gee_classify import process_landsat, add_indices, START, END

    if season == "leafoff":
        mfilter = ee.Filter.Or(ee.Filter.calendarRange(11, 12, "month"),
                               ee.Filter.calendarRange(1, 3, "month"))
    else:
        mfilter = ee.Filter.calendarRange(5, 7, "month")

    def prep(img):
        snow = img.select("QA_PIXEL").bitwiseAnd(1 << 5).eq(0)
        return add_indices(ee, process_landsat(ee, img).updateMask(snow))

    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .filterBounds(region).filterDate(START, END).filter(mfilter)
           .sort("CLOUD_COVER").limit(max_scenes).map(prep))
    return col.median().clip(region), int(col.size().getInfo())


def load_cmd_stations(slug):
    from watershed_nap import load_station_chemistry
    chem_dir = os.path.join(ROOT, "data", "chemistry", slug)
    chem = load_station_chemistry(chem_dir, 0)
    out = []
    with open(os.path.join(chem_dir, "stations.csv"), encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            c = chem.get(s["station_id"])
            if not c or not s.get("lat") or not s.get("lon"):
                continue
            if all(c.get(a) is None for a in ("Sulfate_mgL", "SpecificConductance")):
                continue
            rec = dict(c)
            rec.update(pid=s["station_id"], region=slug,
                       lat=float(s["lat"]), lon=float(s["lon"]))
            out.append(rec)
    return out


def run_extract(slugs, out_csv, season="leafon", radii=None):
    from gee_classify import init_ee
    ee = init_ee()
    rows = []
    for slug in slugs:
        region = region_geometry(ee, CMD_REGIONS[slug])
        pts = load_cmd_stations(slug)
        if not pts:
            print("%s: no stations with sulfate/conductance" % slug)
            continue
        comp, n_scenes = (l8_composite(ee, region) if season == "leafon"
                          else l8_composite_season(ee, region, season))
        print("\n%s: %d stations, %d scenes" % (slug, len(pts), n_scenes))
        if n_scenes < MIN_SCENES:
            print("  SKIP - too few scenes")
            continue
        img = index_image(ee, comp)
        for radius in (radii or [PRIMARY_RADIUS]):
          got = extract_buffers(ee, img, pts, radius, 30, INDEX_BANDS)
          for p in pts:
            v = got.get(p["pid"], {})
            row = dict(region=slug, sensor="L8", radius=radius,
                       tier="cmd", season=season, pid=p["pid"],
                       lat=p["lat"], lon=p["lon"],
                       n_px=v.get("IronSulfate_count"))
            for b in INDEX_BANDS:
                row[b + "_p90"] = v.get(b + "_p90")
                row[b + "_mean"] = v.get(b + "_mean")
            for a in ANALYTES:
                row[a] = p.get(a)
            rows.append(row)
          print("  r=%3dm extracted %d" % (radius, len(pts)))
    os.makedirs(OUTDIR, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s (%d rows)" % (out_csv, len(rows)))


def run_analyse(paths, n_perm=5000, out_txt=None):
    rows = [r for r in load_extracted(paths) if r.get("tier") == "cmd"]
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 88)
    say("PHASE CMD1 - neutral-pH COAL mine drainage, Ohio (PRE-REGISTERED)")
    say("Dose-response over in-stream stations. pH is NOT used to classify.")
    say("CAVEAT (binding): sulfate has NO VNIR absorption. Any association is")
    say("with iron precipitate / turbidity / vegetation that CO-VARIES with it.")
    say("=" * 88)

    # ---- canopy diagnostic, REQUIRED before interpreting any null ----
    ndvi = [r.get("NDVI_stress_p90", float("nan")) for r in rows]
    ndvi = [v for v in ndvi if v == v]
    med_ndvi = statistics.median(ndvi) if ndvi else float("nan")
    say("")
    say("--- CANOPY DIAGNOSTIC (required before any null is interpreted) ---")
    say("  n stations extracted : %d" % len(rows))
    say("  median buffer NDVI   : %.3f  (limit %.2f)"
        % (med_ndvi, CANOPY_NDVI_LIMIT))
    canopy_limited = med_ndvi == med_ndvi and med_ndvi > CANOPY_NDVI_LIMIT
    if canopy_limited:
        say("  *** ABOVE LIMIT - buffers are forest canopy. A null here is a")
        say("      MEASUREMENT LIMITATION, not evidence against the hypothesis.")
    else:
        say("  below limit - buffers contain non-canopy surface; a null would")
        say("  be interpretable as evidence.")

    say("")
    say("--- DOSE-RESPONSE: index vs measured chemistry ---")
    say("  %-16s %-20s %7s %5s %6s %8s  %s"
        % ("index", "analyte", "pooled", "n", "btw%", "perm_p",
           "per-watershed sign"))
    res = []
    for idx in INDEX_BANDS:
        for a in ("Sulfate_mgL", "SpecificConductance"):
            xs, ys, rg = [], [], []
            for r in rows:
                v, c = r.get(idx + "_p90", float("nan")), r.get(a, float("nan"))
                if v == v and c == c:
                    xs.append(v)
                    ys.append(c)
                    rg.append(r["region"])
            if len(xs) < 20:
                continue
            rho, n = spearman(xs, ys)
            if rho != rho:
                continue
            by = {}
            for i, g in enumerate(rg):
                by.setdefault(g, []).append(i)
            per = {}
            for g, ix in by.items():
                if len(ix) >= 5:
                    per[g] = spearman([xs[i] for i in ix], [ys[i] for i in ix])[0]
            hits = 0
            for _ in range(n_perm):
                yp = list(ys)
                for ix in by.values():
                    sub = [ys[i] for i in ix]
                    rng.shuffle(sub)
                    for i, v2 in zip(ix, sub):
                        yp[i] = v2
                r2, _ = spearman(xs, yp)
                if r2 == r2 and abs(r2) >= abs(rho):
                    hits += 1
            p = (hits + 1) / (n_perm + 1)
            signs = [v for v in per.values() if v == v]
            consistent = bool(signs) and (all(v > 0 for v in signs)
                                          or all(v < 0 for v in signs))
            res.append(dict(idx=idx, a=a, rho=rho, n=n, p=p, per=per,
                            btw=100 * variance_split(ys, rg), cons=consistent))
    if not res:
        say("  no testable pairs")
        return
    for r, q in zip(res, benjamini_hochberg([r["p"] for r in res])):
        r["q"] = q
    for r in sorted(res, key=lambda d: -abs(d["rho"])):
        say("  %-16s %-20s %+7.3f %5d %6.0f %8.4f  %s %s"
            % (r["idx"], r["a"], r["rho"], r["n"], r["btw"], r["p"],
               " ".join("%s%+.2f" % (g[:4], v)
                        for g, v in sorted(r["per"].items())),
               "CONSISTENT" if r["cons"] else "signs disagree"))

    say("")
    say("--- VERDICT (pre-registered) ---")
    win = [r for r in res if r["cons"] and r["q"] < 0.05 and abs(r["rho"]) >= 0.3]
    if canopy_limited:
        say("  UNINTERPRETABLE - canopy-limited (median NDVI %.3f > %.2f)."
            % (med_ndvi, CANOPY_NDVI_LIMIT))
        say("  Reported as a measurement limitation, NOT as evidence.")
    elif win:
        say("  SUCCESS - CMD signal detected at neutral pH:")
        for r in win:
            say("    %s vs %s  rho=%+.3f  BH_q=%.4f"
                % (r["idx"], r["a"], r["rho"], r["q"]))
    elif any(r["q"] < 0.05 for r in res):
        say("  PARTIAL - significant pooled but signs inconsistent or |rho|<0.3.")
    else:
        say("  NULL - no index sign-consistent across watersheds.")
        say("  Reported as prominently as a success would be.")
    say("")
    say("  Colorado comparison: FerricIron1 vs dissolved Fe rho=+0.568.")
    say("  H-CMD2 predicted Ohio would NOT be weaker.")
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % out_txt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--regions", default="")
    ap.add_argument("--inputs", default="")
    ap.add_argument("--perms", type=int, default=5000)
    ap.add_argument("--radii", default="")
    ap.add_argument("--season", default="leafon",
                    choices=["leafon", "leafoff"])
    ap.add_argument("--out")
    a = ap.parse_args()
    slugs = [s for s in a.regions.split(",") if s] or list(CMD_REGIONS)
    if a.extract:
        run_extract(slugs, a.out or os.path.join(OUTDIR, "cmd_l8.csv"), a.season,
                    [int(x) for x in a.radii.split(",") if x] or None)
    elif a.analyse:
        import glob
        paths = ([p for p in a.inputs.split(",") if p] or
                 glob.glob(os.path.join(OUTDIR, "cmd_l8*.csv")))
        run_analyse(paths, a.perms, a.out)
    else:
        ap.print_help()
