import pygame as pg
from src.core.services import scene_manager, resource_manager
from src.interface.components.button import Button
from src.sprites import Sprite, BackgroundSprite
from src.utils import GameSettings
from src.entities.monsters import type_multiplier


class BattleScene:
    def __init__(self, game_manager, enemy):
        self.game_manager = game_manager
        self.enemy = enemy
        map_name = getattr(self.game_manager.current_map, "path_name", "")
        is_desert = str(map_name).lower().endswith("desert.tmx")
        bg_path = "backgrounds/background2.png" if is_desert else "backgrounds/background1.png"
        self.background = BackgroundSprite(bg_path)

        all_player_mons = self.game_manager.player.monsters
        all_enemy_mons = self.enemy.monsters

        self.player_team = [m for m in all_player_mons if m.hp > 0][:3]
        self.enemy_team = [m for m in all_enemy_mons if m.hp > 0][:3]
        self.player_buffs = {m: {"atk": 0, "def": 0} for m in self.player_team}

        self.player_index = 0
        self.enemy_index = 0

        self.state = "PLAYER_TURN"
        self.end_text = ""
        self.exp_gain_messages: list[str] = []
        # Track how much damage each player monster dealt for EXP distribution
        self.player_damage: dict[object, int] = {}
        self.end_timer = 0

        self.turn_delay = 0

        self.flash_target = None
        self.flash_timer = 0.0
        self.flash_interval = 0.1
        self.flash_interval_timer = 0.0
        self.flash_visible = True

        self.buttons = []
        self.create_action_buttons()
        # Info banner for monster details
        self.banner_sprite = Sprite("UI/raw/UI_Flat_Banner04a.png", (250, 90))
        # Preload element icons for quick draws
        self.element_icons = {
            "fire": pg.transform.scale(resource_manager.get_image("ingame_ui/fire.png"), (32, 32)),
            "water": pg.transform.scale(resource_manager.get_image("ingame_ui/water.png"), (32, 32)),
            "grass": pg.transform.scale(resource_manager.get_image("ingame_ui/grass.png"), (32, 32)),
            "neutral": pg.transform.scale(resource_manager.get_image("ingame_ui/neutral.png"), (32, 32)),
        }

    def current_player(self):
        return self.player_team[self.player_index]

    def current_enemy(self):
        return self.enemy_team[self.enemy_index]

    def create_action_buttons(self):
        self.buttons = []

        can_switch = len([m for m in self.player_team if m.hp > 0]) > 1
        has_strength = self.game_manager.bag.get_item_count("Strength Potion") > 0
        has_defense = self.game_manager.bag.get_item_count("Defense Potion") > 0
        total_buttons = len(self.current_player().skills) + 1 + (1 if can_switch else 0) + (1 if has_strength else 0) + (1 if has_defense else 0)
        button_width = 150
        button_height = 60
        gap = 20

        total_width = total_buttons * button_width + (total_buttons - 1) * gap
        start_x = (GameSettings.SCREEN_WIDTH - total_width) // 2
        y = GameSettings.SCREEN_HEIGHT - 120

        current_x = start_x
        for i, skill in enumerate(self.current_player().skills):
            self.buttons.append(
                Button(
                    "UI/raw/UI_Flat_Button02a_4.png",
                    "UI/raw/UI_Flat_Button02a_4.png",
                    current_x, y,
                    button_width, button_height,
                    text = skill.name,
                    on_click=lambda s=skill: self.player_attack(s)
                )
            )
            current_x += button_width + gap

        if can_switch:
            self.buttons.append(
                Button(
                    "UI/raw/UI_Flat_Button02a_4.png",
                    "UI/raw/UI_Flat_Button02a_4.png",
                    current_x, y,
                    button_width, button_height,
                    text="Switch",
                    on_click=self.switch_monster
                )
            )
            current_x += button_width + gap

        if has_strength:
            self.buttons.append(
                Button(
                    "UI/raw/UI_Flat_Button02a_4.png",
                    "UI/raw/UI_Flat_Button02a_4.png",
                    current_x, y,
                    button_width, button_height,
                    text="Strength +",
                    on_click=self.use_strength_potion
                )
            )
            current_x += button_width + gap

        if has_defense:
            self.buttons.append(
                Button(
                    "UI/raw/UI_Flat_Button02a_4.png",
                    "UI/raw/UI_Flat_Button02a_4.png",
                    current_x, y,
                    button_width, button_height,
                    text="Defense +",
                    on_click=self.use_defense_potion
                )
            )
            current_x += button_width + gap

        self.buttons.append(
            Button(
                "UI/raw/UI_Flat_Button02a_4.png",
                "UI/raw/UI_Flat_Button02a_4.png",
                current_x, y,
                text = "Run",
                width=button_width, height=button_height,
                on_click=self.end_battle_manual
            )
        )

    
    def start_flash(self, target):
        self.flash_target = target
        self.flash_timer = 0.4
        self.flash_interval_timer = self.flash_interval
        self.flash_visible = False

    def player_attack(self, skill):
        if self.state != "PLAYER_TURN" or self.turn_delay > 0:
            return

        target = self.current_enemy()
        attacker = self.current_player()
        atk_buff = self.player_buffs.get(attacker, {}).get("atk", 0)
        target_def = getattr(target, "defense", 5)
        base_damage = max(1, skill.power + getattr(attacker, "attack", 10) + atk_buff - target_def)
        mult = type_multiplier(getattr(attacker, "element", "neutral"), getattr(target, "element", "neutral"))
        actual_damage = max(1, int(base_damage * mult))
        actual_damage = min(actual_damage, target.hp)
        target.hp -= actual_damage

        
        self.start_flash(target)

        self.player_damage[attacker] = self.player_damage.get(attacker, 0) + actual_damage

        self.turn_delay = 2
        self.state = "ENEMY_WAIT"

        if target.hp <= 0:
            target.hp = 0
            self.handle_enemy_ko()

    def enemy_attack(self):
        target = self.current_player()
        skill = self.current_enemy().skills[0]
        base_damage = max(
            1,
            skill.power
            + getattr(self.current_enemy(), "attack", 10)
            - getattr(target, "defense", 5)
            - self.player_buffs.get(target, {}).get("def", 0)
        )
        mult = type_multiplier(getattr(self.current_enemy(), "element", "neutral"), getattr(target, "element", "neutral"))
        damage = max(1, int(base_damage * mult))
        target.hp -= damage

        
        self.start_flash(target)

        if target.hp <= 0:
            target.hp = 0
            self.handle_player_ko()
        else:
            self.state = "PLAYER_TURN"
            self.create_action_buttons()

    def use_strength_potion(self):
        """Increase current monster's attack for this battle and consume item."""
        if self.state != "PLAYER_TURN" or self.turn_delay > 0:
            return
        if self.game_manager.bag.use_item("Strength Potion"):
            mon = self.current_player()
            self.player_buffs.setdefault(mon, {"atk": 0, "def": 0})
            self.player_buffs[mon]["atk"] += 5
            #self.state = "ENEMY_WAIT"
            #self.turn_delay = 1.5
            self.create_action_buttons()

    def use_defense_potion(self):
        """Increase current monster's defense for this battle and consume item."""
        if self.state != "PLAYER_TURN" or self.turn_delay > 0:
            return
        if self.game_manager.bag.use_item("Defense Potion"):
            mon = self.current_player()
            self.player_buffs.setdefault(mon, {"atk": 0, "def": 0})
            self.player_buffs[mon]["def"] += 5
            #self.state = "ENEMY_WAIT"
            #self.turn_delay = 1.5
            self.create_action_buttons()

    def switch_monster(self):
        """Switch to the next available (non-KO) monster and pass the turn."""
        if self.state != "PLAYER_TURN" or self.turn_delay > 0:
            return

        available = [i for i, m in enumerate(self.player_team) if m.hp > 0 and i != self.player_index]
        if not available:
            return

        self.player_index = available[0]
        self.create_action_buttons()
        self.state = "ENEMY_WAIT"
        self.turn_delay = 2

    def handle_player_ko(self):
        
        if self.player_index < len(self.player_team) - 1:
            self.player_index += 1
            self.state = "PLAYER_TURN"
            self.create_action_buttons()
        else:
            self.end_battle_auto(win=False)

    def handle_enemy_ko(self):
        if self.enemy_index < len(self.enemy_team) - 1:
            self.enemy_index += 1
            self.state = "PLAYER_TURN"
            self.create_action_buttons()
        else:
            self.end_battle_auto(win=True)

    def end_battle_auto(self, win):
        self.state = "END"
        if win:
            total_exp = self.calculate_total_exp_reward()
            self.exp_gain_messages = self.distribute_exp(total_exp)
            self.end_text = f"YOU WIN! +{total_exp} EXP" if total_exp > 0 else "YOU WIN!"
            self.end_timer = 5.0  # give players time to read EXP gains
        else:
            self.end_text = "YOU LOSE!"
            self.end_timer = 3.0

    def end_battle_manual(self):
        self.state = "END"
        self.end_text = "END BATTLE"
        self.end_timer = 1.5

    def update(self, dt):

        if self.flash_timer > 0:
            self.flash_timer -= dt
            self.flash_interval_timer -= dt
            if self.flash_interval_timer <= 0:
                self.flash_interval_timer = self.flash_interval
                self.flash_visible = not self.flash_visible
            if self.flash_timer <= 0:
                self.flash_target = None
                self.flash_visible = True

        
        if self.turn_delay > 0:
            self.turn_delay -= dt
            if self.turn_delay <= 0 and self.state == "ENEMY_WAIT":
                self.state = "ENEMY_TURN"
                self.enemy_attack()

        if self.state == "END":
            self.end_timer -= dt
            if self.end_timer <= 0:
                scene_manager.change_scene("game")

    def handle_event(self, event):
        if self.state == "PLAYER_TURN" and self.turn_delay <= 0:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw_hp_bar(self, screen, x, y, monster, max_width=250, height=14):
        max_hp = monster.max_hp if hasattr(monster, "max_hp") else monster.hp
        ratio = max(0, min(1, monster.hp / max_hp))

        pg.draw.rect(screen, (255, 75, 75), (x, y, max_width, height))
        pg.draw.rect(screen, (25, 255, 125), (x, y, max_width * ratio, height))

        font = pg.font.Font(GameSettings.FONT, 28)
        text = font.render(f"{monster.hp}/{max_hp}", True, (0, 0, 0))
        screen.blit(text, (x + max_width // 2 - text.get_width() // 2, y - 25))

    def draw_stats(self, screen, x, y, monster, is_player: bool = False):
        base_atk = getattr(monster, "attack", 10)
        base_def = getattr(monster, "defense", 5)

        atk = base_atk
        defense = base_def
        if is_player:
            buffs = self.player_buffs.get(monster, {"atk": 0, "def": 0})
            atk += buffs.get("atk", 0)
            defense += buffs.get("def", 0)
        font = pg.font.Font(GameSettings.FONT, 22)
        name_font = pg.font.Font(GameSettings.FONT, 24)

        screen.blit(self.banner_sprite.image, (x, y))
        pad_x = 17
        pad_y = 12

        # Element badge and name on first line
        elem_key = self._element_key(monster)
        icon = self.element_icons.get(elem_key, self.element_icons["neutral"])
        screen.blit(icon, (x + pad_x, y + pad_y - 2))
        name_text = name_font.render(monster.name, True, (0, 0, 0))
        screen.blit(name_text, (x + pad_x + 44, y + pad_y + 6))

        icon_atk = Sprite("ingame_ui/options1.png", (24, 24))
        icon_def = Sprite("ingame_ui/options2.png", (24, 24))

        screen.blit(icon_atk.image, (x + pad_x, y + pad_y + 40))
        text_atk = font.render(f"ATK {atk}", True, (255, 50, 50))
        screen.blit(text_atk, (x + pad_x + 30, y + pad_y + 40))

        screen.blit(icon_def.image, (x + pad_x + 110, y + pad_y + 40))
        text_def = font.render(f"DEF {defense}", True, (50, 50, 255))
        screen.blit(text_def, (x + pad_x + 140, y + pad_y + 40))

    def _element_key(self, monster) -> str:
        elem = getattr(monster, "element", "neutral")
        if hasattr(elem, "value"):
            return str(elem.value)
        if isinstance(elem, str):
            return elem.lower()
        return "neutral"


    def draw(self, screen):
        self.background.draw(screen)

        enemy = self.current_enemy()
        if not (self.flash_target is enemy and not self.flash_visible):
            enemy_sprite = Sprite(enemy.sprite_path, (120, 120))
            x = GameSettings.SCREEN_WIDTH // 4 * 3 - 60
            y = GameSettings.SCREEN_HEIGHT // 2 - 125
            screen.blit(enemy_sprite.image, (x, y))
            
            info_x = GameSettings.SCREEN_WIDTH - 290
            info_y = 24
            self.draw_hp_bar(screen, info_x, info_y + 125, enemy)
            self.draw_stats(screen, info_x, info_y, enemy, is_player=False)

        player = self.current_player()
        if not (self.flash_target is player and not self.flash_visible):
            player_sprite = Sprite(player.sprite_path, (120, 120))
            x = GameSettings.SCREEN_WIDTH // 4 - 60
            y = GameSettings.SCREEN_HEIGHT // 2
            screen.blit(player_sprite.image, (x, y))
            
            info_x = 40
            info_y = 24
            self.draw_hp_bar(screen, info_x, info_y + 125, player)
            self.draw_stats(screen, info_x, info_y, player, is_player=True)

        if self.state == "PLAYER_TURN" and self.turn_delay <= 0:
            for btn in self.buttons:
                btn.draw(screen)

        if self.state == "END":
            overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            font = pg.font.Font(GameSettings.FONT, 96)
            text = font.render(self.end_text, True, (255, 255, 255))
            rect = text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 - 40))
            screen.blit(text, rect)

            if self.exp_gain_messages:
                sub_font = pg.font.Font(GameSettings.FONT, 36)
                start_y = rect.bottom + 10
                for i, msg in enumerate(self.exp_gain_messages):
                    msg_surf = sub_font.render(msg, True, (200, 200, 0))
                    msg_rect = msg_surf.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, start_y + i * 40))
                    screen.blit(msg_surf, msg_rect)

    def enter(self):
        pass

    def exit(self):
        pass

    def calculate_total_exp_reward(self) -> int:
        return sum(m.max_hp for m in self.enemy_team)

    def distribute_exp(self, total_exp: int) -> list[str]:
        if total_exp <= 0:
            return []

        total_damage = sum(self.player_damage.values())
        if total_damage <= 0:
            return []

        summaries: list[str] = []

        # Allocate proportional shares; ensure total distributed equals total_exp
        allocations: list[tuple[object, int]] = []
        running_total = 0
        player_entries = list(self.player_damage.items())
        for idx, (mon, dmg) in enumerate(player_entries):
            if dmg <= 0 or mon.hp <= 0:
                allocations.append((mon, 0))
                continue
            if idx == len(player_entries) - 1:
                share = max(0, total_exp - running_total)
            else:
                share = int(total_exp * (dmg / total_damage))
                running_total += share
            allocations.append((mon, share))

        for mon, share in allocations:
            if share <= 0:
                continue
            before_level = mon.level
            mon.gain_exp(share)
            summary = f"{mon.name} +{share} EXP"
            if mon.level > before_level:
                summary += f" -> Lv {mon.level}"
            summaries.append(summary)

        return summaries
