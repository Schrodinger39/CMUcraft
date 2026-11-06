import pytest

def test_world_player_scale_must_match():
    from cmucraft.scale import Scale
    assert Scale(2).position(10,20,260,240)==(20,40,40)
    with pytest.raises(ValueError): Scale(2).validate_player(1)
    Scale(1).validate_player(1)
