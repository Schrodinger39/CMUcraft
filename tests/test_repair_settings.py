import importlib.util
from pathlib import Path
import nbtlib as n
import pytest
from cmucraft.world import level_file
spec=importlib.util.spec_from_file_location('repair',Path(__file__).resolve().parents[1]/'scripts/repair_world_settings.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_repair_preserves_overworld_and_player_and_is_idempotent(tmp_path):
    level_file(tmp_path,[4,33,5],32);p=tmp_path/'level.dat';f=n.load(p)
    f['Data']['Player']=n.Compound({'Score':n.Int(17)})
    dimensions=f['Data']['WorldGenSettings']['dimensions'];overworld=dimensions['minecraft:overworld'].snbt()
    for dim in ['the_nether','the_end']:
        g=dimensions['minecraft:'+dim]['generator'];g['settings']=n.String('minecraft:'+dim)
        g['biome_source']=n.Compound({'type':n.String('minecraft:fixed'),'biome':n.String('minecraft:plains')})
    f.save();original=p.read_bytes();assert module.repair(p)
    assert p.with_name('level.dat.before-dimension-fix').read_bytes()==original
    fixed=n.load(p);assert fixed['Data']['Player']['Score']==17
    assert fixed['Data']['WorldGenSettings']['dimensions']['minecraft:overworld'].snbt()==overworld
    assert module.repair(p) is False

def test_repair_rejects_other_minecraft_versions(tmp_path):
    level_file(tmp_path,[4,33,5],32);p=tmp_path/'level.dat';f=n.load(p);f['Data']['DataVersion']=n.Int(3000);f.save()
    original=p.read_bytes()
    with pytest.raises(ValueError,match='1.16.5'):module.repair(p)
    assert p.read_bytes()==original
