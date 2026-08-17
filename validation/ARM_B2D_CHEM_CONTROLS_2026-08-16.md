# Phase B2d — the detection failure was our control design. The score tracks chemistry.

**Date:** 2026-08-16 · **Pre-registration:** [`B2D_PREREGISTRATION_2026-08-16.md`](B2D_PREREGISTRATION_2026-08-16.md)
committed `56aa3aa` **before any analysis**
**Raw output:** [`report_b2d_chemcontrols_2026-08-16.txt`](report_b2d_chemcontrols_2026-08-16.txt)

## Two results, and the second one is the important one

> **1. The in-stream failure was an artifact of using contaminated water as a
> negative class.** With controls defined by measured chemistry instead of
> station type, worst-case leave-one-region-out J against clean water goes
> **0.178 → 0.297**, clearing the pre-registered 0.25 bar. *(Original
> station-type result retained: 0.178.)*
>
> **2. The score tracks CONTAMINATION, not mine infrastructure.** Median score,
> monotone in measured chemistry:
>
> | class | n | median score |
> |---|---|---|
> | C1clean — chemically clean streams | 222 | **−0.718** |
> | C1grey — intermediate | 86 | −0.211 |
> | target — mine discharge points | 86 | +0.899 |
> | **C1dirty — contaminated streams, NOT mine infrastructure** | 133 | **+1.157** |
>
> Contaminated streams score **above the mine discharge points themselves.** The
> registered prediction was that C1dirty must exceed C1clean; it exceeds the
> targets.

## Why result 2 settles a question three phases could not

Every prior failure was ambiguous between two explanations: the score detects
**AMD contamination**, or it detects **mine workings and disturbed ground**.
C1dirty separates them — contaminated streams are chemistry without mining
infrastructure.

They score highest of any class. **The score is responding to water chemistry,
not to the presence of a mine.** This also explains, retrospectively and
consistently, why J against C1dirty is **−0.311**: the model cannot separate
targets from contaminated streams *because both are AMD-affected*. Correct
behaviour that the old control design was scoring as failure.

## The detection numbers

| tier | model J | `FerricIron1` alone | perm p | per-region model J |
|---|---|---|---|---|
| **C1clean (PRIMARY)** | **0.297** | **0.298** | 0.0020 | +0.51 +0.30 +0.60 +0.55 |
| C2 terrain-matched | 0.319 | 0.291 | 0.0020 | +0.64 +0.32 +0.59 +0.63 |
| C3b NLCD barren | 0.617 | 0.318 | 0.0020 | +0.65 +0.62 +0.75 +0.88 |
| C1grey | 0.252 | 0.086 | 0.0020 | +0.39 +0.25 +0.26 +0.36 |
| C1dirty *(positive control)* | −0.311 | −0.067 | 0.964 | — |
| C3 *(excluded, circular)* | 0.420 | 0.318 | 0.0020 | — |

**Verdict: PARTIAL**, by the letter of the pre-registered rule. All three
decision tiers clear J ≥ 0.25 with BH p < 0.05, but the rule also required the
model to **beat `FerricIron1` alone**, and on C1clean it ties: **0.297 vs
0.298**, short by 0.001. Reported as PARTIAL, not rounded up.

## The cleaner claim: one band ratio does it alone

`FerricIron1` (SR_B4/SR_B2, red/blue) **used continuously** clears the
pre-registered bar on **all three** decision tiers unaided:

| tier | `FerricIron1` alone |
|---|---|
| C1clean | **+0.298** |
| C2 | **+0.291** |
| C3b | **+0.318** |

This is simpler, more transferable and easier to defend than a fitted
8-feature model, and the model adds nothing to it on the primary tier. **The
honest headline is the single index, not the model.**

`C1grey` behaves as the intermediate class should: model 0.252, single index
0.086 — the multi-feature model helps most where the chemistry is ambiguous.

## What may and may not be claimed

**May be claimed.** Continuous `FerricIron1` separates AMD-affected water from
**chemically-verified clean water** at monitored locations, out-of-region
(worst-case across 4 districts, held-out, 500-draw model null, BH-corrected),
and its score is **monotone in measured contamination** across four independent
classes.

**May NOT be claimed.** That the tool *finds* unknown AMD sources in a blind
search. Every point scored here is a known monitoring station. Blind search over
a full scene is untested and is a different problem — the prior against it is
the bare-ground and background-geology confounds already documented.

**Wording constraint from the pre-registration, honoured:** the claim is
"detects AMD against chemically-verified clean water", **not** the broader
"detects AMD" — the original station-type C1 result does not support the latter,
and that result stays on the record at 0.178.

## Anti-goalpost-moving audit

Redefining a control after it caused failures deserves scrutiny. The three
binding commitments made in advance, and how they held:

1. **Thresholds are published EPA standards** — Fe < 0.3 mg/L (secondary
   drinking-water), pH 6.5–9.0 (aquatic life) for clean; Fe ≥ 1.0 or pH < 6.0
   for dirty. Written down in `56aa3aa` before any run. ✅
2. **The original result is retained and reported beside the new one** —
   0.178 appears in the raw output header and in this report. ✅
3. **Grey band excluded from both classes and counted** (86 stations), not
   forced into whichever class helped. ✅

**Verification that only the control definition changed:** C2 reproduces B2c
exactly (0.319) and C3b exactly (0.617); the `FerricIron1` baseline reproduces
+0.318 vs C3b. Nothing but the C1 relabelling moved. ✅

## Class counts

| region | clean | dirty | grey |
|---|---|---|---|
| Central City | 80 | 49 | 14 |
| Leadville | 39 | 13 | 19 |
| Ouray | 64 | 23 | 20 |
| Silverton | 39 | 48 | 33 |

Silverton has more contaminated than clean in-stream stations — unsurprising for
the Animas, and a concrete illustration of why the old station-type control was
untenable there.

## Limitations

- Colorado Mineral Belt only. The Ohio coal basin is the registered second
  terrain and the outstanding test of B2b's background-geology explanation.
- Sentinel-2, primary 60 m buffer, p90 statistic. Landsat has no C3b coverage.
- Known monitoring locations, not blind search (see above).
- `C1clean` is smaller than the old `C1` (222 vs 446), so intervals are wider.

## Reproduce

```
python continuous_detector.py --sensor S2 --model-perms 500
```

Repo `.venv` — no Earth Engine needed.
