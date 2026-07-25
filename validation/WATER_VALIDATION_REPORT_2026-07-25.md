# Water-Path Validation Report — 2026-07-25

**Author:** Abdulrahman Hussein · Kent State University, Dept. of Earth Sciences
**Supervisor:** Dr. Joseph D. Ortiz
**Tool versions covered:** v2.3.2 → v2.4.1
**Scope:** validation of the water (AMD/CMD) arm of the AMD Detection Tool.
The land arm is unaffected and remains sound — see `validation/README.md`.

---

## 1. Executive summary

The question that started this: *why does Piedmont Lake show no contamination
signal while Ganau Pond does?*

**Three separate answers were found, and together they overturn the previous
water result.**

1. **A code defect.** Piedmont's water was never analysed. A water-mask
   threshold tuned at Ganau excluded 100% of Piedmont's and Atwood's water
   pixels. "Clean" was an artifact of the mask. *Fixed in v2.4.0.*
2. **An index defect.** With the mask fixed, the contamination indices turned
   out to rank the **clean control as the most contaminated**. Ganau shows no
   ferric spectral signature at all. The previous "Ganau = severe" result is
   circular. *Documented as findings W1–W3 in v2.4.1.*
3. **The physical answer, from independent ground truth.** Piedmont genuinely
   *is* contaminated — **462 mg/L sulfate, 25× the control** — but its
   dissolved iron is only **0.16 mg/L**. Sulfate is optically invisible, and
   0.16 mg/L iron is far below optical detectability. **Piedmont correctly
   shows nothing. There is nothing there to see.**

**Bottom line:** the water module cannot presently support a contamination
claim, and — importantly — for these particular lakes *no optical method
could*. This is a detection-limit result, not a tool failure. It is
publishable as such, and it redirects the water work toward targets that are
physically detectable.

---

## 2. What was done

| # | Action | Outcome |
|---|---|---|
| 1 | Re-ran Test D exactly as previously reported | Reproduced the old result, then found it was computed on whole scenes, not water pixels (protocol §D step 1 was skipped) |
| 2 | Counted `water_class` per scene | Piedmont **0/20000**, Atwood **0/20000**, Ganau 79 — the water module never ran on the Ohio lakes |
| 3 | Traced the mask logic in `createUnifiedWaterMask()` | Found `AWEINSH > 0.20`, tuned at Ganau per the code comment |
| 4 | Reproduced all mask gates offline over the exported CSVs | Quantified the exclusion (table §3.1) |
| 5 | Designed and tested a magnitude-free replacement mask | Adopted in v2.4.0; validated against a land control |
| 6 | Simulated old vs widened contamination scoring | Widening breaks the clean control → kept the gate, added an INDETERMINATE class instead |
| 7 | Computed the contamination indices per site | **Found the ranking inverted** (finding W1) |
| 8 | Checked ferric physics (blue→red slope) | Ganau shows **no ferric rise** (finding W1) |
| 9 | Reproduced the Ortiz-lab stepwise pipeline on its own reference sites | Works, but does not discriminate at 5 bands (finding W2) |
| 10 | ROC on albedo-normalised spectra, matched controls | Only Piedmont-vs-Atwood is a fair test (finding W3) |
| 11 | **Queried the Water Quality Portal (USGS NWIS + EPA STORET)** | **Obtained real chemistry for both Ohio lakes (finding W4)** |

All code changes are committed and tagged (v2.4.0, v2.4.1). Every number below
is reproducible from CSVs committed in this repository.

---

## 3. Results and findings

### 3.1 Root cause — a single-site threshold (fixed in v2.4.0)

`AWEInsh = B2 + 2.5·B3 − 1.5·B5 − 0.25·B7` is an **absolute-magnitude** index,
so a fixed cut scales with scene brightness:

