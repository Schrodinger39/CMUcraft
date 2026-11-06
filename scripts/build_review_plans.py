"""Produce source-footprint context sheets, not architecture previews."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape
from cmucraft.campus import REGION
from cmucraft.osm import parse

def build(root):
    root=Path(root);out=root/'audit/buildings';out.mkdir(exist_ok=True)
    features,warnings=parse(root/'data/raw/campus.osm',separate_named_parts=True)
    if warnings:raise ValueError(warnings)
    contexts=[(REGION.local_geometry(f['geometry']),f['tags'].get('name','')) for f in features]
    for file in sorted((root/'data/reference/buildings').glob('*.json')):
        r=json.loads(file.read_text());g=shape(r['footprint_xz']);cx,cz=g.centroid.coords[0]
        span=max(180,g.bounds[2]-g.bounds[0]+60,g.bounds[3]-g.bounds[1]+60)
        scale=640/span;left,top=cx-span/2,cz-span/2
        def xy(p):return (40+(p[0]-left)*scale,100+(p[1]-top)*scale)
        im=Image.new('RGB',(720,840),'#f7f5ee');d=ImageDraw.Draw(im)
        font=ImageFont.load_default(size=14)
        for geom,name in contexts:
            if abs(geom.centroid.x-cx)>span or abs(geom.centroid.y-cz)>span:continue
            parts=geom.geoms if hasattr(geom,'geoms') else [geom]
            for p in parts:
                d.polygon([xy(a) for a in p.exterior.coords],fill='#deded7',outline='#b4b9b5')
                for ring in p.interiors:d.polygon([xy(a) for a in ring.coords],fill='#f7f5ee')
        parts=g.geoms if hasattr(g,'geoms') else [g]
        for p in parts:
            d.polygon([xy(a) for a in p.exterior.coords],fill='#96c3b1',outline='#17644e',width=3)
            for ring in p.interiors:d.polygon([xy(a) for a in ring.coords],fill='#f7f5ee',outline='#17644e',width=2)
        # Clear clipping margins after drawing neighbors.
        for rect in [(0,0,720,95),(0,745,720,840),(0,95,35,745),(685,95,720,745)]:d.rectangle(rect,fill='#f7f5ee')
        title=r['name'];d.text((28,15),title,font=ImageFont.load_default(size=20 if len(title)<45 else 16),fill='#19392e')
        d.text((28,46),r['osm_id']+' | Source geometry, not a completed model',font=font,fill='#485950')
        d.text((28,68),'North up | X east / Z south | Unverified real-world identity and facade',font=font,fill='#485950')
        d.line((50,720,50+20*scale,720),fill='black',width=3);d.text((50,698),'20 m',font=font,fill='black')
        d.text((28,757),f"Area {r['footprint_area_m2']:.1f} m2 | Centroid X/Z {r['centroid_xz_m']}",font=font,fill='#19392e')
        d.text((28,781),'Green: selected footprint. Gray: nearby source footprints.',font=font,fill='#485950')
        d.text((28,808),'© OpenStreetMap contributors, ODbL | CMUcraft / Chris Yu',font=font,fill='#485950')
        im.save(out/(file.stem+'.png'))
    print(out)

if __name__=='__main__':build(Path(__file__).resolve().parents[1])
