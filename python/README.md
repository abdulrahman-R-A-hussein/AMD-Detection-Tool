> # ⚠️ This file is v1.5.1-era and partly stale
>
> **Banner added 2026-09-13.** Its spectral-index table has been corrected
> (it previously gave wrong formulas), but the rest describes an early state of
> the Python package. For current usage see
> [`../docs/OPERATOR_GUIDE.md`](../docs/OPERATOR_GUIDE.md); for current state
> see [`../validation/STATE.md`](../validation/STATE.md).

# AMD Detection Tool - Python/Google Colab Edition

**Version:** 1.5.1  
**Based on:** Rockwell et al. (2021) USGS methodology

Detect **Acid Mine Drainage (AMD)** and **iron sulfate minerals** using satellite imagery from Landsat 8 and Sentinel-2.

---

## 🚀 Quick Start (Google Colab)

1. **Open in Colab:** Upload `AMD_Detection_Tool.ipynb` to Google Colab
2. **Run the first cells:** The notebook will automatically download `amd_detection.py` from GitHub if it is not already present
3. **Run cells:** Follow the step-by-step instructions in the notebook

Alternative (clone the repo in Colab):

```python
!git clone https://github.com/coodawy/AMD-Detection-Tool.git
import sys
sys.path.insert(0, '/content/AMD-Detection-Tool/python')
import amd_detection as amd
```

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

---

## 📦 Installation

### Option A: Google Colab (Recommended)
```python
# In a Colab cell:
!pip install earthengine-api geemap folium --quiet
```

### Option B: Local Jupyter
```bash
pip install -r requirements.txt
```

---

## 🔧 Usage

### Basic Analysis
```python
import amd_detection as amd

# Initialize Google Earth Engine
amd.initialize_gee()

# Define study area
geometry = amd.get_study_area("Iron Mountain, CA")

# Run analysis
results = amd.analyze_region(
    geometry=geometry,
    start_date="2023-06-01",
    end_date="2023-09-30",
    sensor="Landsat 8"
)

# View results on map
Map = amd.create_map()
Map = amd.add_results_to_map(Map, results)
Map
```

### Custom Coordinates
```python
import ee

# Define custom point with buffer
latitude = 40.6722
longitude = -122.5278
buffer_meters = 12000

geometry = ee.Geometry.Point([longitude, latitude]).buffer(buffer_meters)

results = amd.analyze_region(geometry, "2023-06-01", "2023-09-30")
```

### Custom Thresholds
```python
# Modify detection sensitivity
custom_settings = amd.DEFAULT_SETTINGS.copy()
custom_settings["iron_sulfate_threshold"] = 1.10  # More sensitive
custom_settings["ndvi_max"] = 0.20  # Stricter vegetation mask

results = amd.analyze_region(
    geometry=geometry,
    start_date="2023-06-01",
    end_date="2023-09-30",
    settings=custom_settings
)
```

---

## 📍 Pre-defined Study Areas

| Name | Location | Description |
|------|----------|-------------|
| Iron Mountain, CA | USA | Historic copper/zinc mine with extreme AMD |
| Summitville, CO | USA | Gold mine with cyanide heap leach legacy |
| Silverton, CO | USA | Historic mining district |
| Red Mountain Pass, CO | USA | Natural iron oxide deposits |
| Goldfield, NV | USA | Historic gold mining district |
| Rio Tinto, Spain | Spain | Ancient mining region with red river |
| Atwood Lake, OH | USA | Coal mining region |

---

## 🎨 Classification Legend

### Iron Sulfate Minerals (AMD Indicators)
| Class | Name | Risk Level |
|-------|------|------------|
| 9 | Argillic Alteration | EXTREME |
| 17 | Proximal Jarosite | HIGH |
| 12 | Major Iron Sulfate | HIGH |
| 18 | Distal Jarosite | MODERATE |
| 19 | Clay + Ferrous + Iron | MODERATE |
| 14 | Oxidizing Sulfides | HIGH |

### Water Quality Scores
| Score | Category | Description |
|-------|----------|-------------|
| 0 | Clean | No contamination detected |
| 1-2 | Moderate | Some contamination indicators |
| 3-4 | Severe | Multiple contamination indicators |
| 5+ | Extreme | Strong contamination signal |

---

## 📚 API Reference

### Core Functions

| Function | Description |
|----------|-------------|
| `initialize_gee()` | Initialize Google Earth Engine |
| `analyze_region()` | Run complete AMD analysis |
| `create_map()` | Create interactive map |
| `add_results_to_map()` | Add analysis results to map |
| `export_to_drive()` | Export results to Google Drive |

### Utility Functions

| Function | Description |
|----------|-------------|
| `get_study_area()` | Get pre-defined study area |
| `print_class_legend()` | Print classification legend |
| `print_version()` | Print version info |

---

## 🔬 Scientific Background

This tool implements the methodology from:

> **Rockwell, B.W., 2021**, Mapping acid-generating minerals, acidic drainage, iron sulfate minerals, and other mineral groups using Landsat 8 Operational Land Imager data, San Juan Mountains, Colorado, and Four Corners Region. *U.S. Geological Survey Scientific Investigations Map 3466*.

### Spectral Indices Used

> **Corrected 2026-09-13.** The formulas previously listed here were wrong
> — `Iron Sulfate = B4/B2`, `Ferric Iron 1 = B4/B3`,
> `Clay = (B6-B7)/(B6+B7)`. Anyone calibrating against that table was
> debugging a fiction. The values below are the SIM 3466 formulas as verified
> against the published pamphlet and as implemented in
> [`gee_classify.py`](gee_classify.py).

| Index | Formula (Landsat 8 SR bands) | Purpose |
|-------|------------------------------|---------|
| Iron Sulfate | `(B2/B1) - (B5/B4)` | jarosite / iron sulfate; **signed**, roughly -3..+2 |
| Ferric Iron 1 | `B4/B2` | redness — hematite / goethite |
| Ferric Iron 2 | `(B4/B2) * ((B4+B6)/B5)` | oxidised iron |
| Ferrous Iron | `(B3+B6)/(B4+B5)` | reduced iron |
| Clay-Sulfate-Mica | `(B6/B7) - (B5/B4)` | clay minerals |
| Green Vegetation | `B5/B4` | vegetation gate |

**Note:** `Ferric Iron 1` (`B4/B2`) and the water-arm `Turbidity` index are
the *same expression* — they read one physical quantity under two names, and
cannot separate iron from turbidity.

---

## 🛠️ Troubleshooting

### GEE Authentication Failed
```python
# Try manual authentication
import ee
ee.Authenticate()
ee.Initialize()
```

### No Data Found
- Check date range (summer months work best)
- Reduce cloud cover threshold
- Verify geometry coordinates

### Results Look Wrong
- Compare with true color imagery
- Check classification legend
- Try adjusting thresholds

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.
