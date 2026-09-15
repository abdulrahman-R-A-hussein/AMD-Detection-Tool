"""Arm B2 reproduction audit, 2026-09-15 - the evidence behind
validation/AUDIT_2026-09-15_B2_REPRODUCTION.md, regenerated from raw extractions.

  python python/b2_reproduction_audit.py --out validation/report_b2_reproduction_2026-09-15.txt

Three checks, none needing Earth Engine:

  1. TIED SCORES. Every B2 detection row's worst-case leave-one-region-out J from
     the sweep AS COMMITTED (python/seep_detect.py at ad05971, loaded via
     `git show`) against amdtool's tie-corrected sweep. Rows are loaded in the
     REGIONS order (Silverton, Leadville, Ouray, Central City), the order that
     regenerates the committed reports byte for byte.
  2. B2b. The same comparison for every classify_v4 grid point, and for the v3
     baseline (AMDclassFrac vs C3b) the B2b and B2c reports compare against.
  3. POOLED COMPOSITES. Which input files reproduce the control-tier n printed in
     report_seep_b2_s2_c3b_2026-08-15.txt.

Needs the gitignored data/matched/seep_*.csv extractions and the repository's
git history.
"""

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile

import _amdtool_path  # noqa: F401
from amdtool import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "data", "matched")
LEGACY_REV = "ad05971"
REGIONS_ORDER = ("silverton_co", "leadville_co", "ouray_co", "central_city_co")
INDICES = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron", "ClaySulfateMica",
           "GreenNIR", "GreenNIRNorm", "NDVI_stress", "AMDclassFrac"]
V4_GRID = [(k, c) for k in (0.5, 1.0, 1.5, 2.0) for c in (0.25, 0.5)]


