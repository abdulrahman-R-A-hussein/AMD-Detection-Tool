# v1.5.4 Audit — Weaknesses, Contradictions, and Inverted Logic

Source reviewed: `earth-engine/amd_detection_v1.0.0.js` (2841 lines, v1.5.4),
`docs/METHODOLOGY.md`, `earth-engine/*.md` fix-history, `paper.pdf`
(Rockwell, McDougal & Gent 2021, USGS SIM 3466), and the Dec 2025 development
transcript.

---

## A. Blocking scientific defects

### A1. The primary index is not the paper's index

| Source | Iron sulfate mineral index |
|---|---|
| Rockwell 2021, Table 4 | `2/1 − 5/4` (difference of two ratios) |
| `docs/METHODOLOGY.md` line 11 | `(B2/B1) − (B5/B4)` — matches the paper |
| `amd_detection_v1.0.0.js:295` | `(B2 + B4) / B1` — **matches neither** |

The code computes a band-addition ratio, not the paper's ratio difference. The
two quantities have different dynamic range and different physical meaning. The
paper's index subtracts `5/4` specifically to suppress green vegetation; the
implemented index has no vegetation-suppression term, which is why so much
downstream vegetation/road masking had to be bolted on to compensate. Every
threshold, every validation number, and the methodology document are therefore
describing an index the code does not compute.

**Corroborating evidence from your own validation table:** the reported "Iron
Index Mean" is 2.32–3.87 across *all* sites, including the clean control lakes,
while the detection threshold is 1.15. A threshold that essentially every pixel
exceeds is not discriminating anything — the masks are doing all of the
classification work, and the index is along for the ride.

### A2. The classification chain is inverted, collapsing 6 classes into 1

`amd_detection_v1.0.0.js:837-859`. The comment says "MOST RESTRICTIVE FIRST
(per Rockwell Table 4)", and the paper does specify first-match-wins ("the pixel
being assigned to the first class for which all conditions are met"). But
chained `ee.Image.where()` is **last-match-wins** — each call overwrites the
previous. The ordering therefore achieves the exact opposite of what is
intended.

It is made total by the fallback at line 859:

```javascript
.where(hasIron.and(amdLandMask), 12);   // runs LAST, no .not() guards
```

Every pixel that qualified for class 9, 17, 12, 18, 19 or 14 also satisfies
`hasIron AND amdLandMask`, so all of them are rewritten to class 12. **Classes
9 (argillic alteration), 14 (oxidizing sulfides), 17 (proximal jarosite), 18
(distal jarosite) and 19 are unreachable — they can never appear in output.**
The proximal/distal jarosite distinction, which is the scientifically
interesting part of Rockwell's scheme and the part that carries the net-acid-
production ranking, is silently discarded.

### A3. Non-iron classes overwrite iron-sulfate detections

Classes 8, 7, 6, 5, 10, 1, 13 and 11 correctly carry a `hasIron.not()` guard.
Classes **2** (line 879), **3** (line 882) and **4** (line 888) do not. Because
STEP 2 runs after STEP 1, any iron-sulfate pixel lacking clay is overwritten by
class 2/3/4. Real AMD is relabelled as ordinary ferric or ferrous iron.

### A4. The control-site validation is circular

`earth-engine/validation_results.md` reports 0.00–0.01% AMD at Atwood,
Piedmont and Clendening lakes and presents this as proof the method works. But
the land module masks *all* water by construction (`amdLandMask` requires
`unifiedWater.not()`). A clean lake scores ~0% because it is water, not because
the index discriminated it from a contaminated lake. The test cannot fail, so it
demonstrates nothing. There is no confusion matrix, no kappa, no independent
reference labels, and the "Expected" column contains estimates rather than
measured ground truth.

---

## B. The Atwood problem was only half fixed

The transcript shows the diagnosis was correct: at Atwood Lake, clean deep water
with brightness 0.017 produced an Iron Sulfate Index of 5.5 because `B1 → 0`
makes `(B2+B4)/B1` explode. The fix applied was a brightness gate,
`brightness.gt(0.05).and(brightness.lt(0.20))`.

That gate was applied to **criterion 1 only** of the water score
(`amd_detection_v1.0.0.js:1007-1008`). Criteria 3 (Turbidity = `B4/B2`) and 5
(Yellow Index = `B3/B2`) are ratios of the same near-zero numbers and have **no
brightness guard at all**. Criterion 6 (`ndwi.lt(0.2)`) has none either. A dark,
clean lake can therefore still collect 1 (turbidity) + 1 (yellow) + 1 (NDWI) = 3
points and be classified "moderate contamination" — the identical failure mode,
one criterion over.

**Assessment of the fix strategy:** gating on brightness treats the symptom. The
root cause is that ratios are numerically unstable when the denominator
approaches the noise floor, which over water is always. The correct fix is to
(a) propagate a per-pixel validity mask derived from a signal-to-noise floor
rather than a hand-tuned brightness window, and (b) stop using land surface
reflectance over water at all — see C1.

---

## C. Method-level gaps

### C1. Land surface reflectance is being used for aquatic targets
Both LaSRC (Landsat) and Sen2Cor (Sentinel-2) are parameterised for land and
routinely return near-zero or negative reflectance over dark water. Every water
index in this tool is a ratio built on those unreliable values. Current aquatic
practice uses ACOLITE or C2RCC. This single issue explains most of the water
false positives that were chased individually through the development history.

