"""Fit a raised rectangular hip above a flat roof using 2024 surface candidates.
Coordinate descent is deterministic. Held-out cells evaluate fitting residuals,
not absolute survey accuracy. Input must use the shared 1024 m campus grid."""

import json, argparse, numpy as np
from shapely.geometry import shape
from shapely import contains_xy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--surface", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
r = json.loads((root / "data/reference/buildings/hunt-library.json").read_text())
g = shape(r["footprint_xz"])
p = np.array(g.exterior.coords)
o = p[0]
u = p[3] - o
u /= np.linalg.norm(u)
v = np.array([-u[1], u[0]])
a = np.load(args.surface)
z, x = np.indices(a.shape)
m = contains_xy(g.buffer(-2), x + 0.5, z + 0.5) & np.isfinite(a) & (a > 309) & (a < 318)
xy = np.column_stack([x[m] + 0.5, z[m] + 0.5]) - o
uu = xy @ u
vv = xy @ v
obs = a[m]
train = ((x[m] + 2 * z[m]) % 5) != 0


# Physical model: flat lower roof, raised rectangular penthouse, four hip planes.
def pred(q, U=uu, V=vv):
    """Evaluate the lower deck or the nearest of four sloped hip planes at local samples."""
    l, r, t, b, e, s = q
    d = np.minimum.reduce([U - l, r - U, V - t, b - V])
    return np.where(d >= 0, e + s * d, 310.0)


def loss(q):
    """Compute clipped squared residuals on training cells only; limit outlier influence."""
    return np.mean(np.minimum((pred(q)[train] - obs[train]) ** 2, 4))


q = np.array([5.0, 56.0, 6.0, 29.0, 313.8, 0.18])
best = loss(q)
for step in [1, 0.5, 0.25, 0.125]:
    for loop in range(12):
        changed = False
        for i in range(6):
            delta = step if i < 5 else step * 0.03
            for sign in [-1, 1]:
                candidate = q.copy()
                candidate[i] += sign * delta
                l = loss(candidate)
                if l < best:
                    q = candidate
                    best = l
                    changed = True
        if not changed:
            break
error = np.abs(pred(q) - obs)
out = {
    "model": "raised rectangular hipped roof above flat lower deck",
    "source": "PASDA USGS 2024 surface candidates",
    "basis_origin_xz": o.tolist(),
    "basis_u": u.tolist(),
    "basis_v": v.tolist(),
    "hip_u_min_max_m": q[:2].tolist(),
    "hip_v_min_max_m": q[2:4].tolist(),
    "hip_eave_elevation_m": q[4],
    "hip_slope": q[5],
    "lower_roof_elevation_m": 310.0,
    "held_out_cells": int((~train).sum()),
    "held_out_median_absolute_error_m": float(np.median(error[~train])),
    "held_out_p95_absolute_error_m": float(np.percentile(error[~train], 95)),
    "approved": False,
    "limits": [
        "Model does not include mechanical equipment or roof seams",
        "Facade dimensions require separate review",
        "Fitted surface cannot independently certify original footprint accuracy",
    ],
}
args.output.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
