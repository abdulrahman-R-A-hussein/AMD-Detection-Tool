"""Find an iron criterion that TRANSFERS between sites, by leave-one-site-out.

Finding L1: every AMD class requires `IronSulfate > 0.10`, an absolute cutoff on
an unnormalised ratio difference. It scores AUC 0.938 at Silverton (where it was
calibrated) and 0.678 at Summitville, with Youden-optimal cutoffs of opposite
sign. Test C's mistake was judging a threshold by its WITHIN-SITE AUC, which
says nothing about transfer.

This module judges candidates the other way round. For each candidate score:

  * per-site AUC (cutoff-free separability)
  * LEAVE-ONE-SITE-OUT: pool the other sites, take the Youden-optimal cutoff
    there, apply it UNCHANGED to the held-out site, and record recall.

Candidates are ranked by **worst-case (minimum) LOSO recall**, not by mean and
not by AUC. A detector that works at two sites and fails at the third is not a
detector; the minimum is the honest summary.

Two families are tested:
  absolute       - the cutoff transfers as a raw number (what v2.4.0 does)
  scene-relative - the score is standardised WITHIN each site first (z-score or
                   percentile rank), so the cutoff transfers as a shape

CAVEAT: labels come from Rockwell's published map, not from the field. This
measures agreement/transferability, NOT correctness. See python/pool_labels.py.

    .venv/Scripts/python python/iron_criterion_search.py
"""

import argparse
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOLED = os.path.join(ROOT, "data", "matched", "pooled_labels.csv")
EPS = 1e-4


def roc_auc(v, y):
    v, y = np.asarray(v, float), np.asarray(y, int)
    pos, neg = v[y == 1], v[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), float)
    ranks[order] = np.arange(1, len(v) + 1)
    # average ranks over ties
    s = v[order]
    i = 0
    r = ranks[order]
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[i:j + 1] = r[i:j + 1].mean()
        i = j + 1
    ranks[order] = r
    return (ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) \
        / (len(pos) * len(neg))


def youden_cut(v, y):
    v, y = np.asarray(v, float), np.asarray(y, int)
    cuts = np.quantile(v, np.linspace(0.001, 0.999, 600))
    best, bc = -2.0, float(np.median(v))
    for c in np.unique(cuts):
        p = v > c
        tpr = p[y == 1].mean() if (y == 1).any() else 0.0
        fpr = p[y == 0].mean() if (y == 0).any() else 0.0
        if tpr - fpr > best:
            best, bc = tpr - fpr, float(c)
    return bc


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def build_scores(d):
    """Candidate scores. 'abs' transfers as a raw number; 'rel' is
    standardised within each site before any cutoff is applied."""
    b = {k: d[k].to_numpy(float) for k in
         ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]}
    r21 = b["SR_B2"] / (b["SR_B1"] + EPS)
    r54 = b["SR_B5"] / (b["SR_B4"] + EPS)
    r67 = b["SR_B6"] / (b["SR_B7"] + EPS)

    s = {}
    # --- the shipped criterion and normalised variants of it ---
    s["IronSulfate (v2.4.0)"] = d.IronSulfate.to_numpy(float)
    s["IronSulfate normdiff"] = (r21 - r54) / (r21 + r54 + EPS)
    s["B2/B1 ratio"] = r21
    s["normdiff(B2,B1)"] = (b["SR_B2"] - b["SR_B1"]) / (b["SR_B2"] + b["SR_B1"] + EPS)
    # --- the ferric indices, which Test C scored far higher ---
    s["FerricIron1 (B4/B2)"] = d.FerricIron1.to_numpy(float)
    s["normdiff(B4,B2)"] = (b["SR_B4"] - b["SR_B2"]) / (b["SR_B4"] + b["SR_B2"] + EPS)
    s["FerricIron2"] = d.FerricIron2.to_numpy(float)
    s["ClaySulfateMica"] = d.ClaySulfateMica.to_numpy(float)
    s["Clay normdiff"] = (r67 - r54) / (r67 + r54 + EPS)

    # --- composite rules. The AMD classes are conjunctions (iron AND clay AND
    # ferric), so single-index scores understate what the cascade does. These
    # express the conjunction continuously: a per-site z of each component,
    # then MIN (all must be high) or MEAN (they trade off).
    site = d.site.to_numpy()
    z = {k: site_standardise(v, site, "z") for k, v in
         [("iron", s["IronSulfate (v2.4.0)"]),
          ("f1", s["FerricIron1 (B4/B2)"]),
          ("f2", s["FerricIron2"]),
          ("clay", s["ClaySulfateMica"])]}
    s["MIN z(f2, clay)"] = np.minimum(z["f2"], z["clay"])
    s["MIN z(f1, f2, clay)"] = np.minimum(np.minimum(z["f1"], z["f2"]), z["clay"])
    s["MIN z(iron, f2, clay)"] = np.minimum(np.minimum(z["iron"], z["f2"]), z["clay"])
    s["MEAN z(f1, f2, clay)"] = (z["f1"] + z["f2"] + z["clay"]) / 3.0
    s["MEAN z(iron, f1, f2, clay)"] = (z["iron"] + z["f1"] + z["f2"] + z["clay"]) / 4.0
    return s


