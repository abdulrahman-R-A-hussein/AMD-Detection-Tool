> # ⛔ SUPERSEDED
> **Dated November 2025. Retained as a historical record, not as a statement of
> capability.** Banner added 2026-09-13.
>
> This file describes v2.x operation, including a "Validate on Known Sites" workflow and slider-tuning advice.
>
> **What is now known:** **Do not follow the tuning workflow.** Adjusting thresholds until known sites produce the expected answer is the circularity this project retracted (findings W1 and C3). It also documents the **wrong** iron index — `(B2+B4)/B1`, since corrected to `(B2/B1)-(B5/B4)` — and v2.x threshold defaults that measured worst-case Youden J 0.107 against the published map.
>
> Current state: [`validation/STATE.md`](validation/STATE.md) · how to run it and read it: [`docs/OPERATOR_GUIDE.md`](docs/OPERATOR_GUIDE.md) · every number with its sample size: [`validation/ACCURACY_ASSESSMENT.md`](validation/ACCURACY_ASSESSMENT.md)

---

# AMD Detection Tool - Usage & Validation Guide
**Version 1.1.0 - Streamlined Interface**

---

## 🎯 Quick Start (5 Steps)

### 1. **Open the Script in Google Earth Engine**
- Copy the code from `amd_detection_v1.0.0.js`
- Paste into GEE Code Editor
- Click **Run**

### 2. **The Interface Loads**
You'll see a panel on the right with:
- **Sensor selection** (Landsat 8/9, Sentinel-2)
- **Study area dropdown** (18 validation sites pre-loaded)
- **Land AMD sliders** (Iron, Ferric, Clay thresholds)
- **Water Quality module** (🌊 section with contamination thresholds)

### 3. **Two Main Layers Appear**
When you click Run, **2 layers turn ON automatically**:
1. **🏔️ Land AMD Classification** (19 classes - colored minerals on land)
2. **🌊 Water Quality Classification** (3 classes - blue/orange/red water)

**These are SEPARATE and independent!**

### 4. **Toggle Layers to Compare**
In the **Layers panel** (top-right of map), you'll see:
- ✅ 🏔️ Land AMD Classification (ON)
- ✅ 🌊 Water Quality Classification (ON)
- 📊 Water Score (0-7) (OFF - click to enable)
- 🔬 NIR Anomaly (OFF - diagnostic)
- 📷 True Color RGB (OFF - reference)
- 🔬 Iron Sulfate Index (OFF - diagnostic)

**Click the checkboxes to show/hide layers!**

### 5. **Validate on Known Sites**
Select different study areas from dropdown:
- **Atwood Lake, OH** → Should show clean water (blue)
- **Iron Mountain, CA** → Should show severe land AMD (red/magenta)
- **Berkeley Pit, MT** → Should show contaminated water (orange/red)

---

## 📊 Understanding the Layers

### 🏔️ **Land AMD Classification (19 Classes)**

**Purpose:** Detects exposed iron sulfate minerals on land surface

**Color Coding:**
| Color | Class | Meaning |
|-------|-------|---------|
| 🔴 Red | Major Iron Sulfate (12) | Jarosite dominant |
| 🔴 Crimson | Proximal Jarosite (17) | Near source |
| 🟣 Magenta | Major Ferric Iron (2) | Hematite/goethite |
| 🟠 Orange | Clay+Moderate Ferric (7) | Altered rock |
| 🟢 Green | Clay-Sulfate-Mica (5) | Altered minerals |
| 🟢 Forest | Dense Vegetation (11) | Not AMD |

**Controlled by:**
- Iron threshold slider (default: 1.15)
- Ferric 1 slider (default: 1.40)
- Clay slider (default: 0.12)
- "Exclude Water Bodies" checkbox

---

### 🌊 **Water Quality Classification (3 Classes)**

**Purpose:** Detects sulfate/iron contamination IN water bodies

**Color Coding:**
| Color | Class | Score Range | Interpretation |
|-------|-------|-------------|----------------|
| 🔵 Blue | Clean | 0-2 | Normal water |
| 🟠 Orange | Moderate | 3-4 | Some contamination |
| 🔴 Red | Severe | 5-7 | High AMD impact |

**Controlled by:**
- NIR Anomaly sliders (Moderate: 0.03, Severe: 0.08)
- Turbidity Ratio sliders (Moderate: 1.30, Severe: 2.00)
- Iron Water Index slider (0.15)
- Yellow Index slider (1.10)
- Score thresholds (Moderate: 3, Severe: 5)
- "Enable Water Quality Analysis" checkbox

**Key Difference from Land:**
- Uses **NIR reflectance** (not Iron Sulfate formula)
- Filters out **shallow water** (< 2m estimated depth)
- **Multi-criteria scoring** (0-7 points from 7 tests)
- Only appears ON WATER, not on land

