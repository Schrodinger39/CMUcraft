"""Fail-closed release review; source agreement alone cannot certify architecture."""
import argparse
import json
from pathlib import Path

REQUIRED = ('identity', 'location', 'height', 'facades', 'game_walkthrough')
FACADE_DETAILS = ('materials_colors', 'window_layout', 'roof_silhouette', 'entrances',
                  'distinctive_features', 'terrain_connections')


def blockers(record):
    failures=[]
    for field in REQUIRED:
        if record.get('verification',{}).get(field) is not True:
            failures.append(field+' has not passed review')
        if not record.get('evidence',{}).get(field):
            failures.append(field+' has no review evidence')
    height=record.get('surveyed_height_m')
    if not isinstance(height,(int,float)) or isinstance(height,bool) or not 0<height<200:
        failures.append('a supported height in metres is required')
    for detail in FACADE_DETAILS:
        check=record.get('facade_review',{}).get(detail,{})
        if check.get('passed') is not True or not check.get('reference') or not check.get('model_view'):
            failures.append('facade detail lacks a reference/model comparison: '+detail)
    if record.get('identity_warning') and not record.get('identity_resolution'):
        failures.append('building identity conflict is unresolved')
    return failures


def audit(directory):
    files=sorted(Path(directory).glob('*.json'))
    if not files: raise ValueError('No building records; refusing an empty approval')
    records=[json.loads(p.read_text()) for p in files]
    ids=[r['osm_id'] for r in records]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate building identities')
    rows=[{'name':r['name'],'osm_id':r['osm_id'],'blockers':blockers(r)} for r in records]
    return {'ready_for_realistic_release':all(not r['blockers'] for r in rows),
            'buildings_reviewed':len(rows),'approved':sum(not r['blockers'] for r in rows),'buildings':rows,
            'limits':'This gate enforces evidence completeness. It cannot judge visual truth automatically.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--records',default='data/reference/buildings');p.add_argument('--output',default='audit/release-readiness.json')
    a=p.parse_args();report=audit(a.records);Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['approved']}/{report['buildings_reviewed']} approved")
    raise SystemExit(0 if report['ready_for_realistic_release'] else 2)

if __name__=='__main__':main()
