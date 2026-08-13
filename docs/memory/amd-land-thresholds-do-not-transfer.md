---
name: amd-land-thresholds-do-not-transfer
description: "AMD land thresholds are site-specific; judge any new criterion by cross-site worst-case transfer, never by within-site AUC"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0fc5c60d-44e9-423f-b015-759ff98e4182
  modified: 2026-07-26T17:27:12.794Z
---

The land arm's agreement with Rockwell's published map **reverses between
sites**: it over-called ~4x at Silverton (where Test C derived the thresholds)
and under-called ~5.6x at Summitville, an independent Superfund AMD site.

**The methodological lesson, which generalises beyond this project:** Test C
judged thresholds by **within-site AUC** and reported 0.99-level scores. Those
scores said nothing about transfer. Re-derived across three sites, the same
indices score 0.63–0.67, and `FerrousIron` scores **0.437 — below chance**,
with no AMD discriminative power at any site despite Test C's 0.983.

**How to evaluate any future criterion:** leave-one-site-out, fit the cutoff on
the other sites, apply it unchanged to the held-out one, and rank by
**worst-case Youden J**. Not mean, not AUC. Recall alone is gameable by
flagging most of the scene; precision is not comparable across these sites
because AMD base rates differ ~24-fold (1.7% / 2.1% / 26.3%). Machinery already
exists: `python/iron_criterion_search.py`, `python/paper_faithful_test.py`.

**Labels are Rockwell's published map, not field data.** Everything measured
this way is *replica fidelity*, never accuracy. No "better than Rockwell" claim
is supportable without fieldwork — and the user's grant narrative should keep
those two claims separate.

The same defect class hit the water arm first (`AWEINSH > 0.20` tuned at Ganau
excluded 100% of Piedmont's water) — see [[amd-water-module-invalid]]. An
absolute cutoff on a non-normalised index, calibrated at one site, is the
recurring failure mode in this project. Method source: [[amd-sim3466-method-source]].
