import pygame as pg

from src.scenes.scene import Scene
from src.interface.components import Button
from src.utils import GameSettings
from src.utils.definition import Teleport
from src.core.services import scene_manager
from typing import Callable, override


class NavigationOverlay(Scene):
    def __init__(self, game_manager, on_select: Callable[[Teleport], None]):
        super().__init__()
        self.game_manager = game_manager
        self.on_select = on_select
        self.back_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            1200, 20, 50, 50,
            on_click=self.close
        )
        self.dest_buttons: list[Button] = []
        self.info_text: str = ""

    def _build_dest_buttons(self):
        self.dest_buttons.clear()
        teleports = getattr(self.game_manager.current_map, "teleporters", [])
        if not teleports:
            self.info_text = "No destinations on this map."
            return

        self.info_text = "Select a destination"
        start_y = 200
        spacing = 70
        seen: set[str] = set()
        idx = 0
        for tp in teleports:
            label = f"{tp.destination}"
            if label in seen:
                continue
            seen.add(label)
            btn = Button(
                "UI/raw/UI_Flat_Button02a_4.png",
                "UI/raw/UI_Flat_Button02a_1.png",
                x=GameSettings.SCREEN_WIDTH // 2 - 150,
                y=start_y + idx * spacing,
                width=300,
                height=50,
                text=label.replace(".tmx", ""),
                on_click=lambda tp=tp: self._choose(tp)
            )
            self.dest_buttons.append(btn)
            idx += 1

    def _choose(self, tp: Teleport):
        if self.on_select:
            self.on_select(tp)
        scene_manager.close_overlay()

    def close(self):
        scene_manager.close_overlay()

    @override
    def enter(self) -> None:
        self._build_dest_buttons()

    def handle_event(self, event: pg.event.Event) -> None:
        self.back_button.handle_event(event)
        for btn in self.dest_buttons:
            btn.handle_event(event)

    @override
    def update(self, dt: float) -> None:
        self.back_button.update(dt)
        for btn in self.dest_buttons:
            btn.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.back_button.draw(screen)
        for btn in self.dest_buttons:
            btn.draw(screen)

        font = pg.font.Font(GameSettings.FONT, 28)
        title = font.render("Navigation", True, (255, 255, 255))
        screen.blit(title, (GameSettings.SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        if self.info_text:
            sub = font.render(self.info_text, True, (255, 255, 255))
            screen.blit(sub, (GameSettings.SCREEN_WIDTH // 2 - sub.get_width() // 2, 140))
