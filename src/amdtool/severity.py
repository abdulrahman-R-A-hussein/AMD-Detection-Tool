"""Severity report: does a validated index track measured chemistry inside an AOI?

The capability a host application (SpectraLab) exposes. It runs ONE index per
preset - the index each preset was validated on - against that preset's
analytes, so a user cannot fish across the panel for a significant pair.

Every run is EXPLORATORY. Its area, grouping and settings were chosen
interactively, so its p-values describe that run only, and the report says so
in its first lines.

Pipeline: stations (from a chemistry folder) -> composite -> buffer extraction
-> dose-response with a within-tile permutation null -> report.
"""

import csv
import math
import os
from dataclasses import dataclass

from amdtool import claims, imagery
from amdtool.chemistry import CHEM_VARS
from amdtool.dose_response import SEED, analyse
from amdtool.errors import InsufficientDataError


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    index: str
    stat: str
    radius_m: int
    season: str            # "may_jul" or "leafoff"
    analytes: tuple
    station_set: str       # "sources" or "all"
    canopy_limit: object   # float, or None for no canopy gate
    validated_by: str


PRESETS = {
    "metal_mine": Preset(
        key="metal_mine", label="Acid metal-mine drainage",
        index="FerricIron1", stat="p90", radius_m=60, season="may_jul",
        analytes=("Iron_mgL_dissolved", "Iron_mgL_any", "pH"),
        station_set="sources", canopy_limit=None,
        validated_by=("Arm B2 dose-response, Colorado: FerricIron1 vs dissolved "
                      "iron rho +0.568 (n=75, Landsat 8). Per district it is "
                      "+0.64 (Central City, n=20), +0.68 (Ouray, n=17) and +0.64 "
                      "(Silverton, n=15), but +0.004 (Leadville, n=23) - no "
                      "relationship there. Leave-one-region-out R2 is negative, so "
                      "at best it RANKS severity within a district and does not "
                      "predict concentration across districts."),
    ),
    "coal": Preset(
        key="coal", label="Coal / neutral-pH mine drainage",
        index="NDVI_stress", stat="p90", radius_m=30, season="leafoff",
        analytes=("Sulfate_mgL", "SpecificConductance"),
        station_set="all", canopy_limit=0.6,
        validated_by=("Phases CMD1-CMD3, Ohio and Pennsylvania: vegetation index vs "
                      "sulfate and conductance is negative and, in Pennsylvania, "
                      "sign-consistent (conductance -0.187, n=443) - but weak, "
                      "and its spatial scale differs between basins."),
    ),
}

SENSORS = ("L8", "S2")
SENSOR_SCALE_M = {"L8": 30, "S2": 20}
DEFAULT_GRID = 2
DEFAULT_MIN_N = 20
DEFAULT_MIN_GROUP_N = 8
DEFAULT_N_PERM = 5000

_NUMERIC = {"lat", "lon", "radius", "n_px"} | set(CHEM_VARS)


def get_preset(key):
    try:
        return PRESETS[key]
    except KeyError:
        raise ValueError("unknown preset %r; choose from %s" % (key, ", ".join(PRESETS)))


def bands_for(preset):
    bands = [preset.index]
    if preset.canopy_limit is not None and "NDVI_stress" not in bands:
        bands.append("NDVI_stress")
    return bands


def composite(ee, region, preset, sensor):
    if sensor not in SENSORS:
        raise ValueError("sensor must be one of %s" % (SENSORS,))
    if sensor == "S2":
        if preset.season != "may_jul":
            raise ValueError("Sentinel-2 is wired only for the May-July season "
                             "(the validated metal-mine path)")
        return imagery.s2_composite(ee, region)
    if preset.season == "leafoff":
        return imagery.l8_composite_season(ee, region, "leafoff")
    return imagery.l8_composite(ee, region)


