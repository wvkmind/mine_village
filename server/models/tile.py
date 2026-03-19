"""Tile and Room models for the 2D grid map."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Tile:
    x: int
    y: int
    type: str  # "floor", "wall", "door", "passage"
    room_id: str | None = None  # None for walls
    items: list[str] = field(default_factory=list)  # item IDs on ground
    occupants: list[str] = field(default_factory=list)  # character IDs here


@dataclass
class Room:
    id: str
    name: str  # "食堂", "广场", "矿道A"
    type: str  # residential, canteen, plaza, storage, workshop, mine, medical, surface_passage
    tiles: list[tuple[int, int]] = field(default_factory=list)
    indoor: bool = True  # affects sound propagation
    description: str = ""
