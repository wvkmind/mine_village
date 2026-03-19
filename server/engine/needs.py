"""Needs system — per-tick survival stat changes and critical thresholds."""
from __future__ import annotations
from models.world import WorldState
from models.character import Character

# Per-tick drain rates
DRAIN = {
    "hunger": {"idle": 0.5, "labor": 1.0, "sleep": 0.2},
    "energy": {"idle": 0.3, "labor": 0.8, "sleep": -2.5},  # negative = recovery
}

LABOR_ACTIONS = {"mine", "cook", "repair", "craft", "dig", "build_wall", "build_door", "patrol", "forage"}


def update_needs(world: WorldState, char: Character):
    """Update hunger/energy for one tick. Apply critical effects."""
    if char.is_dead:
        return

    mode = "idle"
    if char.current_action == "sleep":
        mode = "sleep"
    elif char.current_action in LABOR_ACTIONS:
        mode = "labor"

    char.hunger = max(0.0, char.hunger - DRAIN["hunger"][mode])
    char.energy = max(0.0, min(100.0, char.energy - DRAIN["energy"][mode]))

    # critical thresholds
    if char.hunger <= 0:
        char.alive = False
        world.add_event(f"{char.name} 饿死了")
        return
    if char.energy <= 0:
        char.energy = 0
        # faint: force rest
        if char.current_action != "sleep":
            char.current_action = "sleep"
            char.action_ticks_left = 10
            world.add_event(f"{char.name} 体力耗尽晕倒了")

    if char.hunger < 10:
        char.health = max(0, char.health - 0.5)
    if char.health <= 0:
        char.alive = False
        world.add_event(f"{char.name} 死亡了")


def get_efficiency(char: Character) -> float:
    """Efficiency multiplier based on needs. 1.0 = normal."""
    eff = 1.0
    if char.hunger < 30:
        eff *= 0.6
    if char.energy < 20:
        eff *= 0.6
    if char.health < 30:
        eff *= 0.5
    return eff
