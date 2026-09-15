"""Region registry: curated bounding boxes plus a user overlay.

Moved 2026-09-14 from python/fetch_wqp.py. The curated REGIONS entries, their
notes and the overlay rules are unchanged. The one change is that the overlay
location is a `data_dir` argument instead of a path derived from this file's
location, so the library works wherever it is installed.

Lookup order is curated-first: an overlay entry can never shadow a curated one,
so a stray `--bbox` cannot silently redefine Silverton.

Entries are (lat_lo, lon_lo, lat_hi, lon_hi, site_types, note). Use
`region_bbox()` to get a `BBox` rather than indexing the tuple.
"""

import json
import os

from amdtool.errors import UnknownRegionError
from amdtool.geometry import BBox

OVERLAY_FILENAME = "regions.json"


def region_slug(name):
    """Canonical slug for a region name: "Silverton, CO" -> "silverton_co".

    This lived as an inline expression in four modules, kept in sync by hand -
    watershed_nap.py said so in a comment. One copy, imported everywhere.
    """
    return name.lower().replace(", ", "_").replace(" ", "_")


# Regions pulled by BBOX rather than a named point - used for Colorado, where
# the target is the whole Animas River watershed (streams + a few lakes), not
# one named waterbody. (lat_lo, lon_lo, lat_hi, lon_hi, siteTypes, note)
REGIONS = {
    "Silverton, CO": (
        37.70, -107.85, 37.95, -107.50, None,
        "Animas River watershed incl. Cement Creek, Mineral Creek. Verified "
        "2026-08-10, no server-side siteType filter (see EXCLUDE_SITE_TYPES): "
        "11410 Iron rows, 5681 Sulfate, across 3606 stations including "
        "62 mine-discharge/adit/tailings/spring source points.",
    ),
    # Added 2026-08-13 (Water Phase 2 Part B) specifically to raise Arm A's n
    # beyond its verified 6-catchment ceiling at Silverton: hybas_12 has a
    # granularity floor there, and 82 stations spanning that whole search area
    # all collapsed into the same 6 polygons. Raising n needs DIFFERENT river
    # systems, not more Silverton stations - each region below drains to a
    # different major system, verified independent by river network, not just
    # by distance:
    #   Animas (Silverton, above)         -> San Juan -> Colorado River
    #   Uncompahgre (Ouray)                -> Gunnison -> Colorado River
    #   Alma/Fairplay, Leadville           -> Arkansas River (two districts)
    #   Creede                             -> Rio Grande
    #   Clear Creek/Central City           -> South Platte River
    #   Lake City/Lake Fork                -> Gunnison (Lake Fork tributary)
    # Counts are Iron-characteristic probe results (WQP, 2026-08-10/13),
    # >=3-sample station counts are what actually matters for a chemistry
    # median; verify per-region distinct-catchment count once delineated,
    # same as Silverton was - do not assume more stations means more n.
    # ------------------------------------------------------------------
    # Added 2026-08-16. OHIO APPALACHIAN COAL BASIN - the PhD's actual target.
    # Colorado is ACID metal-mine drainage; these are COAL mine drainage (CMD)
    # watersheds where the diagnostic problem is different and harder:
    # sulfate contamination HIDDEN UNDER NEUTRAL pH. Alkaline overburden
    # buffers the acid, so pH reads 6.5-8 while sulfate and conductivity stay
    # elevated - and our own B2d "clean water" definition (Fe<0.3 AND pH
    # 6.5-9.0) would file exactly those sites as CLEAN. For CMD, contamination
    # must be keyed on SULFATE and specific conductance, never pH.
    #
    # Mechanistic reason this is worth testing rather than assuming it fails:
    # at neutral pH, Fe(II) oxidises and hydrolyses FAST, so ochre precipitates
    # at the discharge instead of staying in solution and dispersing as it does
    # in acid drainage. Neutral CMD may therefore produce a MORE localised,
    # MORE optically visible iron deposit than the Colorado sites - the
    # opposite of the intuitive expectation.
    #
    # All five are long-monitored CMD restoration watersheds (Ohio EPA, ODNR,
    # local watershed groups), chosen for monitoring density, not for outcome.
    "Monday Creek, OH": (
        39.45, -82.40, 39.72, -82.10, None,
        "Monday Creek, Hocking/Perry/Athens Co. Classic Ohio CMD restoration "
        "watershed. Probe before relying on counts.",
    ),
    "Sunday Creek, OH": (
        39.42, -82.12, 39.70, -81.85, None,
        "Sunday Creek, Athens/Perry/Morgan Co. CMD, incl. Corning/San Toy "
        "discharges. Probe before relying on counts.",
    ),
    "Raccoon Creek, OH": (
        38.85, -82.60, 39.20, -82.25, None,
        "Raccoon Creek, Vinton/Gallia/Jackson Co. Large CMD watershed with a "
        "long Ohio EPA record. Probe before relying on counts.",
    ),
    "Huff Run, OH": (
        40.45, -81.30, 40.72, -81.00, None,
        "Huff Run / Conotton Creek, Carroll/Tuscarawas Co. CMD restoration. "
        "Probe before relying on counts.",
    ),
    "Leading Creek, OH": (
        38.95, -82.20, 39.22, -81.90, None,
        "Leading Creek, Meigs Co. CMD watershed. Probe before relying on "
        "counts.",
    ),
    "Ouray, CO": (
        37.95, -107.90, 38.20, -107.55, None,
        "Uncompahgre River watershed (Gunnison system). Probed 2026-08-10: "
        "2935 Iron rows, 134 stations, 101 with >=3 samples.",
    ),
    "Alma, CO": (
        39.20, -106.20, 39.45, -105.95, None,
        "Arkansas River headwaters, Alma/Fairplay mining district. Probed "
        "2026-08-10: 472 Iron rows, 31 stations, 27 with >=3 samples.",
    ),
    "Leadville, CO": (
        39.15, -106.45, 39.35, -106.15, None,
        "Arkansas River headwaters, California Gulch Superfund site "
        "(different district from Alma, same river system). Probed "
        "2026-08-13: 1685 Iron rows, 83 stations, 72 with >=3 samples.",
    ),
    "Creede, CO": (
        37.75, -107.00, 37.95, -106.75, None,
        "Rio Grande headwaters, Creede mining district (Bulldog Mountain/"
        "Nelson Tunnel). Probed 2026-08-13: 438 Iron rows, 34 stations, "
        "21 with >=3 samples.",
    ),
    "Central City, CO": (
        39.65, -105.75, 39.85, -105.40, None,
        "South Platte River system, Clear Creek/Central City Superfund site. "
        "Probed 2026-08-13: 2317 Iron rows, 161 stations, 105 with >=3 "
        "samples - richest of the new regions.",
    ),
    "Lake City, CO": (
        37.90, -107.45, 38.15, -107.15, None,
        "Lake Fork of the Gunnison, Lake City mining district. Probed "
        "2026-08-13: 202 Iron rows, 13 stations, 11 with >=3 samples - "
        "thinnest of the new regions, may collapse to very few catchments.",
    ),
}


