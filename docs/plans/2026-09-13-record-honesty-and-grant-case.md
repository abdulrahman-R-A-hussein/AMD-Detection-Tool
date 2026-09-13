# Make the record honest, then make the grant case from it

## Context

Three questions were asked. The honest answers:

**1. Is there a findings summary?** Partly. `ARM_CMD3_PA_REPLICATION_2026-09-09.md`
covers CMD3 and `OPERATOR_GUIDE.md` covers interpretation. **No consolidated
accuracy assessment exists.**

**2. Is accuracy summed up?** No. And there is no single number — performance
differs by task, terrain, and *which reference standard* it was measured
against. Most of the impressive figures (87.9% agreement, κ 0.546) are
agreement with **Rockwell's automated map = replica fidelity, not accuracy**.

**3. Breakthrough / best detection tool ever?** **No, and a grant claiming it
would not survive review.** Detection is a **measured null**: at n=86
chemically-confirmed source points, all nine indices failed all three control
tiers; the best case (`FerricIron1` vs C1, Sentinel-2) reaches **J = 0.234**
against a pre-registered bar of 0.25 — short by **0.016**. What exists is a
**severity-ranking tool within a district**, plus a faithful replica of a
published USGS method.

**But there is a real and fundable case, and it is stronger than an
overclaim would be** — because the grant asks for money to resolve exactly the
questions these nulls raise. A tool that already worked would need no campaign.

**The blocker, and why it goes first.** The repo holds two contradictory
narratives split almost exactly at **2026-07-25**. Nine documents assert a
validated water-detection capability that `validation/` has since retracted.
The worst is **`CITATION.cff`**, minted under **DOI 10.5281/zenodo.19429983**
and mirrored to ResearchGate, claiming *"Validated against ground truth
geochemical data from the Muskingum Watershed, Ohio"* — while `STATE.md`
records Ohio as a **clean null** (no feature's 95% CI excludes zero; iron n=17,
sulfate n=23). A reviewer who pulls the DOI and then the repo finds the
applicant contradicting himself. Nothing built on top of that record is safe
until it is fixed.

---

## Part 1 — Document remediation

**The governing rule: never rewrite the validation audit trail.** The dated
reports in `validation/` are the evidence of self-scrutiny and the most
fundable thing in the repo — pre-registration commits verifiably landing
*before* their data (`a452446`, `4765bca`, `56aa3aa`, `6af0b5b`, `df6a6ae`).
Rewriting them would destroy the asset. They get **dated banners**, never edits
to their findings.

### 1a. Rewrite from current state (marketing/overview — no historical value)

| file | the claim to remove |
|---|---|
| `README.md` | *"Successfully detected sulfate contamination (>700 mg/L) in Ganau Pond"*; *"Validated against ground truth (Ganau Lake: 675 mg/L sulfate)"*; *"reducing field survey needs by up to 80%"*; AWEINSH masking listed as an innovation; Quick Start points at `v1.0.0.js`; cites `docs/VALIDATION.md` and `docs/API_REFERENCE.md`, **which do not exist** |
| `PROJECT_OVERVIEW.md` | *"Ganau Lake (675 mg/L sulfate) — correctly classified as severe"*; *"Cost reduction of 70-90%"*; *"Continental-scale monitoring"* |
| `PUBLIC_RELEASE_SUMMARY.md` | the whole L143–176 claim block; **and the author name reads "Ahmad A. Hussein" at L18/31/82/107 vs "Abdulrahman Hussein" at L345** |
| `python/README.md` | its index formulas are **wrong** (`Iron Sulfate = B4/B2`; actual is `(B2/B1)−(B5/B4)`) |

Both READMEs become short pointers to `validation/STATE.md` and
`docs/OPERATOR_GUIDE.md` rather than parallel claim surfaces.

### 1b. Banner as superseded (historical — keep, do not edit findings)

