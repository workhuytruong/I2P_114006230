import pygame as pg
import time
from collections import deque

from src.utils import Direction
from src.sprites.animation import Animation
from src.utils import GameSettings


class OnlinePlayer:
    def __init__(self, sprite_path):
        self.position = pg.Vector2(0, 0)
        self.direction = Direction.DOWN
        self.is_moving = False
        self.map_name = ""
        self.animation = Animation(sprite_path, ["DOWN", "LEFT", "RIGHT", "UP"], 4, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        self.hitbox = pg.Rect(0, 0, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        self._state_buffer: deque = deque(maxlen=5)
        self._render_delay = 0.1  # seconds of buffer to smooth bursty packets
        self._last_velocity = pg.Vector2(0, 0)

    def push_state(self, data, ts: float | None = None):
        ts = ts if ts is not None else time.monotonic()
        state = {
            "t": ts,
            "pos": pg.Vector2(data["x"], data["y"]),
            "dir": Direction[data.get("direction", "DOWN")],
            "moving": data.get("moving", False),
            "map": data.get("map", ""),
        }
        self.map_name = state["map"]
        if self._state_buffer:
            prev = self._state_buffer[-1]
            delta = state["pos"] - prev["pos"]
            dt = state["t"] - prev["t"]
            if dt > 0:
                self._last_velocity = delta / dt
        self._state_buffer.append(state)

    def _consume_buffer(self):
        target_time = time.monotonic() - self._render_delay
        prev = None
        next_state = None
        # Keep buffer sorted in arrival order; find prev/next around target_time
        for s in list(self._state_buffer):
            if s["t"] <= target_time:
                prev = s
            elif s["t"] > target_time:
                next_state = s
                break
        # drop old states
        while len(self._state_buffer) > 2 and self._state_buffer[1]["t"] < target_time:
            self._state_buffer.popleft()
        return prev, next_state, target_time

    def update(self, dt):
        prev, nxt, target_time = self._consume_buffer()
        if prev and nxt and nxt["t"] > prev["t"]:
            alpha = (target_time - prev["t"]) / (nxt["t"] - prev["t"])
            alpha = max(0.0, min(1.0, alpha))
            pos = prev["pos"].lerp(nxt["pos"], alpha)
            self.position.xy = pos
            self.direction = nxt["dir"]
            self.is_moving = nxt["moving"]
        elif prev:
            self.position.xy = prev["pos"]
            self.direction = prev["dir"]
            self.is_moving = prev["moving"]
        elif nxt:
            self.position.xy = nxt["pos"]
            self.direction = nxt["dir"]
            self.is_moving = nxt["moving"]
        else:
            # no buffer; mild extrapolation
            if self._last_velocity.length_squared() > 0:
                self.position.xy = self.position + self._last_velocity * min(dt, 0.3)

        self.animation.set_direction(self.direction)
        self.animation.set_moving(self.is_moving)
        self.animation.update(dt)
        self.animation.rect.topleft = (int(self.position.x), int(self.position.y))
        self.hitbox.topleft = (int(self.position.x), int(self.position.y))

    def draw(self, screen, camera):
        self.animation.rect.topleft = self.position
        self.animation.draw(screen, camera)
