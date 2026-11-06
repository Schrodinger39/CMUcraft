"""Package a portable workbench; downloads are pinned, game binaries are excluded."""
from pathlib import Path
import argparse,json,zipfile


def build(root,output,preview_root=None):
    root=Path(root);output=Path(output)
    manifest=json.loads((root/'modpack/modrinth.index.json').read_text())
    if manifest['dependencies']!={'minecraft':'1.16.5','forge':'36.2.42'}:raise ValueError('Unexpected runtime')
    paths=set()
    for f in manifest['files']:
        path=Path(f['path'])
        if path.is_absolute() or '..' in path.parts or path.parts[0]!='mods':raise ValueError('Unsafe mod path')
        if f['path'] in paths:raise ValueError('Duplicate mod path')
        paths.add(f['path'])
        if len(f['hashes']['sha512'])!=128 or len(f['hashes']['sha1'])!=40:raise ValueError('Invalid hashes')
        if not all(u.startswith('https://') for u in f['downloads']):raise ValueError('HTTPS required')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(root/'modpack/modrinth.index.json','modrinth.index.json')
        z.write(root/'modpack/README.md','overrides/CMUcraft-Workbench-README.md')
        for f in sorted((root/'calibration/world').rglob('*')):
            if f.is_file() and f.name not in ('session.lock',) and '.before-' not in f.name:
                z.write(f,'overrides/saves/CMUcraft-Scale-Calibration/'+str(f.relative_to(root/'calibration/world')))
        if preview_root is not None:
            preview_root=Path(preview_root)
            for folder in sorted(preview_root.iterdir()):
                if folder.is_dir() and (folder/'level.dat').is_file():
                    for file in sorted(folder.rglob('*')):
                        if file.is_file() and file.name!='session.lock' and '.before-' not in file.name:
                            z.write(file,'overrides/saves/'+folder.name+'/'+str(file.relative_to(folder)))
            z.write(preview_root/'README.md','overrides/CMUcraft-Preview-README.md')
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise ValueError('Corrupt package')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('dist/CMUcraft-Workbench.mrpack'));p.add_argument('--preview-root',type=Path);a=p.parse_args()
    print(build(Path(__file__).resolve().parents[1],a.output,a.preview_root))
