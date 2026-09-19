# How to test everything yourself

**Written 2026-09-16.** Every command below that runs offline was run while
writing this guide, and the "expect" lines are copied from those runs.

| part | what you test | needs |
|---|---|---|
| **A** | the Earth Engine map tool | a browser and an Earth Engine account |
| **B** | the Python pipeline and the `amdtool` package | this PC's Earth Engine Python environment |
| **C** | SpectraLab's new **AMD severity report** module | the SpectraLab source folder on its feature branch |
| **D** | the blind-search result, re-checked | the extracted data already on this PC |
| **E** | publishing the Zenodo update | your GitHub and Zenodo accounts |
| **F** | troubleshooting | — |

> **Before you start — what is and isn't installed**
>
> - **No new SpectraLab release was made.** SpectraLab is still 0.39.0, and
>   `SpectraLab-0.39.0.exe` **does not contain the AMD module.**
> - **SpectraLab is not installed on this PC as an app.** You run the new module
>   from source (§C).
> - **The only thing installed** is the `amdtool` package, in
>   `D:\dev\VPCA+STEPWISE-REGRESSION\.venv`.
> - **Zenodo has not been updated.** Its latest version is 1.5.5 (April 2026),
>   which carries retracted claims; v3.11.0 is prepared for you to publish (§E).

All commands are for **PowerShell**. Set this once per window; every Python step
below uses it:

```powershell
$py = "D:\dev\VPCA+STEPWISE-REGRESSION\.venv\Scripts\python.exe"
```

That is the environment with Earth Engine installed. The AMD Detection Tool's
own `.venv` has no `ee` module.

---

## A. The Earth Engine tool (nothing to install)

1. Open <https://code.earthengine.google.com> and sign in. Choose your Cloud
   project in the Code Editor's project selector.
2. **New script.** Paste the whole of
   `D:\dev\Sulfate-Methos\earth-engine\amd_detection_v2.4.0.js` and press
   **Run**. The file name says 2.4.0, but the tool reports **v3.1.0** when it
   starts.
3. **Pick an area.** Exactly one area is active at a time, and the **Study
   Area** dropdown shows which.
   - **Preset:** choose one of the 30 entries.
   - **Custom AOI:** type latitude, longitude and a radius in km (0.3–200),
     then press **Set Custom AOI**.
4. **Read the layer that is on by default:**
   - **🏔️ Land AMD Classification.** Transparent means *unclassified*, **not**
     clean. This is the validated product.

   **Since v3.1.1 the in-water module is RETRACTED and ships OFF**, so no water
   layer is drawn unless you tick its box. If you do, the Console prints why it
   is retracted: its indices ranked a clean control lake highest, and iron and
   sulfate were undetectable in the water column. Its classes are index levels,
   never contamination. Every other diagnostic layer stays hidden in the Layers
   panel (`docs/OPERATOR_GUIDE.md` §2).
5. **Check the v3.1.0 radius fix yourself.** Keep one centre and set the radius to 8,
   then 12, then 20 km. The **σ cutoff panel** must print the **same cut** each
   time, because statistics come from a fixed 12 km circle.
6. **The σ multipliers** sit under **Advanced: override** and are staged: a
   slider does nothing until you press **Apply**. The calibrated values are
   iron 0.50, clay 0.25, ferric 0.50, ferrous 0.50. The old 2.0 / 1.5 values
   flag nothing.
7. **Choosing Sentinel-2** shortens the record to about 2017–2020.
8. **What you may and may not conclude:** `docs/OPERATOR_GUIDE.md` §6.
   - The map is a replica of the USGS method, **not a detector**.
   - **Sulfate cannot be seen** optically.
   - **The tool does not find unknown mine sources.** The blind search tested
     this (§D).

---

## B. The Python pipeline and `amdtool`

```powershell
cd D:\dev\Sulfate-Methos
```

