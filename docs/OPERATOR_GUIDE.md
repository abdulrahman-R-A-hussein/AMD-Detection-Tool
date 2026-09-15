# Operator guide — AMD/CMD detection tool

**Applies to:** `earth-engine/amd_detection_v2.4.0.js` at **v3.1.0** (the
filename still says 2.4.0; the contents do not — see `validation/STATE.md`) and
the `python/` pipeline as of 2026-09-13.

> **Supersedes** `earth-engine/USAGE_GUIDE.md`, `earth-engine/LAYER_STRUCTURE.md`
> and `earth-engine/FINAL_LOGIC_VERIFICATION.md`. Those are dated Nov 2025 and
> describe v2.x behaviour — different thresholds, different default season, a
> class-12 fallback that no longer exists, and water classes 20/21 that were
> removed. Do not follow them.

There are **two surfaces** and they answer different questions.

| | Earth Engine tool | Python pipeline |
|---|---|---|
| **Question** | "what does this ground look like?" | "does the signal track measured chemistry?" |
| **Coverage** | anywhere on Earth | US only (needs Water Quality Portal chemistry) |
| **Needs chemistry** | no | yes |
| **Output** | a map you read | numbers with n, p and a caveat |
| **Validated?** | only in the terrain listed below | yes, within stated bounds |

---

## 0. Setup — from nothing to a first result

**Added 2026-09-13.** This guide previously explained how to *read* the output
but never how to get to it, and its section 8 told readers to run an
interpreter path that exists only on the author's machine.

### Earth Engine tool — about 10 minutes, nothing to install

