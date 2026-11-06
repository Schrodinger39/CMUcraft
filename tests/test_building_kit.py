"""Offline storage safety tests; synthetic saves do not certify Forge behavior."""
import copy
import json
from pathlib import Path
import shutil
import zlib

import nbtlib as n
import numpy as np
import pytest

from cmucraft import building_kit as k
from cmucraft.chisel import encode
from cmucraft.world import write_world, chunk_bytes


@pytest.fixture
def kit(tmp_path):
    root = tmp_path/'repo'
    (root/'data/reference/buildings').mkdir(parents=True)
    (root/'campus_artifacts').mkdir()
    (root/'modpack').mkdir()
    k.write_json(root/'data/reference/buildings/demo.json', {
        'name': 'Test Building', 'utm_origin': [1, 2],
        'footprint_xz': {'type': 'Polygon', 'coordinates': [[[1,1],[10,1],[10,10],[1,10],[1,1]]]}})
    k.write_json(root/'campus_artifacts/manifest.json', {'region': {'utm_origin': [1,2]}, 'vertical_offset_m': 208})
    k.write_json(root/'modpack/modrinth.index.json', {})
    for name in ('LICENSE', 'DATA_LICENSE.md'):
        (root/name).write_text('Test fixture')
    base = tmp_path/'base'
    v = np.zeros((32,32,32), dtype=np.uint8)
    v[0] = 1
    write_world(v, ['minecraft:air', 'minecraft:bedrock'], base, [2,2,2])
    m = k.create_kit(root, 'demo', base, tmp_path/'kit', 2)
    source = tmp_path/'kit/starter-world'
    return root, base, source, m


def test_kit_and_identity(kit, tmp_path):
    root, base, source, m = kit
    assert m['chunks'] == [[0,0]] and m['translation_xyz'] == [0,0,0]
    assert (source.parent/'footprint.png').exists()
    assert (source.parent.with_suffix('.zip')).exists()
    assert n.load(source/'level.dat')['Data']['BorderSize'] == 16
    plan = k.plan_import(base, source, m)
    k.stage_import(base, source, m, tmp_path/'result', plan)
    assert k.selected(base, [[0,0]]) == k.selected(tmp_path/'result', [[0,0]])


def test_chiseled_payload_and_neighbors_preserved(kit, tmp_path):
    _, base, source, m = kit
    bits = np.zeros((16,16,16), dtype=np.uint8)
    bits[1:7,2:11,4:8] = 1
    state, entity = encode(bits, ['minecraft:air','minecraft:iron_block'], (3,4,5))
    blocks = np.zeros((32,16,16), dtype=np.uint8)
    blocks[4,5,3] = 1
    records = k.region_records(source/'region',0,0)
    payload = chunk_bytes(0,0,blocks,['minecraft:air',state],[entity])
    records[(0,0)] = (2,payload,b'\0'*4)
    k.write_region(source/'region',0,0,records)
    before = k.region_records(base/'region',0,0)
    plan = k.plan_import(base, source, m)
    k.stage_import(base,source,m,tmp_path/'result',plan)
    after = k.region_records(tmp_path/'result/region',0,0)
    assert after[(0,0)][1] == payload
    assert after[(1,0)] == before[(1,0)]
    assert k.region_records(base/'region',0,0) == before
    assert k.chunk_nbt(after[(0,0)],0,0)['Level']['TileEntities'][0] == entity


def test_external_stream_and_negative_region(tmp_path):
    # Incompressible synthetic payload exercises .mcc, independently of mod NBT.
    payload = bytes(np.random.default_rng(4).integers(0,256,1_100_000,dtype=np.uint8))
    records = {(-1,-33): (2,payload,b'\0'*4)}
    k.write_region(tmp_path,-1,-2,records)
    assert (tmp_path/'c.-1.-33.mcc').read_bytes() == payload
    assert k.region_records(tmp_path,-1,-2) == records
    k.write_region(tmp_path,-1,-2,{(-1,-33):(2,b'short',b'\0'*4)})
    assert not (tmp_path/'c.-1.-33.mcc').exists()


