"""Memory system — creation, decay, retrieval, and information propagation."""
from __future__ import annotations
import random
from models.world import WorldState
from models.memory import Memory
from models.character import Character

TICKS_PER_DAY = 144
PERMANENT_THRESHOLD = 7  # importance >= this is permanent


def add_memory(world: WorldState, character_id: str, content: str,
               mem_type: str = "event", importance: int = 3,
               related: list[str] | None = None, source: str = "firsthand",
               chain: list[str] | None = None):
    """Create and store a new memory for a character."""
    m = Memory(
        character_id=character_id,
        tick=world.tick,
        type=mem_type,
        content=content,
        importance=importance,
        related_characters=related or [],
        permanent=importance >= PERMANENT_THRESHOLD,
        source=source,
        propagation_chain=chain or [],
    )
    world.memories.append(m)


def get_decision_context(world: WorldState, character_id: str) -> list[Memory]:
    """Get memories for AI decision: recent 12 ticks + all permanent + related compressed."""
    result = []
    for m in world.memories:
        if m.character_id != character_id:
            continue
        if m.tick >= world.tick - 12:
            result.append(m)
        elif m.permanent:
            result.append(m)
    return result


def propagate_info(world: WorldState, speaker: Character, listener: Character,
                   memory: Memory):
    """Speaker shares a memory with listener. Honesty affects distortion."""
    honesty = speaker.personality.honesty
    # distortion: low honesty = content may be exaggerated
    content = memory.content
    if honesty < 30 and random.random() < 0.5:
        content = f"（传闻，可能夸大）{content}"

    chain = memory.propagation_chain.copy()
    chain.append(speaker.id)

    add_memory(
        world, listener.id, content,
        mem_type="rumor" if len(chain) > 1 else memory.type,
        importance=max(1, memory.importance - 1),
        related=memory.related_characters,
        source=f"heard_from_{speaker.id}",
        chain=chain,
    )


def mark_for_compression(world: WorldState):
    """Mark old non-permanent memories for AI compression. Called at day boundaries."""
    threshold = world.tick - TICKS_PER_DAY
    for m in world.memories:
        if not m.permanent and not m.compressed and m.tick < threshold:
            m.compressed = True  # AI will summarize these in batch
