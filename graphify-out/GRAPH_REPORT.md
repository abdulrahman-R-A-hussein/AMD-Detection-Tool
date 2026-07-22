# Graph Report - Sulfate-Methos  (2026-07-22)

## Corpus Check
- 30 files · ~170,204 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 799 nodes · 930 edges · 34 communities (32 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39b802b9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]

## God Nodes (most connected - your core abstractions)
1. `AMD Detection v1.0.0 Script` - 31 edges
2. `createBooleanClassification()` - 15 edges
3. `Image` - 14 edges
4. `Water Quality Contamination Detection Module` - 14 edges
5. `Changelog` - 13 edges
6. `[1.0.0] - 2024-11-15` - 13 edges
7. `Acid Mine Drainage (AMD) and Coal Mine Drainage (CMD) Detection System` - 13 edges
8. `createBooleanClassification()` - 12 edges
9. `Contributing to AMD Detection System` - 12 edges
10. `Project Overview: Acid Mine Drainage Detection System` - 12 edges

## Surprising Connections (you probably didn't know these)
- `AMD Detection Python Module` --semantically_similar_to--> `AMD Detection GEE Script`  [INFERRED] [semantically similar]
  python/amd_detection.py → earth-engine/amd_detection_v1.0.0.js
- `AMD Detection v1.0.0 Script` --references--> `Rockwell, McDougal & Gent 2021 (USGS SIM 3466)`  [EXTRACTED]
  earth-engine/amd_detection_v1.0.0.js → paper.pdf
- `v1.5.4 Audit Rationale` --references--> `AMD Detection v1.0.0 Script`  [EXTRACTED]
  specs/amd-v2/audit.md → earth-engine/amd_detection_v1.0.0.js
- `AMD Detection GEE Script` --references--> `Version 1.5.4`  [EXTRACTED]
  earth-engine/amd_detection_v1.0.0.js → CHANGELOG.md
- `AMD Detection GEE Script` --implements--> `Rockwell et al. (2021) USGS SIM 3466`  [EXTRACTED]
  earth-engine/amd_detection_v1.0.0.js → docs/METHODOLOGY.md

## Import Cycles
- None detected.

## Communities (34 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (42): AMD Detection v1.0.0 Script, v1.5.4 Audit Rationale, Threshold Derivation Script, addAccuracyLayers(), applyIndexClipping(), applyStdDevThresholding(), calculateAllIndices(), calculateStats() (+34 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (36): _auc(), _auc_label2(), closure(), component_spectrum(), convolve_splib07(), endmember_matrix(), group_of(), _kappa_label() (+28 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (41): 1. **Open the Script in Google Earth Engine**, 2. **The Interface Loads**, 3. **Two Main Layers Appear**, 4. **Toggle Layers to Compare**, 5. **Validate on Known Sites**, 🧪 Advanced: Exporting Results, **ALWAYS VISIBLE (Default ON):**, AMD Detection Tool - Usage & Validation Guide (+33 more)

