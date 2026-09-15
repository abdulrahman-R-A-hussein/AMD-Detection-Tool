# Grant case — what the preliminary data supports, and what a field campaign would resolve

**Prepared 2026-09-13** for a PhD grant application. Author: **Abdulrahman
Hussein**, Kent State University, Dr. Joseph D. Ortiz laboratory.

**Companion documents:**
[`validation/ACCURACY_ASSESSMENT.md`](../validation/ACCURACY_ASSESSMENT.md) (every
number with its sample size and reference standard) ·
[`docs/FIELD_CAMPAIGN.md`](FIELD_CAMPAIGN.md) (sampling design and sample sizes) ·
[`validation/STATE.md`](../validation/STATE.md) (canonical state).

> **Use this document to decide what the proposal may say.** It does not claim
> a breakthrough, because the data do not support one. It argues something a
> reviewer can check and is harder to dismiss: the preliminary work has
> established exactly where free satellite data stop being informative, and
> every one of those limits names a measurement that only fieldwork can make.

---

## 1. For a reviewer, in one paragraph

USGS published an automated method for mapping iron-sulfate minerals from
Landsat (Rockwell & Gnesda 2021, SIM 3466) but released no code. This work
reimplements it faithfully and then measures, against real water chemistry and
under criteria written down before each test, what it can and cannot do. It
**ranks** mine-drainage severity within a mineral district
(rho +0.568 against measured dissolved iron, n=75); it does **not** detect
mine drainage against clean ground (a measured null at 86 confirmed discharge
points), does not predict concentration across districts, and in a pre-registered
blind search it did not find unknown sites. Detection and severity are both flat from
10 m to 100 m pixel size, so the limit is **spectral and radiometric, not
spatial**. The proposed campaign pairs synchronous field spectroscopy with
water and sediment chemistry to measure the quantities the satellite cannot —
and tests, rather than assumes, whether a drone adds anything.

---

## 2. What is established

| result | figure | reference standard |
|---|---|---|
| Faithful replica of SIM 3466 | all six index formulas reproduce exactly | the published pamphlet |
| Our own "improvements" were regressions | fixing them: worst-case leave-one-site-out Youden J **0.107 → 0.440** (4.1×), 3 sites | Rockwell's map — **replica fidelity, not accuracy** |
| **Severity ranking** | `FerricIron1` vs dissolved Fe **rho +0.568**, n=75, within-region permutation **p=0.0004**, BH q=0.0072, 24% between-region variance | **measured chemistry** |
| — per district | positive in **three of four**: Central City +0.64 (n=20) · Ouray +0.68 (n=17) · Silverton +0.64 (n=15). **Leadville +0.004 (n=23): no relationship.** The raw report prints it as `+0.00` and flags `[ALL +]` because its check only tests ρ > 0 | measured chemistry |
| — most robust form | vs **pH**, all four negative and tight: −0.30 · −0.40 · −0.24 · −0.27 | measured chemistry |
| Catchment delineation | **6/6 within ±33%** of official USGS drainage areas (previous method 2/6) | NWIS published areas |
| Coal-drainage vegetation signal | negative and **sign-consistent across three disjoint Pennsylvania sub-basins** (conductance −0.187, n=443, p=0.0002) | measured chemistry |

**The bound that must travel with the severity result:** leave-one-region-out
R² is **negative for every** index × analyte pair. It ranks within a district;
it does not predict concentration in a new one. Quote **+0.568 as the Landsat 8
value** — Sentinel-2 gives +0.549.

---

## 3. What is null — stated as null

| null | figure |
|---|---|
| **Detection** of mine discharge vs clean ground | all 9 indices fail all 3 control tiers at **n=86**; best case J **0.234** vs a pre-registered bar of **0.25** |
| The shipped 19-class classifier | vs non-circular bare ground: AUC **0.442**, J **−0.252** (corrected for tied scores; the raw report printed 0.000); at Leadville its median is **7.7× higher on bare ground** than at mine targets |
| **Dissolved iron in the Ohio water column** | no feature's 95% CI excludes zero (iron n=17, sulfate n=23); turbidity *is* detected (rho up to 0.499) |
| **Spatial resolution** as the constraint | flat at 10 / 20 / 30 / 60 / 100 m: +0.494 / +0.526 / +0.493 / +0.523 / +0.517 |
| A **transferable scale** for the coal signal | Ohio strengthens to 1 km (−0.438); Pennsylvania collapses there (+0.003) |
| **Blind search** for unknown sites | **tested 2026-09-15, not supported** (pre-registered): no signal in never-analysed districts (4 of 32 sites flagged at a 5% budget, p = 0.074); not better than bare ground where the index was chosen (McNemar p = 0.038 against α 0.025) |

---

## 4. Why the nulls justify the campaign

