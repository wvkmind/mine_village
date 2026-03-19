"""WorldState — top-level aggregation of all game state."""
from __future__ import annotations
from dataclasses import dataclass, field
from models.tile import Tile, Room
from models.character import Character
from models.relationship import Relationship
from models.memory import Memory
from models.item import Item
from models.creature import Creature, Disease
from models.caravan import CaravanInfo


@dataclass
class WorldState:
    # time
    tick: int = 0

    # map: (x,y) -> Tile
    tiles: dict[tuple[int, int], Tile] = field(default_factory=dict)
    rooms: dict[str, Room] = field(default_factory=dict)
    map_width: int = 0
    map_height: int = 0

    # entities
    characters: dict[str, Character] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    creatures: dict[str, Creature] = field(default_factory=dict)

    # social
    relationships: list[Relationship] = field(default_factory=list)
    memories: list[Memory] = field(default_factory=list)

    # diseases active on characters: character_id -> [Disease]
    active_diseases: dict[str, list[Disease]] = field(default_factory=dict)

    # caravan
    next_caravan_tick: int = 1000
    last_caravan: CaravanInfo | None = None

    # event log (this tick)
    events: list[str] = field(default_factory=list)
    # full log
    log: list[str] = field(default_factory=list)

    # player
    player_id: str | None = None

    def get_tile(self, x: int, y: int) -> Tile | None:
        return self.tiles.get((x, y))

    def get_room_at(self, x: int, y: int) -> Room | None:
        t = self.get_tile(x, y)
        if t and t.room_id:
            return self.rooms.get(t.room_id)
        return None

    def characters_at(self, x: int, y: int) -> list[Character]:
        t = self.get_tile(x, y)
        if not t:
            return []
        return [self.characters[cid] for cid in t.occupants if cid in self.characters]

    def characters_in_room(self, room_id: str) -> list[Character]:
        room = self.rooms.get(room_id)
        if not room:
            return []
        result = []
        for tx, ty in room.tiles:
            t = self.get_tile(tx, ty)
            if t:
                result.extend(self.characters[cid] for cid in t.occupants if cid in self.characters)
        return result

    def get_relationship(self, a: str, b: str) -> Relationship | None:
        for r in self.relationships:
            if (r.character_a == a and r.character_b == b) or \
               (r.character_a == b and r.character_b == a):
                return r
        return None

    def get_memories(self, character_id: str, recent_ticks: int = 12,
                     include_permanent: bool = True) -> list[Memory]:
        result = []
        for m in self.memories:
            if m.character_id != character_id:
                continue
            if m.tick >= self.tick - recent_ticks:
                result.append(m)
            elif include_permanent and m.permanent:
                result.append(m)
        return result

    def add_event(self, text: str):
        self.events.append(text)
        self.log.append(f"[T{self.tick}] {text}")