def test_conflict_missing_global_and_stale_review(kit,tmp_path):
    _,base,source,m = kit
    plan = k.plan_import(base,source,m)
    changed = copy.deepcopy(plan)
    changed['building_id'] = 'other'
    with pytest.raises(ValueError,match='Plan changed'):
        k.stage_import(base,source,m,tmp_path/'result',changed)
    assert not (tmp_path/'result').exists()
    records = k.region_records(base/'region',0,0)
    original = records[(0,0)]
    records[(0,0)] = (2,zlib.compress(zlib.decompress(original[1]),0),original[2])
    k.write_region(base/'region',0,0,records)
    with pytest.raises(ValueError,match='Target conflict'):
        k.plan_import(base,source,m)
    records[(0,0)] = original
    k.write_region(base/'region',0,0,records)
    (source/'mod-data.dat').write_bytes(b'unknown global data')
    with pytest.raises(ValueError,match='Global'):
        k.plan_import(base,source,m)
    (source/'mod-data.dat').unlink()
    records = k.region_records(source/'region',0,0)
    del records[(0,0)]
    k.write_region(source/'region',0,0,records)
    with pytest.raises(ValueError,match='missing chunk'):
        k.plan_import(base,source,m)


def test_poi_delete_and_output_guards(kit,tmp_path):
    _,base,source,m = kit
    k.write_region(base/'poi',0,0,{(0,0):(3,b'opaque-poi',b'\0'*4),(1,0):(3,b'neighbor',b'\0'*4)})
    m['baseline']['poi']['0,0'] = k.fingerprint(k.selected(base,[[0,0]],'poi')[(0,0)])
    plan = k.plan_import(base,source,m)
    with pytest.raises(ValueError,match='new output'):
        k.stage_import(base,source,m,base/'nested',plan)
    k.stage_import(base,source,m,tmp_path/'result',plan)
    assert k.region_records(tmp_path/'result/poi',0,0) == {(1,0):(3,b'neighbor',b'\0'*4)}


def test_invalid_storage_and_coordinates(tmp_path):
    (tmp_path/'r.0.0.mca').write_bytes(bytes(100))
    with pytest.raises(ValueError,match='Truncated'):
        k.region_records(tmp_path,0,0)
    payload = chunk_bytes(0,0,np.zeros((16,16,16),dtype=np.uint8),['minecraft:air'],[])
    with pytest.raises(ValueError,match='coordinate'):
        k.chunk_nbt((2,payload,b'\0'*4),1,0)
    with pytest.raises(ValueError,match='decompressed'):
        k.chunk_nbt((2,payload[:-3],b'\0'*4),0,0)


def test_wrong_version_symlink_and_manifest(kit,tmp_path):
    _,base,source,m = kit
    bad = copy.deepcopy(m)
    bad['translation_xyz'] = [1,0,0]
    with pytest.raises(ValueError,match='untranslated'):
        k.plan_import(base,source,bad)
    (source/'linked').symlink_to(base/'level.dat')
    with pytest.raises(ValueError,match='Symlinks'):
        k.plan_import(base,source,m)
    (source/'linked').unlink()
    level = n.load(source/'level.dat')
    level['Data']['DataVersion'] = n.Int(2865)
    level.save(source/'level.dat')
    with pytest.raises(ValueError,match='1.16.5'):
        k.plan_import(base,source,m)


def test_zip_quarantine(tmp_path):
    import zipfile
    archive = tmp_path/'submission.zip'
    for name in ('../escape', '/absolute', 'C:/drive', 'world\\file'):
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr(name,b'bad')
        with pytest.raises(ValueError,match='Unsafe'):
            k.unpack_submission(archive,tmp_path/'out')
        assert not (tmp_path/'out').exists()
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('world/level.dat',b'fixture')
    with pytest.raises(ValueError,match='limits'):
        k.unpack_submission(archive,tmp_path/'out',max_bytes=3)
    k.unpack_submission(archive,tmp_path/'out')
    assert (tmp_path/'out/world/level.dat').read_bytes() == b'fixture'


