"""Skill system — growth through practice, max 3 skills, efficiency bonuses."""
from __future__ import annotations
import random
from models.character import Character

SKILLS = {
    "mining": "采矿",
    "cooking": "烹饪",
    "repair": "维修",
    "combat": "战斗",
    "medical": "医疗",
    "foraging": "地表采集",
    "social": "社交",
}

MAX_SKILLS = 3

# Action type -> skill it trains
ACTION_SKILL_MAP = {
    "mine": "mining",
    "cook": "cooking",
    "repair": "repair",
    "attack": "combat",
    "heal": "medical",
    "forage": "foraging",
    "talk": "social",
}

# Base growth chance per practice tick
GROWTH_CHANCE = 0.05  # 5% per tick of practice


def try_skill_growth(char: Character, action_type: str) -> str | None:
    """Attempt to grow skill from action. Returns skill name if leveled up, else None."""
    skill_name = ACTION_SKILL_MAP.get(action_type)
    if not skill_name:
        return None

    if skill_name in char.skills:
        # existing skill: chance decreases with level
        level = char.skills[skill_name]
        chance = GROWTH_CHANCE * (1 - level / 100)
        if random.random() < chance:
            char.skills[skill_name] = min(100, level + 1)
            return skill_name
    elif len(char.skills) < MAX_SKILLS:
        # new skill: higher chance to start
        if random.random() < GROWTH_CHANCE * 3:
            char.skills[skill_name] = 1
            return skill_name
    # at max skills and this isn't one of them: no growth
    return None


def get_skill_bonus(char: Character, skill_name: str) -> float:
    """Multiplier from skill level. 1.0 = no skill, up to 2.0 at level 100."""
    level = char.skills.get(skill_name, 0)
    return 1.0 + level / 100.0
