"""Faithful NumPy port of the v2.4.0 land classification, with a self-test.

WHY THIS EXISTS: python/amd_detection.py is a v1.5.1 port that predates every
v2.x correction (wrong iron index, last-match-wins classification, unreachable
classes). Using it for any comparison would evaluate our OLD broken code. This
module ports the CURRENT cascade from earth-engine/amd_detection_v2.4.0.js.

VERIFIED CEILING: 94.95% identical to the real GEE tool over the 20,000
committed Silverton pixels. It cannot reach 100%, and the reason is structural
rather than a porting bug:

    processCollection() does  collection.map(calculateAllIndices)  and THEN
    takes a median composite. So every index band in the tool is the MEDIAN OF
    PER-IMAGE INDEX VALUES. This module can only compute indices from the
    median BANDS that were exported. median(f(x)) != f(median(x)) for the
    ratio-based indices used here.

Consequences:
  * Use this for distribution-level work (class fractions, threshold
    sensitivity studies) where a ~5% per-pixel difference is tolerable.
  * Do NOT use it for pixel-exact comparison against another map, or to
    generate classifications for new sites - run those through GEE so the
    per-image ordering is preserved.
  * The residual disagreement is concentrated at the vegetation boundaries
    (classes 11/13 vs unclassified), i.e. where greenVeg sits near 1.5/3.0 and
    the two averaging orders diverge most.

    .venv/Scripts/python python/classify_v240.py            # run the self-test
"""

import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRUTH = os.path.join(ROOT, "VPCA_Landsat8_Silverton__CO_20260722-v2.csv")
BANDS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]

EPS = 0.0001

# v2.3.0 ROC-derived where noted (validation/README.md, Test C)
S = dict(
    iron=0.10,            # provisional - Test C AUC 0.769, FAILED, kept
    ferric1=1.983,        # derived, AUC 0.992
    ferric2=3.758,        # derived, AUC 0.997
    ferrous=0.959,        # derived, AUC 0.983
    clay=0.021,           # derived, AUC 0.999
    strong_iron=0.15,
    green_veg=1.5, dense_veg=3.0, ndvi_max=0.25,
    brightness_max=0.35, dark_mask=0.2125,
    builtup_bright=0.18, builtup_ndvi_max=0.15, builtup_ndvi_min=-0.10,
    builtup_mndwi_max=-0.20,
    water_thresh=0.3,
)


def indices(d):
    b1, b2, b3, b4, b5, b6, b7 = (d[b].to_numpy(float) for b in BANDS)
    ix = {}
    ix["iron"] = np.clip(b2 / (b1 + EPS) - b5 / (b4 + EPS), -5, 5)
    ix["ferric1"] = b4 / (b2 + EPS)
    ix["ferric2"] = (b4 / (b2 + EPS)) * ((b4 + b6) / (b5 + EPS))
    ix["ferrous"] = (b3 + b6) / (b4 + b5 + EPS)
    ix["clay"] = b6 / (b7 + EPS) - b5 / (b4 + EPS)
    ix["green_veg"] = b5 / (b4 + EPS)
    ix["bright"] = (b2 + b3 + b4) / 3
    ix["ndvi"] = (b5 - b4) / (b5 + b4)
    ix["ndwi"] = (b3 - b5) / (b3 + b5)
    ix["mndwi"] = (b3 - b6) / (b3 + b6)
    ix["aweinsh"] = b2 + 2.5 * b3 - 1.5 * b5 - 0.25 * b7
    ix["b3"], ix["b4"], ix["b6"] = b3, b4, b6
    return ix