def index_composite(ee, bbox, preset, sensor="L8"):
    """The index image a preset scores, and how many scenes built it.

    Returned so one composite serves both the buffer extraction and the score
    raster."""
    comp, n_scenes = composite(ee, bbox.to_ee(ee), preset, sensor)
    if n_scenes < imagery.MIN_SCENES:
        raise InsufficientDataError("only %d scenes over the AOI (need %d)"
                                    % (n_scenes, imagery.MIN_SCENES))
    return imagery.index_image(ee, comp), n_scenes


def extract(ee, bbox, stations, preset, sensor="L8", *, img=None, n_scenes=None):
    """Buffer statistics for each station. Returns (rows, n_scenes).

    Pass `img`/`n_scenes` from index_composite() to reuse a composite."""
    if not stations:
        raise InsufficientDataError("no stations with chemistry inside the AOI")
    if img is None:
        img, n_scenes = index_composite(ee, bbox, preset, sensor)
    scale = SENSOR_SCALE_M[sensor]
    bands = bands_for(preset)
    got = imagery.extract_buffers(ee, img, stations, preset.radius_m, scale, bands)
    rows = []
    for p in stations:
        v = got.get(p["pid"], {})
        row = dict(region="aoi", tier="amd", sensor=sensor,
                   radius=float(preset.radius_m), season=preset.season,
                   pid=p["pid"], lat=p["lat"], lon=p["lon"],
                   n_px=v.get(bands[0] + "_count"))
        for b in bands:
            row[b + "_p90"] = v.get(b + "_p90")
            row[b + "_mean"] = v.get(b + "_mean")
        for a in CHEM_VARS:
            row[a] = p.get(a)
        rows.append(row)
    return rows, n_scenes


def _as_float(v):
    if v is None or v == "" or v == "None":
        return float("nan")
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def normalise_rows(rows):
    """None/'' -> NaN for every numeric column, so analyse() sees one convention."""
    out = []
    for r in rows:
        r = dict(r)
        for k in list(r):
            if k in _NUMERIC or k.endswith(("_p90", "_mean", "_count")):
                r[k] = _as_float(r[k])
        out.append(r)
    return out


def analyse_rows(rows, preset, bbox, *, grid=DEFAULT_GRID, n_perm=DEFAULT_N_PERM,
                 seed=SEED, min_n=DEFAULT_MIN_N, min_group_n=DEFAULT_MIN_GROUP_N):
    """Group stations into a grid x grid tiling of the AOI and run the test."""
    rows = normalise_rows(rows)
    for r in rows:
        r["group"] = bbox.tile_of(r["lat"], r["lon"], grid) or "outside"
    result = analyse(rows, [preset.index], preset.analytes, stat=preset.stat,
                     group_key="group", n_perm=n_perm, seed=seed, min_n=min_n,
                     min_group_n=min_group_n, canopy_band="NDVI_stress_p90",
                     canopy_limit=preset.canopy_limit)
    return rows, result


def group_counts(rows, analyte, index_col):
    counts = {}
    for r in rows:
        if r.get(index_col, float("nan")) == r.get(index_col, float("nan")) \
                and r.get(analyte, float("nan")) == r.get(analyte, float("nan")):
            counts[r["group"]] = counts.get(r["group"], 0) + 1
    return counts


def _fmt(v, spec="%+.3f"):
    return "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else spec % v


