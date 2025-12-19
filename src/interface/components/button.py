from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent
from src.utils import GameSettings

class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None

    def __init__(
        self,
        img_path: str, img_hovered_path:str,
        x: int, y: int, width: int, height: int,
        text: str | None = None ,
        on_click: Callable[[], None] | None = None
    ):
        
        self.img_button_default = Sprite(img_path, (width, height))

        if img_hovered_path:
            self.img_button_hover = Sprite(img_hovered_path, (width, height))
        else:
            self.img_button_hover = self.img_button_default  # fallback to normal image
        self.img_button = self.img_button_default
        self.hitbox = pg.Rect(x, y, width, height)
        self.on_click = on_click
        self.text = text
        self.font = pg.font.Font(GameSettings.FONT, 24)
    @override
    def update(self, dt: float) -> None:
        
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            self.img_button = self.img_button_hover
        else:
            self.img_button = self.img_button_default
    
    def handle_event(self, event: pg.event.Event) -> None:
       
        if event.type == pg.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if self.hitbox.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()

    @override
    def draw(self, screen: pg.Surface) -> None:
    
        screen.blit(self.img_button.image, self.hitbox.topleft)
        if isinstance(self.text, str) and self.text.strip() != "":
            text_surface = self.font.render(self.text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=self.hitbox.center)
            screen.blit(text_surface, text_rect)

def main():
    import sys
    pg.init()

    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Button Test")
    clock = pg.time.Clock()
    
    bg_color = (0, 0, 0)
    def on_button_click():
        nonlocal bg_color
        if bg_color == (0, 0, 0):
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
        
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )
    
    running = True
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            input_manager.handle_events(event)


        dt = clock.tick(60) / 1000.0
        
        button.update(dt)
        input_manager.reset()
        
        screen.fill(bg_color)
        button.draw(screen)
        
        pg.display.flip()
    
    pg.quit()


if __name__ == "__main__":
    main()
