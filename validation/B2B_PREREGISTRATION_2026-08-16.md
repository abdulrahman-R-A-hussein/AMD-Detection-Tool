# Phase B2b — PRE-REGISTRATION

**Written 2026-08-16, BEFORE any imagery was extracted or any parameter swept.**
Committed as its own commit so `git log` order is auditable evidence, exactly as
`4bb3b63` was for Phase B2.

## 1. The observation this phase exists to repair

At 86 chemically-confirmed AMD source points across 4 Colorado districts,
scored against a bare-ground control defined from NLCD class 31 — a label that
owes nothing to the imagery under test:

| score | AUC | worst-case LORO Youden J |
|---|---|---|
| `FerricIron1` alone | 0.793 | **+0.318** |
| `AMDclassFrac` (shipped v3.0.x classifier) | 0.442 | **0.000** |

The classifier contains `FerricIron1` and cannot do what `FerricIron1` does
alone. Corroborated independently: the raw index improves from Landsat 30 m to
Sentinel-2 20 m; the classifier does not.

## 2. Hypothesis (mechanistic, stated before testing)

**H-mech.** `classify_v3()` computes scene-relative thresholds over the **whole
region**. Vegetation and water have low iron-index values and drag the scene
mean down, so `mean + 0.5σ` admits a large share of *ordinary bare ground*.
With the NDVI gate already requiring a pixel to be unvegetated before any AMD
class is assigned, the effective test is "bare, and iron-rich compared with
grass and water" — which most bare pixels pass. The discrimination that matters,
**iron-rich compared with other bare ground**, is never performed.

**H-fix.** Computing those statistics over the **bare/land subset only** makes
the threshold ask the right question and should recover the discrimination
`FerricIron1` already demonstrates.

**Falsifiable prediction, registered now:** the mean of each iron index over the
bare subset must be **higher** than over the whole region, in every region.
**If it is not, H-mech is wrong, and this phase stops and re-diagnoses rather
than tuning parameters.** This check runs BEFORE any parameter sweep,
deliberately, so a wrong diagnosis cannot be hidden by tuning.

## 3. Primary outcome — fixed

**Worst-case leave-one-region-out Youden J of `AMDclassFrac_v4` against C3b**
(NLCD barren). C3b is primary *because bare ground is the confound under
repair*. Pooled AUC is reported but is not the criterion — finding L1.

Secondary, all reported: the same against C1 (in-stream), C2 (terrain-matched),
C3 (the circular NDVI-defined tier, kept for continuity and labelled).

## 4. Decision rule — fixed

| result | verdict |
|---|---|
| J ≥ 0.25 **and** BH-corrected p < 0.05 | **SUCCESS** — the fix works |
| 0.15 ≤ J < 0.25 | **PARTIAL** — improved, not a detector |
| J < 0.15 | **FAILURE** — reported as a null |

Baseline for comparison is the shipped classifier's **0.000**.

## 5. Parameter grid — fixed, nothing added later

- `k_bare ∈ {0.5, 1.0, 1.5, 2.0}` for `IronSulfate`, `FerricIron1`,
  `FerricIron2`, `FerrousIron`
- `clay_bare ∈ {0.25, 0.5}`

8 combinations. **Selected by worst-case LORO J, never pooled.** The full grid
is reported, not the winner alone, so the selection is visible.

## 6. Statistics — fixed

- **Null:** 10,000 within-region label permutations. Never across region —
  source points cluster spatially and districts differ in geology.
- **Correction:** Benjamini–Hochberg across the full family
  (8 grid points × 4 control tiers = 32 tests). Bonferroni threshold reported
  alongside.
- **n and caveat** next to every number.

## 7. Replica-fidelity cost — must be reported, not hidden

This is a **deliberate departure** from SIM 3466, so agreement with Rockwell's
published map will drop. Report worst-case leave-one-site-out J and mean κ
against Rockwell at Silverton / Summitville / Red Mountain Pass, **v3 vs v4 side
by side**.

**Framing fixed now, and it must survive into the report:** agreement with
Rockwell measures **replica fidelity, never accuracy**. Rockwell's map is a
published *automated* classification, not ground truth. Only measured field
chemistry is ground truth. **Losing agreement while gaining ground-truth
discrimination is a SUCCESS**, and the two claims are reported separately so
neither can quietly cannibalise the other.

## 8. Shipping rule — fixed

Port to `earth-engine/amd_detection_v2.4.0.js` and bump to **v4.0.0** only if
the primary outcome reaches SUCCESS. PARTIAL or FAILURE → the shipped tool is
left alone and the result is reported as a null.

## 9. What would falsify each claim

| claim | falsified by |
|---|---|
| H-mech (whole-region stats are the cause) | bare-subset mean not higher than whole-region mean |
| H-fix (bare-subset thresholds repair it) | J < 0.15 vs C3b |
| "improved on Rockwell" | ground-truth J gain not exceeding the fidelity loss in substance |
| generalisability | Colorado-only until tested elsewhere; stated as a limit, not a caveat to be waived |