| Scene | optically water (MNDWI>0.3) | passed `AWEINSH>0.20` | median AWEINSH | median brightness |
|---|---|---|---|---|
| Ganau (Iraq, bright) | 230 | **230 (100%)** | 0.229 | 0.076 |
| Piedmont (Ohio, dark) | 497 | **0** | 0.070 | 0.022 |
| Atwood (Ohio, dark) | 466 | **0** | 0.072 | 0.020 |

Feyisa et al. (2014) intend a ≈0 threshold; it had been raised to 0.20 to
reject wet soil at Ganau. Two further Ganau-tuned gates (`brightness ∈
(0.05,0.20)` on every scoring criterion, `DepthProxy < 1.3`) each
independently excluded the Ohio lakes as well.

**Replacement mask (v2.4.0)** — every term magnitude-free except a deliberate
brightness *ceiling*, because snow/ice passes all four spectral tests and is
separable only by albedo:

```
MNDWI > 0.3  and  AWEInsh > 0  and  NDVI < 0  and  NIR < Green  and  Brightness < 0.30
```

| scene | water px before | after |
|---|---|---|
| Ganau | 230 | 230 (no regression) |
| Piedmont | **0** | **255** |
| Atwood | **0** | **365** |
| Silverton (land control) | 2 | 11 / 20000, all class 0 — no mineral pixels stolen |

`NDVI < 0` was validated against the positive control *before* adoption: Ganau
water is NDVI ≤ −0.12 at p95, so the strict cut costs the contaminated site
nothing.

### 3.2 Finding W1 — the contamination indices are inverted

Computed on v2.4.0 water pixels:

| site | yellow (G/B) | turbidity (R/B) | iron idx | NIR | **red/blue** |
|---|---|---|---|---|---|
| Ganau (675 mg/L sulfate) | 1.25 | 0.85 | 0.53 | 0.044 | **0.85** |
| Piedmont | 1.93 | 1.21 | 0.55 | 0.016 | 1.13 |
| **Atwood (clean control)** | **2.39** | **1.48** | **1.09** | 0.012 | **1.35** |

Every ratio-based index is **highest at the clean control**. Only NIR orders
correctly, and NIR responds to suspended sediment and atmospheric path
radiance as much as to dissolved iron.

**Physical test:** Fe³⁺ absorbs strongly in the blue, so ferric-stained water
must *rise* from blue to red. **Ganau's red/blue = 0.85 — it falls.** Ganau
water carries no ferric signature. It scored "severe" only because it is
bright enough to pass the reliability gate while the others were silenced by
it — and because the thresholds had been tuned until it did.

### 3.3 Finding W2 — 5-band material ID does not discriminate

Reproduced the lab pipeline (`D:\dev\VPCA+STEPWISE-REGRESSION`) on its own
reference loadings, using a curated 12-material AMD candidate set:

| site | expected | result |
|---|---|---|
| Vaal Dam (Witwatersrand mining) | AMD | VPC6 → `Acid Mine Dr Assemb2-Fe3+`; VPC2/3 → jarosite ✓ |
| **Indian River Lagoon (FL, no mining)** | **none** | **VPC2 → Jarosite R²=0.96; VPC4/5 → Ohio Fe concretions** ✗ |

A Florida coastal lagoon returning jarosite is a false positive. With **N = 5
observations** (the 5 water-penetrating S2 bands) any single library spectrum
reaches R² ≈ 0.9 by chance, curated or not — consistent with the lab's own
caveat in `docs/REAL_GEE_RUN_RESULTS.md`. **Per-component material ID at 5
bands is a hypothesis generator, not a discriminative test.** It must not be
used to certify a lake as AMD-positive.

Curated set kept at `python/library_s2_amd_curated.csv`.
Gap noted: **schwertmannite is absent from both lab libraries.**

### 3.4 Finding W3 — only one comparison is methodologically fair

ROC AUC on albedo-normalised band fractions (magnitude removed), vs the Atwood
control:

| feature | Ganau vs Atwood | **Piedmont vs Atwood** |
|---|---|---|
| fB1 (443 nm) | 0.986 | **0.780** |
| fB2 (482 nm) | 0.996 | **0.731** |

