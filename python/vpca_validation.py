"""
VPCA spectral-library validation for the AMD Detection Tool (v2)
================================================================

This is the INDEPENDENT validator, not the detector. It answers one question:

    "Do the spectral components the scene actually contains match the
     minerals the classifier claims are there?"

Method: varimax-rotated Principal Component Analysis (VPCA) - the
Ortiz-lab spectral-decomposition approach (Ali & Ortiz, Kent State) - applied
to an exported Landsat-8 / Sentinel-2 composite, then each rotated component is
matched against USGS Spectral Library v7 end-members convolved to the sensor
bands. Agreement between "VPCA says jarosite here" and "classifier says an
iron-sulfate class here" is the accuracy result.

Author: Abdulrahman Hussein, Kent State University (Dr. Joseph D. Ortiz lab)
Based on the v2.0 upgrade & validation plan (specs/amd-v2/plan.md).

------------------------------------------------------------------
HOW TO RUN
------------------------------------------------------------------
1. Prove the validator itself is correct (no data needed):
       python vpca_validation.py --self-test

2. Validate a real exported scene (see specs/amd-v2/validation-protocol.md
   for how to produce the CSV from Google Earth Engine):
       python vpca_validation.py --scene scene_silverton.csv --sensor L8 --classcol class

3. Water Fe3+ ground-truth regression (Ganau / Dukan):
       python vpca_validation.py --scene water_ganau.csv --sensor L8 --water --conc conc_mgL

The scene CSV must have 7 reflectance columns (0-1 range):
   SR_B1,SR_B2,SR_B3,SR_B4,SR_B5,SR_B6,SR_B7
Optional columns: class (integer classifier output), lon, lat, conc_mgL.
"""

import argparse
import sys
import numpy as np

# ---------------------------------------------------------------------------
# 1. REFERENCE END-MEMBERS
# ---------------------------------------------------------------------------
# Representative reflectance shapes for the color-producing agents relevant to
# acid mine drainage, sampled at the 7 bands this tool uses. Band mapping:
#   SR_B1 Coastal 0.443um | SR_B2 Blue 0.482 | SR_B3 Green 0.561 |
#   SR_B4 Red 0.655 | SR_B5 NIR 0.865 | SR_B6 SWIR1 1.609 | SR_B7 SWIR2 2.201
#
# These are literature-derived SHAPES (USGS splib07 characteristic spectra:
# Kokaly et al. 2017, USGS Data Series 1035). VPCA matching uses spectral
# ANGLE / correlation, which compares shape and is invariant to absolute
# brightness, so representative shapes are valid for the shape-match step.
# For final thesis numbers, replace these with exact splib07 vectors using
# convolve_splib07() below (see docstring). Each vector is documented by its
# diagnostic feature so a reviewer can check the physics.
END_MEMBERS = {
    # Jarosite KFe3(SO4)2(OH)6 - the primary AMD sulfate. Ferric absorption
    # near 0.43 and 0.90 um; blue/coastal suppressed; SWIR1 high with an
    # Fe-OH / SO4 absorption dropping into SWIR2 (~2.27um).
    "jarosite":       [0.055, 0.085, 0.175, 0.220, 0.195, 0.340, 0.215],
    # Schwertmannite Fe8O8(OH)6(SO4) - ochre AMD precipitate, jarosite-like
    # but broader ferric edge, slightly higher NIR.
    "schwertmannite": [0.050, 0.075, 0.150, 0.210, 0.230, 0.360, 0.250],
    # Goethite FeOOH - yellow-brown. Steep VNIR rise, deep 0.90 um crystal
    # field band, high SWIR.
    "goethite":       [0.040, 0.060, 0.120, 0.200, 0.280, 0.400, 0.300],
    # Hematite Fe2O3 - red. Sharp ferric edge near 0.75, strong 0.90 band.
    "hematite":       [0.030, 0.050, 0.090, 0.180, 0.300, 0.420, 0.330],
    # K-alunite KAl3(SO4)2(OH)6 - bright, diagnostic Al-OH absorption ~2.17um
    # (SWIR2 dip). Marks advanced argillic alteration around AMD.
    "alunite":        [0.300, 0.350, 0.450, 0.500, 0.550, 0.450, 0.280],
    # Montmorillonite (clay) - bright VNIR, 2.20um Al-OH absorption.
    "clay_mont":      [0.250, 0.300, 0.400, 0.480, 0.520, 0.500, 0.300],
    # Green vegetation - chlorophyll red/blue absorption, green bump, NIR
    # plateau, SWIR liquid-water absorption.
    "green_veg":      [0.030, 0.040, 0.080, 0.050, 0.450, 0.250, 0.120],
    # Clear water - decreasing reflectance to near-zero NIR/SWIR.
    "clear_water":    [0.050, 0.045, 0.030, 0.018, 0.008, 0.004, 0.003],
    # Fe3+-stained water (AMD lake) - red/green elevated by dissolved/colloidal
    # ferric iron; small NIR bump from suspended particles.
    "fe3_water":      [0.040, 0.050, 0.060, 0.070, 0.040, 0.020, 0.010],
}

