import json
from pathlib import Path
import pytest
from cmucraft.review import blockers,audit,REQUIRED,FACADE_DETAILS


def approved_record():
    return {'name':'Synthetic test only','osm_id':'test/1','surveyed_height_m':12,
      'verification':{k:True for k in REQUIRED},'evidence':{k:'test evidence' for k in REQUIRED},
      'facade_review':{k:{'passed':True,'reference':'test source','model_view':'test view'} for k in FACADE_DETAILS}}


def test_flags_cannot_replace_evidence():
    r=approved_record();assert not blockers(r)
    r.pop('evidence');assert len(blockers(r))==len(REQUIRED)


def test_generic_facade_does_not_pass():
    r=approved_record();r['facade_review'].pop('window_layout')
    assert any('window_layout' in x for x in blockers(r))


def test_unresolved_identity_cannot_pass():
    r=approved_record();r['identity_warning']='Two different buildings share a name'
    assert any('identity conflict' in x for x in blockers(r))


def test_empty_review_is_not_a_release(tmp_path):
    with pytest.raises(ValueError,match='empty'):audit(tmp_path)


def test_current_campus_is_not_claimed_complete():
    result=audit(Path(__file__).parents[1]/'data/reference/buildings')
    assert result['buildings_reviewed']==41
    assert not result['ready_for_realistic_release']
