"""Phase B2c - continuous-score AMD detector, replacing the decision tree.

READ validation/B2C_PREREGISTRATION_2026-08-16.md FIRST (commit 6af0b5b,
written before any model was fitted).

WHY THIS EXISTS. At the same 86 chemically-confirmed source points, against the
same non-circular bare-ground control:

    FerricIron1, CONTINUOUS (p90)              worst-case LORO J  +0.318
    AMDclassFrac, BINARISED, v3 thresholds                         0.000
    AMDclassFrac, BINARISED, v4 bare-relative thresholds           0.000

Two threshold references have been tried and neither recovers what the
continuous index does unaided; B2b confirmed the threshold mechanism 16/16 and
still fixed nothing. The remaining difference is not WHICH threshold - it is
thresholding at all. SIM 3466 is a categorical MAPPING product and we have been
asking it to serve as a DETECTION product.

No Earth Engine. Everything is already extracted on disk.

    python continuous_detector.py --sensor S2
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seep_detect import (REGIONS, OUTDIR, SEED, PRIMARY_RADIUS, PRIMARY_STAT,
                         N_PERM, J_THRESHOLD, load_extracted, auc,
                         best_threshold, j_at, perm_p_within_region,
                         benjamini_hochberg, spearman, variance_split)

# Pre-registered feature set. AMDclassFrac deliberately absent - it is the
# thing being replaced.
FEATURES = ["IronSulfate", "FerricIron1", "FerricIron2", "FerrousIron",
            "ClaySulfateMica", "GreenNIR", "GreenNIRNorm", "NDVI_stress"]
BASELINE = "FerricIron1"
DECISION_TIERS = ("C1clean", "C2", "C3b")   # C3 excluded (NDVI-circular)

# Phase B2d. PUBLISHED EPA thresholds, deliberately external so they cannot be
# accused of being fitted: 0.3 mg/L Fe is the secondary drinking water standard,
# pH 6.5-9.0 the aquatic-life criteria. The grey band between clean and dirty is
# excluded from BOTH rather than forced into one.
FE_CLEAN, PH_CLEAN_LO, PH_CLEAN_HI = 0.3, 6.5, 9.0
FE_DIRTY, PH_DIRTY = 1.0, 6.0


def chem_class(fe, ph):
    """'clean' | 'dirty' | 'grey' | None (insufficient measurement).

    WHY THIS EXISTS: C1 was defined by station TYPE, which is a proxy. Verified
    2026-08-16, 104 of 446 in-stream "negative controls" carry measured
    Fe >= 1.0 mg/L - they are AMD-affected water being used as the negative
    class, and every model has been penalised for declining to call them clean.
    """
    has_fe, has_ph = fe == fe, ph == ph
    if not (has_fe or has_ph):
        return None
    if (has_fe and fe >= FE_DIRTY) or (has_ph and ph < PH_DIRTY):
        return "dirty"
    if (has_fe and fe < FE_CLEAN) and (has_ph and PH_CLEAN_LO <= ph <= PH_CLEAN_HI):
        return "clean"
    return "grey"


def load_points(paths, sensor, radius=PRIMARY_RADIUS, stat=PRIMARY_STAT):
    """Rows -> (features dict, label, region, tier), dropping incomplete rows."""
    out = []
    for r in load_extracted(paths):
        if r.get("sensor") != sensor or r.get("radius") != radius:
            continue
        if r.get("region") not in REGIONS:
            continue
        feats = {f: r.get("%s_%s" % (f, stat), float("nan")) for f in FEATURES}
        if any(v != v for v in feats.values()):
            continue
        fe = r.get("Iron_mgL_any", float("nan"))
        ph = r.get("pH", float("nan"))
        tier = r["tier"]
        if tier == "C1":
            k = chem_class(fe, ph)
            if k is None:
                continue                      # unmeasured: cannot classify
            tier = {"clean": "C1clean", "dirty": "C1dirty", "grey": "C1grey"}[k]
        out.append(dict(x=feats, tier=tier, region=r["region"], pid=r["pid"],
                        fe=fe, ph=ph))
    return out


def zscore_params(rows, regions):
    """Per-region mean/sd, computed ONLY over the given (training) regions.

    The held-out region must contribute nothing - not to the fit, and not to
    preprocessing either. Standardising with the test region's own statistics
    is the most common silent way a held-out test stops being held out.
    """
    par = {}
    for g in regions:
        sub = [r for r in rows if r["region"] == g]
        if not sub:
            continue
        p = {}
        for f in FEATURES:
            v = [r["x"][f] for r in sub]
            m = sum(v) / len(v)
            sd = (sum((a - m) ** 2 for a in v) / len(v)) ** 0.5
            p[f] = (m, sd if sd > 1e-9 else 1.0)
        par[g] = p
    return par


def apply_z(rows, par, fallback_region=None):
    """Standardise each row by ITS OWN region's parameters.

    A held-out region has no training parameters by construction, so it is
    standardised with the pooled mean of the training regions' parameters.
    That is the honest operational case: a new district arrives, and the model
    must score it without having seen it.
    """
    pooled = {}
    for f in FEATURES:
        ms = [p[f][0] for p in par.values()]
        ss = [p[f][1] for p in par.values()]
        pooled[f] = (sum(ms) / len(ms), sum(ss) / len(ss))
    out = []
    for r in rows:
        p = par.get(r["region"], pooled)
        out.append([(r["x"][f] - p[f][0]) / p[f][1] for f in FEATURES])
    return out


def fit_logistic(X, y, l2=1.0, iters=3000, lr=0.05):
    """L2 logistic regression by gradient descent, vectorised with numpy.

    Fixed hyperparameters by pre-registration: with 4 regions there is no
    honest budget for model selection, so a deliberately weak learner is used
    and never tuned.

    Vectorised because the permutation null has to REFIT the model on every
    draw. A pure-Python loop made that unaffordable (~60 s per draw), which is
    why the first version permuted the baseline score instead - and that tested
    the wrong thing. numpy makes the correct null cheap enough to actually run.
    """
    import numpy as np
    Xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    n, d = Xa.shape
    w = np.zeros(d)
    b = 0.0
    pos = ya.sum() or 1.0
    neg = (n - ya.sum()) or 1.0
    # class weights: controls outnumber targets ~5:1; without this the model
    # can score well by predicting "control" everywhere.
    cw = np.where(ya > 0, 1.0 / pos, 1.0 / neg)
    for _ in range(iters):
        z = np.clip(b + Xa @ w, -30.0, 30.0)
        e = (1.0 / (1.0 + np.exp(-z)) - ya) * cw
        w -= lr * (Xa.T @ e + l2 * w / n)
        b -= lr * e.sum()
    return w.tolist(), float(b)


def score(X, w, b):
    return [b + sum(w[j] * xi[j] for j in range(len(w))) for xi in X]


def loro_evaluate(rows, tier, leak=False):
    """Leave-one-REGION-out. Returns (worst J, per-fold J, per-fold coeffs).

    `leak=True` deliberately standardises using ALL regions including the
    held-out one - the pre-registered positive control. It MUST inflate the
    score; if it does not, the leakage guard is not doing anything.
    """
    use = [r for r in rows if r["tier"] in ("target", tier)]
    regs = sorted({r["region"] for r in use})
    if len(regs) < 3:
        return float("nan"), {}, []

    per, coeffs = {}, []
    for held in regs:
        tr = [r for r in use if r["region"] != held]
        te = [r for r in use if r["region"] == held]
        ytr = [1 if r["tier"] == "target" else 0 for r in tr]
        yte = [1 if r["tier"] == "target" else 0 for r in te]
        if sum(ytr) < 5 or sum(yte) < 3 or len(yte) - sum(yte) < 3:
            continue
        par = zscore_params(use if leak else tr,
                            regs if leak else [g for g in regs if g != held])
        w, b = fit_logistic(apply_z(tr, par), ytr)
        coeffs.append((held, w))
        s_tr, s_te = score(apply_z(tr, par), w, b), score(apply_z(te, par), w, b)
        cut, _ = best_threshold([s for s, l in zip(s_tr, ytr) if l],
                                [s for s, l in zip(s_tr, ytr) if not l])
        per[held] = j_at([s for s, l in zip(s_te, yte) if l],
                         [s for s, l in zip(s_te, yte) if not l], cut)
    vals = [v for v in per.values() if v == v]
    return (min(vals) if vals else float("nan")), per, coeffs


def model_perm_p(rows, tier, observed, n_perm, rng):
    """Within-region permutation null for the MODEL, refitting on every draw.

    The pre-registration specifies the null for the reported statistic. An
    earlier version permuted the BASELINE score instead, for speed; that tested
    a different quantity and was misleading wherever the baseline and the model
    disagree - most visibly on Landsat, where the baseline is ~0 while the model
    scores 0.228. Fixed by vectorising the fit so a refit-per-draw null is
    affordable. n_perm is smaller than the baseline null's 10,000 and the actual
    count is reported, not implied.
    """
    if observed != observed:
        return float("nan")
    use = [r for r in rows if r["tier"] in ("target", tier)]
    by = {}
    for i, r in enumerate(use):
        by.setdefault(r["region"], []).append(i)
    lab = [1 if r["tier"] == "target" else 0 for r in use]
    hits = 0
    for _ in range(n_perm):
        perm = list(lab)
        for idx in by.values():
            sub = [lab[i] for i in idx]
            rng.shuffle(sub)
            for i, v in zip(idx, sub):
                perm[i] = v
        shuffled = [dict(r, tier=("target" if perm[i] else tier))
                    for i, r in enumerate(use)]
        j, _, _ = loro_evaluate(shuffled, tier)
        if j == j and j >= observed:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def baseline_loro(rows, tier):
    """FerricIron1 alone, same folds, raw (no standardisation needed for a
    single monotone feature). The bar the model must clear to justify itself."""
    use = [r for r in rows if r["tier"] in ("target", tier)]
    regs = sorted({r["region"] for r in use})
    per = {}
    for held in regs:
        tr = [r for r in use if r["region"] != held]
        te = [r for r in use if r["region"] == held]
        trp = [r["x"][BASELINE] for r in tr if r["tier"] == "target"]
        trn = [r["x"][BASELINE] for r in tr if r["tier"] != "target"]
        tep = [r["x"][BASELINE] for r in te if r["tier"] == "target"]
        ten = [r["x"][BASELINE] for r in te if r["tier"] != "target"]
        if not (trp and trn and tep and ten):
            continue
        cut, _ = best_threshold(trp, trn)
        per[held] = j_at(tep, ten, cut)
    vals = [v for v in per.values() if v == v]
    return (min(vals) if vals else float("nan")), per


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sensor", default="S2", choices=["L8", "S2"])
    ap.add_argument("--inputs", default="")
    ap.add_argument("--perms", type=int, default=N_PERM)
    ap.add_argument("--model-perms", type=int, default=500)
    ap.add_argument("--out")
    a = ap.parse_args(argv)

    import glob
    paths = ([p for p in a.inputs.split(",") if p] or
             [p for p in glob.glob(os.path.join(OUTDIR, "seep_%s_*.csv"
                                                % a.sensor.lower()))
              if "nocloud" not in p and "sweep" not in p])
    rows = load_points(paths, a.sensor)
    rng = random.Random(SEED)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 86)
    say("B2c CONTINUOUS DETECTOR - PRE-REGISTERED (6af0b5b, before any fitting)")
    say("sensor=%s  radius=%dm  stat=%s  features=%d  model-perms=%d"
        % (a.sensor, PRIMARY_RADIUS, PRIMARY_STAT, len(FEATURES), a.model_perms))
    say("Rule: J>=%.2f vs C1+C2+C3b, BH p<0.05, AND beat FerricIron1 alone."
        % J_THRESHOLD)
    say("=" * 86)
    tiers = sorted({r["tier"] for r in rows if r["tier"] != "target"})
    say("n targets=%d  tiers present: %s"
        % (sum(1 for r in rows if r["tier"] == "target"),
           ", ".join("%s=%d" % (t, sum(1 for r in rows if r["tier"] == t))
                     for t in tiers)))
    say()

    say("--- C1 CHEMISTRY RELABELLING (EPA thresholds, pre-registered) ---")
    for g in sorted(REGIONS):
        c = {t: sum(1 for r in rows if r["region"] == g and r["tier"] == t)
             for t in ("C1clean", "C1dirty", "C1grey")}
        say("  %-16s clean=%-4d dirty=%-4d grey=%-4d"
            % (g, c["C1clean"], c["C1dirty"], c["C1grey"]))
    say("  ORIGINAL C1 (station-type) result stays in the record: J = 0.178")
    say()

    say("--- REPRODUCTION CHECK (must match prior runs before judging models) ---")
    for t in tiers:
        bj, bper = baseline_loro(rows, t)
        say("  FerricIron1 alone vs %-4s worst-case LORO J = %+.3f   %s"
            % (t, bj, " ".join("%s=%+.2f" % (g[:4], v)
                               for g, v in sorted(bper.items()))))
    say()

    results = []
    say("--- MODEL vs BASELINE, leave-one-region-out ---")
    say("  %-5s %8s %8s %9s %9s  %s"
        % ("tier", "model_J", "base_J", "perm_p", "BH_q", "per-region model J"))
    for t in tiers:
        mj, mper, coeffs = loro_evaluate(rows, t)
        bj, _ = baseline_loro(rows, t)
        p = model_perm_p(rows, t, mj, a.model_perms, rng)
        results.append(dict(tier=t, mj=mj, bj=bj, p=p, per=mper, coeffs=coeffs))
        say("  %-5s %8.3f %8.3f %9.4f %9s  %s"
            % (t, mj, bj, p, "-",
               " ".join("%s=%+.2f" % (g[:4], v) for g, v in sorted(mper.items()))))
    for r, q in zip(results, benjamini_hochberg([r["p"] for r in results])):
        r["q"] = q
    say()
    for r in results:
        say("  BH_q %-5s = %.4f" % (r["tier"], r["q"]))
    say()

    say("--- WHAT THE MODEL LEARNED (per-fold coefficients, standardised) ---")
    prim = next((r for r in results if r["tier"] == "C1"), results[0])
    say("  %-16s %s" % ("feature",
                        " ".join("%-8s" % g[:8] for g, _ in prim["coeffs"])))
    unstable = []
    for j, f in enumerate(FEATURES):
        vals = [w[j] for _, w in prim["coeffs"]]
        flag = "  <-- SIGN FLIPS" if (max(vals) > 0 > min(vals)) else ""
        if flag:
            unstable.append(f)
        say("  %-16s %s%s" % (f, " ".join("%+8.3f" % v for v in vals), flag))
    say()
    if unstable:
        say("  SIGN INSTABILITY in %d/%d features: %s"
            % (len(unstable), len(FEATURES), ", ".join(unstable)))
        say("  Reported, not smoothed - this is the diagnostic that exposed Arm A.")
    else:
        say("  All coefficient signs stable across folds.")
    say()

    say("--- DISCRIMINATING TEST: does the score track CHEMISTRY or MINING? ---")
    say("  C1dirty = contaminated streams that are NOT mine infrastructure.")
    prim_t = "C1clean"
    mj, _, coef = loro_evaluate(rows, prim_t)
    if coef:
        w = [sum(c[1][j] for c in coef) / len(coef) for j in range(len(FEATURES))]
        par = zscore_params(rows, sorted(REGIONS))
        for t in ("target", "C1clean", "C1dirty", "C1grey"):
            sub = [r for r in rows if r["tier"] == t]
            if not sub:
                continue
            sc = score(apply_z(sub, par), w, 0.0)
            sc.sort()
            say("  %-9s n=%-4d median score = %+.3f"
                % (t, len(sub), sc[len(sc) // 2]))
        say()
        say("  Registered prediction: if the dose-response result is real,")
        say("  C1dirty MUST score above C1clean.")
    say()

    say("--- LEAKAGE POSITIVE CONTROL (a deliberate leak MUST inflate J) ---")
    for t in tiers:
        clean, _, _ = loro_evaluate(rows, t)
        leaked, _, _ = loro_evaluate(rows, t, leak=True)
        ok = "as expected" if leaked > clean else "*** NO INFLATION - guard suspect ***"
        say("  %-5s clean J=%+.3f   leaked J=%+.3f   %s" % (t, clean, leaked, ok))
    say()

    dec = [r for r in results if r["tier"] in DECISION_TIERS]
    have = {r["tier"] for r in dec}
    missing = [t for t in DECISION_TIERS if t not in have]
    say("--- VERDICT (pre-registered vocabulary) ---")
    if missing:
        say("  tiers absent for this sensor: %s" % ", ".join(missing))
    passed = [r for r in dec
              if r["mj"] >= J_THRESHOLD and r["q"] < 0.05 and r["mj"] > r["bj"]]
    if not missing and len(passed) == len(DECISION_TIERS):
        verdict = "SUCCESS"
    elif any(r["mj"] >= 0.15 for r in dec):
        verdict = "PARTIAL"
    else:
        verdict = "NULL"
    say("  %s" % verdict)
    beat = [r["tier"] for r in dec if r["mj"] > r["bj"]]
    say("  model beats FerricIron1 alone on: %s"
        % (", ".join(beat) if beat else "NO TIER"))
    if not beat:
        say("  -> the multi-feature model is NOT worth its complexity;")
        say("     the honest finding is that one index, used continuously,")
        say("     is the detector.")
    if verdict == "NULL":
        say("  Reported as prominently as a success would be.")

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
