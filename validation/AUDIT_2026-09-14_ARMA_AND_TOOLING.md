# Audit 2026-09-14 — two Arm A defects, a geology mislabel, a crashing helper, and a decision bar that does not transfer

**Found while scoping** the SpectraLab integration and the next test. Every item
below was **verified directly** (code read, file inspected, or a command run),
not taken from a summary. None rescues a retracted claim; two of them add
reasons retracted numbers must not be reused.

---

## 1. Arm A computed its σ thresholds over each catchment

**Evidence.** `python/watershed_nap.py:165`:

```python
cls = classify_v3(ee, comp, region).updateMask(valid).rename("class")
```

where `region` is the catchment polygon, and `gee_classify.classify_v3`'s own
docstring states that *"thresholds are computed from `region`'s own pixel"*
distribution.

**Effect.** This is the **same defect** fixed in the Earth Engine tool at v3.1.0:
the extent over which `mean + k·σ` is computed is silently a classification
parameter. A small catchment gets thresholds from its own narrow pixel
distribution, a large one from a broad distribution, so the same ground can be
classified differently depending on the size of the catchment that contains it.
Arm A's per-catchment mineral loadings are therefore not comparable across
catchments of different size.

**Status.** The Arm A retraction (`ARM_A_CROSS_REGION_RETEST_2026-08-13.md`)
**stands** — it rested on leave-one-region-out R² being negative for every model.
This defect is an additional reason those loadings cannot be reused.

**Fix before any Arm A re-run.** Compute σ once per district over
`region_geometry`, then classify every catchment with those fixed thresholds
(the `classify_v4_from_stats` pattern).

---

## 2. Arm A's "31 catchments" are 28 distinct polygons

**Evidence.** Across `data/matched/watershed_nap_*.csv`: 31 rows, **28 distinct
`basin_id`**. Three polygons are counted under two regions:

| `basin_id` | appears under |
|---|---|
| `7121080490` | Alma, Leadville |
| `7121092570` | Ouray, Silverton |
| `7120588780` | Lake City, Ouray |

**Mechanism.** `watershed_nap` de-duplicates catchments *within* a region, and
`pool_watershed_nap.py` / `arma_diagnostics.py` de-duplicate on
`(region, basin_id)`, so a polygon reached from two regions survives twice. It is
reachable from two regions because the curated boxes **overlap or touch**
(Alma lat 39.20–39.45 / lon −106.20…−105.95 overlaps Leadville lat 39.15–39.35 /
lon −106.45…−106.15; Silverton and Ouray share the 37.95° edge) and `hybas_12`
polygons are large enough to span them.

**Effect.** Identical loading values sit on both sides of leave-one-region-out
splits. That kind of leakage usually **flatters** out-of-sample fit, and LORO R²
was negative for every model regardless, so the retraction does not depend on
it. But the per-region rhos and the between/within variance split in the Arm A
retest include duplicated information, and **n should be quoted as 28 distinct
catchments**.

**Fix.** De-duplicate `basin_id` globally, across regions, before pooling.

---

## 3. The geology grouping mislabels Creede — and Lake City

**Recorded grouping** (`STATE.md` OPEN #1 and the Arm A open question; also
`ARM_A_CROSS_REGION_RETEST_2026-08-13.md`): *"Silverton + Ouray (San Juan
calderas) vs Central City + Creede + Leadville"*.

**What the published geology says:**

- **Creede lies within the central San Juan caldera cluster.** The Creede
  caldera formed within the La Garita caldera during eruption of the Snowshoe
  Mountain Tuff (Lipman et al. 2006; Lipman 2000).
- **Lake City lies within the western San Juan caldera complex.** The Lake City
  caldera is nested within the older Uncompahgre caldera and is the source of
  the ~23 Ma Sunshine Peak Tuff (Lipman 1976; USGS revised volcanic history of
  the San Juan, Uncompahgre, Silverton and Lake City calderas).

