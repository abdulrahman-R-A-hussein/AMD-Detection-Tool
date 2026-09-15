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
| 2026-08-16 | CMD1 geometry | Was the null a sampling-geometry artifact? | **Yes, partly** — monotone gradient; PARTIAL at 30 m; signal is *vegetation* | v3.8.0 |
| 2026-09-08 | **CMD2** confound | Is the Ohio vegetation–sulfate link just mining land cover? | **Confound REAL** (+0.519 / −0.283). Primary **PARTIAL by 0.004**. **T2 REFUTES the near-channel reading** — \|rho\| peaks at 1 km | v3.9.0 |
| 2026-09-09 | **Tool v3.1.0** | Can the tool be pointed at any area of interest? | **It could not** — 30 hardcoded AOIs + 5 hand-synced dicts. Now free-form on both surfaces. **3 UI defects fixed**; the AOI extent was silently a classification parameter | tool `v3.1.0` |
| 2026-09-09 | **CMD3** PA replication | Does CMD2's landscape-scale reading hold in another coal basin? | **FAILS TO REPLICATE** on the named falsifier. **Sign replicates** (−0.187, n=443, p=0.0002, **first sign-consistent CMD result**); **scale does not** — PA is monotone *declining*, the opposite of Ohio. CMD2 **bounded to Ohio**; radius shape **fails as a mechanism diagnostic** | v3.10.0 |
| 2026-09-13 | **Record + grant readiness** | Does the outward-facing record match the measured one, and is there an honest grant case? | **It did not** — 9 documents incl. the DOI'd `CITATION.cff` asserted retracted water detection. Corrected; **0 live hazards**. Added ACCURACY_ASSESSMENT, GRANT_CASE, FIELD_CAMPAIGN. One load-bearing number (0.440) was **untraceable to raw output** — regenerated, reproduces exactly. Planned UAV prediction found **non-discriminating**. Python arm made runnable off this machine | v3.10.0 |
| 2026-09-14 | **Audit** while scoping the next test | Is anything the blind-search test and the SpectraLab module would build on defective? | **Eight defects, all verified.** Arm A σ computed per catchment; Arm A's 31 rows = **28** distinct polygons, 3 leaking across LORO; Creede/Lake City **geology mislabelled** (USGS I-2799, I-962) and OPEN #1's recommendation to test on the generating data **withdrawn**; `convolve_splib07` crashes on NumPy 2.x; CMD2 bars don't transfer to PA; a comment claimed an extraction that never happened. Later the same day: `partial_spearman` could return **11.97** in a degenerate case — fixed, and a golden test proves no committed CMD2 value moved. Writing the B2 golden tests: "sign-consistent across four districts" hid **Leadville ρ = +0.004 (n=23)**. Claim narrowed to three of four districts in 6 documents; no number moved. **No retraction rescued** | — |
| 2026-09-14 | **Blind search** registered | Does the tool find mine sources it was not told about? | **Registered before any landscape data.** Co-primary H-BS1 (32 mine sites, never-analysed districts) and H-BS2 (50 mine sites, unused stations); power 0.54 / 0.64 at a threefold lift. **Spring-only sites (43 of 93 in H-BS2) moved to sensitivity before any score existed** — keeping them would have tested spring-finding. Bare-ground baseline; mutually exclusive verdict rows. **Result pending** | — |
| 2026-09-14 | **`amdtool` package + SpectraLab module** (Parts A, C) | Can another application import the validated pipeline without moving one committed number? | **So far yes, proven by tests.** 68 tests rebuild exactly, from raw extractions: CMD1 (16 lines), CMD2 T1 (every line, permutation p included), the CMD3 ladder, B2 worst-case J **0.234**, and the ρ **+0.568** / LORO R² **−0.538** lines. WQP consolidation is byte-identical. `ee_auth` resolves identically to the pre-refactor commit in 6 cases. Permutation p is RNG-identical to legacy. SpectraLab `amd` module on a branch: the offline run equals `amdtool` called directly; suite 509 passed. **Deliberately not done:** a pyproject extra, which would break `uv lock` off this machine and point at a PyPI name that is not ours. **Pending:** remaining legacy scripts → wrappers, regenerated-report diffs, live 1e-12 re-extraction, UI end-to-end run | — |
| 2026-09-15 | **B2 reproduction audit** (found building the refactor gate) | Do the committed B2 reports regenerate from committed code and data? | **Yes, byte for byte, but only in an unrecorded input order**, and regenerating exposed two defects. (9) Worst-case J was evaluated inside runs of **tied scores**, which made it order-dependent: **6 printed values change** (L8 `AMDclassFrac` vs C2 0.000 → +0.235; v3 classifier vs C3b 0.000 → **−0.252**; B2b grid 0.000 → −0.452…0.000). (10) The C3b report **pooled a cloud-unfiltered composite** (161/138 scenes) into its C2/C3 tiers. (11) Input order was never recorded. **No verdict changes**; no row crosses 0.25; the claims that leaned on the zeros get stronger. Fixed in `amdtool` and tested against brute force; errata banners on 4 reports, preregistrations untouched | — |
| 2026-09-15 | **Legacy scripts → `amdtool` wrappers** (Part A gate) | Does turning `seep_detect`, `cmd_detect`, `cmd_confound` and `fetch_wqp` into wrappers move any number? | **No, apart from the deliberate tie fix.** CMD1, CMD2 and B2 dose-LORO regenerate identically through the wrapper CLIs, and CMD3 identically in its CLI part. A live Monday Creek re-extraction matches the committed file exactly (27 stations, max abs diff 0.000). B2 detection tables change only in the 5 tie-corrected rows. **Recomputing p changes one reading:** `AMDclassFrac` vs C2 becomes significant (L8 q 0.0004, S2 q 0.031) while staying below the J bar, so no verdict moves; a first draft of the audit had said those rows stayed far from significance, written before p was recomputed. **Found on the way:** the first copies into `amdtool` had **dropped 53 rationale comments and 9 docstrings**, which AST identity cannot see; all restored before conversion. 185 tests | — |
| 2026-09-15 | **Blind-search analysis hardened, before any result** | Does the analysis code do everything the registration promises? | Checked section by section against the registration, **on synthetic districts only**; no real score was analysed. **Two registered items were missing and are now implemented:** §9's link-distance 100 m / 500 m sensitivity (the same registered stations re-clustered; at 250 m it reproduces the registered 32 / 50 / 37 primary sites exactly) and §10's rule that the field frame must say when the verdicts do not support visiting it. §5's dropped landscape points are now counted in the report. **Still to run:** the snow-masked sensitivity, a second Earth Engine extraction after the primary one. Also fixed, found by SpectraLab's first live run: a failed preview download left a **0-byte PNG**. Earth Engine hit its memory limit at 1024 px; the preview now halves to 512 / 256 px and files are written only from complete downloads. 202 tests | — |
| 2026-09-15 | **Last traceability gaps closed** | Can B2's quoted dose-response p = 0.0004 be regenerated, and does the tied-score defect reach the land arm? | **The p is regenerated exactly; the land arm is unaffected.** The p and q in ARM_B2's Part 2 table existed only in that .md report. Committed code now reproduces all five rows (36 tests, 5,000 within-district draws, seed 20260814, districts in REGIONS order), and a test pins them. At 10,000 draws the same pair gives p = 0.0002, so 0.0004 is a Monte Carlo resolution, not a property of the data. The land-arm Youden searches use only distinct cuts, and the paper-faithful test scores binary predictions, so audit item 9 does not reach them. 207 tests | — |

