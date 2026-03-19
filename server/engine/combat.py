"""Combat system — damage calculation, escape, death."""
from __future__ import annotations
import random
from models.world import WorldState
from models.character import Character


def calculate_damage(attacker: Character, defender: Character) -> float:
    """damage = max(1, atk - def*0.5) * random(0.8, 1.2)"""
    raw = max(1.0, attacker.attack - defender.defense * 0.5)
    return raw * random.uniform(0.8, 1.2)


def execute_combat_tick(world: WorldState, attacker: Character, defender: Character):
    """One combat tick: both sides attack. Check death."""
    if attacker.is_dead or defender.is_dead:
        return

    dmg_to_def = calculate_damage(attacker, defender)
    dmg_to_atk = calculate_damage(defender, attacker)

    defender.health = max(0, defender.health - dmg_to_def)
    attacker.health = max(0, attacker.health - dmg_to_atk)

    world.add_event(f"{attacker.name} 攻击 {defender.name}（伤害 {dmg_to_def:.1f}），"
                    f"{defender.name} 反击（伤害 {dmg_to_atk:.1f}）")

    if defender.health <= 0:
        _handle_death(world, defender)
    if attacker.health <= 0:
        _handle_death(world, attacker)


def attempt_escape(world: WorldState, runner: Character, opponent: Character) -> bool:
    """Try to escape. Takes 1 tick, gets hit during escape. Returns True if escaped."""
    dmg = calculate_damage(opponent, runner)
    runner.health = max(0, runner.health - dmg)
    world.add_event(f"{runner.name} 试图逃跑，被 {opponent.name} 击中（{dmg:.1f}）")

    if runner.health <= 0:
        _handle_death(world, runner)
        return False
    return True


def _handle_death(world: WorldState, char: Character):
    """Process character death — drop inventory, mark dead."""
    char.alive = False
    char.current_action = None
    char.action_ticks_left = 0

    # drop all items on ground
    tile = world.get_tile(char.x, char.y)
    if tile:
        tile.items.extend(char.inventory)
    char.inventory.clear()

    world.add_event(f"{char.name} 死亡了")
