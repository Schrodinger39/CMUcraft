import io
import math
import struct
import zlib
from pathlib import Path
import numpy as np
import nbtlib
import pytest
from cmucraft.world import packed,chunk_bytes,write_world,block_state
from cmucraft.campus import terrain,REGION,erode


def unpack(words,count,bits):
    words=np.asarray(words,dtype=np.int64).view(np.uint64)
    per=64//bits
    return np.array([(int(words[i//per])>>((i%per)*bits))&((1<<bits)-1) for i in range(count)])


@pytest.mark.parametrize('bits',[4,5,6,7,8,9,13])
def test_padded_longs(bits):
    values=np.arange(4096,dtype=np.uint64)%((1<<bits)-1)
    assert np.array_equal(unpack(packed(values,bits),4096,bits),values)


def test_real_terrain_registration():
    root=Path(__file__).resolve().parents[1]
    ground,elev,offset,meta=terrain(root/'data/raw/terrain.tif',REGION)
    assert ground.shape==(1024,1024)
    assert 200<float(elev.min())<300 and 300<float(elev.max())<400
    assert np.max(np.abs(ground+offset-elev))<=0.501
    assert meta['pixel_spacing_m']==4


def test_chunk_roundtrip_and_order():
    blocks=np.zeros((32,16,16),dtype=np.uint8);blocks[0]=1;blocks[19,3,7]=2
    raw=chunk_bytes(4,7,blocks,['minecraft:air','minecraft:bedrock','minecraft:stone'],[])
    f=nbtlib.File.parse(io.BytesIO(zlib.decompress(raw)))
    assert f['DataVersion']==2586
    l=f['Level'];assert l['xPos']==4 and l['zPos']==7
    s=l['Sections'][1];ids=unpack(s['BlockStates'],4096,4).reshape(16,16,16)
    assert str(s['Palette'][int(ids[3,3,7])]['Name'])=='minecraft:stone'
    heights=unpack(l['Heightmaps']['WORLD_SURFACE'],256,9).reshape(16,16)
    assert heights[3,7]==20 and heights[0,0]==1


def test_region_header_and_overwrite_guard(tmp_path):
    v=np.zeros((32,32,32),dtype=np.uint8);v[0]=1
    p=tmp_path/'world';write_world(v,['minecraft:air','minecraft:bedrock'],p,[8,2,8])
    data=(p/'region/r.0.0.mca').read_bytes()
    sectors=set()
    for i in [0,1,32,33]:
        loc=int.from_bytes(data[i*4:i*4+4],'big');start=loc>>8;count=loc&255
        assert start>=2 and count>0 and not(set(range(start,start+count))&sectors)
        sectors.update(range(start,start+count))
        pos=start*4096;length=struct.unpack('>I',data[pos:pos+4])[0]
        assert data[pos+4]==2 and length+4<=count*4096
        nbtlib.File.parse(io.BytesIO(zlib.decompress(data[pos+5:pos+4+length])))
    with pytest.raises(ValueError,match='overwrite'):write_world(v,['minecraft:air','minecraft:bedrock'],p,[8,2,8])
    assert nbtlib.load(p/'level.dat')['Data']['SpawnY']==2


def test_block_properties_and_edges():
    assert block_state('minecraft:oak_log[axis=y]')['Properties']['axis']=='y'
    mask=np.ones((5,5),dtype=bool)
    assert erode(mask).sum()==9
