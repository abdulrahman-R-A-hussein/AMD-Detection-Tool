# Field campaign design — synchronous spectroscopy, water and sediment chemistry, and a drone test

**Prepared 2026-09-13** for the PhD proposal. Author: **Abdulrahman Hussein**,
Kent State University, Dr. Joseph D. Ortiz laboratory.

**Every sample size here comes from
[`python/field_power.py`](../python/field_power.py)**, output committed as
[`validation/report_field_power_2026-09-13.txt`](../validation/report_field_power_2026-09-13.txt),
so no number has to be taken on trust. Closed-form Fisher-z values were checked
by Monte Carlo; at every closed-form n the simulated power was 0.82–0.87.

**Companions:** [`GRANT_CASE.md`](GRANT_CASE.md) (why this campaign) ·
[`validation/ACCURACY_ASSESSMENT.md`](../validation/ACCURACY_ASSESSMENT.md)
(what it builds on).

---

## 0. What changed from the July 2026 design

`validation/WATER_VALIDATION_REPORT_2026-07-25.md` §6 was sound on chemistry and
spectroscopy, and that content is kept. But it predated the entire B2 / CMD
programme, and three gaps followed from that:

| gap in the July design | fixed here |
|---|---|
| targeted **Ohio reservoirs and Iraq** — since shown to be the least informative settings (the Ohio water column is a measured null; the Ganau result was circular and dissolved iron was never measured there) | re-targeted to **where the one validated positive lives** (Colorado mine discharge) and to **where a drone could add something** (Appalachian coal drainage) |
| **no sediment or precipitate protocol**, though the project's own conclusion is that the detectable target is the precipitate, not the water column | §4.2 |
| **no sample count anywhere** | §3, derived from measured effect sizes |

**Do not reuse §6.4 of the July report.** Its suggested thesis framing cites
"validated at Silverton, AUC 0.961", which was withdrawn the following day — it
was Silverton-only and collapsed to 0.63–0.67 across sites.

---

## 1. Hypotheses — to be pre-registered before the first field day

Each verdict table below has **mutually exclusive, exhaustive rows**. That rule
exists because a registration in this project once had overlapping rows, which
left room for choosing the kinder reading after the fact (correction #8,
`validation/DECISION_LOG.md`).

### H-RANK — does severity ranking hold with synchronous data?

Archival chemistry gave `FerricIron1` vs dissolved Fe rho +0.568: +0.64, +0.68
and +0.64 in three districts but +0.004 in Leadville (n=23), and LORO R² negative for every pair. Synchronous sampling
removes the date mismatch that sits inside every archival number.

| outcome | verdict |
|---|---|
| within-district rho has the same sign in **every** district **and** pooled within-region rho ≥ 0.3 | **SUPPORTED** |
| same sign in every district, pooled rho < 0.3 | **WEAK** |
| signs disagree between districts | **NOT SUPPORTED** |

### H-DET — does detection reach the bar with chemistry-verified controls?

Archival best case: worst-case LORO J **0.234** vs a bar of **0.25**.

| worst-case leave-one-district-out Youden J | verdict |
|---|---|
| ≥ 0.25 | **PASS** |
| 0.15 – < 0.25 | **PARTIAL** |
| < 0.15 | **FAIL** |

### H-LIMIT — at what concentration does the index respond?

An **estimation target, not a pass/fail**: the dissolved-Fe concentration at
which index response departs from the control tier, with its confidence
interval, per sensor. Reported whatever it turns out to be.

### H-PRECIP — is the precipitate the detectable target?

| field spectra of precipitate-coated vs uncoated substrate | verdict |
|---|---|
| separate at full spectral resolution **and** after convolution to Landsat/Sentinel-2 bands | **SATELLITE-DETECTABLE** |
| separate at full resolution, **not** after convolution | **SPECTRALLY LIMITED** — the 7-band bound is the constraint |
| do not separate at full resolution | **NOT THE TARGET** |

### H-DISC — can the tool find sites it was not told about?

**Estimation, with confidence intervals:** precision at flagged sites that have
no record, and recall at known sources. This is the discovery test the project
has never run.

### H-UAV — does a drone add anything over leaf-off satellite?

