import pygame as pg
from collections import deque
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, scene_manager, input_manager
from src.sprites import Sprite
from src.interface.components import Button
from typing import override
from src.scenes.backpack_scene import BackpackOverlay
from src.scenes.setting_scene import SettingScene
from src.scenes.navigation_overlay import NavigationOverlay
from src.scenes.chat_overlay import ChatOverlay
from src.utils import GameSettings, Direction
from src.entities.online_player import OnlinePlayer

class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    pause_updates: bool = False

    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        scene_manager.register_scene("backpack", BackpackOverlay(self.game_manager.bag))
        self.setting_overlay = SettingScene(self.game_manager)
        scene_manager.register_scene("setting", self.setting_overlay)
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        self.settings_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            1200, 20, 50, 50,
            on_click=lambda: scene_manager.open_overlay("setting", source ="game")
        )
        self.backpack_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            1125, 20, 50, 50,
            on_click=lambda: scene_manager.open_overlay("backpack")
        )
        self.navigation_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            1050, 20, 50, 50,
            on_click=lambda: scene_manager.open_overlay("navigation", source="game")
        )
        self.online_players = {}
        self.nav_path: list[Position] = []
        self.nav_map: str | None = None
        self.nav_target_label: str = ""
        self.navigation_overlay = NavigationOverlay(self.game_manager, self.set_navigation_target)
        scene_manager.register_scene("navigation", self.navigation_overlay)
        # Chat state
        self._chat_bubbles: dict[int, tuple[str, float]] = {}
        self._chat_last_fetched_id = -1
        self._chat_overlay_last_id = -1
        self._chat_overlay_since = -1
        self._chat_history: list[tuple[int, int, str]] = []
        self._chat_poll_timer = 0.0
        self.chat_overlay = ChatOverlay(
            send_callback=self._send_chat_message,
            fetch_callback=self._fetch_chat_for_overlay,
        )
        scene_manager.register_scene("chat", self.chat_overlay)

    def set_game_manager(self, game_manager: GameManager) -> None:
        self.game_manager = game_manager
        self.nav_path = []
        self.nav_map = None
        self.nav_target_label = ""
        self.reload_overlays()
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        if self.pause_updates:
            return
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()

        # Clear navigation if map changed
        if self.nav_map and self.nav_map != self.game_manager.current_map.path_name:
            self.nav_path = []
            self.nav_map = None
            self.nav_target_label = ""

        # Refresh online players first so collisions can account for them
        if self.online_manager:
            seen_ids = set()
            now = time.monotonic()
            for data in self.online_manager.get_list_players():
                pid = data["id"]
                seen_ids.add(pid)

                if pid not in self.online_players:
                    self.online_players[pid] = OnlinePlayer("character/ow1.png")

                self.online_players[pid].push_state(data, now)
                self.online_players[pid].update(dt)

            # prune players that disappeared from server list
            for pid in list(self.online_players.keys()):
                if pid not in seen_ids:
                    del self.online_players[pid]

            self.game_manager.set_online_entities([
                p for p in self.online_players.values()
                if p.map_name == self.game_manager.current_map.path_name
            ])
            # Poll chat periodically (always, but faster when chat UI active or bubbles shown)
            self._chat_poll_timer -= dt
            if self._chat_poll_timer <= 0:
                active_overlay = scene_manager.overlay_scene is self.chat_overlay
                has_bubbles = bool(self._chat_bubbles)
                self._chat_poll_timer = 0.25 if active_overlay else (0.5 if has_bubbles else 1.0)
                self._pull_chat_messages()
            '''if self._chat_poll_timer <= 0:
                self._chat_poll_timer = 0.3
                self._pull_chat_messages()'''
        else:
            self.game_manager.set_online_entities([])
        
        # Only update player if no overlay is open
        if self.game_manager.player and not scene_manager.overlay_scene:
            self.game_manager.player.update(dt)

        if not scene_manager.overlay_scene:
            self.settings_button.update(dt)
            self.backpack_button.update(dt)
            self.navigation_button.update(dt)

        # Update enemies and other objects regardless of overlay
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
        
        for npc in self.game_manager.current_npcs:
            npc.update(dt)

        self.game_manager.bag.update(dt)

        # Send own position/state to server (non-blocking enqueue)
        if self.online_manager:
            if self.game_manager.player:
                _ = self.online_manager.update(
                    self.game_manager.player.position.x, 
                    self.game_manager.player.position.y,
                    self.game_manager.current_map.path_name,
                    self.game_manager.player.direction.name,
                    self.game_manager.player.is_moving
                )


    @override
    def handle_event(self, event: pg.event.Event) -> None:
        if not scene_manager.overlay_scene and event.type == pg.KEYDOWN and event.key == pg.K_i:
            scene_manager.open_overlay("navigation", source="game")
            return
        if not scene_manager.overlay_scene and event.type == pg.KEYDOWN and event.key == pg.K_t:
            scene_manager.open_overlay("chat", source="game")
            return

        if not scene_manager.overlay_scene:
            self.settings_button.handle_event(event)
            self.backpack_button.handle_event(event)
            self.navigation_button.handle_event(event)
        
        
        if scene_manager.overlay_scene:
            return

        if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            player_rect = self.game_manager.player.animation.rect
            if self.game_manager.current_map.is_bush(player_rect):
                scene_manager.change_scene("wild_catch")
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)

        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        for npc in self.game_manager.current_npcs:
            npc.draw(screen, camera)

        if self.game_manager.show_minimap:
                self.draw_minimap(screen)
        self.game_manager.bag.draw(screen)
        
        '''if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)'''
        
        if not scene_manager.overlay_scene:
            self.settings_button.draw(screen)
            self.backpack_button.draw(screen)
            self.navigation_button.draw(screen)
        
        cam = self.game_manager.player.camera
        for p in self.online_players.values():
            p.draw(screen, cam)

        # Draw navigation path
        if self.nav_map == self.game_manager.current_map.path_name and self.nav_path:
            for pos in self.nav_path:
                px, py = camera.transform_position(pos)
                pg.draw.circle(screen, (0, 255, 0), (px + GameSettings.TILE_SIZE // 2, py + GameSettings.TILE_SIZE // 2), 6)

        # Draw chat bubbles
        self._draw_chat_bubbles(screen, camera)


#Utility for reload after save/load
    def reload_overlays(self):
        
        scene_manager.register_scene("backpack", BackpackOverlay(self.game_manager.bag))
        self.setting_overlay.game_manager = self.game_manager

        self.navigation_overlay = NavigationOverlay(self.game_manager, self.set_navigation_target)
        scene_manager.register_scene("navigation", self.navigation_overlay)

        from src.scenes.wildcatch_scene import WildCatchScene
        scene_manager.register_scene("wild_catch", WildCatchScene(self.game_manager))

        if self.game_manager.player:
            player = self.game_manager.player

            if hasattr(player, "animation") and hasattr(player.animation, "update_pos"):
                player.animation.update_pos(player.position)
        
    def draw_minimap(self, screen):
        current_map = self.game_manager.current_map
        player = self.game_manager.player

        MAX_MINIMAP_SIZE = 180
        MINIMAP_X = 20
        MINIMAP_Y = 20

        full_map_surface = current_map._surface
        map_w = full_map_surface.get_width()
        map_h = full_map_surface.get_height()

        # ✅ 1. Keep aspect ratio
        if map_w >= map_h:
            scale = MAX_MINIMAP_SIZE / map_w
            mini_w = MAX_MINIMAP_SIZE
            mini_h = int(map_h * scale)
        else:
            scale = MAX_MINIMAP_SIZE / map_h
            mini_h = MAX_MINIMAP_SIZE
            mini_w = int(map_w * scale)

        # ✅ 2. Scale the real map
        minimap_surface = pg.transform.scale(
            full_map_surface,
            (mini_w, mini_h)
        )

        # ✅ 3. Border
        pg.draw.rect(
            minimap_surface,
            (255, 255, 255),
            minimap_surface.get_rect(),
            2
        )

        # ✅ 4. Convert player world position → minimap
        scale_x = mini_w / current_map.width_px
        scale_y = mini_h / current_map.height_px

        mini_x = int(player.position.x * scale_x)
        mini_y = int(player.position.y * scale_y)

        # ✅ 5. Draw player dot
        pg.draw.circle(
            minimap_surface,
            (0, 255, 255),
            (mini_x, mini_y),
            4
        )

        # ✅ 6. Draw minimap on screen
        screen.blit(minimap_surface, (MINIMAP_X, MINIMAP_Y))

    # Chat helpers
    def _pull_chat_messages(self) -> None:
        if not self.online_manager:
            return
        msgs = self.online_manager.get_recent_chat(self._chat_last_fetched_id, limit=50)
        if not msgs:
            return
        now = time.monotonic()
        for m in msgs:
            mid = int(m.get("id", -1))
            sender = int(m.get("from", -1))
            text = str(m.get("text", ""))
            if mid <= self._chat_last_fetched_id or not text:
                continue
            self._chat_history.append((mid, sender, text))
            self._chat_last_fetched_id = max(self._chat_last_fetched_id, mid)
            self._chat_overlay_since = max(self._chat_overlay_since, mid)
            self._chat_bubbles[sender] = (text, now + 4.0)
        # push new messages into overlay store too
        new_msgs = [m for m in self._chat_history if m[0] > self._chat_overlay_last_id]
        if new_msgs:
            self.chat_overlay.add_messages(new_msgs)
            self._chat_overlay_last_id = new_msgs[-1][0]
        if len(self._chat_history) > 200:
            self._chat_history = self._chat_history[-200:]

    def _send_chat_message(self, text: str) -> bool:
        if not self.online_manager:
            return False
        ok = self.online_manager.send_chat(text)
        if ok:
            now = time.monotonic()
            pid = self.online_manager.player_id
            self._chat_bubbles[pid] = (text, now + 4.0)
        return ok

    def _fetch_chat_for_overlay(self):
        if not self.online_manager:
            return []
        msgs = self.online_manager.get_recent_chat(self._chat_overlay_since, limit=50)
        if not msgs:
            return []
        now = time.monotonic()
        new_tuples: list[tuple[int, int, str]] = []
        for m in msgs:
            mid = int(m.get("id", -1))
            sender = int(m.get("from", -1))
            text = str(m.get("text", ""))
            if mid <= self._chat_overlay_since or not text:
                continue
            self._chat_history.append((mid, sender, text))
            self._chat_last_fetched_id = max(self._chat_last_fetched_id, mid)
            self._chat_overlay_since = max(self._chat_overlay_since, mid)
            self._chat_bubbles[sender] = (text, now + 4.0)
            new_tuples.append((mid, sender, text))
        if len(self._chat_history) > 200:
            self._chat_history = self._chat_history[-200:]
        return new_tuples

    def _draw_chat_bubbles(self, screen: pg.Surface, camera: PositionCamera) -> None:
        if not self._chat_bubbles:
            return
        now = time.monotonic()
        expired = [pid for pid, (_, ts) in self._chat_bubbles.items() if ts <= now]
        for pid in expired:
            self._chat_bubbles.pop(pid, None)
        if not self._chat_bubbles:
            return

        font = pg.font.Font(GameSettings.FONT, 18)
        local_pid = self.online_manager.player_id if self.online_manager else -1

        if self.game_manager.player and local_pid in self._chat_bubbles:
            text, _ = self._chat_bubbles[local_pid]
            self._draw_chat_bubble_for_pos(screen, camera, self.game_manager.player.position, text, font)

        for pid, (text, _) in self._chat_bubbles.items():
            if pid == local_pid:
                continue
            op = self.online_players.get(pid)
            if not op:
                continue
            if op.map_name != self.game_manager.current_map.path_name:
                continue
            pos = Position(op.position.x, op.position.y)
            self._draw_chat_bubble_for_pos(screen, camera, pos, text, font)

    def _draw_chat_bubble_for_pos(self, screen: pg.Surface, camera: PositionCamera, world_pos: Position, text: str, font: pg.font.Font) -> None:
        px, py = camera.transform_position(world_pos)
        px += GameSettings.TILE_SIZE // 2
        py -= 10
        text_surface = font.render(text, True, (0, 0, 0))
        padding_x = 8
        padding_y = 4
        bubble_w = text_surface.get_width() + padding_x * 2
        bubble_h = text_surface.get_height() + padding_y * 2
        bubble_rect = pg.Rect(0, 0, bubble_w, bubble_h)
        bubble_rect.center = (px, py - bubble_h // 2)
        pg.draw.rect(screen, (255, 255, 255), bubble_rect, border_radius=6)
        pg.draw.rect(screen, (0, 0, 0), bubble_rect, width=1, border_radius=6)
        screen.blit(text_surface, (bubble_rect.x + padding_x, bubble_rect.y + padding_y))
        tail = [
            (px - 6, bubble_rect.bottom),
            (px + 6, bubble_rect.bottom),
            (px, bubble_rect.bottom + 8),
        ]
        pg.draw.polygon(screen, (255, 255, 255), tail)
        pg.draw.polygon(screen, (0, 0, 0), tail, width=1)

    # Navigation helpers
    def set_navigation_target(self, teleport) -> None:
        if not self.game_manager.player:
            return
        target_pos = teleport.pos
        path = self._find_path(self.game_manager.current_map, self.game_manager.player.position, target_pos)
        self.nav_path = path if path else []
        self.nav_map = self.game_manager.current_map.path_name
        self.nav_target_label = teleport.destination

    def _find_path(self, map_obj, start_pos: Position, target_pos: Position) -> list[Position] | None:
        tile = GameSettings.TILE_SIZE
        width = map_obj.tmxdata.width
        height = map_obj.tmxdata.height

        def to_tile(pos: Position) -> tuple[int, int]:
            return int(pos.x // tile), int(pos.y // tile)

        start = to_tile(start_pos)
        goal = to_tile(target_pos)

        blocked: set[tuple[int, int]] = set()
        for rect in getattr(map_obj, "_collision_map", []):
            blocked.add((rect.x // tile, rect.y // tile))

        def block_rect(rect: pg.Rect):
            # Block all tiles covered by the rect
            min_x = rect.left // tile
            max_x = (rect.right - 1) // tile
            min_y = rect.top // tile
            max_y = (rect.bottom - 1) // tile
            for tx in range(min_x, max_x + 1):
                for ty in range(min_y, max_y + 1):
                    blocked.add((tx, ty))

        # Block NPCs and enemy trainers on the current map
        for npc in self.game_manager.current_npcs:
            block_rect(npc.animation.rect)
        for enemy in self.game_manager.current_enemy_trainers:
            block_rect(enemy.animation.rect)

        if goal in blocked:
            blocked.remove(goal)

        q = deque([start])
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

        def neighbors(t):
            x, y = t
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
                    yield (nx, ny)

        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for n in neighbors(cur):
                if n not in came_from:
                    came_from[n] = cur
                    q.append(n)

        if goal not in came_from:
            return None

        path_tiles = []
        cur = goal
        while cur is not None:
            path_tiles.append(cur)
            cur = came_from[cur]
        path_tiles.reverse()

        return [Position(x * tile, y * tile) for x, y in path_tiles]
