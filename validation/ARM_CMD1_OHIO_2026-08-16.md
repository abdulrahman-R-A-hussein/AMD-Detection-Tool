# Phase CMD1 — Ohio coal mine drainage: the canopy blocks the measurement

**Date:** 2026-08-16 · **Pre-registration:** [`CMD1_PREREGISTRATION_2026-08-16.md`](CMD1_PREREGISTRATION_2026-08-16.md)
committed **before any Ohio imagery was extracted**
**Raw output:** [`report_cmd1_ohio_2026-08-16.txt`](report_cmd1_ohio_2026-08-16.txt)

## Verdict: UNINTERPRETABLE — canopy-limited. This is NOT a null.

> At 30 m Landsat, the 60 m buffers around Ohio CMD stream stations are
> **closed forest canopy**: median NDVI **0.870** (p90 statistic) and **0.791**
> (mean statistic), p10 = 0.660, with only **5.1%** of buffers below NDVI 0.4.
> The pixels survive the water mask (median 26 per buffer) — they are simply
> **trees**.
>
> The pre-registered rule says a null under these conditions is a **measurement
> limitation**, not evidence against the hypothesis. That rule is applied here.

Every index shows **inconsistent signs** across watersheds and |rho| ≤ 0.24
pooled, which is exactly what looking at a forest canopy should produce. Without
the canopy diagnostic this would have been written up as "CMD is undetectable at
neutral pH" — a wrong and much more damaging conclusion.

## Why this matters more than a null would have

Placed beside the Colorado result, this produces a **terrain-dependent** finding
that neither region gives alone:

| | **Colorado** (San Juan / Mineral Belt) | **Ohio** (Appalachian coal basin) |
|---|---|---|
| terrain | open alpine, above treeline | closed deciduous forest |
| drainage type | **acid** metal-mine (AMD) | **neutral-pH** coal (CMD) |
| median buffer NDVI | low, non-canopy | **0.79–0.87** |
| detection vs clean water | **J = +0.30** ✅ | **not measurable** |
| dose-response | **rho = +0.568** ✅ | **not measurable** |
| does finer resolution help? | **No** — flat 10–100 m | **untested, but canopy is the barrier** |

**The satellite method works where the ground is visible and fails where it is
not — and the failure is optical access, not chemistry.** In Colorado, resolution
is provably *not* the constraint (flat across a 10× range). In Ohio, the
constraint is that 30 m pixels integrate over a canopy that hides the stream
entirely.

## Consequence for instrumentation — and it reverses our earlier conclusion *for this terrain*

On 2026-08-16 we refuted "resolution is the binding constraint" using Colorado
data, and redirected the instrumentation argument to the spectral axis. **That
conclusion is Colorado-specific and does not transfer to forested CMD terrain.**

In closed-canopy Appalachian watersheds the limiting factor is **optical access
to the streambed and seep**, which no satellite band configuration solves —
a 10 m or even 1 m nadir pixel still sees canopy. What changes the measurement
is a platform that can image **beneath or between the canopy**: low-altitude UAV
flight along the channel, off-nadir viewing, or leaf-off seasonal timing.

**This is a stronger and more specific drone justification than the resolution
argument ever was**, and it applies precisely to the terrain the research
programme targets. It is also falsifiable: fly the same watersheds leaf-off and
at low altitude, and the canopy diagnostic should drop below the 0.6 threshold.

## What was actually established

1. **Ohio CMD is genuinely neutral-pH.** Median pH 7.46–7.72 across five
   watersheds — the premise of the research programme, confirmed on real data
   rather than assumed.
2. **The target-vs-control design does not transfer.** Ohio has **1**
   mine-discharge source point versus Colorado's 86; WQP records CMD discharges
   as ordinary in-stream stations. Design changed to dose-response *before*
   extraction, not after seeing results.
3. **Canopy, not chemistry, is the Ohio barrier** — established with a
   diagnostic registered in advance, under two different statistics.

## What was NOT established

- **Nothing about whether CMD is optically detectable at neutral pH.** The
  measurement never reached the water. H-CMD1 and H-CMD2 remain **untested**,
  not refuted.
- No sulfate claim of any kind. Sulfate has no VNIR absorption; that constraint
  was binding throughout and no result here approaches it.

## Immediate next steps this implies

1. **Leaf-off imagery.** Re-run the identical pipeline on Nov–Mar composites.
   Deciduous canopy is absent; if the diagnostic drops below 0.6 the hypothesis
   becomes testable from satellite. **Cheap, and the obvious first move.**
   Note this breaks the SIM 3466 May–Jul mineral-mapping season, which is a
   deliberate, declared departure — the season exists for mineral mapping in
   open terrain, not for seeing under a canopy.
2. **Riparian-only sampling.** Restrict buffers to pixels adjacent to the mapped
   channel rather than a circular buffer, to exclude hillslope forest.
3. **Only then** the UAV comparison, which now has a specific, measured
   justification rather than a generic resolution argument.

## Coverage

4 of 5 watersheds extracted (159 stations). **Sunday Creek failed on the Earth
Engine memory limit** twice and is absent; its 28 stations are not in these
numbers. The canopy conclusion does not depend on it — the four extracted
watersheds agree closely on NDVI.

## Reproduce

```
python cmd_detect.py --extract --regions <slug>
python cmd_detect.py --analyse --perms 5000
```
