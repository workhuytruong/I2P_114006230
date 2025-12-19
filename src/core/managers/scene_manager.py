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
        #Open a scene as an overlay on top of the current scene.
        if scene_name not in self._scenes:
            raise ValueError(f"Overlay scene '{scene_name}' not found")
        Logger.info(f"Opening overlay scene '{scene_name}'")
        self._overlay_scene = self._scenes[scene_name]
        self.overlay_source = source
        self._overlay_scene.enter()

    def close_overlay(self) -> None:
        #Close the overlay scene if one is active.
        if self._overlay_scene:
            Logger.info(f"Closing overlay scene")
            self._overlay_scene.exit()
            self.overlay_source = None
            self._overlay_scene = None

    def update(self, dt: float) -> None:
        # Handle scene transition
        if self._next_scene is not None:
            self._perform_scene_switch()
            
        # Update current scene
        if self._current_scene:
            if not self._overlay_scene:
                self._current_scene.update(dt)

        # Update overlay scene (topmost)
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
            
        # Exit current scene
        if self._current_scene:
            self._current_scene.exit()
        
        self._current_scene = self._scenes[self._next_scene]
        
        # Enter new scene
        if self._current_scene:
            Logger.info(f"Entering {self._next_scene} scene")
            self._current_scene.enter()
            
        # Clear the transition request
        self._next_scene = None

    @property
    def current_scene(self) -> Scene | None:
        #Public access to the current scene.
        return self._current_scene
    
    @property
    def overlay_scene(self) -> Scene | None:
        #Public access to the overlay scene.
        return self._overlay_scene
