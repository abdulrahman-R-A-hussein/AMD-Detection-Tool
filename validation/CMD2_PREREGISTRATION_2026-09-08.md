# Phase CMD2 — PRE-REGISTRATION: the mining-extent confound test

**Written 2026-09-08, BEFORE any mine polygon was joined to any chemistry or
index value.** Own commit, as `4bb3b63` / `df6a6ae` / `6af0b5b` / `56aa3aa` /
`8531227` were.

## 1. Why this phase exists

[`ARM_CMD1_GEOMETRY_2026-08-16.md`](ARM_CMD1_GEOMETRY_2026-08-16.md) found that
at a 30 m radius in five Ohio coal-drainage watersheds, `NDVI_stress` tracks
measured sulfate at **rho = −0.354** (n=137, within-region permutation
p = 0.0028, 4 of 5 watersheds negative, 5th = +0.03). The verdict was **PARTIAL**
and the report named a single untested confound as the gate on whether it means
anything at all:

> **High-sulfate stations may simply sit in more heavily mined catchments with
> less vegetation overall.** That would produce exactly this correlation without
> any seep-scale signal — a land-cover confound, not detection.

Until that is tested, the permitted claim is *"a vegetation index tracks sulfate
at 30 m in Ohio CMD watersheds"* and explicitly **not** *"we detect CMD seeps."*
This phase tests it.

## 2. Hypotheses

**H-CONF (the confound; this is the hypothesis under test).** The
`NDVI_stress`–sulfate association is explained by catchment-scale mining extent.
Stations draining more heavily mined ground have both higher sulfate **and** less
vegetation, for reasons that have nothing to do with a seep. **Under H-CONF,
conditioning on mining extent removes the association.**

**H-SEEP (the alternative).** There is a near-channel, water-quality-linked
component. **At equal mining extent, higher sulfate still predicts lower
`NDVI_stress`.**

## 3. The covariate — and why it is not circular

**Source: Ohio DNR Division of Mineral Resources Management, `MinesOfOhio`**
(`https://gis.ohiodnr.gov/arcgis/rest/services/MRM_Services/MinesOfOhio/MapServer`).

This is derived from **mine permit records, historical topographic maps and
geologic maps** — it owes **nothing** to any satellite reflectance, and nothing
to our composite. That matters more here than it did for C3b: the signal under
test is a *vegetation* index, so an NLCD-style land-cover covariate would be
partly derived from the same NDVI physics and the test would be contaminated.
A permit-record covariate cannot be.

**Coal layers used, union, fixed now:**

| group | layers |
|---|---|
| surface coal | 12 (Current), 13 (Past), 14 (Historic — topo maps), 15 (Historic — geology maps) |
| underground coal | 19 (Current), 20 (Past), 22 (Abandoned pre-1977, partially known), 23 (Abandoned pre-1977, known) |

Proposed/permitted-but-unmined layers (11, 17, 18) are **excluded** — they are
not disturbed ground. Industrial-minerals layers (25–34) are **excluded** — this
is a coal-drainage question. The union is the primary covariate; the two groups
are also reported separately.

**Primary spatial unit: the station's upstream catchment**, delineated with
MERIT Hydro D8 via the already-validated `python/catchment_dem.py` (6/6 within
±33% of published USGS drainage areas). This is the hydrologically correct unit:
sulfate at a station integrates its upstream area.

**Covariate = mined area fraction of the upstream catchment.**

**Robustness ladder (secondary):** the same fraction within fixed 1 km and 5 km
discs centred on the station.

## 4. Tests, fixed now

### T0 — REQUIRED GUARD, reported before T1 is interpreted

**Does mine extent actually predict sulfate?** Spearman rho(mine_frac, sulfate),
pooled and per watershed.

**If mine extent does not predict sulfate, H-CONF is structurally impossible** —
a variable that does not move the exposure cannot confound it — and T1 is
uninformative rather than supportive. This must be stated first, in that case,
rather than reporting a surviving partial correlation as if it were a victory.
Also reported: rho(mine_frac, `NDVI_stress`), the other leg the confound needs.

### T1 — PRIMARY: partial correlation conditioning on mining extent

**Partial Spearman** rho(`NDVI_stress_p90`, sulfate | mine_frac) at radius 30 m,
pooled across the five watersheds, computed on ranks by residualising both
variables on the rank of mine_frac.