So **Creede belongs with Silverton and Ouray** by volcanic setting, not with
Central City and Leadville (which are Colorado Mineral Belt districts outside the
San Juan volcanic field).

**Consequence.** Under the idea as it was worded — caldera-related districts
positive, the others not — Creede was **−0.800**, i.e. it runs *against* its own
correct label. Because that idea was generated from these same Arm A signs, this
is not a test and carries no p-value, exactly as before. What it does mean is
that the recorded grouping cannot be carried into any future test.

**Caveat that must be settled before any geology test.** *Volcanic setting*
(inside a caldera) and *deposit style* (epithermal vein, porphyry-related vein,
replacement) are different axes. `B2_PREREGISTRATION_2026-08-14.md` §9 words its
prediction as *"volcanic-hosted epithermal / caldera-related (San Juan style)"*,
which blends them. The label must be defined on one explicit axis, from a
citable source, **before** any new region's sign is seen.

**References**
- Lipman, P.W., Robinson, J.E., Dutton, D.R., Ramsey, D.W., and Felger, T.J.,
  2006, *Geologic map of the central San Juan caldera cluster, southwestern
  Colorado*: U.S. Geological Survey Geologic Investigations Series I-2799.
  <https://pubs.usgs.gov/imap/i2799/data/pdf/i2799pamphlet.pdf>
- Lipman, P.W., 2000, Central San Juan caldera cluster: Regional volcanic
  framework, *in* Bethke, P.M., and Hay, R.L., eds., *Ancient Lake Creede*:
  Geological Society of America Special Paper 356, p. 9–71.
  <https://www.usgs.gov/publications/central-san-juan-caldera-cluster-regional-volcanic-framework>
- Lipman, P.W., 1976, *Geologic map of the Lake City caldera area, western San
  Juan Mountains, southwestern Colorado*: U.S. Geological Survey Map I-962.
  <https://pubs.usgs.gov/publication/i962>
- U.S. Geological Survey, *Revised volcanic history of the San Juan,
  Uncompahgre, Silverton, and Lake City calderas in the western San Juan
  Mountains*.
  <https://usgs.gov/publications/revised-volcanic-history-san-juan-uncompahgre-silverton-and-lake-city-calderas-western>

---

## 4. `vpca_validation.convolve_splib07` crashes on NumPy 2.x

**Evidence.** `python/vpca_validation.py:151-152` call `np.trapz`. Both
environments run **NumPy 2.4.6**, where `hasattr(numpy, "trapz")` is `False` and
`numpy.trapezoid` is the replacement. Any call raises `AttributeError`.

**Impact.** Nothing in the repository calls it, so **no reported number is
affected**. It is the documented route to real USGS splib07 spectra, so it would
have failed the first time anyone used it. Fixed in the `amdtool` refactor, with a
unit test.

---

## 5. CMD2's decision bars cannot be reused for Pennsylvania

CMD2 fixed **absolute** partial-rho bars: `RHO_REJECT = 0.25` (confound
rejected) and `RHO_SUPPORT = 0.15` (confound supported). Pennsylvania's **raw**,
unconditioned values are already **−0.143** (sulfate) and **−0.187**
(conductance). "Rejected" is therefore unreachable, and "supported" is nearly
automatic for sulfate before any conditioning is done.

**Consequence.** A Pennsylvania mining-covariate test must be registered as
**attenuation from Pennsylvania's own raw value on the same rows**, not by
reusing Ohio's bars.

---

## 6. A code comment claims an extraction that did not happen

`python/seep_detect.py` says of `THIN_REGIONS` (Creede, Alma): *"Extracted and
reported separately."* No `seep_*_creede_co` or `seep_*_alma_co` file exists, and
no committed B2 report shows their values. **They were never extracted.**

This matters positively for the blind-search test: it confirms Creede, Alma and
Lake City never contributed a `FerricIron1` value at a source point, so they are
genuinely independent of the index choice. Their only prior use was Arm A, which
scored upstream mineral loadings, not source-point buffers.
