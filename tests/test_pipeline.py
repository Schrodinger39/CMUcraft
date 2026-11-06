"""Synthetic geometry unit tests and real OSM integration checks (offline)."""
import hashlib
import json
from pathlib import Path
import numpy as np
import nbtlib
import pytest
from pyproj import Geod
from shapely.geometry import Polygon, box, shape
from cmucraft.geo import Region, rasterize
from cmucraft.osm import parse
from cmucraft.build import build
from cmucraft.schematic import export

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/raw/cmu.osm'


def test_origin_and_axis():
    r=Region(); assert r.xz(r.lon,r.lat)==pytest.approx((128,128))
    x,z=r.xz(r.lon+0.0001,r.lat); assert x>128
    x,z=r.xz(r.lon,r.lat+0.0001); assert z<128
    for p in [(0,0),(256,256),(73.5,101.5)]:
        assert r.xz(*r.lonlat(*p))==pytest.approx(p,abs=1e-7)


def test_independent_geodesic_scale():
    r=Region(); geod=Geod(ellps='WGS84')
    for bearing in range(0,360,30):
        lon,lat,_=geod.fwd(r.lon,r.lat,bearing,100)
        assert np.linalg.norm(np.subtract(r.xz(lon,lat),(128,128)))==pytest.approx(100,abs=0.04)


def test_rectangle_exact_area():
    mask=rasterize(box(10,20,30,50),64)
    assert mask.sum()==600
    assert mask[20,10] and mask[49,29] and not mask[50,30]


def test_hole_preserved():
    polygon=Polygon([(0,0),(10,0),(10,10),(0,10)],holes=[[(2,2),(8,2),(8,8),(2,8)]])
    mask=rasterize(polygon,16)
    assert mask.sum()==64 and not mask[5,5]


def test_clip_no_rescale():
    assert rasterize(box(-10,-10,10,10),16).sum()==100
    assert rasterize(box(20,20,30,30),16).sum()==0


def test_boundary_rule():
    assert not rasterize(box(0.5,0.5,1.5,1.5),4).any()


def test_multipolygon_disconnected():
    assert rasterize(box(0,0,2,2).union(box(5,5,7,7)),10).sum()==8


def test_region_guard():
    with pytest.raises(ValueError): Region(size=0)
    with pytest.raises(ValueError): Region(lon=0)


def test_real_source_hash_and_parse():
    meta=json.loads(SOURCE.with_suffix('.source.json').read_text())
    assert meta['source_kind']=='real_osm'
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==meta['sha256']
    features,warnings=parse(SOURCE)
    assert not warnings
    names={f['tags'].get('name') for f in features}
    assert {'Doherty Hall','Purnell Center for the Arts','Wean Hall','Gates and Hillman Centers'}<=names
    # Nested parent complex must not also include consumed child buildings.
    assert 'Gates Center for Computer Science' not in names
    assert all(f['geometry'].is_valid for f in features)


def test_missing_member_is_reported(tmp_path):
    p=tmp_path/'incomplete.osm'
    p.write_text('<osm><relation id="1"><member type="way" ref="99" role="outer"/>'
                 '<tag k="building" v="yes"/><tag k="type" v="multipolygon"/></relation></osm>')
    features,warnings=parse(p)
    assert not features and len(warnings)==1


def test_schematic_index_order(tmp_path):
    grid=np.zeros((8,8),dtype=np.uint16);grid[2,6]=1
    path=tmp_path/'test.schem';export(grid,path)
    file=nbtlib.load(path)
    assert file.root_name=='Schematic' and file['Version']==2
    assert list(file['Offset'])==[0,0,0]
    raw=np.asarray(file['BlockData'])
    assert len(raw)==128 and raw[6+2*8+64]==2
    assert raw[2+6*8+64]==0
    assert np.all(raw[:64]==1)
    assert len(file['Palette'])==file['PaletteMax']


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    dest=tmp_path_factory.mktemp('map')
    report=build(SOURCE,dest,Region())
    return dest,report


def test_real_build_distance_report(built):
    dest,report=built
    assert report['building_count']>=8 and report['distance_pair_count']>=28
    assert not report['parse_warnings']
    assert report['max_relative_projection_error']<0.0005
    assert report['max_centroid_quantization_error_m']<=2**0.5+1e-8
    assert 10000<report['occupied_cells']<40000
    assert report['clipped_count']>0


def test_geojson_coordinates_and_csv(built):
    dest,_=built
    data=json.loads((dest/'buildings.geojson').read_text())
    for f in data['features']:
        geom=shape(f['geometry']); assert geom.is_valid
        lon,lat=geom.representative_point().coords[0]
        assert -80<lon<-79 and 40<lat<41
    grid=np.load(dest/'grid.npy')
    rows=np.loadtxt(dest/'cells.csv',delimiter=',',skiprows=1,dtype=int)
    assert len(rows)==np.count_nonzero(grid)
    assert np.array_equal(grid[rows[:,1],rows[:,0]],rows[:,2])


def test_schematic_matches_real_grid(built):
    dest,_=built
    file=nbtlib.load(dest/'cmu_core.schem')
    blocks=np.asarray(file['BlockData']).reshape(2,256,256)
    grid=np.load(dest/'grid.npy')
    assert np.array_equal(blocks[1]==2,grid>0)


def test_source_integrity_guard(tmp_path):
    p=tmp_path/'bad.osm';p.write_text('<osm/>')
    p.with_suffix('.source.json').write_text('{"sha256":"bad"}')
    with pytest.raises(ValueError,match='SHA256'): build(p,tmp_path/'out',Region())


def test_expansion_requires_download(tmp_path):
    with pytest.raises(ValueError,match='bbox'): build(SOURCE,tmp_path/'out',Region(size=1024))


def test_architecture_keeps_named_gates_hillman_parts():
    features,warnings=parse(SOURCE,separate_named_parts=True)
    names={f['tags'].get('name') for f in features}
    assert not warnings
    assert 'Gates and Hillman Centers' not in names
    assert 'Gates Center for Computer Science' in names
    assert 'Hillman Center for Future Generation Technologies' in names