1. **The test suite.** No Earth Engine is needed; tests that need the
   gitignored `data\` folder skip on a clean clone.

   ```powershell
   & $py -m pytest tests\
   ```

   **Expect:** `207 passed` (about 45 s).

2. **Earth Engine credentials.**

   ```powershell
   & $py python\ee_auth.py
   ```

   **Expect:** `credentials: service_account (...)`, then
   `Earth Engine initialised OK`. On a new PC, follow `OPERATOR_GUIDE.md` §0
   step 3.

3. **Regenerate committed results.** No Earth Engine is needed. Each command
   rewrites a committed file with identical content, so `git status` must stay
   clean afterwards:

   ```powershell
   & $py python\b2_reproduction_audit.py --out validation\report_b2_reproduction_2026-09-15.txt
   & $py python\b2_dose_response_regen.py --out validation\report_b2_dose_response_2026-09-15.txt
   git status --short validation
   ```

   - **Expect:** the first finishes instantly and the second in about 1 minute.
   - **Expect:** `git status` prints **nothing** for these files.
   - The dose-response report shows FerricIron1 vs dissolved Fe **+0.568,
     n = 75, p = 0.0004, q = 0.0072**.

4. **A first live run** (Earth Engine, about 10–15 minutes). It downloads
   chemistry, extracts leaf-off NDVI at 30 / 60 / 100 m, and runs the
   dose-response:

   ```powershell
   & $py python\fetch_wqp.py --region "Monday Creek, OH"
   & $py python\cmd_detect.py --extract --season leafoff --radii 30,60,100 --bands NDVI_stress --regions monday_creek_oh --out data\matched\cmd_first.csv
   & $py python\cmd_detect.py --analyse --inputs data\matched\cmd_first.csv
   ```

   `memory limit - retrying at batch=N` lines are normal (§F).

---

## C. SpectraLab with the AMD severity report (from source)

### C1. Check you are on the right code

```powershell
cd D:\dev\VPCA+STEPWISE-REGRESSION
git -c safe.directory=D:/dev/VPCA+STEPWISE-REGRESSION branch --show-current
.\.venv\Scripts\python.exe -c "import amdtool; print(amdtool.__file__)"
```

- **The branch must be** `feature/amd-severity-module`. If it isn't, run:

  ```powershell
  git -c safe.directory=D:/dev/VPCA+STEPWISE-REGRESSION checkout feature/amd-severity-module
  ```

- **The second command must print**
  `D:\dev\Sulfate-Methos\src\amdtool\__init__.py`. If it fails, reinstall
  `amdtool`:

  ```powershell
  uv pip install --no-deps -e D:\dev\Sulfate-Methos --python .venv\Scripts\python.exe
  ```

### C2. The offline tests (no Earth Engine, about 20 s)

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_amd_module_offline.py tests\test_amd_settings_reach_spec.py tests\test_manifest_attribution.py tests\test_registry.py
```

**Expect:** `25 passed`.

### C3. Run it in the app

1. **Start the app:**

   ```powershell
   .\.venv\Scripts\python.exe scripts\run_ui.py
   ```

   Then open **<http://localhost:8080>** in your browser. The app does not open
   one itself. To use another port, first set `$env:PORT="8090"`.
2. **Sign in to Earth Engine.** Go to **Settings → Connect Earth Engine**.
   Alternatively, open *Advanced: use a lab service-account key instead* and
   give the path to your key file.
3. **New Run.** Enter your name and a mission name. Under **Module**, choose
   **"AMD severity report: index vs water chemistry (Landsat 8 / Sentinel-2)"**.
4. **Draw a rectangle that spans more than one district.** A single district
   usually has fewer than the 20 stations the test needs, and correctly returns
   `NO_TESTABLE_PAIRS`. Two tests worth running:
   - **Metal mine:** Silverton + Ouray, about **lat 37.70–38.20, lon −107.90 to
     −107.50**. Set **Drainage type** `metal_mine`, **Sensor** `L8`, **Water
     chemistry** `wqp`.
   - **Coal:** Huff Run, Ohio, about **lat 40.45–40.72, lon −81.30 to −81.00**.
     Set **Drainage type** `coal`, **Sensor** `L8`.
5. **Press Run.** A 391 km² box took about 80 s; bigger boxes download more
   chemistry and take a few minutes.