`earth-engine/validation_results.md` (its **filename asserts validation** and
its "All clean lakes show <0.01% AMD" pass was a mask artifact — 0/497 and
0/466 water pixels admitted), `earth-engine/water_quality_module_guide.md`,
`USAGE_GUIDE.md` (instructs the reader to *tune sliders until known sites
match* — the retracted circularity), `LAYER_STRUCTURE.md`,
`FINAL_LOGIC_VERIFICATION.md` (titled *"Zero Contradictions"*),
`MASKING_LOGIC_FIX.md`, `docs/METHODOLOGY.md`, `specs/amd-v2/*`.

Banner states: date, what it described, what superseded it, and one line on
what is now known. `specs/amd-v2/validation-protocol.md` additionally still
instructs running **Test D** with a *"Pass criterion R² ≥ 0.7"* — Test D was
retracted in v2.4.1.

### 1c. Append, never rewrite

`CHANGELOG.md` — stops at v1.5.4 while code is at v3.1.0 and science at
v3.10.0. Add entries through v3.10.0 including the retractions, and a note that
the v1.5.4 "Ganau validated" entries are superseded.

### 1d. Remove refuted public-facing templates

`docs/SOCIAL_MEDIA_GUIDE.md` carries two ready-to-post templates asserting
*"validated against ground truth measurements (675 mg/L sulfate detection)"*.

### 1e. Requires your action — I draft only

- **`CITATION.cff` + Zenodo.** I write a corrected abstract and bump the
  version; **you must publish a new Zenodo version** — a local edit does not
  change a minted DOI. This is the only hazard that survives any repo cleanup.
- **`.private/EB2_DOCUMENTATION.md`** asserts the same refuted validation and
  lists the retracted water module as evidence of ability. It is gitignored and
  may already be with an attorney. **I will flag it and not touch it** —
  correcting a filing is your call, not a code change.

---

## Part 2 — `validation/ACCURACY_ASSESSMENT.md`

The document that answers "how accurate is it". Opens with the distinction
everything else depends on:

| reference | what a number against it means |
|---|---|
| Rockwell's published map | **replica fidelity only** — an automated product, never field-verified |
| measured field chemistry | the **only** ground truth |
| control tiers C1/C2/C3/C3b | accuracy *relative to that negative class*; **C3 was circular** |

Then one table per capability, every figure with n, reference, pooled-vs-
worst-case, and status. The load-bearing content:

- **Land replica** — Silverton 87.9% agreement, κ **0.546**, n=8,093 px; but
  precision vs Rockwell's AMD calls **0.137**, binary κ **0.212**. Summitville
  κ **0.080**, and the disagreement **reverses direction** (we flag 4.1× more
  at Silverton, Rockwell flags 5.6× more at Summitville) — which is why *"more
  sensitive than Rockwell"* is withdrawn. Worst-case LOSO J **0.107 → 0.440**
  over 3 sites.
- **Water detection — NULL.** Full L8 and S2 tables. Best: `FerricIron1` vs C1
  at **J 0.234** (bar 0.25). **`AMDclassFrac` vs bare ground: AUC 0.456,
  J −0.304** — the shipped classifier is substantially a bare-ground detector.
- **Severity ranking — the one ground-truth positive, tempered.**
  `FerricIron1` vs dissolved Fe **+0.568** (n=75, within-region perm
  **p=0.0004**, BH q=0.0072, 24% between-region). **Cite the tempered version:
  LORO R² is negative for every index × analyte pair** → ranks within a
  district, does not predict across. Most robust: **vs pH, all four districts
  −0.24 to −0.40**. Note **+0.568 is Landsat; Sentinel-2 gives +0.549** —
  `STATE.md` quotes it without naming the sensor.
- **Resolution — flat.** 10/20/30/60/100 m: +0.494/+0.526/+0.493/+0.523/+0.517.
- **Coal/CMD** — both ladders, Ohio and PA, and their opposite shapes.
- **Catchment delineation — the cleanest result in the project:** 6/6 within
  ±33% of published USGS areas (`hybas_12` managed 2/6).

