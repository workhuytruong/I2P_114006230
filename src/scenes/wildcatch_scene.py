from __future__ import annotations
import pygame as pg
from typing import TYPE_CHECKING

from src.scenes.scene import Scene
from src.sprites import BackgroundSprite, Sprite
from src.utils import GameSettings, Position
from src.core.services import scene_manager
from src.interface.components.button import Button
from src.entities.monsters import random_wild_monster

if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager


class WildCatchScene(Scene):
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager
        self.background = BackgroundSprite("backgrounds/background1.png")

        self.wild_monster = None
        self.monster_sprite: Sprite | None = None

        self.catch_button: Button | None = None
        self.run_button: Button | None = None

    def enter(self) -> None:
    
        current_map = getattr(self.game_manager, "current_map_key", "")
        bg_path = "backgrounds/background2.png" if "desert" in current_map else "backgrounds/background1.png"
        self.background = BackgroundSprite(bg_path)
        
        self.wild_monster = random_wild_monster(current_map)
        self.monster_sprite = Sprite(self.wild_monster.sprite_path, size=(96, 96))

    
        width, height = 200, 60
        center_x = GameSettings.SCREEN_WIDTH // 2

        self.catch_button = Button(
            img_path="UI/raw/UI_Flat_Button02a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button02a_4.png",
            x=center_x - width - 10,
            y=GameSettings.SCREEN_HEIGHT - 120,
            width=width,
            height=height,
            on_click=self.catch_monster,
        )

        self.run_button = Button(
            img_path="UI/raw/UI_Flat_Button02a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button02a_4.png",
            x=center_x + 10,
            y=GameSettings.SCREEN_HEIGHT - 120,
            width=width,
            height=height,
            on_click=self.run_away,
        )

        font = pg.font.Font(GameSettings.FONT, 24)
        self.catch_button.text_surface = font.render("Catch", True, (0, 0, 0))
        self.catch_button.text_pos = (self.catch_button.hitbox.x + 20, self.catch_button.hitbox.y + 15)

        self.run_button.text_surface = font.render("Run", True, (0, 0, 0))
        self.run_button.text_pos = (self.run_button.hitbox.x + 20, self.run_button.hitbox.y + 15)

    def exit(self) -> None:
        ...

    def update(self, dt: float) -> None:
        if self.catch_button:
            self.catch_button.update(dt)
        if self.run_button:
            self.run_button.update(dt)

    def draw(self, screen: pg.Surface) -> None:
    
        self.background.draw(screen)

        if self.monster_sprite:
            x = GameSettings.SCREEN_WIDTH // 2 - 48
            y = GameSettings.SCREEN_HEIGHT // 2 - 96
            self.monster_sprite.update_pos(Position(x, y))
            self.monster_sprite.draw(screen)
            self.draw_monster_info(screen, x, y + 110)

        
        for btn in (self.catch_button, self.run_button):
            if not btn:
                continue
            btn.draw(screen)
            if hasattr(btn, "text_surface"):
                screen.blit(btn.text_surface, btn.text_pos)

        pokeballs = self.game_manager.bag.get_item_count("Pokeball")

        font = pg.font.Font(GameSettings.FONT, 24)
        text = font.render(f"Pokeballs: {pokeballs}", True, (255, 255, 0))
        screen.blit(text, (40, 40))

    def draw_monster_info(self, screen: pg.Surface, x: int, y: int) -> None:

        m = self.wild_monster
        if not m:
            return

        font = pg.font.Font(GameSettings.FONT, 24)
        info = font.render(f"{m.name}  Lv {m.level}", True, (255, 255, 255))
        screen.blit(info, (x - 40, y))


        bar_w, bar_h = 220, 16
        ratio = max(0, min(1, m.hp / m.max_hp))
        pg.draw.rect(screen, (80, 80, 80), (x - 40, y + 30, bar_w, bar_h))
        pg.draw.rect(screen, (0, 200, 0), (x - 40, y + 30, bar_w * ratio, bar_h))
        hp_text = font.render(f"HP: {m.hp}/{m.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (x - 40, y + 55))

        exp_text = font.render(f"EXP: {m.exp}/{m.exp_to_next}", True, (200, 200, 0))
        screen.blit(exp_text, (x - 40, y + 80))

    def handle_event(self, event: pg.event.Event) -> None:
        if self.catch_button:
            self.catch_button.handle_event(event)
        if self.run_button:
            self.run_button.handle_event(event)

        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.run_away()

    def catch_monster(self) -> None:

        bag = self.game_manager.bag

        if bag.get_item_count("Pokeball") <= 0:
            print("No Pokeballs left!")
            return

        used = bag.use_item("Pokeball")
        if not used:
            print("Failed to use Pokeball")
            return
        
        if self.wild_monster:
            self.game_manager.bag.add_monster(self.wild_monster)
        scene_manager.change_scene("game")

    def run_away(self) -> None:
        scene_manager.change_scene("game")
