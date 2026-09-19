# Field-campaign pre-registration: Ohio first (Piedmont, then Clendening, then Atwood)

**Written 2026-09-19. Committed BEFORE any field measurement.** Commit ancestry
is the proof. The commit adding this file must be an ancestor of:
- the station-list amendment (§10);
- every commit containing field data.

If it is not, this registration is void.

**Committed in the same commit, and fixed by it:**

| artifact | what it fixes |
|---|---|
| `python/field_power.py` (+ `tests/test_field_power.py`) | the power numbers in §7; two Ohio anchors and a two-catchment column added, every earlier number unchanged |
| `validation/report_field_power_2026-09-19.txt` | the exact power tables quoted in §7 |
| `python/ohio_lake_archive.py` | the archival chemistry the author had seen (§9) |
| `validation/report_ohio_lakes_archive_2026-09-19.txt` | that chemistry, as printed |

This registration fixes the **design, the tests and the verdict rules**. The
**station coordinates** are fixed later, by a placement rule written here
(§3.3), in an amendment committed before field day 1 (§10).

---

## 1. Why this campaign, and why Ohio

`docs/FIELD_CAMPAIGN.md` put Colorado first and **dropped the Ohio reservoirs**,
because "the water column is a measured null at double the earlier sample".
This registration changes the order. **Ohio comes first** for four practical
reasons:
- the lakes are near the Kent State lab;
- the supervisor prefers them;
- drones are easy to take there;
- travel and cost are lower.

That choice has a scientific cost, stated here rather than discovered later:

- **The project's validated positive is not field-tested here.** That positive
  is severity ranking, `FerricIron1` vs dissolved Fe, ρ +0.568 across four
  Colorado districts. Ohio's drainage is circumneutral, and its dissolved iron
  is almost gone (§9).
- **Discovery (H-DISC) is not tested here.** The registered blind-search frame
  is Colorado-only.
