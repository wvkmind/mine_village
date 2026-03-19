"""Tick engine — the 10-step main loop that drives the world forward."""
from __future__ import annotations
import random
from models.world import WorldState
from models.character import Character
from engine.actions import Action, TICK_COST
from engine.validation import get_legal_actions, validate_action, resolve_competition, NAME_TO_DIR
from engine.needs import update_needs, LABOR_ACTIONS
from engine.combat import execute_combat_tick
from engine.skills import try_skill_growth
from engine.economy import earn_points
from engine.items import use_item, drop_item, pickup_item

AUTOSAVE_INTERVAL = 100


def advance(world: WorldState, player_action: Action | None = None,
            ai_decisions: dict[str, Action] | None = None):
    """Advance world by one tick. The 10-step main loop."""
    world.tick += 1
    world.events.clear()

    # 1. Collect player input
    actions: list[Action] = []
    if player_action:
        actions.append(player_action)

    # 2. Collect NPC actions (from AI or rule fallback)
    if ai_decisions:
        for npc_id, action in ai_decisions.items():
            actions.append(action)
    # NPCs without AI decisions that are idle get a wait action
    for char in world.characters.values():
        if char.is_player or char.is_dead or char.is_busy:
            continue
        if ai_decisions and char.id in ai_decisions:
            continue
        actions.append(Action.wait(char.id))

    # 3. Validate all actions
    valid_actions = []
    for a in actions:
        err = validate_action(world, a)
        if err:
            world.add_event(f"{a.actor_id} 行动无效: {err}")
        else:
            valid_actions.append(a)

    # 4. Resolve competition
    valid_actions = resolve_competition(valid_actions, world)

    # 5. Execute all actions
    for a in valid_actions:
        _execute_action(world, a)

    # 6. Settle consequences (needs, diseases)
    for char in world.characters.values():
        if char.is_dead:
            continue
        update_needs(world, char)
        # tick down busy actions
        if char.action_ticks_left > 0:
            char.action_ticks_left -= 1
            if char.action_ticks_left <= 0:
                # action completed
                _complete_action(world, char)
                char.current_action = None

    # 7. Environment events (handled by engine/events.py, called externally)
    # 8. Update map state (occupant lists)
    _update_occupants(world)

    # 9. Autosave check (handled by caller)
    # 10. Push state to frontend (handled by API layer)


def _execute_action(world: WorldState, action: Action):
    """Execute a single validated action."""
    char = world.characters.get(action.actor_id)
    if not char:
        return

    if action.type == "move":
        d = NAME_TO_DIR.get(action.target)
        if d:
            char.x += d[0]
            char.y += d[1]

    elif action.type == "talk":
        world.add_event(f"{char.name} 对 {action.target} 说话")
        # dialogue content handled by AI layer

    elif action.type == "pickup":
        pickup_item(world, char, action.target)
        world.add_event(f"{char.name} 捡起了物品")

    elif action.type == "drop":
        drop_item(world, char, action.target)

    elif action.type == "eat":
        use_item(world, char, action.target)
        char.current_action = "eat"
        char.action_ticks_left = TICK_COST["eat"]
        world.add_event(f"{char.name} 开始吃东西")

    elif action.type == "attack":
        target = world.characters.get(action.target)
        if target:
            execute_combat_tick(world, char, target)
            try_skill_growth(char, "attack")

    elif action.type in LABOR_ACTIONS:
        char.current_action = action.type
        char.action_ticks_left = TICK_COST.get(action.type, 4)
        char.action_target = action.target
        earn_points(char, action.type)
        try_skill_growth(char, action.type)

    elif action.type == "sleep":
        char.current_action = "sleep"
        char.action_ticks_left = TICK_COST["sleep"]

    elif action.type == "wait":
        pass  # do nothing


def _complete_action(world: WorldState, char: Character):
    """Called when a multi-tick action finishes."""
    action = char.current_action
    if action == "mine":
        # produce ore at character's location
        from models.item import Item
        ore_id = f"ore_{world.tick}_{char.id}"
        world.items[ore_id] = Item(id=ore_id, name="矿石", type="material", weight=5.0, durability=-1)
        tile = world.get_tile(char.x, char.y)
        if tile:
            tile.items.append(ore_id)
        world.add_event(f"{char.name} 完成一轮采矿")

    elif action == "cook":
        from models.item import Item
        meal_id = f"meal_{world.tick}_{char.id}"
        world.items[meal_id] = Item(
            id=meal_id, name="热餐", type="food", weight=0.6,
            durability=0, effects={"hunger": 40, "energy": 5},
        )
        tile = world.get_tile(char.x, char.y)
        if tile:
            tile.items.append(meal_id)
        world.add_event(f"{char.name} 做好了一份热餐")

    elif action == "sleep":
        char.energy = min(100, char.energy + 60)
        world.add_event(f"{char.name} 睡醒了")

    elif action == "repair":
        world.add_event(f"{char.name} 完成了维修工作")


def _update_occupants(world: WorldState):
    """Rebuild tile occupant lists from character positions."""
    for t in world.tiles.values():
        t.occupants.clear()
    for char in world.characters.values():
        if char.alive:
            t = world.get_tile(char.x, char.y)
            if t:
                t.occupants.append(char.id)
