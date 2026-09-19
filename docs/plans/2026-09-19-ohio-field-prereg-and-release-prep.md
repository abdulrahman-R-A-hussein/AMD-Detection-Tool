> Mirror of the approved plan (machine-local file: `~/.claude/plans/so-what-is-next-functional-bear.md`), 2026-09-19. The repo copy is authoritative.
>
> **Details fixed at execution, not in the plan:** `NDVI_stress` uses the committed 2013–2020 May–Jul composite CMD2 used, so the index side of H-RANK-OH is fixed today. The drone test's satellite arm uses the event's own leaf-off window; a date-range argument is added before the station-list amendment. The drone test is scored against precipitate cover, because the Clendening and Piedmont-catchment fetch showed dissolved iron has left the water.

# Next round: Ohio-first field pre-registration, Zenodo prep, SpectraLab merge memo, snow-masked run

## Context

The author said "next" to the five-item list. On 2026-09-17 they chose four
pieces of work:
- the field pre-registration, covering all six hypotheses;
- Zenodo release prep;
- a SpectraLab merge memo;
- starting the snow-masked run.

The UI test, publishing, and the merge decision stay the author's.

**The field campaign changes: Ohio first, not Colorado.** The author will
sample **Piedmont Lake** first, then **Clendening Lake** if possible, and
**Atwood Lake** as background if funded. The reasons:
- they are near the Kent lab, which the supervisor prefers;
- the drones are easy to take there;
- less travel means lower cost.

`docs/FIELD_CAMPAIGN.md` was built the other way round: Colorado first, then
the Pennsylvania/Ohio coal basins, and it **explicitly dropped the Ohio
reservoirs** ("the water column is a measured null at double the earlier
sample"). The registration has to face that record head-on, not quietly reverse
it.

**What the record says about these lakes (read-only checks):**

| fact | value | source |
|---|---|---|
| Piedmont sulfate / iron | 462 mg/L (n=26, 374–560) / median 162 µg/L | `validation/README.md` W4 |
| Atwood sulfate / iron | 18.3 mg/L (n=101) / median 302 µg/L, **higher than Piedmont** | same: a sulfate control, **not** an iron control |
| Ohio water column vs index | sulfate n=23, iron n=17: no feature's CI excludes zero; turbidity n=50: 6 features do | `WATER_PHASE2_2026-08-10.md` B1 |
| Piedmont vs Atwood | blue-fraction AUC ≈ 0.78, the one fair Ohio comparison; the record names **dissolved iron (and clarity) measured at both lakes** as what would settle it | README W3 |
| Ohio canopy | 30 m stream buffers are median NDVI 0.870, so UNINTERPRETABLE; the drone case is imaging along channels, leaf-off | STATE, CMD1 |
| Ohio CMD pH | median 7.46–7.72, five watersheds | STATE |
| Clendening | **no chemistry on record locally**; needs a Water Quality Portal fetch | `data/chemistry/` |

**Intended outcome:** a registration the author could run on Piedmont alone. It
must not reopen the closed water-column question, and it must state before any
field day what each lake can and cannot show.

---

## Defaults I chose (change any at approval)

1. **Sample the lakes and their inflow streams,** not the open water only. Open-water
   optical detection is closed. Precipitate, drone access and the one Ohio
   positive (vegetation index vs sulfate) all live at the inflows.
2. **Colorado, Pennsylvania and H-DISC are carried to a later, separate
   registration.** The blind-search frame is Colorado-only, and severity ranking
   (the validated positive) cannot be field-tested in Ohio. This is said plainly
   in the registration and the DECISION_LOG.
3. **Sediment magnetism** (from your GSA talk) is registered as an **estimation
   arm**, with no verdict. δ³⁴S is listed as contingent on a lab quote.

---

## 1. Field pre-registration (main deliverable)

**Before writing it (execution step 1; no field data involved):**
- **Clendening chemistry:** `python python/fetch_wqp.py --bbox <Clendening bbox>`
  with the Earth Engine venv. The registration discloses this fetch.
- **Power numbers:** regenerate with `python python/field_power.py`, adding the
  two-lake sign-consistency case if it isn't there (small addition, with a
  test).

