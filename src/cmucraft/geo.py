"""Geographic coordinates -> UTM 17N metres -> Minecraft X/Z."""
from dataclasses import dataclass
from math import floor, ceil
import numpy as np
from pyproj import Transformer
from shapely import contains_xy, transform
from shapely.geometry import box

FORWARD = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
INVERSE = Transformer.from_crs("EPSG:32617", "EPSG:4326", always_xy=True)

@dataclass(frozen=True)
class Region:
    lon: float = -79.9442
    lat: float = 40.4431
    size: int = 256

    def __post_init__(self):
        if not 1 <= self.size <= 2048:
            raise ValueError("size must be 1..2048 metres; tile larger projects")
        if not (-84 <= self.lon < -78 and 0 <= self.lat < 84):
            raise ValueError("This project uses northern UTM zone 17 (EPSG:32617)")

    @property
    def origin(self):
        e, n = FORWARD.transform(self.lon, self.lat)
        return e - self.size / 2, n + self.size / 2

    def xz(self, lon, lat):
        e, n = FORWARD.transform(lon, lat)
        west, north = self.origin
        return e - west, north - n

    def lonlat(self, x, z):
        west, north = self.origin
        return INVERSE.transform(west + x, north - z)

    def local_geometry(self, geometry):
        return transform(geometry, lambda xy: np.column_stack(self.xz(xy[:,0],xy[:,1])))

    def geographic_geometry(self, geometry):
        return transform(geometry, lambda xz: np.column_stack(self.lonlat(xz[:,0],xz[:,1])))

    @property
    def extent(self):
        return box(0, 0, self.size, self.size)

    def download_bbox(self, margin=100):
        coords = [self.lonlat(x,z) for x in (-margin,self.size+margin)
                  for z in (-margin,self.size+margin)]
        return (min(p[0] for p in coords), min(p[1] for p in coords),
                max(p[0] for p in coords), max(p[1] for p in coords))


def rasterize(geometry, size):
    """Select cells whose centres are strictly inside; boundary-centres excluded.

    Never stretch geometry. Narrow/sub-metre details may disappear. Holes remain.
    Work in polygon bounding boxes to avoid full-grid geometry allocations.
    """
    mask = np.zeros((size, size), dtype=bool)
    if geometry.is_empty:
        return mask
    a,b,c,d = geometry.bounds
    x0,z0 = max(0,floor(a)),max(0,floor(b))
    x1,z1 = min(size,ceil(c)),min(size,ceil(d))
    if x1 <= x0 or z1 <= z0:
        return mask
    x,z = np.meshgrid(np.arange(x0,x1)+0.5,np.arange(z0,z1)+0.5)
    mask[z0:z1,x0:x1] = contains_xy(geometry,x,z)
    return mask
