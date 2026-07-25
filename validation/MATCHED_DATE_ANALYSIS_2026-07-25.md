# Matched-date analysis: satellite reflectance vs measured water chemistry

**Date:** 2026-07-25 · **Tool:** v2.5.1 · **Author:** Abdulrahman Hussein
**Data:** `data/matched/matched_spectra_chemistry.csv` (42 rows)
**Code:** `python/fetch_wqp.py` → `python/match_scenes.py` → `python/detection_limit.py`

## What was done

Every dated water-chemistry sample from the Water Quality Portal (USGS NWIS +
EPA STORET + Ohio EPA) was matched to a **single** satellite scene acquired
within ±5 days — never a composite, because chemistry is measured on one day.
The v2.4.0 water mask was applied and a window-median reflectance extracted at
each station.

- 3,023 unique chemistry records, 14 lakes, 2013–2023
- **42 matched spectra↔chemistry pairs** (34 Sentinel-2, 8 Landsat 8/9)
- 33 carry Total Recoverable iron; median 206 clean water pixels per window

Two defects were found and fixed while building this, both of which would have
silently corrupted the result:

1. **WQP station coordinates are not on water.** They mark shore access points
   and dams. At a 30 m radius most stations returned 0–6 water pixels; at
   150–400 m they return 21–900. Sampling radius is now 300 m, so we measure
   *lake water near the station*, not the station pixel. Defensible for small
   well-mixed reservoirs, but it must be stated.
2. **Tile selection by date alone picked the wrong lake.** The study lakes are
   >100 km apart; a MultiPoint spanning them selects the least-cloudy tile over
   *any* of them. Grouping is now per (lake, date).

## Results

### 1. Sulfate is optically invisible — confirmed quantitatively

n = 41, range **10.6–439 mg/L**. **No feature's 95% bootstrap CI excludes
zero.** Across a 40× concentration range, nothing in the visible or SWIR
responds. This is the predicted physics (SO₄²⁻ has no VNIR absorption) now
measured rather than asserted, and it retires the v1.5.4–v2.4.0 claim that the
tool detects sulfate contamination.

### 2. Iron: a real, reproducible association with reduced reflectance

n = 33, range 58–6,200 µg/L Total Recoverable.

| feature | Spearman ρ | 95% CI |
|---|---|---|
| **SR_B2 (blue, 490 nm)** | **−0.462** | [−0.735, −0.101] |
| SR_B3 (green) | −0.404 | [−0.678, −0.054] |
| SR_B4 (red) | −0.397 | [−0.687, −0.049] |

Median blue reflectance falls **0.0275 → 0.0185 (−33%)** between Fe < 300 and
Fe > 1,000 µg/L.

**It is not the turbidity confound.** Iron and turbidity do co-vary (ρ = 0.511),
but turbidity itself does not drive blue reflectance (ρ = −0.047), and the iron
signal *survives* controlling for it — partial ρ = **−0.473** vs raw −0.462.
Excluding Atwood, which contributes 21 of 42 rows, the association holds:
ρ = −0.441 (n = 17) across independent lakes.

### 3. But the signal is NOT ferric absorption

| | absolute band | albedo-normalised shape |
|---|---|---|
| blue B2 | −0.462 | f_B2 −0.146 |
| green B3 | −0.404 | f_B3 +0.104 |
| red B4 | −0.397 | f_B4 +0.108 |
| **red/blue ratio** | — | **+0.111** |

Every band darkens together while the *shape* barely changes. Ferric iron
absorbs strongly in the blue, so genuine Fe³⁺ colouring must drive **red/blue
sharply up**; it moves +0.111, i.e. essentially not at all.

**Conclusion: higher iron co-occurs with broadband darker water, without the
spectral signature of ferric iron.** Unmeasured alternatives — CDOM/dissolved
organic carbon (which absorbs blue strongly and darkens water overall), water
depth, and algal absorption — remain fully consistent with these data. Note
that two of the highest-iron samples came from *clear* water (Lake Hope,
2,650 µg/L at 1.43 NTU), so this is not a suspended-sediment effect either.

### 4. The tool's own iron index tracks turbidity, not iron

`iron_idx` = (B2/B1) − (B5/B4) correlates with **turbidity** at ρ = 0.278
(CI excludes 0) and shows no significant relationship with iron. Likewise
`red_blue` (ρ = 0.451) and `green_blue` (ρ = 0.341) track turbidity. This is
the independent, quantitative confirmation of finding W1: the contamination
indices respond to sediment, not to acid mine drainage.

## What this supports, and what it does not

**Supports:** a genuine, confound-controlled association between water-column
iron and reduced visible reflectance in Sentinel-2/Landsat imagery, detectable
at 1–6 mg/L Total Recoverable Fe. That is a legitimate preliminary result.

**Does not support:** attributing that association to ferric iron optics. The
spectral shape is wrong for Fe³⁺, and the discriminating measurement (CDOM/DOC)
was never made at these sites.

## Limitations

- n = 33 for iron; only **5 rows exceed 1,000 µg/L**, so the high end rests on
  five observations from four lakes.
- **Only 4 Dissolved iron measurements** exist — the dissolved/particulate
  split, which finding W4 showed is decisive, cannot be tested.
- Atwood contributes half the rows; repeat visits to one lake are not
  independent samples.
- Sampling radius (300 m) means these are lake-water spectra near a station,
  not co-located with the water sample itself.
- Mixed sensors (34 S2 at 10–20 m, 8 L8/L9 at 30 m) with different band
  centres and atmospheric correction.
- **No DOC/CDOM, depth, or TSS data** — the alternatives to the iron
  explanation are untested, not excluded.

## Next steps this justifies

1. **Field campaign measuring CDOM/DOC, Secchi depth and dissolved vs total
   Fe** alongside synchronous spectra. That single addition would separate the
   iron hypothesis from the organic-matter hypothesis, which is precisely what
   these data cannot do.
2. Expand n at the high end — target sample dates with Fe > 1 mg/L and pull
   every available scene, rather than one per date.
3. Drone work at cm scale: the association found here is in the *water column*
   at 10–30 m. Precipitate on bed, shoreline and inflows is a different, likely
   stronger target, invisible to satellites but not to a 7 cm sensor.