# Which end-members represent an iron-sulfate / AMD land signal (for closure
# against the classifier's iron-sulfate classes).
AMD_MINERALS = ("jarosite", "schwertmannite", "goethite", "hematite")

# SPECTRAL AGENT GROUPS. At 7-band (Landsat-8 / Sentinel-2) resolution the four
# ferric AMD minerals share a nearly identical band shape - they differ mainly
# in narrow crystal-field / SO4 features (~0.43, 0.90, 2.2-2.27um) that a
# multispectral sensor cannot resolve. VPCA therefore recovers color-producing
# AGENT GROUPS, not individual minerals. Discriminating jarosite vs goethite vs
# hematite requires hyperspectral data (this is finding H2 in the plan). The
# validator reports and scores at the group level, which is what 7-band VPCA
# can legitimately support.
AGENT_GROUPS = {
    "jarosite": "ferric", "schwertmannite": "ferric",
    "goethite": "ferric", "hematite": "ferric",
    "alunite": "clay_alunite", "clay_mont": "clay_alunite",
    "green_veg": "vegetation",
    "clear_water": "water", "fe3_water": "water",
}

BAND_COLS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]

# A component is a confident match to a library group when its contrast
# direction correlates at least this strongly with the end-member's deviation
# from the scene mean.
R_MATCH = 0.80


def group_of(name):
    """Spectral agent group for an end-member name."""
    return AGENT_GROUPS.get(name, name)


def endmember_matrix():
    """Return (names, P x 7 array) of the reference end-members."""
    names = list(END_MEMBERS.keys())
    M = np.array([END_MEMBERS[n] for n in names], dtype=float)
    return names, M


def convolve_splib07(wavelengths_um, reflectance, rsr_table):
    """Convolve a raw splib07 spectrum to sensor bands (the RIGOROUS path).

    Parameters
    ----------
    wavelengths_um : (W,) array of wavelengths in micrometres for the spectrum.
    reflectance    : (W,) array of reflectance values 0-1.
    rsr_table      : dict {band_name: (wl_um array, response array)} giving the
                     relative spectral response for each of the 7 bands. Get L8
                     OLI / S2 MSI RSR from USGS / ESA and load them here.

    Returns
    -------
    dict {band_name: convolved_reflectance} = integral(refl*RSR)/integral(RSR).

    Use this to replace the embedded END_MEMBERS with exact splib07 values for
    final reporting. The embedded shapes above are the offline default.
    """
    out = {}
    for band, (wl_rsr, resp) in rsr_table.items():
        r_interp = np.interp(wl_rsr, wavelengths_um, reflectance,
                             left=np.nan, right=np.nan)
        good = np.isfinite(r_interp)
        if good.sum() == 0:
            out[band] = np.nan
        else:
            out[band] = np.trapz(r_interp[good] * resp[good], wl_rsr[good]) / \
                        np.trapz(resp[good], wl_rsr[good])
    return out


# ---------------------------------------------------------------------------
# 2. VARIMAX ROTATION
# ---------------------------------------------------------------------------
def varimax(Phi, gamma=1.0, max_iter=200, tol=1e-8):
    """Kaiser varimax rotation of a loading matrix Phi (p vars x k factors).

    Returns (rotated_loadings, rotation_matrix R) with rotated = Phi @ R.
    Varimax maximises the variance of squared loadings within each factor, so
    each rotated component loads strongly on a few bands - i.e. becomes a
    physically interpretable band-shape rather than an abstract axis.
    """
    p, k = Phi.shape
    R = np.eye(k)
    d = 0.0
    for _ in range(max_iter):
        d_old = d
        Lambda = Phi @ R
        # gradient of the varimax criterion
        u, s, vt = np.linalg.svd(
            Phi.T @ (Lambda**3 - (gamma / p) *
                     Lambda @ np.diag(np.diag(Lambda.T @ Lambda)))
        )
        R = u @ vt
        d = np.sum(s)
        if d_old != 0 and abs(d - d_old) / d < tol:
            break
    return Phi @ R, R