---

## 🔬 Diagnostic Layers (Hidden by Default)

### Click to Enable These for Detailed Analysis:

**📊 Water Score (0-7)**
- Shows contamination score for each water pixel
- 0 = passes 0 tests (clean)
- 7 = fails all 7 tests (severe)
- Use to fine-tune thresholds

**🔬 NIR Anomaly (Water)**
- Gradient: dark blue (0%) to red (15%)
- Clean water: < 1% (dark blue)
- Contaminated: 3-10% (yellow/red)
- **Most diagnostic indicator!**

**🔬 Turbidity Ratio**
- Gradient: blue (0.5) to red (3.0)
- Shows suspended particle concentration
- Red/Blue band ratio

**🔬 Iron Sulfate Index**
- For land AMD only
- Gradient: cyan (1.15) to red (4.0)
- Shows (B2+B4)/B1 values

**📷 True Color (RGB)**
- Natural color satellite image
- Use to verify visual features

---

## ✅ How to Validate the Tool

### **Test 1: Clean Water Control**

**Site:** Atwood Lake, OH

**Steps:**
1. Select "Atwood Lake, OH" from study area dropdown
2. Wait for layers to load (~10 seconds)
3. Look at the water body

**Expected Result:**
- 🌊 Water Quality layer shows **BLUE** (clean)
- 🏔️ Land AMD layer shows minimal/no AMD (not in water)
- If you toggle 📊 Water Score, should see **0-2** scores

**If you see orange/red in water:**
- Thresholds too strict - increase NIR Anomaly, Turbidity sliders
- Or: shallow areas picking up bottom sediment - increase Shallow Water Cutoff

---

### **Test 2: Severe Land AMD**

**Site:** Iron Mountain, CA

**Steps:**
1. Select "Iron Mountain, CA" from dropdown
2. Zoom to the mountain area
3. Look at exposed rock surfaces

**Expected Result:**
- 🏔️ Land AMD layer shows **RED/CRIMSON/MAGENTA** (Classes 12, 17, 2)
- 🌊 Water Quality shows **ORANGE/RED** in downstream creeks
- Both layers show contamination, but separately!

**If you see no AMD:**
- Lower Iron threshold slider (try 1.0)
- Check if vegetation is masking (toggle False Color layer)

---

### **Test 3: Contaminated Water**

**Site:** Berkeley Pit, MT

**Steps:**
1. Select "Berkeley Pit, MT" from dropdown
2. Look at the large open pit lake

**Expected Result:**
- 🌊 Water Quality layer shows **RED** (severe contamination)
- 📊 Water Score shows **5-7** points
- 🔬 NIR Anomaly shows elevated reflectance (yellow/red)

**Ground truth:**
- pH = 2.5
- Sulfate = 4,000 mg/L
- Dissolved metals: Cu, Fe, Zn

**If water shows clean (blue):**
- Lower NIR Anomaly threshold (try 0.02 for Moderate)
- Lower Score Moderate threshold (try 2)

---

### **Test 4: Mixed Land + Water AMD**

**Site:** Ganau Area, Iraq

**Steps:**
1. Select "Ganau Area, Iraq" 
2. Look at both land and water features

**Expected Result:**
- 🏔️ Land shows yellow/orange alteration zones
- 🌊 Water shows orange contamination in some areas
- Can see AMD transition from source (land) to drainage (water)

---

## 🎛️ Slider Adjustment Guide

### **When to Adjust Land AMD Sliders:**

**Iron Slider (1.15 default)**
- **Increase (1.3-1.5):** Too many false positives, want high-confidence only
- **Decrease (0.9-1.0):** Missing AMD, want more sensitivity

**Ferric 1 Slider (1.40 default)**
- Controls red mineral detection (hematite, goethite)
- Adjust if seeing incorrect ferric classifications

**Clay Slider (0.12 default)**
- Controls alteration zone detection
- Lower = more sensitive to clay-sulfate-mica

---

### **When to Adjust Water Quality Sliders:**

**NIR Anomaly (Mod: 0.03, Sev: 0.08)**
- **Most important sliders!**
- Increase if clean lakes show as contaminated
- Decrease if missing known contamination

**Turbidity Ratio (Mod: 1.3, Sev: 2.0)**
- Increase if sediment plumes flagged as AMD
- Decrease if missing turbid AMD water

**Score Thresholds (Mod: 3, Sev: 5)**
- Mod threshold: How many tests must fail for "moderate" class?
- Increase for stricter classification
- Decrease for more sensitive detection

---

## 🐛 Troubleshooting

### **Issue: "All water shows as contaminated"**

**Causes:**
- Thresholds too low
- Shallow water included (seeing bottom)

**Fixes:**
1. Increase NIR Anomaly thresholds (try 0.05 / 0.10)
2. Increase Shallow Water Cutoff (try 1.5)
3. Increase Score Moderate threshold (try 4)

