import pygame as pg
import time
from typing import Callable, List, Tuple

from src.scenes.scene import Scene
from src.utils import GameSettings
from src.core.services import scene_manager
from src.interface.components import Button


class ChatOverlay(Scene):
    def __init__(
        self,
        send_callback: Callable[[str], bool],
        fetch_callback: Callable[[], List[Tuple[int, int, str]]],
    ):
        super().__init__()
        self.send_callback = send_callback
        self.fetch_callback = fetch_callback
        self.input_text = ""
        self.messages: list[Tuple[int, int, str]] = []  # (id, from, text)
        self.font = pg.font.Font(GameSettings.FONT, 20)
        self.last_fetch = 0.0
        self.fetch_interval = 0.25
        self._seen_ids: set[int] = set()
        self.close_button = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            GameSettings.SCREEN_WIDTH - 70,
            20,
            50,
            50,
            on_click=scene_manager.close_overlay,
        )

    def enter(self) -> None:
        self.input_text = ""
        self.last_fetch = 0.0
        self._fetch_messages(force=True)

    def add_messages(self, msgs: List[Tuple[int, int, str]]) -> None:
        if not msgs:
            return
        for mid, sender, text in msgs:
            if mid in self._seen_ids:
                continue
            self._seen_ids.add(mid)
            self.messages.append((mid, sender, text))
        if len(self.messages) > 200:
            self.messages = self.messages[-200:]

    def handle_event(self, event: pg.event.Event) -> None:
        self.close_button.handle_event(event)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                scene_manager.close_overlay()
            elif event.key == pg.K_RETURN:
                txt = self.input_text.strip()
                if txt:
                    self.send_callback(txt)
                    self.input_text = ""
                    self._fetch_messages(force=True)
            elif event.key == pg.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if event.unicode and len(self.input_text) < 120:
                    self.input_text += event.unicode

    def update(self, dt: float) -> None:
        self.close_button.update(dt)
        self.last_fetch += dt
        if self.last_fetch >= self.fetch_interval:
            self._fetch_messages()

    def draw(self, screen: pg.Surface) -> None:
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Message box
        box_rect = pg.Rect(50, GameSettings.SCREEN_HEIGHT - 200, GameSettings.SCREEN_WIDTH - 100, 150)
        pg.draw.rect(screen, (30, 30, 30), box_rect)
        pg.draw.rect(screen, (200, 200, 200), box_rect, 2)

        # Render messages (last 6)
        y = box_rect.y + 10
        for mid, sender, text in self.messages[-6:]:
            msg_surface = self.font.render(f"[{sender}] {text}", True, (255, 255, 255))
            screen.blit(msg_surface, (box_rect.x + 10, y))
            y += msg_surface.get_height() + 4

        # Input line
        input_rect = pg.Rect(50, GameSettings.SCREEN_HEIGHT - 40, GameSettings.SCREEN_WIDTH - 100, 30)
        pg.draw.rect(screen, (20, 20, 20), input_rect)
        pg.draw.rect(screen, (200, 200, 200), input_rect, 2)
        input_surface = self.font.render(self.input_text + "_", True, (255, 255, 255))
        screen.blit(input_surface, (input_rect.x + 8, input_rect.y + 5))

        self.close_button.draw(screen)

    def _fetch_messages(self, force: bool = False):
        if not force and self.last_fetch < self.fetch_interval:
            return
        self.last_fetch = 0.0
        try:
            msgs = self.fetch_callback()
            self.add_messages(msgs)
        except Exception:
            pass
