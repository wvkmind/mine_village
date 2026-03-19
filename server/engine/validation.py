"""Validation — generate legal actions for a character and validate submitted actions."""
from __future__ import annotations
from engine.actions import Action, TICK_COST
from engine.map_loader import DIRECTIONS
from models.world import WorldState
from models.character import Character

DIR_NAMES = {(0, -1): "north", (0, 1): "south", (-1, 0): "west", (1, 0): "east"}
NAME_TO_DIR = {v: k for k, v in DIR_NAMES.items()}

# Room type -> allowed work actions
ROOM_WORK = {
    "mine": ["mine"],
    "canteen": ["cook"],
    "workshop": ["repair", "craft"],
    "medical": ["heal"],
}


def get_legal_actions(world: WorldState, char: Character) -> list[dict]:
    """Return list of legal action descriptors for this character."""
    if char.is_dead or char.is_busy:
        return []

    actions: list[dict] = []
    tile = world.get_tile(char.x, char.y)
    room = world.get_room_at(char.x, char.y)

    # move — check adjacent walkable tiles
    for (dx, dy), name in DIR_NAMES.items():
        nx, ny = char.x + dx, char.y + dy
        t = world.get_tile(nx, ny)
        if t and t.type != "wall":
            actions.append({"action": "move", "direction": name})

    # talk — characters in same room or adjacent tile
    nearby = set()
    if room:
        for c in world.characters_in_room(room.id):
            if c.id != char.id and c.alive:
                nearby.add(c.id)
    for dx, dy in DIRECTIONS:
        for c in world.characters_at(char.x + dx, char.y + dy):
            if c.id != char.id and c.alive:
                nearby.add(c.id)
    for cid in nearby:
        actions.append({"action": "talk", "target": cid})

    # pickup — items on current tile
    if tile:
        for item_id in tile.items:
            actions.append({"action": "pickup", "target": item_id})

    # eat — food in inventory
    for item_id in char.inventory:
        item = world.items.get(item_id)
        if item and item.type == "food":
            actions.append({"action": "eat", "target": item_id})

    # use — usable items in inventory
    for item_id in char.inventory:
        item = world.items.get(item_id)
        if item and item.type in ("tool", "medicine"):
            actions.append({"action": "use", "target": item_id})

    # work — based on room type
    if room:
        for work_type in ROOM_WORK.get(room.type, []):
            actions.append({"action": work_type})

    # sleep — in residential room or rest room
    if room and room.type in ("residential", "rest"):
        actions.append({"action": "sleep"})

    # attack — any nearby character
    for cid in nearby:
        actions.append({"action": "attack", "target": cid})

    # drop — items in inventory
    for item_id in char.inventory:
        actions.append({"action": "drop", "target": item_id})

    # wait — always available
    actions.append({"action": "wait"})

    return actions


def validate_action(world: WorldState, action: Action) -> str | None:
    """Validate an action. Returns error message or None if valid."""
    char = world.characters.get(action.actor_id)
    if not char:
        return "角色不存在"
    if char.is_dead:
        return "角色已死亡"
    if char.is_busy:
        return "角色正忙"

    if action.type == "move":
        d = NAME_TO_DIR.get(action.target)
        if not d:
            return "无效方向"
        nx, ny = char.x + d[0], char.y + d[1]
        t = world.get_tile(nx, ny)
        if not t or t.type == "wall":
            return "无法通行"

    elif action.type in ("talk", "attack"):
        target = world.characters.get(action.target)
        if not target or not target.alive:
            return "目标不存在或已死亡"

    elif action.type in ("pickup", "eat", "use", "drop"):
        if action.type == "pickup":
            tile = world.get_tile(char.x, char.y)
            if not tile or action.target not in tile.items:
                return "物品不在此处"
        else:
            if action.target not in char.inventory:
                return "物品不在背包中"

    return None


def resolve_competition(actions: list[Action], world: WorldState) -> list[Action]:
    """When multiple characters target the same resource, only one succeeds.
    Others get a 'competition_failed' event. First-come (list order) wins."""
    claimed: dict[str, str] = {}  # target -> winner actor_id
    result = []
    for a in actions:
        if a.type == "pickup" and a.target:
            if a.target in claimed:
                world.add_event(f"{a.actor_id} 争夺 {a.target} 失败（被 {claimed[a.target]} 抢先）")
                continue
            claimed[a.target] = a.actor_id
        result.append(a)
    return result
