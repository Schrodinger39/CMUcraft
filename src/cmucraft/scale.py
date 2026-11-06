"""One shared scale for geometry and avatar; never scale individual footprints to fit."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Scale:
    blocks_per_metre: float=1.0
    avatar_height_metres: float=1.8

    def __post_init__(self):
        if self.blocks_per_metre<=0:raise ValueError('Scale must be positive')

    def position(self,x_metres,z_metres,elevation_metres,vertical_origin=0):
        s=self.blocks_per_metre
        return x_metres*s,(elevation_metres-vertical_origin)*s,z_metres*s

    @property
    def required_player_scale(self):
        return self.blocks_per_metre

    def validate_player(self,player_scale=1.0):
        if abs(player_scale-self.required_player_scale)>1e-6:
            raise ValueError('World and player scales differ; this distorts perceived proportions')
