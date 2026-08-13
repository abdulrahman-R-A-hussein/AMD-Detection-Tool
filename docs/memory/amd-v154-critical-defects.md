---
name: amd-v154-critical-defects
description: Blocking scientific bugs found in AMD detection v1.5.4 (earth-engine JS) during 2026-07-18 audit
metadata: 
  node_type: memory
  type: project
  originSessionId: b8bbe776-2f5c-4312-bada-a4aa5f8fd187
---

Audit of `earth-engine/amd_detection_v1.0.0.js` (v1.5.4) on 2026-07-18 found four blocking defects. Full write-up: `specs/amd-v2/audit.md`.

1. **Wrong primary index.** Code line 295 computes iron sulfate index as `(B2+B4)/B1`, but Rockwell 2021 (paper.pdf, Table 4) and the project's own `docs/METHODOLOGY.md` both specify `2/1 − 5/4` = `(B2/B1)−(B5/B4)`. Threshold 1.15 is below the all-site index mean (2.3–3.9), so it discriminates nothing — masks do all the work.
2. **Inverted classification.** Chained `ee.Image.where()` is last-match-wins, but the code comments/paper want first-match-wins. Unconditional class-12 fallback at line 859 makes classes 9/14/17/18/19 (incl. proximal/distal jarosite) unreachable.
3. **Missing iron guards.** Classes 2,3,4 (lines 879/882/888) lack `hasIron.not()`, so they overwrite real AMD.
4. **Circular validation.** `validation_results.md` control-lake 0% AMD is guaranteed by the water mask, not by the index — proves nothing. No confusion matrix/kappa/ground truth.

Also: water-score brightness guard only on criterion 1 (Atwood false-positive half-fixed); score documented 0–7 but max is 9; depth proxy epsilon placed after log; winter calendarRange may not wrap.

Good parts to keep: per-image-then-composite order, S2_SR_HARMONIZED, unified water mask, Cloud Score+, Green/Red + SWIR1 road bypass, and Ferric1/Ferric2/Ferrous/Clay formulas (verified correct vs Table 4).

See [[amd-v2-vpca-validation-plan]].
