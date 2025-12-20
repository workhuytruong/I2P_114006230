from src.entities.monsters import Monster


class RemoteTrainer:

    def __init__(self, monsters_data: list[dict], name: str = "Online Trainer"):
        self.name = name
        self.monsters = [Monster.from_dict(m) for m in monsters_data]

    def to_dict(self):
        return {"name": self.name, "monsters": [m.to_dict() for m in self.monsters]}
