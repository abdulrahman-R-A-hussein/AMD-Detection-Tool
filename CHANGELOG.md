# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Note on everything below v3.0.0
Entries for v1.x record what was believed at the time. Several are
**retracted** — in particular every "Ganau Lake validated" / "675 mg/L" /
"correctly displays contamination" entry, and the `AWEINSH > 0.20` water-mask
"fix". See the v3.x entries and [`validation/STATE.md`](validation/STATE.md).

## [3.10.0] - 2026-09-13
### Changed
- Corrected the externally-facing record. `CITATION.cff`, `README.md`,
  `PROJECT_OVERVIEW.md` rewritten; nine historical documents bannered as
  superseded; `earth-engine/validation_results.md` renamed, because its
  filename asserted a validation it does not contain.
- Author name unified to **Abdulrahman Hussein** (six occurrences of a
  different name in `PUBLIC_RELEASE_SUMMARY.md`).
### Added
- `validation/ACCURACY_ASSESSMENT.md` — every performance number with its
  sample size and, critically, *which reference standard* it was measured
  against.

## [3.10.0-cmd3] - 2026-09-09
### Added
- **CMD3, Pennsylvania replication.** Pre-registered before any PA data was
  fetched. Three spatially disjoint tiles, 274 sulfate-matched stations.
### Findings
- **FAILS TO REPLICATE** on the falsifier named in advance. The **sign**
  replicates (conductance −0.187, n=443, p=0.0002, **first sign-consistent
  CMD result**); the **scale** does not — PA is monotone *declining* and dead
  at 1 km (+0.003), the opposite of Ohio's U-shape.
- CMD2's landscape-scale reading is therefore **bounded to Ohio**.
- **Radius shape fails as a mechanism diagnostic** — it returns opposite
  mechanisms for the same drainage type.

## [3.9.0] - 2026-09-08
### Findings
- **CMD2: the mining-extent confound is REAL** — mine extent predicts sulfate
  (+0.519) and vegetation (−0.283), carrying ~42% of the raw covariance.
- Primary partial test **PARTIAL by 0.004** (−0.246 vs a pre-registered bar of
  0.25). The bar was fixed in advance and was not moved.
- **The near-channel reading of CMD1 is REFUTED.** |rho| peaks at 1 km. The
  UAV argument drawn from the CMD1 geometry gradient is **withdrawn** — the
  second UAV argument withdrawn in this project.

## [3.1.0] - 2026-09-09 (Earth Engine tool)
### Added
- **Free-form AOI** (latitude / longitude / radius) alongside the 30 presets —
  the tool can now be pointed anywhere on Earth without editing source.
### Fixed
- Adaptive-threshold checkbox rendered `false` while the setting was `true`,
  so the tool booted in one mode while the UI claimed the other.
- σ multiplier sliders started at 2.0/1.5 against calibrated 0.5/0.25 with a
  slider **minimum of 1.0** — any drag silently applied a configuration
  measured at worst-case Youden J **0.000**. Now staged behind an Apply
  button, with the two missing controls added.
- Date filter defaulted to 2024, outside the 2013–2020 collection window, so
  enabling it returned zero images.
- **The AOI extent was a classification parameter.** σ statistics now come
  from a fixed 12 km circle on the AOI centre (inside the 8–15 km calibration
  band) rather than the display AOI, so the same pixel no longer changes class
  when a larger circle is drawn.

## [3.0.0 - 3.8.0] - 2026-07 to 2026-08
### Findings (see validation/ for each, with sample sizes)
- **Land replica verified**: all six SIM 3466 index formulas reproduce exactly.
- **Three of our own "improvements" were regressions.** Fixing them took
  worst-case leave-one-site-out Youden J **0.107 → 0.440**.
- **Detection is a measured NULL** at 86 chemically confirmed source points:
  nine indices, three control tiers, best case J 0.234 vs a bar of 0.25.
- **Severity ranking is a ground-truth-validated positive**, bounded: rho
  **+0.568** vs dissolved Fe (n=75, p=0.0004), but negative leave-one-region-out
  R² for every pair → ranks within a district, does not predict across.
- **Resolution is NOT the binding constraint** in 10–100 m — refuted. The
  Landsat→Sentinel-2 gain was a *sensor* effect.
- **Catchment delineation rebuilt** on MERIT Hydro D8: 6/6 within ±33% of
  published USGS areas, versus 2/6 for the previous approach.
### Retracted
- The entire in-water contamination-scoring module (findings W1–W4).
- "Our map predicts dissolved Fe better than Rockwell's" — collapsed at n=31.
- "Our tool is more sensitive than Rockwell's" — the direction of disagreement
  reverses between sites.
- The Ganau Pond and Muskingum Watershed validation claims.