def test_real_external_nbt_and_cross_region_neighbors(tmp_path):
    # Actual valid 1.16 chunk NBT containing incompressible extra mod data.
    raw = chunk_bytes(31,32,np.zeros((16,16,16),dtype=np.uint8),['minecraft:air'],[])
    obj = k.chunk_nbt((2,raw,b'\0'*4),31,32)
    obj['Level']['TestOpaqueModData'] = n.ByteArray(
        np.random.default_rng(7).integers(-128,128,1_100_000,dtype=np.int8))
    import io
    stream = io.BytesIO()
    obj.write(stream)
    payload = zlib.compress(stream.getvalue())
    k.write_region(tmp_path,0,1,{(31,32):(2,payload,b'\0'*4)})
    read = k.region_records(tmp_path,0,1)[(31,32)]
    assert (tmp_path/'c.31.32.mcc').exists()
    assert k.chunk_nbt(read,31,32) == obj
    (tmp_path/'c.31.32.mcc').unlink()
    with pytest.raises(FileNotFoundError):
        k.region_records(tmp_path,0,1)


def test_worldgen_mismatch_and_output_overwrite(kit,tmp_path):
    root,base,source,m = kit
    with pytest.raises(ValueError,match='already exists'):
        k.create_kit(root,'demo',base,source.parent,2)
    level = n.load(source/'level.dat')
    level['Data']['WorldGenSettings']['seed'] = n.Long(123)
    level.save(source/'level.dat')
    with pytest.raises(ValueError,match='generation settings'):
        k.plan_import(base,source,m)


def test_runtime_global_normalization_is_narrow(tmp_path):
    a,b=tmp_path/'a',tmp_path/'b'
    for folder,tick,map_id in ((a,10,1),(b,999,-42)):
        (folder/'data').mkdir(parents=True)
        n.File({'DataVersion':n.Int(2586),'data':n.Compound({
            'Raids':n.List[n.Compound]([]),'NextAvailableID':n.Int(1),'Tick':n.Int(tick)})},gzipped=True).save(folder/'data/raids.dat')
        (folder/'xaeromap.txt').write_text(f'id:{map_id}\n')
    assert k.global_files(a)==k.global_files(b)
    raid=n.load(b/'data/raids.dat')
    raid['data']['NextAvailableID']=n.Int(2)
    raid.save(b/'data/raids.dat')
    assert k.global_files(a)!=k.global_files(b)
    (b/'xaeromap.txt').write_text('id:1\nunknown:data')
    assert 'xaeromap.txt' in k.global_files(b)


def test_worldgen_key_order_is_not_a_conflict(kit):
    _,base,source,m=kit
    level=n.load(source/'level.dat')
    old=level['Data']['WorldGenSettings']
    level['Data']['WorldGenSettings']=n.Compound(dict(reversed(list(old.items()))))
    level.save(source/'level.dat')
    k.plan_import(base,source,m)


def test_empty_runtime_region_is_not_a_truncated_record(tmp_path):
    (tmp_path/'r.0.0.mca').touch()
    assert k.region_records(tmp_path,0,0)=={}
    (tmp_path/'r.0.0.mca').write_bytes(b'\0')
    with pytest.raises(ValueError,match='Truncated'):
        k.region_records(tmp_path,0,0)


def test_trial_base_removes_player_identity(kit,tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('first_pack',Path(__file__).resolve().parents[1]/'scripts/build_first_contributor_pack.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _,base,_,_=kit
    (base/'playerdata').mkdir()
    (base/'playerdata/private.dat').write_bytes(b'private')
    (base/'level.dat_old').write_bytes(b'private')
    level=n.load(base/'level.dat')
    level['Data']['Player']=n.Compound({'name':n.String('private')})
    level['Data']['WanderingTraderId']=n.String('private')
    level.save(base/'level.dat')
    module.sanitize_base(base,tmp_path/'clean')
    assert not (tmp_path/'clean/playerdata').exists()
    assert not (tmp_path/'clean/level.dat_old').exists()
    data=n.load(tmp_path/'clean/level.dat')['Data']
    assert 'Player' not in data and 'WanderingTraderId' not in data
    assert (base/'playerdata/private.dat').exists()
