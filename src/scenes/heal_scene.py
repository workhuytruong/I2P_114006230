import pygame as pg
from typing import override

from src.scenes.scene import Scene
from src.core.services import scene_manager, resource_manager
from src.utils import GameSettings
from src.interface.components import Button


class HealScene(Scene):
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.font = pg.font.Font(GameSettings.FONT, 28)
        self.title_font = pg.font.Font(GameSettings.FONT, 36)
        self.selected_index = 0
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            1200, 20, 50, 50,
            on_click=self._close
        )

    @override
    def enter(self):
        self.selected_index = 0

    @override
    def exit(self):
        pass

    @override
    def update(self, dt: float):
        self.close_button.update(dt)

    def handle_event(self, event: pg.event.Event) -> None:
        self.close_button.handle_event(event)
        mons = self.game_manager.bag.monsters
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self._close()
                return
            if event.key == pg.K_UP and mons:
                self.selected_index = (self.selected_index - 1) % len(mons)
            if event.key == pg.K_DOWN and mons:
                self.selected_index = (self.selected_index + 1) % len(mons)
            if event.key in (pg.K_RETURN, pg.K_SPACE) and mons:
                mon = mons[self.selected_index]
                mon.hp = mon.max_hp
                self._close()

    @override
    def draw(self, screen: pg.Surface) -> None:
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("Heal a Pokemon", True, (255, 255, 255))
        screen.blit(title, (GameSettings.SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        mons = self.game_manager.bag.monsters
        y = 160
        for i, m in enumerate(mons):
            color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
            text = self.font.render(f"{m.name} Lv{m.level} HP {m.hp}/{m.max_hp}", True, color)
            screen.blit(text, (200, y))
            try:
                sprite = resource_manager.get_image(m.sprite_path)
                sprite = pg.transform.scale(sprite, (48, 48))
                screen.blit(sprite, (140, y - 4))
            except Exception:
                pass
            y += 40

        potions = self.game_manager.bag.get_item_count("Potion")
        potion_text = self.font.render(f"Potions: {potions}", True, (180, 255, 180))
        screen.blit(potion_text, (200, y + 20))

        hint = self.font.render("Arrow keys to select, Enter to heal, Esc/Close to exit", True, (200, 200, 200))
        screen.blit(hint, (GameSettings.SCREEN_WIDTH // 2 - hint.get_width() // 2, GameSettings.SCREEN_HEIGHT - 80))

        self.close_button.draw(screen)

    def _close(self):
        scene_manager.close_overlay()
