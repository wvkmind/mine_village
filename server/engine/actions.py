"""Action definitions — all possible character actions with tick costs and preconditions."""
from __future__ import annotations
from dataclasses import dataclass

# Action tick costs
TICK_COST = {
    "move": 1,
    "talk": 1,
    "long_talk": 3,
    "pickup": 1,
    "drop": 1,
    "use": 1,
    "eat": 4,
    "wait": 1,
    "attack": 1,
    "mine": 6,
    "cook": 4,
    "repair": 5,
    "craft": 6,  # varies by item
    "dig": 6,
    "build_wall": 4,
    "build_door": 3,
    "sleep": 36,
    "patrol": 3,
    "heal": 3,
    "forage": 4,
}


@dataclass
class Action:
    type: str
    actor_id: str
    target: str | None = None  # character_id, item_id, direction, or None
    message: str | None = None  # for talk actions
    ticks: int = 1

    @staticmethod
    def move(actor_id: str, direction: str) -> Action:
        return Action(type="move", actor_id=actor_id, target=direction, ticks=1)

    @staticmethod
    def talk(actor_id: str, target_id: str, message: str = "") -> Action:
        return Action(type="talk", actor_id=actor_id, target=target_id, message=message, ticks=1)

    @staticmethod
    def pickup(actor_id: str, item_id: str) -> Action:
        return Action(type="pickup", actor_id=actor_id, target=item_id, ticks=1)

    @staticmethod
    def eat(actor_id: str, item_id: str) -> Action:
        return Action(type="eat", actor_id=actor_id, target=item_id, ticks=TICK_COST["eat"])

    @staticmethod
    def attack(actor_id: str, target_id: str) -> Action:
        return Action(type="attack", actor_id=actor_id, target=target_id, ticks=1)

    @staticmethod
    def work(actor_id: str, work_type: str) -> Action:
        return Action(type=work_type, actor_id=actor_id, ticks=TICK_COST.get(work_type, 4))

    @staticmethod
    def wait(actor_id: str) -> Action:
        return Action(type="wait", actor_id=actor_id, ticks=1)

    @staticmethod
    def sleep(actor_id: str) -> Action:
        return Action(type="sleep", actor_id=actor_id, ticks=TICK_COST["sleep"])