**Ganau vs Atwood is confounded** — different continent, atmosphere (Iraqi
dust inflates blue), water type and depth. AUC ≈ 0.99 cannot be attributed to
contamination. **Piedmont vs Atwood is the fair test** (same region, sensor,
dates, atmospheric correction) and gives a real but *moderate* AUC ≈ 0.78.

### 3.5 Finding W4 — ground truth resolves it (NEW)

Retrieved from the **Water Quality Portal** (aggregates USGS NWIS + EPA
STORET + Ohio EPA), in-lake stations only, 2013 onward:

| lake | n (SO₄) | sulfate median | sulfate range | n (Fe) | iron median | iron max |
|---|---|---|---|---|---|---|
| **Piedmont** | 26 | **462 mg/L** | 374–560 | 26 | **162 µg/L** | 1,530 µg/L |
| **Atwood (control)** | 101 | **18.3 mg/L** | 10.6–23.1 | 86 | **302 µg/L** | 2,750 µg/L |
| Ganau (published) | — | 675 mg/L | — | — | not measured | — |

Piedmont stations: `21OHIO_WQX-201927` (L-1), `21OHIO_WQX-301988` (L-2),
`USGS-400925081105700`. Atwood stations: `21OHIO_WQX-201925/201926/303523/303524`,
`USGS-403219081155500`. Sample dates: Piedmont 2013-06-05 → 2016-05-17;
Atwood 2015-04-14 → 2017-10-18 — both **inside** the L8 composite window
(2013-2020) used by the tool.

**Three consequences:**

1. **Piedmont is genuinely contaminated.** 462 mg/L sulfate is 25× the control
   and the same order as Ganau's 675 mg/L. The site selection was correct; the
   documented coal-mine-drainage legacy is real and current.
2. **Atwood is a valid control for sulfate (18 mg/L) but NOT for iron** — its
   iron is *higher* than Piedmont's (302 vs 162 µg/L; note 80/86 Atwood values
   are Total Recoverable, i.e. including particulates, so this partly reflects
   suspended sediment rather than dissolved metal). Any specificity claim
   phrased in terms of iron is invalid.
3. **Neither lake can be detected optically.** Sulfate has no VNIR absorption
   at any concentration. Dissolved iron at 0.16–0.30 mg/L is one to two orders
   of magnitude below the level at which ferric iron visibly colours water
   (visible orange staining is generally a mg/L-scale phenomenon; the precise
   limit for L8/S2 should be established from literature and from the field
   campaign in §6).

**So the honest answer to the original question is not "Piedmont is clean" and
not "the tool missed it". It is: Piedmont is contaminated by sulfate, sulfate
is invisible, its iron has already precipitated out of the water column, and
therefore no optical sensor can see it. The tool's negative is correct — but
it was correct for the wrong reason, since the mask had excluded the lake
entirely.**

---

## 4. What this changes

- **Retract** the 2026-07-23 Test D result (done, v2.4.1).
- **Do not** present Ganau as a validated water detection. Its ground truth is
  *sulfate*; its spectrum shows no ferric signature; its thresholds were tuned
  to it.
- **Do** present the detection-limit finding. "I selected a genuinely
  contaminated lake, obtained independent chemistry, and demonstrated the
  contamination is below optical detectability" is a stronger, more rigorous
  result than an unexamined positive.
- **The land arm is unaffected** and remains the headline result: Silverton
  VPCA closure AUC 0.961, ROC-derived thresholds (Test C), Atwood control
  recovering no ferric component, and the honest IronSulfate-vs-bare-rock
  failure (AUC 0.769).

---

## 5. Next steps — achievable now, with free existing data

These need no fieldwork and no new funding.

### 5.1 Matched-date spectra ↔ chemistry dataset (highest value)

The chemistry above is **dated**, and the satellite archive is **free and
historic**. Pair them:

