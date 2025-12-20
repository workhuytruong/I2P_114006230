from enum import Enum


class Element(str, Enum):
    NEUTRAL = "neutral"
    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"


def _parse_element(raw: object) -> Element:
    if isinstance(raw, Element):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        for e in Element:
            if lowered == e.value:
                return e
    return Element.NEUTRAL


def type_multiplier(attacker_element: object, defender_element: object) -> float:
    atk = _parse_element(attacker_element)
    df = _parse_element(defender_element)
    if atk == Element.NEUTRAL or df == Element.NEUTRAL or atk == df:
        return 1.0
    if atk == Element.WATER and df == Element.FIRE:
        return 1.5
    if atk == Element.FIRE and df == Element.GRASS:
        return 1.5
    if atk == Element.GRASS and df == Element.WATER:
        return 1.5
    
    if df == Element.WATER and atk == Element.FIRE:
        return 0.75
    if df == Element.FIRE and atk == Element.GRASS:
        return 0.75
    if df == Element.GRASS and atk == Element.WATER:
        return 0.75
    return 1.0


class Monster:
    def __init__(
        self,
        name: str,
        hp: int,
        max_hp: int,
        level: int,
        sprite_path: str,
        exp: int = 0,
        attack: int = 10,
        defense: int = 5,
        element: Element | str | None = None,
    ):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.level = level
        self.sprite_path = sprite_path
        self.exp = exp
        self.attack = attack
        self.defense = defense
        self.element: Element = _parse_element(element)
        self.skills: list[Skill] = []
        # Flashing state
        self.flash_timer = 0
        self.flash_duration = 0.4
        self.flash_state = False
        self.flash_interval = 0.1   # blink speed

    @property
    def exp_to_next(self) -> int:
        return 30 + self.level * 10

    def gain_exp(self, amount: int):
        if amount <= 0:
            return
        self.exp += amount

        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            # Small stat bump on level up
            self.max_hp += 5
            self.hp = self.max_hp

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "level": self.level,
            "exp": self.exp,
            "attack": self.attack,
            "defense": self.defense,
            "sprite_path": self.sprite_path,
            "element": self.element.value,
            "skills": [s.__dict__ for s in self.skills]
        }
    def update(self, dt: float):
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Monster":
        m = cls(
            name=data["name"],
            hp=data["hp"],
            max_hp=data["max_hp"],
            level=data["level"],
            sprite_path=data["sprite_path"],
            exp=data.get("exp", 0),
            attack=data.get("attack", 10),
            defense=data.get("defense", 5),
            element=data.get("element"),
        )
        m.skills = [Skill(s["name"], s["power"], s.get("cost", 0)) for s in data.get("skills", [])]
        return m
    
class Skill:
    def __init__(self, name: str, power: int, cost: int = 0):
        self.name = name
        self.power = power
        self.cost = cost  #develop later 
    
    def to_dict(self) -> dict:
        return {"name": self.name, "power": self.power, "cost": self.cost}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["name"], data["power"], data.get("cost", 0))
    

# WILD MONSTER RANDOM SYSTEM

import random
import json
import os


def _load_wild_pools() -> dict[str, list[dict]]:
    json_path = os.path.join("saves", "wildpokemon.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("wildpokemon.json must be a JSON object keyed by map name.")

    pools: dict[str, list[dict]] = {}
    for key, monsters in data.items():
        if isinstance(monsters, list):
            pools[key] = monsters

    if not pools:
        raise ValueError("wildpokemon.json contains no wild monster pools.")

    return pools


WILD_MONSTER_POOLS = _load_wild_pools()


def create_monster_from_template(tpl: dict) -> "Monster":
    
    m = Monster(
        name=tpl["name"],
        hp=tpl["hp"],
        max_hp=tpl["max_hp"],
        level=tpl["level"],
        sprite_path=tpl["sprite_path"],
        attack=tpl.get("attack", 10),
        defense=tpl.get("defense", 5),
        element=tpl.get("element"),
    )

    # I add skill for monster
    m.skills = [
        Skill(s["name"], s["power"], s.get("cost", 0))
        for s in tpl.get("skills", [])
    ]

    return m


def random_wild_monster(map_name: str | None = None) -> "Monster":
    if not map_name:
        raise ValueError("Map name required to select wild monsters")

    pool = WILD_MONSTER_POOLS.get(map_name)
    if not pool:
        raise ValueError(f"No wild monsters configured for map '{map_name}'")

    tpl = random.choice(pool)
    return create_monster_from_template(tpl)
