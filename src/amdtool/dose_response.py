"""Dose-response: does a satellite index track measured water chemistry?

Extracted 2026-09-14 from python/cmd_detect.run_analyse, where the computation,
the permutation test and the verdict were inline and existed only as printed
text. This returns data; formatting is the caller's job.

The algorithm is unchanged, including the ORDER in which the random number
generator is consumed: one Random(seed), iterated over indices x analytes in
the given order, shuffling within groups in order of first appearance. The
committed CMD1/CMD3 reports reproduce exactly only if that order is preserved.

Defaults reproduce the pre-registered CMD1 analysis. A host application
(SpectraLab) passes its own grouping and minimum group size.
"""

import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from amdtool.stats import benjamini_hochberg, spearman, variance_split

SEED = 20260814

VERDICT_UNINTERPRETABLE = "UNINTERPRETABLE"
VERDICT_SUCCESS = "SUCCESS"
VERDICT_PARTIAL = "PARTIAL"
VERDICT_NULL = "NULL"
VERDICT_NO_PAIRS = "NO_TESTABLE_PAIRS"


@dataclass
class PairResult:
    index: str
    analyte: str
    rho: float
    n: int
    p: float
    q: float = float("nan")
    per_group: Dict[str, float] = field(default_factory=dict)
    between_pct: float = float("nan")
    sign_consistent: bool = False


@dataclass
class DoseResponseResult:
    n_rows: int
    canopy_median_ndvi: float
    canopy_limit: Optional[float]
    canopy_limited: bool
    pairs: List[PairResult]
    verdict: str
    winners: List[PairResult]
    settings: dict

    def ranked(self):
        """Pairs by descending |rho| - the order the reports print."""
        return sorted(self.pairs, key=lambda d: -abs(d.rho))


def analyse(rows, indices, analytes=("Sulfate_mgL", "SpecificConductance"), *,
            stat="p90", group_key="region", n_perm=5000, seed=SEED,
            min_n=20, min_group_n=5, canopy_band="NDVI_stress_p90",
            canopy_limit=0.6, rho_bar=0.3, q_bar=0.05):
    """Spearman dose-response with a within-group permutation null.

    rows        dicts carrying '<index>_<stat>', each analyte, and group_key.
                Missing values must be float('nan') (amdtool.io.load_extracted
                does this).
    indices     index names to test, in order.
    analytes    chemistry columns to test, in order.
    canopy_limit  None skips the canopy gate (e.g. the metal-mine preset).

    Verdict, in the pre-registered precedence:
      UNINTERPRETABLE  canopy gate failed (median buffer NDVI above the limit);
      SUCCESS          some pair is sign-consistent AND BH q < q_bar AND
                       |rho| >= rho_bar;
      PARTIAL          some pair has BH q < q_bar;
      NULL             otherwise;
      NO_TESTABLE_PAIRS  no pair had >= min_n complete rows.
    """
    rng = random.Random(seed)
    settings = dict(indices=list(indices), analytes=list(analytes), stat=stat,
                    group_key=group_key, n_perm=n_perm, seed=seed, min_n=min_n,
                    min_group_n=min_group_n, canopy_band=canopy_band,
                    canopy_limit=canopy_limit, rho_bar=rho_bar, q_bar=q_bar)

    med_ndvi = float("nan")
    canopy_limited = False
    if canopy_limit is not None:
        ndvi = [r.get(canopy_band, float("nan")) for r in rows]
        ndvi = [v for v in ndvi if v == v]
        med_ndvi = statistics.median(ndvi) if ndvi else float("nan")
        canopy_limited = med_ndvi == med_ndvi and med_ndvi > canopy_limit

    res = []
    for idx in indices:
        for a in analytes:
            xs, ys, rg = [], [], []
            for r in rows:
                v = r.get("%s_%s" % (idx, stat), float("nan"))
                c = r.get(a, float("nan"))
                if v == v and c == c:
                    xs.append(v)
                    ys.append(c)
                    rg.append(r[group_key])
            if len(xs) < min_n:
                continue
            rho, n = spearman(xs, ys)
            if rho != rho:
                continue
            by = {}
            for i, g in enumerate(rg):
                by.setdefault(g, []).append(i)
            per = {}
            for g, ix in by.items():
                if len(ix) >= min_group_n:
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
            res.append(PairResult(index=idx, analyte=a, rho=rho, n=n, p=p,
                                  per_group=per,
                                  between_pct=100 * variance_split(ys, rg),
                                  sign_consistent=consistent))

    if not res:
        return DoseResponseResult(len(rows), med_ndvi, canopy_limit,
                                  canopy_limited, [], VERDICT_NO_PAIRS, [],
                                  settings)

    for r, q in zip(res, benjamini_hochberg([r.p for r in res])):
        r.q = q

    winners = [r for r in res
               if r.sign_consistent and r.q < q_bar and abs(r.rho) >= rho_bar]
    if canopy_limited:
        verdict = VERDICT_UNINTERPRETABLE
    elif winners:
        verdict = VERDICT_SUCCESS
    elif any(r.q < q_bar for r in res):
        verdict = VERDICT_PARTIAL
    else:
        verdict = VERDICT_NULL
    return DoseResponseResult(len(rows), med_ndvi, canopy_limit, canopy_limited,
                              res, verdict, winners, settings)
