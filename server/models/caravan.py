"""Caravan info model — external world interface."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CaravanInfo:
    news: list[str] = field(default_factory=list)
    person_updates: dict[str, str] = field(default_factory=dict)  # {name: status}
    road_events: list[str] = field(default_factory=list)
    main_city_changes: list[str] = field(default_factory=list)
    cargo: dict[str, int] = field(default_factory=dict)  # item_type -> quantity
    arriving_characters: list[str] = field(default_factory=list)  # new NPC IDs
    departing_characters: list[str] = field(default_factory=list)
