> # ⛔ SUPERSEDED
> **Dated November 2025. Retained as a historical record, not as a statement of
> capability.** Banner added 2026-09-13.
>
> This file documents the in-water contamination-scoring module and its physical mechanism, including "NIR Anomaly (MOST DIAGNOSTIC!)" and a "Validation Against Known Sites" table.
>
> **What is now known:** **The entire in-water module is retracted.** Every ratio index ranked the *clean* control highest. The Ohio water column is a measured null (no feature's 95% CI excludes zero for iron or sulfate); what the water arm actually detects is **turbidity**. The "Validation Against Known Sites" table lists *expected* results, not measured ones.
>
> Current state: [`validation/STATE.md`](validation/STATE.md) · how to run it and read it: [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) · every number with its sample size: [`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md)

---

# Water Quality Contamination Detection Module
**Separate from Land AMD Detection**

## Overview

This module provides advanced spectral analysis for detecting sulfate/iron contamination in water bodies. It uses a multi-criteria scoring system based on peer-reviewed remote sensing literature.

---

## Key Concepts

### Why Water is Different from Land

**Clean Water Physics:**
- **NIR (Near-Infrared):** < 1% reflectance - water molecules absorb NIR strongly
- **Blue:** Highest reflectance (2-5%) - lowest absorption
- **SWIR:** ~0% reflectance - water is opaque

**Contaminated Water:**
- **Suspended iron particles (jarosite, goethite)** scatter NIR → increases to 3-15%
- **Dissolved Fe³⁺** creates yellow-orange color → increases red/green ratio
- **Turbidity** from AMD precipitates → increases red/blue ratio

---

## Spectral Indices Explained

### 1. NIR Anomaly (MOST DIAGNOSTIC!)

**What it measures:** Absolute NIR reflectance (Band 5)

**Why it works:** Clean water acts as a "black body" in NIR due to H₂O absorption. When iron sulfate minerals precipitate in water, particles scatter NIR light.

| Value | Interpretation |
|-------|---------------|
| < 0.01 (1%) | Clean deep water |
| 0.03-0.08 (3-8%) | Moderate contamination (suspended particles) |
| > 0.08 (8%) | Severe contamination |

**Slider:** NIR Anomaly (Mod/Sev)

---

### 2. Turbidity Ratio

**Formula:** Red / Blue (B4 / B2)

**Why it works:** 
- Red penetrates turbid water better than blue
- Blue is absorbed by suspended particles
- Ratio increases with particle concentration

| Value | Interpretation |
|-------|---------------|
| 0.6-1.0 | Clean water |
| 1.3-2.0 | Moderate turbidity (AMD precipitates) |
| > 2.0 | Severe turbidity |

**Slider:** Turbidity Ratio (Mod/Sev)

---

### 3. Iron in Water Index

**Formula:** (Red/Blue) - (NIR/Red)

**Why it works:** Combines two effects:
1. Red/Blue increase = Fe³⁺ coloration
2. NIR/Red increase = particle scattering

| Value | Interpretation |
|-------|---------------|
| -0.5 to 0.0 | Clean water |
| 0.15-0.50 | Moderate Fe contamination |
| > 0.50 | Severe Fe contamination |

**Slider:** Iron Water Index (Mod)

---

### 4. Yellow Substance Index

**Formula:** Green / Blue (B3 / B2)

**Why it works:** Dissolved/colloidal iron (Fe³⁺) shifts spectral peak toward yellow-green wavelengths.

| Value | Interpretation |
|-------|---------------|
| 0.9-1.05 | Clean water |
| 1.10-1.25 | Moderate Fe³⁺ (dissolved iron) |
| > 1.25 | High Fe³⁺ concentration |

**Slider:** Yellow Index (Mod)

---

### 5. Water Depth Proxy

**Formula:** ln(Blue) / ln(Green)

**Why it works:** Blue penetrates deeper than green. Ratio decreases with depth.

| Value | Interpretation |
|-------|---------------|
| 1.0-1.1 | Deep water (> 5m) |
| 1.2-1.5 | Shallow water (1-3m) |
| > 1.5 | Very shallow (< 1m) - bottom contamination |

**Slider:** Shallow Water Cutoff (masks out pixels > threshold to avoid bottom reflectance)

---

## Multi-Criteria Contamination Score (0-7 Scale)

### How Scoring Works

Each water pixel receives **1 point** for each criterion met:

1. ✅ NIR Anomaly > Moderate threshold (+1 point)
2. ✅ NIR Anomaly > Severe threshold (+1 additional point)
3. ✅ Turbidity Ratio > Moderate (+1)
4. ✅ Turbidity Ratio > Severe (+1)
5. ✅ Iron Water Index > Moderate (+1)
6. ✅ Yellow Index > Moderate (+1)
7. ✅ NDWI < Clean threshold (degraded water quality) (+1)

**Maximum score:** 7 points (extremely contaminated)

### Classification Thresholds

| Score | Classification | Interpretation |
|-------|---------------|----------------|
| 0-2 | **Clean Water** (Blue) | Meets < 3 criteria, likely clean |
| 3-4 | **Moderate Contamination** (Orange) | Multiple indices elevated |
| 5-7 | **Severe Contamination** (Red) | Most/all criteria exceeded |

**Sliders:** 
- Score Mod Threshold (default: 3)
- Score Sev Threshold (default: 5)

---

## Visualization Layers

### Water Quality Classification
3-class map: Blue (clean), Orange (moderate), Red (severe)

### Individual Index Layers (Gradient)
- **NIR Anomaly (Water):** 0-15%, dark blue to red
- **Turbidity Ratio (Water):** 0.5-3.0, blue to red
- **Iron in Water Index:** -0.5 to 1.0, blue to red
- **Contamination Score (0-7):** Blue to dark red (8-color palette)

All layers are **masked to water only** (not shown on land).

---

## Workflow

### 1. Water Body Extraction
- Uses NDWI > 0.0 AND mNDWI > 0.2 AND NIR < 0.15
- Isolates water pixels from land

### 2. Depth Filtering
- Removes shallow water (< 2m estimated depth)
- Prevents bottom sediment/vegetation contamination
- Uses ln(Blue)/ln(Green) ratio

### 3. Index Calculation
- Computes all 6 contamination indices
- Only on deep water pixels

### 4. Multi-Criteria Scoring
- Evaluates each pixel against 7 criteria
- Sums score (0-7)

### 5. Classification
- Score 0-2 = Clean
- Score 3-4 = Moderate
- Score 5-7 = Severe

---

## Recommended Defaults

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| NIR Anomaly (Mod) | 0.03 | 0.01-0.10 | 3% = moderate suspended particles |
| NIR Anomaly (Sev) | 0.08 | 0.05-0.15 | 8% = severe contamination |
| Turbidity Ratio (Mod) | 1.30 | 1.0-2.0 | Moderate turbidity start |
| Turbidity Ratio (Sev) | 2.00 | 1.5-3.0 | High turbidity |
| Iron Water Index (Mod) | 0.15 | 0.05-0.50 | Fe contamination threshold |
| Yellow Index (Mod) | 1.10 | 1.0-1.5 | Dissolved Fe³⁺ threshold |
| Shallow Water Cutoff | 1.30 | 1.0-2.0 | Exclude shallow < 2m |
| Score Mod Threshold | 3 | 2-5 | Need 3+ criteria |
| Score Sev Threshold | 5 | 4-7 | Need 5+ criteria |

---

## Validation Against Known Sites

### Expected Results:

| Site | Expected Water Quality | Why |
|------|----------------------|-----|
| Atwood Lake, OH | Clean (score 0-2) | Control - clean reservoir |
| Berkeley Pit, MT | Severe (score 6-7) | pH 2.5, 4000 mg/L sulfate |
| Ganau Pond, Iraq | Moderate-Severe (score 3-6) | Known AMD impact |
| Sunday Creek, OH | Moderate (score 3-4) | Coal AMD seepage |

---

## How to Use

### Test on Known Clean Water:
1. Select **Atwood Lake, OH** 
2. Enable **Water Quality Classification** layer
3. **Expected:** Blue (clean) throughout lake
4. **If not:** Adjust thresholds upward (more strict)

### Test on Known Contaminated Water:
1. Select **Berkeley Pit, MT** or **Ganau Area, Iraq**
2. Enable **Water Quality Classification** layer
3. **Expected:** Orange/Red in pit water
4. **Toggle individual index layers** to see which indices are elevated

### Fine-Tune Thresholds:
1. Enable **Contamination Score (0-7)** layer
2. Click on water pixels to see exact scores
3. Adjust slider thresholds to match known ground truth

---

## References

### Spectral Library:
- USGS Spectral Library Version 7 (water, jarosite, goethite spectra)
- Rockwell et al. (2021) - Iron sulfate mineral detection

### Water Optics:
- McFeeters (1996) - NDWI for water extraction
- Feyisa et al. (2014) - AWEInsh index
- Ritchie et al. (2003) - Turbidity detection

### AMD in Water:
- Doxaran et al. (2002) - Suspended particle detection
- Ravankhah et al. (2017) - AMD water detection Iran
- Wei et al. (2022) - Adaptive water quality classification
- Minerals 2021 - UAS hyperspectral AMD monitoring

---

## Advantages Over Simple Iron Sulfate Index

| Feature | Iron Sulfate (Land) | Water Quality Module |
|---------|---------------------|---------------------|
| **Target** | Exposed minerals on land | Contamination in water |
| **Method** | (B2+B4)/B1 threshold | Multi-criteria scoring |
| **Criteria** | 1 index | 7 criteria |
| **Classes** | Binary (AMD/not) | 3 classes (clean/mod/sev) |
| **Depth correction** | No | Yes (removes shallow water) |
| **Sensitivity** | Fixed threshold | Adaptive scoring system |
| **False positives** | Vegetation, shadows | Excluded by water mask |

---

## Troubleshooting

### "All water shows as contaminated"
- **Cause:** Thresholds too low, or shallow water included
- **Fix:** Increase threshold values, increase Shallow Water Cutoff

### "Known contaminated water shows as clean"
- **Cause:** Thresholds too high, or water mask too strict
- **Fix:** Lower threshold values, check NDWI/mNDWI are detecting water

### "Red pixels in very deep/dark water"
- **Cause:** Division artifact (B1 → 0 in dark areas)
- **Fix:** This module uses NIR, not B1 division - should not occur

### "Bottom vegetation/sediment flagged as contaminated"
- **Cause:** Shallow water not filtered
- **Fix:** Increase Shallow Water Cutoff threshold

---

## Next Steps for Research

1. **Validate against in-situ measurements:**
   - Compare contamination scores to measured SO₄²⁻, Fe, pH
   - Build correlation curves

2. **Adaptive thresholding:**
   - Use Otsu's method for automatic threshold selection
   - Implement split-based approach (SBA) for spatial variation

3. **Machine learning:**
   - Train Random Forest on labeled data (clean/contaminated sites)
   - Achieve 85-95% accuracy (reported in literature)

4. **Time series analysis:**
   - Track water quality changes over time
   - Detect AMD plume movement, seasonal variation

---

**This module is completely separate from the land-based AMD detection - use both together for comprehensive AMD assessment!**
