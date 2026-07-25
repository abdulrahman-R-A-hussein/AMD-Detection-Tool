# Methodology

## Scientific Foundation

This detection system implements and extends the USGS iron sulfate mineral detection methodology published by Rockwell et al. (2021) in Scientific Investigations Map 3466.

### Core Spectral Indices

#### Iron Sulfate Index
```
IS = (B2/B1) - (B5/B4)
```
Detects jarosite and other iron sulfate minerals. Threshold >1.15 indicates presence.

**Physical basis:** Jarosite exhibits strong absorption in blue wavelengths (B1) relative to green (B2), combined with iron's NIR absorption characteristics.

#### Ferric Iron Indices

**Ferric Iron 1:**
```
F1 = B4/B2
```
Threshold: >1.40

**Ferric Iron 2:**
```
F2 = (B4/B2) × (B4+B6)/B5
```
Threshold: >2.50

Detects ferric iron minerals (goethite, hematite) based on red/blue ratio enhanced by SWIR response.

#### Clay-Sulfate-Mica Index
```
CSM = (B6/B7) - (B5/B4)
```
Threshold: >0.12

Identifies clay minerals, alunite, and muscovite through SWIR absorption features.

### Water Quality Extension

This research extends terrestrial mineral detection to aquatic environments through novel multi-criteria scoring.

#### Water Identification

**Unified Water Mask:**
```
Water = MNDWI > 0.3
    AND AWEINSH > 0.20
    AND Brightness < 0.30
    AND NDVI < 0.2
    AND NDWI > -0.1
```

**⚠️ Known defect (2026-07-25):** the `AWEINSH > 0.20` cut was tuned on Ganau
Pond and does **not** generalize. AWEInsh is an absolute-magnitude index, so
the threshold scales with scene brightness: dark temperate reservoir water
(Piedmont and Atwood, median AWEINSH ≈ 0.07) fails it entirely, yielding zero
analysable water pixels and a false "clean" reading. Under repair — see
`validation/README.md` (Test D retraction).

#### Contamination Scoring System

7-point scoring system combining multiple spectral indicators:

**Score Components:**
1. **Iron Sulfate Index** (0-2 points)
   - >threshold in valid brightness range: +2 points
   
2. **NIR Anomaly** (0-2 points)
   - >0.03: +1 point (moderate)
   - >0.08: +1 additional point (severe)
   
3. **Turbidity Ratio** (0-2 points)
   - >1.3: +1 point (moderate)
   - >2.0: +1 additional point (severe)
   
4. **Iron Water Index** (0-1 point)
   - >0.15: +1 point
   
5. **Yellow Index** (0-1 point)
   - >1.10: +1 point
   
6. **NDWI** (0-1 point)
   - <0.5: +1 point (reduced water content)

**Classification:**
- Score 0-2: Clean water (blue)
- Score 3-4: Moderate contamination (orange)
- Score 5-7: Severe contamination (red)

### Validation Strategy

**Ground Truth:**
- Ganau Lake, Iraq: 675 mg/L sulfate. ⚠️ This is a **tuning anchor, not a
  validation**: the contamination thresholds were adjusted until Ganau scored
  severe, so "correctly classified as severe" is circular. Note also that
  SO₄²⁻ has **no VNIR absorption** — sulfate itself is optically invisible.
  What the scoring can detect is dissolved/colloidal iron, turbidity and
  colour that co-vary with sulfate at this site.
- USGS reference sites: Colorado, Nevada, Utah validation

**Spectral Validation:**
- Threshold optimization based on known contaminated vs. clean sites
- Cross-sensor consistency (Landsat 8/9, Sentinel-2)

## Multi-Sensor Integration

### Landsat 8/9 OLI Processing
```
Reflectance = (DN × 0.0000275) - 0.2
Clipped to [0.0, 1.0]
```

### Sentinel-2 MSI Processing
```
Reflectance = DN / 10000
Clipped to [0.0, 1.0]
```

Cloud masking uses QA_PIXEL band (Landsat) or Cloud Score+ (Sentinel-2 hybrid mode).

## Quality Assurance

### Masking Strategy
1. **Mutual exclusivity:** Land AMD and water quality modules cannot overlap
2. **Depth filtering:** Shallow water (<1.3 depth proxy) excluded to reduce false positives
3. **Vegetation exclusion:** Green/Red ratio >1.0 masked from mineral detection
4. **Road detection bypass:** Strong iron signal (>2.5) overrides road masking

### Known Limitations
- Contaminated water with high suspended particles may have elevated NIR (addressed in v1.5.4)
- Sensor-specific calibration may vary slightly between Landsat and Sentinel-2
- Cloud shadow can reduce apparent reflectance
- Shallow or narrow streams may fall below pixel resolution

## References

Rockwell, B. W., McDougal, R. R., & Gent, C. A. (2021). Improved automated identification and mapping of iron sulfate minerals, other mineral groups, and vegetation using Landsat 8 Operational Land Imager data, San Juan Mountains, Colorado, and Four Corners Region. U.S. Geological Survey Scientific Investigations Map 3466. https://doi.org/10.3133/sim3466
