# Audit, 2026-09-19 — the shipped Earth Engine tool presented a retracted capability by default

**What prompted it:** the author asked whether the Earth Engine code had been
updated for testing. It had not been touched since 2026-09-09, so its defaults
were read against the current claim record.

**This is a presentation defect, not a new measurement.** No number in any
report changes. What changes is what the tool asserts to the person using it.

---

## The finding

**The retracted in-water module shipped switched ON.** Opening
`earth-engine/amd_detection_v2.4.0.js` (v3.1.0) in the Code Editor produced:

| what the user saw | where |
|---|---|
| a **"🌊 Water Quality Classification"** layer drawn over every water body, visible on load, reading **clean / moderate / severe** | `Map.addLayer(..., true)` |
| a ticked checkbox, **"Enable Water Quality Analysis"** | `enableWaterQualityModule: true` |
| help text: *"Separate module - detects sulfate/iron contamination in water bodies"* | control panel |
| a legend line: *"💡 Water contamination: See 🌊 Water Quality Classification layer"* | legend |
| a file header claiming the tool *"Extends USGS terrestrial mineral detection methodology to contaminated water bodies quality assessment"* | lines 19–20 |

**Why that is wrong, from this project's own measurements:**
- **Finding W1:** the in-water indices ranked a chemically **clean control lake
  highest**. The whole module is retracted.
- **Water Phase 2, B1:** in 83 matched station-dates, **no** reflectance
  feature's confidence interval excluded zero against iron (n=17) or sulfate
  (n=23). **Turbidity was detectable** at n=50, which is what those bands
  actually see.
- **Sulfate has no VNIR absorption** at any concentration.

**A second, smaller defect:** the internal-validation printout computed
"Contaminated" and "Clean" water percentages from **land classes 20 and 21**.
Those classes were removed in v2.4.0, so it printed **0.00% every time** while
implying the tool had measured water.

**Severity:** the tool is the artefact a reviewer or a GSA audience is most
likely to open. Every other externally-facing document was corrected on
2026-09-13; the tool's own defaults were missed then.

## What changed (tool v3.1.1)

1. **`enableWaterQualityModule: false`** — the module is off on load.
2. The layer is **hidden** and renamed **"🌊 Water index levels (RETRACTED -
   not validated)"**; its palette comment now reads low / mid / high index,
   not clean / moderate / severe.
3. The checkbox reads **"Water Quality Analysis (RETRACTED - experimental)"**,
   its help text states the retraction, and **ticking it prints the reason** in
   the Console.
4. The legend says in-water contamination **is not a product of this tool**.
5. The dead classes 20/21 printout is replaced by a statement that the land
   raster does not classify water.
6. The header describes the tool as iron-sulfate **mineral mapping**, with the
   retraction stated.
7. The absolute-threshold panel line now reads "Iron-index cut over water
   (RETRACTED module)" instead of "Contaminated H2O".

**The land classification is untouched.** No index, threshold, σ rule or class
cascade was modified: `git diff` touches only defaults, labels and comments.

## Verification

- **Syntax:** the file parses (`new Function(source)` in a browser, 160,713
  bytes, no error). There is no JavaScript runtime on this machine, so this is
  a parse check, not an execution test.
- **Defaults, read back from the file:** `TOOL_VERSION` v3.1.1;
  `enableWaterQualityModule` false; checkbox value false; water layer
  `addLayer(..., false)`.
- **No user-visible string still says "Contaminated"** except comments
  explaining the change.
- **Not verified here:** an actual run in the Code Editor. Earth Engine's UI
  cannot be driven from this machine. **The author's own paste-and-run is the
  check** — `docs/HOW_TO_TEST.md` §A.

## Caveat

This audit corrects what the tool **says**. It does not add evidence about what
the tool **can do**. The in-water module remains retracted; leaving it in the
code, off and labelled, is a deliberate choice so that past diagnostic work
stays reproducible.
