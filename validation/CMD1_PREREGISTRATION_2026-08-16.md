# Phase CMD1 — PRE-REGISTRATION: neutral-pH coal mine drainage, Ohio

**Written 2026-08-16, BEFORE any Ohio imagery was extracted.** Own commit, as
`4bb3b63` / `df6a6ae` / `6af0b5b` / `56aa3aa` were.

## 1. Why this phase exists, and why it is the harder problem

Everything validated so far is **acid metal-mine drainage** in the Colorado
Mineral Belt, where low pH is itself diagnostic. The target of this research
programme is **coal mine drainage (CMD)** in the Appalachian basin, where
alkaline overburden buffers the acid and **sulfate contamination is hidden
under neutral pH**.

Confirmed empirically before writing this, across five Ohio CMD watersheds:

| watershed | median pH | median sulfate (mg/L) | source points |
|---|---|---|---|
| Monday Creek | 7.46 | 51.0 | 1 |
| Sunday Creek | 7.69 | 30.2 | 0 |
| Raccoon Creek | 7.60 | 100.7 | 0 |
| Huff Run | 7.72 | 23.0 | 0 |
| Leading Creek | 7.64 | 49.5 | 0 |

**pH is neutral everywhere.** Any method keyed on acidity is blind here — and
that includes **our own B2d control definition**, which files Fe < 0.3 mg/L with
pH 6.5–9.0 as "clean" and would therefore classify a 500 mg/L-sulfate neutral
CMD stream as clean water. That defect is recorded here as the direct motivation
for this phase.

**Design consequence:** Ohio has **1 mine-discharge source point** versus
Colorado's 86, so the target-vs-control design does **not** transfer. This phase
uses a **dose-response design over in-stream stations**, which needs no class
balance and which is the design that produced Colorado's robust result.

## 2. Hypotheses

**H-CMD1 (primary).** At neutral pH, optical indices track measured **sulfate**
and **specific conductance** across CMD-affected streams.

**H-CMD2 (mechanistic, and the interesting one).** At neutral pH, Fe(II)
oxidises and hydrolyses rapidly, so ochre precipitates **at** the discharge
rather than staying in solution and dispersing as it does in acid drainage.
Neutral CMD may therefore produce a **more localised, more optically visible**
iron deposit than acidic AMD — the opposite of the intuitive expectation.
**Prediction:** `FerricIron1` rho vs sulfate in Ohio is **not weaker** than its
Colorado rho vs dissolved Fe (+0.568).

## 3. Wording constraint — non-negotiable

**Sulfate has no VNIR absorption.** Nothing here may be reported as optical
sulfate detection at any concentration. Any association found is with **iron
precipitate, turbidity, vegetation, or colour that co-varies with sulfate**, and
must be worded that way in every output.

## 4. Contamination classes — from PUBLISHED thresholds, not chosen by us

Used for the secondary classification test only; the primary test is continuous.

- **Contaminated:** sulfate ≥ **250 mg/L** (US EPA secondary MCL) **or**
  specific conductance ≥ **500 µS/cm**.
- **Clean:** sulfate < **25 mg/L** **and** conductance < **300 µS/cm**
  (USEPA 2011 Appalachian aquatic-life conductivity benchmark).
- **Grey band** between: excluded from the classification test and counted.
- **pH is NOT used to classify.** That is the entire point of this phase.

Counts before extraction: contaminated 68, clean 32, grey 87.

## 5. Primary test — fixed

Spearman rho of each of the 8 continuous indices (p90, 60 m buffer) against
**median sulfate** and **median specific conductance**, per station.

- **Reported per watershed AND pooled**, with the **between/within-region
  variance split** — mandatory since the Colorado sulfate result reversed sign
  once region structure was removed.
- **Sign consistency across all five watersheds is the headline check**, exactly
  as it was for Colorado. A pooled rho with inconsistent signs is not a result.
- **Null:** within-region permutation, 5,000 draws. **Correction:** BH across
  (8 indices × 2 analytes).

## 6. The canopy diagnostic — required BEFORE interpreting any null

Appalachian streams are narrow and forest-canopied. A 60 m buffer may contain
almost no exposed ground or water, in which case a null means "nothing visible"
rather than "no relationship".

**Required, reported before any correlation:** median NDVI within the buffers,
and the count of buffers with any non-vegetated pixel. **If median NDVI > 0.6, a
null is UNINTERPRETABLE** as evidence against H-CMD1 and must be reported as a
measurement-limitation, not a negative result.

## 7. Decision rule — fixed

| result | verdict |
|---|---|
| an index shows sign-consistent rho across all 5 watersheds, BH p < 0.05, and \|rho\| ≥ 0.3 pooled | **SUCCESS — CMD signal detected at neutral pH** |
| significant pooled but signs inconsistent, or \|rho\| < 0.3 | **PARTIAL** |
| no index sign-consistent | **NULL** — reported as prominently as a success |
| median buffer NDVI > 0.6 | **UNINTERPRETABLE** — canopy-limited, stated as such |

## 8. What would falsify each claim

| claim | falsified by |
|---|---|
| H-CMD1 | no index sign-consistent across the five watersheds |
| H-CMD2 (neutral ochre is more visible) | Ohio rho materially weaker than Colorado's +0.568 |
| "the method generalises beyond Colorado" | Ohio null while Colorado holds |
| any sulfate claim | it is not permitted at all — see §3 |