1. Sign in at [code.earthengine.google.com](https://code.earthengine.google.com)
   and register a Google Cloud project for Earth Engine. Noncommercial research
   use is available. The Code Editor's project selector supplies the project;
   the script does not name one.
2. New script → paste
   [`earth-engine/amd_detection_v2.4.0.js`](../earth-engine/amd_detection_v2.4.0.js)
   → **Run**.
3. **Nothing else.** Every collection it reads is public — Landsat 8/9
   Collection 2 Level 2, Sentinel-2 SR Harmonized, Cloud Score+. No assets, no
   permissions to request.
4. *Optional:* the **Export Threshold CSV** button needs two drawn geometry
   layers named `amdPolygons` and `cleanPolygons`. If they are missing it prints
   instructions rather than failing. Nothing else uses them.

> **Sentinel-2 quietly shortens the record.** The collection window is
> 2013–2020, but Sentinel-2 surface reflectance begins in 2017, so selecting it
> analyses roughly 2017–2020 — a different basis from the Landsat presets.

### Python pipeline

1. **Python 3.11.**
2. **One virtual environment, in the repository:**

   ```bash
   python -m venv .venv
   ```

   Activate it — PowerShell `.venv/Scripts/Activate.ps1`, bash
   `source .venv/bin/activate` — then:

   ```bash
   pip install -r python/requirements.txt
   pip install -e .
   ```

   The second line installs **`amdtool`**, the importable package the
   validated pipeline now lives in (`src/amdtool`, added 2026-09-14). Every
   `python/*.py` command below keeps working without it; it is what lets
   another program — SpectraLab's *AMD severity report* — call the same code.
   Check it with `python -m pytest tests/` (tests that need the gitignored
   `data/` skip when it is absent).

3. **Earth Engine credentials — choose one.** Resolution lives in one place,
   [`python/ee_auth.py`](../python/ee_auth.py).

   | option | do this | when |
   |---|---|---|
   | **A. personal account** | `earthengine authenticate`, then set `GEE_PROJECT` to your Cloud project id | simplest; most people |
   | **B. service account** | set `GEE_SERVICE_ACCOUNT_KEY` to the JSON key path. The service account must *also* be registered for Earth Engine — a separate step from creating it | unattended runs |

   Check it before anything else:

   ```bash
   python python/ee_auth.py
   ```

   It prints `Earth Engine initialised OK`, or says exactly what is missing.

4. **Smoke tests:**

   | command | needs | expect |
   |---|---|---|
   | `python python/classify_v240.py` | nothing — runs from a bare clone | a self-test pass against the committed Silverton pixel export |
   | `python python/catchment_dem.py --self-test` | Earth Engine | `6/6 within +/-33%` and `PASS` |

5. **Data.** `data/` is gitignored and regenerable from committed code.
   Chemistry needs only a network connection. **Rockwell's raster** is needed
   only for the Rockwell-comparison arm:
   - download from USGS ScienceBase, DOI
     [10.5066/P9BYV5H4](https://doi.org/10.5066/P9BYV5H4) — a zip of about
     **309 MB**;
   - extract so this exact path exists, with its `.ige` (**~4.7 GB**) and
     `.rrd` (**~1.6 GB**) sidecars beside it — **~6.3 GB** in total:

     ```
     data/rockwell/L8_US_Southwest/SouthWest/l8_aa13_southwest_mosaic11.img
     ```

     Four modules hard-code that path.

6. **A first real result**, roughly 10–15 minutes:

   ```bash
   python python/fetch_wqp.py --region "Monday Creek, OH"
   python python/cmd_detect.py --extract --season leafoff --radii 30,60,100 \
       --bands NDVI_stress --regions monday_creek_oh --out data/matched/cmd_first.csv
   python python/cmd_detect.py --analyse --inputs data/matched/cmd_first.csv
   ```

   Observed run times: a chemistry fetch takes **2–8 minutes** per region; an
   extraction pass **1–5 minutes** per region, and up to ~19 minutes for a
   large one.

7. **Expect alarming-looking retry lines.** `memory limit - retrying at batch=N`
   is normal Earth Engine behaviour, handled automatically. If a region still
   fails, see *The GEE memory trap* in section 8 **before** changing anything —
   two of the four ways to make it fit silently change the numbers.

---

## 1. Pointing it at an area

### Earth Engine

Two ways, and exactly one AOI is active at a time — the **Study Area** dropdown
always shows which.

- **Presets** — 30 entries in the dropdown. Selecting one fills the custom
  boxes beneath it, so the two controls can never disagree.
- **Custom AOI** — type latitude, longitude and radius in km, press
  **Set Custom AOI**. "Fill lat/lon from map centre" fills the centre only.

Rejected input is refused with a reason and nothing changes. The radius floor is
0.3 km (below that the statistics reducer has fewer than ~30 pixels); the
ceiling is 200 km.

> **The radius does not mean what you might assume — read §5 before trusting a
> classification at an unusual extent.**

### Python

```bash
python python/fetch_wqp.py --region "West Branch Susquehanna, PA" \
    --bbox "40.6,-78.6,41.4,-77.2"
python python/fetch_wqp.py --list-regions
```

`--bbox` registers the region in `data/regions.json` and fetches it. Every
consumer (`seep_detect`, `cmd_detect`, `watershed_nap`) resolves through that
overlay, so no source edit is needed. The 12 **curated** regions stay
authoritative — an overlay entry can never shadow one.

---

## 2. What each layer shows

15 layers. Only the first two are on by default.

### Visible by default

| Layer | What it is | How to read it |
|---|---|---|
| 🏔️ **Land AMD Classification** | 19-class integer raster | The main product. Class table in §3. Transparent = unclassified, **not** "clean". |
| 🌊 **Water Quality Classification** | 4 states over water | Blue 0 = clean · Orange 1 = moderate · Red 2 = severe · **Grey 3 = INDETERMINATE** |

> **Grey is not clean.** Class 3 means the water was too dark or too bright for
> the ratio indices to be reliable (`brightness` outside 0.05–0.20), so it was
> **not measured**. Pooling grey with blue is the single easiest way to
> manufacture a false negative. The legend does not currently show grey — a
> known gap, listed in §7.

### Water diagnostics (hidden)

| Layer | What it is | Caveat |
|---|---|---|
| 📊 Water Score (0–9) | the contamination score before thresholding | Six criteria; see §4. The palette has 8 colours over a 0–9 range, so adjacent scores can share a colour. |
| 🔬 NIR Anomaly (Water) | raw SR_B5 over water | High NIR over water means particles — sediment *or* iron floc. Not diagnostic alone. |
| 🔬 Turbidity Ratio | B4/B2 over water | **Numerically identical to `FerricIron1`.** The same quantity under two names — it cannot separate turbidity from iron. |

### Reference and land diagnostics (hidden)

| Layer | What it is |
|---|---|
| 📷 True Color / False Color | visual reference |
| 🔬 Iron Sulfate Index | `(B2/B1) − (B5/B4)`, masked to valid land |
| 🔬 Ferric Iron Index | raw `FerricIron1` = B4/B2, **unmasked** |
| 🔬 MNDWI (Water) | raw water index |
| Iron / Ferric / Clay Masks | only when Accuracy Tools is on |

> **The accuracy-mask overlays always use the ABSOLUTE thresholds**, even when
> the map is in adaptive mode (the default). They will not match the
> classification. Same for the statistics panel and the click inspector — §7.

---

## 3. The class table

**The cascade is first-match-wins, and its order is not numeric order.** A pixel
matching several definitions gets the one tested first.

### The six AMD classes — these are the product

Tested first, in this order. **Every one requires clay**, mirroring Rockwell
Table 4.

| Order | Class | Name | NAP rank |
|---|---|---|---|
| 1 | **9** | Argillic Alteration | 5 |
| 2 | **17** | Proximal Jarosite | 3 |
| 3 | **12** | Major Iron Sulfate | 2 |
| 4 | **18** | Distal Jarosite | 4 |
| 5 | **19** | Clay + Ferrous + Iron | 6 |
| 6 | **14** | Oxidizing Sulfides | **1** |

**NAP = net acid production, verified from SIM 3466 Table 4. Rank 1 is the
worst.** So class 14 produces the most acid, then 12, 17, 18, 9, 19.

Class 9 differs from 17 *only* by a brightness test, and 9 is tested first — so
17 catches the otherwise-identical bright pixels.

### Non-AMD classes

8, 7, 5, 2, 3, 1, 4 (clay/ferric/ferrous combinations), 13 (sparse veg + ferric),
11 (dense vegetation).

**Classes 6 and 10 are unreachable** — earlier branches in the cascade dominate
them. **15 and 16 do not exist.** **20 and 21 were removed**; water no longer
appears in the land raster at all.

---

## 4. The water score

Six criteria, max 9 points, each gated on the brightness reliability window:

| Criterion | Points |
|---|---|
| Iron Sulfate index over water | +2 |
| NIR anomaly (moderate, then severe) | +1, +1 |
| Turbidity ratio (moderate, then severe) | +1, +1 |
| Iron Water Index | +1 |
| Yellow Index | +1 |
| NDWI degradation | +1 |

Score ≥ 3 → moderate; ≥ 5 → severe. Failing the reliability gate → **grey 3**,
never blue 0.

---

## 5. The one thing that will mislead you: AOI extent

In adaptive mode — **the default, and the calibrated one** — the cutoff for each
index is `mean + k × σ` computed over a region. That makes the region a
**classification parameter**.

**v3.1.0 fixed the worst of this.** Statistics are now computed over a **fixed
12 km circle on the AOI centre**, not over the display AOI, so the same
coordinates give the same map regardless of the radius you type. The calibration
band is **8–15 km** (Summitville 8, Red Mountain Pass 10, Silverton 15), so 12 km
reproduces the geometry the fit was measured on.

**What still needs your judgement:** if you map a 100 km AOI, the threshold is
sampled from 12 km and applied across all of it. The AOI status label tells you
when the mapped extent exceeds the statistics sample, and the σ cutoff panel
shows the exact `mean`, `sd`, `k` and resulting cut in force.

**To check this yourself:** run one centre at 8, 12 and 20 km. The printed cut
must be **identical**. (Set `settings.statsRadiusMode = 'matchAOI'` and it will
move — that is the old behaviour, kept only for reproducing pre-v3.1.0 figures.)

### The σ multipliers

Calibrated: **iron 0.50, clay 0.25, ferric 0.50, ferrous 0.50** — worst-case
leave-one-site-out Youden J **0.440** against Rockwell's map over three sites.

They sit behind **Advanced: override**, and changes are **staged** — a slider
drag shows a warning and changes nothing until you press Apply. This is
deliberate: the v2.x values of 2.0/1.5 measure **worst-case J = 0.000**, and
before v3.1.0 a single drag applied them silently.

Two of the four were never fitted (ferric and ferrous are set equal to iron), and
clay is provisional (per-fold fits −0.5, −0.5, +1.0). Treat classes 1–8 — which
these drive — as unvalidated.

---

## 6. What you may and may not conclude

Verbatim from `validation/DECISION_LOG.md`. **These are not stylistic
preferences; each was learned by getting it wrong.**

### MAY claim

- Faithful SIM 3466 replica (index level, exact).
- Our three departures were regressions; fixing them improved worst-case
  cross-site J **4.1×**.
- Continuous `FerricIron1` separates AMD-affected from **chemically-verified
  clean** water at **monitored locations**, out-of-region across 4 Colorado
  districts, with a score **monotone in measured contamination**.
- Continuous scoring separates mine discharge from bare ground (**J +0.617**)
  where the binarised classifier cannot (**0.000**).
- In Ohio coal watersheds a **vegetation** index tracks measured sulfate at
  **landscape scale**, and the mining-extent confound is **real** (mine extent →
  sulfate **+0.519**, → `NDVI_stress` **−0.283**) and carries ~42% of it.

### MAY NOT claim

- Finding unknown sources in **blind scene-wide search** — untested. Every
  validated result scored a *known* monitoring station.
- **Optical sulfate detection at any concentration.** Sulfate has no VNIR
  absorption. Ever. Any apparent signal is iron, turbidity, or colour that
  co-varies with sulfate — word it that way.
- That **resolution is the constraint** — refuted for 10–100 m in Colorado. The
  Sentinel-2 gain was a *sensor* effect.
- That the method works for **neutral-pH coal drainage** — measured null.
- That the Ohio vegetation signal is **near-channel** or seep-scale — refuted
  2026-09-08; |rho| peaks at 1 km.
- That the Ohio **mining-extent confound has been cleared** — the primary test
  missed its pre-registered bar by 0.004 (PARTIAL, not rejected).
- That **agreement with Rockwell's map means accuracy** — it is a published
  *automated* classification, not ground truth. Agreement measures replica
  fidelity. Only measured field chemistry is ground truth.

### Where it has been validated at all

Open acid-drainage terrain (Colorado mineral districts). It **does not transfer**
to forested neutral-pH coal drainage. Outside those, the tool will still draw a
map — that map is unvalidated.

---

## 7. Known quirks (real, tracked, not yet fixed)

- **Statistics panel, click inspector and accuracy masks use absolute
  thresholds unconditionally**, so in the default adaptive mode they disagree
  with the map. The panel now says so instead of asserting a false cutoff.
- The **click inspector is a different classifier from the map** — it keeps
  iron-only fallbacks to class 12 that were deliberately removed from the map
  cascade, and its "abundant" cut is `iron > 2.0` while its own printed text
  says `>0.30`. Clicked labels and map colours will routinely disagree.
- **Classes 6 and 10 unreachable**; 15/16 absent; 20/21 removed.
- **Legend swatch mismatches**: class 1 shows `A0522D` vs palette `8B7355`;
  class 5 shows `00FF00` vs `90EE90`.
- **Legend omits water class 3 (grey/INDETERMINATE).**
- **Dead settings**: `useWaterMask`, `useAWEINSH`, `brightnessMin`,
  `useNDWIComparison`, `useMultiCriteriaScore`, `useSceneRelativeThresholds` are
  declared and never read.
- **Season and Compositing changes need a manual reload** (re-pick the study
  area). Sensor, cloud method, AOI and sliders auto-reload.
- **Sentinel-2 is not 10 m for most of the panel** — SWIR is 20 m, coastal 60 m.
  Only `FerricIron1` and the green:NIR pair are true 10 m. Report effective GSD
  per index.
- `performInternalValidation()` is defined and **never called**, and still
  reports the removed classes 20/21.

---

## 8. Running the Python pipeline

### Environment

Use the single virtual environment from section 0 — `python/requirements.txt`
now lists every package the pipeline imports. It previously omitted `rasterio`,
`requests` and `shapely`, so a fresh install failed at first use in seven
modules.

> **On the author's machine only**, there are two environments for historical
> reasons: Earth Engine plus `rasterio` in
> `D:/dev/VPCA+STEPWISE-REGRESSION/.venv`, and a repo-local `.venv` without
> `ee`. That split is local, not part of the project; `CLAUDE.md` records it.

> **After a machine reinstall both venvs break** with `No Python at '...'` while
> `site-packages` is intact — `pyvenv.cfg` pins an absolute path under the old
> user profile. Fix: install CPython 3.11 (the wheels are cp311) and repoint
> `home`/`executable` in both `pyvenv.cfg`. Nothing needs reinstalling.

### The GEE memory trap has four levers — and only two are safe

`User memory limit exceeded` is about **compute-graph size**, not pixel count —
`bestEffort=True` does not help.

**Safe (request-size only — the numbers do not meaningfully change):**

1. **Band count** — `--bands <one band>`. **Reach for this first.** Verified
   **exactly bit-identical**: one-band vs eight-band extraction of the same 27
   stations gives max absolute difference **0.000**.
2. **Batch size** — halves down to a floor of **1**. Measured batch=1 vs
   batch=25 over 20 stations at 500 m: max absolute difference **1.11e-16**,
   one double-precision ULP. Say *"identical to within float epsilon"*, not
   *"identical"* — unlike the band subset, this one is not bit-exact.

**NOT safe — changes the result, not just the request:**

3. **Scene depth** (the 120-scene cap). A shallower stack is a **different
   median composite and different numbers.** Never reduce it for one region and
   pool the result with regions that kept 120. If you must reduce it, reduce it
   for *every* region in the comparison and say so in the report.
4. **Coarser scale.** Same objection, more so.

**The order matters.** Exhaust levers 1 and 2 before considering 3 — reaching
for the scene cap first is the tempting mistake, and it silently converts a
memory problem into a methodology problem.

### End-to-end on a new region

```bash
PY=python    # the activated environment from section 0

# 1. chemistry (once per region)
$PY python/fetch_wqp.py --region "<Name>, <ST>" --bbox "lat_lo,lon_lo,lat_hi,lon_hi"

# 2a. coal / neutral-pH dose-response
$PY python/cmd_detect.py --extract --season leafoff --radii 30,60,100,500,1000 \
      --bands NDVI_stress --regions <slug> --out data/matched/cmd_<slug>.csv
$PY python/cmd_detect.py --analyse --inputs data/matched/cmd_<slug>.csv

# 2b. acid metal-mine seep detection
$PY python/seep_detect.py --extract --sensor L8 --regions <slug>
$PY python/seep_detect.py --analyse
```

### What stays region-locked no matter what

- **Rockwell's raster is US-Southwest only.** `compare_rockwell`, `pool_labels`,
  `iron_index_transfer`, `iron_criterion_search`, `paper_faithful_test` and
  `watershed_nap`'s Rockwell arm are unavailable elsewhere. `resolve_region()`
  returns `rockwell_available=False` for any overlay region rather than
  producing a silently empty zonal read.
- **ODNR MinesOfOhio is Ohio-only**, so the CMD2 mining-extent confound test
  cannot be repeated in another state without a new **non-satellite-derived**
  mine-polygon source. NLCD is explicitly rejected for this — it shares the NDVI
  physics and would regress the vegetation signal partly on itself.
- **The Water Quality Portal is US-only.** The Python arm cannot follow the
  Earth Engine tool abroad.

---

## 9. Reading a result honestly

Beside any rho / R² / AUC, always report:

1. **n**, and the **caveat**.
2. For grouped data, the **between/within variance split** — a pooled sulfate
   result once *reversed sign* (−0.563 → +0.220) when region effects were
   removed; it was 67.5% between-region variance.
3. **Worst-case leave-one-region-out**, never pooled — within-site AUCs of 0.99
   collapsed to 0.63–0.67 pooled, and one index fell to 0.437, below chance.
4. **Sign consistency across regions.** A pooled rho with inconsistent signs has
   never been a result in this project.
5. **Multiple-comparison correction** where more than one test was run.

And: **never test a hypothesis on the data that generated it.** If a grouping or
cutoff was chosen by looking at the outcome, any p-value from it is meaningless.
Say so, and state what would actually test it.

**A null or a collapse is a valid, publishable result** and gets reported as
prominently as a positive.
