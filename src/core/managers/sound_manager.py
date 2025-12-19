import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self.bgm_volume = 1.0
        self.sfx_volume = 0.7
        self.muted = False
    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        audio.set_volume(0 if self.muted else self.bgm_volume)
        audio.play(-1)
        self.current_bgm = audio
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=None):
        sound = load_sound(filepath)
        vol = self.sfx_volume if volume is None else volume
        sound.set_volume(0 if self.muted else vol)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
    
    def set_bgm_volume(self, value: float):
        self.bgm_volume = max(0, min(1, value))
        if self.current_bgm and not self.muted:
            self.current_bgm.set_volume(self.bgm_volume)
    
    def set_Sfx_volume(self, value:float):
        self.sfx_volume = max(0, min(1, value))
    
    def set_mute(self, mute:bool):
        self.muted = mute
        if self.current_bgm:
            self.current_bgm.set_volume(0 if self.muted else self.bgm_volume)
    
    def toggle_mute(self):
        self.set_mute(not self.muted)
    