---

## The nine corrections that shaped the method

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

### 6. A monotone trend inside a narrow window is not a trend (CMD2, and the second time)
CMD1 measured `NDVI_stress` vs sulfate at 30, 60 and 100 m, saw 0.354 → 0.253 →
0.255 as the radius grew, and concluded the target was **near the channel** —
"geometry-limited", with a UAV justification drawn from it. Extending the same
ladder to 500 m and 1000 m gave **0.393 and 0.438**: the curve is a **U**, and
its maximum is at the *largest* footprint tested. The three-point window had
been sitting on the descending left arm.

**This is the second time in this project.** The Colorado "resolution is the
binding constraint" claim failed the same way — clean inside 30 m → 20 m,
reversed once the ladder was extended within one sensor.

**Consequence:** a ladder must be extended until the trend **turns or
plateaus**, and a direction of effect may not be claimed from an interior
window. It also cost the second of two UAV arguments this project has had to
withdraw, both of which had felt like the most concrete instrumentation case
available at the time.

**THIRD INSTANCE, and it goes further (CMD3, 2026-09-09).** Extending the
ladder was not enough either. Pennsylvania's full 30→1000 m ladder is
**monotone declining** (−0.143 → −0.050 on sulfate; −0.187 → **+0.003** on
conductance) — the **opposite shape** from Ohio's U-rising-to-1 km. Each
basin's result is the other's registered falsifier.

