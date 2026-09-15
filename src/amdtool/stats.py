"""Statistics shared by every amdtool analysis - one implementation each.

Consolidated 2026-09-14 from python/seep_detect.py (auc, best_threshold, j_at,
loro_worst_j, perm_p_within_region, benjamini_hochberg, variance_split,
spearman) and python/cmd_confound.py (partial_spearman, perm_p_within,
per_region, signs). Before this, Spearman existed in five modules and AUC in
five, with small differences.

THE BODIES BELOW ARE COPIED VERBATIM. Permutation p-values depend on the exact
sequence of RNG calls and float operations, and the refactor's behaviour-neutral
gate requires every committed validation/ report to reproduce exactly. Do not
"tidy" these functions without re-running that gate.

The exact binomial, McNemar, Wilson and Holm helpers are new, for the
blind-search test, and use only the standard library.

Everything is pure standard library except partial_spearman, which uses numpy.
"""

import math
import statistics


# ------------------------------------------------------------ detection

def auc(pos, neg):
    """Mann-Whitney U / (n1*n2), ties at 0.5."""
    if not pos or not neg:
        return float("nan")
    allv = sorted(pos + neg)
    n = len(allv)
    ranks, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2.0 + 1
        ranks[allv[i]] = r
        i = j + 1
    rp = sum(ranks[v] for v in pos)
    u = rp - len(pos) * (len(pos) + 1) / 2.0
    return u / (len(pos) * len(neg))


def best_threshold(pos, neg):
    """Threshold maximising Youden J (TPR - FPR) on the given sample."""
    if not pos or not neg:
        return float("nan"), float("nan")
    cuts = sorted(set(pos + neg))
    bj, bt = -2.0, float("nan")
    for c in cuts:
        tpr = sum(1 for v in pos if v >= c) / len(pos)
        fpr = sum(1 for v in neg if v >= c) / len(neg)
        if tpr - fpr > bj:
            bj, bt = tpr - fpr, c
    return bt, bj


def j_at(pos, neg, cut):
    if not pos or not neg or cut != cut:
        return float("nan")
    tpr = sum(1 for v in pos if v >= cut) / len(pos)
    fpr = sum(1 for v in neg if v >= cut) / len(neg)
    return tpr - fpr


def _prep_folds(scores, regions):
    """Precompute each LORO fold's score-descending index order ONCE.

    Scores never change under label permutation - only labels do - so the sort
    is loop-invariant. Hoisting it turns the O(n^2)-per-draw threshold search
    into a single O(n) sweep, which is what makes 10,000 permutations x 27
    tests finish in minutes instead of hours.
    """
    regs = sorted(set(regions))
    folds = {}
    for held in regs:
        tr = [i for i, r in enumerate(regions) if r != held]
        te = [i for i, r in enumerate(regions) if r == held]
        tr.sort(key=lambda i: -scores[i])
        te.sort(key=lambda i: -scores[i])
        folds[held] = (tr, te)
    return regs, folds


def _worst_j_fast(scores, labels, regs, folds):
    """Worst-case LORO Youden J via one descending sweep per fold."""
    worst, per = None, {}
    for held in regs:
        tr, te = folds[held]
        p_tr = sum(labels[i] for i in tr)
        n_tr = len(tr) - p_tr
        p_te = sum(labels[i] for i in te)
        n_te = len(te) - p_te
        if not (p_tr and n_tr and p_te and n_te):
            continue
        tp = fp = 0
        best_j, cut = -2.0, None
        for k, i in enumerate(tr):         # fit threshold on the OTHER regions
            if labels[i]:
                tp += 1
            else:
                fp += 1
            # DELIBERATE CHANGE from the committed sweep (audit 2026-09-15, item 9).
            # A `>=` cut cannot fall between two equal scores, so J is evaluated
            # only after the LAST member of a run of tied scores. Evaluating it
            # part-way through a tie made the chosen cut - and the held-out J -
            # depend on the order rows arrived in. Only tied scores are affected:
            # AMDclassFrac (18-95% tied) moved; the continuous indices did not.
            if k + 1 < len(tr) and scores[tr[k + 1]] == scores[i]:
                continue
            j = tp / p_tr - fp / n_tr
            if j > best_j:
                best_j, cut = j, scores[i]
        tp = fp = 0
        for i in te:                       # apply it to the held-out region
            if scores[i] >= cut:
                if labels[i]:
                    tp += 1
                else:
                    fp += 1
        jt = tp / p_te - fp / n_te
        per[held] = jt
        worst = jt if worst is None else min(worst, jt)
    return (worst if worst is not None else float("nan")), per