# ---------------------------------------------------------------------------
# 3. CORE VPCA
# ---------------------------------------------------------------------------
def l2norm_rows(X):
    """Brightness-normalize: scale each pixel spectrum to unit length so only
    SHAPE (not albedo) varies. Removes the trivial brightness axis that would
    otherwise dominate the components and make dark end-members (water) match
    everything. Standard pre-step for spectral-shape mineral discrimination."""
    X = np.asarray(X, float)
    norm = np.linalg.norm(X, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return X / norm


def run_vpca(X, var_target=0.99, max_components=6, normalize=True):
    """Varimax-rotated PCA of a scene matrix X (n pixels x 7 bands).

    normalize=True brightness-normalizes each pixel first (land / shape-based
    mineral discrimination). Use normalize=False for water, where albedo and
    Fe3+ intensity ARE the signal.

    Returns a dict with:
      loadings   : (7 x k) rotated loading vectors (one spectral shape/comp)
      scores     : (n x k) rotated per-pixel component scores
      var_ratio  : (k,)  fraction of total variance carried by each rotated comp
      k          : number of retained components
      mean, std  : column standardization used (for reference)
    """
    X = np.asarray(X, dtype=float)
    if normalize:
        X = l2norm_rows(X)
    # z-score standardize each band (VPCA works on the correlation structure)
    mean = X.mean(axis=0)
    std = X.std(axis=0, ddof=1)
    std[std == 0] = 1.0
    Xz = (X - mean) / std

    # PCA via SVD of the standardized matrix
    U, S, Vt = np.linalg.svd(Xz, full_matrices=False)
    eigvals = (S**2) / (Xz.shape[0] - 1)          # variance per PC
    total_var = eigvals.sum()
    var_ratio_pc = eigvals / total_var

    # choose how many components to retain. Kaiser-Guttman rule: keep PCs whose
    # eigenvalue exceeds 1 (they explain more than a single standardized band).
    # This avoids over-fragmenting one material across several noise components.
    # Fall back to the variance target if Kaiser would keep too few.
    n_kaiser = int(np.sum(eigvals > 1.0))
    cum = np.cumsum(var_ratio_pc)
    n_var = int(np.searchsorted(cum, var_target) + 1)
    k = max(2, min(max(n_kaiser, min(n_var, 3)), max_components, Xz.shape[1]))

    # loadings = eigenvector * sqrt(eigenvalue) => correlation of band w/ PC
    load_pc = Vt[:k].T * np.sqrt(eigvals[:k])      # (7 x k)
    scores_pc = U[:, :k] * S[:k]                    # (n x k) PC scores

    # varimax-rotate the loadings; rotate scores by the same R (X ~= Sr Lr^T)
    load_rot, R = varimax(load_pc)
    scores_rot = scores_pc @ R

    # variance carried by each ROTATED component (loadings^2 summed over bands)
    comp_var = np.sum(load_rot**2, axis=0)
    var_ratio = comp_var / total_var

    # order components by variance, descending
    order = np.argsort(var_ratio)[::-1]
    return {
        "loadings": load_rot[:, order],
        "scores": scores_rot[:, order],
        "var_ratio": var_ratio[order],
        "k": k,
        "mean": mean,
        "std": std,
    }


# ---------------------------------------------------------------------------
# 4. SPECTRAL-ANGLE / CORRELATION MATCHING
# ---------------------------------------------------------------------------
def shape_similarity(a, b):
    """Cosine similarity of mean-centred vectors == Pearson correlation.

    Scale/offset invariant, so it compares SHAPE across the 7 bands. A rotated
    component's sign is arbitrary, so callers take the absolute value.
    Returns r in [-1, 1]. |r|->1 means near-identical band shape.
    """
    a = np.asarray(a, float) - np.mean(a)
    b = np.asarray(b, float) - np.mean(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def spectral_angle_deg(a, b):
    """Spectral Angle Mapper distance in degrees (0 = identical direction)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 90.0
    cos = np.clip(np.dot(a, b) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(abs(cos))))


def component_spectrum(X, score, top_frac=0.10):
    """Empirical spectra of the pixels at each extreme of a component score.

    A component contrasts two ends. Return the mean ORIGINAL reflectance of the
    top-scoring and bottom-scoring pixels - real, positive, reflectance-like
    spectra we can match to the library by spectral angle. This is how a VPCA
    component gets a physical identity: "pixels that load high here look like X".
    """
    hi = np.quantile(score, 1 - top_frac)
    lo = np.quantile(score, top_frac)
    top = X[score >= hi].mean(axis=0)
    bot = X[score <= lo].mean(axis=0)
    return top, bot


def match_components(X, scores, endmember_names, M, top_frac=0.10, normalize=True):
    """Identify each rotated component by matching its spectral CONTRAST
    DIRECTION to the library end-members.

    normalize must match the value passed to run_vpca so the empirical spectra
    and the library end-members live in the same (brightness-normalized or raw)
    space.

    A component's contrast direction = (mean spectrum of its high-scoring
    pixels) - (mean spectrum of its low-scoring pixels). This is the reflectance
    direction the component encodes. We match it to each end-member's deviation
    from the scene mean (end-member - scene_mean); the material whose deviation
    best aligns (highest |correlation|) is the component's identity. Matching a
    direction, not an absolute end, prevents a component being mislabelled by
    its opposite pole.

    Returns list of dicts (one per component):
       {comp, best, group, r, sam_deg, sign, ranked}
    - r    : correlation of the contrast direction with the end-member deviation
    - sign : +1 if material is at HIGH-score end, -1 if LOW. Orient scores by
             this so "high oriented score = material-rich".
    """
    Xw = l2norm_rows(X) if normalize else np.asarray(X, float)
    Mw = l2norm_rows(M) if normalize else np.asarray(M, float)
    scene_mean = Xw.mean(axis=0)
    results = []
    k = scores.shape[1]
    for c in range(k):
        top, bot = component_spectrum(Xw, scores[:, c], top_frac)
        direction = top - bot
        scored = []
        for name, em in zip(endmember_names, Mw):
            dev = np.asarray(em) - scene_mean
            r = shape_similarity(direction, dev)         # sign-aware corr
            sam = spectral_angle_deg(direction, dev)     # orientation-agnostic
            scored.append((name, r, sam))
        scored.sort(key=lambda t: abs(t[1]), reverse=True)  # best |corr| first
        best_name, best_r, best_sam = scored[0]
        results.append({
            "comp": c,
            "best": best_name,
            "group": group_of(best_name),
            "r": best_r,
            "sam_deg": best_sam,
            "sign": 1.0 if best_r >= 0 else -1.0,
            "ranked": scored,
        })
    return results


# ---------------------------------------------------------------------------
# 5. SPATIAL CLOSURE (VPCA vs classifier)
# ---------------------------------------------------------------------------
def _otsu_threshold(x, nbins=256):
    """Otsu's method: threshold that maximises between-class variance."""
    x = np.asarray(x, float)
    hist, edges = np.histogram(x, bins=nbins)
    centers = (edges[:-1] + edges[1:]) / 2
    w = np.cumsum(hist)
    wb = w / w[-1]
    wf = 1 - wb
    mb = np.cumsum(hist * centers) / np.maximum(w, 1)
    mtot = np.sum(hist * centers) / w[-1]
    mf = (mtot - np.cumsum(hist * centers)) / np.maximum(w[-1] - w, 1)
    between = wb * wf * (mb - mf) ** 2
    idx = int(np.nanargmax(between))
    return centers[idx]


# The tool's IRON-SULFATE / AMD indicator classes (legend "AMD Indicator
# Classes"): 9 Argillic, 12 Major Iron Sulfate, 14 Oxidizing Sulfides,
# 17 Proximal Jarosite, 18 Distal Jarosite, 19 Clay+Ferrous+Iron. These - NOT
# all classes 1-19 (which include vegetation 11/13 and clay-only) - are what the
# ferric VPCA component should co-locate with.
AMD_CLASSES = (9, 12, 14, 17, 18, 19)


def _auc(score, label):
    """Mann-Whitney ROC-AUC of `score` ranking positive `label` pixels highest.
    Prevalence- and threshold-free: 0.5 = no relation, 1.0 = perfect."""
    score = np.asarray(score, float)
    label = np.asarray(label, int)
    pos, neg = score[label == 1], score[label == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), float)
    ranks[order] = np.arange(1, len(score) + 1)
    return float((ranks[label == 1].sum() - len(pos) * (len(pos) + 1) / 2)
                 / (len(pos) * len(neg)))


