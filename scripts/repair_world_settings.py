"""Repair only the known CMUcraft 1.16.5 dimension-generator defect, with backup."""
import argparse,shutil
from pathlib import Path
import nbtlib as n

def repair(path):
    path=Path(path);f=n.load(path);data=f['Data']
    if int(data['DataVersion'])!=2586:raise ValueError('Only Java 1.16.5 saves are supported')
    settings=data['WorldGenSettings'];seed=int(settings['seed']);dimensions=settings['dimensions'];changed=False
    for dim,preset in [('the_nether','nether'),('the_end','end')]:
        generator=dimensions['minecraft:'+dim]['generator']
        if str(generator.get('settings'))!='minecraft:'+dim:continue
        if str(generator['biome_source']['type'])!='minecraft:fixed':raise ValueError('Unexpected generator; refusing to edit')
        generator['settings']=n.String('minecraft:'+preset)
        source=n.Compound({'type':n.String('minecraft:multi_noise' if dim=='the_nether' else 'minecraft:the_end'),'seed':n.Long(seed)})
        if dim=='the_nether':source['preset']=n.String('minecraft:nether')
        generator['biome_source']=source;changed=True
    if changed:
        backup=path.with_name(path.name+'.before-dimension-fix')
        if backup.exists():raise ValueError('Backup already exists; refusing to overwrite it')
        shutil.copy2(path,backup);temporary=path.with_name(path.name+'.repairing');f.save(temporary);temporary.replace(path)
    return changed

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('level_dat',type=Path);a=p.parse_args();print('Repaired' if repair(a.level_dat) else 'No known defect found')
