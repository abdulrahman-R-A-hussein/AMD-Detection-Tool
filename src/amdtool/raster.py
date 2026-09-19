"""Score rasters: one index over a BBox as a GeoTIFF and a PNG preview.

Uses Earth Engine's synchronous download (getDownloadURL / getThumbURL), the
same mechanism as python/catchment_dem._fetch_band. That endpoint refuses
requests above ~32 MB, so the download scale is coarsened when the AOI is large
enough to exceed MAX_PIXELS_PER_SIDE. The scale actually used is returned and
must be reported: a coarsened raster is a display product, never the input to
any statistic (statistics are computed at native scale by extract_buffers).

Requires the `geo` extra (requests).
"""

import logging
import math

log = logging.getLogger(__name__)

# A 2,500 x 2,500 float32 GeoTIFF is ~25 MB, inside the ~32 MB request limit.
MAX_PIXELS_PER_SIDE = 2500

# Smallest PNG preview worth returning after halving on a memory error.
MIN_PNG_DIMENSIONS = 256

# A GeoTIFF small enough for the 32 MB request cap can still exceed Earth
# Engine's MEMORY limit, because the limit is about computing the composite
# behind it, not about the file. The first two-district run through SpectraLab
# (2026-09-19: 1,950 km2, 134 Landsat scenes) failed this way at 30 m while the
# statistics, computed per station buffer, had already succeeded. On that error
# the scale is doubled, up to this multiple of the scale first requested.
MAX_GEOTIFF_SCALE_FACTOR = 16

# Display palette: low -> high. Display only; it cannot change any value.
PALETTE = ["2c7bb6", "abd9e9", "ffffbf", "fdae61", "d7191c"]


def download_scale(bbox, native_m):
    """Smallest scale >= native_m that keeps both sides <= MAX_PIXELS_PER_SIDE."""
    lat_c = math.radians((bbox.lat_lo + bbox.lat_hi) / 2.0)
    width_m = (bbox.lon_hi - bbox.lon_lo) * 111320.0 * math.cos(lat_c)
    height_m = (bbox.lat_hi - bbox.lat_lo) * 110540.0
    needed = max(width_m, height_m) / MAX_PIXELS_PER_SIDE
    return float(max(native_m, math.ceil(needed)))


def display_range(ee, image, band, bbox, scale):
    """2nd and 98th percentile of the band over the AOI - for the PNG stretch only."""
    stats = image.select([band]).reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]), geometry=bbox.to_ee(ee),
        scale=max(scale, 60), maxPixels=1e9, bestEffort=True).getInfo()
    lo, hi = stats.get("%s_p2" % band), stats.get("%s_p98" % band)
    if lo is None or hi is None or hi <= lo:
        return None
    return float(lo), float(hi)


def _get(url, timeout):
    import requests
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError("Earth Engine download failed: %s %s"
                           % (resp.status_code, resp.content[:200]))
    return resp.content


def _write(path, content):
    """Write only a complete download. Opening the file first left a 0-byte
    file behind whenever the request failed (seen in the first live SpectraLab
    run, 2026-09-15)."""
    if not content:
        raise RuntimeError("Earth Engine returned an empty file for %s" % path)
    with open(path, "wb") as fh:
        fh.write(content)


def export_geotiff(ee, image, band, bbox, path, native_m, timeout=900):
    """Write one band as a GeoTIFF (EPSG:4326). Returns {"path", "scale_m"}.

    On Earth Engine's memory limit the scale is doubled and the request
    retried, up to MAX_GEOTIFF_SCALE_FACTOR times the starting scale - the same
    concession export_png makes with its dimensions. The scale actually used is
    returned and must be reported: a coarsened raster is a display product, and
    no statistic is ever computed from it.
    """
    scale = download_scale(bbox, native_m)
    ceiling = scale * MAX_GEOTIFF_SCALE_FACTOR
    while True:
        url = image.select([band]).getDownloadURL({
            "region": bbox.to_ee(ee), "scale": scale,
            "format": "GEO_TIFF", "crs": "EPSG:4326"})
        try:
            content = _get(url, timeout)
            break
        except RuntimeError as exc:
            if "memory" not in str(exc).lower() or scale * 2 > ceiling:
                raise
            scale *= 2.0
            log.info("raster memory limit - retrying at %d m", scale)
    _write(path, content)
    return {"path": path, "scale_m": scale}


def export_png(ee, image, band, bbox, path, native_m, dimensions=1024, timeout=300):
    """Write a colour PNG preview. Returns {"path", "min", "max", "dimensions"},
    or None if the band has no usable range over the AOI.

    Earth Engine renders the thumbnail from the whole composite, so a deep scene
    stack can exceed its memory limit. The first live run (103 Landsat scenes,
    391 km2) failed at 1024 px with "User memory limit exceeded" and succeeded at
    512. On that error the size halves, down to MIN_PNG_DIMENSIONS. The preview is
    display-only, so its size changes no number.
    """
    rng = display_range(ee, image, band, bbox, native_m)
    if rng is None:
        return None
    dims = dimensions
    while True:
        url = image.select([band]).getThumbURL({
            "region": bbox.to_ee(ee), "min": rng[0], "max": rng[1],
            "palette": PALETTE, "dimensions": dims, "format": "png"})
        try:
            content = _get(url, timeout)
            break
        except RuntimeError as exc:
            if "memory" not in str(exc).lower() or dims // 2 < MIN_PNG_DIMENSIONS:
                raise
            dims //= 2
            log.info("preview memory limit - retrying at %d px", dims)
    _write(path, content)
    return {"path": path, "min": rng[0], "max": rng[1], "dimensions": dims}