Stated in full in §5.

---

## 2. Where — the sites follow the evidence

### Campaign A — Colorado mineral districts (the validated positive)

**Silverton, Ouray, Leadville, Central City.** The 86 confirmed source points
and the only ground-truth-validated positive are here. Roughly 2,050–2,280 km
from Kent.

Archival records already reach every iron tier — **but unevenly**, because
agencies chose where to sample. Source points per dissolved-Fe tier (mg/L):

| district | control < 0.1 | low 0.1–1 | moderate 1–10 | high ≥ 10 | no dissolved value |
|---|---|---|---|---|---|
| Silverton | 5 | 3 | 6 | **1** | 6 |
| Ouray | 7 | 9 | 1 | **0** | 5 |
| Leadville | 9 | 5 | 4 | 5 | 0 |
| Central City | 4 | 0 | 2 | **14** | 0 |
| **total** | 25 | 17 | 13 | 20 | 11 |

**Ouray has no high-iron source point on record, and Silverton has one.** In
Ouray the high tier may have to be filled from in-stream stations (two on
record) or left short and reported as such. A controlled gradient is itself
something only fieldwork can provide.

**Season.** SIM 3466 specifies May–July imagery for mineral mapping. At these
elevations snow limits access into early summer, so the usable window where
imagery season and access overlap may be short — **confirm locally before
committing dates.**

### Campaign B — Appalachian coal drainage (the drone test)

Coal basins are where satellite measurements fall **below** the project's bar
(Ohio −0.354 with inconsistent signs; Pennsylvania −0.143 / −0.187), so they are
where a drone could show added value. They are also close to Kent.

| basin | distance from Kent | sulfate-matched stations on record |
|---|---|---|
| **Huff Run, OH** | **65 km** | 47 |
| **Clearfield Creek, PA** | 245 km | 113 |
| **Moshannon Creek, PA** | 270 km | 138 |
| Raccoon Creek, OH | 253 km | 50 |
| Chest Creek, PA | 223 km | 23 |
| Monday / Sunday Creek, OH | ~190 km | 12 / 13 — **too thin** |

**Recommended: Huff Run, Clearfield Creek, Moshannon Creek** — three
spatially disjoint basins with enough existing stations to support a
three-basin sign-consistency test, one of them an hour from campus.
Raccoon Creek is the substitute.

**Season: leaf-off (November–March), non-negotiable.** Leaf-on Ohio was
canopy-limited (median buffer NDVI 0.870) and therefore uninterpretable.

### Dropped, with reasons

- **Ohio reservoirs** — the water column is a measured null at double the
  earlier sample; resampling it answers a question already answered.
- **Iraq (Ganau / Dukan)** — kept only as a **low-cost contingency** if access
  exists. Dissolved iron was never measured there; a single visit measuring TSS
  and dissolved Fe would settle whether its optical signal is suspended
  sediment, which is the working hypothesis.

---

## 3. How many — derived, not asserted

A "station" is one location sampled once, synchronously with an overpass.

### 3.1 Severity ranking (H-RANK)

Stations per district to detect a within-district Spearman rho, α = 0.05
two-sided, power 0.80:

| true rho | stations per district | simulated power at that n | anchor |
|---|---|---|---|
| 0.30 | **89** | 0.820 | the project's bar |
| 0.40 | 51 | 0.828 | |
| **0.50** | **33** | 0.832 | **design target** |
| 0.568 | 25 | 0.848 | measured pooled value |
| 0.64 | 20 | 0.869 | measured Central City / Silverton value (Ouray +0.68; Leadville +0.004) |

**Why the design targets rho 0.5 within district rather than 0.3:** detecting
0.3 in *every* district needs 89 × 4 = **356** stations, which is not a
realistic single campaign. Pooled within-region, 144 stations clears the 89
needed for rho 0.3 (approximately, treating stations as independent).

### 3.2 Why the archival data could not settle sign consistency

Probability that **every** district estimates a positive rho when the true
effect is positive:

