import numpy as np
import pytest
from cmucraft.chisel import encode,decode_geometry


def test_detail_orientation_and_palette_survive_encoding():
    a=np.zeros((16,16,16),dtype=np.uint8);a[:,14:,:]=2;a[:,2:14,7:9]=1
    block,nbt=encode(a,['minecraft:air','minecraft:iron_block','minecraft:glass'],(11,70,24))
    ids,palette=decode_geometry(nbt)
    assert block in ('chiselsandbits:chiselediron','chiselsandbits:chiseledglass')
    assert palette[ids[5,8,7]]=='minecraft:iron_block'
    assert palette[ids[5,15,2]]=='minecraft:glass'
    assert palette[ids[5,2,2]]=='minecraft:air'
    assert int(nbt['chiselBlockData']['statistics']['blockCount'])==np.count_nonzero(a)
    assert (int(nbt['x']),int(nbt['y']),int(nbt['z']))==(11,70,24)


def test_unknown_emissive_material_requires_properties():
    with pytest.raises(ValueError,match='Unsupported'):
        encode(np.ones((16,16,16),dtype=np.uint8),['minecraft:air','minecraft:glowstone'],(0,0,0))
