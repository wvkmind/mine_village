"""State management — save/load world state as JSON."""
from __future__ import annotations
import json, os, dataclasses
from datetime import datetime
from models.world import WorldState
from models.tile import Tile, Room
from models.character import Character, Personality
from models.relationship import Relationship
from models.memory import Memory
from models.item import Item
from models.creature import Creature, Disease
from models.caravan import CaravanInfo

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")


def _to_dict(obj):
    """Recursively convert dataclasses to dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    if isinstance(obj, dict):
        # handle tuple keys (tile coords)
        return {(f"{k[0]},{k[1]}" if isinstance(k, tuple) else k): _to_dict(v)
                for k, v in obj.items()}
    return obj


def save_world(world: WorldState, path: str | None = None) -> str:
    """Save world state to JSON. Returns path."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    if path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"save_{ts}.json")

    data = _to_dict(world)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # also write auto-save
    auto = os.path.join(SAVE_DIR, "auto.json")
    with open(auto, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_world(path: str | None = None) -> WorldState:
    """Load world state from JSON."""
    if path is None:
        path = os.path.join(SAVE_DIR, "auto.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    w = WorldState(
        tick=d["tick"],
        map_width=d["map_width"],
        map_height=d["map_height"],
        next_caravan_tick=d.get("next_caravan_tick", 1000),
        player_id=d.get("player_id"),
        log=d.get("log", []),
    )

    # tiles
    for key, td in d.get("tiles", {}).items():
        x, y = map(int, key.split(","))
        w.tiles[(x, y)] = Tile(**td)

    # rooms
    for rid, rd in d.get("rooms", {}).items():
        rd["tiles"] = [tuple(t) for t in rd["tiles"]]
        w.rooms[rid] = Room(**rd)

    # characters
    for cid, cd in d.get("characters", {}).items():
        p = cd.pop("personality", {})
        cd["personality"] = Personality(**p)
        w.characters[cid] = Character(**cd)

    # items
    for iid, idata in d.get("items", {}).items():
        w.items[iid] = Item(**idata)

    # relationships
    for rd in d.get("relationships", []):
        w.relationships.append(Relationship(**rd))

    # memories
    for md in d.get("memories", []):
        w.memories.append(Memory(**md))

    # creatures
    for crid, crd in d.get("creatures", {}).items():
        w.creatures[crid] = Creature(**crd)

    # diseases
    for cid, diseases in d.get("active_diseases", {}).items():
        w.active_diseases[cid] = [Disease(**dd) for dd in diseases]

    return w
