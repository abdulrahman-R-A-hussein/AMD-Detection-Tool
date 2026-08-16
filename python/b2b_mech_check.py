"""Phase B2b - the falsifiable mechanism check, run BEFORE any parameter sweep.

Registered in validation/B2B_PREREGISTRATION_2026-08-16.md section 2:

    "the mean of each iron index over the bare subset must be HIGHER than over
     the whole region, in every region. If it is not, H-mech is wrong, and this
     phase stops and re-diagnoses rather than tuning parameters."

Placed before the sweep deliberately, so a wrong diagnosis cannot be papered
over by tuning until something works. That failure mode - tune until the number
looks right, then invent the mechanism afterwards - is how findings W1 and
Test C were produced, and this file exists to make it impossible here.

    python b2b_mech_check.py            # VPCA venv (needs `ee`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gee_classify import (init_ee, STAT_BANDS, tiled_mean_stddev,
                          bare_subset_stats)
from seep_detect import REGIONS, region_geometry, l8_composite


def main():
    ee = init_ee()
    print("=" * 86)
    print("B2b MECHANISM CHECK - bare-subset vs whole-region index statistics")
    print("Registered prediction: bare-subset mean must be HIGHER, every region.")
    print("=" * 86)

    verdicts = []
    for slug in REGIONS:
        region = region_geometry(ee, REGIONS[slug])
        comp, n_scenes = l8_composite(ee, region)
        whole = tiled_mean_stddev(ee, comp, STAT_BANDS, region, n_tiles=4)
        bare = bare_subset_stats(ee, comp, region, STAT_BANDS, n_tiles=4)

        print("\n%s  (%d scenes)" % (slug, n_scenes))
        print("  %-18s %10s %10s %10s  %s"
              % ("index", "whole", "bare", "delta", "predicted?"))
        for b in STAT_BANDS:
            w, k = whole[b + "_mean"], bare[b + "_mean"]
            ok = k > w
            verdicts.append((slug, b, ok))
            print("  %-18s %10.4f %10.4f %+10.4f  %s"
                  % (b, w, k, k - w, "yes" if ok else "NO <-- against H-mech"))

    iron = [v for v in verdicts if v[1] != "ClaySulfateMica"]
    n_ok = sum(1 for _, _, ok in iron if ok)
    print("\n" + "=" * 86)
    print("IRON indices matching the registered prediction: %d/%d"
          % (n_ok, len(iron)))
    if n_ok == len(iron):
        print("H-mech SUPPORTED - proceed to the parameter sweep.")
    elif n_ok == 0:
        print("H-mech REFUTED - STOP. Do not sweep parameters. Re-diagnose:")
        print("  the bare subset is NOT iron-richer than the whole region, so")
        print("  whole-region statistics cannot be what admits bare ground.")
    else:
        print("H-mech PARTIAL - report which indices fail and why before any")
        print("  sweep. Do not proceed on the passing subset alone without")
        print("  saying so explicitly in the report.")


if __name__ == "__main__":
    main()
