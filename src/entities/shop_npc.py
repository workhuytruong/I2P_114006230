from typing import override
from src.entities.npc import NPC, NPCClassification
from src.core.services import scene_manager
from src.utils import GameSettings, Direction


class ShopNPC(NPC):
    shop_items: list[dict]

    def __init__(self, *args, shop_items: list[dict], **kwargs):
        super().__init__(*args, **kwargs)
        self.shop_items = shop_items

    @override
    def interact(self):
        from src.scenes.shop_scene import ShopScene
        scene_manager.register_scene("shop", ShopScene(self))
        scene_manager.open_overlay("shop", source=self)


    @override
    def to_dict(self):
        base = super().to_dict()
        base["shop_items"] = self.shop_items
        return base

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

        npc = cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            NPCClassification(data["classification"]),
            data.get("max_tiles"),
            facing,
            sprite_sheet=sprite_sheet,
            shop_items=data.get("shop_items", []),
        )
        return npc