- **Null:** within-region permutation, **5,000 draws**, shuffling sulfate
  **within watershed** — the same null that destroyed the pooled Colorado
  sulfate claim and that Arm B2 passed.
- **Per-watershed signs reported**, and sign consistency remains the headline
  check, exactly as at every prior radius.
- Between/within-region variance split reported, as always.

### T2 — SECONDARY: far-field radius extension, 500 m and 1000 m

Amendment 2 of CMD1 registered the interpretation of the radius ladder in
advance: **|rho| rising as radius grows ⇒ the association is with catchment-scale
land cover, not the seep.** The ladder currently stops at 100 m. This extends the
identical leaf-off extraction to **500 m and 1000 m**.

This tests H-CONF with **completely different machinery and no over-control
risk**, which is why it is included alongside T1.

**Registered predictions:**
- Under **H-SEEP**: |rho| at 500 m and 1000 m is **lower** than at 30 m,
  continuing the monotone trend already observed (30 > 60 > 100).
- Under **H-CONF**: |rho| is **flat or rising** out to 1000 m, because a
  landscape-scale land-cover association does not care where the buffer sits.

## 5. Decision rule — fixed before any number is computed

Applied to T1, at the pre-registered 30 m radius, on `NDVI_stress` vs sulfate.
Attenuation is measured against the published raw value **rho = −0.354**.

| outcome | verdict |
|---|---|
| partial \|rho\| ≥ 0.25, same sign, perm p < 0.05 | **CONFOUND REJECTED** — the association is not explained by mining extent |
| partial \|rho\| < 0.15, **or** perm p ≥ 0.05 | **CONFOUND SUPPORTED** — the finding is land cover; the CMD vegetation claim is **withdrawn** |
| 0.15 ≤ partial \|rho\| < 0.25, or attenuation > 40% with p < 0.05 | **PARTIAL** — materially attenuated; claim weakened, not withdrawn, and reported as weakened |

T2 does not override T1; it is reported alongside and a disagreement between them
is reported as a disagreement, not resolved by preference.

## 6. The asymmetry in what T1 can prove — registered NOW so it cannot be
invoked post hoc

**Mining extent is not a nuisance variable. It is the physical cause of the
sulfate.** Conditioning on the cause of the exposure is a conservative test, and
its two outcomes are **not** symmetric in strength:

- A **surviving** partial association is **strong** evidence: at equal mining
  extent, sulfate still tracks vegetation, which land cover alone cannot produce.
- A **collapsing** partial association is **ambiguous** between a genuine
  land-cover confound and **over-control** — removing the causal pathway that
  carries the real signal.

This asymmetry is written down now, before the result, precisely so that a
collapse cannot later be explained away as over-control by choice. **If T1
collapses, the registered verdict is CONFOUND SUPPORTED and the claim is
withdrawn** — the over-control reading may be *noted* as an alternative but may
**not** be used to keep the claim alive. T2 exists to break exactly this tie with
independent machinery.

## 7. Stated risks

- **ODNR historic-mine coverage is incomplete by construction** ("from topo
  maps", "partially known"). Under-mapping weakens the covariate and biases T0
  and T1 **toward finding no confound**. If T0 is weak, that is a live
  explanation and must be stated rather than read as "no confound exists".
- **Catchment delineation will fail or clip for some stations.** Those are
  **dropped and counted**, never silently imputed. Final n is reported next to
  every statistic, as is the count dropped.
- **n falls** from the 137 stations with sulfate to those that also have a clean
  catchment. Small-n results get the exact permutation p-value, not a hand-wave.
- **500 m and 1000 m buffers will cross land-cover boundaries and other streams.**
  That is inherent to the test, not a defect; `n_px` is reported per radius.

## 8. Wording constraint — unchanged and non-negotiable

**Sulfate has no VNIR absorption.** Nothing in this phase may be reported as
optical sulfate detection at any concentration. Any association is with
vegetation, iron precipitate, turbidity or colour that **co-varies** with
sulfate, and must be worded that way in every output.

## 9. What would falsify what

| claim | falsified by |
|---|---|
| H-CONF (the confound explains it) | partial \|rho\| ≥ 0.25 with p < 0.05 at equal mining extent |
| H-SEEP (near-channel signal exists) | partial \|rho\| < 0.15 or p ≥ 0.05; **or** T2 showing \|rho\| flat/rising to 1000 m |
| "mining extent is a valid confound at all" | T0 showing mine_frac does not predict sulfate |
| any optical sulfate claim | not permitted at all — see §8 |