def overlay_path(data_dir):
    return os.path.join(data_dir, OVERLAY_FILENAME)


def load_overlay(data_dir):
    """Read <data_dir>/regions.json. Returns {} when absent or unreadable."""
    if not data_dir:
        return {}
    try:
        with open(overlay_path(data_dir), encoding="utf-8") as fh:
            raw = json.load(fh)
    except (IOError, OSError, ValueError):
        return {}
    out = {}
    for name, e in raw.items():
        try:
            out[name] = (float(e["lat_lo"]), float(e["lon_lo"]),
                         float(e["lat_hi"]), float(e["lon_hi"]),
                         e.get("site_types"),
                         e.get("note", "added via --bbox"))
        except (KeyError, TypeError, ValueError):
            continue          # a malformed entry is skipped, never fatal
    return out


def all_regions(data_dir=None):
    """Curated REGIONS plus the overlay. Curated entries win on conflict.

    Curated REGIONS plus the overlay in data_dir.
    """
    merged = dict(load_overlay(data_dir))
    merged.update(REGIONS)
    return merged


def save_overlay_entry(data_dir, name, lat_lo, lon_lo, lat_hi, lon_hi, note=""):
    """Add/replace one overlay region. Refuses to shadow a curated region."""
    if name in REGIONS:
        raise ValueError(
            "%r is a curated region; edit REGIONS in amdtool/regions.py to "
            "change it" % name)
    if not (-90 <= lat_lo < lat_hi <= 90):
        raise ValueError("need -90 <= lat_lo < lat_hi <= 90, got %s..%s"
                         % (lat_lo, lat_hi))
    if not (-180 <= lon_lo < lon_hi <= 180):
        raise ValueError("need -180 <= lon_lo < lon_hi <= 180, got %s..%s"
                         % (lon_lo, lon_hi))
    path = overlay_path(data_dir)
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (IOError, OSError, ValueError):
        raw = {}
    raw[name] = {"lat_lo": lat_lo, "lon_lo": lon_lo,
                 "lat_hi": lat_hi, "lon_hi": lon_hi,
                 "site_types": None,
                 "note": note or "added via --bbox"}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2, sort_keys=True)
    return path


def find_region(key, data_dir=None):
    """Region name or slug -> (name, entry). Raises UnknownRegionError."""
    regions = all_regions(data_dir)
    if key in regions:
        return key, regions[key]
    for name, entry in regions.items():
        if region_slug(name) == key:
            return name, entry
    raise UnknownRegionError(
        "Unknown region %r. Known: %s. To add one, register a bounding box "
        "(fetch_wqp.py --region \"<Name>, <ST>\" --bbox "
        "'lat_lo,lon_lo,lat_hi,lon_hi')." % (key, ", ".join(sorted(regions))))


def region_bbox(key, data_dir=None):
    """Region name or slug -> BBox."""
    return BBox.from_wqp(find_region(key, data_dir)[1])
