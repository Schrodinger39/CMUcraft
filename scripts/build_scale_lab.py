"""Generate a labelled human-scale comparison world; not a CMU building replica."""
from pathlib import Path
import argparse
import numpy as np
from cmucraft.world import write_world
from cmucraft.campus import PALETTE,ID

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('build/scale-lab'));args=p.parse_args()
volume=np.zeros((64,64,64),dtype=np.uint8)
volume[0]=ID['bedrock'];volume[1:31]=ID['stone'];volume[31]=ID['smooth_stone']
signs=[]
for idx,s in enumerate([1,1.5,2]):
 x=4+idx*20;z=24;w=round(6*s);h=round(4*s);depth=round(8*s)
 # Identical nominal 6m x 8m x 4m room, three candidate world scales.
 volume[32:32+h,z:z+depth,x:x+w]=ID['sandstone']
 volume[32:31+h,z+1:z+depth-1,x+1:x+w-1]=0
 doorw=max(1,round(s));doorh=round(2*s)
 volume[32:32+doorh,z,x+w//2:x+w//2+doorw]=0
 volume[32+h,z:z+depth,x:x+w]=ID['glass']
 signs.append((x,32,z-3,[f'{s:g} blocks / m',f'Door {doorh} blocks',f'Avatar scale {s:g}','Calibration only']))
 volume[32,z-3,x]=ID['oak_sign[rotation=0,waterlogged=false]']
 # Measured 10m baseline for each scale.
 for dx in range(round(10*s)):
  volume[31,45,x+dx]=ID['white_wool'] if dx%2==0 else ID['gray_concrete']
write_world(volume,PALETTE,args.output,[32,33,15],signs)
import nbtlib as n
f=n.load(args.output/'level.dat');f['Data']['LevelName']=n.String('CMUcraft - Scale Calibration');f.save()
print(args.output)
