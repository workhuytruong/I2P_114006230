import pygame as pg
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.core.services import scene_manager


class NotificationOverlay(Scene):
    def __init__(self, message: str, duration: float = 2.5):
        self.message = message
        self.duration = duration
        self.timer = duration
        self.font_large = pg.font.Font(GameSettings.FONT, 48)
        self.font_small = pg.font.Font(GameSettings.FONT, 28)

    def enter(self):
        self.timer = self.duration

    def exit(self):
        pass

    def update(self, dt: float):
        self.timer -= dt
        if self.timer <= 0:
            scene_manager.close_overlay()

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type in (pg.MOUSEBUTTONDOWN, pg.KEYDOWN):
            scene_manager.close_overlay()

    def draw(self, screen: pg.Surface):

        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        lines = self.message.split("\n")
        start_y = GameSettings.SCREEN_HEIGHT // 2 - (len(lines) * 40) // 2
        for i, line in enumerate(lines):
            font = self.font_large if i == 0 else self.font_small
            surf = font.render(line, True, (255, 255, 255))
            rect = surf.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, start_y + i * 50))
            screen.blit(surf, rect)