Two things to surface that `STATE.md` currently omits:
- **`NDVI_stress` vs C3b = J +0.700, AUC 0.962** — the largest separation
  anywhere in the water arm, and it must carry a warning: NLCD barren
  plausibly shares NDVI physics, the same reason CMD3 rejected NLCD as a
  covariate.
- **The B2c Landsat tier is not significant** (BH q = 0.2558 on all three);
  do not present "0.228 vs −0.019" as a result.

---

## Part 3 — `docs/GRANT_CASE.md`

The honest fundable argument, built in this order:

1. **What is proven** — a faithful replica of a published USGS method, with
   three of our own "improvements" measured as regressions and fixed (4.1×);
   one ground-truth-validated positive, bounded to within-district ranking;
   externally validated catchment delineation.
2. **What is null, and stated as null** — detection at n=86; the Ohio water
   column; resolution across 10–100 m.
3. **Why the nulls are the justification.** Every null names the measurement
   that would resolve it, and none can be resolved from free satellite data.
   This is the section that does the work.
4. **The methodological asset.** Four retractions caught in-house before
   publication, pre-registrations committed before their data with hashes a
   reviewer can verify, and a project rule that a null is reported as
   prominently as a positive. That is reviewable evidence of rigour, and it is
   rare.
5. **Instrumentation** — per your decision: **ASD-class field spectrometer +
   ≥10-band sensor + water/sediment chemistry**, which is the axis the Colorado
   data actually implicate. The **UAV goes in as a falsifiable canopy-access
   hypothesis** in forested terrain, with its prediction fixed in advance (the
   canopy diagnostic should drop below 0.6), **not** as a resolution argument.
   Stated plainly: two of three UAV arguments were withdrawn by our own
   pre-registered rules, and a resolution-based ask would collide with our own
   published refutation.
6. **Claim boundaries** — the MAY/MAY NOT list, verbatim, so the proposal
   cannot drift past them.

---

## Part 4 — `docs/FIELD_CAMPAIGN.md`

Rebuild `WATER_VALIDATION_REPORT_2026-07-25.md` §6, which is sound on chemistry
and spectroscopy but predates the entire B2/CMD programme. Keep: the ±1 hour
overpass rule, the four Fe concentration tiers, the analyte list (dissolved
**and** total Fe, Fe²⁺/Fe³⁺ speciation, SO₄²⁻, pH, Eh, acidity, conductivity,
**TSS/turbidity** and **DOC/CDOM** as the two main optical confounds,
chlorophyll-a), and the sky-glint-corrected water-leaving reflectance
requirement.

Fix the three gaps:

- **Re-target the sites.** §6 aims at Ohio reservoirs and Iraq — the two
  settings since shown least informative. The validated positive lives at
  **Colorado seep points**, and the honest open question is the **blind-search
  / discovery gap**. Sites follow the evidence.
- **Add a bed-sediment and shoreline-precipitate protocol.** The project's own
  conclusion is that the detectable target is *the precipitate, not the water
  column* — and §6 has no sediment design at all, only "bottom type" as an
  ancillary note. This is the largest gap relative to our own findings.
- **Derive a sample count, with the power calculation shown.** No document
  states any n. Anchor it on the measured effect sizes we now have
  (rho +0.568 within district; the 0.016 shortfall against J = 0.25) so the
  number is defensible rather than asserted.

**You supply nothing here** — but the site list stays reviewable, since access,
permits and lab capacity are yours to judge.

---

## Part 5 — Cold-start fixes (after Parts 1–3; noted now so it isn't lost)

**The Python arm is currently unrunnable by anyone but you on this machine.**

1. The GEE service-account key is hardcoded to a **sibling repo** in five
   files — `gee_classify.py:22`, `catchment_dem.py:44`,
   `catchment_delineation.py:36`, `match_scenes.py:39`, `watershed_nap.py:62`
   — with no env var, no flag, no fallback. A new user gets a bare
   `FileNotFoundError` naming a directory that does not exist for them.
