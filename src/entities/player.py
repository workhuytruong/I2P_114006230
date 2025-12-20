from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override, List
import json
from src.entities.monsters import Monster
class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager
    monsters: list
    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)

        self.direction = Direction.DOWN
        self.is_moving = False

    @property
    def monsters(self):
        return self.game_manager.bag.monsters

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)

        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= self.speed*dt
            
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += self.speed*dt
            
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= self.speed*dt
           
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += self.speed*dt
            
        factor = 1.0
        if dis.x != 0 and dis.y != 0:
            factor = 1 / math.sqrt(2)

        dis.x *= factor
        dis.y *= factor
        
        self.is_moving = (dis.x != 0 or dis.y != 0)

        if self.is_moving:
            if abs(dis.x) > abs(dis.y):
                if dis.x > 0:
                    self.direction = Direction.RIGHT
                else:
                    self.direction = Direction.LEFT
            else:
                if dis.y > 0:
                    self.direction = Direction.DOWN
                else:
                    self.direction = Direction.UP


        hitbox = self.animation.rect.copy()
        hitbox.x += dis.x
        if self.game_manager.check_collision(hitbox):
            hitbox.x -= dis.x
            hitbox.x = self._snap_to_grid(hitbox.x)
        hitbox.y += dis.y
        if self.game_manager.check_collision(hitbox):
            hitbox.y -= dis.y
            hitbox.y = self._snap_to_grid(hitbox.y)

        self.position.x = hitbox.x
        self.position.y = hitbox.y
        
        tp = self.game_manager.current_map.check_teleport(hitbox)
        if tp:
            dest = tp.destination
            self.game_manager.switch_map(dest)

        self.animation.set_direction(self.direction)
        self.animation.set_moving(self.is_moving)

        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        base = super().to_dict()
        return base
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        x = data["x"] * GameSettings.TILE_SIZE
        y = data["y"] * GameSettings.TILE_SIZE
        return cls(x, y, game_manager)