**`validation/FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md`**

It follows the structure of `BLIND_SEARCH_PREREGISTRATION_2026-09-14.md`:
- why the test exists;
- the question;
- the sample, fixed;
- the tests, with mutually exclusive and exhaustive verdict rows;
- power;
- sensitivity analyses;
- disclosures;
- what each outcome would mean;
- how to reproduce.

**Tiers, fixed in order regardless of results:**

| tier | lakes | why it's in |
|---|---|---|
| **1** | **Piedmont** | the contaminated lake (462 mg/L sulfate); runs alone if nothing else is funded |
| **2** | + Clendening | a second mined catchment, the only possible sign replicate |
| **3** | + Atwood | the sulfate control; needed for H-CONF only |

**Why Atwood can't be a third replicate:** its sulfate range is 10.6–23.1 mg/L,
so a within-Atwood rho is expected near zero. That is said in advance.

**Hypotheses mapped to Ohio** (six-hypothesis coverage as chosen):

| hypothesis | Ohio form | tiers |
|---|---|---|
| **H-CONF** (new, replaces the lake part of H-DET) | Does the Piedmont–Atwood blue-fraction difference survive adjustment for synchronously measured turbidity/TSS and chlorophyll? | 3 |
| **H-RANK** | At inflow stations, does the vegetation index track measured sulfate and conductance, **negatively**, the standing CMD2/3 claim? | 1 = within Piedmont only; 2 = sign consistency across both lakes |
| **H-PRECIP** | Do coated and uncoated inflow substrates separate at full spectral resolution, and still after convolution to Landsat/S2 bands? | all |
| **H-LIMIT** | Estimation: the dissolved Fe at which precipitate appears, with a CI | all |
| **H-UAV** | Leaf-off drone vs leaf-off Landsat/Sentinel-2, on the same inflow stations, per `FIELD_CAMPAIGN.md` §5 | all |
| **Magnetism** | Estimation only: χ_lf / IRM / FORC of inflow and lake sediment vs sulfate and conductance | all |
| **H-DISC, Colorado H-RANK/H-DET** | **Not tested here**; carried forward | — |

H-CONF has three verdict rows:
- **EXPLAINED BY WATER CLARITY**
- **RESIDUAL DIFFERENCE**
- **NO DIFFERENCE IN SYNCHRONOUS DATA**

Its limit, stated in advance: with two lakes, a residual difference is **not**
attributable to mine drainage, because lake identity confounds it.

**Stations:**
- **Per lake:** about 33 (lake transect + inflow mouths + upstream inflow
  reaches). That gives power 0.83 for within-lake rho 0.5, from
  `FIELD_CAMPAIGN.md` §3.1, re-checked.
- **Selection rule fixed now** (maps and access only, before any measurement).
  The station list itself is committed later, with a SHA-256, **before field
  day 1**, as the blind-search site list was.

**Measurements:** reuse `FIELD_CAMPAIGN.md` §4:
- dissolved **and** total Fe, with Fe²⁺ measured in the field;
- sulfate, conductance, pH, TSS/turbidity, chlorophyll;
- field spectra;
- sediment.

**Season:** drone and inflow work leaf-off. In-lake H-CONF sampling is
synchronous with a clear overpass. Windows are fixed in the registration to
avoid ice: about Nov 1 – Dec 15 and Mar 15 – Apr 15.

**Analysis code** is named per test (reuse only):
- `amdtool.stats` for permutation, BH/Holm and Wilson;
- `cmd_detect.py` for dose-response, the canopy gate and sign consistency;
- `catchment_dem.py` for inflow catchments.

