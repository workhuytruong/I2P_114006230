import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Item
from src.entities.monsters import Monster
from src.entities.item import Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []

    @property
    def monsters(self) -> list[Monster]:
        """Public access to monsters."""
        return list(self._monsters_data)

    @property
    def items(self) -> list[Item]:
        """Public access to items."""
        return list(self._items_data)
    
    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        pass

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": [m.to_dict() for m in self.monsters],  # convert each Monster
            "items": [i.to_dict() for i in self.items],        # convert each Item
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters_data = data.get("monsters") or []
        items_data = data.get("items") or []

        monsters = [Monster.from_dict(m) for m in monsters_data]
        items = [Item.from_dict(i) for i in items_data]
        bag = cls(monsters, items)
        return bag
    
    def add_monster(self, monster):
        self._monsters_data.append(monster)

    def remove_monster(self, monster):
        self._monsters_data.remove(monster)

    def add_item(self, item, count=1):
        for i in self._items_data:
            if i.name == item.name:
                i.count += count
                return
        item.count = count
        self._items_data.append(item)

    def use_item(self, item_name):
        for i in self._items_data:
            if i.name == item_name:
                i.count -= 1
                if i.count <= 0:
                    self._items_data.remove(i)
                return True
        return False
    
    def get_item_count(self, item_name: str) -> int:
        for i in self._items_data:
            if i.name == item_name:
                return i.count
        return 0

    def get_coins(self) -> int:
        for i in self._items_data:
            if i.name == "Coins":
                return i.count
        return 0

    def add_coins(self, amount: int):
        from src.entities.item import Item
        self.add_item(Item("Coins", 0, "ingame_ui/coin.png"), amount)


    def spend_coins(self, amount: int) -> bool:
        for i in self._items_data:
            if i.name == "Coins" and i.count >= amount:
                i.count -= amount
                return True
        return False