def committed_seep_detect():
    src = subprocess.run(["git", "show", "%s:python/seep_detect.py" % LEGACY_REV], cwd=ROOT,
                         capture_output=True, check=True).stdout
    path = os.path.join(tempfile.mkdtemp(), "seep_detect_%s.py" % LEGACY_REV)
    with open(path, "wb") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("seep_detect_committed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def files(pattern, districts=REGIONS_ORDER):
    return [os.path.join(M, pattern % d) for d in districts]


def vectors(rows, key, tier, extra=lambda r: True):
    sel = [r for r in rows if r["tier"] in ("target", tier) and r.get(key) == r.get(key) and extra(r)]
    return ([r[key] for r in sel], [1 if r["tier"] == "target" else 0 for r in sel],
            [r["region"] for r in sel])


def tied_share(scores):
    counts = {}
    for v in scores:
        counts[v] = counts.get(v, 0) + 1
    return sum(c for c in counts.values() if c > 1) / len(scores)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    old = committed_seep_detect()
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 96)
    say("ARM B2 REPRODUCTION AUDIT - 2026-09-15")
    say("committed sweep = python/seep_detect.py @ %s; corrected = amdtool.stats (tie groups)" % LEGACY_REV)
    say("=" * 96)

    say()
    say("1. TIED SCORES - worst-case LORO J, radius 60 m, p90, rows in REGIONS order")
    changed = crossed = 0
    blocks = [("L8", files("seep_l8_%s.csv"), ("C1", "C2", "C3")),
              ("S2", files("seep_s2_%s.csv"), ("C1", "C2", "C3")),
              ("S2", files("seep_s2_%s.csv") + files("seep_s2_c3b_%s.csv"), ("C3b",))]
    say("  %-6s %-15s %-4s %5s %6s %7s %9s %9s  %s" % ("sensor", "index", "tier", "n-", "tied", "AUC",
                                                     "committed", "corrected", "note"))
    for sensor, paths, tiers in blocks:
        rows = [r for r in old.load_extracted(paths) if r["radius"] == 60 and r["region"] in REGIONS_ORDER]
        for index in INDICES:
            for tier in tiers:
                sc, lb, rg = vectors(rows, index + "_p90", tier)
                if sum(lb) < 10 or len(lb) - sum(lb) < 10:
                    continue
                jo = old.loro_worst_j(sc, lb, rg)[0]
                jn = stats.loro_worst_j(sc, lb, rg)[0]
                pos = [v for v, l in zip(sc, lb) if l]
                neg = [v for v, l in zip(sc, lb) if not l]
                note = []
                if "%.3f" % jo != "%.3f" % jn:
                    note.append("PRINTED VALUE CHANGES")
                    changed += 1
                for bar in (0.25, 0.15):
                    if (jo >= bar) != (jn >= bar):
                        note.append("crosses %.2f" % bar)
                        crossed += bar == 0.25
                say("  %-6s %-15s %-4s %5d %5.1f%% %7.3f %+9.3f %+9.3f  %s"
                    % (sensor, index, tier, len(lb) - sum(lb), 100 * tied_share(sc),
                       stats.auc(pos, neg), jo, jn, " | ".join(note)))
    say("  rows whose printed J changes: %d; rows crossing the 0.25 decision bar: %d" % (changed, crossed))

    say()
    say("2. B2b - AMDclassFrac_v4_p90 vs C3b, every grid point; and the v3 baseline")
    rows = old.load_extracted(files("seep_v4_%s.csv"))
    say("  %-22s %7s %9s %9s" % ("grid point", "AUC", "committed", "corrected"))
    best = None
    for k_bare, clay in V4_GRID:
        sc, lb, rg = vectors(rows, "AMDclassFrac_v4_p90", "C3b",
                             lambda r, k=k_bare, c=clay: r.get("k_bare") == k and r.get("clay_bare") == c
                             and r["region"] in REGIONS_ORDER)
        jo, jn = old.loro_worst_j(sc, lb, rg)[0], stats.loro_worst_j(sc, lb, rg)[0]
        best = jn if best is None else max(best, jn)
        pos = [v for v, l in zip(sc, lb) if l]
        neg = [v for v, l in zip(sc, lb) if not l]
        say("  k_bare=%.1f clay=%.2f   %7.3f %+9.3f %+9.3f" % (k_bare, clay, stats.auc(pos, neg), jo, jn))
    say("  best corrected J = %+.3f -> pre-registered verdict %s" % (
        best, "SUCCESS" if best >= 0.25 else "PARTIAL" if best >= 0.15 else "FAILURE (unchanged)"))
    rows = [r for r in old.load_extracted(files("seep_s2_%s.csv") + files("seep_s2_c3b_%s.csv"))
            if r["radius"] == 60 and r["region"] in REGIONS_ORDER]
    sc, lb, rg = vectors(rows, "AMDclassFrac_p90", "C3b")
    say("  v3 baseline AMDclassFrac vs C3b: committed %+.3f, corrected %+.3f"
        % (old.loro_worst_j(sc, lb, rg)[0], stats.loro_worst_j(sc, lb, rg)[0]))

    say()
    say("3. POOLED COMPOSITES - control n printed in report_seep_b2_s2_c3b_2026-08-15.txt:")
    say("   C1 446, C2 575, C3b 350, C3 578")
    sets = {
        "S2 + C3b files": files("seep_s2_%s.csv") + files("seep_s2_c3b_%s.csv"),
        "S2 + C3b + _nocloudfilter files": files("seep_s2_%s.csv") + files("seep_s2_c3b_%s.csv") + [
            os.path.join(M, "seep_s2_central_city_co_nocloudfilter.csv"),
            os.path.join(M, "seep_s2_leadville_co_nocloudfilter.csv")],
    }
    for name, paths in sets.items():
        rows = [r for r in old.load_extracted(paths) if r["radius"] == 60 and r["region"] in REGIONS_ORDER]
        n = {t: sum(1 for r in rows if r["tier"] == t) for t in ("C1", "C2", "C3b", "C3")}
        say("  %-32s C1 %d, C2 %d, C3b %d, C3 %d" % (name, n["C1"], n["C2"], n["C3b"], n["C3"]))
    for f in ("seep_s2_central_city_co_nocloudfilter.csv", "seep_s2_leadville_co_nocloudfilter.csv",
              "seep_s2_central_city_co.csv", "seep_s2_leadville_co.csv"):
        rows = old.load_extracted([os.path.join(M, f)])
        scenes = sorted({int(r["n_scenes"]) for r in rows if r.get("n_scenes") == r.get("n_scenes")})
        say("  %-44s n_scenes %s" % (f, scenes))

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % a.out)


if __name__ == "__main__":
    sys.exit(main())