**Also updated:**
- **`docs/FIELD_CAMPAIGN.md`:** a new "§0: September 2026, Ohio-first" note that
  explains the reversal of "Dropped: Ohio reservoirs" and what it costs
  scientifically. The Colorado/PA design stays as the later arm.
- **`validation/STATE.md`:** NEXT item 5 now points to the registration; any
  Ohio-lake claim stays bounded.
- **`validation/DECISION_LOG.md`:** a 2026-09-19 row covering what was asked,
  why Ohio (cost, proximity, drones, supervisor), what that costs (severity
  ranking isn't field-tested), and what was decided.
- **Plan mirror:** `docs/plans/2026-09-19-ohio-field-prereg-and-release-prep.md`.

## 2. Snow-masked blind-search sensitivity (starts first, runs in parallel)

- **Command:** `D:/dev/VPCA+STEPWISE-REGRESSION/.venv/Scripts/python.exe python/blind_search.py --extract --snow-masked`,
  started in the background at the beginning of execution. It covers seven
  districts, takes about a day, and skips finished districts, so it resumes.
- **Resume command** recorded in STATE before it starts. If the session ends,
  you re-run the same command in your own terminal.
- **Rule already committed:** a 5xx/DNS stop means re-extract, not FAILED.
- **When all seven are done,** run `--analyse`. Its snow-masked block is a
  **sensitivity, never a verdict**. It goes in an addendum to
  `ARM_BLIND_SEARCH_2026-09-15.md`, with n and caveat, plus STATE and
  DECISION_LOG, then commit and push.

## 3. Zenodo release prep (you publish)

- **`CITATION.cff`:** `version: 3.11.0`, `date-released:` the commit date (you
  adjust it if you publish later), and one abstract sentence on the blind-search
  null.
- **Zenodo metadata:** if a `.zenodo.json` exists, bump it the same way.
- **Release notes:** draft `docs/releases/v3.11.0.md` from
  `ROUND_SUMMARY_2026-09-16.md` plus the new registration. If the repo already
  has a changelog convention, use that instead.
- **Order:** after the registration commit, so the release contains it.
- **No tag, no push of a tag, no GitHub release.** Those steps, from
  HOW_TO_TEST §E steps 2–5, stay yours, because a pushed tag can trigger the
  archive.

## 4. SpectraLab merge memo (branch `feature/amd-severity-module`)

- **Where:** `docs/RELEASE_DECISION_0.40.0.md` in SpectraLab, committed with
  the repo's own author identity and `-c safe.directory`. Never stage the HMAC
  key, service-account keys, or the pre-existing untracked items.
- **Content** (read-only checks first):
  - what a 0.40.0 release needs: version bump, RELEASES.md, wheel, exe via
    `scripts/build_exe.py`, and the test suite;
  - **how `amdtool` gets into a released build.** It is an editable local
    install now and is not on PyPI, so the wheel or exe must vendor it, or pin
    a git URL. This is likely the main blocker; check SpectraLab's
    `pyproject.toml`;
  - what merge vs stay-on-branch costs;
  - your UI test stays the gate.
- **No version bump, build, merge or release.**

---

## Verification

1. **Tests:**
   - `python -m pytest tests/` → 207 pass, plus any new `field_power` test;
   - the SpectraLab AMD tests → 25 pass, 1 skipped.
2. **Registration:**
   - every number cited is regenerated from committed code;
   - verdict rows are checked for mutual exclusivity;
   - its SHA-256 is recorded in STATE;
   - the commit lands before any field data exist.
3. **Snow-masked run:** a background process is running, the resume command is
   in STATE, and progress is logged per district.
4. **Diffs:** `git diff --cached --name-only` is checked before every commit in
   both repos. The pushes succeed, and only the pre-existing untracked items
   remain.
5. **Reply:** a plain-language summary listing what is still yours to do: tag,
   release and Zenodo; the UI test; the merge decision; station coordinates,
   permits and lab choice.
