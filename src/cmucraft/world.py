"""Minecraft Java 1.16.5 Anvil writer. No existing worlds are read or edited."""
import io
import json
import math
import struct
import time
import zlib
from pathlib import Path
import numpy as np
import nbtlib as n


def packed(values,bits):
    """1.16 padded long layout: entries never straddle a 64-bit word."""
    values=np.asarray(values,dtype=np.uint64).ravel()
    per=64//bits
    padded=np.zeros(math.ceil(len(values)/per)*per,dtype=np.uint64)
    padded[:len(values)]=values
    words=np.bitwise_or.reduce(padded.reshape(-1,per)<<np.arange(0,per*bits,bits,dtype=np.uint64),axis=1)
    return n.LongArray(words.view(np.int64))


def block_state(state):
    if '[' not in state:
        return n.Compound({'Name':n.String(state)})
    name,props=state[:-1].split('[',1)
    return n.Compound({'Name':n.String(name),'Properties':n.Compound({k:n.String(v) for k,v in (p.split('=') for p in props.split(','))})})


def chunk_bytes(cx,cz,blocks,palette,signs):
    height=blocks.shape[0]
    sections=[]
    for sy in range(height//16):
        slab=blocks[sy*16:(sy+1)*16]
        unique,inverse=np.unique(slab,return_inverse=True)
        if len(unique)==1 and unique[0]==0:
            continue
        bits=max(4,(len(unique)-1).bit_length())
        sections.append(n.Compound({'Y':n.Byte(sy),
            'Palette':n.List[n.Compound]([block_state(palette[int(i)]) for i in unique]),
            'BlockStates':packed(inverse,bits)}))
    occupied=blocks!=0
    top=np.where(occupied.any(axis=0),height-np.argmax(occupied[::-1],axis=0),0)
    heightmaps=n.Compound({key:packed(top,9) for key in ('WORLD_SURFACE','MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES','OCEAN_FLOOR')})
    level=n.Compound({'xPos':n.Int(cx),'zPos':n.Int(cz),'Status':n.String('full'),
        'LastUpdate':n.Long(0),'InhabitedTime':n.Long(0),'isLightOn':n.Byte(0),
        'Sections':n.List[n.Compound](sections),'Biomes':n.IntArray([1]*1024),
        'Heightmaps':heightmaps,'Entities':n.List[n.Compound]([]),
        'TileEntities':n.List[n.Compound](signs),
        'TileTicks':n.List[n.Compound]([]),'LiquidTicks':n.List[n.Compound]([]),
        'PostProcessing':n.List[n.List[n.Short]]([n.List[n.Short]([]) for _ in range(16)]),
        'Structures':n.Compound({'Starts':n.Compound({}),'References':n.Compound({})})})
    out=io.BytesIO();n.File({'DataVersion':n.Int(2586),'Level':level}).write(out)
    return zlib.compress(out.getvalue(),6)


def level_file(path,spawn,size):
    flat=n.Compound({'type':n.String('minecraft:flat'),'settings':n.Compound({
        'biome':n.String('minecraft:plains'),'layers':n.List[n.Compound]([
            n.Compound({'height':n.Int(1),'block':n.String('minecraft:bedrock')}),
            n.Compound({'height':n.Int(31),'block':n.String('minecraft:stone')}),
            n.Compound({'height':n.Int(1),'block':n.String('minecraft:grass_block')})]),
        'structures':n.Compound({'structures':n.Compound({})})})})
    dimensions=n.Compound({'minecraft:overworld':n.Compound({'type':n.String('minecraft:overworld'),'generator':flat})})
    for dim in ('the_nether','the_end'):
        dimensions['minecraft:'+dim]=n.Compound({'type':n.String('minecraft:'+dim),'generator':n.Compound({
            'type':n.String('minecraft:noise'),'seed':n.Long(0),'settings':n.String('minecraft:'+dim),
            'biome_source':n.Compound({'type':n.String('minecraft:fixed'),'biome':n.String('minecraft:nether_wastes' if dim=='the_nether' else 'minecraft:the_end')})})})
    rules={'doDaylightCycle':'false','doWeatherCycle':'false','doMobSpawning':'false',
           'doFireTick':'false','randomTickSpeed':'0','keepInventory':'true'}
    data=n.Compound({'DataVersion':n.Int(2586),'version':n.Int(19133),
        'Version':n.Compound({'Id':n.Int(2586),'Name':n.String('1.16.5'),'Snapshot':n.Byte(0)}),
        'LevelName':n.String('CMUcraft - Pittsburgh Campus'),'GameType':n.Int(1),
        'allowCommands':n.Byte(1),'hardcore':n.Byte(0),'Difficulty':n.Byte(0),
        'initialized':n.Byte(1),'Time':n.Long(6000),'DayTime':n.Long(6000),
        'LastPlayed':n.Long(int(time.time()*1000)),
        'SpawnX':n.Int(spawn[0]),'SpawnY':n.Int(spawn[1]),'SpawnZ':n.Int(spawn[2]),
        'SpawnAngle':n.Float(180),'GameRules':n.Compound({k:n.String(v) for k,v in rules.items()}),
        'raining':n.Byte(0),'thundering':n.Byte(0),'clearWeatherTime':n.Int(100000000),
        'BorderCenterX':n.Double(size/2),'BorderCenterZ':n.Double(size/2),'BorderSize':n.Double(size-2),
        'WorldGenSettings':n.Compound({'seed':n.Long(0),'generate_features':n.Byte(0),'bonus_chest':n.Byte(0),'dimensions':dimensions}),
        'DataPacks':n.Compound({'Enabled':n.List[n.String](['vanilla']),'Disabled':n.List[n.String]([])})})
    n.File({'Data':data},gzipped=True).save(path/'level.dat')


def write_world(volume,palette,path,spawn,signs=(),extra_entities=()):
    path=Path(path)
    if (path/'level.dat').exists():
        raise ValueError('Refusing to overwrite an existing world; select a new output directory')
    (path/'region').mkdir(parents=True,exist_ok=True)
    size=volume.shape[1]; chunks=size//16
    entities={}
    for x,y,z,lines in signs:
        sign=n.Compound({'id':n.String('minecraft:sign'),'x':n.Int(x),'y':n.Int(y),'z':n.Int(z),'Color':n.String('black')})
        for i,line in enumerate(lines[:4]):sign[f'Text{i+1}']=n.String(json.dumps({'text':line}))
        entities.setdefault((x//16,z//16),[]).append(sign)
    occupied_entities={(int(e['x']),int(e['y']),int(e['z'])) for group in entities.values() for e in group}
    for entity in extra_entities:
        x,y,z=(int(entity[k]) for k in ('x','y','z'))
        if not (0<=x<size and 0<=z<size and 0<=y<volume.shape[0]):
            raise ValueError('Block entity outside exported volume')
        if (x,y,z) in occupied_entities:raise ValueError('Duplicate block entity position')
        occupied_entities.add((x,y,z))
        entities.setdefault((x//16,z//16),[]).append(entity)
    for rz in range(math.ceil(chunks/32)):
        for rx in range(math.ceil(chunks/32)):
            header=bytearray(8192); body=bytearray();sector=2
            for lz in range(32):
                for lx in range(32):
                    cx,cz=rx*32+lx,rz*32+lz
                    if cx>=chunks or cz>=chunks:continue
                    raw=chunk_bytes(cx,cz,volume[:,cz*16:(cz+1)*16,cx*16:(cx+1)*16],palette,entities.get((cx,cz),[]))
                    record=struct.pack('>I',len(raw)+1)+b'\x02'+raw
                    count=math.ceil(len(record)/4096)
                    if count>255:
                        # Java external chunk stream: a one-sector stub points to
                        # the unchanged zlib payload in c.<chunkX>.<chunkZ>.mcc.
                        (path/'region'/f'c.{cx}.{cz}.mcc').write_bytes(raw)
                        record=struct.pack('>I',1)+b'\x82';count=1
                    index=lx+lz*32
                    header[index*4:index*4+4]=((sector<<8)|count).to_bytes(4,'big')
                    body.extend(record);body.extend(bytes(count*4096-len(record)));sector+=count
            (path/'region'/f'r.{rx}.{rz}.mca').write_bytes(header+body)
    level_file(path,spawn,size)
    return chunks*chunks
