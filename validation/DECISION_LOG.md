# DECISION LOG — the chronological journey

**Purpose.** `STATE.md` says *where we are*. This file says *how we got here* —
every phase, what question it asked, what was decided, and **why**, including
the wrong turns. Written so that if the chat history is lost, or months pass, or
someone asks "why did you do it that way?", the reasoning is recoverable and not
just the conclusion.

**Reading order for a cold start:** `CLAUDE.md` → `STATE.md` → this file →
the individual dated reports.

**Rule:** every phase gets a row here the day it runs. A phase that produced a
retraction or a null gets the same detail as one that produced a positive.

---

## The through-line in one paragraph

We reimplemented a published USGS land-mapping method (SIM 3466) faithfully,
proved our own "improvements" to it were regressions, then spent the water arm
discovering — four separate times — that our *controls and framing* were the
problem rather than the imagery. Each correction made the claim smaller and more
defensible. The current defensible claim is narrow, ground-truth-validated, and
terrain-bounded: **a single continuous band ratio separates AMD-affected water
from chemically-verified clean water at monitored locations in open acid-drainage
terrain, and does not transfer to forested neutral-pH coal drainage.**

---

## Phase ledger

| date | phase | question | outcome | tag |
|---|---|---|---|---|
| 2026-07 | Land replica audit | Is our tool a faithful SIM 3466 replica? | **Yes** — all 6 index formulas exact | v3.0.x |
| 2026-07 | Departure test | Were our 3 changes improvements? | **No — all regressions.** Fixing → worst-case J 0.107→0.440 (4.1×) | v3.0.x |
| 2026-07 | Water module audit | Does the water arm work? | **RETRACTED** — indices ranked the clean control highest; Ganau claim circular | — |
| 2026-08-10 | Arm A (n=6) | Does our map predict Fe better than Rockwell's? | Looked strong (rho +0.714 vs +0.257) | — |
| 2026-08-13 | Arm A retest (n=31) | Does it survive 7 river systems? | **RETRACTED** — pooled rho +0.056; LORO R² negative everywhere; signs incoherent | v3.0.11 |
| 2026-08-13 | DEM delineation | Fix `hybas_12` catchment dilution? | Built, 6/6 vs published areas (was 2/6) | v3.0.12 |
| 2026-08-14 | **B2** seep detection | Can we detect AMD at 86 confirmed source points? | **Detection NULL; dose-response POSITIVE** (rho +0.568) | v3.1.0 |
| 2026-08-14 | B2 LORO temper | Does the dose-response survive held-out regions? | **Tempered** — signs hold 4/4 but LORO R² negative → *ranks*, doesn't *predict* | v3.1.1 |
| 2026-08-15 | Sentinel-2 | Does a better sensor help? | J −0.018→+0.234 vs C1 | v3.2.0 |
| 2026-08-16 | Resolution ladder | Is resolution the constraint? | **REFUTED** — flat 10–100 m. The S2 gain was a *sensor* effect | v3.3.0 |
| 2026-08-16 | **B2b** bare-ground fix | Do bare-relative thresholds fix the classifier? | **FAILED** — mechanism confirmed 16/16, fix changed nothing | v3.3.1 |
| 2026-08-16 | **B2c** continuous score | Is *thresholding* the problem? | **Yes** — J 0.000→+0.617 vs bare ground. Still PARTIAL on in-stream | v3.4.0 |
| 2026-08-16 | **B2d** chemistry controls | Were the in-stream controls contaminated? | **Yes** — 104/446 had Fe ≥1 mg/L. J 0.178→0.297. Score tracks *contamination* | v3.5.0 |
| 2026-08-16 | **CMD1** Ohio leaf-on | Does it transfer to neutral-pH coal drainage? | **UNINTERPRETABLE** — canopy (NDVI 0.870) | v3.6.0 |
| 2026-08-16 | CMD1 leaf-off | Same, with the canopy off | **NULL** — NDVI 0.496, no index sign-consistent | v3.7.0 |

---

## The five corrections that shaped the method

Each was a case where **we** were wrong, not the data. They are the most
transferable content in this project.

### 1. Within-sample performance lies (finding L1)
Test C's thresholds scored AUC 0.99 at Silverton and 0.63–0.67 pooled;
`FerrousIron` fell to 0.437 — *below chance*. **Consequence:** every criterion
since is judged by **worst-case leave-one-region-out**, never pooled.

### 2. Pooled significance over grouped data lies (the sulfate reversal)
A pooled sulfate correlation of rho = −0.563 (p = 0.001) **reversed sign** to
+0.220 once region structure was removed — it was 67.5% between-region variance,
i.e. comparing river systems rather than testing a relationship. **Consequence:**
the between/within variance split is now mandatory beside any pooled correlation,
and permutation nulls shuffle *within* region only.

### 3. Controls chosen by the quantity under test are circular (twice)
- **W1:** the Ganau water claim scored a site against the threshold that site
  defined.
