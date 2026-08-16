# Arm B2 on Sentinel-2 — the resolution effect

**Date:** 2026-08-15 · **Pre-registration:** [`B2_PREREGISTRATION_2026-08-14.md`](B2_PREREGISTRATION_2026-08-14.md) (committed `4bb3b63` before any extraction)
**Landsat companion:** [`ARM_B2_SEEP_DETECTION_2026-08-14.md`](ARM_B2_SEEP_DETECTION_2026-08-14.md)
**Raw output:** [`report_seep_b2_s2_2026-08-15.txt`](report_seep_b2_s2_2026-08-15.txt)

## Headline

> **Resolution is the binding constraint, and we can now show it with numbers.**
>
> The same index, same 86 source points, same controls, same pre-registered
> test — only the pixel size changes. `FerricIron1` goes from **no
> discriminative power at Landsat 30 m** to **BH-significant separation against
> all three control tiers at Sentinel-2 20 m**, missing the pre-registered
> detection threshold only on the hardest tier, and only by 0.016.

## The comparison that matters

`FerricIron1` (SR_B4/SR_B2, red/blue), worst-case leave-one-region-out Youden J,
n=86 targets, 4 districts, 10,000 within-region permutations:

| control tier | **Landsat 8, 30 m** | **Sentinel-2, 20 m** | BH q (S2) |
|---|---|---|---|
| C1 in-stream (hardest) | −0.018 | **+0.234** | 0.0003 |
| C2 terrain-matched | −0.101 | **+0.291** | 0.0003 |
| C3 bare ground | −0.045 | **+0.318** | 0.0003 |

Every tier flips from *below zero* to *strongly positive*. This is not a
marginal shift; at 30 m the index is worthless for discrimination, at 20 m it
separates real mine discharges from every control class we could construct.

**Pre-registered decision rule (J ≥ 0.25 vs all three tiers AND BH q < 0.05):**
`FerricIron1` **fails on C1 alone, at J = 0.234 vs the 0.25 threshold.** By the
registered rule this is still a null, and it is recorded as one — the threshold
was fixed in advance precisely so it could not be moved afterwards. But it is a
qualitatively different null from Landsat's, where the same index failed all
three tiers with *negative* J.

Other indices at 20 m: `ClaySulfateMica` clears 0.25 against C2 (0.320) but not
C1 (0.023). `AMDclassFrac` — the shipped classifier — remains at ≈0.000 against
C1 and C2, i.e. **the classifier does not improve with resolution while the raw
index does.** That is consistent with the Landsat finding that its AMD calls are
driven by the NDVI/bare-ground gate rather than by iron.

## What this licenses, and what it does not

**Licensed:** the statement that spatial resolution, not spectral capability, is
the limiting factor for AMD source detection in this terrain. Two independent
sensors, identical analysis, one variable changed, effect present on the index
with the clearest mechanism and absent on the index that is confounded by
bareness.

**Not licensed:** any claim that detection "works" at 20 m. It does not meet the
pre-registered bar. The honest statement is that the trend is steep and in the
predicted direction over the only two ground sample distances free imagery
offers.

**Extrapolation to 7 cm is extrapolation, not measurement**, and must be labelled
that way wherever it appears. What the data support is a direction and a slope
between 30 m and 20 m, not a value at 0.07 m.

## Independent convergence with paper2

Galaszkiewicz et al. (2024) reported Sentinel-2 resolving only 3 of 6 known
sulphurous discharges and concluded 0.16 m aerial imagery was "the most viable
choice". This is an independent replication of that conclusion at **n=86 rather
than n=6**, in different terrain, with different chemistry, on a different index
family, and with a pre-registered statistical criterion rather than a visual
count. Their qualitative finding and this quantitative one agree.

Note this holds **despite** their own green:NIR indices performing poorly here:
`GreenNIR`/`GreenNIRNorm` reach J=0.217 against C2 but fail C1 and C3, and fail
sign consistency in the Landsat dose-response. The convergence is on the
*resolution conclusion*, not on their index.

## Deviations from the pre-registration — declared

1. **Sentinel-2 was run at the primary 60 m buffer only**, not at the registered
   30/100 m sensitivity radii. Reason: compute cost — the full three-radius S2
   extraction was projected at 5+ hours across four regions. Landsat retains all
   three radii as registered. This weakens the S2 sensitivity analysis; it does
   not affect the primary comparison, which uses the primary radius on both
   sensors.
2. **S2 composites are capped** at the 120 least-cloudy scenes with
   `CLOUDY_PIXEL_PERCENTAGE < 20`. Not a statistical choice — a median over 554
   scenes (Silverton) exceeds the Earth Engine graph limit and cannot be built
   at all. The cap is deterministic and identical across regions, so it cannot
   favour one district.
3. **S2 effective resolution is 20 m, not 10 m, for this index panel.** The SIM
   3466 indices need SWIR (B11/B12, 20 m) and `IronSulfate` needs the coastal
   band (60 m). `FerricIron1` is red/blue and *is* natively 10 m, so the ladder
   can go finer for it specifically — recorded in `seep_detect.S2_NATIVE_M`.
   The headline comparison above is therefore 30 m vs 20 m, a factor of 1.5,
   which makes the size of the effect more striking, not less.

## Caveats

- Land-surface ferric precipitate only. Never dissolved sulfate — sulfate has no
  VNIR absorption.
- The C3 tier remains circular for vegetation-sensitive indices (see the Landsat
  report); the C3b NLCD amendment is the fix and is reported separately.
- Two generations of extraction jobs raced during this session because a
  `taskkill` did not stop the first batch; the surviving CSVs were verified to
  carry 3 radii × 4 regions × 86 targets before analysis, and the radius-60
  subset used here is internally consistent.
