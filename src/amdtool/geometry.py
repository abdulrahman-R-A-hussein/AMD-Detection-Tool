"""One bounding-box convention for the whole library.

The scripts used four: fetch_wqp (lat_lo, lon_lo, lat_hi, lon_hi),
cmd_confound (lon_lo, lat_lo, lon_hi, lat_hi), ee.Geometry.Rectangle
([lon_lo, lat_lo, lon_hi, lat_hi]), and point-plus-radius in the Earth Engine
tool. Every amdtool function takes a BBox and converts at the boundary, so the
order can never be silently swapped.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BBox:
    """WGS84 degrees. Field names, not positions, carry the meaning."""

    lat_lo: float
    lon_lo: float
    lat_hi: float
    lon_hi: float

    def __post_init__(self):
        if not (-90.0 <= self.lat_lo < self.lat_hi <= 90.0):
            raise ValueError("need -90 <= lat_lo < lat_hi <= 90, got %r..%r"
                             % (self.lat_lo, self.lat_hi))
        if not (-180.0 <= self.lon_lo < self.lon_hi <= 180.0):
            raise ValueError("need -180 <= lon_lo < lon_hi <= 180, got %r..%r"
                             % (self.lon_lo, self.lon_hi))

    # ---- construction --------------------------------------------------
    @classmethod
    def from_wqp(cls, entry):
        """From a fetch_wqp REGIONS-style tuple (lat_lo, lon_lo, lat_hi, lon_hi, ...)."""
        return cls(float(entry[0]), float(entry[1]), float(entry[2]), float(entry[3]))

    @classmethod
    def from_lonlat(cls, lon_lo, lat_lo, lon_hi, lat_hi):
        """From the lon-first order used by Earth Engine and cmd_confound."""
        return cls(float(lat_lo), float(lon_lo), float(lat_hi), float(lon_hi))

    @classmethod
    def from_geojson(cls, geojson):
        """Bounding box of any GeoJSON geometry, Feature or FeatureCollection."""
        xs, ys = [], []

        def walk(obj):
            if isinstance(obj, dict):
                t = obj.get("type")
                if t == "FeatureCollection":
                    for f in obj.get("features", []):
                        walk(f)
                elif t == "Feature":
                    walk(obj.get("geometry"))
                elif t == "GeometryCollection":
                    for g in obj.get("geometries", []):
                        walk(g)
                elif "coordinates" in obj:
                    walk(obj["coordinates"])
            elif isinstance(obj, (list, tuple)):
                if len(obj) >= 2 and all(isinstance(v, (int, float)) for v in obj[:2]):
                    xs.append(float(obj[0]))
                    ys.append(float(obj[1]))
                else:
                    for v in obj:
                        walk(v)

        walk(geojson)
        if not xs:
            raise ValueError("GeoJSON contains no coordinates")
        if min(xs) == max(xs) or min(ys) == max(ys):
            raise ValueError("GeoJSON has zero width or height - draw an area, "
                             "not a point or a line")
        return cls(min(ys), min(xs), max(ys), max(xs))

    # ---- conversion ----------------------------------------------------
    def to_ee(self, ee):
        return ee.Geometry.Rectangle([self.lon_lo, self.lat_lo,
                                      self.lon_hi, self.lat_hi])

    def to_wqp(self):
        return (self.lat_lo, self.lon_lo, self.lat_hi, self.lon_hi)

    # ---- queries -------------------------------------------------------
    def contains(self, lat, lon):
        return (self.lat_lo <= lat <= self.lat_hi
                and self.lon_lo <= lon <= self.lon_hi)

    @property
    def center(self):
        return ((self.lat_lo + self.lat_hi) / 2.0, (self.lon_lo + self.lon_hi) / 2.0)

    def area_km2(self):
        """Spherical approximation; good to well under 1% at these sizes."""
        r = 6371.0088
        dlon = math.radians(self.lon_hi - self.lon_lo)
        return (r * r * dlon
                * abs(math.sin(math.radians(self.lat_hi))
                      - math.sin(math.radians(self.lat_lo))))

    def grid(self, k):
        """k x k equal-degree tiles, ids 'r<row>c<col>' from the south-west.

        Outcome-blind grouping for within-group permutation and sign
        consistency - the same logic as CMD3's disjoint tiles.
        """
        if k < 1:
            raise ValueError("k must be >= 1")
        dlat = (self.lat_hi - self.lat_lo) / k
        dlon = (self.lon_hi - self.lon_lo) / k
        tiles = {}
        for r in range(k):
            for c in range(k):
                tiles["r%dc%d" % (r, c)] = BBox(
                    self.lat_lo + r * dlat, self.lon_lo + c * dlon,
                    self.lat_lo + (r + 1) * dlat, self.lon_lo + (c + 1) * dlon)
        return tiles

    def tile_of(self, lat, lon, k):
        """Tile id for a point, or None if the point is outside the box.

        Points exactly on the northern or eastern edge fall in the last tile,
        so every point inside the box belongs to exactly one tile.
        """
        if not self.contains(lat, lon):
            return None
        r = min(k - 1, int((lat - self.lat_lo) / (self.lat_hi - self.lat_lo) * k))
        c = min(k - 1, int((lon - self.lon_lo) / (self.lon_hi - self.lon_lo) * k))
        return "r%dc%d" % (r, c)