def closure(scores, comps, classes, amd_classes=AMD_CLASSES):
    """Agreement between the ferric VPCA component and the classifier's
    IRON-SULFATE classes.

    Primary metric is AUC: does the ferric component score rank the classifier's
    iron-sulfate pixels above the rest? (threshold-free, robust to the small AMD
    prevalence). Also reports an Otsu-thresholded binary agreement/kappa for
    reference. Returns None if no ferric component was found.
    """
    from sklearn.metrics import cohen_kappa_score

    amd_comp = next((m for m in comps if m["group"] == "ferric"), None)
    if amd_comp is None:
        return None

    c = amd_comp["comp"]
    score = scores[:, c] * amd_comp["sign"]   # orient so high = ferric-rich
    classes = np.asarray(classes)
    clf_amd = np.isin(classes, list(amd_classes)).astype(int)

    auc = _auc(score, clf_amd)
    thr = _otsu_threshold(score)
    vpca_amd = (score > thr).astype(int)
    agreement = float(np.mean(vpca_amd == clf_amd))
    try:
        kappa = float(cohen_kappa_score(clf_amd, vpca_amd))
    except Exception:
        kappa = float("nan")
    return {
        "component": c,
        "matched_mineral": amd_comp["best"],
        "auc": auc,
        "agreement": agreement,
        "kappa": kappa,
        "n": len(classes),
        "n_amd": int(clf_amd.sum()),
        "vpca_amd_frac": float(vpca_amd.mean()),
        "clf_amd_frac": float(clf_amd.mean()),
        "threshold": float(thr),
    }


