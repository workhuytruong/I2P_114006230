from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera
from src.entities.monsters import Monster

class EnemyTrainerClassification(Enum):
    STATIONARY = "stationary"

@dataclass
class IdleMovement:
    def update(self, enemy: "EnemyTrainer", dt: float) -> None:
        return

class EnemyTrainer(Entity):
    classification: EnemyTrainerClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction
    monsters: list

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        classification: EnemyTrainerClassification = EnemyTrainerClassification.STATIONARY,
        max_tiles: int | None = 2,
        facing: Direction | None = None,
        monsters: list | None = None,
        sprite_sheet: str | None = None,
    ) -> None:
        super().__init__(
            x,
            y,
            game_manager,
            sprite_sheet=sprite_sheet or "character/ow1.png",
        )
        self.classification = classification
        self.max_tiles = max_tiles
        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError("Idle EnemyTrainer requires a 'facing' Direction at instantiation")
            self._set_direction(facing)
        else:
            raise ValueError("Invalid classification")
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False
        self.monsters = monsters or []
    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_los_to_player()
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(los_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("RIGHT")
        elif direction == Direction.LEFT:
            self.animation.switch("LEFT")
        elif direction == Direction.DOWN:
            self.animation.switch("DOWN")
        else:
            self.animation.switch("UP")
        self.los_direction = self.direction

    def _get_los_rect(self) -> pygame.Rect | None:
        
        if self.max_tiles is None:
            return None

        tile_size = GameSettings.TILE_SIZE
        x, y = int(self.position.x), int(self.position.y)

        if self.los_direction == Direction.UP:
            return pygame.Rect(x, y - tile_size * self.max_tiles, tile_size, tile_size * self.max_tiles)
        elif self.los_direction == Direction.DOWN:
            return pygame.Rect(x, y + tile_size, tile_size, tile_size * self.max_tiles)
        elif self.los_direction == Direction.LEFT:
            return pygame.Rect(x - tile_size * self.max_tiles, y, tile_size * self.max_tiles, tile_size)
        elif self.los_direction == Direction.RIGHT:
            return pygame.Rect(x + tile_size, y, tile_size * self.max_tiles, tile_size)
        return None

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        
        player_hitbox = player.hitbox
        if los_rect.colliderect(player_hitbox):
            self.detected = True
            if input_manager.key_pressed(pygame.K_RETURN) or input_manager.key_pressed(pygame.K_SPACE):
                if len(self.monsters) >= 1:
                    self.game_manager.start_battle(self)
            return
        self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "EnemyTrainer":
        classification = EnemyTrainerClassification(data.get("classification", "stationary"))
        max_tiles = data.get("max_tiles")
        sprite_sheet = data.get("sprite_sheet")
        facing_val = data.get("facing")
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None and classification == EnemyTrainerClassification.STATIONARY:
            facing = Direction.DOWN
        
        monsters_data = data.get("monsters", [])
        monsters = []

        for m in monsters_data:
            monsters.append(Monster.from_dict(m))  
            # If your Monster class constructor is different, adjust accordingly
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            classification,
            max_tiles,
            facing,
            monsters=monsters,
            sprite_sheet=sprite_sheet,
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["classification"] = self.classification.value
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        base["monsters"] = [m.to_dict() for m in self.monsters]
        base["sprite_sheet"] = self.sprite_sheet
        return base
