"""End-to-end: does restoring SIM 3466's own specification fix the transfer failure?

The v2.4.0 land arm departs from Rockwell & Gnesda (2021) in three ways that
this repo introduced as "improvements". Each is tested here in isolation and in
combination, leave-one-site-out, against Rockwell's published map.

  A  as shipped      Jul-Sep composite, absolute cutoffs, catch-all class 12
  B  + season        May-Jul, per SIM 3466 p.4: "late May through early July
                     are optimal"; mid-Jul-Oct is explicitly warned against
                     because senesced dry vegetation mimics clay-sulfate-mica
  C  + thresholding  per-scene percentile instead of an absolute constant, per
                     "isolating the highest values using a common standard
                     deviation threshold" (SIM 3466, Final Index Thresholding)
  D  + clay term     every one of Rockwell's six iron-sulfate classes
                     (9,12,14,17,18,19) requires `clay AND`. Our cascade ends
                     with a catch-all `has_iron -> 12` carrying no clay
                     requirement, which appears nowhere in their table 4 and
                     makes our AMD decision equivalent to has_iron alone.

Every configuration is scored LEAVE-ONE-SITE-OUT: any cutoff is fitted on the
other two sites and applied unchanged to the held-out one, so no configuration
is scored on data used to tune it.

CAVEAT: labels are Rockwell's map, not field data. A configuration scoring
better here reproduces the published product more faithfully. That is the
replica question, and it is NOT evidence of greater accuracy on the ground.

    .venv/Scripts/python python/paper_faithful_test.py
"""

import argparse
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JULSEP = os.path.join(ROOT, "data", "matched", "pooled_labels.csv")
MAYJUL = os.path.join(ROOT, "data", "matched", "pooled_labels_may.csv")
SITES = ["Red_Mountain_Pass", "Silverton", "Summitville"]
IRON_ABS, CLAY_ABS = 0.10, 0.021


def pct_of(v, cut):
    return float((v <= cut).mean() * 100.0)


def fit_pct(d_tr, col, abs_cut):
    """Percentile that the shipped absolute cutoff occupies, averaged over the
    training sites. This is the 'shape' the cutoff transfers as."""
    ps = [pct_of(d_tr[d_tr.site == s][col].to_numpy(float), abs_cut)
          for s in d_tr.site.unique()]
    return float(np.mean(ps))


def metrics(pred, y):
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    tn = int((~pred & (y == 0)).sum())
    rec = tp / (tp + fn) if tp + fn else np.nan
    fpr = fp / (fp + tn) if fp + tn else np.nan
    prec = tp / (tp + fp) if tp + fp else np.nan
    n = tp + fp + fn + tn
    po = (tp + tn) / n if n else np.nan
    pe = (((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)) if n else np.nan
    kappa = (po - pe) / (1 - pe) if pe not in (None, 1) and not np.isnan(pe) else np.nan
    return dict(recall=rec, fpr=fpr, prec=prec, J=rec - fpr, kappa=kappa,
                flagged=pred.mean(), n_pos=tp + fn)


def predict(d_te, d_tr, cfg):
    """AMD prediction for one held-out site under configuration cfg."""
    iron = d_te.IronSulfate.to_numpy(float)
    clay = d_te.ClaySulfateMica.to_numpy(float)
    if cfg["relative"]:
        p_iron = fit_pct(d_tr, "IronSulfate", IRON_ABS)
        has_iron = iron > np.percentile(iron, p_iron)
        if cfg["clay"]:
            p_clay = fit_pct(d_tr, "ClaySulfateMica", CLAY_ABS)
            has_clay = clay > np.percentile(clay, p_clay)
    else:
        has_iron = iron > IRON_ABS
        has_clay = clay > CLAY_ABS
    return (has_iron & has_clay) if cfg["clay"] else has_iron


CONFIGS = [
    ("A  as shipped (v2.4.0)", dict(may=False, relative=False, clay=False)),
    ("B  + paper season", dict(may=True, relative=False, clay=False)),
    ("C  + scene-relative cut", dict(may=True, relative=True, clay=False)),
    ("D  + clay term (full)", dict(may=True, relative=True, clay=True)),
    ("   season only, w/ clay", dict(may=True, relative=False, clay=True)),
    ("   scene-rel only (Jul-Sep)", dict(may=False, relative=True, clay=False)),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--julsep", default=JULSEP)
    ap.add_argument("--mayjul", default=MAYJUL)
    args = ap.parse_args(argv)

    data = {False: pd.read_csv(args.julsep), True: pd.read_csv(args.mayjul)}
    for k, v in data.items():
        print("%-18s %5d px, positives %3d (%.2f%%)"
              % ("May-Jul" if k else "Jul-Sep", len(v), v.label.sum(),
                 100 * v.label.mean()))

    print("\n" + "=" * 94)
    print("LEAVE-ONE-SITE-OUT, scored against Rockwell's AMD classes")
    print("=" * 94)
    print("  %-28s %-19s %7s %7s %7s %7s %8s"
          % ("configuration", "held-out site", "recall", "FPR", "J", "kappa",
             "flagged"))
    summary = []
    for name, cfg in CONFIGS:
        d = data[cfg["may"]]
        js, ks = [], []
        print("  " + "-" * 90)
        for st in SITES:
            te, tr = d[d.site == st], d[d.site != st]
            if not len(te) or not te.label.any():
                continue
            m = metrics(predict(te, tr, cfg), te.label.to_numpy(int))
            js.append(m["J"])
            ks.append(m["kappa"])
            print("  %-28s %-19s %7.3f %7.3f %7.3f %7.3f %7.1f%%"
                  % (name, st.replace("_", " "), m["recall"], m["fpr"],
                     m["J"], m["kappa"], 100 * m["flagged"]))
            name = ""
        summary.append((CONFIGS[[c[0] for c in CONFIGS].index(
            [c[0] for c in CONFIGS][len(summary)])][0], min(js),
            float(np.mean(js)), min(ks), float(np.mean(ks))))

    print("\n" + "=" * 94)
    print("SUMMARY - worst case across the three held-out sites")
    print("=" * 94)
    print("  %-30s %9s %9s %9s %9s" % ("configuration", "MIN J", "mean J",
                                       "MIN kappa", "mean kappa"))
    base = None
    for name, mj, avj, mk, avk in summary:
        if base is None:
            base = mj
        tag = ""
        if base and mj > base:
            tag = "   %.1fx vs A" % (mj / base) if base > 0 else ""
        print("  %-30s %9.3f %9.3f %9.3f %9.3f%s"
              % (name.strip(), mj, avj, mk, avk, tag))

    print("\n  A is what ships. Read the MIN column: a configuration that works\n"
          "  at two sites and fails at the third has not transferred.\n"
          "  Labels are Rockwell's published map, so this measures replica\n"
          "  fidelity - reproducing their product - NOT field accuracy.")


if __name__ == "__main__":
    main()