def site_standardise(v, site, how):
    out = np.empty(len(v), float)
    for st in np.unique(site):
        m = site == st
        x = v[m]
        if how == "z":
            sd = x.std()
            out[m] = (x - x.mean()) / (sd if sd > 0 else 1.0)
        else:                                   # percentile rank in [0,1]
            out[m] = pd.Series(x).rank(pct=True).to_numpy()
    return out


def evaluate(name, v, y, site, family):
    sites = sorted(np.unique(site))
    per_auc = {st: roc_auc(v[site == st], y[site == st]) for st in sites}
    rows = []
    for st in sites:
        tr, te = site != st, site == st
        if not y[tr].any() or not (y[tr] == 0).any() or not y[te].any():
            continue
        c = youden_cut(v[tr], y[tr])
        p = v[te] > c
        tp = int((p & (y[te] == 1)).sum())
        fp = int((p & (y[te] == 0)).sum())
        fn = int((~p & (y[te] == 1)).sum())
        rec = tp / (tp + fn) if tp + fn else float("nan")
        prec = tp / (tp + fp) if tp + fp else float("nan")
        fpr = p[y[te] == 0].mean() if (y[te] == 0).any() else float("nan")
        lo, hi = wilson(tp, tp + fn)
        rows.append(dict(site=st, cut=c, recall=rec, prec=prec, fpr=fpr,
                         J=rec - fpr, flagged=p.mean(), lo=lo, hi=hi,
                         n_pos=tp + fn))
    if not rows:
        return None
    recs = [r["recall"] for r in rows]
    js = [r["J"] for r in rows]
    return dict(name=name, family=family, folds=rows, auc=per_auc,
                min_recall=min(recs), mean_recall=float(np.mean(recs)),
                spread=max(recs) - min(recs), min_J=min(js),
                mean_J=float(np.mean(js)),
                min_auc=float(np.nanmin(list(per_auc.values()))),
                mean_prec=float(np.nanmean([r["prec"] for r in rows])))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=POOLED)
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args(argv)

    d = pd.read_csv(args.csv)
    y = d.label.to_numpy(int)
    site = d.site.to_numpy()
    sites = sorted(np.unique(site))
    print("pooled: %d px, %d sites, label=1 %d (%.2f%%)"
          % (len(d), len(sites), y.sum(), 100 * y.mean()))
    for st in sites:
        m = site == st
        print("  %-20s n=%6d  positives %4d (%5.2f%%)"
              % (st, m.sum(), y[m].sum(), 100 * y[m].mean()))
    if len(sites) < 2:
        raise SystemExit("need >=2 sites for leave-one-site-out")

    base = build_scores(d)
    results = []
    for name, v in base.items():
        results.append(evaluate(name, v, y, site, "absolute"))
        for how, tag in (("z", "z-score"), ("rank", "pctile")):
            results.append(evaluate("%s [%s]" % (name, tag),
                                    site_standardise(v, site, how), y, site,
                                    "scene-relative"))
    results = [r for r in results if r]

    print("\n" + "=" * 92)
    print("LEAVE-ONE-SITE-OUT: cutoff fitted on the other sites, applied "
          "unchanged to the held-out one")
    print("=" * 92)
    print("  Ranked by MIN Youden J on the held-out site. J = TPR - FPR is\n"
          "  prevalence-independent, so it is comparable across sites whose\n"
          "  AMD base rates differ 24-fold (1.7% / 2.6% / 40.2%), and unlike\n"
          "  recall it cannot be gamed by flagging most of the scene.\n")
    print("  %-32s %-15s %7s %7s %7s %8s %7s"
          % ("candidate", "family", "MIN J", "mean J", "MIN AUC", "MIN rec",
             "spread"))
    for r in sorted(results, key=lambda r: -r["min_J"]):
        print("  %-32s %-15s %7.3f %7.3f %7.3f %8.3f %7.3f"
              % (r["name"], r["family"], r["min_J"], r["mean_J"],
                 r["min_auc"], r["min_recall"], r["spread"]))

    print("\n" + "=" * 92)
    print("Per-fold detail for the top %d by worst-case recall" % args.top)
    print("=" * 92)
    for r in sorted(results, key=lambda r: -r["min_J"])[:args.top]:
        print("\n  %s   [%s]" % (r["name"], r["family"]))
        print("    per-site AUC: " + "  ".join(
            "%s=%.3f" % (k.replace("_", " "), v) for k, v in r["auc"].items()))
        for f in r["folds"]:
            print("    held-out %-20s cut=%+8.4f  J=%.3f  recall=%.3f "
                  "[95%% %.2f-%.2f, n+=%d]  prec=%.3f  flagged=%.1f%%"
                  % (f["site"], f["cut"], f["J"], f["recall"], f["lo"],
                     f["hi"], f["n_pos"], f["prec"], 100 * f["flagged"]))

    print("\nRanked by MINIMUM recall on purpose: a criterion that works at two\n"
          "sites and fails at the third has not transferred. Compare each row\n"
          "against 'IronSulfate (v2.4.0) / absolute', which is what ships.")
    print("\nLabels are Rockwell's map, not field data - this measures\n"
          "transferable AGREEMENT, not correctness.")


if __name__ == "__main__":
    main()
