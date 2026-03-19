"""Memory model for NPC knowledge and information propagation."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Memory:
    character_id: str
    tick: int
    type: str  # "event", "conversation", "observation", "rumor"
    content: str  # natural language description
    importance: int = 1  # 1-10, >= 7 is permanent
    related_characters: list[str] = field(default_factory=list)
    permanent: bool = False
    source: str = "firsthand"  # "firsthand", "heard_from_xxx", "overheard"
    propagation_chain: list[str] = field(default_factory=list)  # [original, relay1, relay2...]
    compressed: bool = False  # True after AI summarization
