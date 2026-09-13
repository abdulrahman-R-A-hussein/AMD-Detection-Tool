> # ⚠️ CLAIM RULES FOR ANYTHING POSTED FROM THIS FILE
>
> **Added 2026-09-13.** Two templates in this guide previously asserted
> *"validated against ground truth measurements (675 mg/L sulfate detection)"*.
> That claim is **retracted** — it was circular, the thresholds having been
> tuned until that site scored contaminated. **The templates have been
> rewritten.** If either was already posted, the post carries a retracted
> claim.
>
> Before posting anything about this project:
>
> - **Never** claim optical **sulfate** detection. Sulfate has no VNIR
>   absorption. Any apparent signal is iron, turbidity, or colour that
>   co-varies with sulfate.
> - **Never** claim scene-wide **detection** of mine drainage. It is a measured
>   null: nine indices, three control tiers, n=86 confirmed source points.
> - **Never** claim a cost-saving percentage. No analysis supports one.
> - Agreement with Rockwell's published map is **replica fidelity, not
>   accuracy.**
> - What may be claimed: severity *ranking within a mineral district*
>   (rho +0.568 vs measured dissolved iron, n=75), and a faithful replica of a
>   published USGS method.
>
> Full boundaries: [`docs/OPERATOR_GUIDE.md`](OPERATOR_GUIDE.md) section 6.

# Social Media & DOI Registration Guide

## 🎨 GitHub Social Preview Image (1280x640px)

### **Design Specifications**
- **Dimensions**: 1280x640 pixels (GitHub's recommended size)
- **Format**: PNG or JPG
- **File location**: Repository root as `social-preview.png` or `preview.png`

### **Design Elements**

#### **Background**
- Satellite imagery showing contamination detection
- Map visualization with colored AMD detection areas
- Clean, professional scientific aesthetic

#### **Text Content**
```
AMD Detection System
Advanced Remote Sensing for Environmental Monitoring

Abdulrahman R. A. Hussein
Kent State University
www.climtawy.com

Open Source • MIT License
```

#### **Visual Elements**
- Color-coded contamination map (blue/orange/red water quality)
- Spectral index visualization
- Earth Engine/Google Cloud logo
- Kent State University branding (optional)

#### **Typography**
- Clean, modern sans-serif font
- High contrast for readability
- Professional scientific appearance

### **Creation Tools**
- **Canva**: Free online design tool with GitHub preview template
- **Figma**: Professional design tool
- **Photoshop**: Advanced image editing
- **PowerPoint**: Simple option for quick creation

### **Implementation**
1. Create image in recommended tool
2. Save as `social-preview.png` in repository root
3. GitHub will automatically detect and use it
4. Test by sharing repository link on social media

---

## 📚 DOI Registration with Zenodo

### **Why Register DOI?**
- Permanent academic citation
- Required for many journal publications
- Tracks citations and usage metrics
- Professional credibility for EB-2 application

### **Registration Steps**

#### **1. Connect GitHub to Zenodo**
- Visit [zenodo.org](https://zenodo.org)
- Sign in with GitHub account
- Authorize Zenodo access
- Enable "GitHub integration"

#### **2. Select Repository**
- Navigate to GitHub settings
- Select "coodawy/AMD-Detection-Tool"
- Enable DOI generation

#### **3. Configure Metadata**
- **Title**: "Acid Mine Drainage Detection System: Advanced Remote Sensing for Environmental Monitoring"
- **Authors**: Abdulrahman Rabie Ahmed Hussein
- **Affiliation**: Kent State University, Department of Earth Sciences
- **Description**: Copy from README.md abstract
- **Keywords**: acid mine drainage, remote sensing, water quality, Google Earth Engine
- **License**: MIT
- **Version**: 1.5.4

#### **4. Create DOI**
- Trigger new release on GitHub
- Zenodo automatically generates DOI
- DOI format: `10.5281/zenodo.XXXXXX`
- Update CITATION.cff with actual DOI

#### **5. Update Citation**
Replace placeholder in README.md:
```bibtex
@software{hussein2025amd,
  author = {Hussein, Abdulrahman R. A.},
  title = {Acid Mine Drainage Detection System: Advanced Remote Sensing for Environmental Monitoring},
  year = {2025},
  version = {1.5.4},
  url = {https://github.com/coodawy/AMD-Detection-Tool},
  doi = {10.5281/zenodo.XXXXXX},  # Update with actual DOI
  note = {Based on Rockwell et al. (2021) USGS SIM 3466}
}
```

---

## 📱 Social Media Strategy

### **LinkedIn Post Template**
```
🌍 Excited to share my open-source #AcidMineDrainage Detection System!

An open reimplementation of USGS SIM 3466 (Rockwell & Gnesda 2021) for mapping iron-sulfate minerals from Landsat, with a pre-registered assessment of where it works and where it does not. Severity ranking validated against measured USGS/EPA iron chemistry; scene-wide detection is a measured null and reported as one.

🔬 Key Features:
• 19-class land mineral classification
• 3-class water quality assessment  
• Multi-sensor support (Landsat 8/9, Sentinel-2)
• Open-source MIT license

📊 Impact: Addresses 19,000+ km of AMD-impacted waterways in the US alone, with global applicability for environmental justice and water quality monitoring.

🔗 GitHub: https://github.com/coodawy/AMD-Detection-Tool
🌐 Website: www.climtawy.com
📧 ORCID: 0009-0003-0401-9219

#RemoteSensing #WaterQuality #EnvironmentalScience #OpenScience #Geospatial #EarthEngine
```

### **Twitter/X Post Template**
```
🚀 Just published my open-source Acid Mine Drainage Detection System!

Open reimplementation of USGS SIM 3466 for iron-sulfate mapping, plus a pre-registered measurement of its limits. Nulls reported as prominently as positives.

🔗 https://github.com/coodawy/AMD-Detection-Tool

#RemoteSensing #WaterQuality #OpenScience #EnvironmentalMonitoring
```

### **ResearchGate Update**
- Share project link
- Highlight novel methodology extension
- Mention validation results
- Invite collaboration

---

## 📊 Tracking Metrics for EB-2 Application

### **GitHub Metrics**
- **Stars**: Repository popularity indicator
- **Forks**: Community adoption measure
- **Issues/Discussions**: Community engagement
- **Pull Requests**: Collaboration evidence

### **Academic Metrics**
- **DOI Citations**: Academic impact
- **Google Scholar**: Track mentions
- **ResearchGate Views**: Professional engagement
- **LinkedIn Engagement**: Network reach

### **Social Media Metrics**
- **Post Views**: Reach measurement
- **Shares/Retweets**: Content virality
- **Comments**: Community interest
- **Profile Visits**: Professional curiosity

### **Documentation for EB-2**
- Screenshot of GitHub stats (stars, forks)
- DOI registration confirmation
- Social media engagement screenshots
- Collaboration requests received
- Citation tracking from Google Scholar

---

## 🔗 Quick Links

- **GitHub Repository**: https://github.com/coodawy/AMD-Detection-Tool
- **LinkedIn**: https://linkedin.com/in/climatawy
- **ResearchGate**: https://researchgate.net/profile/Abdulrahman-Hussein-5
- **ORCID**: https://orcid.org/0009-0003-0401-9219
- **Website**: https://www.climtawy.com
- **Zenodo**: https://zenodo.org

---

*This guide helps maximize project visibility and track impact metrics for professional documentation.*
