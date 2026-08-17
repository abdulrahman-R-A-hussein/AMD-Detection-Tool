# Phase B2d — PRE-REGISTRATION

**Written 2026-08-16, BEFORE any analysis was run.** Own commit, as `4bb3b63`
(B2), `df6a6ae` (B2b) and `6af0b5b` (B2c) were.

## 1. The defect this phase repairs — in our own control design

Every phase has failed on the same tier: **C1, the in-stream controls.** B2c's
continuous model scored J = 0.178 there against a 0.25 bar, and was *worse* than
`FerricIron1` alone (0.234).

Verified on disk before writing this:

| region | in-stream ("controls") | chemically clean | **dirty, Fe ≥ 1.0 mg/L** |
|---|---|---|---|
| Silverton | 122 | 39 | **31** |
| Leadville | 72 | 39 | 5 |
| Ouray | 109 | 64 | **22** |
| Central City | 143 | 80 | **46** |
| **total** | **446** | **222** | **104** |

**104 of 446 "negative controls" are AMD-affected water.** Every model has been
required to call contaminated streams "not AMD", and scored as failing when it
declined. C1 was defined by *station type*, which is a proxy; measured chemistry
is the actual quantity of interest and we already hold it.

## 2. Class definitions — from PUBLISHED standards, not chosen by us

Deliberately external so they cannot be accused of being fitted to the outcome:

- **C1clean** (negative class): Fe < **0.3 mg/L** — US EPA secondary drinking
  water standard for iron — **and** pH in **[6.5, 9.0]** — EPA aquatic-life
  criteria.
- **C1dirty** (positive control): Fe ≥ **1.0 mg/L** **or** pH < **6.0**.
- **Grey band** (between the two): **excluded from both**, and counted in the
  report. An explicit "don't know" rather than a forced call.

Stations lacking the required measurements are excluded and counted.

## 3. Primary outcome — fixed

Worst-case leave-one-region-out Youden J of the **unchanged B2c continuous
model** against **C1clean**. Same 8 features, same fixed `C = 1.0`, same folds,
same code path. **Only the control definition changes**, so any difference is
attributable to that and nothing else.

Secondary, reported: C2, C3b. C3 remains excluded (NDVI-circular).

## 4. Decision rule — fixed

| result | verdict |
|---|---|
| J ≥ 0.25 vs C1clean, C2 **and** C3b, BH p < 0.05, and beats `FerricIron1` alone | **SUCCESS — first detector claim** |
| clears C1clean but not every tier | **PARTIAL** |
| J < 0.15 vs C1clean | **NULL** — and the C1 failure was never about control contamination |

## 5. The discriminating test — new, and the scientifically interesting one

Score **C1dirty**: chemically contaminated streams that are **not** mine
infrastructure. No phase has run this.

| if C1dirty scores… | the score is detecting… |
|---|---|
| **high**, like targets | **AMD itself** — contamination wherever it occurs |
| **low**, like clean streams | **mine infrastructure / disturbed ground**, not chemistry |

**Registered prediction, stated before running: if the B2 dose-response result
is real, C1dirty must score above C1clean.** Failure to do so would undercut the
severity claim, and must be reported as undercutting it rather than explained
away.

## 6. Anti-goalpost-moving commitment

Redefining a control after it caused failures is exactly the move that should
attract suspicion. Three binding constraints, fixed here:

1. Thresholds are **published EPA standards**, written down before any run.
2. The **original C1 result (J = 0.178) stays in the record** and is reported
   **beside** every C1clean number, never replaced by it.
3. If C1clean succeeds, the claim is explicitly **"detects AMD against
   chemically-verified clean water"** — not "detects AMD", which the original
   C1 result does not support.

## 7. Verification required before any verdict

- **Class counts printed per region** (clean / dirty / grey / missing) before
  any score is computed.
- **C2 and C3b must reproduce B2c exactly** (J = 0.319 and 0.617). If they move,
  something other than the C1 relabelling changed and the comparison is void.
- **Baseline reproduction:** `FerricIron1` alone vs C3b must still give +0.318.
- **Leakage positive control** re-run, including re-checking the C3 anomaly
  observed in B2c (leak failed to inflate on that tier alone).

## 8. What would falsify each claim

| claim | falsified by |
|---|---|
| "C1 contamination explains the failure" | J < 0.15 vs C1clean |
| "the score detects AMD, not mine infrastructure" | C1dirty scoring at or below C1clean |
| "only the control definition changed" | C2/C3b failing to reproduce B2c |
| generalisability | Colorado Mineral Belt only until the Ohio coal basin is run |
