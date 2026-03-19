"""Economy — labor points earning and spending."""
from __future__ import annotations
from models.character import Character

# Points earned per tick of work
EARN_RATES = {
    "mine": 3,
    "cook": 2,
    "patrol": 2,
    "repair": 4,
    "heal": 3,
    "craft": 2,
    "forage": 2,
}

# Costs for services/goods
COSTS = {
    "meal": 5,
    "basic_tool": 15,
    "medical_treatment": 20,
    "weapon": 30,
}


def earn_points(char: Character, action_type: str):
    """Award labor points for a work action tick."""
    pts = EARN_RATES.get(action_type, 0)
    if pts:
        char.labor_points += pts


def spend_points(char: Character, amount: int) -> bool:
    """Deduct points. Returns False if insufficient."""
    if char.labor_points < amount:
        return False
    char.labor_points -= amount
    return True
