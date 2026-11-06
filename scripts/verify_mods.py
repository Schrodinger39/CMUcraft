"""Verify an installed instance against the pinned manifest; no credential/log dumps."""
import argparse,hashlib,json,zipfile
from pathlib import Path


def verify(instance,manifest):
    rows=[]
    for entry in manifest['files']:
        rel=Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe manifest path')
        file=Path(instance)/rel
        ok=file.is_file() and file.stat().st_size==entry['fileSize']
        if ok:
            data=file.read_bytes()
            ok=all(hashlib.new(kind,data).hexdigest()==value for kind,value in entry['hashes'].items())
            if ok:
                with zipfile.ZipFile(file) as z:ok=z.testzip() is None
        rows.append({'file':str(rel),'integrity_passed':ok})
    return {'mods':rows,'all_integrity_checks_passed':all(r['integrity_passed'] for r in rows),
            'runtime_compatibility_verified':False,'note':'Checks bytes only. Launch, save/reload and multiplayer require separate tests.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('instance',type=Path);a=p.parse_args()
    m=json.loads((Path(__file__).resolve().parents[1]/'modpack/modrinth.index.json').read_text())
    report=verify(a.instance,m);print(json.dumps(report,indent=2));raise SystemExit(0 if report['all_integrity_checks_passed'] else 1)