| true rho | stations per district | P(all 3 positive) | P(all 4 positive) |
|---|---|---|---|
| 0.30 | 20 | 0.750 | **0.681** |
| 0.30 | 30 | 0.867 | 0.827 |
| 0.30 | 50 | 0.946 | 0.929 |
| 0.50 | 20 | 0.962 | 0.949 |
| 0.50 | 30 | 0.993 | 0.990 |

**At the ~20 source points per district in the archive, a real rho of 0.3
still fails the four-district sign check about one time in three.** Leadville's
+0.00 may be partly sampling, not only heterogeneity — and a campaign is the
only way to tell.

### 3.3 Discovery (H-DISC)

Field visits to estimate a proportion to a 95% Wilson half-width:

| half-width | at p = 0.5 (worst case) | at p = 0.2 |
|---|---|---|
| ± 0.20 | 21 | — |
| **± 0.15** | **39** | 26 |
| ± 0.10 | 93 | 60 |

**Recommended: ~40 visits to flagged sites with no record (precision) and ~40
to known sources (recall).**

### 3.4 Recommended design

| component | stations / visits | what it buys |
|---|---|---|
| **Campaign A** — 4 districts × 36 (9 per iron tier) | **144** | power ≥ 0.80 for within-district rho 0.5; P(all 4 positive \| rho 0.3) > 0.83; pooled rho 0.3 |
| minimum viable A — 3 districts × 33 | 99 | rho 0.5 within district; drops the four-district check |
| **Discovery** — flagged-unrecorded + known sources | **~80** | precision and recall each to ± 0.15 |
| **Campaign B** — 3 basins × 30 | **90** | P(all 3 positive \| rho 0.3) = 0.867 for the UAV comparison |
| field duplicates and blanks | +10% | QA/QC |

**Two sampling events per station** (high flow and baseflow) would separate
dilution from loading. If the budget allows only one, sample at **baseflow**,
when concentrations are highest.

---

## 4. What to measure at every station

### 4.1 Water

- **Iron, both fractions:** dissolved (field-filtered 0.45 µm, acidified) **and**
  total. The distinction is central — total iron tracks suspended sediment,
  which *is* optically visible, so pooling the two manufactures correlation.
- **Fe²⁺ measured in the field**, colorimetrically, at collection. It oxidises
  within minutes to hours; a lab value is not Fe²⁺.
- SO₄²⁻, pH, Eh/ORP, specific conductance, temperature, alkalinity/acidity,
  Al, Mn.
- **TSS and turbidity** — the main optical confound; turbidity is what the
  water arm already detects.
- **DOC / CDOM** — the other main confound.
- Chlorophyll-a.

### 4.2 Sediment and precipitate — new

The July design had none of this, though the project concluded that
circumneutral drainage precipitates its iron to the bed and that the precipitate
is the plausible target.

- **Bed sediment:** composite of three grabs, top ~2 cm.
- **Shoreline / bank precipitate:** scrape within a fixed quadrat at the channel
  margin; photograph with a colour card.
- **Precipitate areal cover and thickness** within the quadrat — this is what
  links a field observation to a fraction of a pixel.
- **Lab:** total and acid-extractable Fe; **XRD mineralogy on a subset** to
  identify phases (schwertmannite, ferrihydrite, goethite, jarosite). At
  7 bands these collapse into one ferric group; whether they separate at
  higher spectral resolution is H-PRECIP.

### 4.3 Spectroscopy

- **Above-water radiometry** (ASD-class): water-leaving radiance, sky radiance
  and downwelling irradiance, with sky-glint removal following an established
  above-surface protocol (e.g. Mobley 1999, *Applied Optics*). This bypasses
  atmospheric correction, which was a demonstrated confound.
- **Contact-probe spectra** of wet precipitate, dried precipitate, and uncoated
  substrate at the same site.
- White-reference calibration at every station.

### 4.4 Synchrony and ancillary

- **Within ±1 hour of a Sentinel-2 or Landsat 8/9 overpass**, clear sky.
  **Record the actual offset** at every station; do not round it away.
- GPS (≤ 3 m), Secchi depth, water depth, bottom type, flow or stage, wind,
  cloud, sun and view geometry, photographs.

---

## 5. The drone test (Campaign B)

### 5.1 The prediction originally planned does not discriminate