def loro_worst_j(scores, labels, regions):
    """Worst-case leave-one-REGION-out Youden J.

    THE criterion, per the pre-registration. Fit the threshold on every region
    except one, apply it to the held-out region, keep the worst fold. Pooled
    or within-region J is reported alongside but is NOT the criterion - Test C
    scored 0.99 within-site and 0.63 across sites, which is exactly the failure
    mode this guards against.
    """
    if len(set(regions)) < 2:
        return float("nan"), {}
    regs, folds = _prep_folds(scores, regions)
    return _worst_j_fast(scores, labels, regs, folds)


def perm_p_within_region(scores, labels, regions, observed, n_perm, rng):
    """One-sided p from shuffling labels WITHIN region only.

    Never across regions: source points cluster spatially and regions differ in
    geology, illumination and scene availability, so a global shuffle destroys
    the blocking and inflates significance.
    """
    if observed != observed:
        return float("nan")
    by = {}
    for i, r in enumerate(regions):
        by.setdefault(r, []).append(i)
    regs, folds = _prep_folds(scores, regions)
    lab = list(labels)
    perm = list(lab)
    hits = 0
    for _ in range(n_perm):
        for idx in by.values():
            sub = [lab[i] for i in idx]
            rng.shuffle(sub)
            for i, v in zip(idx, sub):
                perm[i] = v
        j, _ = _worst_j_fast(scores, perm, regs, folds)
        if j == j and j >= observed:
            hits += 1
    return (hits + 1) / (n_perm + 1)


# ------------------------------------------------------------ correlation

