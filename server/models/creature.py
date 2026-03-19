"""Creature and Disease models."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Creature:
    id: str
    type: str
    x: int = 0
    y: int = 0
    attack: float = 5.0
    defense: float = 3.0
    health: float = 50.0
    loot: list[str] = field(default_factory=list)  # item IDs dropped on kill/capture
    medicinal_value: str = ""  # which disease this creature can cure


@dataclass
class Disease:
    id: str
    name: str
    severity: int = 1  # 1-10
    health_drain_per_tick: float = 0.1
    cure_material: str = ""  # item type needed to cure
    tick_contracted: int = 0
