"""Experimental Chisels & Bits 1.0.63 block-entity writer.

The storage layout was inspected in the pinned upstream JAR. Runtime round-trip
validation is still required before any generated detail goes into a release.
Only non-emissive concrete/stone, iron and glass are supported here.
"""
import numpy as np
import nbtlib as n
from .world import block_state,packed

MATERIALS={
 'minecraft:air':('air',False),
 'minecraft:iron_block':('iron',True),
 'minecraft:white_concrete':('rock',True),
 'minecraft:gray_concrete':('rock',True),
 'minecraft:light_gray_concrete':('rock',True),
 'minecraft:black_concrete':('rock',True),
 'minecraft:brown_terracotta':('rock',True),
 'minecraft:sandstone':('rock',True),
 'minecraft:stone_bricks':('rock',True),
 'minecraft:black_stained_glass':('glass',False),
 'minecraft:glass':('glass',False),
}


def encode(bits,palette,position):
    bits=np.asarray(bits)
    if bits.shape!=(16,16,16):raise ValueError('Expected Y/Z/X 16-cubed detail grid')
    if not np.issubdtype(bits.dtype,np.integer) or bits.min()<0 or bits.max()>=len(palette):raise ValueError('Invalid material index')
    if palette[0]!='minecraft:air' or any(p not in MATERIALS for p in palette):raise ValueError('Unsupported material properties')
    ids,inverse,counts=np.unique(bits,return_inverse=True,return_counts=True)
    used=[(int(i),int(count)) for i,count in zip(ids,counts) if i!=0]
    if not used:raise ValueError('Empty details must be ordinary air')
    primary=max(used,key=lambda pair:pair[1])[0]
    opaque=np.array([MATERIALS[p][1] for p in palette])[bits]
    columns=[]
    for y,z,x in np.argwhere(opaque):
        columns.append(n.Compound({'coordinate':n.Compound({'xCoordinate':n.Int(x),'yCoordinate':n.Int(z)}),'value':n.Int(y)}))
    # Non-emissive materials use standard friction. Statistics remain a runtime
    # compatibility check, not proof that Forge has accepted this block entity.
    statistics=n.Compound({
      'primaryState':block_state(palette[primary]),
      'blockStates':n.List[n.Compound]([n.Compound({'blockState':block_state(palette[i]),'count':n.Int(count)}) for i,count in used]),
      'columnBlockList':n.List[n.Compound](columns),'blockCount':n.Int(int(np.count_nonzero(bits))),
      'blockShouldCheckWeakPowerCount':n.Int(int(opaque.sum())),
      'totalUpperLevelSlipperiness':n.Float(float(np.count_nonzero(bits[-1]))*.6),'totalLightLevel':n.Int(0)})
    storage=n.Compound({'palette':n.List[n.Compound]([block_state(palette[int(i)]) for i in ids]),
      'blockStates':packed(inverse,max(4,(len(ids)-1).bit_length()))})
    x,y,z=position
    entity=n.Compound({'id':n.String('chiselsandbits:chiseled'),'x':n.Int(x),'y':n.Int(y),'z':n.Int(z),
      'chiselBlockData':n.Compound({'compressedStorage':storage,'statistics':statistics})})
    return 'chiselsandbits:chiseled'+MATERIALS[palette[primary]][0],entity


def decode_geometry(entity):
    """Independent read-back for coordinate/material tests; not a Forge integration test."""
    storage=entity['chiselBlockData']['compressedStorage'];palette=storage['palette'];bits=max(4,(len(palette)-1).bit_length());per=64//bits
    words=np.asarray(storage['blockStates'],dtype=np.int64).view(np.uint64)
    ids=((words[:,None]>>np.arange(0,per*bits,bits,dtype=np.uint64))&((1<<bits)-1)).ravel()[:4096]
    if ids.max()>=len(palette):raise ValueError('Palette overrun')
    return ids.reshape(16,16,16),[str(p['Name']) for p in palette]
