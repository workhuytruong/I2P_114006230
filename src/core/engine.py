import pygame as pg

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager

from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.backpack_scene import BackpackOverlay
from src.scenes.wildcatch_scene import WildCatchScene

class Engine:

    screen: pg.Surface              # Screen Display of the Game
    clock: pg.time.Clock            # Clock for FPS control
    running: bool                   # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")

        pg.init()

        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self._did_autosave = False
        
        pg.display.set_caption(GameSettings.TITLE)
        self.game_scene = GameScene()
        scene_manager.register_scene("menu", MenuScene())
        scene_manager.register_scene("game", self.game_scene)
        scene_manager.register_scene("wild_catch", WildCatchScene(self.game_scene.game_manager))
        
        scene_manager.change_scene("menu")

    def _autosave_on_exit(self) -> None:
        if self._did_autosave:
            return

        try:
            if hasattr(self, "game_scene") and getattr(self.game_scene, "game_manager", None):
                self.game_scene.game_manager.save()
        finally:
            self._did_autosave = True

    def run(self):
        Logger.info("Running the Game Loop ...")

        try:
            while self.running:
                dt = self.clock.tick(GameSettings.FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.render()
                input_manager.reset()
        finally:
            self._autosave_on_exit()
            pg.quit()

    def handle_events(self):

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._autosave_on_exit()
                self.running = False

            # Always update input manager
            input_manager.handle_events(event)

            if scene_manager.overlay_scene:
                scene_manager.overlay_scene.handle_event(event)
            elif scene_manager.current_scene:
                scene_manager.current_scene.handle_event(event)
    def update(self, dt: float):
        if scene_manager.overlay_scene:
            scene_manager.overlay_scene.update(dt)
        else:
            scene_manager.update(dt)
        

    def render(self):
        self.screen.fill((0, 0, 0))     # Make sure the display is cleared
        scene_manager.draw(self.screen) # Draw the current scene
        pg.display.flip()               # Render the display
    
   