1. Download full WQP results (not just summaries) for the in-lake stations,
   keeping `ActivityStartDate`, station coordinates, and every characteristic
   (Fe, SO₄, pH, turbidity, TSS, conductivity, chlorophyll).
2. For each sample date, find the nearest cloud-free Landsat 8/9 or Sentinel-2
   scene within **±3 days** (S2 has 5-day revisit, so most samples will match).
   Do *not* use the median composite for this — use the single scene.
3. Extract the water-pixel spectrum at the station coordinate (3×3 median to
   suppress noise), applying the v2.4.0 mask.
4. Build the table: one row per sample = spectrum + measured chemistry.
5. Regress and report the **detection limit**: at what Fe concentration does
   any band or ratio begin to respond above noise? Expected answer given
   0.16–0.30 mg/L: *no response*, which is itself the publishable result.

This converts "we can't see it" from an assertion into a measured limit.
Piedmont (26 samples) + Atwood (101 sulfate / 86 iron) gives ~110 candidate
match-ups before cloud screening.

### 5.2 Add a genuinely detectable site

The Ohio sites that *do* show orange ferric staining are the actively
discharging AMD streams of the Monday Creek / Sunday Creek / Raccoon Creek
watersheds (Ohio University's ORITE has long-running research there). These
have Fe in the mg/L to tens-of-mg/L range and visible precipitate.

Caveat to check first: those are **streams**, often narrower than a 30 m
Landsat pixel. Screen for reaches, ponds, or treatment-system settling basins
wide enough for ≥3 clean pixels (Sentinel-2 at 10 m helps). Where a wide
enough target exists, that is where optical detection should succeed — and it
provides the positive control the water arm currently lacks.

### 5.3 Fix the remaining tool issues

- Add a **water-pixel-only export** (all water pixels, not a 20k scene
  subsample) so the protocol's `water_class >= 0` filter has rows.
- Rebuild the contamination score around shape-based, albedo-normalised
  features rather than raw ratios, and re-derive every threshold by ROC
  against real chemistry (the Test C method, which worked for land).
- Add **schwertmannite** to the spectral libraries.
- Re-examine `DepthProxy < 1.3`, which is also magnitude-dependent.

### 5.4 Housekeeping

- The lab framework's `graphify-out/graph.json` is stale (built at the initial
  commit; missing all of `src/vpca` and `scripts/`).
- **Security:** `D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json`
  is a live GCP service-account private key in plaintext at the repo root. It
  is gitignored and not in git history, but rotate it if that tree is ever
  copied or shared.

---

## 6. Future work — PhD field campaign design

The single thing that would convert this from a limitation study into a
validated method is **synchronous field spectroscopy plus water chemistry**.

### 6.1 Core design

**Sample within ±1 hour of satellite overpass.** Sentinel-2 revisits every 5
days; overpass times are published. Anything not synchronous introduces
variability that will dominate the signal you are trying to measure.

**Site stratification — pick a concentration gradient, not just "polluted vs
clean". The current work failed partly because both Ohio lakes sit at the same
(undetectable) iron level.** Target roughly:

| tier | dissolved Fe | example |
|---|---|---|
| control | < 0.1 mg/L | Atwood-type reservoir |
| low | 0.1–1 mg/L | Piedmont-type reservoir |
| moderate | 1–10 mg/L | AMD-influenced pond / settling basin |
| high | 10–100+ mg/L | active seep, orange precipitate |

Without the top two tiers there is no signal to calibrate against.

### 6.2 Measure at every station

- **Water chemistry:** dissolved **and** total Fe (filtered 0.45 µm vs
  unfiltered — the distinction is central here), Fe²⁺/Fe³⁺ speciation, SO₄²⁻,
  pH, Eh, alkalinity/acidity, conductivity, **TSS and turbidity** (the main
  optical confound), DOC/CDOM (the other main confound), chlorophyll-a.