def benjamini_hochberg(pvals):
    """Return the BH-adjusted p-values, order preserved."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [1.0] * m
    prev = 1.0
    for rank, i in enumerate(reversed(idx), 1):
        k = m - rank + 1
        prev = min(prev, pvals[i] * m / k)
        adj[i] = prev
    return adj


def variance_split(values, regions):
    """Fraction of total variance that is BETWEEN regions.

    Mandatory next to any pooled correlation here: the pooled sulfate result
    reversed sign once 67.5%-between-region structure was removed.
    """
    vals = [(v, r) for v, r in zip(values, regions) if v == v]
    if len(vals) < 3:
        return float("nan")
    grand = statistics.mean(v for v, _ in vals)
    by = {}
    for v, r in vals:
        by.setdefault(r, []).append(v)
    ss_b = sum(len(g) * (statistics.mean(g) - grand) ** 2 for g in by.values())
    ss_t = sum((v - grand) ** 2 for v, _ in vals)
    return ss_b / ss_t if ss_t else float("nan")


def spearman(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a == a and b == b]
    if len(pairs) < 4:
        return float("nan"), len(pairs)
    def rank(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and a[order[j + 1]] == a[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    n = len(pairs)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return (num / den if den else float("nan")), n


def _rank(v):
    import numpy as np
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return np.asarray(out)


def partial_spearman(x, y, z):
    """Spearman rho of x vs y with z removed, on ranks.

    Residualise rank(x) and rank(y) on rank(z) by least squares, then correlate
    the residuals. This is the rank analogue of a partial correlation and is
    what the pre-registration fixed as the primary statistic.
    """
    import numpy as np
    rx, ry, rz = _rank(x), _rank(y), _rank(z)
    A = np.column_stack([rz, np.ones(len(rz))])
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    sx, sy = ex.std(), ey.std()
    # DELIBERATE CHANGE from the verbatim copy (2026-09-14, audit item 7).
    # The original guard was `sx == 0 or sy == 0`. When rank(z) explains rank(x)
    # or rank(y) exactly, least squares leaves residuals at floating-point noise
    # level - small but not exactly zero - so the guard never fired and this
    # returned noise divided by noise: 11.97 on a constructed case, a
    # "correlation" far outside [-1, 1]. Compare against the spread of the ranks
    # themselves instead. For any real data this threshold is many orders of
    # magnitude below the residual spread, so no committed number changes;
    # tests/test_golden.py verifies that for CMD2.
    tol = 1e-9 * max(float(rx.std()), float(ry.std()), 1.0)
    if sx <= tol or sy <= tol:
        return float("nan")
    return float((ex * ey).mean() / (sx * sy))


def perm_p_within(x, y, z, regions, observed, n_perm, rng):
    """Shuffle y WITHIN watershed; z travels with the station, not with y.

    This is the null that destroyed the pooled Colorado sulfate claim and that
    Arm B2 passed. Keeping z attached to the station is the point: it asks
    whether the x-y link survives at equal mining extent, not whether the
    triple is jointly random.
    """
    by = {}
    for i, g in enumerate(regions):
        by.setdefault(g, []).append(i)
    hits = 0
    for _ in range(n_perm):
        yp = list(y)
        for ix in by.values():
            sub = [y[i] for i in ix]
            rng.shuffle(sub)
            for i, v in zip(ix, sub):
                yp[i] = v
        r = partial_spearman(x, yp, z)
        if r == r and abs(r) >= abs(observed):
            hits += 1
    return (hits + 1) / (n_perm + 1)


def per_region(x, y, regions, z=None, minn=5):
    by = {}
    for i, g in enumerate(regions):
        by.setdefault(g, []).append(i)
    out = {}
    for g, ix in by.items():
        if len(ix) < minn:
            continue
        xs, ys = [x[i] for i in ix], [y[i] for i in ix]
        if z is None:
            out[g] = spearman(xs, ys)[0]
        else:
            out[g] = partial_spearman(xs, ys, [z[i] for i in ix])
    return out


def signs(per):
    v = [s for s in per.values() if s == s]
    return v, bool(v) and (all(s > 0 for s in v) or all(s < 0 for s in v))


# ------------------------------------------------------------ blind search
# New 2026-09-14. Exact, standard library only, so the registered test does not
# depend on a SciPy version.

Z_95 = 1.959963984540054


def binomial_sf_ge(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p). Exact."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x)
               for x in range(k, n + 1))


def binomial_test_greater(k, n, p0):
    """One-sided exact p for H1: success probability > p0."""
    if n <= 0:
        return float("nan")
    return binomial_sf_ge(k, n, p0)


def mcnemar_exact_greater(b, c):
    """One-sided exact McNemar for H1: condition B flags more than C.

    b = pairs flagged by B only, c = pairs flagged by C only. Concordant pairs
    carry no information. Returns 1.0 when there are no discordant pairs.
    """
    m = b + c
    if m == 0:
        return 1.0
    return binomial_sf_ge(b, m, 0.5)


def wilson_interval(k, n, z=Z_95):
    """Wilson score interval for a proportion k/n."""
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def holm(pvals, alpha=0.05):
    """Holm step-down. Returns (reject flags, adjusted p), in input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    reject = [False] * m
    adjusted = [1.0] * m
    running = 0.0
    still_rejecting = True
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adjusted[i] = running
        if still_rejecting and pvals[i] <= alpha / (m - rank):
            reject[i] = True
        else:
            still_rejecting = False
    return reject, adjusted