### Planned
- Python workflow automation with batch processing
- Temporal trend analysis for contamination monitoring
- Web application interface
- Machine learning classification enhancement
- Mobile field validation app

---

## [1.5.4] - 2025-01-09

### Fixed
- **Water quality layer wet soil misclassification**: Raised AWEINSH threshold from 0.0 to 0.20
  - Real water bodies (depth) have AWEINSH > 0.20-0.30
  - Wet bare soil (surface moisture) has AWEINSH < 0.20
  - Validated: Ganau Lake water=0.249, wet soil=0.18-0.19
  - Removed NIR threshold approach (unreliable for contaminated water with suspended particles)

### Changed
- Optimized unified water mask for better land/water separation
- Enhanced discrimination between irrigated agriculture and water bodies

---

## [1.5.3] - 2025-01-08

### Fixed
- Initial attempt at wet soil exclusion using NIR < 5% threshold
- Identified limitation: Contaminated water can have elevated NIR (4-5%) overlapping with wet soil

### Notes
- Version superseded by v1.5.4 with superior AWEINSH-based approach

---

## [1.5.2] - 2025-01-08

### Fixed
- **Critical water quality layer blank issue**: Water bodies showing no color in Water Quality Classification
  - Root cause: `.selfMask()` in `createBooleanClassification()` masked all water pixels (value 0)
  - Mask propagated through `isLandAMD.not()` causing entire water quality layer to be masked
  - Solution: Added `.unmask(0)` before land AMD overlap exclusion check
  - Validated: Ganau Lake (675 mg/L sulfate) now correctly displays contamination

### Added
- Comprehensive masking logic documentation

---

## [1.5.1] - 2025-01-05

### Changed
- Removed water classification classes (20, 21) from land AMD module to prevent overlap
- Water quality now exclusively handled by dedicated Water Quality Classification module
- Updated legend to direct users to Water Quality layer

---

## [1.5.0] - 2025-01-03

### Added
- **Water Quality Classification Module**: Novel 3-class system for contaminated water detection
  - Clean water (blue), Moderate contamination (orange), Severe contamination (red)
  - Multi-criteria contamination scoring (0-7 points)
  - Spectral indices: NIR anomaly, turbidity, iron water index, yellow index
- **Unified Water Mask**: Multi-criteria approach (MNDWI, AWEINSH, brightness, NDVI, NDWI)
- **Depth filtering**: Excludes shallow water to improve accuracy
- **Land/Water separation**: Explicit mutual exclusivity between modules

### Research Innovation
- First implementation extending USGS terrestrial mineral detection to water quality assessment
- Validated against ground truth measurements (Ganau Lake: 675 mg/L sulfate)

---

## [1.0.0] - 2024-11-15

### Added

#### Core Features
- Multi-sensor support:
  - Landsat 8 Collection 2 Level-2
  - Landsat 9 Collection 2 Level-2
  - Sentinel-2 L2A (harmonized)
- Spectral indices calculation:
  - Iron Sulfate Mineral Index (B2/B1 - B5/B4)
  - Ferric Iron 1 "Redness Index" (B4/B2)
  - Ferric Iron 2 (B4/B2 × (B4+B6)/B5)
  - Ferrous Iron (B3+B6)/(B4+B5)
  - Clay-Sulfate-Mica Index (B6/B7 - B5/B4)
  - Green Vegetation Index (B5/B4)
  - NDVI, NDWI, MNDWI, AWEInsh

- Boolean Classification System:
  - 19 material classes
  - Priority-based classification logic
  - Contaminated water detection
  - Extreme AMD override logic

- Water Detection & Masking:
  - Multi-index approach (MNDWI + AWEInsh)
  - Contaminated water identification
  - Clean water masking

- User Interface:
  - Interactive map visualization
  - Real-time threshold adjustment (sliders)
  - Study area selector (8 sites)
  - Sensor selector (3 options)
  - Statistics panel with diagnostics
  - Complete 19-class legend
  - Accuracy verification tools

- Study Areas (8 total):
  - **Original:** Piedmont Lake OH, Clendening Lake OH, Genau Iraq, Delaware OH
  - **Paper Validation:** Goldfield NV, Bauer Mill UT, Silverton CO, Marysvale UT

- Documentation:
  - README.md with project overview
  - PROJECT_PLAN.md with development roadmap
  - GITHUB_SETUP.md with Git workflow
  - SCALING_FIX.md with technical details
  - IMPLEMENTATION_GUIDE.md with step-by-step instructions
  - CHANGELOG.md (this file)

### Fixed

#### Critical Fixes
- **Negative Reflectance Values:** Added `.clamp(0.0, 1.0)` to ensure valid reflectance range
  - Issue: Landsat Collection 2 scaling formula produced negative values for low-signal pixels
  - Solution: Clip all reflectance values to physically valid range [0.0, 1.0]
  - Impact: Iron Sulfate Index now shows positive values (0.5-2.5 range)

