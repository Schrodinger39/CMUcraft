"""Package two fixed trial worlds from a reviewed, runtime-initialized base.

No game binaries or mod JARs are bundled. A source base must be closed and backed up.
Trial proposals do not authorize whole-chunk integration or building ownership.
"""
import argparse
import json
from pathlib import Path
import shutil
import zipfile

import nbtlib as n
from cmucraft.building_kit import create_kit, check_world, digest, write_json


def sanitize_base(source, output):
    check_world(source)
    shutil.copytree(source, output)
    for name in ('playerdata', 'advancements', 'stats'):
        shutil.rmtree(output/name, ignore_errors=True)
    for name in ('level.dat_old', 'session.lock', 'icon.png', 'xaeromap.txt'):
        (output/name).unlink(missing_ok=True)
    for p in output.rglob('*.bak'):
        p.unlink()
    level = n.load(output/'level.dat')
    level['Data'].pop('Player', None)
    level['Data'].pop('WanderingTraderId', None)
    level.save(output/'level.dat')


def build(root, base, output):
    root, base, output = Path(root), Path(base), Path(output)
    if output.exists():
        raise ValueError('Select a new output directory')
    output.mkdir(parents=True)
    clean = output/'reviewed-base'
    sanitize_base(base, clean)
    manifests = []
    for building in ('hunt-library', 'cohon-university-center'):
        kit = output/building
        m = create_kit(root, building, clean, kit, 130)
        m['trial_release'] = 'builders-round1'
        m['scope'] = 'Independent exterior proposals; no automatic integration or exclusive claim'
        write_json(kit/'kit.json', m)
        shutil.copy2(root/'docs/buildings'/f'{building}.md', kit/'BUILDING-BRIEF.md')
        (kit/'START-HERE.md').write_text(f'''# {m['name']} — exterior trial

You can try this world now. No claim or permission is needed for a private proposal.
Read BUILDING-BRIEF.md, use the reference plan, and try one small exterior detail.
The existing building is rough context, not an approved design. Keep other buildings
and terrain intact. Do not assume the whole world-border square is yours to demolish.
One block is one metre; keep the original coordinates and orientation.

Install the combined CMUcraft-First-Builds.mrpack as a new instance, or use this ZIP
with the exact environment in modrinth.index.json. Put starter-world in its saves
folder. Do not open in vanilla or upgrade mods. This world is named
CMUcraft Kit - {m['name']} in Singleplayer.

Post a screenshot and a short explanation in this building's linked task. No separate
claim issue is needed. A screenshot is enough for a design proposal; to offer an actual
build for integration, close Minecraft and submit the complete world ZIP including
all .mcc files, plus kit.json. Full saves are required for C&B details.

This is a trial pack. A local three-block C&B save/integration/re-entry test passed
on the existing HMCL setup, but this newly packaged download has not had a fresh
launcher-import test. Full-building collisions and transfers remain unverified.
CUC's new trial world has not yet been opened in a client.

Reservation bounds X/Z (upper limits exclusive): {m['bounds_xz_exclusive']}.
Neighbor references inside that square: {', '.join(m['intersecting_references'])}.
Do not modify these neighbors. Proposals are reviewed separately; the square is not
an exclusive assignment. A maintainer confirms scope and issues a current production
kit before any whole-building integration. Keep your original save.
''', encoding='utf-8')
        shutil.make_archive(str(kit), 'zip', kit.parent, kit.name)
        manifests.append(m)
    pack_index = json.loads((root/'modpack/modrinth.index.json').read_text())
    pack_index.update(name='CMUcraft First Builds — Hunt + CUC', versionId='builders-round1',
                      summary='Two exterior trial worlds; propose a small detail without claiming a whole building')
    pack = output/'CMUcraft-First-Builds.mrpack'
    with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('modrinth.index.json', json.dumps(pack_index, indent=2))
        z.write(root/'docs/BUILDERS.md','overrides/START-HERE.md')
        for m in manifests:
            folder=output/m['building_id']
            for file in sorted(folder.rglob('*')):
                if not file.is_file(): continue
                rel=file.relative_to(folder)
                dest=('overrides/saves/'+m['building_id']+'/'+rel.relative_to('starter-world').as_posix()
                      if rel.parts[0]=='starter-world' else
                      'overrides/CMUcraft-kits/'+m['building_id']+'/'+rel.as_posix())
                z.write(file,dest)
    with zipfile.ZipFile(pack) as z:
        if z.testzip(): raise ValueError('Corrupt pack')
        if any(any(part in name.split('/') for part in ('playerdata','advancements','stats')) for name in z.namelist()):
            raise ValueError('Private player files in pack')
    write_json(output/'SHA256.json',{p.name:digest(p.read_bytes()) for p in [pack,*output.glob('*.zip')]})
    return pack


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    print(build(Path(__file__).resolve().parents[1],a.base,a.output))
