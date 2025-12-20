import pygame as pg

from src.scenes.scene import Scene
from src.utils import Logger

class SceneManager:
    
    _scenes: dict[str, Scene]
    _current_scene: Scene | None = None
    _next_scene: str | None = None
    _overlay_scene: Scene | None = None

    def __init__(self):
        Logger.info("Initializing SceneManager")
        self._scenes = {}
        self.overlay_source = None

    def register_scene(self, name: str, scene: Scene) -> None:
        self._scenes[name] = scene

    def get_scene(self, name: str) -> Scene | None:
        return self._scenes.get(name)
        
    def change_scene(self, scene_name: str) -> None:
        if scene_name not in self._scenes:
            raise ValueError(f"Scene '{scene_name}' not found")
        Logger.info(f"Changing scene to '{scene_name}'")
        self._next_scene = scene_name

    def open_overlay(self, scene_name: str, source=None) -> None:

        if scene_name not in self._scenes:
            raise ValueError(f"Overlay scene '{scene_name}' not found")
        Logger.info(f"Opening overlay scene '{scene_name}'")
        self._overlay_scene = self._scenes[scene_name]
        self.overlay_source = source
        self._overlay_scene.enter()

    def close_overlay(self) -> None:
        if self._overlay_scene:
            Logger.info(f"Closing overlay scene")
            self._overlay_scene.exit()
            self.overlay_source = None
            self._overlay_scene = None

    def update(self, dt: float) -> None:
        if self._next_scene is not None:
            self._perform_scene_switch()
            
        if self._current_scene:
            if not self._overlay_scene:
                self._current_scene.update(dt)

        if self._overlay_scene:
            self._overlay_scene.update(dt)

    def draw(self, screen: pg.Surface) -> None:
        if self._current_scene:
            self._current_scene.draw(screen)
        if self._overlay_scene:
            self._overlay_scene.draw(screen)

    def _perform_scene_switch(self) -> None:
        if self._next_scene is None:
            return
            
        if self._current_scene:
            self._current_scene.exit()
        
        self._current_scene = self._scenes[self._next_scene]
        
        if self._current_scene:
            Logger.info(f"Entering {self._next_scene} scene")
            self._current_scene.enter()
            
        self._next_scene = None

    @property
    def current_scene(self) -> Scene | None:
        return self._current_scene
    
    @property
    def overlay_scene(self) -> Scene | None:
        return self._overlay_scene