2. `python/requirements.txt` **omits `rasterio`, `requests`, `shapely`** (all
   imported) and lists `geemap`, which is installed in neither venv — so
   `amd_detection.py` is dead here too.
3. **My own `OPERATOR_GUIDE.md` §8 is wrong**: it opens the worked example with
   `VPCA=D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe`. On any other
   machine every following line fails. It needs a `§0 Setup` — EE registration,
   venv, key, and the Rockwell raster's ScienceBase **DOI 10.5066/P9BYV5H4**
   with its required extract path
   `data/rockwell/L8_US_Southwest/SouthWest/l8_aa13_southwest_mosaic11.img`
   (hardcoded in four modules, documented in zero committed files).

---

## Logging rule (`CLAUDE.md`) — non-negotiable

Dated report in `validation/`; `STATE.md` updated; a `DECISION_LOG.md` row;
this plan mirrored to `docs/plans/`; commit **and push** after each Part so
nothing is lost if we stop partway.

> Push still needs your credentials — 7 commits and `v3.10.0` are unpushed:
> ```bash
> git push origin main --follow-tags
> ```

---

## Verification

1. **No refuted claim survives.** Grep the tree for `675`, `700 mg/L`, `Ganau`,
   `correctly classified`, `Successfully detected`, `80%`, `70-90%`,
   `Muskingum`, `AWEINSH > 0.20` — every surviving hit must sit inside a
   `validation/` historical report or under an explicit superseded banner.
2. **Every number in the accuracy assessment traces to a raw file.** Spot-check
   at least the four load-bearing ones (0.440, 0.234, +0.568, −0.354) against
   `validation/report_*.txt`, not against another summary.
3. **Author name is consistent** across every committed document.
4. **No document asserts validation in its filename or title** without the
   evidence to match — specifically `earth-engine/validation_results.md`.
5. **`git log --diff-filter=A` on the pre-registration files** still shows each
   landing before its data commit; the audit trail must be intact and
   verifiable after the cleanup.

---

## Outcome (filled in after execution, 2026-09-13)

**All five parts delivered.**

- **Part 1 — record remediation.** 21 files changed. Rewritten: `CITATION.cff`
  (also fixed a wrong repository URL and the SIM 3466 author list, corrected to
  Rockwell & Gnesda from the USGS data-release README), `README.md`,
  `PROJECT_OVERVIEW.md`, `python/README.md`. Bannered: nine historical
  documents plus three release-process records. Renamed
  `earth-engine/validation_results.md`. Also found beyond the plan:
  `CONTRIBUTING.md`'s *example commit message* modelled the retracted AWEINSH
  claim. **Sweep: 0 live hazards.**
- **Part 2 — `validation/ACCURACY_ASSESSMENT.md`.** Verification item 2 caught
  a real gap: `0.440` failed its trace (only an unrelated AUC matched in raw
  output). Regenerated with `paper_faithful_test.py`; reproduces exactly;
  committed.
- **Part 3 — `docs/GRANT_CASE.md`.** Verification item 5 run: all 7
  pre-registrations precede their results by ancestry (11 min – 5 h 06 m);
  CMD1 filename dates (08-16) differ from commit dates (08-24). Both disclosed,
  with what commit order does and does not prove.
- **Part 4 — `docs/FIELD_CAMPAIGN.md` + `python/field_power.py`.** Sample sizes
  simulation-checked. **Deviation from plan:** the planned UAV prediction (canopy
  diagnostic < 0.6) was found **non-discriminating** — leaf-off satellite already
  meets it — and was replaced with a paired UAV-vs-satellite test.
- **Part 5 — cold start.** `python/ee_auth.py` replaces five `init_ee` copies;
  `requirements.txt` +3 packages; `OPERATOR_GUIDE.md` §0. Verified: compile,
  imports, live EE call, CMD1 baseline −0.354/137/0.0028, DEM 6/6,
  `classify_v240` PASS.

**Outstanding, author-only:** publish the corrected Zenodo version; review
`.private/EB2_DOCUMENTATION.md`; check the author-name inconsistency did not
propagate; push.