6. **Where the results go:**
   `Documents\SpectraLab\outputs\<your name>\<mission>\amd\` (or the folder set
   under **Settings → Output folder**).

   | file | contents |
   |---|---|
   | `amd_report.md` | the verdict, the per-tile table and the claim boundaries |
   | `amd_dose_response.csv`, `amd_stations_extracted.csv` | the numbers behind it |
   | `amd_FerricIron1.tif` / `.png` | the score map (coal runs name it after `NDVI_stress`); display only |
   | `chemistry\` | the Water Quality Portal download |

   In the mission folder, `run_manifest.json` should list **Landsat** and
   **Water Quality Portal** under `attribution → data_citations`.
7. **How to read the verdict:**

   | verdict | meaning |
   |---|---|
   | `SUCCESS` / `PARTIAL` / `NULL` | the test ran |
   | `UNINTERPRETABLE` | coal buffers were mostly canopy |
   | `NO_TESTABLE_PAIRS` | fewer than 20 usable stations |

   Every report says **EXPLORATORY**: you chose the area while looking, so
   **don't cite the p-values**. Full guide: `docs\AMD_MODULE.md` in that
   repository.

### C4. The live test (optional, about 80 s, uses Earth Engine)

```powershell
$env:SPECTRALAB_EE_TESTS = "1"
$env:GEE_SERVICE_ACCOUNT_JSON = "D:\dev\VPCA+STEPWISE-REGRESSION\<your-key-file>.json"
.\.venv\Scripts\python.exe -m pytest -q tests\test_amd_module_live.py
```

**Expect:** `1 passed`. It fails if any output file is empty.

> **Don't use `SpectraLab-0.39.0.exe` for this.** It predates the module. If you
> run `uv run ...` instead of the `.venv` python, `uv` may re-sync the
> environment. That is fine, unless a long Earth Engine job is running from the
> same `.venv` at the time.

---

## D. Re-check the blind-search result yourself

The seven extracted districts are already in `data\matched\blindsearch_s2_*.csv`.

```powershell
cd D:\dev\Sulfate-Methos
& $py python\blind_search.py --analyse --registration validation\BLIND_SEARCH_PREREGISTRATION_2026-09-14.md --out validation\report_blind_search_2026-09-15.txt
& $py python\blind_search.py --frame --registration validation\BLIND_SEARCH_PREREGISTRATION_2026-09-14.md --out validation\blind_search_field_frame_2026-09-15.csv
git status --short validation
```

- **The analysis refuses to run** unless the registration is committed and the
  site list still matches its registered SHA-256.
- **Expect:** H-BS1 **NO SIGNAL DETECTED** (4 of 32 sites, p = 0.0738) and
  H-BS2 **NOT BETTER THAN BARE GROUND** (14 of 50; McNemar p = 0.0384 against a
  Holm level of 0.025).
- **Expect:** `git status` prints nothing, because the regenerated files are
  identical.
- **Write-up:** `validation\ARM_BLIND_SEARCH_2026-09-15.md`.
- **The one registered piece not run** is the snow-masked sensitivity (about a
  day):

  ```powershell
  & $py python\blind_search.py --extract --snow-masked
  ```

  Then run `--analyse` again; the report gains a snow-masked section.

---

## E. Publishing the Zenodo update (when you are ready)

**What Zenodo shows today (checked 2026-09-19):**
- **The latest archived version is 1.5.5, published 2026-04-05.**
  - Version DOI: `10.5281/zenodo.19429983`.
  - Concept DOI, which always resolves to the newest version:
    `10.5281/zenodo.19424985`.
- **Its description still claims** validation against Muskingum Watershed
  chemistry and names Ganau Pond. The project has retracted both.
- **Nothing from v2.x or v3.x has ever reached Zenodo.** Those versions were git
  tags only. Zenodo's GitHub integration archives a **GitHub Release**, not a
  tag, and the only GitHub Releases are 1.5.4 and 1.5.5.

**Already prepared for you (2026-09-19):**
- `CITATION.cff` is at `version: 3.11.0` and `date-released: 2026-09-19`, with
  the corrected abstract and the concept DOI.
- The README badge and BibTeX match.
- `CHANGELOG.md` has the `[3.11.0]` entry.

**Your steps:**

1. **If you publish on a later day,** change `date-released:` in `CITATION.cff`
   to that day, then commit and push.
2. **Tag and push the tag:**

   ```powershell
   cd D:\dev\Sulfate-Methos
   git pull
   git tag -a v3.11.0 -m "v3.11.0"
   git push origin v3.11.0
   ```

3. **On GitHub:**
   - go to **Releases → Draft a new release**, and choose tag `v3.11.0`;
   - for the notes, paste the `[3.11.0]` section of `CHANGELOG.md`;
   - click **Publish release**.

   **This is the step that triggers Zenodo.**
4. **Check Zenodo** a few minutes later: open
   <https://doi.org/10.5281/zenodo.19424985>. It should show **version 3.11.0**,
   with a description that begins *"An open reimplementation of the automated
   iron-sulfate mineral mapping method…"* (taken from `CITATION.cff`).
   - **If no new version appears within about 30 minutes,** the integration is
     off for this repository.
   - Upload by hand: open the record on zenodo.org, choose **New version**,
     upload the release `.zip`, and set the version to 3.11.0.
   - **Replace the description with the `CITATION.cff` abstract.** Zenodo
     pre-fills it from 1.5.5, which carries the retracted claims.
   - Then click **Publish**.
5. **Flag the old version.** Zenodo lets you edit a published record's
   description, though not its files.
   - Open version **1.5.5**, choose **Edit**, and make the first line: *"SUPERSEDED
     — the validation claims in this version were retracted; see the latest
     version, 10.5281/zenodo.19424985."*
   - Then **Publish**. Do the same for any earlier version listed.
6. **Tell the record.** In `validation\STATE.md` (OPEN → NEXT), mark the Zenodo
   item done.

---

## F. Troubleshooting

| you see | what it means |
|---|---|
| `memory limit - retrying at batch=N` | normal. Earth Engine's compute limit; batches shrink to 1 automatically |
| `Sleeping … before retry k of 5 … after 502/503` or a DNS error | a transient Earth Engine or network fault; the client retries. If a district still writes a `.FAILED` file for this reason, delete it and re-run that district. That is the rule committed before the blind-search result |
| tests `SKIPPED` | the gitignored `data\` folder or git history isn't there. Expected on a clean clone |
| `ModuleNotFoundError: No module named 'ee'` | wrong Python; use `$py` |
| `No Earth Engine credentials found` | follow `OPERATOR_GUIDE.md` §0 step 3 |
| SpectraLab: *"needs the amdtool package"* | re-run the install command in §C1 |
| SpectraLab: preview PNG missing, warning in the run | display only; the GeoTIFF and every statistic are unaffected |
