# Acid Mine Drainage (AMD) / Coal Mine Drainage (CMD) Detection System

### An open reimplementation of USGS SIM 3466 — and a pre-registered measurement of what it can and cannot do

[![Version](https://img.shields.io/badge/version-3.10.0-blue.svg)](https://github.com/abdulrahman-R-A-hussein/AMD-Detection-Tool)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-Enabled-orange.svg)](https://earthengine.google.com/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19429983.svg)](https://doi.org/10.5281/zenodo.19429983)

Rockwell & Gnesda (2021, USGS SIM 3466) published a method for automated
iron-sulfate mineral mapping from Landsat 8, and a result raster — but no code.
This repository reimplements that method in Google Earth Engine and Python, and
then does the part that is usually left out: **measures, against real field
chemistry and under pre-registered criteria, where it works and where it
fails.**

Author: **Abdulrahman Hussein**, Kent State University
(Dr. Joseph D. Ortiz laboratory) · ORCID
[0009-0003-0401-9219](https://orcid.org/0009-0003-0401-9219)

---

## ⚠️ Retraction notice — read before citing anything

**Versions up to and including 1.5.4 claimed a validated in-water
contamination-detection capability. Those claims are retracted.** Specifically
withdrawn:

- *"Validated against ground truth geochemical data from the Muskingum
  Watershed, Ohio"* — the Ohio water column is a **measured null**. No
  feature's 95% CI excludes zero for iron (n=17) or sulfate (n=23).
- *"Successfully detected sulfate contamination (>700 mg/L) in Ganau Pond"* —
  **circular.** The thresholds were tuned until that site scored contaminated.
- The *"clean" control lakes* that appeared to pass — the water mask admitted
  **zero** water pixels at two of them (0/497 and 0/466). "Clean" was a mask
  artifact, and one of those lakes carries 462 mg/L sulfate.
- *"Adaptive water masking via AWEINSH threshold optimization"*, listed as an
  innovation — it is the project's canonical failure mode: an absolute cutoff
  on a non-normalised index, which does not transfer between scenes.
- *"Reducing field survey needs by up to 80%"* / *"cost reduction of 70–90%"* —
  no analysis anywhere supports these numbers.

**Sulfate has no VNIR absorption. No optical sulfate detection is claimed at
any concentration**, and none is possible. Any apparent signal is iron,
turbidity, or colour that co-varies with sulfate.

The earlier ResearchGate item *"Automating the Detection of Cryptic Sulfate
Pollution"* and Zenodo versions ≤ 1.5.4 carry the retracted claims and should
be read with this notice attached.

---

## What is actually established

Every figure below is measured, with its sample size and its reference
standard. **Full detail and provenance:
[`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md).**

| capability | result | measured against |
|---|---|---|
| **Land replica** | all six index formulas reproduce **exactly**; three of our own "improvements" were regressions, and fixing them took worst-case leave-one-site-out Youden J **0.107 → 0.440** | Rockwell's published map — **replica fidelity, not accuracy** |
| **Detection of mine discharge** | **NULL.** All nine indices fail all three control tiers at n=86 confirmed source points; best case J **0.234** vs a pre-registered bar of **0.25** | measured USGS/EPA chemistry |
| **Severity ranking** | `FerricIron1` vs dissolved Fe **rho +0.568** (n=75, within-region permutation p=0.0004); positive in three of four districts (+0.64, +0.68, +0.64) and **≈0 in Leadville** (+0.004, n=23) | measured chemistry ✅ |
| — its bound | leave-one-region-out R² is **negative for every** index × analyte pair → **ranks within a district, does not predict across districts** | measured chemistry |
| **Spatial resolution** | **flat** 10–100 m (+0.494 / +0.526 / +0.493 / +0.523 / +0.517) — resolution is *not* the binding constraint in that range | measured chemistry |
| **Coal/CMD vegetation signal** | negative and sign-consistent in two basins, but at a **basin-specific scale** — Ohio strengthens to 1 km, Pennsylvania collapses to +0.003 there | measured chemistry |
| **Catchment delineation** | **6/6 within ±33%** of published USGS drainage areas | official NWIS areas ✅ |

### What may not be claimed

- Finding **unknown** sources in blind scene-wide search — **tested and not
  supported**. A pre-registered blind search (2026-09-15) found no signal in
  districts never used to choose the index (4 of 32 sites, p = 0.074), and no
  advantage over bare ground where it was chosen.
- Optical **sulfate** detection, at any concentration, ever.
- That resolution is the constraint — refuted for 10–100 m.
- That agreement with Rockwell's map means **accuracy** — it is an automated
  product, not ground truth.
- That the shipped 19-class classifier detects mine discharge: measured against
  bare ground it scores **AUC 0.456**, worst-case J **−0.304**. It is
  substantially a bare-ground detector.

---

## Documentation — start here

| document | what it is |
|---|---|
| [`validation/STATE.md`](validation/STATE.md) | **canonical current state** — proven / retracted / open / next. Read first. |
| [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) | how to run both surfaces, what every layer means, what you may conclude |
| [`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md) | every performance number, with n and reference standard |
| [`validation/DECISION_LOG.md`](validation/DECISION_LOG.md) | the chronological journey, wrong turns included |
| [`validation/`](validation/) | dated reports and the pre-registrations, each committed **before** its data |

---

## Quick start

### Earth Engine (no install)

1. Register for [Earth Engine](https://code.earthengine.google.com) (a Google
   Cloud project with the Earth Engine API enabled is required).
2. Paste [`earth-engine/amd_detection_v2.4.0.js`](earth-engine/amd_detection_v2.4.0.js)
   into the Code Editor and Run. *(The filename says 2.4.0; the contents are
   v3.1.0 — see `validation/STATE.md`.)*
3. Pick a preset from **Study Area**, or type latitude / longitude / radius
   under **Custom AOI** and press *Set Custom AOI*. It will point anywhere on
   Earth.

**Before interpreting the output, read `docs/OPERATOR_GUIDE.md` §5** — in
adaptive mode (the default, and the calibrated one) the classification cutoff
is computed from scene statistics, and the guide explains what that does and
does not license.

### Python pipeline

See [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) §8 for setup,
authentication, and the command sequence. It needs a Google Earth Engine
service account and, for the Rockwell comparison arm, the published raster
(USGS ScienceBase, DOI [10.5066/P9BYV5H4](https://doi.org/10.5066/P9BYV5H4)).

---

## Repository layout

```
validation/      the log: dated reports, pre-registrations, STATE.md
python/          analysis pipeline (extraction, statistics, delineation)
earth-engine/    the interactive GEE tool
docs/            OPERATOR_GUIDE.md, plans, memory
data/            gitignored; regenerable from committed code
paper.pdf        the full 47-page USGS SIM 3466 pamphlet (method source)
paper2.pdf       Galaszkiewicz et al. 2024 (green:NIR — tested, failed here)
```

---

## How this project works

Four claims have been retracted after they failed a test this project ran on
itself. That is the method, not an accident:

- **Never judge a threshold by within-site performance.** Within-site AUCs of
  0.99 collapsed to 0.63–0.67 pooled; one index fell to 0.437, below chance.
- **Never put an absolute cutoff on a non-normalised index.** The same defect
  broke the water mask and the land thresholds.
- **Report the between/within variance split beside any pooled correlation.** A
  pooled sulfate result *reversed sign* (−0.563 → +0.220) once region effects
  were removed.
- **Never test a hypothesis on the data that generated it.**
- **A null or a collapse is a valid result** and is reported as prominently as
  a positive.

Every phase is pre-registered before its data exists, and the registration
commit is verifiable in git history.

---

## Citation

```bibtex
@software{hussein_amd_2026,
  author  = {Hussein, Abdulrahman},
  title   = {Acid Mine Drainage (AMD) and Coal Mine Drainage (CMD) Detection System},
  version = {3.10.0},
  year    = {2026},
  doi     = {10.5281/zenodo.19429983},
  url     = {https://github.com/abdulrahman-R-A-hussein/AMD-Detection-Tool}
}
```

Please also cite the source method: Rockwell, B.W., and Gnesda, W.R., 2021,
USGS Scientific Investigations Map 3466,
[doi:10.3133/sim3466](https://doi.org/10.3133/sim3466).

## License

MIT — see [LICENSE](LICENSE).
