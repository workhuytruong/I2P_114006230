import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override
from src.core import GameManager

class MenuScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    play_button: Button
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        self.continue_button = Button(
            "UI/raw/UI_Flat_Button02a_4.png",
            "UI/raw/UI_Flat_Button02a_1.png",
            px - 150,
            py - 120,
            300,
            60,
            text="Continue",
            on_click=self._continue_game,
        )
        self.play_button = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            px + 50, py, 100, 100,
            on_click=self._new_game
        )
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px - 150, py, 100, 100,
            on_click=lambda: scene_manager.open_overlay("setting", source="menu")
        )

    def _continue_game(self) -> None:
        gm = GameManager.load_save()
        if gm is None:
            return

        game_scene = scene_manager.get_scene("game")
        if game_scene and hasattr(game_scene, "set_game_manager"):
            game_scene.set_game_manager(gm)

        scene_manager.change_scene("game")

    def _new_game(self) -> None:
        gm = GameManager.load_default()
        if gm is None:
            return

        game_scene = scene_manager.get_scene("game")
        if game_scene and hasattr(game_scene, "set_game_manager"):
            game_scene.set_game_manager(gm)

        scene_manager.change_scene("game")

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        self.continue_button.update(dt)
        self.play_button.update(dt)
        self.setting_button.update(dt)
    

    @override
    def handle_event(self, event: pg.event.Event) -> None:
        self.continue_button.handle_event(event)
        self.play_button.handle_event(event)
        self.setting_button.handle_event(event)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.continue_button.draw(screen)
        self.play_button.draw(screen)
        self.setting_button.draw(screen)
