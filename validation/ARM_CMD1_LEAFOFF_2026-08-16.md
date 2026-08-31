# CMD1 Amendment 1 — leaf-off retest: the canopy came off, and the signal is not there

**Date:** 2026-08-16 · **Registered:** [`CMD1_PREREGISTRATION_2026-08-16.md`](CMD1_PREREGISTRATION_2026-08-16.md)
Amendment 1, committed **before the run**
**Raw output:** [`report_cmd1_leafoff_2026-08-16.txt`](report_cmd1_leafoff_2026-08-16.txt)

## Verdict: NULL — and this time it is a real, interpretable null

> **The retest worked as a measurement.** Median buffer NDVI fell
> **0.870 → 0.496** (p90) and **0.791 → 0.426** (mean), below the pre-registered
> 0.6 canopy limit. Registered prediction 1 **confirmed**: deciduous canopy was
> the May–Jul barrier. Coverage also improved, 159 → **187 stations**, all five
> watersheds.
>
> **And with the ground visible, there is still no signal.** No index is
> sign-consistent across the five watersheds against either sulfate or specific
> conductance. Best |rho| = 0.253 (`NDVI_stress` vs sulfate, p = 0.075), with
> signs disagreeing. **NULL by the pre-registered rule.**

The July run said "we cannot see." This run says "we can see, and it is not
there." Those are different findings, and only the second one is evidence.

## Season comparison — the diagnostic working as designed

| | median NDVI p90 | median NDVI mean | n | verdict |
|---|---|---|---|---|
| leaf-on (May–Jul) | 0.870 | 0.791 | 157 | **UNINTERPRETABLE** |
| **leaf-off (Nov–Mar)** | **0.496** | **0.426** | **187** | **NULL** |

This is the value of registering the canopy diagnostic in advance: it converted
an unusable result into a testable one, and it named the fix before the fix was
tried.

## What this establishes

**The Colorado method does not transfer to Ohio coal drainage.** Same indices,
same buffer geometry, same statistics, same permutation null:

| | Colorado (acid, open alpine) | Ohio (neutral CMD, leaf-off) |
|---|---|---|
| detection vs clean water | **J = +0.30** | not applicable (1 source point) |
| dose-response, best index | **rho = +0.568**, sign-consistent 4/4 | **signs disagree 5/5** |
| verdict | positive | **NULL** |

**H-CMD2 is refuted as stated.** The prediction was that neutral-pH CMD would be
*not weaker* than Colorado, on the mechanistic argument that fast Fe(II)
oxidation concentrates ochre at the discharge. Ohio is weaker, and not
marginally.

## What this does NOT establish — the boundary matters

This is a null **at 30 m, in 60 m circular buffers, from satellite**. It does
not show that no optical signal exists at a CMD seep. Three specific reasons,
none of them excuses, all of them testable:

1. **Sampling geometry still misses the target.** Ohio streams are metres wide;
   a 60 m circular buffer at 30 m pixels is mostly floodplain and forest floor
   even leaf-off. The signal, if it exists, is on the streambed and the seep
   face — a few square metres. **Test: riparian-only sampling** restricted to
   pixels adjacent to the mapped channel.
2. **Leaf-off brings its own artifacts**, registered in advance: low sun angle,
   long shadows, wet ground. These add noise and could mask a weak signal.
3. **Neutral-pH ochre may be thin rather than extensive.** Rapid oxidation
   concentrates iron *at* the discharge rather than spreading it downstream —
   which was the argument *for* H-CMD2, but it equally predicts a very small
   footprint that 30 m pixels cannot resolve.

Reason 1 and reason 3 point the same way: **the target is likely sub-pixel at
Landsat scale.** That is a resolution argument — but note it is a *geometry*
argument specific to narrow forested streams, not the generic resolution claim
that Colorado data already refuted.

## Consequence for the research programme

The honest position after two Ohio runs:

- **Satellite AMD detection works in open, acid, metal-mine terrain.** Proven,
  out-of-region, against measured chemistry.
- **Satellite CMD detection in forested Appalachian terrain is not demonstrated
  and is now a measured null**, with sampling geometry and sub-pixel footprint
  as the leading remaining explanations.
- **This is the strongest, most specific case yet for airborne/UAV work in CMD
  terrain** — not on generic resolution grounds, which Colorado refuted, but
  because the target here is a few square metres of seep face under a riparian
  corridor, in a watershed where the satellite measurement has now been shown to
  see the ground and still find nothing.

That is a defensible, falsifiable, and publishable boundary statement: it says
where the free-satellite method works, where it fails, and what measurement
would settle the failing case.

## Also fixed this run: the recurring Earth Engine memory failure

**5 of 5 watersheds completed, including Sunday Creek**, which failed twice
before. The fix was capping the collection at the 120 least-cloudy scenes.

The root cause was never batch size or tiling: a median over hundreds of scenes
with `add_indices` mapped onto each is too large a compute graph to **build**,
so nothing downstream can rescue it. Same fix that finally completed Silverton
Sentinel-2 after four failures. Deterministic, and identical compositing depth
for every watershed so it cannot favour one.

Two further correctness items in this run:

- **Month-wrap:** Nov–Mar crosses the year boundary and
  `calendarRange(11, 3, "month")` returns **empty**, not inclusive. Handled with
  an `Or` of two ranges; unhandled it would have silently produced no scenes.
- **Snow masking** (`QA_PIXEL` bit 5), registered in advance — snow is bright
  and seasonal, and would otherwise be a season-dependent artifact that could
  masquerade as either signal or canopy relief.

## Next

1. **Riparian-only sampling** (channel-adjacent pixels, not circular buffers) —
   cheap, uses extracted data plus a channel mask, and directly tests the
   leading explanation.
2. Only then UAV, which now has a measured, terrain-specific justification.

## Reproduce

```
python cmd_detect.py --extract --season leafoff --regions <slug>
python cmd_detect.py --analyse --perms 5000 --inputs data/matched/cmdoff_l8_*.csv
```