- **Field spectroscopy:** ASD or equivalent, water-leaving reflectance with
  proper sky-glint correction. This is the crucial bridge — it lets you test
  the spectral hypothesis independently of atmospheric correction, which was a
  confound in this study (Iraqi dust inflating Ganau's blue).
- **Ancillary:** Secchi depth, water depth, bottom type (bottom reflectance
  contaminates shallow water), wind state, sun/view geometry, GPS.

### 6.3 What this enables that the current data cannot

1. **A real detection limit** for Fe in water for L8/S2 — a defensible,
   citable number.
2. **Deconvolution of the confounds** (turbidity, CDOM, bottom, atmosphere)
   that presently make Ganau-vs-Atwood uninterpretable.
3. **Atmospheric-correction validation** — compare field water-leaving
   reflectance against L2 surface reflectance at the same moment.
4. **Honest end-members.** The current `fe3_water` vector is invented. Field
   spectra of actual AMD water become a real library entry, convolvable to
   L8/S2 via the existing `convolve_splib07()` function.
5. **A defensible VPCA/stepwise application** — with N in the hundreds of
   samples rather than 5 band-observations, the statistics stop being
   degenerate (finding W2).

### 6.4 Suggested framing for the thesis

The most defensible scope, given everything above:

> The tool detects **iron-bearing mineral surfaces** (gossans, ferricrete,
> precipitate-coated substrate) reliably — validated at Silverton, AUC 0.961.
> It does **not** detect dissolved sulfate, and detects dissolved iron only
> above a concentration threshold established in this work. Where mine
> drainage is circumneutral and iron has precipitated to the sediment, the
> detectable target is the **precipitate on the bed and shoreline**, not the
> water column.

That reframing turns the negative result into the contribution, and it is
consistent with everything measured here.

### 6.5 Ganau / Dukan (Iraq)

If Iraqi fieldwork is possible, the same protocol applies, plus: measure
**dissolved iron**, which was never measured at Ganau — only sulfate. Given
finding W1 (no ferric spectral rise), the working hypothesis is that Ganau's
optical signal is **suspended sediment, not iron**, and a single field
campaign with TSS + Fe would settle it definitively.

---

## 7. Limitations of this report

- Chemistry was retrieved as summary statistics over station groups, not as
  individual dated records; §5.1 requires the full download.
- Piedmont and Atwood sampling windows differ (2013–2016 vs 2015–2017) and do
  not perfectly overlap.
- Atwood iron is dominated by Total Recoverable (80/86), Piedmont mixes
  Dissolved and Total — not strictly comparable fractions.
- Optical detectability of dissolved Fe is asserted here on physical grounds
  and order-of-magnitude reasoning; the precise limit needs a literature
  citation and, ideally, the field campaign in §6.
- Only one contaminated site (Ganau) was available outside Ohio, and it is
  confounded by atmosphere and water type.
- No pixel currently classifies as "clean" under v2.4.0 in any test scene, so
  optical **specificity remains untested, not passing**.

---

## Sources

- [Water Quality Portal](https://www.waterqualitydata.us/) — USGS NWIS + EPA STORET + Ohio EPA aggregated water chemistry
- [USGS Mine Drainage and Water Quality Research](https://usgs.gov/centers/pa-water/science/mine-drainage-and-water-quality-research)
- [Ohio EPA — AMD abatement and treatment plan (Moxahala, App. F)](https://dam.assets.ohio.gov/image/upload/epa.ohio.gov/Portals/35/tmdl/MoxAppF_Final.pdf)
- [Ohio DNR — AMD abatement and treatment plan guidance](https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/minerals/AMDAT_guidance_document.pdf)
- [Ohio University ORITE — Acid Mine Drainage Research](https://www.ohio.edu/engineering/orite/research/projects/acid-mine-drainage)
- [OSU — Remining / AMD fact sheet](https://ceg.osu.edu/media/document/2021-09-09/amd_factsheet_rev2_9.2016.pdf)