#### Landsat Scaling
- Corrected Landsat Collection 2 Level-2 Surface Reflectance formula
  - Formula: Reflectance = (DN × 0.0000275) - 0.2
  - Applied clipping after scaling to prevent negatives
  - Verified against USGS official documentation

#### Water Masking
- Improved water detection with dual-index approach
- Fixed false positives in water classification
- Enhanced contaminated water detection logic

### Changed

#### Code Structure
- Reorganized processing functions for clarity
- Added comprehensive comments explaining methodology
- Improved error handling and diagnostics

#### Documentation
- Enhanced code comments with band descriptions
- Added threshold explanations
- Included paper references (Rockwell et al. 2021)

#### User Experience
- Improved statistics panel formatting
- Better legend organization (6 AMD classes + 11 other classes)
- More informative console output

### Removed
- Removed commented-out alternative scaling methods
- Removed redundant masking logic

### Technical Details

#### Landsat Collection 2 Processing
```javascript
// Scaling formula (official USGS)
var scaled = bands.multiply(0.0000275).add(-0.2);

// Clipping to valid range
var clipped = scaled.clamp(0.0, 1.0);
```

#### Sentinel-2 Processing
```javascript
// Scaling with clipping
var scaled = image.select(['B1', 'B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
  .multiply(0.0001)
  .clamp(0.0, 1.0)
  .rename(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']);
```

#### Classification Logic
- 19 classes with priority-based assignment
- Water masking applied before classification
- Extreme AMD (Iron > 2.0) overrides water mask
- Contaminated water detection (Iron > 1.8 in water)

### Testing

#### Validation
- ✅ Statistics show positive Iron Sulfate Index (0.5-2.5 range)
- ✅ Band reflectances in valid range (0.0-0.4)
- ✅ All 19 classes visualize correctly
- ✅ Paper validation sites ready for comparison

#### Paper Validation Sites
- Goldfield, NV: Expected Iron Sulfate 1.2-1.8
- Bauer Mill, UT: Expected Iron Sulfate 0.9-1.4
- Silverton, CO: Expected Iron Sulfate 1.1-1.6
- Marysvale, UT: Expected Iron Sulfate 0.8-1.3

### Performance

#### Processing Time
- Image loading: 5-10 seconds
- Index calculation: 2-3 seconds
- Classification: 2-3 seconds
- Statistics computation: 5-10 seconds
- **Total:** 15-30 seconds per study area

#### Memory Usage
- Typical scene: ~500MB
- Composite (median): ~200MB
- Classification layer: ~50MB

### Known Issues

None currently identified. All critical issues resolved.

### Dependencies

#### Google Earth Engine
- LANDSAT/LC08/C02/T1_L2
- LANDSAT/LC09/C02/T1_L2
- COPERNICUS/S2_SR_HARMONIZED

#### External Libraries
- None (pure GEE JavaScript)

### Migration Guide

No migration needed for v1.0.0 (initial release).

### Contributors

- Development & Testing: [Your Name]
- Methodology: Rockwell et al. (2021) USGS SIM 3466
- Validation: Kent State University

### References

Rockwell, B. W., McDougal, R. R., & Gent, C. A. (2021). Improved automated identification and mapping of iron sulfate minerals, other mineral groups, and vegetation using Landsat 8 Operational Land Imager data, San Juan Mountains, Colorado, and Four Corners Region. U.S. Geological Survey Scientific Investigations Map 3466.

---

## [0.9.0] - 2025-11-10

### Added
- Initial project structure
- Core algorithm skeleton
- Basic documentation

### Status
- Pre-release development version
- Not recommended for production use

---

## Version History Summary

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | 2025-11-15 | Production | Initial release with all core features |
| 0.9.0 | 2025-11-10 | Pre-release | Development version |

---

## Future Versions

### v1.1.0 (Planned)
- Performance optimization
- Additional study areas
- Enhanced documentation
- User feedback integration

### v2.0.0 (Planned)
- Python module implementation
- Google Colab notebook
- Batch processing
- API interface

### v3.0.0 (Planned)
- Web application
- User authentication
- Result export/sharing
- Advanced analytics

---

## How to Report Issues

1. Check existing issues on GitHub
2. Create new issue with:
   - Clear title
   - Detailed description
   - Steps to reproduce
   - Expected vs. actual behavior
   - Screenshots/logs if applicable

## How to Contribute

See GITHUB_SETUP.md for contribution workflow.

---

**Last Updated:** 2025-01-09  
**Maintained By:** Abdulrahman Hussein  
**Affiliation:** Kent State University, Environmental Remote Sensing Laboratory  
**Supervisor:** Dr. Joseph D. Ortiz  
**License:** MIT  
**Website:** www.climtawy.com  
**ORCID:** 0009-0003-0401-9219