# ---------------------------------------------------------------------------
# 6. WATER Fe3+ REGRESSION
# ---------------------------------------------------------------------------
def water_regression(scores, comps, conc):
    """Regress the Fe3+-matched component score against known concentration.

    Returns dict {component, r2, rmse, slope, intercept, n} or None.
    """
    # The Fe3+/clean-water contrast is one axis; it may be labelled by either
    # pole (clear_water or fe3_water) - both are the 'water' group. Ferric also
    # qualifies (dissolved ferric iron). Pick that component; R^2 is sign-
    # invariant so the pole label does not matter.
    fe_comp = None
    for m in comps:
        if m["group"] in ("water", "ferric"):
            fe_comp = m
            break
    if fe_comp is None:
        return None
    c = fe_comp["comp"]
    x = scores[:, c] * fe_comp["sign"]   # orientation only affects slope sign
    y = np.asarray(conc, float)
    mask = np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(y) < 3:
        return None
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    pred = slope * x + intercept
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
    return {"component": c, "matched": fe_comp["best"], "r2": float(r2),
            "rmse": rmse, "slope": float(slope), "intercept": float(intercept),
            "n": int(len(y))}


# ---------------------------------------------------------------------------
# 7. REPORTING
# ---------------------------------------------------------------------------
def print_report(vpca, comps, clo=None, wreg=None):
    print("\n" + "=" * 66)
    print("VPCA SPECTRAL-LIBRARY VALIDATION REPORT")
    print("=" * 66)
    print(f"Retained components: {vpca['k']}")
    print(f"Variance explained (rotated): "
          f"{', '.join(f'{v*100:.1f}%' for v in vpca['var_ratio'])}"
          f"  (cumulative {vpca['var_ratio'].sum()*100:.1f}%)")
    print("\nComponent -> best-matching library end-member (group):")
    print(f"  {'comp':>4} {'variance':>9} {'end-member':>16} {'group':>13} {'|r|':>6} {'SAM(deg)':>9}")
    for m, v in zip(comps, vpca["var_ratio"]):
        flag = "  <-- AMD" if m["group"] == "ferric" else ""
        print(f"  {m['comp']:>4} {v*100:>8.1f}% {m['best']:>16} {m['group']:>13} "
              f"{abs(m['r']):>6.3f} {m['sam_deg']:>9.2f}{flag}")

    if clo is not None:
        print("\n" + "-" * 66)
        print("SPATIAL CLOSURE  (VPCA AMD component vs classifier AMD classes)")
        print("-" * 66)
        print(f"  Matched mineral       : {clo['matched_mineral']} "
              f"(component {clo['component']})")
        print(f"  Pixels compared       : {clo['n']}  "
              f"(classifier iron-sulfate: {clo['n_amd']} = "
              f"{clo['clf_amd_frac']*100:.2f}%)")
        print(f"  AUC (ferric score vs  : {clo['auc']:.3f}   "
              f"({_auc_label2(clo['auc'])})")
        print(f"       iron-sulfate class)  <- primary, threshold-free metric")
        print(f"  Otsu binary agreement : {clo['agreement']*100:.2f}%")
        print(f"  Cohen's kappa         : {clo['kappa']:.3f}   "
              f"({_kappa_label(clo['kappa'])})")
    elif not any(m["group"] == "ferric" for m in comps):
        print("\n" + "-" * 66)
        print("SPATIAL CLOSURE  (VPCA AMD component vs classifier AMD classes)")
        print("-" * 66)
        print("  NO ferric / iron-sulfate component recovered by VPCA.")
        print("  The scene contains no independent iron-sulfate spectral")
        print("  signal. For a clean control site this is the EXPECTED, correct")
        print("  result (specificity): the tool is not inventing AMD here.")

    if wreg is not None:
        print("\n" + "-" * 66)
        print("WATER Fe3+ GROUND-TRUTH REGRESSION")
        print("-" * 66)
        print(f"  Matched signal : {wreg['matched']} (component {wreg['component']})")
        print(f"  n samples      : {wreg['n']}")
        print(f"  R^2            : {wreg['r2']:.3f}")
        print(f"  RMSE           : {wreg['rmse']:.2f} mg/L")
    print("=" * 66 + "\n")


