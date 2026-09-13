"""Sample-size calculations for the field campaign (docs/FIELD_CAMPAIGN.md).

Every number in the campaign design comes from this script, so a reviewer can
re-run it and so nobody has to trust an asserted n.

Three questions, each tied to a result already measured in validation/:

  1. DOSE-RESPONSE. How many synchronous stations per district to detect a
     within-district Spearman rho? Anchored on the measured per-district values
     (+0.64 / +0.00 / +0.68 / +0.64 for FerricIron1 vs dissolved Fe) and on the
     project's own |rho| >= 0.3 bar.

  2. SIGN CONSISTENCY. The project's headline check is that every district
     shows the same sign. If the true within-district rho is r and each of k
     districts has n stations, how likely is it that all k estimates come out
     positive? This is what failed in Ohio and passed in Pennsylvania.

  3. DISCOVERY. To test blind search, the field team visits sites the tool flags
     (precision) and sites with known sources (recall). How many visits to pin
     each proportion to a given 95% Wilson half-width?

Method: closed-form Fisher-z with the Bonett & Wright (2000) variance inflation
for Spearman, CHECKED by Monte Carlo on bivariate normal data with the Pearson
correlation set to 2*sin(pi*rho_s/6), which gives the requested Spearman rho.
The closed form is only trusted where the simulation agrees with it.

Usage:
    python python/field_power.py            # full report
    python python/field_power.py --reps 20000
"""

import argparse
import math

import numpy as np
from scipy import stats

Z_ALPHA = stats.norm.ppf(0.975)   # two-sided 0.05
POWER = 0.80
Z_BETA = stats.norm.ppf(POWER)


def n_spearman(rho):
    """Closed-form n for Spearman rho at alpha=.05 two-sided, power .80."""
    fz = math.atanh(rho)
    base = ((Z_ALPHA + Z_BETA) / fz) ** 2 + 3
    return math.ceil((base - 3) * (1 + rho ** 2 / 2) + 3)


def _pearson_for_spearman(rho_s):
    return 2 * math.sin(math.pi * rho_s / 6)


def sim_power(rho_s, n, reps, rng):
    """Monte Carlo power for Spearman rho at n (two-sided p < .05)."""
    r = _pearson_for_spearman(rho_s)
    cov = [[1, r], [r, 1]]
    hits = 0
    for _ in range(reps):
        x = rng.multivariate_normal([0, 0], cov, size=n)
        if stats.spearmanr(x[:, 0], x[:, 1]).pvalue < 0.05:
            hits += 1
    return hits / reps


def sim_sign_positive(rho_s, n, reps, rng):
    """P(estimated Spearman rho > 0) in ONE district of n stations."""
    r = _pearson_for_spearman(rho_s)
    cov = [[1, r], [r, 1]]
    pos = 0
    for _ in range(reps):
        x = rng.multivariate_normal([0, 0], cov, size=n)
        if stats.spearmanr(x[:, 0], x[:, 1]).statistic > 0:
            pos += 1
    return pos / reps


def wilson_halfwidth(p, n):
    z = Z_ALPHA
    denom = 1 + z * z / n
    return z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom


def n_for_halfwidth(p, hw):
    n = 2
    while wilson_halfwidth(p, n) > hw:
        n += 1
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20260913)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)

    print("FIELD CAMPAIGN SAMPLE SIZES   alpha=0.05 two-sided, power=0.80, "
          "reps=%d, seed=%d" % (a.reps, a.seed))

    # ---- 1. dose-response ---------------------------------------------------
    print("\n1. DOSE-RESPONSE - stations per district to detect Spearman rho")
    print("   rho    closed-form n   simulated power at that n   anchor")
    anchors = {0.30: "project bar |rho| >= 0.3",
               0.40: "",
               0.50: "",
               0.568: "measured pooled FerricIron1 vs dissolved Fe (L8)",
               0.64: "measured Central City / Silverton district rho"}
    for rho, why in anchors.items():
        n = n_spearman(rho)
        pw = sim_power(rho, n, a.reps, rng)
        print("   %.3f  %5d           %.3f                        %s"
              % (rho, n, pw, why))

    # ---- 2. sign consistency ------------------------------------------------
    print("\n2. SIGN CONSISTENCY - P(all k districts estimate a positive rho)")
    print("   per-district probability simulated; all-k = product (districts "
          "independent)")
    print("   true rho   n/district   P(one +)   P(all 3 +)   P(all 4 +)")
    for rho in (0.20, 0.30, 0.50):
        for n in (10, 20, 30, 50):
            p1 = sim_sign_positive(rho, n, a.reps, rng)
            print("   %.2f       %3d          %.3f      %.3f        %.3f"
                  % (rho, n, p1, p1 ** 3, p1 ** 4))

    # ---- 3. discovery -------------------------------------------------------
    print("\n3. DISCOVERY - field visits to estimate precision or recall")
    print("   95%% Wilson half-width at the least-favourable p = 0.5")
    for hw in (0.20, 0.15, 0.10):
        print("   +/- %.2f   ->  %3d visits" % (hw, n_for_halfwidth(0.5, hw)))
    print("   at p = 0.2 (a plausible precision for a detector that failed "
          "its bar):")
    for hw in (0.15, 0.10):
        print("   +/- %.2f   ->  %3d visits" % (hw, n_for_halfwidth(0.2, hw)))


if __name__ == "__main__":
    main()
