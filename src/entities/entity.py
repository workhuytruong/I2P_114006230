from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core import GameManager


class Entity:
    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    sprite_sheet: str
    
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        sprite_sheet: str = "character/ow1.png",
    ) -> None:

        self.sprite_sheet = sprite_sheet
        
        self.animation = Animation(
            self.sprite_sheet, ["DOWN", "LEFT", "RIGHT", "UP"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.animation.update_pos(self.position)
        self.game_manager = game_manager
        
        self.hitbox = pg.Rect(
            int(self.position.x),
            int(self.position.y),
            GameSettings.TILE_SIZE,
            GameSettings.TILE_SIZE
        )
    def update(self, dt: float) -> None:
        self.animation.update_pos(self.position)
        self.animation.update(dt)
        self.update_hitbox()
        
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        self.animation.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)
    def update_hitbox(self):
        self.hitbox.topleft = (int(self.position.x), int(self.position.y))    
    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
    
    @property
    def camera(self) -> PositionCamera:
        # Center camera on player
        x = int(self.position.x - GameSettings.SCREEN_WIDTH / 2)
        y = int(self.position.y - GameSettings.SCREEN_HEIGHT / 2)

        # Clamp to map boundaries
        map_width = self.game_manager.current_map.width_px
        map_height = self.game_manager.current_map.height_px

        x = max(0, min(x, map_width - GameSettings.SCREEN_WIDTH))
        y = max(0, min(y, map_height - GameSettings.SCREEN_HEIGHT))

        return PositionCamera(x, y)

     
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, float | int], game_manager: GameManager) -> Entity:
        x = float(data["x"])
        y = float(data["y"])
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager)
        
