"""Keep building, terrain and player scale consistent.
The default is one block per metre with an unchanged Minecraft avatar."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    """Shared blocks-per-metre conversion; avatar_height_metres is descriptive metadata."""

    blocks_per_metre: float = 1.0
    avatar_height_metres: float = 1.8

    def __post_init__(self):
        """Reject zero or negative block scales."""
        if self.blocks_per_metre <= 0:
            raise ValueError("Scale must be positive")

    def position(self, x_metres, z_metres, elevation_metres, vertical_origin=0):
        """Convert local metres to Minecraft (x, y, z), subtracting the vertical datum offset."""
        s = self.blocks_per_metre
        return x_metres * s, (elevation_metres - vertical_origin) * s, z_metres * s

    @property
    def required_player_scale(self):
        """Return the avatar multiplier needed to keep proportions under the world scale."""
        return self.blocks_per_metre

    def validate_player(self, player_scale=1.0):
        """Reject a player multiplier that does not match the chosen world multiplier."""
        if abs(player_scale - self.required_player_scale) > 1e-6:
            raise ValueError(
                "World and player scales differ; this distorts perceived proportions"
            )
