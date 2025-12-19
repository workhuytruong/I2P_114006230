
import pygame as pg
import os
from src.utils import GameSettings, Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button, Slider
from src.sprites import Sprite
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override
from src.core.managers.game_manager import GameManager

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    back_button: Button
    sound_toggle_button: Button
    home_button: Button

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.background = BackgroundSprite("backgrounds/background1.png")

        # Layout anchors
        self.panel_w = 760
        self.panel_h = 420
        self.panel_x = (GameSettings.SCREEN_WIDTH - self.panel_w) // 2
        self.panel_y = (GameSettings.SCREEN_HEIGHT - self.panel_h) // 2
        center_x = self.panel_x + self.panel_w // 2

        self.back_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.panel_x + self.panel_w - 60, self.panel_y + 16, 44, 44,
            on_click= self.close_overlay
        )

        self.home_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.panel_x + 16, self.panel_y + self.panel_h - 66, 44, 44,
            on_click= self.go_home
        )
        
        # Row anchors
        self.row1_y = self.panel_y + 110
        self.row2_y = self.row1_y + 130
        self.row3_y = self.row2_y + 90
        controls_x = self.panel_x + 220

        # Volume slider
        self.volume_slider = Slider(
            controls_x, self.row1_y, 340, 20,
            initial_value=sound_manager.bgm_volume, 
            track_img_path="UI/raw/UI_Flat_BarFill01g.png", 
            fill_img_path= "UI/raw/UI_Flat_Bar01a.png", 
            knob_img_path= "UI/raw/UI_Flat_Handle02a.png"
        )

        # Sound on/off buttons
        self.sound_toggle_button = Button(
            "UI/raw/UI_Flat_ToggleOn03a.png", None,
            controls_x + 220, self.row1_y + 40, 50, 50, 
            on_click=self.toggle_sound
        )
        self.toggle_on_sprite = Sprite("UI/raw/UI_Flat_ToggleOn03a.png", (50, 50))
        self.toggle_off_sprite = Sprite("UI/raw/UI_Flat_ToggleOff03a.png", (50, 50))

        self.save_slots = ["game0", "game1", "game2"]  # add more slots if needed

        
        self.save_button = Button(
                "UI/button_save.png", "UI/button_save_hover.png",
                center_x - 60, self.row3_y, 70, 70,
                on_click=self.save_game
            )
        
        self.load_button = Button(
                "UI/button_load.png", "UI/button_load_hover.png",
                center_x + 40, self.row3_y, 70, 70,
                on_click= self.load_game
            )
        self.from_menu = False

        self.minimap_toggle_button = Button(
            "UI/raw/UI_Flat_ToggleOn03a.png", None,
            controls_x + 220, self.row2_y - 12,
            50, 50,
            on_click=self.toggle_minimap
        )

    def toggle_sound(self):
        sound_manager.toggle_mute()
        
        if sound_manager.muted:
            self.sound_toggle_button.img_button_default = self.toggle_off_sprite
        else:
            self.sound_toggle_button.img_button_default = self.toggle_on_sprite
    
    def toggle_minimap(self):
        self.game_manager.show_minimap = not self.game_manager.show_minimap

        if  not self.game_manager.show_minimap:
            self.minimap_toggle_button.img_button_default = self.toggle_off_sprite
        else:
            self.minimap_toggle_button.img_button_default = self.toggle_on_sprite

    def close_overlay(self):
        scene_manager.close_overlay()
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")

    def go_home(self):
        scene_manager.close_overlay()
        scene_manager.change_scene("menu")
    
    def save_game(self):
        self.game_manager.save()
        

    def load_game(self):
        gm = GameManager.load_save()
        if gm:

            self.game_manager = gm

            
            active_scene = scene_manager.current_scene
            if active_scene:
                active_scene.game_manager = gm
                active_scene.reload_overlays()
                if gm.player:
                    gm.player.camera.x = gm.player.position.x
                    gm.player.camera.y = gm.player.position.y
                #if needed
                active_scene.game_manager.try_switch_map()

            Logger.info("Game loaded and overlays reloaded")

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        source = scene_manager.overlay_source
        self.from_menu = (source == "menu")

    @override
    def exit(self) -> None:
        pass

    def handle_event(self, event):
        self.volume_slider.handle_event(event)
        self.back_button.handle_event(event)   
        self.sound_toggle_button.handle_event(event)
        self.home_button.handle_event(event)
        self.save_button.handle_event(event)
        self.load_button.handle_event(event)
        self.minimap_toggle_button.handle_event(event)
    @override
    def update(self, dt: float) -> None:
        self.back_button.update(dt)
        self.sound_toggle_button.update(dt)
        self.volume_slider.update(dt)
        sound_manager.set_bgm_volume(self.volume_slider.value)
        self.home_button.update(dt)
        self.save_button.update(dt)
        self.load_button.update(dt)
        self.minimap_toggle_button.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        
        
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Glassy panel
        panel_surface = pg.Surface((self.panel_w, self.panel_h), pg.SRCALPHA)
        panel_surface.fill((20, 20, 20, 180))
        screen.blit(panel_surface, (self.panel_x, self.panel_y))
        pg.draw.rect(screen, (255, 255, 255), (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2)

        title_font = pg.font.Font(GameSettings.FONT, 42)
        section_font = pg.font.Font(GameSettings.FONT, 28)
        font = pg.font.Font(GameSettings.FONT, 22)

        title = title_font.render("Settings", True, (255, 255, 255))
        screen.blit(title, (self.panel_x + 24, self.panel_y + 12))

        # Audio section
        screen.blit(section_font.render("Audio", True, (200, 255, 255)), (self.panel_x + 30, self.row1_y - 38))
        self.volume_slider.draw(screen)
        volume_percent = int(self.volume_slider.value * 100)
        volume_text = font.render(f"Volume: {volume_percent}%", True, (255, 255, 255))
        screen.blit(volume_text, (self.panel_x + 40, self.row1_y - 4))

        status = "Off" if sound_manager.muted else "On"
        status_text = font.render(f"Mute: {status}", True, (255, 255, 255))
        screen.blit(status_text, (self.panel_x + 40, self.row1_y + 40))
        self.sound_toggle_button.draw(screen)

        # Gameplay section
        screen.blit(section_font.render("Gameplay", True, (200, 255, 200)), (self.panel_x + 30, self.row2_y - 38))
        status = "ON" if self.game_manager.show_minimap else "OFF"
        text = font.render(f"Minimap: {status}", True, (255, 255, 255))
        screen.blit(text, (self.panel_x + 40, self.row2_y - 4))
        self.minimap_toggle_button.draw(screen)

        # Save/Load section (hidden from menu)
        if not self.from_menu:
            screen.blit(section_font.render("Save / Load", True, (255, 220, 180)), (self.panel_x + 30, self.row3_y - 38))
            self.save_button.draw(screen)
            self.load_button.draw(screen)

        # Nav buttons
        self.back_button.draw(screen)
        self.home_button.draw(screen)