- **The lake water column is not reopened.** Sulfate has no VNIR absorption.
  Lake-water iron and sulfate were a measured null (Water Phase 2, B1: sulfate
  n=23 and iron n=17, no feature's CI excluding zero). **No hypothesis here
  scores lake-water reflectance against iron or sulfate.** H-CONF scores it
  against water clarity only.

**What Ohio can test that nothing so far has:**
1. **The one standing Ohio claim, out of sample:** a vegetation index tracks
   sulfate negatively in coal watersheds (CMD2, as bounded by CMD3). The five
   Ohio watersheds behind that claim were:
   - Huff Run;
   - Leading Creek;
   - Monday Creek;
   - Sunday Creek;
   - Raccoon Creek.

   Neither Piedmont's catchment (Stillwater Creek) nor Clendening's (Brushy
   Fork) is among them.
2. **Whether the plausible target exists at all.** Circumneutral drainage
   drops its iron to the bed. Nobody has yet measured whether that precipitate
   is present, spectrally distinct, and visible from a drone at these inflows.
3. **The one fair Ohio lake comparison** (finding W3): Piedmont vs Atwood, AUC
   ≈ 0.78 in the coastal/blue fraction. It has never been checked against
   synchronously measured water clarity.

## 2. The questions

| id | question | kind |
|---|---|---|
| **H-RANK-OH** | At inflow stations, does `NDVI_stress` at 1000 m track synchronously measured sulfate, **negatively**? | verdict |
| **H-UAV-OH** | Leaf-off, at the channel margin: does a drone `FerricIron1` track measured precipitate cover where the leaf-off satellite does not? | verdict |
| **H-PRECIP** | Is precipitate spectrally distinct from uncoated substrate, and does that survive convolution to satellite bands? | verdict |
| **H-CONF** | Is the Piedmont–Atwood blue-fraction difference explained by water clarity? | verdict, Tier 3 only |
| **H-LIMIT** | At what total iron and sulfate does precipitate appear? | estimation |
| **MAG** | Do sediment magnetic properties co-vary with drainage chemistry? | estimation |

**Not tested here and carried forward** to a separate registration, if
Colorado work is funded:
- Colorado H-RANK (severity);
- Colorado H-DET (detection against chemistry-verified controls);
- H-DISC.

---

## 3. The sample: fixed

### 3.1 Tiers, fixed in order

| tier | adds | role |
|---|---|---|
| **1** | **Piedmont Lake** (Stillwater Creek) | the contaminated lake; runs alone if nothing else is funded |
| **2** | **Clendening Lake** (Brushy Fork) | the second mined catchment, and the only possible sign replicate |
| **3** | **Atwood Lake** (Indian Fork) | the sulfate control; required for H-CONF, and used by nothing else as a verdict |

- **A tier is added only by funding and access, never by results.**
- **Each tier's verdicts are reported when that tier's sampling is complete.** A
  later tier adds verdicts; it never withdraws an earlier one.
- **Atwood is not a replicate.** Its archival sulfate spans 10.6–23.1 mg/L
  (n=98), so a within-Atwood rank test of sulfate has almost no range to rank.

### 3.2 Station types

- **Inflow stations:** on the mapped stream network inside a lake's catchment,
  upstream of the full-pool backwater. These carry H-RANK-OH, H-UAV-OH,
  H-PRECIP, H-LIMIT and MAG.
- **In-lake stations:** **10 per lake**, at equal spacing along the lake's
  centreline from the main inflow arm to the dam, each at least **150 m from
  shore**. That keeps the 3×3 window of the coarsest band used (Sentinel-2 B1,
  60 m) entirely on water. These carry H-CONF and in-lake sediment for MAG.

### 3.3 Inflow placement rule, blind to chemistry and imagery

1. **Catchment:** the area draining to the lake's dam, delineated with
   `python/catchment_dem.py` (MERIT D8).
2. **Mouths first:** one station at every tributary mouth that carries a mapped
   flowline, placed just upstream of the full-pool backwater.
3. **Then a grid:** further stations upstream along each tributary at **1.5 km
   channel-distance intervals**, measured from the mouth.
   - Tributaries are visited largest drainage area first, round-robin, one
     station per tributary per round.
   - Placement stops when the catchment reaches its target (§3.4).
4. **Access moves:** a point that cannot be reached safely or with permission
   moves to the nearest accessible point within **300 m** along the channel.
   - If there is none, it is dropped and the next grid point is used.
   - Every move and drop is logged in the §10 amendment.
5. **Archival stations** are reused only if they fall within 300 m of a grid
   point.
6. **No index value, image or archival chemistry value is consulted** to place,
   move or drop a station. This rule exists because archival chemistry for both
   catchments had already been seen (§9). Choosing stations by it would inflate
   any correlation.

### 3.4 How many

| per catchment | target | minimum | why (§7) |
|---|---|---|---|
| inflow stations | **51** | **42** | 51 gives power 0.83 for \|ρ\| 0.40; 42 gives 0.83 for the Ohio archival \|ρ\| 0.438 |
| of which flown by drone (H-UAV-OH) | all | **30** | below 30, H-UAV-OH is NOT RUN |
| in-lake | 10 | 10 | H-CONF needs ≥ 20 usable station-visits per lake (§6.4) |

Field duplicates and blanks come on top, at 10% of samples.

### 3.5 When

- **Primary event:** one visit per station in the **autumn window, 1 Nov – 15
  Dec**. This is leaf-off, near baseflow, and before ice.
  - Only at baseflow: no sampling within 72 h after ≥ 12.7 mm (0.5 in) of rain
    at the nearest NOAA gauge.
- **Optional second event (high flow):** the spring window, **15 Mar – 30
  Apr**. It is analysed **separately** and never pooled with the primary event
  for a verdict.
- **Synchrony:** chemistry and in-lake sampling on a Sentinel-2 or Landsat 8/9
  overpass day, clear sky. The actual offset is recorded at every station. The
  primary analyses use same-day matches, and a ±1 h subset is a sensitivity
  analysis (§8).
- **If sampling starts after 15 Dec 2027,** the author re-affirms this
  registration by amendment before field day 1.

---

## 4. What is measured

This follows `docs/FIELD_CAMPAIGN.md` §4, which is not repeated here.

**Every station:**
- dissolved (0.45 µm, field-filtered) **and** total Fe, never pooled;
- Fe²⁺ in the field;
- SO₄²⁻, pH, ORP, specific conductance, temperature, alkalinity;
- dissolved **Mn** (archival stream values reach 1,220–1,400 µg/L; a
  circumneutral-drainage marker), Al;
- TSS and turbidity, DOC/CDOM, chlorophyll-a.

**Inflow stations add:**
- a **precipitate quadrat** at the channel margin nearest the station point,
  with a nadir photograph and colour card, and areal cover (%) scored by the
  protocol fixed in §10, blind to chemistry and imagery;
- **paired contact-probe spectra** of coated and uncoated substrate wherever
  precipitate is present;
- bed sediment (composite of three grabs, top ~2 cm).

**In-lake stations add:**
- above-water radiometry;
- surface sediment by grab;
- Secchi depth.

---

## 5. Scores: fixed

| score | definition | code |
|---|---|---|
| **`NDVI_stress`** | (NIR − red)/(NIR + red), Landsat 8 SR; **p90** within a **1000 m** buffer of the station; **the composite CMD2 used, unchanged**: May–Jul median over 2013–2020. The index side of the test is therefore fixed today, and only the chemistry is new | `amdtool.imagery.l8_composite`, extracted as in `python/cmd_detect.py` |
| **satellite `FerricIron1`** | red/blue (B4/B2), Landsat 8/9 SR; **p90** within **30 m**; leaf-off composite restricted to **the event's own sampling window**, because precipitate is present or absent *then*. If fewer than 3 scenes, widen to the full Nov–Mar season containing the event | `amdtool.imagery.l8_composite_season(season="leafoff")`. It currently fixes 2013–2020, so a date-range argument, with a test, is added before the §10 amendment; the default stays byte-identical |
| **drone `FerricIron1`** | red/blue from panel-calibrated drone reflectance; **median** over a 30 m reach centred on the station, restricted to a **2 m waterline strip on each bank**, digitised on the RGB orthomosaic **before** any index is computed | fixed in §10 (camera, GSD ≤ 5 cm) |
| **precipitate contrast, full resolution** | (a) continuum-removed band depth of the ferric absorption, minimum over 850–1,000 nm, continuum 750–1,250 nm; (b) R(650 ± 10 nm) / R(480 ± 10 nm) | contact-probe spectra |
| **precipitate contrast, convolved** | `FerricIron1` after convolving each spectrum to the **Sentinel-2 MSI** spectral response functions (B4/B2); Landsat 8 OLI reported alongside | — |
| **`f_B1`** | coastal-band fraction, B1 / (B1+…+B5), 3×3 all-water window, same-day scene | `python/match_scenes.py --days 0`, `python/detection_limit.py` `features()` |

The predicted sign is **negative** for `NDVI_stress` vs sulfate (CMD2). It is
**positive** for both `FerricIron1` scores vs precipitate cover, and for
coated minus uncoated contrast.

---

## 6. Tests and verdicts: fixed

**Every verdict table is read top to bottom, and the first row that holds is
the verdict.** That makes the rows mutually exclusive and exhaustive by
construction (correction #8, `DECISION_LOG.md`).

**Shared conventions:**
- **Randomness:** permutations use 5,000 draws; bootstraps use 2,000 draws;
  seed **20260919** for all.
- **Statistics:** Spearman ρ and within-catchment permutation come from
  `amdtool.stats`.
- **Missing values:** a station missing a score or the outcome is excluded
  from that test and counted in the report.

### 6.1 H-RANK-OH: `NDVI_stress` vs sulfate at inflow stations

**Tier 1 (Piedmont alone):**

| rule | verdict |
|---|---|
| fewer than 42 inflow stations with both values | **ESTIMATE ONLY:** ρ and 95% bootstrap CI, no verdict |
| ρ ≤ −0.30 and permutation p < 0.05 (two-sided) | **SUPPORTED IN PIEDMONT** |
| ρ < 0 | **WEAK** |
| otherwise | **NOT SUPPORTED** |

**Tier 2 (Piedmont + Clendening), evaluated additionally:**

| rule | verdict |
|---|---|
| either catchment below 42 | **ESTIMATE ONLY** |
| both catchments ρ < 0, **and** pooled within-catchment ρ ≤ −0.30 with within-catchment permutation p < 0.05 | **SUPPORTED, SIGN-CONSISTENT** |
| both catchments ρ < 0 | **WEAK** |
| otherwise (signs disagree, or neither negative) | **NOT SUPPORTED** |

**Reported with every H-RANK-OH verdict:**
- the between/within-catchment variance split beside the pooled ρ;
- a caveat that CMD2 found **~42% of the archival covariance runs through
  catchment mining extent**. A SUPPORTED verdict therefore means "the
  association replicates", **not** "the vegetation signal is drainage rather
  than mining land cover". The mining-extent partial is secondary (§8).

### 6.2 H-UAV-OH: drone vs leaf-off satellite, against precipitate cover

**Why the outcome is precipitate cover, not chemistry.** `FIELD_CAMPAIGN.md`
§5.2 scored both instruments against chemistry. It is changed here, before any
field data, because in both catchments dissolved iron has already left the
water:
- archival stream dissolved Fe medians are 11 and 17 µg/L (§9);
- so station chemistry does not measure what a waterline image can see;
- precipitate cover does.

Chemistry outcomes are secondary (§8).

**The bar** for either instrument:
- Spearman ρ ≥ +0.30 against cover, with permutation p < 0.05;
- at Tier 2, positive in both catchments as well.

| rule | verdict |
|---|---|
| the drone camera lacks calibrated red and blue bands, or fewer than 30 stations flown in any catchment in the tier | **NOT RUN** (reason reported) |
| cover is zero at more than 80% of flown stations | **NO TARGET:** precipitate too rare to rank; prevalence with a Wilson CI |
| drone meets the bar **and** satellite does not | **SUPPORTED:** the drone adds information |
| **both** meet the bar | **NO ADDED VALUE:** satellite suffices |
| otherwise | **NOT SUPPORTED** |

This test is justified by a hypothesis measured against a satellite baseline,
**not** by either drone argument this project has withdrawn: resolution
(2026-08-15), and the near-channel reading (CMD2). It can fail.

### 6.3 H-PRECIP: is the precipitate spectrally distinct?

**Unit:** an inflow station with visible precipitate, carrying paired
coated/uncoated spectra from the same session.

**Tests:**
- **Full resolution:** one-sided Wilcoxon signed-rank on the paired differences
  for features (a) and (b). Holm over the two at α 0.05. The spectrum
  "separates" if either is rejected.
- **Convolved:** one-sided Wilcoxon on Sentinel-2 `FerricIron1`, at p < 0.05.

| rule | verdict |
|---|---|
| fewer than 15 paired stations across all sampled catchments | **INSUFFICIENT PRECIPITATE:** count and prevalence with a Wilson CI |
| the convolved contrast separates | **SATELLITE-BAND-DETECTABLE:** the contrast survives 7-band convolution; says nothing yet about pixel fraction |
| the full-resolution contrast separates | **SPECTRALLY LIMITED:** only finer spectral resolution sees it |
| otherwise | **NOT SEPARABLE** |

**No power claim is made.** No prior coated-vs-uncoated effect size exists at
these sites; this is a first measurement, and 15 pairs is a floor, not a
powered n.

### 6.4 H-CONF: Piedmont vs Atwood blue fraction (Tier 3 only)

**Unit:** an in-lake station-visit on a date when both lakes were sampled on the
same overpass. A visit is usable if its same-day window is all water.

**Statistics:**
- **Unadjusted:** AUC of `f_B1`, Piedmont vs Atwood (`amdtool.stats.auc`).
- **Adjusted:** the AUC of `f_B1` residuals after a rank regression on
  turbidity, chlorophyll-a and sampling date (fixed effect), pooled over both
  lakes.
- **Intervals:** 95% CIs by bootstrap resampling of stations within lake.

| rule | verdict |
|---|---|
| fewer than 20 usable station-visits in either lake | **NOT RUN** |
| unadjusted CI includes 0.5 | **NO DIFFERENCE IN SYNCHRONOUS DATA** |
| adjusted CI includes 0.5 | **EXPLAINED BY WATER CLARITY** |
| otherwise | **RESIDUAL DIFFERENCE** |

**Stated now:** a RESIDUAL DIFFERENCE is **not attributable to mine drainage**.
With two lakes, lake identity confounds everything else that differs between
them, including:
- depth;
- bottom type;
- algal community;
- DOC/CDOM.

DOC/CDOM is reported as the first candidate.

### 6.5 H-LIMIT (estimation, no verdict)

- **Model:** logistic regression of precipitate presence (cover > 0) on log₁₀
  total Fe, and separately on log₁₀ sulfate.
- **Reported:** the concentration at 50% probability with a 95% bootstrap CI.
- **Fallback:** if presence is all-or-none, or the fit does not converge, the
  counts are reported instead.

### 6.6 MAG (estimation, no verdict)

At inflow stations, Spearman ρ with 95% bootstrap CIs between each bed-sediment
magnetic property and each outcome:
- **properties:** χ_lf (mass-specific), SIRM and S-ratio (S₋₃₀₀);
- **outcomes:** sulfate and precipitate cover.

Benjamini–Hochberg is applied within this arm.

**Descriptive only:**
- FORC and XRD on a subset;
- in-lake surface sediment across the sampled lakes.

**δ³⁴S / δ¹⁸O of sulfate** is contingent on a laboratory quote. Any hypothesis
about it is fixed by an amendment committed **before any isotope result is
received**.

**Multiplicity:** the four verdict hypotheses ask different questions and each
has its own verdict, so there is no family correction across them. Corrections
within a hypothesis are as stated. Secondary analyses are BH-corrected and
**never** verdicts.

---

## 7. Power: computed before any data

From `validation/report_field_power_2026-09-19.txt` (seed 20260913, 4,000 reps):

| true \|ρ\| | stations for power 0.80 (closed form) | simulated power at that n | anchor |
|---|---|---|---|
| 0.30 | 89 | 0.820 | the project's bar |
| **0.40** | **51** | 0.828 | **the inflow target** |
| **0.438** | **42** | 0.830 | **Ohio `NDVI_stress` vs sulfate, 1000 m (CMD2): the minimum** |
| 0.50 | 33 | 0.832 | |
| 0.246 | 132 | 0.810 | Ohio partial ρ after mining extent (CMD2) |

**Sign consistency at Tier 2:** at true |ρ| 0.30 and 50 stations per
catchment, P(both catchments estimate the predicted sign) = **0.964**. At 30
stations it is 0.909.

**Stated in advance:**
- **The design is powered for the raw Ohio association, not for the
  confound-adjusted one.** That would need 132 stations per catchment, so the
  adjusted value is an estimate only.
- **A NOT SUPPORTED verdict at 42–51 stations does not exclude |ρ| near 0.25.**

---

## 8. Secondary and sensitivity analyses: reported, never verdicts

- **Conductance** as the H-RANK-OH outcome. CMD3 found it the better-powered
  arm.
- **The radius ladder** for `NDVI_stress`: 30, 60, 100 and 500 m.
- **Leaf-off** `NDVI_stress`, and a leaf-on composite of the **same year** as
  the event.
- **Sentinel-2 (10 m) `FerricIron1`** for the satellite arm of H-UAV-OH.
- **Partial ρ given catchment mining extent** (ODNR `MinesOfOhio`), via
  `python/cmd_confound.py`. This is the CMD2 confound.
- **Chemistry outcomes for H-UAV-OH:** sulfate, total Fe and dissolved Mn.
- **The ±1 h synchrony subset.**
- **The spring (high-flow) event**, separately.
- **H-CONF with DOC/CDOM** added to the adjustment.
- **Per-station precipitate mineralogy** (XRD subset) against spectral
  contrast.

---

## 9. Disclosures, written before the data

**Seen before this registration was written:**
- the Water Validation Report and finding W4 (2026-07-25): Piedmont sulfate
  462 mg/L, Atwood 18.3 mg/L;
- finding W3: AUC ≈ 0.78;
- Water Phase 2 B1: the lake water-column null;
- CMD1–CMD3.

**Also seen, on 2026-09-19, before writing:** archival chemistry for both
catchments, fetched with `python/fetch_wqp.py --bbox` and printed in
`report_ohio_lakes_archive_2026-09-19.txt`.

| catchment | stream stations | stream sulfate | stream dissolved Fe, median (n) | pH |
|---|---|---|---|---|
| Piedmont | 8 | 15.1–967 mg/L | 11.25 µg/L (n=16) | 7.6–8.99 |
| Clendening | 16 | 12.1–1,370 mg/L | 17.15 µg/L (n=24) | 7.07–8.99 |

That fetch shaped three choices:
- the inflow focus;
- precipitate cover as H-UAV-OH's outcome;
- the placement rule in §3.3, which forbids using those values.

**The regenerated W4 values differ trivially** from the July figures: 461 vs
462 mg/L, and Atwood 19 vs 18.3 mg/L with n 98 vs 101. The script keeps water
samples only.

**Limits of the data and design:**
- **Atwood is a sulfate control, not an iron control** (W4): its total
  recoverable Fe median, 298 µg/L, exceeds Piedmont's total Fe median, 201.
- **Atwood's archival pH includes a value of 0**, a recording error. It is
  printed as-is and not used.
- **The Ohio claim is PARTIAL on its own confound test** (CMD2: partial ρ
  −0.246 against a bar of 0.25). H-RANK-OH tests the raw association and
  inherits that caveat.
- **The drone and camera are not yet specified.** If the camera lacks
  calibrated red and blue bands, H-UAV-OH is NOT RUN.
- **Not fixed here, because they are the author's:** permissions (MWCD),
  drone flight authorisation, and the laboratory. **None of them may be chosen
  with reference to any measured value.**

---

## 10. Station-list amendment: required before field day 1

It must be committed before the first field measurement, and it must contain:
1. the catchment delineations and the placement log (§3.3), including every
   move and drop;
2. `validation/field_stations_<date>.csv` and its **SHA-256**;
3. the drone and camera model, band centres, GSD, and flight plan;
4. the precipitate-cover scoring protocol: photograph with colour card, and
   either a fixed hue rule or two observers blind to chemistry and imagery;
5. the laboratory, methods and detection limits;
6. the sampling-window dates for the first event;
7. the `l8_composite_season` date-range argument (§5), committed with a test
   showing the default output is unchanged.

---

## 11. What each outcome would mean

| outcome | meaning |
|---|---|
| H-RANK-OH SUPPORTED (Tier 2) | the Ohio vegetation–sulfate association replicates in two catchments never used to find it; still land cover *or* drainage (§6.1) |
| H-RANK-OH NOT SUPPORTED | the standing Ohio claim does not transfer to these catchments at 42–51 stations; reported as prominently as a success |
| H-UAV-OH SUPPORTED | a drone sees waterline precipitate that 30 m leaf-off satellite cannot, which is the first measured case for airborne monitoring of circumneutral drainage |
| H-UAV-OH NO ADDED VALUE / NOT SUPPORTED / NO TARGET | bounds airborne monitoring here; NO TARGET means there is little to see |
| H-PRECIP SATELLITE-BAND-DETECTABLE | the target is optically distinct at satellite bands; whether it fills enough of a pixel is the next question |
| H-PRECIP SPECTRALLY LIMITED | a hyperspectral or field-spectral method is needed; 7-band imagery is the constraint |
| H-CONF EXPLAINED BY WATER CLARITY | W3's lake difference was clarity; the lake pathway is closed by measurement, not inference |
| H-CONF RESIDUAL DIFFERENCE | the lakes differ spectrally beyond clarity; the cause stays unattributed |

**No outcome here fails to produce a publishable result.**

## 12. Reproduce

```
python python/field_power.py > validation/report_field_power_2026-09-19.txt
python python/fetch_wqp.py --region "Piedmont Lake catchment, OH" --bbox "40.06,-81.32,40.225,-81.10"
python python/fetch_wqp.py --region "Clendening Lake, OH" --bbox "40.225,-81.30,40.32,-81.10"
python python/ohio_lake_archive.py --out validation/report_ohio_lakes_archive_2026-09-19.txt
```

Use the Earth Engine venv for anything that touches `ee` (CLAUDE.md). The two
fetches need only network access. The WQP archive can grow, so a later fetch
may print more rows than this report.
