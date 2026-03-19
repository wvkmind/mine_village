"""AI decision — call AI for NPC actions, parse output, rule fallback."""
from __future__ import annotations
import re, logging
from models.world import WorldState
from models.character import Character
from engine.actions import Action, TICK_COST
from ai.prompt import build_decision_prompt, DECISION_SYSTEM
from ai import poe_client

log = logging.getLogger("ai_decision")

# Rule fallback by role
_FALLBACK_ACTIONS = {
    "矿工": "mine",
    "厨师": "cook",
    "医生": "heal",
    "维修工": "repair",
    "巡逻者": "patrol",
    "老者": "wait",
}


def get_npc_action(world: WorldState, npc: Character) -> Action:
    """Get AI decision for NPC. Falls back to rule-based action."""
    if npc.is_busy or npc.is_dead:
        return Action.wait(npc.id)

    if poe_client.is_available():
        prompt = build_decision_prompt(world, npc)
        raw = poe_client.query(prompt, system=DECISION_SYSTEM, task="npc_decision")
        if raw:
            action = _parse_response(raw, npc, world)
            if action:
                return action
            log.info(f"AI parse failed for {npc.id}, using fallback")

    return _rule_fallback(npc, world)


def _parse_response(raw: str, npc: Character, world: WorldState) -> Action | None:
    """Parse AI response: ACTION/TARGET/REASON/DIALOGUE format."""
    action_match = re.search(r"ACTION:\s*(.+)", raw)
    target_match = re.search(r"TARGET:\s*(.+)", raw)
    dialogue_match = re.search(r"DIALOGUE:\s*(.+)", raw)

    if not action_match:
        return None

    action_str = action_match.group(1).strip().lower()
    target_str = target_match.group(1).strip() if target_match else None
    dialogue = dialogue_match.group(1).strip() if dialogue_match else None

    if target_str and target_str.lower() == "none":
        target_str = None

    # map action string to Action
    if action_str.startswith("move"):
        parts = action_str.split()
        direction = parts[1] if len(parts) > 1 else (target_str or "north")
        return Action.move(npc.id, direction)
    elif action_str in ("talk", "对话", "说话"):
        return Action.talk(npc.id, target_str or "", dialogue or "")
    elif action_str in ("eat", "吃"):
        # find food in inventory
        for iid in npc.inventory:
            item = world.items.get(iid)
            if item and item.type == "food":
                return Action.eat(npc.id, iid)
    elif action_str in ("attack", "攻击"):
        if target_str:
            return Action.attack(npc.id, target_str)
    elif action_str in ("sleep", "睡觉"):
        return Action.sleep(npc.id)
    elif action_str in ("wait", "等待"):
        return Action.wait(npc.id)
    elif action_str in TICK_COST:
        return Action.work(npc.id, action_str)

    return None


def _rule_fallback(npc: Character, world: WorldState) -> Action:
    """Simple rule-based action based on NPC role and needs."""
    # critical needs first
    if npc.hunger < 20:
        for iid in npc.inventory:
            item = world.items.get(iid)
            if item and item.type == "food":
                return Action.eat(npc.id, iid)
    if npc.energy < 15:
        return Action.sleep(npc.id)

    # role-based default
    action_type = _FALLBACK_ACTIONS.get(npc.role, "wait")
    if action_type in TICK_COST:
        return Action.work(npc.id, action_type)
    return Action.wait(npc.id)
