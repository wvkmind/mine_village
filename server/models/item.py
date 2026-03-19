"""Item model."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Item:
    id: str
    name: str
    type: str  # "food", "tool", "material", "medicine", "weapon", "misc"
    weight: float = 1.0
    durability: int = -1  # uses left, -1 = non-consumable
    effects: dict[str, float] = field(default_factory=dict)  # e.g. {"hunger": 30} or {"attack": 5}
    description: str = ""