### C2. No shoreline erosion
Mixed land/water pixels at the shoreline are the classic AMD false-positive
source, and the transcript records exactly this ("only few pixels around the
lake"). A one-pixel morphological erosion of the water mask removes them at
near-zero cost. Not implemented.

### C3. Thresholds are not sensor-transferable
Sentinel-2 B1 (60 m) and Landsat 8 B1 (30 m) have different bandpasses and
spatial support, yet the same 1.15 threshold is applied to both. The code
already accepts sensor-specific tuning for the built-up mask but not for the
indices themselves.

### C4. Fixed thresholds where the paper uses adaptive ones
Rockwell isolates high values using "a common standard deviation threshold,
followed by an index-specific clip of the lowest values". The code has
`useStdDevThresholds` and `applyIndexClipping` implemented but defaulted **off**
(lines 501, 509) and never exposed in the UI — so the paper's actual
thresholding strategy is present in the codebase and unused.

### C5. Score scale mismatch
Documented as 0–7 (`METHODOLOGY.md`, layer label, viz `max: 7`), but the criteria
sum to a maximum of 9 (2+2+2+1+1+1). Class boundaries at 3 and 5 sit on a scale
whose top is undefined.

### C6. Depth proxy is numerically fragile
`ln(B2)/ln(B3)` with `.add(epsilon)` applied **after** the log rather than to the
band. When B3 approaches 1.0 the denominator approaches 0. The transcript also
records that this proxy misbehaves on land — the response was to harden the water
mask upstream, which was the right call, but the proxy itself was left unguarded.

### C7. Winter season filter is likely broken
`ee.Filter.calendarRange(months[0], months[last])` with `'Winter (Dec-Feb)' =
[12,1,2]` evaluates as `calendarRange(12, 2)`. Needs verification; if it does not
wrap, the winter preset silently returns an empty or wrong collection.

---

## D. Evaluation of the author's own additions beyond Rockwell 2021

Assessed on two axes: was the **idea** scientifically sound, and was the
**implementation** correct. Several ideas independently converge on published
methods — evidence the scientific instincts were right even where code was not.

| Addition (author's) | Idea verdict | Implementation verdict | v2 disposition |
|---|---|---|---|
| Water-quality extension of a land-minerals method | Correct and novel direction; where 2022–2025 AMD literature went | Undermined by land-SR inputs over water (C1) | Keep, re-plumb inputs |
| Turbidity red/blue ratio | Independently reinvents published **AMWI** (Kizel basin) | OK, but unguarded in dark water (B) | Keep as formal AMWI |
| Depth proxy ln(B)/ln(G) | Is **Stumpf (2003) log-ratio bathymetry**; purpose (bottom-reflectance FP removal) is valid — author correctly defended keeping it when advised to delete it | Fragile epsilon/log (C6) | Keep, harden |
| NIR anomaly criterion | Physically correct (particle scattering vs H₂O absorption) | Sound | Keep |
| Yellow index (G/B) for Fe³⁺ | Parallels water-color/dominant-wavelength literature | Correlated with other criteria | Fold into VPCA components |
| Unified water mask / mutual exclusivity | Correct diagnosis of a real dual-definition conflict; sound architecture | Correct | Keep as-is |
| AWEINSH > 0.20 wet-soil cutoff | Legitimate empirical calibration (Ganau field obs.) | Single-site calibrated | Re-derive multi-site |
| NDBI rejection for built-up masking | Author empirically discovered the documented urban/mine-waste NDBI conflict | Replacement (brightness+NDVI+MNDWI) defensible | Keep |
| SWIR road-bypass with strong-iron override | Genuine spectral reasoning (iron oxides have high SWIR1) | Threshold collision with dark mask | Keep idea, fix thresholds |
| Brightness window 0.05–0.20 | Valid first-order QA gate, empirically derived (Atwood vs Ganau) | Applied to 1 of 6 criteria only (B) | Generalize to all criteria |
| Multi-criteria contamination score | Weight-of-evidence is a legitimate pattern | Criteria share bands → one signal votes 3× | Replace votes with orthogonal VPCA components |
| Cloud Score+ multi-method masking | Current best practice, beyond the paper | Correct | Keep |
| Click-to-inspect diagnostics | Good validation tooling; how Atwood FP was found | Correct | Keep |

**Summary:** the blocking defects in section A live almost entirely in the
inherited/translated Rockwell layer (index transcription, `where()` ordering),
not in the author's novel water direction. The author's framework survives into
v2 intact; v2 replaces the plumbing beneath it.

## E. What is genuinely good and should be kept (baseline layer)

- Indices are computed **per-image then composited**, not from a median
  composite. This is the correct order and better than much published work.
- `COPERNICUS/S2_SR_HARMONIZED` is the right collection choice — it handles the
  post-Jan-2022 BOA offset that trips up most Sentinel-2 code.
- The unified water mask resolved a real dual-definition conflict; the
  mutual-exclusivity architecture between land and water modules is sound.
- Cloud Score+ integration is current best practice.
- The Green/Red ratio and SWIR1 road-bypass logic for separating iron oxides
  from asphalt is a genuine improvement over the paper.
- Ferric Iron 1, Ferric Iron 2, Ferrous Iron and Clay-Sulfate-Mica formulas all
  verified correct against Table 4.