This is the section that does the work. Each null names a measurement that
**cannot** be made from archival satellite data plus public chemistry.

| null | what would resolve it | why the satellite archive cannot |
|---|---|---|
| Detection misses the bar by 0.016 | **Synchronous** field reflectance + chemistry at the same moment | public chemistry is sampled on days unrelated to overpasses; temporal mismatch is in every number above |
| Ranking does not transfer across districts | a **detection limit and response curve per district**, from a stratified iron gradient | archival stations cluster at whatever concentrations agencies chose to monitor; the gradient is not controlled |
| Water column is a null while turbidity is detected | co-measured **TSS, turbidity, DOC/CDOM** at every station | these confounds are absent or unmatched in public records, so iron cannot be separated from sediment and colour |
| The detectable target is plausibly the **precipitate**, not the water | **bed-sediment and shoreline-precipitate** sampling with field spectra of the precipitate itself | no public dataset measures precipitate composition at mine outflows |
| Resolution is flat, so the limit is spectral | an **ASD-class field spectrometer** and a **≥10-band** sensor | the index panel is built from 7 broad Landsat-equivalent bands (Sentinel-2 is mapped onto the same set), at which the iron minerals collapse into one ferric group; what narrower bands resolve cannot be learned from those 7 |
| The archival blind search found no discovery signal | **field visits** to a registered sample of flagged ground with no record, and to known sources it misses | whether flagged unrecorded ground is ever a source has no ground truth until someone goes there; the archive predicts mostly spoil and outcrop |

**A tool that already detected mine drainage would need no campaign.** The
preliminary data are valuable precisely because they locate the boundary.

---

## 5. The methodological asset — and exactly what it proves

### 5.1 Retractions caught before publication

Each of these was a claim the author believed, tested, and withdrew:

- **The in-water contamination module** — every ratio index ranked the *clean*
  control lake highest; the apparent validation was circular.
- **"Our map predicts dissolved iron better than Rockwell's"** — strong at n=6,
  collapsed when raised to n=31 across seven river systems.
- **"Our tool is more sensitive than Rockwell's"** — the direction of
  disagreement reverses between sites (4.1× more at one, 5.6× fewer at another).
- **"Resolution is the binding constraint"** — refuted by a within-sensor
  ladder; the improvement was a sensor effect.
- **A near-channel reading of the Ohio coal signal**, and the drone argument
  drawn from it — refuted when the radius ladder was extended.
- **A pooled sulfate correlation** (rho −0.563, p=0.001) — reversed sign to
  +0.220 once region effects were removed; it was 67.5% between-region variance.

### 5.2 Pre-registration — verifiable, with an honest limit

Seven phases were registered in writing and committed to git **before** their
results were committed. An eighth, the blind search, followed: registered in
`ad05971` on 2026-09-14, result on 2026-09-15. The seven were verified
2026-09-13 by commit ancestry, not by filename:

| phase | registration | results | gap |
|---|---|---|---|
| B2 detection | `4bb3b63` 2026-08-14 15:50 | `fa1f7e2` 20:56 | 5 h 06 m |
| B2b classifier fix | `df6a6ae` 2026-08-16 14:19 | `b735737` 14:53 | 34 m |
| B2c continuous score | `6af0b5b` 2026-08-16 16:54 | `eba7116` 17:12 | 18 m |
| B2d chemistry controls | `56aa3aa` 2026-08-16 20:03 | `c8d0180` 20:27 | 24 m |
| CMD1 coal drainage | `8531227` 2026-08-24 19:10 | `d3a2c5b` 19:21 | 11 m |
| CMD2 confound | `a452446` 2026-09-08 20:26 | `0cad804` 20:57 | 31 m |
| CMD3 replication | `4765bca` 2026-09-09 19:16 | `e2ef059` 20:48 | 1 h 32 m |

**What this proves, and what it does not.** Commit order proves each
registration existed in the repository before its results were committed. It
does **not** prove the analysis was not run locally in the gap — which is as
short as 11 minutes. Do not overstate it to a reviewer.

**The stronger evidence is that registrations fired against the author's
interest.** CMD2's registered secondary test refuted CMD1's preferred reading
and withdrew a drone argument the author wanted. CMD3 fired the falsifier its
own registration named, bounding a result from the day before. Retrofitted
registrations do not do that.

**Two disclosures a careful reviewer would otherwise find:**
- The CMD1 files carry **2026-08-16 in their filenames** but entered git on
  **2026-08-24**. Ordering between registration and result still holds.
- CMD3's registration had **non-mutually-exclusive verdict rows**. The
  specific named falsifier was applied rather than the kinder row, and the
  defect is recorded as a correction in `validation/DECISION_LOG.md`.

---

## 6. Instrumentation — what the evidence supports buying

