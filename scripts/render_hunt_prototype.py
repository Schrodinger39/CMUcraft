import io,zlib,struct,json,argparse
from pathlib import Path
import numpy as np,nbtlib
from PIL import Image,ImageDraw,ImageFont
from cmucraft.chisel import decode_geometry
parser=argparse.ArgumentParser();parser.add_argument('world_folder',type=Path);args=parser.parse_args()
out=args.world_folder;data=np.load(out/'geometry.npz');volume=data['blocks'];palette=list(data['palette']);micro={}
for file in (out/'world/region').glob('*.mca'):
 raw=file.read_bytes()
 for i in range(1024):
  entry=int.from_bytes(raw[4*i:4*i+4],'big')
  if not entry:continue
  pos=(entry>>8)*4096;length=int.from_bytes(raw[pos:pos+4],'big');compression=raw[pos+4]
  payload=(file.parent/f'c.{i%32}.{i//32}.mcc').read_bytes() if compression==130 else raw[pos+5:pos+4+length]
  nbt=nbtlib.File.parse(io.BytesIO(zlib.decompress(payload)))
  for entity in nbt['Level']['TileEntities']:
   if str(entity['id'])=='chiselsandbits:chiseled':
    ids,pal=decode_geometry(entity);indices=np.array([{'minecraft:air':0,'minecraft:iron_block':1,'minecraft:black_stained_glass':2,'minecraft:light_gray_concrete':3,'minecraft:brown_terracotta':4,'minecraft:black_concrete':5}[n] for n in pal])
    micro[tuple(int(entity[k]) for k in ('x','y','z'))]=indices[ids].astype('uint8')

def rectangles(a):
 a=a.copy()
 while a.any():
  row,col=np.argwhere(a)[0];m=int(a[row,col]);w=1
  while col+w<a.shape[1] and a[row,col+w]==m:w+=1
  h=1
  while row+h<a.shape[0] and (a[row+h,col:col+w]==m).all():h+=1
  a[row:row+h,col:col+w]=0;yield int(col),int(row),w,h,m

cache={}
def mesh(bits):
 key=bits.tobytes()
 if key in cache:return cache[key]
 faces=[]
 for axis,sign,shade in [(0,1,1.0),(1,-1,.82),(2,-1,.7)]:
  neighbor=np.zeros_like(bits)
  if axis==0:neighbor[:-1]=bits[1:]
  elif axis==1:neighbor[:,1:]=bits[:,:-1]
  else:neighbor[:,:,1:]=bits[:,:,:-1]
  visible=np.where((bits!=0)&(neighbor==0),bits,0)
  for plane in range(16):
   layer=np.take(visible,plane,axis=axis)
   for u,v,w,h,mat in rectangles(layer):
    q=plane+(1 if sign==1 else 0)
    if axis==0:verts=[(u,q,v),(u+w,q,v),(u+w,q,v+h),(u,q,v+h)]
    elif axis==1:verts=[(u,v,q),(u+w,v,q),(u+w,v+h,q),(u,v+h,q)]
    else:verts=[(q,v,u),(q,v,u+w),(q,v+h,u+w),(q,v+h,u)]
    faces.append((verts,mat,shade))
 faces.sort(key=lambda f:sum(x+z-1.4*y for x,y,z in f[0])/4,reverse=True)
 cache[key]=faces;return faces
im=Image.new('RGB',(1200,900),'#e3e9ed');d=ImageDraw.Draw(im)
def project(x,y,z):return 600+(x-z)*11,900-(x+z)*3.2-(y-32)*13
# Context ground is deliberately neutral: this is a building prototype, not a landscape claim.
d.polygon([project(x,32,z) for x,z in [(8,16),(100,16),(100,92),(8,92)]],fill='#b7c3ad')
positions=[(int(x),int(y),int(z)) for y,z,x in np.argwhere(volume[33:]!=0)]
positions=[(x,y+33,z) for x,y,z in positions]
positions.sort(key=lambda p:p[0]+p[2]-1.4*p[1],reverse=True)
fullfaces=[([(0,1,0),(1,1,0),(1,1,1),(0,1,1)],1,1), ([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],1,.82), ([(0,0,0),(0,0,1),(0,1,1),(0,1,0)],1,.7)]
for x,y,z in positions:
 if (x,y,z) in micro:
  faces=mesh(micro[(x,y,z)]);s=1/16
 else:faces=fullfaces;s=1
 for verts,mat,shade in faces:
  color={1:(222,224,224),2:(78,111,123),3:(180,181,174),4:(112,65,48),5:(40,38,33)}[mat]
  d.polygon([project(x+vx*s,y+vy*s,z+vz*s) for vx,vy,vz in verts],fill=tuple(int(v*shade) for v in color))
d.rectangle((0,0,1200,100),fill='#f7f5ee');d.text((28,20),'Hunt exterior / geometry development view',font=ImageFont.load_default(size=29),fill='#233c34')
d.text((28,64),'Real rotated footprint + 2024 measured roof planes + sub-block fins. NOT an approved replica.',font=ImageFont.load_default(size=17),fill='#52665c')
d.rectangle((0,850,1200,900),fill='#f7f5ee');d.text((28,867),'Rendered from exported block geometry, not a Minecraft screenshot. Colors are preview swatches.',font=ImageFont.load_default(size=16),fill='#52665c')
im.save(out/'geometry_preview.png');print('Rendered',len(micro),'detail blocks,',len(cache),'unique meshes',flush=True)
