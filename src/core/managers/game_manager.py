from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os, shutil
import pygame as pg
from typing import TYPE_CHECKING
from src.scenes.battle_scene import BattleScene
from src.core.services import scene_manager
from src.entities.monsters import Monster
if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: Bag
    npcs: dict[str, list]

    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str

    # For tracking JSON file
    current_save_path: str | None = None
    online_entities: list

    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 npcs: None,
                 bag: Bag | None = None):
                     
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.npcs = npcs if npcs is not None else {}
        self.bag = bag if bag is not None else Bag([], [])
        
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        
        self.current_save_path: str | None = None

        self.show_minimap = True
        self.online_entities = []

    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
    
    @property
    def current_npcs(self):
        return self.npcs.get(self.current_map_key, [])

    def switch_map(self, target: str) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        
        self.next_map = target
        self.should_change_scene = True
            
    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                self.player.position = self.maps[self.current_map_key].spawn.copy()
                self.player.animation.update_pos(self.player.position)
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        for npc in self.npcs.get(self.current_map_key, []):
            if rect.colliderect(npc.animation.rect):
                return True
        for online in self.online_entities:
            if getattr(online, "map_name", "") == self.current_map.path_name:
                if rect.colliderect(online.hitbox):
                    return True

        
        return False
    
    def set_online_entities(self, entities: list) -> None:
        self.online_entities = entities
        
    def save(self):
       
        save_path = "saves/game_save.json"

        # Pause updates in GameScene
        active_scene = scene_manager.current_scene
        if active_scene and hasattr(active_scene, "pause_updates"):
            active_scene.pause_updates = True

        try:
            os.makedirs("saves", exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {save_path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")
        finally:
            if active_scene and hasattr(active_scene, "pause_updates"):
                active_scene.pause_updates = False
             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}")
            return None
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def load_default(cls) -> "GameManager | None":
        
        default_path = "saves/game.json"
        return cls.load(default_path)

    @classmethod
    def load_save(cls) -> "GameManager | None":
    
        save_path = "saves/game_save.json"
        if not os.path.exists(save_path):
            default_path = "saves/game.json"
            shutil.copy(default_path, save_path)
        return cls.load(save_path)
    
    def to_dict(self) -> dict[str, object]:
        
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            block["npcs"] = [n.to_dict() for n in self.npcs.get(key, [])]
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": {
                "x": self.player.position.x / GameSettings.TILE_SIZE,
                "y": self.player.position.y / GameSettings.TILE_SIZE,
                **self.player.to_dict(),  # include other player data
            } if self.player else None,
            "bag": self.bag.to_dict(),
            "settings": {
                "show_minimap": self.show_minimap
            },

        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        from src.entities.shop_npc import ShopNPC
        from src.entities.healer_npc import HealerNPC
        from src.entities.npc import NPC, NPCClassification

        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            trainers,
            npcs = None,
            bag=None
        )
        gm.current_map_key = current_map
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
        
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        Logger.info("Loading NPCs")

        gm.npcs = {}

        for m in data["map"]:
            map_key = m["path"]
            raw_npcs = m.get("npcs", [])   # SAFE even if no NPCs
            gm.npcs[map_key] = []

            for npc_data in raw_npcs:
                npc_type = npc_data.get("classification")

                if npc_type == "shop":
                    gm.npcs[map_key].append(
                        ShopNPC.from_dict(npc_data, gm)
                    )
                elif npc_type == "healer":
                    gm.npcs[map_key].append(
                        HealerNPC.from_dict(npc_data, gm)
                    )
                else:
                    # Future healer / talker NPCs can go here
                    gm.npcs[map_key].append(
                        NPC.from_dict(npc_data, gm)
                    )


        Logger.info("Loading Player")
        if data.get("player"):
            player = Player.from_dict(data["player"], gm)
            player.position.x = data["player"]["x"] * GameSettings.TILE_SIZE
            player.position.y = data["player"]["y"] * GameSettings.TILE_SIZE
            player.animation.update_pos(player.position)
            gm.player = player
        
        gm.show_minimap = data.get("settings", {}).get("show_minimap", True)

        return gm
    
    def start_battle(self, enemy):

        # Skip starting a battle if the player has no monsters to use
        if not self.bag or len(self.bag.monsters) == 0:
            Logger.warning("Cannot start battle: no monsters in bag.")
            self._notify("You have no monsters available to battle!")
            return

        # Prevent battle if enemy has no available monsters
        active_enemy_mons = [m for m in getattr(enemy, "monsters", []) if m.hp > 0]
        if len(active_enemy_mons) == 0:
            Logger.warning("Cannot start battle: enemy has no available monsters.")
            self._notify("No enemy monsters available to battle.")
            return

        # Create BattleScene and register it temporarily
        battle_scene = BattleScene(self, enemy)

        # Register & switch scene
        scene_manager.register_scene("battle_scene", battle_scene)
        scene_manager.change_scene("battle_scene")
    
    def end_battle(self):
        scene_manager.change_scene("game")

    def _notify(self, message: str, duration: float = 2.5) -> None:
        """Show a temporary overlay message without changing scenes."""
        from src.scenes.notification_overlay import NotificationOverlay

        scene_manager.register_scene("notification_overlay", NotificationOverlay(message, duration))
        scene_manager.open_overlay("notification_overlay", source=scene_manager.current_scene)
