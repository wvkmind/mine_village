"""Character model — shared by NPC and player."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Personality:
    """8-axis personality, each 0-100."""
    sociability: int = 50
    diligence: int = 50
    courage: int = 50
    generosity: int = 50
    honesty: int = 50
    curiosity: int = 50
    temper: int = 50
    ambition: int = 50


@dataclass
class Character:
    id: str
    name: str
    is_player: bool = False

    # position
    x: int = 0
    y: int = 0

    # survival (0-100, 0 = critical)
    hunger: float = 80.0
    energy: float = 80.0
    health: float = 100.0

    # combat (hidden from player display)
    attack: float = 5.0
    defense: float = 3.0

    # skills: max 3, name -> proficiency 0-100
    skills: dict[str, int] = field(default_factory=dict)

    # social
    labor_points: int = 0
    reputation: int = 50

    # action state
    current_action: str | None = None
    action_ticks_left: int = 0
    action_target: str | None = None
    alive: bool = True

    # inventory: list of item IDs
    inventory: list[str] = field(default_factory=list)
    equipped: dict[str, str | None] = field(default_factory=lambda: {"weapon": None, "tool": None})

    # NPC-only
    personality: Personality = field(default_factory=Personality)
    role: str = ""  # "矿工", "厨师", "医生", "维修工", "巡逻者", "老者", ""

    @property
    def is_busy(self) -> bool:
        return self.action_ticks_left > 0

    @property
    def is_dead(self) -> bool:
        return not self.alive
