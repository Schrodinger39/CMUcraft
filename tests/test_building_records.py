"""Guard reference packets against wrong identities, swapped axes and stale snapshots."""
from pathlib import Path
import json,hashlib
import numpy as np
from shapely.geometry import shape
from cmucraft.campus import REGION,build_campus
from cmucraft.osm import parse
import pytest
ROOT=Path(__file__).parents[1]


def test_reference_coordinates_match_source():
    source=ROOT/'data/raw/campus.osm';fs,warnings=parse(source,separate_named_parts=True);assert not warnings
    by_id={f['id']:f for f in fs};checksum=hashlib.sha256(source.read_bytes()).hexdigest()
    for file in (ROOT/'data/reference/buildings').glob('*.json'):
        record=json.loads(file.read_text());original=by_id[record['osm_id']]
        assert original['tags']['name']==record['name']
        assert record['snapshot_sha256']==checksum
        assert shape(record['footprint_wgs84']).equals_exact(original['geometry'],1e-10)
        local=shape(record['footprint_xz'])
        assert local.equals_exact(REGION.local_geometry(original['geometry']),1e-6)
        assert np.allclose(record['utm_origin'],REGION.origin,atol=1e-6,rtol=0)
        assert abs(local.area-record['footprint_area_m2'])<0.001


def test_legacy_generator_requires_explicit_opt_in(tmp_path):
    with pytest.raises(ValueError,match='Legacy procedural'):
        build_campus(ROOT,tmp_path)