### Community 3 - "Community 3"
Cohesion: 0.24
Nodes (13): analyze_index(), _auc_label(), main(), otsu_threshold(), print_results(), Honest threshold derivation for the AMD Detection Tool (v2) ====================, Two Gaussian populations with a known crossover; confirm the derived     thresho, ROC-AUC via the rank (Mann-Whitney U) identity. Assumes higher index =>     more (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (53): Geometry, Image, ImageCollection, Map, add_legend_to_map(), add_results_to_map(), add_water_legend_to_map(), analyze_region() (+45 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (40): 1. NIR Anomaly (MOST DIAGNOSTIC!), 1. Water Body Extraction, 2. Depth Filtering, 2. Turbidity Ratio, 3. Index Calculation, 3. Iron in Water Index, 4. Multi-Criteria Scoring, 4. Yellow Substance Index (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (35): 1. Professional Documentation Created, 2. Technical Documentation, 3. Code Updates, 4. Version Control & Organization, 5. Folder Structure Created, **CHANGELOG.md** - Complete Version History, **CITATION.cff** - Academic Citation Metadata, ✅ Cleaned & Professional: (+27 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (32): **1. GitHub Profile Setup**, **2. Google Scholar Profile**, **3. ORCID Profile**, Academic Identity Alignment Guide, **Author Name in Papers:**, 📈 **Benefits of This Strategy**, **BibTeX Format:**, 📄 **Citation Standards** (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (31): Addresses Critical Gap, Author, Core Implementation, Documentation, Executive Summary, For Collaborators, For Developers, For Researchers (+23 more)

### Community 9 - "Community 9"
Cohesion: 0.29
Nodes (7): AMD Detection GEE Script, AMD Detection Python Module, Water Quality Classification Module, Version 1.5.4, Rockwell et al. (2021) USGS SIM 3466, Water Quality Extension Methodology, AMD Detection UI Screenshot

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (24): addAccuracyLayers(), applyIndexClipping(), applyStdDevThresholding(), calculateStats(), createBooleanClassification(), createBuiltUpMask(), createComposite(), createContaminatedWaterMask() (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (29): [1.0.0] - 2024-11-15, Added, Changed, Classification Logic, Code Structure, Contributors, Core Features, Critical Fixes (+21 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (28): **1. Connect GitHub to Zenodo**, **2. Select Repository**, **3. Configure Metadata**, **4. Create DOI**, **5. Update Citation**, **Academic Metrics**, **Background**, **Creation Tools** (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (28): **After Cleanup:**, **Before Cleanup:**, **Deleted Redundant Controls:**, **DIAGNOSTIC LAYERS (Hidden - Click to Enable)**, 🔄 How the Separation Works, **I want to see...**, **Land AMD Detection:**, **Land AMD Section** (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (28): **1. Consistency**, **2. Scientific Accuracy**, **3. User Experience**, **4. Validation-Ready**, 🎯 Benefits of Unified Mask, 📊 Comparison Table, Critical Masking Logic Fix, 🔍 Decision Tree (After Fix) (+20 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (27): [0.9.0] - 2025-11-10, [1.5.0] - 2025-01-03, [1.5.1] - 2025-01-05, [1.5.2] - 2025-01-08, [1.5.3] - 2025-01-08, [1.5.4] - 2025-01-09, Added, Added (+19 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (25): ✅ Conclusion, ✅ Contradiction-Free Architecture, **Core Principle: Mutual Exclusivity**, 🎯 Detection Coverage (Everything Detected), **Diagnostic Layers Reveal Causes:**, 📊 Differentiation Matrix, Final Logic Verification: Zero Contradictions, 🚀 Final Verification (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (24): AMD Detection Tool - Python/Google Colab Edition, 📚 API Reference, Basic Analysis, 🎨 Classification Legend, 🤝 Contributing, Core Functions, Custom Coordinates, Custom Thresholds (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (23): Acid Mine Drainage (AMD) and Coal Mine Drainage (CMD) Detection System, 🙏 Acknowledgments, Advanced Remote Sensing for Environmental Monitoring, 🔗 Citation, 📧 Contact & Collaboration, 🤝 Contributing, 📈 Development Status, Google Earth Engine (Recommended) (+15 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (22): 🎓 **Affiliation Format**, Authorship & Citation Strategy, **Authorship: Sole Author (You)**, 📊 **Citation Examples**, 📞 **Communication Strategy**, 📋 **Decision Summary**, **EB-2 Immigration Benefits:**, ✅ **Final Checklist** (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (21): **1. Academic Credibility**, **1. Zenodo DOI Integration**, **2. Abstract Updated with Graduate Symposium Content**, **2. Research Visibility**, **3. ResearchGate Publication Added**, **3. Website Traffic Strategy**, **4. Email Removed to Drive Website Traffic**, **4. Professional Branding** (+13 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (20): Areas for Contribution, Code Contributions, Code of Conduct, Code Review Process, Code Style Guidelines, Commit Message Format, Community Support, Contributing to AMD Detection System (+12 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (20): 1. Update Personal Information, 2. GitHub Repository Setup, 3. Optional Enhancements, 4. Development Files Organization, 5. Python Code Review, 6. Social Media & Professional Network, 7. Academic Visibility, Code Quality (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (19): **1. AMD/CMD Terminology Update**, **2. CITATION.cff Configuration**, **3. EB-2 References Removed from Public Files**, **4. Academic Identity Standardization**, **Author Format:**, **Citation Date:**, ✅ **Completed Updates**, **Core Documentation:** (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (17): A1. The primary index is not the paper's index, A2. The classification chain is inverted, collapsing 6 classes into 1, A3. Non-iron classes overwrite iron-sulfate detections, A4. The control-site validation is circular, A. Blocking scientific defects, B. The Atwood problem was only half fixed, C1. Land surface reflectance is being used for aquatic targets, C2. No shoreline erosion (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (17): Clay-Sulfate-Mica Index, Contamination Scoring System, Core Spectral Indices, Ferric Iron Indices, Iron Sulfate Index, Known Limitations, Landsat 8/9 OLI Processing, Masking Strategy (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (15): AMD Detection Tool - Validation Results, 📊 Detection Thresholds Used, International Sites, Key Metrics, ⚠️ Limitations Identified, ✅ Method Successfully Validated, Recommendations, Reference (+7 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (14): **After DOI Created:**, **Content Should Include:**, **Design Tips:**, 🔍 **How to Test Your Social Preview**, **Method 1: GitHub Social Preview Checker**, **Method 2: LinkedIn Card Validator**, **Method 3: Twitter Card Validator**, **Method 4: Facebook Debugger** (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (11): Author Information Update Summary, ✅ Completed Updates, **Core Files:**, 📊 CV Integration, **Expertise Areas Highlighted:**, 📋 Files Updated, **Name Updates:**, 🎯 Professional Branding Consistency (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (7): 1. Guiding hypotheses (the science backbone your supervisor will ask for), 2. The VPCA validation you asked for — exactly what it is and how it runs, 3. Code upgrades (each ties to an audit item), 4. Deriving thresholds honestly (replaces the circular validation), 5. Deliverables, 6. Sequence, AMD Detection v2.0 — Upgrade & Validation Plan

### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (7): 0. One-time setup, AMD Detection v2 — Validation Protocol, Test A — Paper fidelity (H1), Test B — VPCA spectral-library closure (H2, H4), Test C — Honest threshold derivation (§4), Test D — Water Fe³⁺ ground-truth regression (H3), What each deliverable does (for the write-up)

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (5): How to add a run, Interpretation, Results, Still to do, Validation Log — AMD Detection v2

## Knowledge Gaps
- **439 isolated node(s):** `Task`, `Planned`, `Fixed`, `Changed`, `Fixed` (+434 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AMD Detection v1.0.0 Script` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `[1.0.0] - 2024-11-15` connect `Community 13` to `Community 17`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Why does `Changelog` connect `Community 17` to `Community 13`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `Task`, `AMD Detection Tool - Python Module for Google Earth Engine ====================`, `Initialize Google Earth Engine with authentication.          Parameters     -` to the rest of the system?**
  _486 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10631229235880399 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0915915915915916 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._