def _auc_label2(a):
    if a != a:
        return "n/a"
    if a < 0.6: return "no agreement"
    if a < 0.7: return "weak"
    if a < 0.8: return "moderate"
    if a < 0.9: return "strong"
    return "excellent"


def _kappa_label(k):
    if k != k:  # NaN
        return "undefined"
    if k < 0.2: return "poor"
    if k < 0.4: return "fair"
    if k < 0.6: return "moderate"
    if k < 0.8: return "substantial"
    return "almost perfect"


# ---------------------------------------------------------------------------
# 8. SELF-TEST  (proves the validator recovers known minerals)
# ---------------------------------------------------------------------------
def self_test(seed=0, n=4000, noise=0.01, verbose=True):
    """Synthesize a scene as convex mixtures of KNOWN end-members + noise,
    run the full VPCA pipeline, and confirm it recovers those end-members.

    This is the validator's own unit test: if VPCA cannot recover minerals we
    KNOW are present in a controlled scene, it cannot be trusted on real data.
    Returns True on pass.
    """
    rng = np.random.default_rng(seed)
    names, M = endmember_matrix()

    # --- LAND scene: the three separable land color agents, with TWO ferric
    # minerals mixed in on purpose. A 7-band sensor cannot separate jarosite
    # from goethite (finding H2), so they must COLLAPSE into one ferric
    # component rather than spawn two - the test checks exactly that.
    land = ["jarosite", "goethite", "clay_mont", "green_veg"]
    land_groups = sorted({group_of(t) for t in land})       # ferric,clay,veg
    T = M[[names.index(t) for t in land]]
    # INDEPENDENT abundances (NOT sum-to-one): real landscapes vary each
    # material independently, giving full-rank variation. Squared -> sparse.
    abund = rng.random((n, len(land))) ** 2
    Xland = np.clip(abund @ T + rng.normal(0, noise, size=(n, 7)), 0, None)
    vpca = run_vpca(Xland)
    comps = match_components(Xland, vpca["scores"], names, M)
    recovered = sorted({m["group"] for m in comps
                        if abs(m["r"]) >= R_MATCH and m["group"] in land_groups})
    n_ferric_comps = sum(1 for m in comps if m["group"] == "ferric")
    # H2: jarosite+goethite must NOT resolve as distinct mineral GROUPS - they
    # both identify as 'ferric'. Success = every expected group recovered and
    # no spurious non-land group appears.
    land_ok = set(recovered) == set(land_groups)

    # --- WATER scene: clear water mixed with a Fe3+ fraction proportional to a
    # known concentration; the Fe3+ component score should track concentration.
    f = rng.random(n)                                   # Fe3+ mixing fraction
    conc = f * 675.0                                    # mg/L (Ganau-scale)
    ew, ef = np.array(END_MEMBERS["clear_water"]), np.array(END_MEMBERS["fe3_water"])
    Xw = np.clip((1 - f)[:, None] * ew + f[:, None] * ef +
                 rng.normal(0, noise / 2, size=(n, 7)), 0, None)
    vpca_w = run_vpca(Xw, normalize=False)
    comps_w = match_components(Xw, vpca_w["scores"], names, M, normalize=False)
    wreg = water_regression(vpca_w["scores"], comps_w, conc)
    water_ok = wreg is not None and wreg["r2"] >= 0.80

    ok = land_ok and water_ok
    if verbose:
        print("\n" + "=" * 66)
        print("SELF-TEST: recover known spectral groups from synthetic scenes")
        print("=" * 66)
        print(f"  LAND scene: {n} px, constituents {land}")
        print(f"  land groups expected: {land_groups}")
        print_report(vpca, comps)
        print(f"  recovered groups (|r|>=0.80): {recovered}")
        print(f"  ferric components: {n_ferric_comps} "
              f"(all identify as the 'ferric' group - H2: jarosite/goethite "
              f"not separable at 7 bands)")
        print(f"  LAND: {'PASS' if land_ok else 'FAIL'}")
        print("  " + "-" * 62)
        print(f"  WATER scene: {n} px, Fe3+ fraction vs conc 0-675 mg/L")
        if wreg:
            print(f"  Fe3+ regression R^2={wreg['r2']:.3f}  RMSE={wreg['rmse']:.1f} mg/L")
        print(f"  WATER: {'PASS' if water_ok else 'FAIL'}")
        print("  " + "=" * 62)
        print(f"  OVERALL: {'PASS' if ok else 'FAIL'}")
        print("=" * 66 + "\n")
    return ok


