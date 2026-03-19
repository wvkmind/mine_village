"""Item system — usage, durability, crafting framework."""
from __future__ import annotations
from models.world import WorldState
from models.character import Character
from models.item import Item


def use_item(world: WorldState, char: Character, item_id: str) -> bool:
    """Use an item from inventory. Apply effects, reduce durability. Returns success."""
    item = world.items.get(item_id)
    if not item or item_id not in char.inventory:
        return False

    # apply effects
    for stat, delta in item.effects.items():
        if stat == "hunger":
            char.hunger = min(100, char.hunger + delta)
        elif stat == "energy":
            char.energy = min(100, char.energy + delta)
        elif stat == "health":
            char.health = min(100, char.health + delta)
        elif stat == "attack":
            char.attack += delta
        elif stat == "defense":
            char.defense += delta

    # durability
    if item.durability > 0:
        item.durability -= 1
        if item.durability <= 0:
            char.inventory.remove(item_id)
            del world.items[item_id]
            world.add_event(f"{char.name} 的 {item.name} 损坏了")
    elif item.durability == 0:
        # single-use, already consumed
        char.inventory.remove(item_id)
        del world.items[item_id]

    return True


def drop_item(world: WorldState, char: Character, item_id: str) -> bool:
    """Drop item from inventory to ground."""
    if item_id not in char.inventory:
        return False
    char.inventory.remove(item_id)
    tile = world.get_tile(char.x, char.y)
    if tile:
        tile.items.append(item_id)
    return True


def pickup_item(world: WorldState, char: Character, item_id: str) -> bool:
    """Pick up item from ground to inventory."""
    tile = world.get_tile(char.x, char.y)
    if not tile or item_id not in tile.items:
        return False
    tile.items.remove(item_id)
    char.inventory.append(item_id)
    return True
