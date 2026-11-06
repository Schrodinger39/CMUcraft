import io,json,math,struct,zlib
from pathlib import Path
import numpy as np
import nbtlib
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('world',type=Path,nargs='?',default=Path('campus_artifacts/world'))
parser.add_argument('--expected-chunks',type=int,default=4096)
args=parser.parse_args();world=args.world
chunks=sections=0
for file in sorted((world/'region').glob('*.mca')):
 data=file.read_bytes(); used=set()
 for i in range(1024):
  entry=int.from_bytes(data[i*4:i*4+4],'big')
  if not entry:continue
  sector,count=entry>>8,entry&255
  assert sector>=2 and count>0
  allocated=set(range(sector,sector+count));assert not allocated & used;used|=allocated
  pos=sector*4096;length=int.from_bytes(data[pos:pos+4],'big');assert length+4<=count*4096
  compression=data[pos+4];assert compression in (2,130)
  if compression==130:
   assert length==1 and count==1
   _,rx,rz=file.stem.split('.')
   cx=int(rx)*32+i%32;cz=int(rz)*32+i//32
   payload=(file.parent/f'c.{cx}.{cz}.mcc').read_bytes()
  else:payload=data[pos+5:pos+4+length]
  f=nbtlib.File.parse(io.BytesIO(zlib.decompress(payload)))
  assert f['DataVersion']==2586
  l=f['Level'];assert l['Status']=='full'
  assert len(l['Biomes'])==1024
  assert int(l['xPos'])%32==i%32 and int(l['zPos'])%32==i//32
  for s in l['Sections']:
   bits=max(4,(len(s['Palette'])-1).bit_length());per=64//bits
   assert len(s['BlockStates'])==math.ceil(4096/per)
   words=np.asarray(s['BlockStates'],dtype=np.int64).view(np.uint64)
   values=((words[:,None]>>np.arange(0,per*bits,bits,dtype=np.uint64))&((1<<bits)-1)).ravel()[:4096]
   assert values.max()<len(s['Palette'])
   sections+=1
  chunks+=1
level=nbtlib.load(world/'level.dat')['Data'];assert chunks==args.expected_chunks
result={'chunks_decoded':chunks,'sections_decoded':sections,'region_files':len(list((world/'region').glob('*.mca'))),'all_palette_indices_valid':True,'all_region_records_nonoverlapping':True,'data_version':2586,'spawn':[int(level[k]) for k in ('SpawnX','SpawnY','SpawnZ')],'runtime_game_test':False}
print(json.dumps(result,indent=2))