It was that low-altitude imaging would bring the canopy diagnostic — median
buffer NDVI — below 0.6. **Leaf-off satellite already achieves that on its
own:** 0.462 in Ohio and 0.529 in Pennsylvania, against 0.870 leaf-on. A test
the satellite passes cannot justify a drone.

### 5.2 H-UAV — the discriminating comparison, on the same stations

Every Campaign B chemistry station gets both a leaf-off satellite value
(extracted with the existing `python/cmd_detect.py` pipeline) and a UAV value
(a ≥10-band index sampled along the channel margin at that station). Both are
scored against the same measured chemistry.

| outcome (the bar: \|rho\| ≥ 0.3 with sign consistency across the 3 basins) | verdict |
|---|---|
| UAV meets the bar **and** satellite does not | **SUPPORTED** — the drone adds information |
| **both** meet the bar | **NO ADDED VALUE** — satellite suffices |
| UAV does not meet the bar | **NOT SUPPORTED** |

These rows are mutually exclusive and exhaustive. **NOT SUPPORTED is a
publishable result** — it would bound airborne monitoring of coal drainage —
and is reported as prominently as SUPPORTED.

### 5.3 Why this is not a revival of a withdrawn argument

Two drone arguments were withdrawn by this project's own tests (resolution, and
a near-channel reading of the Ohio signal), and CMD3's registration forbids
reviving the withdrawn one. H-UAV is justified by a **hypothesis tested against
a satellite baseline**, not by the withdrawn evidence, and it can fail.

### 5.4 Flight design parameters, to be fixed in the registration

- Leaf-off only; calibration panel imaged on every flight.
- Ground sample distance chosen to resolve the channel margin — fix the value
  in the registration from measured channel widths, not afterwards.
- Flights within the same synchrony window as the chemistry.

---

## 6. Analysis plan — reuse what already exists

| task | existing code |
|---|---|
| AUC, Youden J, worst-case leave-one-region-out, within-region permutation, BH correction | `python/seep_detect.py` |
| dose-response, canopy gate, sign consistency | `python/cmd_detect.py` |
| upstream catchments (validated 6/6) | `python/catchment_dem.py` |
| sample sizes | `python/field_power.py` |
| new regions without editing source | `python/fetch_wqp.py --bbox` |

**Standing rules, each learned by getting it wrong:** judge by worst-case
leave-one-district-out, never pooled or within-site; report the between/within
variance split beside any pooled correlation; correct for multiple comparisons;
never test a hypothesis on the data that generated it; report nulls as
prominently as positives.

---

## 7. What each outcome would mean

| outcome | what it establishes |
|---|---|
| H-RANK supported | severity ranking survives synchronous measurement — the archival positive was not a date artifact |
| H-RANK not supported | the archival positive was partly an artifact of unsynchronised data |
| H-DET pass | the 0.016 shortfall was measurement noise, and detection is achievable |
| H-DET fail | detection is genuinely out of reach at satellite spectral resolution — a citable bound |
| H-LIMIT (any value) | the first defensible detection limit for this method |
| H-PRECIP satellite-detectable | reframes the target from water to substrate |
| H-PRECIP spectrally limited | a hyperspectral or ≥10-band sensor is the justified next step |
| H-DISC (any interval) | the first measurement of whether the tool finds anything new |
| H-UAV supported / no added value / not supported | whether airborne monitoring of coal drainage is worth its cost |

**There is no outcome here that fails to produce a publishable result.**

---

## 8. Risks

- **Cloud cover breaks synchrony.** Plan more field days than usable overpasses.
- **Snow and access** at the Colorado districts.
- **Winter sampling** for leaf-off Campaign B — ice and access.
- **Holding times** — especially Fe²⁺, which is why it is measured in the field.
- **Mine sites are hazardous.** Never enter adits, shafts or tunnels; sample
  discharge at the portal from outside. Obtain landowner and agency permission
  before any visit.
- **Unfillable tiers** — Ouray may not reach nine high-iron stations (§2).

## 9. Decisions that remain yours

Exact station locations within each district or basin, permits and land access,
the analytical laboratory, the budget, and whether to fund the second
(high-flow) sampling event.
