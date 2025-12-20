import pygame as pg
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.interface.components import Button
from src.core.services import scene_manager, resource_manager
from typing import override
from src.data.bag import Bag 

class BackpackOverlay(Scene):

    def __init__(self, bag: Bag):
        super().__init__()
        self.bag = bag

        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2

        # Close button
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            1200, 20, 50, 50,
            on_click=self.close_overlay
        )

        self.font = pg.font.Font(GameSettings.FONT, 24)
        self.element_icons = {
            "fire": pg.transform.scale(resource_manager.get_image("ingame_ui/fire.png"), (36, 36)),
            "water": pg.transform.scale(resource_manager.get_image("ingame_ui/water.png"), (36, 36)),
            "grass": pg.transform.scale(resource_manager.get_image("ingame_ui/grass.png"), (36, 36)),
            "neutral": pg.transform.scale(resource_manager.get_image("ingame_ui/neutral.png"), (36, 36)),
        }

        # Scrolling
        self.scroll_y = 0
        self.scroll_speed = 40

        
    def close_overlay(self):
        scene_manager.close_overlay()

    @override
    def handle_event(self, event):
        self.close_button.handle_event(event)
        # Scroll wheel
        if event.type == pg.MOUSEWHEEL:
            self.scroll_y += event.y * self.scroll_speed
            self.scroll_y = max(min(self.scroll_y, 0), -2000)

    @override
    def update(self, dt):
        self.close_button.update(dt)

    @override
    def draw(self, screen):
        
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        
        self.close_button.draw(screen)

        start_x = 120
        y = 120 + self.scroll_y

        
        #Monster Section
        
        screen.blit(self.font.render("Monsters", True, (255, 255, 0)), (start_x, y))
        y += 40

        for m in self.bag.monsters:


            sprite = resource_manager.get_image(m.sprite_path)
            sprite = pg.transform.scale(sprite, (64, 64))
            
            screen.blit(sprite, (start_x, y))

            elem_icon = self.element_icons.get(self._element_key(m), self.element_icons["neutral"])
            screen.blit(elem_icon, (start_x + 72, y))

            text = f"{m.name}  Lv:{m.level}"
            screen.blit(self.font.render(text, True, (255, 255, 255)), (start_x + 120, y))

            hp = m.hp
            max_hp = m.max_hp
            ratio = hp / max_hp

            bar_w = 170
            bar_h = 12

            pg.draw.rect(screen, (60, 60, 60), (start_x + 120, y + 30, bar_w, bar_h))
            pg.draw.rect(screen, (0, 220, 0), (start_x + 120, y + 30, bar_w * ratio, bar_h))

            exp_text = f"EXP: {m.exp}/{m.exp_to_next}"
            screen.blit(self.font.render(exp_text, True, (200, 200, 0)), (start_x + 120, y + 50))

            y += 80

        y += 20

        
        # Item Section
        
        screen.blit(self.font.render("Items", True, (0, 255, 255)), (start_x, y))
        y += 40

        for item in self.bag.items:


            icon = resource_manager.get_image(item.sprite_path)
            icon = pg.transform.scale(icon, (48, 48))
            
            screen.blit(icon, (start_x, y))

            text = f"{item.name}: x{item.count}"
            screen.blit(self.font.render(text, True, (255, 255, 255)), (start_x + 60, y))

            y += 60

    
    def _element_key(self, monster) -> str:
        elem = getattr(monster, "element", "neutral")
        if hasattr(elem, "value"):
            return str(elem.value)
        if isinstance(elem, str):
            return elem.lower()
        return "neutral"
