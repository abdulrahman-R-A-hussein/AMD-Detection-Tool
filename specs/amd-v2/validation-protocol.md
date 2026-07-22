# AMD Detection v2 — Validation Protocol

**The test document.** Hand this to whoever runs the validation. It says exactly
what to run, what to click, what to export, what numbers to expect, and how to
read them. Every step maps to a hypothesis from [`plan.md`](plan.md).

| Test | Hypothesis | Tool | Produces |
|------|-----------|------|----------|
| A. Paper fidelity | H1 | GEE tool (Silverton) | class-fraction comparison to SIM 3466 |
| B. VPCA closure | H2, H4 | `vpca_validation.py` | groups recovered, ferric match, agreement %, Cohen's κ |
| C. Threshold derivation | §4 | `derive_thresholds.py` | ROC-AUC + Youden threshold per index |
| D. Water Fe³⁺ | H3 | `vpca_validation.py --water` | R², RMSE vs ground truth |

---

## 0. One-time setup

```bash
cd D:\dev\Sulfate-Methos
python -m venv .venv
.venv/Scripts/python -m pip install -r python/requirements.txt
```

**Prove the validators are correct before trusting any real number** (this is
the point — a validator that can't recover known truth is worthless):

```bash
.venv/Scripts/python python/vpca_validation.py --self-test
.venv/Scripts/python python/derive_thresholds.py --self-test
```

Both must print `RESULT: PASS` / `OVERALL: PASS`. The VPCA self-test builds a
synthetic scene from known minerals and confirms VPCA recovers the ferric /
clay / vegetation groups and that jarosite+goethite correctly **collapse into
one ferric component** (finding H2). The threshold self-test recovers a known
crossover at 0.100.

---

## Test A — Paper fidelity (H1)

**Goal:** the corrected index `IronSulfate = (B2/B1) − (B5/B4)` reproduces
Rockwell's San Juan map more faithfully than the old `(B2+B4)/B1` heuristic.

1. Open `earth-engine/amd_detection_v2.3.0.js` in the GEE Code Editor, Run.
2. Select **Silverton, CO** (the paper's own area). Sensor **Landsat 8**,
   season **Summer**.
3. Read the console STATISTICS SUMMARY: note the **iron-sulfate area %** and the
   index mean / p90.
4. Toggle the **Land AMD Classification** layer. **Expected:** red/crimson
   iron-sulfate classes (12/14/17/18) concentrate in the known alteration
   zones — Red Mountain, Ironton, Ohio Peak — with vegetated valleys in greens.
   A solid single-color circle is a FAIL (that was the pre-v2.0.1 bug).
5. Click a known jarosite site (~37.918, −107.664). **Expected:** a red class,
   `OVERALL: ✓ VISIBLE`, index positive (≈0.15–0.35). Click a vegetated valley:
   index should be **negative**.

**Pass criterion (qualitative):** the spatial pattern of iron-sulfate classes
matches the published SIM 3466 sheet's alteration footprint; clean valleys are
not flagged. Record the class-% for the report.

> Note: the old "expected 3–10% AMD" range in `validation_results.md` was tuned
> to the *wrong* index and is **not** a valid v2 yardstick. Derive expected
> ranges from Rockwell's own reported figures instead.

---

## Test B — VPCA spectral-library closure (H2, H4)

**Goal:** confirm the scene genuinely contains the mineral signals the
classifier claims, using the independent Ortiz-lab VPCA method.

1. In the GEE tool, with your area loaded, click **Export VPCA CSV**
   (top-right panel). A task appears in the **Tasks** tab — run it. It writes
   `VPCA_<sensor>_<area>_<date>.csv` to Google Drive `GEE_Exports/`.
   Columns: `SR_B1..SR_B7, class, water_class, lon, lat` (one row per pixel).
2. Download the CSV, then:
   ```bash
   .venv/Scripts/python python/vpca_validation.py --scene VPCA_L8_Silverton_*.csv --sensor L8 --classcol class
   ```
3. Read the report:
   - **Component → end-member table.** Each varimax component is matched to a
     library end-member and its spectral **group** (ferric / clay_alunite /
     vegetation / water). A component tagged `<-- AMD` matched a ferric mineral.
   - **Spatial closure.** `Pixel agreement %` and `Cohen's κ` between the VPCA
     ferric component and the classifier's iron-sulfate classes.

**How to read it:**
- A ferric component present with |r| ≥ 0.80 (SAM ≤ ~15°) = the scene really
  contains an iron-sulfate spectral signal → the classifier isn't inventing it.
- **κ interpretation:** <0.2 poor · 0.2–0.4 fair · 0.4–0.6 moderate ·
  0.6–0.8 substantial · >0.8 almost perfect. For a known AMD site, expect the
  ferric group to be recovered and κ in the moderate+ range. Low κ at a known
  AMD site = the classifier and the independent spectral evidence disagree →
  investigate thresholds (Test C).
- **H2 note:** you will NOT get separate jarosite / goethite / hematite
  components at 7 bands — they identify as one **ferric group**. That is the
  expected, defensible finding; report it as a resolution limit, and cite that
  distinguishing them needs hyperspectral data.

**Control check:** run Test B on a clean lake / vegetated control (Atwood, OH).
**Expected:** no ferric component recovered (or |r| < 0.8), classifier AMD
fraction ≈ 0. A ferric match at a clean control = false-positive signal to fix.

---

## Test C — Honest threshold derivation (§4)

**Goal:** replace guessed thresholds with ROC-derived ones that carry an AUC.

1. Load the tool over the study area and let the composite build (the
   threshold export needs `settings.currentComposite`).
2. In the Code Editor, hover **Geometry Imports** (top-left of the map) →
   **+ new layer**; click the layer's **gear icon** and rename it exactly
   `amdPolygons`; draw polygons over **confirmed-AMD** ground (e.g., Red
   Mountain gossans). Repeat for a second layer named exactly `cleanPolygons`
   over **confirmed-clean** ground (vegetated valley, clean lake). Avoid
   shadows, roads, snow, and anything ambiguous — polygon purity is the
   experiment.
3. Click **Export Threshold CSV** (settings panel, VALIDATION EXPORT section).
   It samples the 5 index bands (`IronSulfate, FerricIron1, FerricIron2,
   FerrousIron, ClaySulfateMica`) inside each polygon set, tags `label`
   (1 = AMD, 0 = clean), and queues `Thresh_<sensor>_<area>_<date>.csv`. If a
   layer is missing/misnamed, the Console prints instructions instead.
4. **Tasks** tab (top-right) → **RUN** → CSV lands in Drive `GEE_Exports`.
5. Run:
   ```bash
   .venv/Scripts/python python/derive_thresholds.py --csv Thresh_<...>.csv
   ```
6. Read the table: per index, **AUC** (separability), the **Youden threshold**
   (use this as the tool's setting), sensitivity/specificity, and the label-free
   **Otsu** cross-check.

**Pass / action:**
- AUC ≥ 0.8 (good+) → the index is a usable discriminator; set the tool's
  threshold to the Youden value.
- AUC ~0.5 → the index does not separate AMD from clean here; do not rely on it.
- Update `IronSulfate` (currently provisional 0.10) and the ferric/clay
  thresholds in `earth-engine/amd_detection_v2.3.0.js` `settings` to the derived
  Youden values, and record AUC + sens/spec in the methodology.

---

## Test D — Water Fe³⁺ ground-truth regression (H3)

**Goal:** show the water Fe³⁺ signal tracks measured concentration
(Ganau 675 mg/L; Dukan).

1. Export a water-pixel CSV (the VPCA CSV already carries `water_class`; filter
   to `water_class >= 0`), including `lon, lat`.
2. For pixels/points where you have lab concentrations, add a `conc_mgL` column.
3. Run:
   ```bash
   .venv/Scripts/python python/vpca_validation.py --scene water_ganau.csv --sensor L8 --water --conc conc_mgL
   ```
4. Read **R²** and **RMSE (mg/L)** of the Fe³⁺ component vs concentration.

**Pass criterion:** R² ≥ 0.7 with the slope in the physically expected
direction (higher component score = higher Fe³⁺). Report R² and RMSE. With only
one ground-truth site you can report the single-site prediction and error;
multi-site (Ganau + Dukan + a clean control) makes it a real regression.

---

## What each deliverable does (for the write-up)

- **`vpca_validation.py`** — the independent validator. VPCA decomposes the
  exported scene into orthogonal spectral components; each is matched to USGS
  library end-members by spectral angle; the ferric component's spatial score is
  compared to the classifier output (closure) and, in water mode, regressed
  against ground truth. Not the detector — the check on the detector.
- **`derive_thresholds.py`** — turns confirmed AMD/clean samples into ROC-AUC
  and Youden thresholds so every threshold in the tool has a provenance.
- **`amd_detection_v2.3.0.js`** — the detector, with the corrected index,
  first-match-wins classification, and the **Export VPCA CSV** button that feeds
  the two scripts above.

**Reproducibility:** all sampling uses `seed: 42`; the composite window and
cloud settings are printed to the GEE console on every run — record them with
each exported CSV so any result can be regenerated.
