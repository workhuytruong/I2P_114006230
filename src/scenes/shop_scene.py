import pygame as pg
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.core.services import scene_manager, resource_manager
from src.interface.components.button import Button
from src.entities.item import Item


class ShopScene(Scene):
    def __init__(self, shop_npc):
        super().__init__()
        self.shop_npc = shop_npc
        self.game_manager = shop_npc.game_manager
        self.bag = self.game_manager.bag

        self.font = pg.font.Font(GameSettings.FONT, 24)
        self.small_font = pg.font.Font(GameSettings.FONT, 20)
        # Slightly larger element badges for better readability in shop lists
        self.element_icons = {
            "fire": pg.transform.scale(resource_manager.get_image("ingame_ui/fire.png"), (40, 40)),
            "water": pg.transform.scale(resource_manager.get_image("ingame_ui/water.png"), (40, 40)),
            "grass": pg.transform.scale(resource_manager.get_image("ingame_ui/grass.png"), (40, 40)),
            "neutral": pg.transform.scale(resource_manager.get_image("ingame_ui/neutral.png"), (40, 40)),
        }

        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            1200, 20, 50, 50,
            on_click=self.close
        )

        self.buy_buttons = []
        self.buy_scroll = 0
        self.buy_scroll_speed = 20
        self.buy_panel_top = 80
        self.buy_panel_height = 540
        self.buy_header_y = self.buy_panel_top + 24
        self.buy_row_start = self.buy_header_y + 28
        self.buy_row_spacing = 84

        self.sell_buttons = []
        # Scrolling for sell list
        self.sell_scroll = 0
        self.sell_scroll_speed = 20
        self.sell_panel_top = 80
        self.sell_panel_height = 540
        self.sell_header_y = self.sell_panel_top + 24
        self.sell_row_start = self.sell_header_y + 28
        self.sell_row_spacing = 84

    # ------------------------
    # CLOSE SHOP
    # ------------------------
    def close(self):
        scene_manager.close_overlay()

    # ------------------------
    # BUILD UI
    # ------------------------
    def enter(self):
        self.create_buttons()
        # Reset scroll each time overlay opens
        self.buy_scroll = 0
        self.sell_scroll = 0

    def create_buttons(self):
        self.buy_buttons.clear()
        self.sell_buttons.clear()

        buy_panel_x = 60
        buy_panel_w = 560
        buy_button_w = 120
        buy_button_h = 40
        buy_button_x = buy_panel_x + buy_panel_w - buy_button_w - 20

        # -------- BUY LIST (NPC STOCK) --------
        for idx, item in enumerate(self.shop_npc.shop_items):
            row_y = self.buy_row_start + idx * self.buy_row_spacing
            btn = Button(
                "UI/raw/UI_Flat_Button02a_4.png",
                "UI/raw/UI_Flat_Button02a_4.png",
                buy_button_x, row_y + 6, buy_button_w, buy_button_h,
                text="Buy",
                on_click=lambda i=item: self.buy_item(i)
            )
            self.buy_buttons.append((item, btn))

        sell_panel_x = 660
        sell_panel_w = 560
        sell_button_w = 120
        sell_button_h = 40
        sell_button_x = sell_panel_x + sell_panel_w - sell_button_w - 20

        # -------- SELL LIST (PLAYER MONSTERS) --------
        for idx, mon in enumerate(self.bag.monsters):
            row_y = self.sell_row_start + idx * self.sell_row_spacing
            btn = Button(
                "UI/raw/UI_Flat_Button02a_4.png",
                "UI/raw/UI_Flat_Button02a_4.png",
                sell_button_x, row_y + 10, sell_button_w, sell_button_h,
                text="Sell",
                on_click=lambda m=mon: self.sell_monster(m)
            )
            self.sell_buttons.append((mon, btn))
        self.buy_scroll = self._clamp_buy_scroll(len(self.buy_buttons))
        self.sell_scroll = self._clamp_sell_scroll(len(self.sell_buttons))

    # ------------------------
    # BUY LOGIC
    # ------------------------
    def buy_item(self, item_data):
        if item_data["count"] <= 0:
            print("OUT OF STOCK")
            return

        price = item_data["buy_price"]

        if self.bag.spend_coins(price):
            self.bag.add_item(Item(
                item_data["name"],
                1,
                item_data["sprite_path"]
            ))

            # ✅ IMPORTANT: DECREASE NPC STOCK
            item_data["count"] -= 1
            self.create_buttons()

        else:
            print("NOT ENOUGH COINS")

    # ------------------------
    # SELL LOGIC (POKÉMON)
    # ------------------------
    def sell_monster(self, monster):
        price = (monster.level * 1.5)//1   # simple formula
        self.bag.add_coins(price)
        self.bag.remove_monster(monster)
        self.create_buttons()

    # ------------------------
    # INPUT
    # ------------------------
    def handle_event(self, event):
        self.close_button.handle_event(event)
        if event.type == pg.MOUSEWHEEL:
            self.sell_scroll += event.y * self.sell_scroll_speed
            self.sell_scroll = self._clamp_sell_scroll(len(self.sell_buttons))
            self.buy_scroll += event.y * self.buy_scroll_speed
            self.buy_scroll = self._clamp_buy_scroll(len(self.buy_buttons))

        buy_view_bottom = self.buy_panel_top + self.buy_panel_height - 10
        for idx, (_, btn) in enumerate(self.buy_buttons):
            row_y = self.buy_row_start + idx * self.buy_row_spacing + self.buy_scroll
            btn.hitbox.y = row_y + 6
            if row_y < self.buy_row_start or row_y > buy_view_bottom:
                continue
            btn.handle_event(event)


        for idx, (_, btn) in enumerate(self.sell_buttons):
            row_y = self.sell_row_start + idx * self.sell_row_spacing + self.sell_scroll
            btn.hitbox.y = row_y + 10
            # Skip interaction when row is above header or below panel
            view_bottom = self.sell_panel_top + self.sell_panel_height - 10
            if row_y < self.sell_row_start or row_y > view_bottom:
                continue
            btn.handle_event(event)

    # ------------------------
    # UPDATE
    # ------------------------
    def update(self, dt):
        self.close_button.update(dt)

        for idx, (_, btn) in enumerate(self.buy_buttons):
            row_y = self.buy_row_start + idx * self.buy_row_spacing + self.buy_scroll
            btn.hitbox.y = row_y + 6
            btn.update(dt)

        for idx, (_, btn) in enumerate(self.sell_buttons):
            row_y = self.sell_row_start + idx * self.sell_row_spacing + self.sell_scroll
            btn.hitbox.y = row_y + 10
            btn.update(dt)

    # ------------------------
    # DRAW
    # ------------------------
    def draw(self, screen):
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Base panels
        self._draw_panel(screen, (60, 80, 560, 600))
        self._draw_panel(screen, (660, 80, 560, 600))

        self.close_button.draw(screen)

        # -------- HEADER --------
        coins = self.bag.get_coins()
        screen.blit(self.font.render(f"Coins: {coins}", True, (255, 255, 0)), (80, 40))
        screen.blit(self.small_font.render("Click Buy/Sell buttons to trade", True, (200, 200, 200)), (320, 44))

        # -------- BUY SECTION --------
        buy_header_y = self.buy_header_y
        buy_list_start = self.buy_row_start
        y = buy_list_start + self.buy_scroll
        screen.blit(self.font.render("SHOP ITEMS", True, (0, 255, 255)), (100, buy_header_y - 32))

        buy_view_bottom = self.buy_panel_top + self.buy_panel_height - 10

        for item, btn in self.buy_buttons:
            if y < buy_list_start or y > buy_view_bottom:
                btn.hitbox.y = y + 6
                y += self.buy_row_spacing
                continue
            icon = resource_manager.get_image(item["sprite_path"])
            icon = pg.transform.scale(icon, (48, 48))
            screen.blit(icon, (100, y))

            name_line = f'{item["name"]}  {item["buy_price"]}c'
            stock_line = f'Stock: {item["count"]}'
            screen.blit(self.font.render(name_line, True, (255, 255, 255)), (160, y))
            screen.blit(self.small_font.render(stock_line, True, (180, 180, 180)), (160, y + 30))

            btn.hitbox.y = y + 6
            btn.draw(screen)
            y += self.buy_row_spacing

        # -------- SELL SECTION --------
        header_y = self.sell_header_y
        list_start = self.sell_row_start
        y = list_start + self.sell_scroll
        screen.blit(self.font.render("SELL MONSTERS", True, (255, 200, 100)), (700, header_y - 32))

        view_bottom = self.sell_panel_top + self.sell_panel_height - 10

        for mon, btn in self.sell_buttons:
            # Cull rows outside panel
            if y < list_start or y > view_bottom:
                btn.hitbox.y = y + 10
                y += self.sell_row_spacing
                continue
            price = mon.level * 2
            icon = self.element_icons.get(self._element_key(mon), self.element_icons["neutral"])
            sprite = resource_manager.get_image(mon.sprite_path)
            sprite = pg.transform.scale(sprite, (64, 64))
            screen.blit(sprite, (700, y - 4))
            # Center the larger element badge next to sprite
            icon_y = y + 6
            screen.blit(icon, (770, icon_y))
            txt = f"{mon.name} Lv{mon.level} {price}c"
            screen.blit(self.font.render(txt, True, (255, 255, 255)), (820, y + 2))

            # Quick stats (mirrors bag info)
            hp_text = f"HP {mon.hp}/{mon.max_hp}"
            atk_def_text = f"ATK {getattr(mon, 'attack', 10)}  DEF {getattr(mon, 'defense', 5)}"
            screen.blit(self.small_font.render(hp_text, True, (200, 255, 200)), (820, y + 30))
            screen.blit(self.small_font.render(atk_def_text, True, (200, 200, 255)), (820, y + 54))

            # Update button position to follow scroll
            btn.hitbox.y = y + 10
            btn.draw(screen)
            y += self.sell_row_spacing

    def _element_key(self, monster) -> str:
        elem = getattr(monster, "element", "neutral")
        if hasattr(elem, "value"):
            return str(elem.value)
        if isinstance(elem, str):
            return elem.lower()
        return "neutral"

    def _draw_panel(self, screen, rect_tuple, border_color=(255, 255, 255), fill=(20, 20, 20, 160)):
        x, y, w, h = rect_tuple
        panel = pg.Surface((w, h), pg.SRCALPHA)
        panel.fill(fill)
        screen.blit(panel, (x, y))
        pg.draw.rect(screen, border_color, (x, y, w, h), 2)

    def _clamp_buy_scroll(self, count: int) -> int:
        view_bottom = self.buy_panel_top + self.buy_panel_height - 40
        content_bottom = self.buy_row_start + count * self.buy_row_spacing
        min_scroll = view_bottom - content_bottom
        if min_scroll > 0:
            min_scroll = 0
        return int(max(min(self.buy_scroll, 0), min_scroll))

    def _clamp_sell_scroll(self, count: int) -> int:
        view_bottom = self.sell_panel_top + self.sell_panel_height - 40
        content_bottom = self.sell_row_start + count * self.sell_row_spacing
        min_scroll = view_bottom - content_bottom
        if min_scroll > 0:
            min_scroll = 0
        return int(max(min(self.sell_scroll, 0), min_scroll))