So the deeper lesson is not about window width at all: **radius shape does not
diagnose mechanism.** CMD1 amendment 2 registered it as the way to tell "seep"
from "catchment-scale land cover", and it returns *opposite mechanisms for the
same drainage type*. It is more plausibly measuring basin geometry — how
disturbance sits relative to monitoring stations — than anything about seeps.

**Consequence:** a shape-of-curve argument cannot carry a mechanism claim
across sites unless the shape itself has been shown to transfer. If mechanism
is the question, vary mechanism, not footprint. And CMD2's catchment-scale
conclusion is **bounded to Ohio**, not withdrawn — the Ohio measurement stands;
only its generality does not.

### 9. A prediction must be one the baseline could fail (field campaign, 2026-09-13)
The grant plan proposed a falsifiable drone test: low-altitude imaging would
bring the canopy diagnostic (median buffer NDVI) below 0.6. Checked against
existing results, **leaf-off satellite already does that** — 0.462 in Ohio,
0.529 in Pennsylvania. The prediction could not fail for the drone *or* the
satellite, so it could not tell them apart, and would have "confirmed" a drone
on evidence the satellite already provides.

**Consequence:** a test of added value is run against the baseline on the same
units. H-UAV now compares UAV and leaf-off satellite at the same chemistry
stations, with mutually exclusive rows: UAV meets the bar and satellite does
not / both meet it / UAV does not.

**A related near-miss the same day:** a load-bearing figure (0.440) was cited
in five documents but existed only in prose reports, so every "verification" of
it had compared one summary with another. **A number is verified only against
raw output.** Regenerated and committed, it reproduced exactly.

### 8. A pre-registered verdict table must have MUTUALLY EXCLUSIVE rows (CMD3)
CMD3's registration listed three outcomes: `(a) and (b) → REPLICATES`,
`(a) or (b) not both → PARTIAL`, and `neither, or |rho| peaks at 30 m → FAILS`.
The result satisfied **(a)**, failed **(b)**, *and* peaked at 30 m — so rows 2
and 3 both applied and disagreed. Row 2 was the kinder one.

**The specific named falsifier governed: FAILS TO REPLICATE.** But the
registration should never have permitted the choice. Enumerating a named
falsifier alongside a generic partial branch that the same data can satisfy
leaves exactly the post-hoc latitude the registration exists to remove.

**Consequence:** verdict rows are checked for mutual exclusivity *before*
committing the registration, and where they can overlap, the registration states
which row wins in advance.

### 7. A widget that hard-codes state next to the state it mirrors will drift from it (tool v3.1.0)
`settings.useStdDevThresholds` was `true`; the checkbox that displays it
rendered `value: false`. GEE's `ui.Checkbox` does not fire `onChange` from its
constructor, so the two simply disagreed: the tool booted in adaptive mode
while the UI claimed fixed, the first click was a silent no-op, and the
**second** click switched the whole classification to the absolute thresholds
that measured worst-case J 0.107. The same defect appeared twice more in the
same file — the date boxes armed `useSpecificDate` from a partially-typed
range, and the σ sliders started at 2.0/1.5 against calibrated 0.5/0.25 with a
slider *minimum* of 1.0, so any drag silently applied a configuration this
project had measured at **J = 0.000**.

**Consequence:** a widget's initial value is always **read** from the setting it
displays, never written beside it; and a control whose calibrated value is not
inside its own range is a trap, not a control. Threshold edits are now staged
behind an Apply button, so no single gesture can silently replace a calibrated
classification.

