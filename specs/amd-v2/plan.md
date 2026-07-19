# AMD Detection v2.0 — Upgrade & Validation Plan

**Goal:** turn a heuristic that *looks* like Rockwell 2021 into a
scientifically defensible, literature-current framework that produces
*verifiable* iron/sulfate readings on land **and** water, and prove it with a
real VPCA + spectral-library test — not another circular control-lake table.

Status: **PLAN — awaiting approval. No code will be written until you say go.**

---

## 1. Guiding hypotheses (the science backbone your supervisor will ask for)

- **H1 (fidelity):** implementing Rockwell's *actual* index `2/1 − 5/4` with his
  adaptive std-dev + clip thresholding reproduces his San Juan class map more
  faithfully than the current `(B2+B4)/B1` heuristic. *Test:* re-run Silverton,
  compare class fractions to the published SIM 3466 map sheet.
- **H2 (separability):** the diagnostic land indices, convolved from the USGS
  spectral library, actually separate jarosite / goethite / hematite /
  schwertmannite at Landsat-8 and Sentinel-2 resolution. *Test:* library
  convolution + VPCA loadings (below).
- **H3 (water transfer):** replacing land-SR ratios with an aquatic-reflectance
  workflow + a physically-grounded Fe³⁺ index reduces false positives at clean
  control lakes and tracks the Ganau 675 mg/L ground truth. *Test:* VPCA of the
  water pixels vs. known concentration.
- **H4 (VPCA closure):** the dominant varimax-rotated components of the scene
  reflectance correspond to real color-producing agents (Fe³⁺ minerals, clay,
  vegetation, clear water) and their spatial loadings match where the classifier
  fires. This is the KSU/Ortiz method (your lab's own method) used as an
  *independent* validator, not as the detector.

---

## 2. The VPCA validation you asked for — exactly what it is and how it runs

VPCA (varimax-rotated PCA) is the Ortiz-lab spectral-decomposition method
(Ali & Ortiz; the Lake Erie / SBG work). Applied here it answers one question:
**"Do the spectral components the data actually contains match the minerals my
classifier claims are there?"** That is the closure test between your output and
first-principles spectroscopy.

**Pipeline (implemented as a Python notebook, `python/vpca_validation.py`):**

1. **Reference end-members.** Pull jarosite, schwertmannite, goethite, hematite,
   K-alunite, montmorillonite (clay), green vegetation, and clear water from the
   **USGS Spectral Library v7** (splib07). Convolve each to Landsat-8 OLI and to
   Sentinel-2 MSI relative spectral response → reference reflectance vectors in
   the exact bands your tool uses. *This is the "verify with spectrum library"
   step.*
2. **Scene matrix.** Export the multi-band composite for a study area from GEE
   (already supported via `exportIndices`). Reshape to an N-pixels × 7-bands
   matrix; standardize.
3. **PCA → varimax rotation.** Retain components explaining ≥95% variance; rotate
   with varimax so each component loads on a physically interpretable band-shape.
4. **Interpret loadings.** Correlate each rotated component's spectral loading
   against the convolved library end-members (spectral angle / cosine
   similarity). A component that matches jarosite to within a small spectral
   angle = the scene genuinely contains a jarosite-like signal.
5. **Spatial closure.** Map each component's per-pixel score back to the raster.
   Overlay on the classifier output. **Agreement between "VPCA says jarosite
   here" and "classifier says class 17 here" is the accuracy result.**
6. **Water variant.** Repeat steps 2–5 on water-only pixels to decompose CPAs
   (Fe³⁺, suspended sediment, CDOM, clear water) and regress the Fe³⁺ component
   score against the Ganau/Dukan known values.

**Metrics produced:** variance explained per component; spectral-angle match to
each library mineral; component-vs-class spatial agreement (%, Cohen's κ);
Fe³⁺-component vs. ground-truth concentration (R², RMSE). These are the numbers
for your supervisor.

---

## 3. Code upgrades (each ties to an audit item)

**Tier 1 — correctness (must fix; these are bugs, not enhancements):**
1. Replace iron sulfate index with `(B2/B1) − (B5/B4)` = Rockwell `2/1 − 5/4`;
   re-derive its threshold empirically (§4). *(A1)*
2. Rebuild classification as **first-match-wins** (reverse the `where` order or
   use an explicit priority remap) so classes 9/14/17/18/19 become reachable;
   remove the unconditional class-12 fallback. *(A2)*
3. Add `hasIron.not()` guards to classes 2, 3, 4. *(A3)*
4. Add brightness/SNR validity mask to **all** water-score criteria, not just
   criterion 1. *(B)*
5. Fix score scale to its true max (rename to 0–9 or re-weight to 0–7) and move
   class breaks accordingly. *(C5)*
6. Fix/verify the winter `calendarRange` wrap. *(C7)*

**Tier 2 — method upgrades (the "elevate the paper" part):**
7. Enable the paper's adaptive std-dev threshold + low-end clip by default, UI-
   exposed. *(C4)* — this is literally Rockwell's method, currently dormant.
8. Sensor-specific index thresholds via the RSR-convolved library values from
   the VPCA step — thresholds become *derived*, not guessed. *(C3, H2)*
9. One-pixel morphological erosion on the water mask. *(C2)*
10. Guard the depth proxy (`epsilon` inside the log; clamp). *(C6)*

**Tier 3 — aquatic breakthrough (adapt to water, the new science):**
11. Add a physically-grounded **Fe³⁺ water index** and an **AMWI**-style
    red/blue normalized difference (validated in 2021–2024 AMD-water literature)
    as first-class water criteria, replacing the ad-hoc turbidity/yellow
    heuristics.
12. Document an **ACOLITE/C2RCC aquatic-reflectance path** as the recommended
    input for water bodies (GEE stays the land path); this is what makes water
    readings trustworthy rather than land-SR artifacts. *(C1)*
13. Optional supervised layer: the 2024 RF/kNN/MLP Sentinel-2+WorldView-3
    approach as a cross-check, using the VPCA components as features.

---

## 4. Deriving thresholds honestly (replaces the circular validation)

For each index, build a **two-population separability test**: sample pixels at
confirmed-AMD polygons (Iron Mountain, Summitville, Silverton, Berkeley Pit) and
at confirmed-clean polygons; compute the histogram overlap and pick the threshold
at the crossover / by Otsu / by Youden's J. Report the ROC-AUC per index. This
gives every threshold a defensible provenance instead of a hand-typed constant.

---

## 5. Deliverables

- `earth-engine/amd_detection_v2.0.0.js` — corrected + upgraded GEE tool.
- `python/vpca_validation.py` (+ notebook) — the runnable VPCA + library test.
- `docs/METHODOLOGY.md` — rewritten to match the code, with the corrected
  formulas and the hypothesis/validation framing.
- `specs/amd-v2/validation-protocol.md` — the step-by-step **test document you
  hand to whoever runs the validation**: what to click, what to export, what
  numbers to expect, and how to read them.
- `docs/HOW_IT_WORKS.md` — plain "what the code does and how" walkthrough.

---

## 6. Sequence

1. Approve this plan.
2. Tier 1 correctness fixes → immediate re-validation on Silverton (H1).
3. Build the VPCA/library notebook → run H2 separability.
4. Tier 2 + Tier 3 upgrades, thresholds re-derived from §4.
5. Full VPCA closure + water ground-truth regression (H3, H4).
6. Rewrite docs; produce the validation protocol; version bump + push.