- **C3 (mine, 2026-08-14):** I defined bare ground *by NDVI*, so `NDVI_stress`
  separated from it by construction (AUC 0.898). Caught during analysis, fixed
  with an NLCD-based control (C3b) that owes nothing to our imagery — which
  **confirmed** rather than overturned the affected result.

**Consequence:** controls must come from an external source, and a positive
control is run to prove the guard works.

### 4. Our controls contained the thing we were detecting (B2d)
104 of 446 "clean" in-stream controls had measured Fe ≥ 1.0 mg/L. Three phases
of models were penalised for refusing to call polluted streams clean.
**Consequence:** controls are defined by **measured chemistry against published
EPA thresholds**, never by station type; and the original number is always
reported beside the corrected one.

### 5. A confirmed mechanism is not a sufficient cause (B2b)
The bare-ground threshold diagnosis passed its falsifiable pre-check **16/16**,
and fixing it changed *nothing* (J stayed 0.000). **Consequence:** a mechanism
check licenses a fix attempt; it does not predict success, and the pre-check is
run *before* any parameter sweep so a wrong diagnosis cannot be tuned away.

---

## Methodological infrastructure built (and why)

| device | why it exists | what it caught |
|---|---|---|
| **Pre-registration before every phase** | 3 of 4 retractions came from post-hoc choices | Kept B2c at PARTIAL when the model tied the baseline by 0.001 |
| **Worst-case LORO** | finding L1 | Every marginal claim since |
| **Within-region permutation** | the sulfate reversal | Confirmed the B2 dose-response is not the ecological fallacy |
| **Leakage positive control** | held-out tests silently stop being held out | Fired correctly 3/4 tiers; the 1 failure is reported, not hidden |
| **Canopy diagnostic** | a null must not be confused with a blind measurement | Converted Ohio from a false "CMD undetectable" to a real, testable null |
| **Anti-goalpost-moving clause** | redefining a failing control looks like cheating | B2d: EPA thresholds, original result retained beside the new one |
| **Sign-consistency check** | Arm A's collapse | Killed paper2's GreenNIR indices 3 separate times |

---

## Recurring engineering traps (each cost real time)

1. **GEE "User memory limit exceeded" is compute-GRAPH size, not pixel count.**
   `bestEffort` does not help. Tiling and batch-shrinking help only for
   *reduction* size. When a **median over hundreds of scenes** is the problem,
   the graph cannot be *built* — the fix is capping the collection
   (`S2_MAX_SCENES` / `L8_MAX_SCENES = 120`, least-cloudy). This finally
   completed Silverton after 4 failures and Ohio 5/5 after 2.
2. **Two virtualenvs.** GEE work needs `D:/dev/VPCA+STEPWISE-REGRESSION/.venv`.
3. **EE drops the band prefix on single-band `reduceRegions`** — produced an
   all-NaN `AMDclassFrac` column that read as "finds nothing".
4. **`calendarRange(11, 3)` is EMPTY, not wrapping.** Nov–Mar needs an `Or`.
5. **Dedup keys must include every varying parameter** — omitting
   `k_bare`/`clay_bare` collapsed 8 grid points onto 1 and produced a verdict
   from 1/8 of the data.
6. **Waiters must watch for process exit, not output files.** A crashed job left
   a waiter polling for 7 hours for a file that would never be written.

---

## Claims: what may and may not be said

**MAY claim**
- Faithful SIM 3466 replica (index level, exact).
- Our three departures were regressions; fixing them improved worst-case
  cross-site J 4.1×.
- Continuous `FerricIron1` separates AMD-affected from **chemically-verified
  clean** water at **monitored locations**, out-of-region across 4 Colorado
  districts, with a score **monotone in measured contamination**.
- Continuous scoring separates mine discharge from bare ground (J +0.617) where
  the binarised classifier cannot (0.000).

**MAY NOT claim**
- Finding unknown sources in blind scene-wide search — **untested**.
- Optical **sulfate** detection at any concentration — sulfate has no VNIR
  absorption. Ever.
- That resolution is the constraint — **refuted** for 10–100 m in Colorado.
- That the method works for neutral-pH coal drainage — **measured null**.
- That agreement with Rockwell's map means accuracy — it is an automated
  product, not ground truth.

---

## Open, in priority order

1. **Riparian-only sampling (Ohio).** Circular 60 m buffers around metre-wide
   streams are mostly floodplain even leaf-off. Directly tests the leading
   explanation for the CMD null. Cheap.
2. **Blind-search test (Colorado).** The gap between "scores known points
   correctly" and "finds unknown sites" is the difference between a severity
   tool and a discovery tool.
3. **UAV comparison**, once (1) bounds what satellite geometry can do.
4. Arm A DEM re-run; land-arm uncalibrated constants (`ferric1/2StdMult`,
   `ferrousStdMult` are 0.5 by assumption); departures D4–D6 unmeasured.