def classify(d):
    """Return the v2.4.0 class per row (0 = unclassified)."""
    x = indices(d)
    has_iron = x["iron"] > S["iron"]
    has_f1 = x["ferric1"] > S["ferric1"]
    has_f2 = x["ferric2"] > S["ferric2"]
    has_fe2 = x["ferrous"] > S["ferrous"]
    has_clay = x["clay"] > S["clay"]

    sparse_veg = (x["green_veg"] > S["green_veg"]) & (x["green_veg"] <= S["dense_veg"])
    dense_veg = x["green_veg"] > S["dense_veg"]

    # v2.4.0 scene-independent water mask
    water = ((x["mndwi"] > S["water_thresh"]) & (x["aweinsh"] > 0.0)
             & (x["ndvi"] < 0.0)
             & (d.SR_B5.to_numpy(float) < x["b3"]) & (x["bright"] < 0.30))

    built_up = ((x["bright"] > S["builtup_bright"])
                & (x["ndvi"] < S["builtup_ndvi_max"])
                & (x["ndvi"] > S["builtup_ndvi_min"])
                & ((x["mndwi"] < S["builtup_mndwi_max"])
                   | ((x["mndwi"] > -0.10) & (x["mndwi"] < 0.10))))

    not_bright = x["bright"] < S["brightness_max"]
    not_dark = (x["b6"] > S["dark_mask"]) & (x["bright"] > 0.05)

    with np.errstate(divide="ignore", invalid="ignore"):
        no_green_peak = (x["b3"] / np.where(x["b4"] == 0, np.nan, x["b4"])) <= 1.0
    low_swir1 = x["b6"] < 0.20
    not_dense = x["green_veg"] < 3.5
    # road mask OFF by default in v2.0.1+
    passes_veg_road = no_green_peak & (
        (x["ndvi"] < S["ndvi_max"]) | (has_iron & low_swir1 & not_dense))

    land = ~water & not_bright & not_dark & ~built_up & passes_veg_road

    out = np.zeros(len(d), dtype=int)

    def assign(cond, val):
        m = cond & (out == 0)
        out[m] = val

    # STEP 1 - iron sulfate classes, first-match-wins
    assign(has_iron & has_f1 & has_f2 & has_clay & land & not_bright, 9)
    assign(has_iron & has_f1 & has_f2 & has_clay & land, 17)
    assign(has_iron & has_f1 & ~has_f2 & has_clay & land, 12)
    assign(has_iron & ~has_f1 & has_f2 & has_clay & land, 18)
    assign(has_iron & has_fe2 & has_clay & land, 19)
    assign(has_iron & has_clay & ~has_f1 & ~has_f2 & land, 14)
    assign(has_iron & land, 12)
    # STEP 2 - non-iron-sulfate classes
    assign(has_clay & has_f1 & has_f2 & ~has_iron & land, 8)
    assign(has_clay & (has_f1 | has_f2) & ~has_iron & land, 7)
    assign(has_clay & has_f1 & ~has_f2 & ~has_iron & land, 6)
    assign(has_clay & ~has_f1 & ~has_iron & land, 5)
    assign(has_clay & has_fe2 & ~has_iron & land, 10)
    assign(has_f1 & has_f2 & ~has_clay & ~has_iron & land, 2)
    assign(has_f1 & has_fe2 & ~has_clay & ~has_iron & land, 3)
    assign(has_f1 & ~has_f2 & ~has_clay & ~has_iron & land, 1)
    assign(has_fe2 & ~has_clay & ~has_f1 & ~has_iron & land, 4)
    assign(sparse_veg & has_f1 & ~has_iron & ~water, 13)
    assign(dense_veg & ~has_iron & ~water, 11)
    return out


def verify(path=TRUTH, tol=0.94):
    """Compare against the real tool. Threshold is 0.94, not 1.0, because of
    the median-of-index vs index-of-median difference documented above."""
    d = pd.read_csv(path)
    got = classify(d)
    truth = d["class"].astype(int).to_numpy()
    agree = (got == truth).mean()
    print("port vs GEE tool on %d Silverton pixels: %.2f%% identical"
          % (len(d), 100 * agree))
    if agree < tol:
        bad = pd.DataFrame({"ours": got, "gee": truth})
        bad = bad[bad.ours != bad.gee]
        print("\nTop mismatches (port -> gee):")
        print(bad.groupby(["ours", "gee"]).size().sort_values(ascending=False).head(12))
    return agree


if __name__ == "__main__":
    a = verify()
    print("\nPASS - at the documented 94.95% ceiling (median-of-index limit); "
          "safe for distribution-level use only."
          if a >= 0.94 else
          "\nFAIL - below the known ceiling; the port has drifted from the JS.")
