"""Regenerate Arm B2's dose-response family - Part 2 of
validation/ARM_B2_SEEP_DETECTION_2026-08-14.md - from committed code.

  python python/b2_dose_response_regen.py --out validation/report_b2_dose_response_2026-09-15.txt

That report's permutation p and BH q (e.g. FerricIron1 vs dissolved Fe
p = 0.0004, q = 0.0072) appear in no committed raw output; they were quoted
from the report into README, CITATION.cff, GRANT_CASE and ACCURACY_ASSESSMENT.
This regenerates the whole family:

  - the 86 B2 source points, Landsat 8, 60 m buffers, p90;
  - 9 indices x 4 analytes (dissolved Fe, total Fe, sulfate, pH) = 36 tests;
  - analyte permuted WITHIN district, 5,000 draws, seed 20260814, then
    Benjamini-Hochberg over the 36;
  - districts read in REGIONS order (Silverton, Leadville, Ouray, Central City),
    the order that regenerates the committed B2 reports byte for byte.

A 10,000-draw run is printed too. A permutation p is a Monte Carlo estimate, so
its printed value depends on the number of draws; the second run shows how much.

Needs the gitignored data/matched/seep_l8_*.csv. No Earth Engine.
"""

import argparse
import os
import sys

import _amdtool_path  # noqa: F401
from amdtool import dose_response
from amdtool.io import load_extracted

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "data", "matched")
REGIONS_ORDER = ("silverton_co", "leadville_co", "ouray_co", "central_city_co")
INDICES = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron", "ClaySulfateMica",
           "GreenNIR", "GreenNIRNorm", "NDVI_stress", "AMDclassFrac"]
ANALYTES = ("Iron_mgL_dissolved", "Iron_mgL_any", "Sulfate_mgL", "pH")
SEED = 20260814


def family(rows, n_perm):
    return dose_response.analyse(rows, INDICES, ANALYTES, stat="p90", group_key="region",
                                 n_perm=n_perm, seed=SEED, min_n=10, min_group_n=5,
                                 canopy_limit=None)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    paths = [os.path.join(M, "seep_l8_%s.csv" % d) for d in REGIONS_ORDER]
    rows = [r for r in load_extracted(paths) if r["radius"] == 60 and r["tier"] == "target"]
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 96)
    say("ARM B2 DOSE-RESPONSE FAMILY - regenerated 2026-09-15 from committed code")
    say("86 source points (L8, 60 m, p90); within-district permutation; BH over the family")
    say("inputs, in order: %s" % ", ".join("seep_l8_%s.csv" % d for d in REGIONS_ORDER))
    say("=" * 96)
    say("target rows: %d" % len(rows))
    for n_perm in (5000, 10000):
        res = family(rows, n_perm)
        say()
        say("--- %d within-district permutations, seed %d; family = %d tests ---"
            % (n_perm, SEED, len(res.pairs)))
        say("  %-15s %-20s %7s %4s %8s %8s %8s  %s"
            % ("index", "analyte", "rho", "n", "perm_p", "BH_q", "between", "signs"))
        for p in sorted(res.pairs, key=lambda p: (p.p, p.index, p.analyte)):
            say("  %-15s %-20s %+7.3f %4d %8.4f %8.4f %7.0f%%  %s"
                % (p.index, p.analyte, p.rho, p.n, p.p, p.q, p.between_pct,
                   "consistent" if p.sign_consistent else "disagree"))
    say()
    say("CAVEAT: a permutation p is a Monte Carlo estimate; compare the two runs.")
    say("It tests LAND-SURFACE ferric precipitate at source points, never dissolved")
    say("iron or sulfate directly. Sulfate has no VNIR absorption.")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % a.out)


if __name__ == "__main__":
    sys.exit(main())
