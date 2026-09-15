"""Score rasters: one index over a BBox as a GeoTIFF and a PNG preview.

Uses Earth Engine's synchronous download (getDownloadURL / getThumbURL), the
same mechanism as python/catchment_dem._fetch_band. That endpoint refuses
requests above ~32 MB, so the download scale is coarsened when the AOI is large
enough to exceed MAX_PIXELS_PER_SIDE. The scale actually used is returned and
must be reported: a coarsened raster is a display product, never the input to
any statistic (statistics are computed at native scale by extract_buffers).

Requires the `geo` extra (requests).
"""

import math

# A 2,500 x 2,500 float32 GeoTIFF is ~25 MB, inside the ~32 MB request limit.
MAX_PIXELS_PER_SIDE = 2500

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


def export_geotiff(ee, image, band, bbox, path, native_m, timeout=900):
    """Write one band as a GeoTIFF (EPSG:4326). Returns {"path", "scale_m"}."""
    scale = download_scale(bbox, native_m)
    url = image.select([band]).getDownloadURL({
        "region": bbox.to_ee(ee), "scale": scale,
        "format": "GEO_TIFF", "crs": "EPSG:4326"})
    with open(path, "wb") as fh:
        fh.write(_get(url, timeout))
    return {"path": path, "scale_m": scale}


def export_png(ee, image, band, bbox, path, native_m, dimensions=1024, timeout=300):
    """Write a colour PNG preview. Returns {"path", "min", "max"} or None if the
    band has no usable range over the AOI."""
    rng = display_range(ee, image, band, bbox, native_m)
    if rng is None:
        return None
    url = image.select([band]).getThumbURL({
        "region": bbox.to_ee(ee), "min": rng[0], "max": rng[1],
        "palette": PALETTE, "dimensions": dimensions, "format": "png"})
    with open(path, "wb") as fh:
        fh.write(_get(url, timeout))
    return {"path": path, "min": rng[0], "max": rng[1]}
