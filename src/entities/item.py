import pygame as pg

class Item:
    def __init__(self, name: str, count: int = 1, sprite_path: str = ""):
        self.name = name
        self.count = count
        self.sprite_path = sprite_path

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "sprite_path": self.sprite_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            name=data["name"],
            count=data.get("count", 1),
            sprite_path=data.get("sprite_path", "")
        )