---

### **Issue: "Known contaminated water shows clean"**

**Causes:**
- Thresholds too high
- Water mask too strict (not detecting water)

**Fixes:**
1. Decrease NIR Anomaly Moderate (try 0.02)
2. Decrease Score Moderate threshold (try 2)
3. Toggle 🔬 MNDWI layer - verify water is being detected

---

### **Issue: "Can't see layers / nothing appears"**

**Causes:**
- Layers hidden
- No imagery for date range
- Cloud cover blocking view

**Fixes:**
1. Check **Layers panel** (top-right) - click checkboxes to enable
2. Change compositing method (try "quality" or "latest")
3. Adjust season filter (try "Summer Only")
4. Check console for image count - should be > 0

---

### **Issue: "Vegetation flagged as AMD"**

**Causes:**
- NDVI threshold too high

**Fixes:**
1. This shouldn't happen - vegetation is filtered in both methods
2. Toggle False Color (NIR-R-G) to verify it's actually vegetation
3. If genuine AMD under sparse vegetation, this is correct!

---

### **Issue: "Dark areas show false positives"**

**Causes:**
- Division artifact where B1 → 0

**Fixes:**
1. Already handled! Brightness filter (> 0.05) excludes these
2. If still seeing, check if Shadow areas - this is expected behavior

---

## 📈 Comparing Land vs Water Results

### **How to Compare Side-by-Side:**

1. **Method 1: Toggle Layers**
   - Turn ON both classifications
   - They overlay - land shows on land, water shows in water
   - No conflict because they're mutually exclusive!

2. **Method 2: Individual Toggle**
   - Turn OFF 🏔️ Land AMD
   - Turn ON 🌊 Water Quality
   - See only water contamination
   - Reverse to see only land

3. **Method 3: Use Diagnostic Layers**
   - Enable 📊 Water Score
   - Enable 🔬 Iron Sulfate Index
   - Compare values - are they correlated?

### **Expected Patterns:**

| Site Type | Land AMD | Water Quality |
|-----------|----------|---------------|
| **Source area** | High (red/magenta) | Variable (depends on flow) |
| **Downstream creek** | Low (background) | High (orange/red) |
| **Clean control** | None | Clean (blue) |
| **Abandoned mine** | High near waste piles | High in seepage |

---

## 🧪 Advanced: Exporting Results

### **Export Classification Raster:**

```javascript
// Add this after the script loads
var classification = createBooleanClassification();

Export.image.toDrive({
  image: classification,
  description: 'AMD_Land_Classification',
  region: settings.currentRegion,
  scale: 30,
  crs: 'EPSG:4326',
  maxPixels: 1e9
});
```

### **Export Water Quality:**

```javascript
var waterResult = createWaterQualityClassification();

Export.image.toDrive({
  image: waterResult.classification,
  description: 'Water_Quality_Classification',
  region: settings.currentRegion,
  scale: 30,
  crs: 'EPSG:4326',
  maxPixels: 1e9
});
```

---

## 📚 References & Literature

### **Land AMD Detection:**
- Rockwell et al. (2021) - Iron Sulfate Mineral Detection
- Zabcic et al. (2021) - Landsat AMD mapping

### **Water Quality Detection:**
- Doxaran et al. (2002) - Suspended particle detection
- Ritchie et al. (2003) - Turbidity monitoring
- Ravankhah et al. (2017) - AMD water detection (Iran)
- Wei et al. (2022) - Adaptive water quality classification

### **Spectral Libraries:**
- USGS Spectral Library v7 (jarosite, goethite, water)

---

## 🎯 Summary: Simplified Layer Structure

### **ALWAYS VISIBLE (Default ON):**
1. 🏔️ Land AMD Classification
2. 🌊 Water Quality Classification

### **FOR VALIDATION (Click to Enable):**
- 📊 Water Score (0-7)
- 🔬 NIR Anomaly
- 🔬 Turbidity Ratio
- 🔬 Iron Sulfate Index
- 🔬 MNDWI
- 📷 True Color RGB
- 📷 False Color NIR-R-G

### **CONTROLS:**
**Land AMD:**
- 3 sliders (Iron, Ferric, Clay)
- 1 checkbox (Exclude Water)
- 1 slider (Water threshold)

**Water Quality:**
- 1 checkbox (Enable module)
- 8 sliders (NIR, Turbidity, Iron Water, Yellow, Depth, Scores)

**Total: 13 controls** (was 20+ before cleanup)

---

## ✅ You're Ready!

Run the tool, test on the validation sites, and adjust sliders based on your results. The separate land/water classifications let you track AMD from **source (exposed minerals) → transport (contaminated streams) → impact (polluted lakes)**.

**Questions? Check console for debugging info!**