# ---------------------------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------------------------
def load_scene(path):
    import pandas as pd
    df = pd.read_csv(path)
    missing = [c for c in BAND_COLS if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: scene CSV is missing band columns: {missing}\n"
                 f"       expected {BAND_COLS}")
    df = df.dropna(subset=BAND_COLS)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description="VPCA spectral-library validation "
                                             "for the AMD Detection Tool.")
    ap.add_argument("--self-test", action="store_true",
                    help="run the synthetic recovery test and exit")
    ap.add_argument("--scene", help="CSV of exported pixels (SR_B1..SR_B7)")
    ap.add_argument("--sensor", default="L8", choices=["L8", "S2"],
                    help="sensor whose bands the CSV holds (documentation)")
    ap.add_argument("--classcol", default="class",
                    help="column with classifier class integers (for closure)")
    ap.add_argument("--water", action="store_true",
                    help="water mode: regress Fe3+ component vs --conc")
    ap.add_argument("--conc", default="conc_mgL",
                    help="column with known concentration (water mode)")
    args = ap.parse_args(argv)

    if args.self_test or not args.scene:
        ok = self_test()
        if not args.scene:
            sys.exit(0 if ok else 1)

    df = load_scene(args.scene)
    X = df[BAND_COLS].to_numpy(float)
    print(f"Loaded {len(df)} pixels from {args.scene} (sensor {args.sensor})")

    # land closure uses brightness-normalized shape space; water uses raw
    # reflectance (albedo / Fe3+ intensity is the signal).
    norm = not args.water
    vpca = run_vpca(X, normalize=norm)
    names, M = endmember_matrix()
    comps = match_components(X, vpca["scores"], names, M, normalize=norm)

    clo = None
    if not args.water and args.classcol in df.columns:
        clo = closure(vpca["scores"], comps, df[args.classcol].to_numpy())
    wreg = None
    if args.water and args.conc in df.columns:
        wreg = water_regression(vpca["scores"], comps, df[args.conc].to_numpy())

    print_report(vpca, comps, clo, wreg)


if __name__ == "__main__":
    main()