def report_markdown(rows, result, preset, bbox, *, sensor, grid, n_scenes=None,
                    title="AMD severity report", include_stepwise=True):
    col = "%s_%s" % (preset.index, preset.stat)
    L = ["# %s" % title, "",
         "> **%s**" % claims.EXPLORATORY_NOTICE, "",
         "## Run", "",
         "| | |", "|---|---|",
         "| preset | %s (`%s`) |" % (preset.label, preset.key),
         "| index | `%s` %s, %d m buffer |" % (preset.index, preset.stat, preset.radius_m),
         "| sensor / season | %s / %s |" % (sensor, preset.season),
         "| AOI | lat %.4f to %.4f, lon %.4f to %.4f (%.0f km2) |"
         % (bbox.lat_lo, bbox.lat_hi, bbox.lon_lo, bbox.lon_hi, bbox.area_km2()),
         "| grouping | %d x %d grid tiles, outcome-blind |" % (grid, grid),
         "| stations extracted | %d |" % result.n_rows]
    if n_scenes is not None:
        L.append("| scenes in composite | %d |" % n_scenes)
    L += ["", "**What this preset was validated on:** %s" % preset.validated_by, ""]

    if preset.canopy_limit is not None:
        L += ["## Canopy check", "",
              "Median buffer NDVI **%s** (limit %.2f) - %s" % (
                  _fmt(result.canopy_median_ndvi, "%.3f"), preset.canopy_limit,
                  "**above the limit: buffers are mostly canopy**"
                  if result.canopy_limited else "below the limit"), ""]

    L += ["## Verdict", "", "**%s** - %s" % (result.verdict,
                                              claims.VERDICT_TEXT.get(result.verdict, "")), ""]

    if result.pairs:
        L += ["## Dose-response", "",
              "| index | analyte | rho | n | perm p | BH q | between-tile % | per tile | signs |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in result.ranked():
            L.append("| `%s` | %s | %s | %d | %.4f | %.4f | %.0f | %s | %s |" % (
                r.index, r.analyte, _fmt(r.rho), r.n, r.p, r.q, r.between_pct,
                " ".join("%s %s" % (g, _fmt(v, "%+.2f"))
                         for g, v in sorted(r.per_group.items())) or "-",
                "consistent" if r.sign_consistent else "disagree"))
        L += ["", "Stations per tile with both an index value and chemistry:", ""]
        for a in preset.analytes:
            counts = group_counts(rows, a, col)
            L.append("- %s: %s" % (a, ", ".join("%s=%d" % kv for kv in sorted(counts.items()))
                                   or "none"))
        L += ["", "Tiles with fewer than %d stations are left out of the per-tile "
                  "columns and the sign check." % result.settings["min_group_n"], ""]

    L += ["## Claim boundaries", "", claims.boundaries_markdown(include_stepwise=include_stepwise), ""]
    return "\n".join(L)


def write_outputs(out_dir, rows, result, preset, bbox, *, sensor, grid,
                  n_scenes=None, include_stepwise=True):
    """Write stations CSV, dose-response CSV and report.md. Returns
    [{"path","kind","label"}] in the shape SpectraLab's RunResult expects."""
    os.makedirs(out_dir, exist_ok=True)
    outputs = []

    p_st = os.path.join(out_dir, "amd_stations_extracted.csv")
    keys = sorted({k for r in rows for k in r})
    with open(p_st, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    outputs.append({"path": p_st, "kind": "csv", "label": "Stations and extracted index values"})

    p_dr = os.path.join(out_dir, "amd_dose_response.csv")
    with open(p_dr, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["index", "analyte", "rho", "n", "perm_p", "bh_q",
                    "between_tile_pct", "sign_consistent", "per_tile"])
        for r in result.ranked():
            w.writerow([r.index, r.analyte, r.rho, r.n, r.p, r.q, r.between_pct,
                        r.sign_consistent,
                        ";".join("%s=%s" % (g, v) for g, v in sorted(r.per_group.items()))])
    outputs.append({"path": p_dr, "kind": "csv", "label": "Dose-response table"})

    p_md = os.path.join(out_dir, "amd_report.md")
    with open(p_md, "w", encoding="utf-8") as fh:
        fh.write(report_markdown(rows, result, preset, bbox, sensor=sensor, grid=grid,
                                 n_scenes=n_scenes, include_stepwise=include_stepwise))
    outputs.append({"path": p_md, "kind": "txt", "label": "AMD severity report"})
    return outputs