**The deeper one, found underneath those three.** `applyStdDevThresholding`
reduced over `settings.currentRegion`, which made the **AOI extent a
classification parameter** — the same pixel changed class depending on how big a
circle the operator drew, and nothing in the UI said so. The calibration was
fitted at 8–15 km; the shipped presets ranged 1 km to 100 km. Statistics now
come from a fixed 12 km circle on the AOI centre.

**Consequence, and it generalises past this file:** this is the same family as
"never put an absolute cutoff on a non-normalised index" — a *scene-relative*
cutoff is only meaningful if the scene is fixed. Any statistic used as a
threshold must be computed over a region recorded as a parameter, never over
whatever the operator happened to be looking at.

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
- In coal watersheds a **vegetation** index tracks measured sulfate and
  conductance **negatively**, and this replicates across two independent basins.
  In Pennsylvania it is **sign-consistent across three disjoint sub-basins**
  (conductance −0.187, n=443, p=0.0002) — the first sign-consistent result the
  CMD arm has produced.
- In **Ohio** the mining-extent confound is **real** (mine extent → sulfate
  +0.519, → `NDVI_stress` −0.283) and carries ~42% of it.

**MAY NOT claim**
- Finding unknown sources in blind scene-wide search — **untested**.
- Optical **sulfate** detection at any concentration — sulfate has no VNIR
  absorption. Ever.
- That resolution is the constraint — **refuted** for 10–100 m in Colorado.
- That the method works for neutral-pH coal drainage — **measured null**.
- That the Ohio vegetation signal is **near-channel** or seep-scale —
  **refuted 2026-09-08**: |rho| peaks at 1 km, which is CMD1's own
  pre-registered signature of catchment-scale land cover. **The UAV argument
  drawn from the CMD1 geometry gradient is withdrawn** — the second UAV
  argument this project has had to withdraw.
- That the coal-basin association is **landscape-scale in general** — CMD3
  bounded that to Ohio. Pennsylvania's ladder is monotone *declining* and dead
  at 1 km (+0.003, p = 0.96). The scale is **basin-specific**.
- That **radius shape diagnoses mechanism.** It returns opposite mechanisms for
  the same drainage type in two basins, so it more plausibly measures basin
  geometry. A shape-of-curve argument cannot carry a mechanism claim across
  sites unless the shape has been shown to transfer.
- That Pennsylvania's association is **conditioned** — it is not, and cannot be
  with anything available. ODNR is Ohio-only; NLCD is rejected for sharing the
  NDVI physics.
- That the Ohio mining-extent confound has been **cleared** — the primary test
  missed its pre-registered bar by 0.004 (PARTIAL, not rejected).
- That agreement with Rockwell's map means accuracy — it is an automated
  product, not ground truth.

---

## Open, in priority order

1. ~~**Mining-extent confound test (Ohio).**~~ **DONE 2026-09-08 (CMD2).**
   The confound is **real and operative**; the primary test came back
   **PARTIAL by 0.004**; and T2 refuted the near-channel reading outright.
   The claim stays "vegetation index tracks sulfate", now qualified as
   **landscape-scale**, and never "we detect seeps".
   **Successor:** a better disturbance covariate (ODNR historic coverage is
   incomplete, so the surviving −0.246 is most plausibly land cover it missed),
   and the 1 km/5 km disc sign consistency tested on data that did not
   generate it.
2. ~~**Tighter / channel-masked sampling (Ohio).** The radius gradient has not
   bottomed out at 30 m.~~ **Superseded 2026-09-08.** It *had* bottomed out —
   the ladder is U-shaped and tightening further sampled the wrong end.
2. **Blind-search test (Colorado).** The gap between "scores known points
   correctly" and "finds unknown sites" is the difference between a severity
   tool and a discovery tool.
3. **UAV comparison**, once (1) bounds what satellite geometry can do.
4. Arm A DEM re-run; land-arm uncalibrated constants (`ferric1/2StdMult`,
   `ferrousStdMult` are 0.5 by assumption); departures D4–D6 unmeasured.