| item | supported by | strength |
|---|---|---|
| **ASD-class field spectrometer** | resolution is flat 10–100 m, so the limit is spectral/radiometric; field water-leaving reflectance bypasses atmospheric correction, a demonstrated confound | **strong** |
| **≥10-band multispectral sensor** (UAV-mounted) | same axis; narrower bands test what 7-band Landsat cannot resolve — the iron minerals collapse to one ferric group at 7 bands | **strong** |
| **Water + sediment chemistry** (filtered/unfiltered Fe, Fe²⁺/Fe³⁺, SO₄²⁻, TSS, DOC/CDOM) | every null in §3 is unresolvable without it | **strong** |
| **UAV platform** | — as a **hypothesis to test**, not a demonstrated need (§6.1) | **conditional** |
| **Sub-metre / 7 cm imaging on resolution grounds** | **not supported.** A resolution-based ask would contradict this project's own published refutation | **do not argue** |

### 6.1 The drone, framed so it survives review

Two drone arguments have already been withdrawn by this project's own
pre-registered tests, and CMD3's registration forbids reviving the withdrawn
one. A new, separately registered test is not a revival — **provided it is
justified by a hypothesis, not by the withdrawn evidence.**

**The prediction originally planned does not discriminate, and must not be
used.** It was that low-altitude imaging would bring the canopy diagnostic
(median buffer NDVI) below 0.6. **Leaf-off satellite already does:** 0.462 in
Ohio and 0.529 in Pennsylvania, against 0.870 leaf-on. A test that satellite
passes on its own cannot justify a drone.

**The discriminating test is UAV against satellite, at the same stations:**

> **H-UAV.** At stations where co-located leaf-off Landsat/Sentinel-2 buffers
> fail the project's bar (|rho| ≥ 0.3 with sign consistency) against measured
> iron, a ≥10-band UAV index sampled along the channel margin **meets** it.
>
> **Falsifier:** the UAV index performs no better than the satellite buffer on
> the same stations, or meets the bar only where the satellite already does.

If H-UAV fails, that is a publishable result — it would bound airborne
monitoring of mine drainage — and it must be reported as prominently as a pass.

---

## 7. Claim boundaries — verbatim, so the proposal cannot drift

**MAY claim**
- Faithful SIM 3466 replica (index level, exact).
- Our three departures were regressions; fixing them improved worst-case
  cross-site J 4.1×.
- Continuous `FerricIron1` separates AMD-affected from **chemically-verified
  clean** water at **monitored locations**, out-of-region across 4 Colorado
  districts, with a score **monotone in measured contamination**.
- Continuous scoring separates mine discharge from bare ground (J +0.617)
  where the binarised classifier cannot (0.000).
- In coal watersheds a **vegetation** index tracks measured sulfate and
  conductance **negatively**, replicating across two independent basins.

**MAY NOT claim**
- Finding unknown sources in blind scene-wide search — **tested 2026-09-15, not supported**.
- Optical **sulfate** detection at any concentration — sulfate has no VNIR
  absorption. **Ever.**
- That resolution is the constraint — **refuted** for 10–100 m.
- That the method works for neutral-pH coal drainage — **measured null**.
- That the coal signal is near-channel, or landscape-scale in general.
- That agreement with Rockwell's map means accuracy.
- Any cost-saving percentage — none has ever been measured.
- That this is the best, first, or most accurate detection tool — nothing
  measured supports a comparative claim.

---

## 8. What a reviewer will find, and how to get ahead of it

| they will find | address it by |
|---|---|
| **Zenodo DOI 10.5281/zenodo.19429983**, whose abstract (≤ v1.5.4) claims validation against Muskingum Watershed chemistry — the opposite of the measured null | **publish the corrected Zenodo version before submitting.** The corrected text is in `CITATION.cff`; a local edit does not change a minted DOI |
| The earlier ResearchGate item on "cryptic sulfate pollution" | cite it only alongside the retraction; do not reuse its claims |
| An author-name inconsistency in an April 2026 release document | corrected in the repository; check that it did not propagate elsewhere |
| Negative leave-one-region-out R² | state it first, in the results, before a reviewer finds it |
| The Colorado positive rests on four districts | say so, and propose the campaign as the test of transfer |

---

## 9. Limitations of the preliminary data

- The one ground-truth positive is **Colorado-only, four districts**, and does
  not transfer across them.
- All chemistry is **archival**, unsynchronised with imagery.
- Rockwell's comparison raster covers the **US Southwest only**.
- The Pennsylvania coal result is **unconditioned** for mining extent; no
  non-satellite mine-extent source is available outside Ohio.
- The Ohio confound test came back **PARTIAL by 0.004**, not cleared.
- **Pre-registration timing** proves order, not that analysis was not run in
  the gap (§5.2).
