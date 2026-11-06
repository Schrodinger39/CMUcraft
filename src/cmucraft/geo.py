"""Coordinate conventions: input is WGS84 longitude/latitude in degrees.
Projection is UTM 17N in metres; local X increases east and Z increases south.
A mask is indexed [z, x], never [x, z]. Clipping never rescales a building."""

from dataclasses import dataclass
from math import floor, ceil
import numpy as np
from pyproj import Transformer
from shapely import contains_xy, transform
from shapely.geometry import box

# always_xy keeps longitude/easting first even when a CRS advertises another axis order.
FORWARD = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
INVERSE = Transformer.from_crs("EPSG:32617", "EPSG:4326", always_xy=True)


@dataclass(frozen=True)
class Region:
    """A square local survey extent centered on WGS84 longitude/latitude.

    size is the edge length in metres; origin is its northwest UTM corner."""

    lon: float = -79.9442
    lat: float = 40.4431
    size: int = 256

    def __post_init__(self):
        """Reject unsupported extents or coordinates outside northern UTM zone 17."""
        if not 1 <= self.size <= 2048:
            raise ValueError("size must be 1..2048 metres; tile larger projects")
        if not (-84 <= self.lon < -78 and 0 <= self.lat < 84):
            raise ValueError("This project uses northern UTM zone 17 (EPSG:32617)")

    @property
    def origin(self):
        """Return (west easting, north northing) in UTM metres for the local origin."""
        e, n = FORWARD.transform(self.lon, self.lat)
        # The northwest corner lies west and north of the projected center.
        return e - self.size / 2, n + self.size / 2

    def xz(self, lon, lat):
        """Project degrees to local metres; subtract northing so Minecraft Z points south."""
        e, n = FORWARD.transform(lon, lat)
        west, north = self.origin
        # Reversing northing is intentional: positive Z goes south in Minecraft.
        return e - west, north - n

    def lonlat(self, x, z):
        """Invert local metre coordinates to WGS84 (longitude, latitude)."""
        west, north = self.origin
        return INVERSE.transform(west + x, north - z)

    def local_geometry(self, geometry):
        """Transform all Shapely coordinate pairs from degrees into local X/Z metres."""
        return transform(
            geometry, lambda xy: np.column_stack(self.xz(xy[:, 0], xy[:, 1]))
        )

    def geographic_geometry(self, geometry):
        """Transform local geometry back to degrees for geographic GeoJSON output."""
        return transform(
            geometry, lambda xz: np.column_stack(self.lonlat(xz[:, 0], xz[:, 1]))
        )

    @property
    def extent(self):
        """Return the local square clipping polygon, from zero to size on each axis."""
        return box(0, 0, self.size, self.size)

    def download_bbox(self, margin=100):
        """Return a WGS84 bounding box with a metre margin for complete nearby ways."""
        coords = [
            self.lonlat(x, z)
            for x in (-margin, self.size + margin)
            for z in (-margin, self.size + margin)
        ]
        return (
            min(p[0] for p in coords),
            min(p[1] for p in coords),
            max(p[0] for p in coords),
            max(p[1] for p in coords),
        )


def rasterize(geometry, size):
    """Select cells whose centres are strictly inside; boundary-centres excluded.

    Never stretch geometry. Narrow/sub-metre details may disappear. Holes remain.
    Work in polygon bounding boxes to avoid full-grid geometry allocations.
    """
    mask = np.zeros((size, size), dtype=bool)
    if geometry.is_empty:
        return mask
    a, b, c, d = geometry.bounds
    x0, z0 = max(0, floor(a)), max(0, floor(b))
    x1, z1 = min(size, ceil(c)), min(size, ceil(d))
    if x1 <= x0 or z1 <= z0:
        return mask
    # Test centers, not corners; exact boundary centers are excluded by contains_xy.
    x, z = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(z0, z1) + 0.5)
    mask[z0:z1, x0:x1] = contains_xy(geometry, x, z)
    return mask
