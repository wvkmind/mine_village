"""Relationship model and event impact table."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Relationship:
    character_a: str
    character_b: str
    value: int = 0  # -100 to 100
    type: str = "stranger"  # stranger, acquaintance, friend, close_friend, rival, enemy, spouse, family
    history: list[dict] = field(default_factory=list)  # [{tick, event_type, delta, description}]


# Event type -> (min_delta, max_delta) — AI picks exact value based on personality
EVENT_IMPACT = {
    "help":             (5, 20),
    "gift":             (3, 15),
    "conflict":         (-40, -10),
    "deception_caught": (-50, -15),
    "daily_chat":       (-2, 5),
    "shared_danger":    (10, 30),
    "betrayal":         (-80, -30),
}

# Thresholds for relationship type transitions
TYPE_THRESHOLDS = {
    "enemy":        (-100, -50),
    "rival":        (-50, -10),
    "stranger":     (-10, 10),
    "acquaintance": (10, 30),
    "friend":       (30, 60),
    "close_friend": (60, 100),
    # spouse and family are set explicitly, not by threshold
}


def classify_relationship(value: int, current_type: str) -> str:
    """Determine relationship type from value. Preserves spouse/family."""
    if current_type in ("spouse", "family"):
        return current_type
    for rtype, (lo, hi) in TYPE_THRESHOLDS.items():
        if lo <= value < hi:
            return rtype
    return "close_friend" if value >= 60 else "enemy"
