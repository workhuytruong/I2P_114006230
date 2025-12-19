from typing import override
from src.entities.npc import NPC, NPCClassification
from src.core.services import scene_manager
from src.utils import GameSettings, Direction


class HealerNPC(NPC):
    @override
    def interact(self):
        from src.scenes.heal_scene import HealScene
        scene_manager.register_scene("healer", HealScene(self.game_manager))
        scene_manager.open_overlay("healer", source=self)

    @classmethod
    @override
    def from_dict(cls, data, game_manager):
        facing_val = data.get("facing", "DOWN")
        sprite_sheet = data.get("sprite_sheet")
        if isinstance(facing_val, str):
            facing = Direction[facing_val.upper()]
        elif isinstance(facing_val, Direction):
            facing = facing_val
        else:
            facing = Direction.DOWN

        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            NPCClassification(data["classification"]),
            data.get("max_tiles"),
            facing,
            sprite_sheet=sprite_sheet,
        )
