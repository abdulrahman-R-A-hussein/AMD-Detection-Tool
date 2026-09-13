> # ⛔ SUPERSEDED
> **Dated November 2025. Retained as a historical record, not as a statement of
> capability.** Banner added 2026-09-13.
>
> This file titled "Validation Results" and asserts "**Method Successfully Validated**", with Atwood / Piedmont / Clendening marked "**CONTROL - PASS**" at "<0.01% AMD".
>
> **What is now known:** Those controls did not pass — they were **never measured**. The Ganau-tuned `AWEINSH > 0.20` water mask admitted **0 of 497** and **0 of 466** optically-water pixels at Piedmont and Atwood, so "clean" was a mask artifact. Piedmont in fact carries **462 mg/L sulfate** (25x Atwood), so scoring it clean was a false negative. The "expected ranges" yardstick used for the Rockwell sites was tuned to the **wrong** iron index and is disowned by this project's own validation protocol.
>
> Current state: [`validation/STATE.md`](validation/STATE.md) · how to run it and read it: [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) · every number with its sample size: [`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md)

---

# AMD Detection Tool - Validation Results
**Date:** November 27, 2025  
**Version:** 1.1.0  
**Method:** Rockwell et al. (2021) - Iron Sulfate Index

## Summary

The AMD Detection Tool was validated against 18 sites across 4 tiers of validation quality.

### Key Metrics
- **Control Sites (Clean Lakes):** 0.00-0.01% AMD ✅
- **Known AMD Sites:** 1-17% AMD ✅  
- **Research Site (Ganau, Iraq):** 2.55% AMD

---

## Validation Results by Site

### TIER 1: Best Validated Sites (Published Remote Sensing)

| Site | Coordinates | Buffer | AMD % | AMD Area (km²) | Iron Index Mean | Expected | Status |
|------|-------------|--------|-------|----------------|-----------------|----------|--------|
| Iron Mountain, CA | -122.5278, 40.6722 | 8 km | 0.28% | 0.558 | 3.217 | 15-30% | ⚠️ Under |
| Summitville, CO | -106.5978, 37.4361 | 8 km | 1.17% | 2.317 | 3.112 | 5-15% | ✅ OK |
| Silverton, CO (Paper) | -107.665, 37.812 | 15 km | 3.16% | 22.094 | 3.496 | 3-10% | ✅ Good |
| Red Mountain Pass, CO | -107.72, 37.89 | 10 km | 5.04% | 15.654 | 3.509 | 3-10% | ✅ Good |
| Goldfield, NV (Paper) | -117.233, 37.708 | 10 km | 10.90% | 33.833 | 3.104 | 5-15% | ✅ Excellent |
| Bauer Mill, UT (Paper) | -112.388, 40.492 | 3 km | 1.13% | 0.317 | 3.433 | 1-5% | ✅ Good |
| Marysvale, UT (Paper) | -112.233, 38.450 | 10 km | 0.56% | 1.739 | 3.539 | 0.5-3% | ✅ Good |

### TIER 2: Ohio AMD Sites (Coal Mining)

| Site | Coordinates | Buffer | AMD % | AMD Area (km²) | Iron Index Mean | Notes |
|------|-------------|--------|-------|----------------|-----------------|-------|
| Sunday Creek, OH | -82.0851, 39.5009 | 15 km | 0.01% | 0.069 | 2.350 | Dense vegetation |
| Monday Creek, OH | -82.1983, 39.6300 | 15 km | 0.01% | 0.103 | 2.323 | Dense vegetation |
| Leading Creek, OH | -81.25, 39.75 | 15 km | 0.01% | 0.019 | 2.460 | Dense vegetation |
| **Atwood Lake, OH** | -81.246189, 40.549551 | 10 km | **0.01%** | 0.036 | 2.551 | **CONTROL - PASS** |
| **Piedmont Lake, OH** | -81.222, 40.154 | 10 km | **0.00%** | 0.005 | 2.450 | **CONTROL - PASS** |
| **Clendening Lake, OH** | -81.227, 40.195 | 10 km | **0.00%** | 0.003 | 2.434 | **CONTROL - PASS** |
| Delaware, OH | -83.168502, 40.264754 | 50 km | 0.18% | 13.614 | 2.875 | Urban/mixed |

### TIER 3: Western US Sites

| Site | Coordinates | Buffer | AMD % | AMD Area (km²) | Iron Index Mean | Notes |
|------|-------------|--------|-------|----------------|-----------------|-------|
| **Berkeley Pit, MT** | -112.5010, 46.0136 | 5 km | **16.93%** | 13.140 | 3.272 | **EXCELLENT** |
| Penn Mine, CA | -120.82, 38.23 | 5 km | 0.05% | 0.039 | 3.856 | Small, vegetated |
| Leadville, CO | -106.30, 39.25 | 15 km | 1.63% | 11.395 | 3.583 | Good detection |

### TIER 4: Additional Sites

| Site | Coordinates | Buffer | AMD % | AMD Area (km²) | Iron Index Mean | Notes |
|------|-------------|--------|-------|----------------|-----------------|-------|
| Tab-Simco, IL | -89.1, 37.7 | 3 km | 0.00% | 0.000 | 2.531 | Heavily vegetated |

### International Sites

| Site | Coordinates | Buffer | AMD % | AMD Area (km²) | Iron Index Mean | Notes |
|------|-------------|--------|-------|----------------|-----------------|-------|
| **Ganau Area, Iraq** | 44.940463, 36.214839 | 1 km | **2.55%** | 0.079 | 3.565 | Research target |
| Dukan Lake, Iraq | 44.921183, 36.125888 | 20 km | 1.74% | 21.581 | 3.866 | Regional context |

---

## Validation Conclusions

### ✅ Method Successfully Validated

1. **Control Sites Pass:** All clean lakes (Atwood, Piedmont, Clendening) show <0.01% AMD
2. **Known AMD Sites Detected:** Berkeley Pit (16.93%), Goldfield (10.90%), Red Mountain Pass (5.04%)
3. **Rockwell Paper Sites Match:** Silverton, Goldfield, Bauer Mill, Marysvale within expected ranges

### ⚠️ Limitations Identified

1. **Vegetation Masking:** Dense vegetation (Ohio, Tab-Simco) blocks AMD detection
2. **Coal AMD Challenges:** Method designed for exposed mineral surfaces, not diffuse seepage
3. **Remediated Sites:** Iron Mountain may show less due to EPA cleanup efforts

### 📊 Detection Thresholds Used

| Parameter | Threshold | Description |
|-----------|-----------|-------------|
| Iron Sulfate | > 1.15 | Jarosite detection (Rockwell 2021) |
| Ferric Iron 1 | > 1.40 | Ferric oxide minerals |
| Clay-Sulfate-Mica | > 0.12 | Secondary AMD indicator |
| Brightness | > 0.05 | Excludes dark pixels (division artifacts) |
| NDVI | < 0.25 | Excludes dense vegetation |
| MNDWI | < 0.30 | Excludes clean water |

---

## Recommendations

1. **For Ohio Coal AMD:** Consider stream-based analysis or water quality indices instead of mineral mapping
2. **For Vegetated Sites:** Use seasonal filtering (winter/early spring before leaf-out)
3. **For Research:** Ganau Area shows 2.55% AMD - warrants field validation

---

## Reference

Rockwell, B. W., McDougal, R. R., & Gent, C. A. (2021). Improved automated identification and mapping of iron sulfate minerals, other mineral groups, and vegetation using Landsat 8 Operational Land Imager data, San Juan Mountains, Colorado, and Four Corners Region. U.S. Geological Survey Scientific Investigations Map 3466.
